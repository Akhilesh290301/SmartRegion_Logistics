import os

import streamlit as st

from basyx_client import BasyxClient


def get_basyx_base_url():
    env_url = os.getenv("BASYX_BASE_URL")

    if env_url:
        return env_url.rstrip("/")

    try:
        secret_url = st.secrets.get("BASYX_BASE_URL")

        if secret_url:
            return str(secret_url).rstrip("/")
    except Exception:
        pass

    return "http://localhost:8081"


BASYX_BASE_URL = get_basyx_base_url()
_client = BasyxClient(base_url=BASYX_BASE_URL)


def empty_repository():
    return {
        "connected": False,
        "endpoint": BASYX_BASE_URL,
        "aas_count": 0,
        "shells": [],
        "submodels": [],
        "companies": [],
        "services": [],
        "resources": [],
        "requirements": [],
        "error": None,
    }


@st.cache_data(ttl=60, show_spinner=False)
def load_repository():
    try:
        repository = _client.load_smartregion_repository()

        repository.setdefault("connected", True)
        repository.setdefault("endpoint", BASYX_BASE_URL)
        repository.setdefault("aas_count", 0)
        repository.setdefault("shells", [])
        repository.setdefault("submodels", [])
        repository.setdefault("companies", [])
        repository.setdefault("services", [])
        repository.setdefault("resources", [])
        repository.setdefault("requirements", [])
        repository.setdefault("error", None)

        return repository

    except Exception as exc:
        repository = empty_repository()
        repository["error"] = str(exc)
        return repository


def refresh_repository():
    load_repository.clear()
    return load_repository()


def get_repository_summary(repository):
    if not repository:
        repository = empty_repository()

    return {
        "connected": bool(repository.get("connected")),
        "endpoint": repository.get(
            "endpoint",
            BASYX_BASE_URL,
        ),
        "aas_count": repository.get(
            "aas_count",
            len(repository.get("shells", [])),
        ),
        "company_count": len(
            repository.get("companies", [])
        ),
        "service_count": len(
            repository.get("services", [])
        ),
        "resource_count": len(
            repository.get("resources", [])
        ),
        "requirement_count": len(
            repository.get("requirements", [])
        ),
        "error": repository.get("error"),
    }


def get_companies(repository):
    if not repository:
        return []

    return repository.get("companies", [])


def get_services(repository):
    if not repository:
        return []

    return repository.get("services", [])


def get_resources(repository):
    if not repository:
        return []

    return repository.get("resources", [])


def get_requirements(repository):
    if not repository:
        return []

    return repository.get("requirements", [])


def get_company(repository, company_id):
    return next(
        (
            company
            for company in get_companies(repository)
            if company.get("company_id") == company_id
        ),
        None,
    )


def get_service(repository, service_id):
    return next(
        (
            service
            for service in get_services(repository)
            if service.get("service_id") == service_id
        ),
        None,
    )


def get_resource(repository, resource_id):
    return next(
        (
            resource
            for resource in get_resources(repository)
            if resource.get("resource_id") == resource_id
        ),
        None,
    )


def get_requirement(repository, requirement_id):
    return next(
        (
            requirement
            for requirement in get_requirements(repository)
            if requirement.get("requirement_id") == requirement_id
        ),
        None,
    )
