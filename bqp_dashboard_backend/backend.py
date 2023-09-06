from flask import current_app, Blueprint, request
import os

from http import HTTPStatus
from hashlib import md5

import bqp_database_access as database
from bqp_database_access.users import UnknownIdentityError


backend = Blueprint("backend", __name__)


@backend.post("/login")
def login():
    request_data = request.get_json()

    identity = request_data["identity"]
    secret = request_data["secret"]

    # TODO authenticate against LDAP

    try:
        if not database.users.authenticate(identity, secret):
            raise RuntimeError("failed to authenticate")

        user = database.users.fetch_user_by_identity(request_data["identity"])

        if user.blocked:
            raise RuntimeError("user is blocked")

    except Exception as error:
        # TODO log error

        return {
            "status": HTTPStatus.UNAUTHORIZED,
            "error_message": "The identity/password is not valid. Please try again!",
        }

    else:
        return {
            "status": HTTPStatus.OK,
            "user_token": user.email,  # TODO change with data-model-v2
            "force_secret_reset": user.force_secret_reset,
        }
