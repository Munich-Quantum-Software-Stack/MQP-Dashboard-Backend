import secrets
import string
from datetime import datetime, timedelta
from http import HTTPStatus

import bqp_database_access as database
from bqp_database_access.tokens import (
    TokenExistsError,
    TokenExpirationAfterMaximum,
    TokenExpirationBeforeNow,
    TokenNotFound,
    TooManyTokensError,
)
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

blueprint = Blueprint("tokens", __name__)


def generate_token() -> str:
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
    )


@blueprint.post("/tokens")
@jwt_required()
def create_token():
    """Create a token with given token data."""

    request_data = request.get_json()

    user_token = get_jwt_identity()
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
            "token_data": {
                "token_value": token,
                "token_name": remember_name,
                "token_expiration": expiration.isoformat(),
            }
        }, HTTPStatus.OK

    except TooManyTokensError as error:
        return {
            "error_message": "Too many tokens alive.",
        }, HTTPStatus.FORBIDDEN

    except TokenExpirationBeforeNow as error:
        return {
            "error_message": "Token expiration before now.",
        }, HTTPStatus.FORBIDDEN

    except TokenExpirationAfterMaximum as error:
        return {
            "error_message": "Token expiration beyond user limit.",
        }, HTTPStatus.FORBIDDEN
    except TokenExistsError as error:
        return {
            "error_message": f"Token {request_data['token_name']} already exists.",
        }


@blueprint.get("/tokens")
@jwt_required()
def get_all_tokens():
    """Get all tokens that belong to user."""

    identity = get_jwt_identity()
    tokens = database.tokens.fetch_active_tokens_of_identity(identity)

    sanitized_tokens = [
        {
            "token_name": token.remember_name,
            "revoked": token.revoked,
            "revoke_reason": token.revoke_reason,
            "token_expiration": token.expiration.isoformat(),
        }
        for token in tokens
    ]

    # print("tokens: ", sanitized_tokens)

    return {
        "tokens": sanitized_tokens,
    }, HTTPStatus.OK


@blueprint.get("/tokens/user_limits")
@jwt_required()
def get_user_token_creation_limits():
    """Fetch the user security level limits."""

    identity = get_jwt_identity()

    user = database.users.fetch_user_by_identity(identity)

    security_level = user.security_level

    return {
        "max_lifetime": security_level.token_max_lifetime,
        "max_jobs": security_level.token_max_jobs,
        "max_budget": security_level.token_max_budget,
    }


@blueprint.delete("/tokens")
@jwt_required()
def revoke_token():
    """Revoke given token and owner combination."""

    request_data = request.get_json()
    identity = get_jwt_identity()

    try:
        database.tokens.revoke_token_by_name_and_identity(
            request_data["token_name"], identity
        )

        return {"message": f"Revoked {request_data['token_name']}."}, HTTPStatus.OK

    except TokenNotFound as error:
        return {"error_message": "Token not found."}, HTTPStatus.BAD_REQUEST
