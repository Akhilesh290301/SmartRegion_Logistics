from basyx_client import BasyxClient


BASYX_URL = "http://localhost:8081"


def load_repository():

    client = BasyxClient(
        base_url=BASYX_URL
    )

    try:

        repository = (
            client.load_smartregion_repository()
        )

        repository["connected"] = True
        repository["endpoint"] = BASYX_URL

        return repository

    except Exception as error:

        print(
            "BaSyx repository error:",
            error
        )

        return {
            "connected": False,
            "endpoint": BASYX_URL,
            "aas_count": 0,
            "shells": [],
            "submodels": [],
            "companies": [],
            "services": [],
            "resources": [],
            "requirements": []
        }


def get_companies(repository):
    return repository.get(
        "companies",
        []
    )


def get_services(repository):
    return repository.get(
        "services",
        []
    )


def get_resources(repository):
    return repository.get(
        "resources",
        []
    )


def get_requirements(repository):
    return repository.get(
        "requirements",
        []
    )


def get_repository_summary(repository):

    return {
        "connected":
            repository.get(
                "connected",
                False
            ),

        "endpoint":
            repository.get(
                "endpoint",
                BASYX_URL
            ),

        "aas_count":
            repository.get(
                "aas_count",
                0
            ),

        "company_count":
            len(
                get_companies(
                    repository
                )
            ),

        "service_count":
            len(
                get_services(
                    repository
                )
            ),

        "resource_count":
            len(
                get_resources(
                    repository
                )
            ),

        "requirement_count":
            len(
                get_requirements(
                    repository
                )
            )
    }