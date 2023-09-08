from flask import current_app, Blueprint, request

import string
import os
import secrets
from http import HTTPStatus
from hashlib import md5
from datetime import datetime, timedelta

import bqp_database_access as database
from bqp_database_access.users import UnknownIdentityError
from bqp_database_access.tokens import (
    TooManyTokensError,
    TokenExistsError,
    TokenExpirationBeforeNow,
    TokenNotFound,
    TokenExpirationAfterMaximum,
)


def generate_token() -> str:
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
    )


backend = Blueprint("backend", __name__)


@backend.post("/login")
def login_user():
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
            "user_token": user.identity,
            "force_secret_reset": user.force_secret_reset,
        }


@backend.post("/tokens")
def create_token():
    """Create a token with given token data."""

    request_data = request.get_json()

    user_token = request_data["user_token"]
    remember_name = request_data["token_name"]

    expiration = datetime.combine(
        datetime.now().date() + timedelta(days=int(request_data["validity"])),
        datetime.max.time(),
    )

    token = generate_token()

    try:
        database.tokens.add_new_token(
            remember_name,
            user_token,
            token,
            expiration,
            request_data["max_nb_jobs"],
            request_data["max_budget"],
        )

        return {
            "status": HTTPStatus.OK,
            "token_data": {
                "token_value": token,
                "token_name": remember_name,
                "token_expiration": expiration.isoformat(),
            },
        }

    except TooManyTokensError as error:
        return {
            "status": HTTPStatus.FORBIDDEN,
            "error_message": "Too many tokens alive.",
        }

    except TokenExpirationBeforeNow as error:
        return {
            "status": HTTPStatus.FORBIDDEN,
            "error_message": "Token expiration before now.",
        }

    except TokenExpirationAfterMaximum as error:
        return {
            "status": HTTPStatus.FORBIDDEN,
            "error_message": "Token expiration beyond user limit.",
        }


@backend.get("/tokens")
def get_all_tokens():
    """Get all tokens that belong to user."""

    request_data = request.get_json()

    identity = request_data["user_token"]

    tokens = database.tokens.fetch_active_tokens_of_identity(identity)

    sanitized_tokens = [
        {
            "token_name": token.remember_name,
            "token_expiration": token.expiration.isoformat(),
        }
        for token in tokens
    ]

    return {
        "status": HTTPStatus.OK,
        "tokens": sanitized_tokens,
    }


@backend.delete("/tokens")
def revoke_token():
    """Revoke given token and owner combination."""

    request_data = request.get_json()

    try:
        database.tokens.revoke_token_by_name_and_identity(
            request_data["token_name"], request_data["token_owner"]
        )

        return {"status": HTTPStatus.OK}

    except TokenNotFound as error:
        return {"status": HTTPStatus.BAD_REQUEST}


@backend.get("/jobs")
def fetch_all_jobs():
    """Fetch all jobs belonging to a user."""

    request_data = request.get_json()

    jobs = database.jobs.fetch_by_identity(request_data["user_token"])

    sanitized_jobs = [job.to_dict() for job in jobs]

    return {"status": HTTPStatus.OK, "jobs": sanitized_jobs}
