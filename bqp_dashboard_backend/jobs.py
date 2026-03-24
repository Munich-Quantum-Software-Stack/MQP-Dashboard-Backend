from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from http import HTTPStatus
import bqp_database_access as database
from eliot import log_call


BLUEPRINT = Blueprint("jobs", __name__)


@BLUEPRINT.get("/jobs")
@jwt_required()
@log_call
def fetch_all_jobs():
    """
    Return a paginated list of jobs for the current user.

    Args:
        page (int): Page number of results.
        jobs_per_page (int): Number of jobs per page.
        order (str): Sort order, "ASC" or "DESC".
        order_by (str): Field to order by. "ID" or any field name form the quantum database, e.g. timestamp_submitted.
        filter (str): String of the filter to be applied (setting CANELLED will yield only jobs with the CANCELLED status)

    Returns:
        dict: Jobs in the requested range and total number of jobs.
    """
    page_nr = request.args.get("p")
    if not page_nr:
        page_nr = 0
    else:
        page_nr = int(page_nr)

    jpp = request.args.get("jpp")
    if not jpp:
        jpp = 20
    else:
        jpp = int(jpp)

    order = request.args.get("order")
    if not order:
        order = "ASC"

    order_by = request.args.get("order_by")

    if not order_by:
        order_by = "ID"

    filter_query = request.args.get("filter")

    identity = get_jwt_identity()
    query = database.jobs.fetch_by_identity_pages(
        identity=identity,
        page=page_nr,
        jobs_per_page=jpp,
        order=order,
        order_by=order_by,
        filter_query=filter_query,
    )
    jobs, totaljob_nr = query["jobs"], query["totaljob_nr"]
    sanitized_jobs = [job.to_dict() for job in jobs]
    return {"jobs": sanitized_jobs, "totaljob_nr": totaljob_nr}, HTTPStatus.OK


@BLUEPRINT.get("/jobs/<id>")
@jwt_required()
@log_call
def fetch_job(id=0):
    """Fetch all jobs belonging to a user."""
    identity = get_jwt_identity()
    jobs = database.jobs.fetch_by_identity(identity)

    sanitized_jobs = [job.to_dict() for job in jobs]

    job = None
    for jobItem in sanitized_jobs:
        if jobItem.get("id") == int(id):
            job = jobItem

    return {"job": job}, HTTPStatus.OK
