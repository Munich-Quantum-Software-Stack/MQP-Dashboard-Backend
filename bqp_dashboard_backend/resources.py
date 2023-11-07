from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from http import HTTPStatus


import bqp_database_access as database


blueprint = Blueprint("resources", __name__)


@blueprint.get("/resources")
@jwt_required()
def fetch_all_resources():
    """Fetch all jobs belonging to a user."""

    identity = get_jwt_identity()
    resources = database.resources.fetch_resources_available_to_identity(identity)

    sanitized_resources = [resource.to_dict() for resource in resources]

    return {"resources": sanitized_resources}, HTTPStatus.OK
