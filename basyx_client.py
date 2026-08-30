import os
import re
import requests
import streamlit as st


class BasyxClient:
    def __init__(self, base_url=None, timeout=90):

        if base_url is None:
            try:
                base_url = st.secrets["BASYX_URL"]
            except (KeyError, FileNotFoundError):
                base_url = os.getenv(
                    "BASYX_URL",
                    "http://localhost:8081"
                )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, endpoint):
        response = requests.get(
            f"{self.base_url}{endpoint}",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _get_collection(self, endpoint):
        items = []
        cursor = None

        while True:
            url = endpoint

            if cursor:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}cursor={cursor}"

            data = self._get(url)

            if isinstance(data, list):
                items.extend(data)
                break

            if not isinstance(data, dict):
                break

            result = data.get("result") or data.get("results") or []

            if isinstance(result, list):
                items.extend(result)

            paging = (
                data.get("paging_metadata")
                or data.get("pagingMetadata")
                or {}
            )
            cursor = paging.get("cursor")

            if not cursor:
                break

        return items

    def get_shells(self):
        return self._get_collection("/shells")

    def get_submodels(self):
        return self._get_collection("/submodels")

    def is_connected(self):
        try:
            self.get_shells()
            return True
        except Exception:
            return False

    @staticmethod
    def _model_type(element):
        if not isinstance(element, dict):
            return ""

        model_type = element.get("modelType", "")

        if isinstance(model_type, dict):
            return model_type.get("name") or model_type.get("value") or ""

        return str(model_type)

    @staticmethod
    def _children(element):
        if not isinstance(element, dict):
            return []

        submodel_elements = element.get("submodelElements")

        if isinstance(submodel_elements, list):
            return submodel_elements

        value = element.get("value")

        if isinstance(value, list):
            return value

        statements = element.get("statements")

        if isinstance(statements, list):
            return statements

        return []

    @classmethod
    def _find(cls, element, id_short):
        if element is None:
            return None

        target = str(id_short).lower()

        if isinstance(element, list):
            for item in element:
                found = cls._find(item, id_short)

                if found is not None:
                    return found

            return None

        if not isinstance(element, dict):
            return None

        current_id_short = str(element.get("idShort", "")).lower()

        if current_id_short == target:
            return element

        for child in cls._children(element):
            found = cls._find(child, id_short)

            if found is not None:
                return found

        return None

    @staticmethod
    def _multilingual(value):
        if not isinstance(value, list):
            return value

        for item in value:
            if isinstance(item, dict) and item.get("language") == "en":
                return item.get("text")

        for item in value:
            if isinstance(item, dict):
                text = item.get("text")

                if text:
                    return text

        return None

    @classmethod
    def _reference_value(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            return value

        if isinstance(value, list):
            for item in reversed(value):
                result = cls._reference_value(item)

                if result:
                    return result

            return None

        if not isinstance(value, dict):
            return None

        keys = value.get("keys")

        if isinstance(keys, list) and keys:
            for key in reversed(keys):
                if not isinstance(key, dict):
                    continue

                reference = key.get("value")

                if reference:
                    return reference

        inner_value = value.get("value")

        if inner_value is not None:
            return cls._reference_value(inner_value)

        return None

    @staticmethod
    def _normalize_entity_id(value, prefix=None):
        if value in (None, "", [], {}):
            return None

        text = str(value)

        if prefix:
            pattern = rf"({re.escape(prefix)}[A-Za-z0-9_-]+)"
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1)

            return None

        for entity_prefix in [
            "COMPANY-",
            "SERVICE-",
            "RES-",
            "REQ-",
        ]:
            pattern = rf"({re.escape(entity_prefix)}[A-Za-z0-9_-]+)"
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1)

        if ":" in text:
            return text.split(":")[-1]

        return text

    @classmethod
    def _element_value(cls, element):
        if element is None:
            return None

        if not isinstance(element, dict):
            return element

        model_type = cls._model_type(element)
        value = element.get("value")

        if model_type == "MultiLanguageProperty":
            return cls._multilingual(value)

        if model_type == "ReferenceElement":
            return cls._reference_value(value)

        if model_type == "Property":
            return value

        if model_type == "Capability":
            return cls._reference_value(element.get("semanticId", {}))

        return value

    @classmethod
    def _value(cls, container, id_short, default=None):
        element = cls._find(container, id_short)

        if element is None:
            return default

        value = cls._element_value(element)

        if value in (None, ""):
            return default

        return value

    @classmethod
    def _float(cls, container, id_short, default=None):
        value = cls._value(container, id_short)

        if value in (None, ""):
            return default

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _bool(cls, container, id_short, default=False):
        value = cls._value(container, id_short)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() == "true"

        return default

    @classmethod
    def _company_id(cls, submodel):
        return cls._normalize_entity_id(
            submodel.get("id"),
            "COMPANY-",
        )

    @classmethod
    def _service_id(cls, submodel):
        return cls._normalize_entity_id(
            submodel.get("id"),
            "SERVICE-",
        )

    @classmethod
    def _resource_id(cls, submodel):
        return cls._normalize_entity_id(
            submodel.get("id"),
            "RES-",
        )

    @classmethod
    def _requirement_id(cls, submodel):
        return cls._normalize_entity_id(
            submodel.get("id"),
            "REQ-",
        )

    @classmethod
    def _capability_semantic_id(cls, submodel):
        capability = None

        def walk(element):
            nonlocal capability

            if capability is not None:
                return

            if isinstance(element, list):
                for item in element:
                    walk(item)
                return

            if not isinstance(element, dict):
                return

            if cls._model_type(element) == "Capability":
                capability = cls._reference_value(
                    element.get("semanticId")
                )
                return

            for child in cls._children(element):
                walk(child)

        walk(submodel)
        return capability

    def _parse_companies(self, submodels):
        company_map = {}

        for submodel in submodels:
            if submodel.get("idShort") != "CompanyData":
                continue

            company_id = self._company_id(submodel)

            if not company_id:
                continue

            company_map[company_id] = {
                "company_id": company_id,
                "name": (
                    self._value(submodel, "CompanyName")
                    or company_id
                ),
                "description": self._value(
                    submodel,
                    "CompanyDescription",
                ),
                "location": None,
                "city": None,
                "state": None,
                "country": None,
                "role": (
                    "Requesting Company"
                    if company_id == "COMPANY-004"
                    else "Provider"
                ),
            }

        for submodel in submodels:
            if submodel.get("idShort") != "ContactInformations":
                continue

            company_id = self._company_id(submodel)

            if not company_id:
                continue

            if company_id not in company_map:
                company_map[company_id] = {
                    "company_id": company_id,
                    "name": company_id,
                    "location": None,
                    "city": None,
                    "state": None,
                    "country": None,
                    "role": (
                        "Requesting Company"
                        if company_id == "COMPANY-004"
                        else "Provider"
                    ),
                }

            city = (
                self._value(submodel, "CityTown")
                or self._value(submodel, "Citytown")
            )
            state = (
                self._value(submodel, "StateCounty")
                or self._value(submodel, "Statecounty")
            )
            country = self._value(submodel, "NationalCode")

            company_map[company_id].update(
                {
                    "city": city,
                    "state": state,
                    "country": country,
                    "location": city,
                }
            )

        return list(company_map.values())

    def _service_capabilities(self, submodels):
        result = {}

        for submodel in submodels:
            if submodel.get("idShort") != "CapabilityDescription":
                continue

            service_id = self._service_id(submodel)

            if not service_id:
                continue

            result[service_id] = self._capability_semantic_id(submodel)

        return result

    def _supporting_resources(self, service_submodel):
        result = []
        container = self._find(
            service_submodel,
            "SupportingResources",
        )

        if not container:
            return result

        def walk(element):
            if isinstance(element, list):
                for item in element:
                    walk(item)
                return

            if not isinstance(element, dict):
                return

            if self._model_type(element) == "ReferenceElement":
                reference = self._reference_value(
                    element.get("value")
                )
                resource_id = self._normalize_entity_id(
                    reference,
                    "RES-",
                )

                if resource_id and resource_id not in result:
                    result.append(resource_id)

            for child in self._children(element):
                walk(child)

        walk(container)
        return result

    def _parse_services(self, submodels):
        capability_map = self._service_capabilities(submodels)
        services = []

        for submodel in submodels:
            if submodel.get("idShort") != "SmartRegionServiceOffering":
                continue

            service_id = (
                self._value(submodel, "ServiceId")
                or self._service_id(submodel)
            )

            if not service_id:
                continue

            provider_element = self._find(
                submodel,
                "ProviderAASReference",
            )
            provider_reference = self._element_value(provider_element)
            provider_company_id = self._normalize_entity_id(
                provider_reference,
                "COMPANY-",
            )

            services.append(
                {
                    "service_id": service_id,
                    "name": (
                        self._value(submodel, "ServiceName")
                        or service_id
                    ),
                    "category": self._value(
                        submodel,
                        "ServiceCategory",
                    ),
                    "provider_company_id": provider_company_id,
                    "provider_reference": provider_reference,
                    "capability_semantic_id": capability_map.get(
                        service_id
                    ),
                    "origin_area": self._value(
                        submodel,
                        "OriginArea",
                    ),
                    "destination_area": self._value(
                        submodel,
                        "DestinationArea",
                    ),
                    "maximum_service_distance": self._float(
                        submodel,
                        "MaximumServiceDistance",
                    ),
                    "distance_unit": self._value(
                        submodel,
                        "DistanceUnit",
                    ),
                    "pricing_model": self._value(
                        submodel,
                        "PricingModel",
                    ),
                    "base_price": self._float(
                        submodel,
                        "BasePrice",
                    ),
                    "price_per_distance": self._float(
                        submodel,
                        "PricePerDistance",
                    ),
                    "currency": self._value(
                        submodel,
                        "Currency",
                    ),
                    "supporting_resources": self._supporting_resources(
                        submodel
                    ),
                    "service_status": self._value(
                        submodel,
                        "ServiceStatus",
                    ),
                    "last_updated": self._value(
                        submodel,
                        "LastUpdated",
                    ),
                }
            )

        return services

    @staticmethod
    def _new_resource(resource_id):
        return {
            "resource_id": resource_id,
            "name": resource_id,
            "resource_type": None,
            "product_family": None,
            "provider_company_id": None,
            "location": None,
            "city": None,
            "state": None,
            "country": None,
            "capability_semantic_id": None,
            "availability_status": None,
            "operational_status": None,
            "reservation_status": None,
            "available_capacity": None,
            "total_capacity": None,
            "reserved_capacity": None,
            "capacity_unit": None,
            "capacity_type_reference": None,
            "availability_windows": [],
            "technical_properties": {},
        }

    def _parse_resources(self, submodels, services):
        resource_map = {}

        for service in services:
            for raw_resource_id in service.get(
                "supporting_resources",
                [],
            ):
                resource_id = self._normalize_entity_id(
                    raw_resource_id,
                    "RES-",
                )

                if not resource_id:
                    continue

                if resource_id not in resource_map:
                    resource_map[resource_id] = self._new_resource(
                        resource_id
                    )

                resource_map[resource_id]["provider_company_id"] = (
                    service.get("provider_company_id")
                )

        for submodel in submodels:
            resource_id = self._resource_id(submodel)

            if not resource_id:
                continue

            if resource_id not in resource_map:
                resource_map[resource_id] = self._new_resource(
                    resource_id
                )

        for submodel in submodels:
            if submodel.get("idShort") != "Nameplate":
                continue

            resource_id = self._resource_id(submodel)

            if not resource_id or resource_id not in resource_map:
                continue

            resource_map[resource_id].update(
                {
                    "name": (
                        self._value(
                            submodel,
                            "ManufacturerProductDesignation",
                        )
                        or resource_id
                    ),
                    "resource_type": self._value(
                        submodel,
                        "ManufacturerProductType",
                    ),
                    "product_family": self._value(
                        submodel,
                        "ManufacturerProductFamily",
                    ),
                }
            )

        for submodel in submodels:
            if submodel.get("idShort") != "AssetLocation":
                continue

            resource_id = self._resource_id(submodel)

            if not resource_id or resource_id not in resource_map:
                continue

            city = (
                self._value(submodel, "CityTown")
                or self._value(submodel, "Citytown")
            )
            state = (
                self._value(submodel, "StateCounty")
                or self._value(submodel, "Statecounty")
            )
            country = self._value(submodel, "NationalCode")

            resource_map[resource_id].update(
                {
                    "location": city,
                    "city": city,
                    "state": state,
                    "country": country,
                }
            )

        for submodel in submodels:
            if submodel.get("idShort") != "CapabilityDescription":
                continue

            resource_id = self._resource_id(submodel)

            if not resource_id or resource_id not in resource_map:
                continue

            resource_map[resource_id]["capability_semantic_id"] = (
                self._capability_semantic_id(submodel)
            )

        for submodel in submodels:
            if (
                submodel.get("idShort")
                != "SmartRegionResourceAvailability"
            ):
                continue

            resource_id = self._resource_id(submodel)

            if not resource_id or resource_id not in resource_map:
                continue

            windows = []
            windows_container = self._find(
                submodel,
                "AvailabilityWindows",
            )

            if windows_container:
                for item in self._children(windows_container):
                    windows.append(
                        {
                            "available_from": self._value(
                                item,
                                "AvailableFrom",
                            ),
                            "available_until": self._value(
                                item,
                                "AvailableUntil",
                            ),
                        }
                    )

            resource_map[resource_id].update(
                {
                    "availability_status": self._value(
                        submodel,
                        "AvailabilityStatus",
                    ),
                    "operational_status": self._value(
                        submodel,
                        "OperationalStatus",
                    ),
                    "reservation_status": self._value(
                        submodel,
                        "ReservationStatus",
                    ),
                    "available_capacity": self._float(
                        submodel,
                        "AvailableCapacity",
                    ),
                    "total_capacity": self._float(
                        submodel,
                        "TotalCapacity",
                    ),
                    "reserved_capacity": self._float(
                        submodel,
                        "ReservedCapacity",
                    ),
                    "capacity_unit": self._value(
                        submodel,
                        "CapacityUnit",
                    ),
                    "capacity_type_reference": self._value(
                        submodel,
                        "CapacityTypeReference",
                    ),
                    "availability_windows": windows,
                    "last_updated": self._value(
                        submodel,
                        "LastUpdated",
                    ),
                }
            )

        for submodel in submodels:
            if submodel.get("idShort") != "TechnicalData":
                continue

            resource_id = self._resource_id(submodel)

            if not resource_id or resource_id not in resource_map:
                continue

            technical = {}

            for field in [
                "MaximumPayload",
                "CargoVolume",
                "MinimumTemperature",
                "MaximumTemperature",
                "TotalFloorArea",
                "MaximumLiftingCapacity",
            ]:
                value = self._value(submodel, field)

                if value is None:
                    continue

                try:
                    value = float(value)
                except (TypeError, ValueError):
                    pass

                technical[field] = value

            resource_map[resource_id]["technical_properties"] = technical
            resource_map[resource_id].update(
                {
                    "maximum_payload": technical.get(
                        "MaximumPayload"
                    ),
                    "cargo_volume": technical.get(
                        "CargoVolume"
                    ),
                    "minimum_temperature": technical.get(
                        "MinimumTemperature"
                    ),
                    "maximum_temperature": technical.get(
                        "MaximumTemperature"
                    ),
                    "total_floor_area": technical.get(
                        "TotalFloorArea"
                    ),
                    "maximum_lifting_capacity": technical.get(
                        "MaximumLiftingCapacity"
                    ),
                }
            )

        for service in services:
            provider_id = service.get("provider_company_id")

            for raw_resource_id in service.get(
                "supporting_resources",
                [],
            ):
                resource_id = self._normalize_entity_id(
                    raw_resource_id,
                    "RES-",
                )

                if resource_id in resource_map:
                    resource_map[resource_id][
                        "provider_company_id"
                    ] = provider_id

        resources = [
            resource
            for resource_id, resource in resource_map.items()
            if str(resource_id).upper().startswith("RES-")
        ]

        resources.sort(
            key=lambda item: item.get("resource_id", "")
        )

        return resources

    def _requirement_capabilities(self, submodels):
        result = {}

        for submodel in submodels:
            if submodel.get("idShort") != "CapabilityDescription":
                continue

            requirement_id = self._requirement_id(submodel)

            if not requirement_id:
                continue

            result[requirement_id] = self._capability_semantic_id(
                submodel
            )

        return result

    def _evaluation_policies(self, submodels):
        policies = {}

        for submodel in submodels:
            if (
                submodel.get("idShort")
                != "SmartRegionEvaluationPolicy"
            ):
                continue

            requirement_id = self._requirement_id(submodel)

            if not requirement_id:
                continue

            criteria = []
            criteria_container = self._find(
                submodel,
                "EvaluationCriteria",
            )

            if criteria_container:
                for item in self._children(criteria_container):
                    criteria.append(
                        {
                            "criterion_id": (
                                self._value(
                                    item,
                                    "CriterionId",
                                )
                                or self._value(
                                    item,
                                    "CriterionID",
                                )
                            ),
                            "criterion_type": self._value(
                                item,
                                "CriterionType",
                            ),
                            "weight": self._float(
                                item,
                                "Weight",
                                0.0,
                            ),
                            "preference_direction": self._value(
                                item,
                                "PreferenceDirection",
                            ),
                            "enabled": self._bool(
                                item,
                                "Enabled",
                                True,
                            ),
                        }
                    )

            policies[requirement_id] = {
                "ranking_enabled": self._bool(
                    submodel,
                    "RankingEnabled",
                    True,
                ),
                "ranking_method": self._value(
                    submodel,
                    "RankingMethod",
                ),
                "normalize_weights": self._bool(
                    submodel,
                    "NormalizeWeights",
                    True,
                ),
                "criteria": criteria,
            }

        return policies

    def _parse_requirements(self, submodels):
        capability_map = self._requirement_capabilities(submodels)
        policy_map = self._evaluation_policies(submodels)
        requirements = []

        for submodel in submodels:
            if submodel.get("idShort") != "SmartRegionRequirement":
                continue

            requirement_id = (
                self._value(submodel, "RequirementId")
                or self._requirement_id(submodel)
            )

            if not requirement_id:
                continue

            requester_element = self._find(
                submodel,
                "RequestingCompanyAASReference",
            )
            requester_reference = self._element_value(
                requester_element
            )
            requesting_company = self._normalize_entity_id(
                requester_reference,
                "COMPANY-",
            )

            capacity_container = self._find(
                submodel,
                "CapacityRequirements",
            )

            required_capacity = None
            capacity_unit = None
            capacity_operator = None
            capacity_mandatory = None
            capacity_type_reference = None

            if capacity_container:
                capacity_items = self._children(capacity_container)

                if capacity_items:
                    first = capacity_items[0]

                    required_capacity = self._float(
                        first,
                        "RequiredValue",
                    )
                    capacity_unit = self._value(
                        first,
                        "Unit",
                    )
                    capacity_operator = self._value(
                        first,
                        "Operator",
                    )
                    capacity_mandatory = self._bool(
                        first,
                        "Mandatory",
                        True,
                    )

                    capacity_type_element = self._find(
                        first,
                        "CapacityTypeReference",
                    )
                    capacity_type_reference = self._element_value(
                        capacity_type_element
                    )

            technical_constraints = []
            technical_container = self._find(
                submodel,
                "TechnicalConstraints",
            )

            if technical_container:
                for item in self._children(technical_container):
                    property_reference_element = self._find(
                        item,
                        "PropertyReference",
                    )
                    property_reference = self._element_value(
                        property_reference_element
                    )

                    technical_constraints.append(
                        {
                            "property_reference": property_reference,
                            "property": self._normalize_entity_id(
                                property_reference
                            ),
                            "operator": self._value(
                                item,
                                "Operator",
                            ),
                            "required_value": self._value(
                                item,
                                "RequiredValue",
                            ),
                            "unit": self._value(
                                item,
                                "Unit",
                            ),
                            "mandatory": self._bool(
                                item,
                                "Mandatory",
                                True,
                            ),
                        }
                    )

            requirements.append(
                {
                    "requirement_id": requirement_id,
                    "title": (
                        self._value(
                            submodel,
                            "RequirementTitle",
                        )
                        or requirement_id
                    ),
                    "requesting_company": requesting_company,
                    "requesting_company_reference": requester_reference,
                    "requirement_type": self._value(
                        submodel,
                        "RequirementType",
                    ),
                    "service_category": self._value(
                        submodel,
                        "ServiceCategory",
                    ),
                    "resource_type": self._value(
                        submodel,
                        "ResourceType",
                    ),
                    "origin": self._value(
                        submodel,
                        "Origin",
                    ),
                    "destination": self._value(
                        submodel,
                        "Destination",
                    ),
                    "required_location": self._value(
                        submodel,
                        "RequiredLocation",
                    ),
                    "required_from": self._value(
                        submodel,
                        "RequiredFrom",
                    ),
                    "required_until": self._value(
                        submodel,
                        "RequiredUntil",
                    ),
                    "required_capacity": required_capacity,
                    "capacity_unit": capacity_unit,
                    "capacity_operator": capacity_operator,
                    "capacity_mandatory": capacity_mandatory,
                    "capacity_type_reference": capacity_type_reference,
                    "technical_constraints": technical_constraints,
                    "maximum_price": self._float(
                        submodel,
                        "MaximumPrice",
                    ),
                    "priority": self._value(
                        submodel,
                        "RequirementPriority",
                    ),
                    "status": self._value(
                        submodel,
                        "RequirementStatus",
                    ),
                    "capability_semantic_id": capability_map.get(
                        requirement_id
                    ),
                    "evaluation_policy": policy_map.get(
                        requirement_id,
                        {},
                    ),
                }
            )

        return requirements

    def load_smartregion_repository(self):
        shells = self.get_shells()
        submodels = self.get_submodels()

        companies = self._parse_companies(submodels)
        services = self._parse_services(submodels)
        resources = self._parse_resources(
            submodels,
            services,
        )
        requirements = self._parse_requirements(submodels)

        return {
            "connected": True,
            "endpoint": self.base_url,
            "aas_count": len(shells),
            "shells": shells,
            "submodels": submodels,
            "companies": companies,
            "services": services,
            "resources": resources,
            "requirements": requirements,
        }
