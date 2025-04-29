from http import HTTPStatus


def test_fetch_all_jobs(active_client) -> None:
    """Test if all jobs are fetched associated with a user."""

    response = active_client.get("/jobs", headers=active_client.headers)    
    assert response.status_code == HTTPStatus.OK and response.json["jobs"]


def test_fetch_job_by_id(active_client) -> None:
    """Test if a job can be fetched by a job id."""

    response = active_client.get("/jobs/0", headers=active_client.headers)
    
    assert response.status_code == HTTPStatus.OK

### TODO this feature is not implemented yet, we will test for it once it is. 
#def test_fetching_job_with_invalid_id(active_client) -> None:
#    """Test that fetching correctly fails with invalid id."""
#    
#    raise NotImplementedError
