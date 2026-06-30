from http import HTTPStatus


def test_admin_panel_requires_jwt(inactive_client) -> None:
    response = inactive_client.get("/admin/panel")

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_admin_panel_forbidden_for_non_admin(active_client) -> None:
    response = active_client.get("/admin/panel", headers=active_client.headers)

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_admin_panel_access_for_admin(active_admin_client) -> None:
    response = active_admin_client.get(
        "/admin/panel", headers=active_admin_client.headers
    )

    assert (
        response.status_code == HTTPStatus.OK
        and response.json["redirect_to"] == "/admin/panel"
        and response.json["superuser_level"] == "ADMIN"
    )


def test_admin_group_lookup_for_ldap_user(inactive_client) -> None:
    payload = {"identity": "ldap_test_user", "secret": "ldap_test_password"}

    response = inactive_client.post("/admin/group", json=payload)

    assert response.status_code == HTTPStatus.OK and response.json["group"] == "Editor"


def test_admin_login_redirect(inactive_client) -> None:
    user_data = {"identity": "admin_test_user", "secret": "test_password"}

    response = inactive_client.post("/login", json=user_data)

    assert (
        response.status_code == HTTPStatus.OK
        and response.json["is_admin"] is True
        and response.json["redirect_to"] == "/admin/panel"
    )
