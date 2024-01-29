from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity

from http import HTTPStatus
import bqp_database_access as database


blueprint = Blueprint("jobs", __name__)


@blueprint.get("/jobs")
@jwt_required()
def fetch_all_jobs():
    """Fetch all jobs belonging to a user."""

    identity = get_jwt_identity()
    jobs = database.jobs.fetch_by_identity(identity)

    sanitized_jobs = [job.to_dict() for job in jobs]
    sorted_jobs_by_id = sorted(sanitized_jobs, key=lambda x: x[1], reverse=True)
    return {"jobs": sorted_jobs_by_id}, HTTPStatus.OK


@blueprint.get("/jobs/<id>")
@jwt_required()
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
