import streamlit as st
from datetime import datetime, date, time
from html import escape

from repository import (
    load_repository,
    get_repository_summary,
    get_companies,
    get_services,
    get_resources,
    get_requirements,
)
from matcher import run_matching
from i18n import TRANSLATIONS
from styles import APP_CSS

st.set_page_config(
    page_title="SmartRegion Logistics Matching",
    page_icon="🔗",
    layout="wide",
)

st.markdown(APP_CSS, unsafe_allow_html=True)


def safe(value):
    return escape(str(value))


def value_or_dash(value):
    if value in (None, "", [], {}):
        return "—"
    return str(value)


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_reference(value):
    if value in (None, "", [], {}):
        return "—"

    value = str(value)
    return value.split(":")[-1] if ":" in value else value


def parse_repository_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def combine_datetime(selected_date, selected_time, original_datetime=None):
    timezone_info = original_datetime.tzinfo if original_datetime else None
    return datetime.combine(
        selected_date,
        selected_time,
    ).replace(tzinfo=timezone_info)


def company_display(company):
    name = company.get("name") or company.get("company_id")
    return f'{name} ({company.get("company_id")})'


_, language_column = st.columns([8.7, 1.3])

with language_column:
    language = st.selectbox(
        "Language",
        ["English", "Deutsch"],
        label_visibility="collapsed",
    )

t = TRANSLATIONS[language]

repository = load_repository()
companies = get_companies(repository)
services = get_services(repository)
resources = get_resources(repository)
requirements = get_requirements(repository)
summary = get_repository_summary(repository)

hero_html = (
    '<div class="hero-wrapper">'
    '<div class="hero-badge">SMARTREGION · ASSET ADMINISTRATION SHELL</div>'
    '<h1 class="hero-title">'
    'SmartRegion '
    f'<span class="hero-highlight">{safe(t["matching_engine"])}</span>'
    "</h1>"
    f'<p class="hero-subtitle">{safe(t["subtitle"])}</p>'
    '<div class="hero-tags">'
    '<span class="hero-tag">AAS</span>'
    '<span class="hero-tag">Requirement Mode</span>'
    '<span class="hero-tag">Repository Based</span>'
    '<span class="hero-tag">Explainable Matching</span>'
    "</div>"
    "</div>"
)

st.markdown(hero_html, unsafe_allow_html=True)

if summary["connected"]:
    st.success(f'✓ Repository connected · {summary["endpoint"]}')
else:
    st.error(f'Repository unavailable · {summary["endpoint"]}')

m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("AAS", summary["aas_count"], "Total AAS")

with m2:
    st.metric(
        t["companies"],
        summary["company_count"],
        t["registered_companies"],
    )

with m3:
    st.metric(
        t["services"],
        summary["service_count"],
        t["offered_services"],
    )

with m4:
    st.metric(
        t["resources"],
        summary["resource_count"],
        t["available_resources"],
    )

with m5:
    st.metric(
        t["stored_requirements"],
        summary["requirement_count"],
        "Requirement AAS",
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f'<div class="section-heading">{safe(t["requirement_configuration"])}</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="section-description">'
    f'{safe(t["repository_requirement_description"])}'
    "</div>",
    unsafe_allow_html=True,
)

custom_requirement = st.toggle(
    t["custom_requirement"],
    help=t["custom_help"],
)

requesting_companies = [
    company
    for company in companies
    if company.get("role") == "Requesting Company"
]

if not requesting_companies:
    requesting_companies = [
        company
        for company in companies
        if company.get("company_id") == "COMPANY-004"
    ]

requester_labels = {
    company_display(company): company.get("company_id")
    for company in requesting_companies
}

