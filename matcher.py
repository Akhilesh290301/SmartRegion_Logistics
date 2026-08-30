from datetime import datetime


def normalize(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def capability_matches(requirement, service, resource):
    required = normalize(
        requirement.get("capability_semantic_id")
        or requirement.get("service_category")
    )
    offered = normalize(
        service.get("capability_semantic_id")
        or service.get("category")
    )
    resource_capability = normalize(resource.get("capability_semantic_id"))

    if not required:
        return True

    return required == offered or required == resource_capability


def capacity_matches(requirement, resource):
    required = number(requirement.get("required_capacity"))
    available = number(resource.get("available_capacity"))

    if required is None:
        return True
    if available is None:
        return False

    requirement_unit = normalize(requirement.get("capacity_unit"))
    resource_unit = normalize(resource.get("capacity_unit"))

    if requirement_unit and resource_unit and requirement_unit != resource_unit:
        return False

    return available >= required


def availability_status_matches(resource):
    status = normalize(resource.get("availability_status"))
    return status in {"available", "partially_available"}


def time_window_matches(requirement, resource):
    required_from = parse_datetime(requirement.get("required_from"))
    required_until = parse_datetime(requirement.get("required_until"))

    if not required_from and not required_until:
        return True

    windows = resource.get("availability_windows", [])
    if not windows:
        return False

    for window in windows:
        available_from = parse_datetime(window.get("available_from"))
        available_until = parse_datetime(window.get("available_until"))

        if not available_from or not available_until:
            continue

        start_ok = required_from is None or available_from <= required_from
        end_ok = required_until is None or available_until >= required_until

        if start_ok and end_ok:
            return True

    return False


def location_matches(requirement, service, resource):
    required_location = normalize(
        requirement.get("required_location") or requirement.get("origin")
    )

    if not required_location:
        return True

    resource_location = normalize(resource.get("location"))
    service_area = [
        normalize(item)
        for item in service.get("service_area", [])
    ]

    return required_location == resource_location or required_location in service_area


def certification_matches(requirement, service, resource, company):
    required = requirement.get("certifications", [])

    if not required:
        single = requirement.get("certification_standard")
        if single:
            required = [single]

    if not required:
        return True

    offered = {
        normalize(item)
        for item in (
            company.get("certifications", [])
            + service.get("certifications", [])
            + resource.get("certifications", [])
        )
    }

    return all(normalize(certification) in offered for certification in required)


def price_matches(requirement, service):
    maximum_price = number(requirement.get("maximum_price"))

    if maximum_price is None:
        return True

    price = number(service.get("base_price"))

    if price is None:
        return True

    return price <= maximum_price


def evaluate_candidate(requirement, company, service, resource):
    checks = {
        "Capability": capability_matches(requirement, service, resource),
        "Capacity": capacity_matches(requirement, resource),
        "Availability": availability_status_matches(resource),
        "Time window": time_window_matches(requirement, resource),
        "Location / service area": location_matches(
            requirement, service, resource
        ),
        "Certification": certification_matches(
            requirement, service, resource, company
        ),
        "Price constraint": price_matches(requirement, service),
    }

    passed = sum(checks.values())
    hard_score = (passed / len(checks)) * 100

    mandatory_fields = {
        "Capability",
        "Capacity",
        "Availability",
        "Time window",
        "Location / service area",
        "Certification",
    }

    mandatory_pass = all(checks[name] for name in mandatory_fields)

    if mandatory_pass:
        classification = "Suitable"
    elif hard_score >= 60:
        classification = "Partially Suitable"
    else:
        classification = "Unsuitable"

    explanation = [
        (
            f"✓ {criterion}: requirement satisfied."
            if result
            else f"✕ {criterion}: requirement not satisfied."
        )
        for criterion, result in checks.items()
    ]

    return hard_score, classification, explanation


def run_matching(requirement, companies, services, resources):
    company_map = {
        company.get("company_id"): company
        for company in companies
    }

    results = []

    for service in services:
        provider_id = service.get("provider_company_id")
        company = company_map.get(provider_id, {})

        if company.get("role") == "Requesting Company":
            continue

        supporting_resources = service.get("supporting_resources", [])

        for resource in resources:
            resource_id = resource.get("resource_id")

            if supporting_resources and resource_id not in supporting_resources:
                continue

            if resource.get("provider_company_id") != provider_id:
                continue

            score, classification, explanation = evaluate_candidate(
                requirement,
                company,
                service,
                resource,
            )

            results.append(
                {
                    "provider_name": company.get("name", provider_id),
                    "provider_id": provider_id,
                    "service_id": service.get("service_id"),
                    "service_name": service.get("name"),
                    "resource_id": resource_id,
                    "resource_name": resource.get("name", resource_id),
                    "resource_type": resource.get("resource_type"),
                    "location": (
                        resource.get("location")
                        or company.get("location")
                    ),
                    "available_capacity": resource.get("available_capacity"),
                    "availability_status": resource.get(
                        "availability_status"
                    ),
                    "score": round(score, 1),
                    "classification": classification,
                    "explanation": explanation,
                }
            )

    priority = {
        "Suitable": 3,
        "Partially Suitable": 2,
        "Unsuitable": 1,
    }

    results.sort(
        key=lambda item: (
            priority.get(item["classification"], 0),
            item["score"],
        ),
        reverse=True,
    )

    return results