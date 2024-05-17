from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from http import HTTPStatus
from eliot import log_call


import bqp_database_access as database


BLUEPRINT = Blueprint("resources", __name__)


@BLUEPRINT.get("/resources")
@jwt_required()
@log_call
def fetch_all_resources():
    """Fetch all jobs belonging to a user."""

    identity = get_jwt_identity()
    #resources = database.resources.fetch_resources_available_to_identity(identity)
    resources = database.resources.fetch_all_resources()
    sanitized_resources = [resource.to_dict() for resource in resources]

    return {"resources": sanitized_resources}, HTTPStatus.OK