if not custom_requirement:
    if not requirements:
        st.error(
            "No SmartRegion requirements were found in the BaSyx repository."
        )
        st.stop()

    requirement_purpose_labels = {
        "REQ-001": "Refrigerated Transport · Base Case",
        "REQ-002": "Refrigerated Transport · High Capacity",
        "REQ-003": "Refrigerated Transport · Availability Test",
        "REQ-004": "Warehouse Storage · Capacity Test",
        "REQ-005": "Standard Truck · General Freight",
    }

    requirement_map = {}

    for requirement in requirements:
        requirement_id = requirement.get("requirement_id") or "Unknown"
        purpose = (
            requirement_purpose_labels.get(requirement_id)
            or requirement.get("title")
            or requirement_id
        )
        requirement_map[f"{requirement_id} — {purpose}"] = requirement

    selected_label = st.selectbox(
        t["requirement"],
        list(requirement_map.keys()),
    )

    base_requirement = dict(requirement_map[selected_label])

    default_requester = clean_reference(
        base_requirement.get("requesting_company")
    )

    requester_display_default = next(
        (
            label
            for label, company_id in requester_labels.items()
            if company_id == default_requester
        ),
        None,
    )

    requester_options = list(requester_labels.keys())

    if not requester_options:
        requester_options = [
            "SmartParts Manufacturing GmbH (COMPANY-004)"
        ]
        requester_labels[requester_options[0]] = "COMPANY-004"

    requester_index = (
        requester_options.index(requester_display_default)
        if requester_display_default in requester_options
        else 0
    )

    default_requirement_type = (
        base_requirement.get("requirement_type") or "COMBINED"
    )
    default_service_category = (
        base_requirement.get("service_category") or "TRANSPORT"
    )
    default_resource_type = base_requirement.get("resource_type") or ""
    default_capacity = to_float(
        base_requirement.get("required_capacity"),
        0.0,
    )
    default_capacity_unit = (
        base_requirement.get("capacity_unit") or "kg"
    )
    default_operator = (
        base_requirement.get("capacity_operator") or ">="
    )

    location_options = sorted(
        {
            company.get("city") or company.get("location")
            for company in companies
            if company.get("city") or company.get("location")
        }
    )

    default_origin = (
        base_requirement.get("origin")
        or base_requirement.get("required_location")
        or ""
    )
    default_destination = base_requirement.get("destination") or ""

    for location_value in [default_origin, default_destination]:
        if location_value and location_value not in location_options:
            location_options.append(location_value)

    location_options = sorted(set(location_options))

    service_categories = sorted(
        {
            service.get("category")
            for service in services
            if service.get("category")
        }
    )

    if default_service_category not in service_categories:
        service_categories.insert(0, default_service_category)

    resource_types = sorted(
        {
            resource.get("resource_type")
            for resource in resources
            if resource.get("resource_type")
        }
    )

    if (
        default_resource_type
        and default_resource_type not in resource_types
    ):
        resource_types.insert(0, default_resource_type)

    if not resource_types:
        resource_types = [
            "RefrigeratedTruck",
            "StandardTruck",
            "Warehouse",
            "Forklift",
        ]

    original_from = parse_repository_datetime(
        base_requirement.get("required_from")
    )
    original_until = parse_repository_datetime(
        base_requirement.get("required_until")
    )

    if original_from is None:
        original_from = datetime(2026, 9, 2, 8, 0)

    if original_until is None:
        original_until = datetime(2026, 9, 2, 18, 0)

    left_column, right_column = st.columns(2)

    with left_column:
        requester_label = st.selectbox(
            t["requesting_company"],
            requester_options,
            index=requester_index,
        )
        requesting_company = requester_labels[requester_label]

        requirement_types = ["COMBINED", "SERVICE", "RESOURCE"]

        requirement_type = st.selectbox(
            "Requirement Type",
            requirement_types,
            index=(
                requirement_types.index(default_requirement_type)
                if default_requirement_type in requirement_types
                else 0
            ),
        )

        service_category = st.selectbox(
            t["service_category"],
            service_categories,
            index=(
                service_categories.index(default_service_category)
                if default_service_category in service_categories
                else 0
            ),
        )

        resource_type = st.selectbox(
            t["resource_type"],
            resource_types,
            index=(
                resource_types.index(default_resource_type)
                if default_resource_type in resource_types
                else 0
            ),
        )

        if location_options:
            origin = st.selectbox(
                "Origin / Required Location",
                location_options,
                index=(
                    location_options.index(default_origin)
                    if default_origin in location_options
                    else 0
                ),
            )

            destination_options = ["Not Applicable"] + location_options
            destination_default = (
                default_destination
                if default_destination
                else "Not Applicable"
            )

            destination = st.selectbox(
                t["destination"],
                destination_options,
                index=(
                    destination_options.index(destination_default)
                    if destination_default in destination_options
                    else 0
                ),
            )

            if destination == "Not Applicable":
                destination = ""
        else:
            origin = st.text_input(
                "Origin / Required Location",
                value=default_origin,
            )
            destination = st.text_input(
                t["destination"],
                value=default_destination,
            )

    with right_column:
        required_capacity = st.number_input(
            t["required_capacity"],
            min_value=0.0,
            value=default_capacity,
            step=100.0,
        )

        capacity_units = ["kg", "t", "m2", "m3", "unit", "pallet"]

        if default_capacity_unit not in capacity_units:
            capacity_units.insert(0, default_capacity_unit)

        capacity_unit = st.selectbox(
            t["capacity_unit"],
            capacity_units,
            index=capacity_units.index(default_capacity_unit),
        )

        capacity_operators = [">=", ">", "=", "<=", "<"]

        capacity_operator = st.selectbox(
            "Capacity Operator",
            capacity_operators,
            index=(
                capacity_operators.index(default_operator)
                if default_operator in capacity_operators
                else 0
            ),
        )

        st.markdown(f'**{t["required_from"]}**')
        from_date_column, from_time_column = st.columns([1.4, 1])

        with from_date_column:
            required_from_date = st.date_input(
                "From Date",
                value=original_from.date(),
                label_visibility="collapsed",
            )

        with from_time_column:
            required_from_time = st.time_input(
                "From Time",
                value=original_from.time(),
                label_visibility="collapsed",
            )

        st.markdown(f'**{t["required_until"]}**')
        until_date_column, until_time_column = st.columns([1.4, 1])

        with until_date_column:
            required_until_date = st.date_input(
                "Until Date",
                value=original_until.date(),
                label_visibility="collapsed",
            )

        with until_time_column:
            required_until_time = st.time_input(
                "Until Time",
                value=original_until.time(),
                label_visibility="collapsed",
            )

    required_from = combine_datetime(
        required_from_date,
        required_from_time,
        original_from,
    ).isoformat()

    required_until = combine_datetime(
        required_until_date,
        required_until_time,
        original_until,
    ).isoformat()

    selected_requirement = {
        **base_requirement,
        "requesting_company": requesting_company,
        "requirement_type": requirement_type,
        "service_category": service_category,
        "resource_type": resource_type,
        "origin": origin,
        "destination": destination,
        "required_location": (
            origin if service_category == "WAREHOUSING" else None
        ),
        "required_capacity": required_capacity,
        "capacity_unit": capacity_unit,
        "capacity_operator": capacity_operator,
        "required_from": required_from,
        "required_until": required_until,
        "capability_semantic_id": (
            base_requirement.get("capability_semantic_id") or ""
        ),
    }

