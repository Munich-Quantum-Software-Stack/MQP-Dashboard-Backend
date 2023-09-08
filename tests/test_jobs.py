from http import HTTPStatus


def test_fetch_all_jobs(active_client) -> None:
    """Test if all jobs are fetched associated with a user."""

    user_data = {"user_token": active_client.user_token}

    response = active_client.get("/jobs", json=user_data)

    assert response.json["status"] == HTTPStatus.OK
