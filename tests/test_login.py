from http import HTTPStatus
import ldap


def test_ldap_access(app) -> None:
    """Test whether the LDAP server is reachable."""

    user_dn = "cn=ldap_test_user,ou=QuantumComputing,ou=Kennungen,o=lrz-muenchen,c=de"
    secret = "ldap_test_password"

    connection = ldap.initialize("ldap://localhost:8888")
    connection.protocol_version = ldap.VERSION3
    connection.set_option(ldap.OPT_REFERRALS, 0)

    auth_user = connection.simple_bind_s(user_dn, secret)

    assert auth_user

    connection.unbind_s()


# temporarily
def test_correct_login(inactive_client) -> None:
    """Test whether a normal login works."""

    user_data = {"identity": "test_user", "secret": "test_password"}

    response = inactive_client.post("/login", json=user_data)

    assert (
        response.status_code == HTTPStatus.OK
        and response.json["access_token"] is not None
        and response.json["force_secret_reset"] is not None
    )


def test_login_with_non_existing_user(inactive_client) -> None:
    """Test whether login with a non-existing user correctly fails."""

    user_data = {"identity": "non_existing_user", "secret": "test_password"}

    response = inactive_client.post("/login", json=user_data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_with_wrong_password(inactive_client) -> None:
    """Test whether login with a wrong password correctly fails."""

    user_data = {"identity": "test_user", "secret": "wrong_password"}

    response = inactive_client.post("/login", json=user_data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_with_blocked_user(inactive_client) -> None:
    """Test whether login with a blocked user correctly fails."""

    user_data = {"identity": "blocked_test_user", "secret": "test_password"}

    response = inactive_client.post("/login", json=user_data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_ldap_login_user(inactive_client):
    """Test whether a LDAP marked user can log in."""

    user_data = {"identity": "ldap_test_user", "secret": "ldap_test_password"}

    response = inactive_client.post("/login", json=user_data)
    assert (
        response.status_code == HTTPStatus.OK
        and response.json["access_token"] is not None
        and response.json["force_secret_reset"] is not None
    )
