from http import HTTPStatus


def test_fetch_all_jobs(active_client) -> None:
    """Test if all jobs are fetched associated with a user."""

    response = active_client.get("/jobs", headers=active_client.headers)
    assert (
        response.status_code == HTTPStatus.OK
        and response.json["jobs"]
        and response.json["totaljob_nr"] == 3
    )


def test_fetch_all_jobs_ASC(active_client) -> None:
    """Test if all jobs are fetched associated with a user."""

    response = active_client.get(
        "/jobs?p=0&jpp=20&order=ASC&order_by=ID&filter=COMPLETED",
        headers=active_client.headers,
    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json["jobs"]
        and response.json["totaljob_nr"] == 1
    )


def test_fetch_all_jobs_DESC(active_client) -> None:
    """Test if all jobs are fetched associated with a user."""

    response = active_client.get(
        "/jobs?p=0&jpp=20&order=DESC&order_by=ID&filter=COMPLETED",
        headers=active_client.headers,
    )
    assert response.status_code == HTTPStatus.OK and response.json["jobs"]


def test_fetch_all_jobs_time(active_client) -> None:
    """Test if all jobs are fetched associated with a user."""

    response = active_client.get(
        "/jobs?p=0&jpp=20&order=ASC&order_by=timestamp_submitted&filter=COMPLETED",
        headers=active_client.headers,
    )
    assert response.status_code == HTTPStatus.OK and response.json["jobs"]


def test_fetch_all_jobs_cancelled(active_client) -> None:
    """Test if all jobs are fetched associated with a user."""

    response = active_client.get(
        "/jobs?p=0&jpp=20&order=ASC&order_by=ID&filter=CANCELLED",
        headers=active_client.headers,
    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json["jobs"]
        and response.json["totaljob_nr"] == 1
    )


def test_fetch_job_by_id(active_client) -> None:
    """Test if a job can be fetched by a job id."""

    response = active_client.get("/jobs/0", headers=active_client.headers)

    assert response.status_code == HTTPStatus.OK


### TODO this feature is not implemented yet, we will test for it once it is.
# def test_fetching_job_with_invalid_id(active_client) -> None:
#    """Test that fetching correctly fails with invalid id."""
#
#    raise NotImplementedError
