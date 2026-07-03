from http import HTTPStatus
from mqp_dashboard_backend import resources


def test_fetching_all_resources(active_client) -> None:
    """Test that the authenticated resources endpoint returns all resources."""

    response = active_client.get("/resources", headers=active_client.headers)

    resource_names = [resource["name"] for resource in response.json["resources"]]

    assert response.status_code == HTTPStatus.OK
    assert set(response.json) == {
        "resources",
        "available_resources",
        "restricted_resource_names",
    }
    assert resource_names == sorted(resource_names)
    assert resource_names == ["TEST_QPU_1", "TEST_QPU_2"]


def test_available_resources_are_sorted_and_part_of_all_resources(
    active_client,
) -> None:
    """Test that available resources are sorted and match accessible fixtures."""

    response = active_client.get("/resources", headers=active_client.headers)

    available_resource_names = [
        resource["name"] for resource in response.json["available_resources"]
    ]
    resource_names = {resource["name"] for resource in response.json["resources"]}

    assert response.status_code == HTTPStatus.OK
    assert available_resource_names == sorted(available_resource_names)
    assert set(available_resource_names).issubset(resource_names)
    assert available_resource_names == ["TEST_QPU_1", "TEST_QPU_2"]


def test_fetching_resources_reports_restricted_names(active_client) -> None:
    """Test that restricted resource names are exposed in the response."""

    response = active_client.get("/resources", headers=active_client.headers)

    restricted_resource_names = response.json["restricted_resource_names"]
    available_resource_names = {
        resource["name"] for resource in response.json["available_resources"]
    }

    assert response.status_code == HTTPStatus.OK
    assert isinstance(restricted_resource_names, list)
    assert all(isinstance(name, str) for name in restricted_resource_names)
    assert available_resource_names.isdisjoint(restricted_resource_names)


def test_fetching_resources_requires_authentication(inactive_client) -> None:
    """Test that anonymous users cannot fetch resources."""

    response = inactive_client.get("/resources")

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_fetching_resources_returns_forbidden_for_database_type_error(
    active_client, monkeypatch
) -> None:
    """Test the endpoint response when the database rejects the identity."""

    def raise_type_error(identity):
        raise TypeError(f"invalid identity: {identity}")

    monkeypatch.setattr(
        resources.database.resources,
        "fetch_resources_available_to_identity",
        raise_type_error,
    )

    response = active_client.get("/resources", headers=active_client.headers)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json == {"error_message": "invalid identity: test_user"}