else:
    st.info(
        "Custom Requirement creates a temporary requirement. "
        "It does not modify the BaSyx repository."
    )

    requester_options = list(requester_labels.keys())

    if not requester_options:
        requester_options = [
            "SmartParts Manufacturing GmbH (COMPANY-004)"
        ]
        requester_labels[requester_options[0]] = "COMPANY-004"

    service_categories = sorted(
        {
            service.get("category")
            for service in services
            if service.get("category")
        }
    )

    if not service_categories:
        service_categories = [
            "TRANSPORT",
            "WAREHOUSING",
            "EQUIPMENT_SHARING",
        ]

    resource_types = sorted(
        {
            resource.get("resource_type")
            for resource in resources
            if resource.get("resource_type")
        }
    )

    if not resource_types:
        resource_types = [
            "RefrigeratedTruck",
            "StandardTruck",
            "Warehouse",
            "Forklift",
        ]

    locations = sorted(
        {
            company.get("city") or company.get("location")
            for company in companies
            if company.get("city") or company.get("location")
        }
    )

    if not locations:
        locations = [
            "Magdeburg",
            "Halle (Saale)",
            "Quedlinburg",
        ]

    left_column, right_column = st.columns(2)

    with left_column:
        requirement_id = st.text_input(
            "Requirement ID",
            value="CUSTOM-001",
        )
        requirement_title = st.text_input(
            t["requirement_title"],
            value="Custom Requirement",
        )
        requester_label = st.selectbox(
            t["requesting_company"],
            requester_options,
        )
        requesting_company = requester_labels[requester_label]

        requirement_type = st.selectbox(
            "Requirement Type",
            ["COMBINED", "SERVICE", "RESOURCE"],
        )
        service_category = st.selectbox(
            t["service_category"],
            service_categories,
        )
        resource_type = st.selectbox(
            t["resource_type"],
            resource_types,
        )
        origin = st.selectbox(
            "Origin / Required Location",
            locations,
        )
        destination = st.selectbox(
            t["destination"],
            ["Not Applicable"] + locations,
        )

        if destination == "Not Applicable":
            destination = ""

    with right_column:
        required_capacity = st.number_input(
            t["required_capacity"],
            min_value=0.0,
            value=12000.0,
            step=100.0,
        )
        capacity_unit = st.selectbox(
            t["capacity_unit"],
            ["kg", "t", "m2", "m3", "unit", "pallet"],
        )
        capacity_operator = st.selectbox(
            "Capacity Operator",
            [">=", ">", "=", "<=", "<"],
        )

        st.markdown(f'**{t["required_from"]}**')
        from_date_column, from_time_column = st.columns([1.4, 1])

        with from_date_column:
            required_from_date = st.date_input(
                "Custom From Date",
                value=date(2026, 9, 2),
                label_visibility="collapsed",
            )

        with from_time_column:
            required_from_time = st.time_input(
                "Custom From Time",
                value=time(8, 0),
                label_visibility="collapsed",
            )

        st.markdown(f'**{t["required_until"]}**')
        until_date_column, until_time_column = st.columns([1.4, 1])

        with until_date_column:
            required_until_date = st.date_input(
                "Custom Until Date",
                value=date(2026, 9, 2),
                label_visibility="collapsed",
            )

        with until_time_column:
            required_until_time = st.time_input(
                "Custom Until Time",
                value=time(18, 0),
                label_visibility="collapsed",
            )

    capability_options = {
        "Temperature Controlled Transport": (
            "urn:smartregion:semantic:capability:"
            "TemperatureControlledTransport"
        ),
        "General Freight Transport": (
            "urn:smartregion:semantic:capability:"
            "GeneralFreightTransport"
        ),
        "Warehouse Storage": (
            "urn:smartregion:semantic:capability:WarehouseStorage"
        ),
        "Material Handling": (
            "urn:smartregion:semantic:capability:MaterialHandling"
        ),
    }

    selected_capability_name = st.selectbox(
        "Required Capability",
        list(capability_options.keys()),
    )

    required_from = datetime.combine(
        required_from_date,
        required_from_time,
    ).isoformat()

    required_until = datetime.combine(
        required_until_date,
        required_until_time,
    ).isoformat()

    selected_requirement = {
        "requirement_id": requirement_id,
        "title": requirement_title,
        "requesting_company": requesting_company,
        "requirement_type": requirement_type,
        "service_category": service_category,
        "resource_type": resource_type,
        "origin": origin,
        "destination": destination,
        "required_location": (
            origin if service_category == "WAREHOUSING" else None
        ),
        "required_capacity": required_capacity,
        "capacity_unit": capacity_unit,
        "capacity_operator": capacity_operator,
        "capacity_mandatory": True,
        "required_from": required_from,
        "required_until": required_until,
        "maximum_price": None,
        "capability_semantic_id": capability_options[
            selected_capability_name
        ],
        "technical_constraints": [],
        "evaluation_policy": {},
        "custom": True,
    }

