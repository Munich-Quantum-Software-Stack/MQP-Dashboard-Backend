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
    try:
        available_resources = database.resources.fetch_resources_available_to_identity(identity)
        sanitized_available_resources = [resource.to_dict() for resource in available_resources]
        resources = database.resources.fetch_all_resources()
        sanitized_resources = [resource.to_dict() for resource in resources]
        #restricted_resources = database.fetch_resources_restricted_to_identity(identity)
        #sanitized_restricted_resources = [resource.to_dict() for resource in restricted_resources]
        sorted_resources_by_name = sorted(sanitized_resources, key=lambda x: x["name"], reverse=False)

        return { 
            "resources": sorted_resources_by_name, 
            "available_resources": sanitized_available_resources ,
            #"restricted_resources": sanitized_restricted_resources
        }, HTTPStatus.OK
    except TypeError as error:
        return {
            "error_message": error
        }, HTTPStatus.FORBIDDEN
