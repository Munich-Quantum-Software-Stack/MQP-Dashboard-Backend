# ------------------------------------------------------------------------------
# Copyright 2026 Munich Quantum Software Stack Project
#
# Licensed under the Apache License, Version 2.0 with LLVM Exceptions (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://github.com/Munich-Quantum-Software-Stack/QDMI/blob/develop/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# ------------------------------------------------------------------------------

"""MQP Dashboard Tokens Module"""

import secrets
import string
from datetime import datetime, timedelta
from http import HTTPStatus
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from eliot import log_call
import bqp_database_access as database
from bqp_database_access._database import open_database
from bqp_database_access.tokens import (
    TokenExistsError,
    TokenExpirationAfterMaximum,
    TokenExpirationBeforeNow,
    TokenNotFound,
    TooManyTokensError,
)


BLUEPRINT = Blueprint("tokens", __name__)


def generate_token() -> str:
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
    )


@BLUEPRINT.post("/tokens/new")
@jwt_required()
@log_call
def create_token():
    """
    Create a token with given token data.
    Args:
        token_name (string): name of token
        validity (integer): validity time of token (day)
        max_nb_jobs (integer): maximum number of jobs for this token
        max_budget (integer): maximum budget for this token

    Returns:
        token_value: hash value of token
        token_name: remember name of token
        token_expiration: the expiration of token
    """

    request_data = request.get_json()

    user_token = get_jwt_identity()
    remember_name = request_data["token_name"]

    expiration = datetime.combine(
        datetime.now().date() + timedelta(days=int(request_data["validity"])),
        datetime.max.time(),
    )

    token = generate_token()

    quantum_db = open_database()
    user = quantum_db.User.get(identity=user_token)
    _user_group_names = [user_group.name.upper() for user_group in user.user_groups]

    try:
        if "MQP_EDU" in _user_group_names:
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
                    "token_value": "ThisIsAnEducationalTokenItCannotBeUsedToSubmitJobsThisIsAnEducat",
                    "token_name": remember_name,
                    "token_expiration": expiration.isoformat(),
                }
            }, HTTPStatus.OK
        else:
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

    except TooManyTokensError:
        return {
            "error_message": "Too many tokens alive.",
        }, HTTPStatus.FORBIDDEN

    except TokenExpirationBeforeNow:
        return {
            "error_message": "Token expiration before now.",
        }, HTTPStatus.FORBIDDEN

    except TokenExpirationAfterMaximum:
        return {
            "error_message": "Token expiration beyond user limit.",
        }, HTTPStatus.FORBIDDEN
    except TokenExistsError:
        return {
            "error_message": f"Token {request_data['token_name']} already exists.",
        }, HTTPStatus.FORBIDDEN


@BLUEPRINT.get("/tokens")
@jwt_required()
@log_call
def get_all_tokens():
    """
    Get all tokens that belong to user.
    Returns:
        Token list
    """

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

    sortedTokens = sorted(sanitized_tokens, key=lambda x: x["token_name"], reverse=True)

    return {
        "tokens": sortedTokens,
    }, HTTPStatus.OK


@BLUEPRINT.get("/tokens/user_limits")
@jwt_required()
@log_call
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


@BLUEPRINT.delete("/tokens")
@jwt_required()
@log_call
def revoke_token():
    """
    Revoke given token and owner combination.
    Returns:
        HTTPStatus
    """

    request_data = request.get_json()
    identity = get_jwt_identity()

    try:
        database.tokens.revoke_token_by_name_and_identity(
            request_data["token_name"], identity
        )

        return {"message": f"Revoked {request_data['token_name']}."}, HTTPStatus.OK

    except TokenNotFound:
        return {"error_message": "Token not found."}, HTTPStatus.BAD_REQUEST