valid_time_window = True

try:
    start_dt = datetime.fromisoformat(
        selected_requirement["required_from"]
    )
    end_dt = datetime.fromisoformat(
        selected_requirement["required_until"]
    )

    if end_dt <= start_dt:
        st.error(
            "Required Until must be later than Required From."
        )
        valid_time_window = False
except Exception:
    st.error("Invalid requirement time window.")
    valid_time_window = False

st.markdown("<br>", unsafe_allow_html=True)

s1, s2, s3, s4 = st.columns(4)

with s1:
    st.markdown(
        '<div class="info-card">'
        '<div class="card-label">REQUIREMENT</div>'
        '<div class="card-value card-value-small">'
        f'{safe(value_or_dash(selected_requirement.get("requirement_id")))}'
        "</div>"
        '<div class="card-small">'
        f'{safe(value_or_dash(selected_requirement.get("title")))}'
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with s2:
    st.markdown(
        '<div class="info-card">'
        '<div class="card-label">RESOURCE TYPE</div>'
        '<div class="card-value card-value-small">'
        f'{safe(value_or_dash(selected_requirement.get("resource_type")))}'
        "</div>"
        '<div class="card-small">'
        f'{safe(value_or_dash(selected_requirement.get("service_category")))}'
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with s3:
    origin_display = value_or_dash(
        selected_requirement.get("origin")
        or selected_requirement.get("required_location")
    )

    destination_value = selected_requirement.get("destination")

    route_display = (
        f"{origin_display} → {destination_value}"
        if destination_value
        else origin_display
    )

    st.markdown(
        '<div class="info-card">'
        '<div class="card-label">ROUTE / LOCATION</div>'
        '<div class="card-value card-value-small">'
        f"{safe(route_display)}"
        "</div>"
        '<div class="card-small">Matching location</div>'
        "</div>",
        unsafe_allow_html=True,
    )

with s4:
    capacity_display = (
        f'{selected_requirement.get("required_capacity")} '
        f'{selected_requirement.get("capacity_unit")}'
    )

    st.markdown(
        '<div class="info-card">'
        '<div class="card-label">REQUIRED CAPACITY</div>'
        '<div class="card-value card-value-small">'
        f"{safe(capacity_display)}"
        "</div>"
        '<div class="card-small">'
        f'{safe(selected_requirement.get("capacity_operator"))} required'
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with st.expander("Requirement AAS Details"):
    left_details, right_details = st.columns(2)

    with left_details:
        st.write(
            "**Requirement ID:**",
            value_or_dash(selected_requirement.get("requirement_id")),
        )
        st.write(
            "**Requirement Title:**",
            value_or_dash(selected_requirement.get("title")),
        )
        st.write(
            "**Requesting Company:**",
            value_or_dash(
                selected_requirement.get("requesting_company")
            ),
        )
        st.write(
            "**Requirement Type:**",
            value_or_dash(selected_requirement.get("requirement_type")),
        )
        st.write(
            "**Service Category:**",
            value_or_dash(selected_requirement.get("service_category")),
        )
        st.write(
            "**Resource Type:**",
            value_or_dash(selected_requirement.get("resource_type")),
        )

    with right_details:
        st.write(
            "**Required Capability:**",
            value_or_dash(
                selected_requirement.get("capability_semantic_id")
            ),
        )
        st.write(
            "**Capacity Operator:**",
            value_or_dash(selected_requirement.get("capacity_operator")),
        )
        st.write(
            "**Required From:**",
            value_or_dash(selected_requirement.get("required_from")),
        )
        st.write(
            "**Required Until:**",
            value_or_dash(selected_requirement.get("required_until")),
        )

st.markdown("<br>", unsafe_allow_html=True)

run_button = st.button(
    f'🔎 {t["run_matching"]}',
    use_container_width=True,
    disabled=not valid_time_window,
)

if run_button:
    results = run_matching(
        requirement=selected_requirement,
        companies=companies,
        services=services,
        resources=resources,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-heading">{safe(t["matching_results"])}</div>',
        unsafe_allow_html=True,
    )

    if not results:
        st.warning(t["no_matching_resources"])
    else:
        for rank, result in enumerate(results, start=1):
            provider = result.get("provider_name") or "Unknown Provider"
            service_name = result.get("service_name") or "—"
            resource_id = result.get("resource_id") or "—"
            resource_name = result.get("resource_name") or resource_id
            score = float(result.get("score", 0))
            classification = result.get("classification") or "Unsuitable"

            if classification == "Suitable":
                status_class = "status-good"
                status_text = t["suitable"]
            elif classification == "Partially Suitable":
                status_class = "status-partial"
                status_text = t["partial"]
            else:
                status_class = "status-bad"
                status_text = t["not_suitable"]

            result_card = (
                '<div class="match-card">'
                '<div class="match-flex">'
                "<div>"
                '<div class="company-name">'
                f"#{rank} &nbsp; {safe(provider)}"
                "</div>"
                '<div class="company-meta">'
                f"{safe(service_name)} &nbsp; • &nbsp;"
                f"{safe(resource_id)} &nbsp; • &nbsp;"
                f"{safe(resource_name)}"
                "</div>"
                f'<div class="{status_class}">{safe(status_text)}</div>'
                "</div>"
                "<div>"
                f'<div class="score">{score:.1f}%</div>'
                f'<div class="score-label">{safe(t["match_score"])}</div>'
                "</div>"
                "</div>"
                "</div>"
            )

            st.markdown(result_card, unsafe_allow_html=True)

            with st.expander(
                f'{t["match_explanation"]} — {resource_id}'
            ):
                evaluation_column, data_column = st.columns([1.5, 1])

                with evaluation_column:
                    st.markdown(f'#### {t["evaluation"]}')
                    for explanation in result.get("explanation", []):
                        st.write(explanation)

                with data_column:
                    st.markdown("#### Repository Data")
                    st.write("**Provider:**", provider)
                    st.write("**Service:**", service_name)
                    st.write("**Resource ID:**", resource_id)
                    st.write("**Resource:**", resource_name)
                    st.write(
                        "**Resource Type:**",
                        value_or_dash(result.get("resource_type")),
                    )
                    st.write(
                        "**Location:**",
                        value_or_dash(result.get("location")),
                    )
                    st.write(
                        "**Available Capacity:**",
                        value_or_dash(
                            result.get("available_capacity")
                        ),
                    )
                    st.write(
                        "**Availability:**",
                        value_or_dash(
                            result.get("availability_status")
                        ),
                    )

st.markdown("<br>", unsafe_allow_html=True)

with st.expander(t["providers_resources"]):
    st.markdown("### Companies")

    company_table = []

    for company in companies:
        company_id = company.get("company_id")

        related_services = [
            service
            for service in services
            if service.get("provider_company_id") == company_id
        ]

        related_resources = [
            resource
            for resource in resources
            if resource.get("provider_company_id") == company_id
        ]

        company_table.append(
            {
                "Company ID": company_id,
                "Company": company.get("name"),
                "Location": company.get("location"),
                "Services": len(related_services),
                "Resources": len(related_resources),
                "Role": company.get("role"),
            }
        )

    st.dataframe(
        company_table,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Services")

    service_table = [
        {
            "Service ID": service.get("service_id"),
            "Service": service.get("name"),
            "Category": service.get("category"),
            "Provider": service.get("provider_company_id"),
            "Supporting Resources": ", ".join(
                service.get("supporting_resources", [])
            ),
        }
        for service in services
    ]

    st.dataframe(
        service_table,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Resources")

    resource_table = [
        {
            "Resource ID": resource.get("resource_id"),
            "Resource": resource.get("name"),
            "Type": resource.get("resource_type"),
            "Provider": resource.get("provider_company_id"),
            "Location": resource.get("location"),
            "Available Capacity": resource.get("available_capacity"),
            "Unit": resource.get("capacity_unit"),
            "Availability": resource.get("availability_status"),
        }
        for resource in resources
    ]

    st.dataframe(
        resource_table,
        use_container_width=True,
        hide_index=True,
    )

st.markdown(
    '<div class="footer">'
    "SmartRegion Logistics AAS Prototype · "
    "BaSyx Requirement → Capability → Service → Resource → "
    "Constraint Evaluation → Explainable Matching"
    "</div>",
    unsafe_allow_html=True,
)