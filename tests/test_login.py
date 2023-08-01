from http import HTTPStatus


def test_correct_login(client) -> None:
    """Test whether a normal login works."""

    user_data = {"identity": "test_user", "secret": "test_password"}

    response = client.post("/login", json=user_data)

    assert (
        response.json["status"] == HTTPStatus.OK
        and response.json["user_token"]
        and response.json["force_secret_reset"] is not None
    )


def test_login_with_non_existing_user(client) -> None:
    """Test whether login with a non-existing user correctly fails."""

    user_data = {"identity": "non_existing_user", "secret": "test_password"}

    response = client.post("/login", json=user_data)

    assert response.json["status"] == HTTPStatus.UNAUTHORIZED


def test_login_with_wrong_password(client) -> None:
    """Test whether login with a wrong password correctly fails."""

    user_data = {"identity": "test_user", "secret": "wrong_password"}

    response = client.post("/login", json=user_data)

    assert response.json["status"] == HTTPStatus.UNAUTHORIZED


def test_login_with_blocked_user(client) -> None:
    """Test whether login with a blocked user correctly fails."""

    user_data = {"identity": "blocked_test_user", "secret": "test_password"}

    response = client.post("/login", json=user_data)

    assert response.json["status"] == HTTPStatus.UNAUTHORIZED
