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

"""MQP Dashboard Login Module"""

import os
from datetime import timedelta
from http import HTTPStatus
import ldap
import bqp_database_access as database
from bqp_database_access.users import (
    BlockedIdentityError,
    IncorrectSecretError,
    UnknownIdentityError,
)
from eliot import log_call
from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from .config import limiter

BLUEPRINT = Blueprint("login", __name__)


class AuthenticationError(Exception):
    """Base exception for authentication errors."""


class AuthenticationMechanismUnknownError(AuthenticationError):
    """Raised when the authentication mechanism is unknown."""


class UnauthorizedUser(Exception):
    """Raised when a user is not authorized to perform an action."""


@log_call(include_args=["identity"])
def authenticate_user_by_ldap(identity: str, secret: str):
    """
    Authenticate user by LDAP.
    """

    connect = None
    search_user_dn = os.environ.get("LDAP_USER_DN")
    user_dn = f"cn={identity},{search_user_dn}"
    try:
        connect = ldap.initialize(os.environ.get("QUANTUM_DS_HOST"))
        connect.protocol_version = ldap.VERSION3  # pylint: disable=no-member
        connect.set_option(ldap.OPT_REFERRALS, 0)  # pylint: disable=no-member

        # authenticate user
        if connect.simple_bind_s(user_dn, secret) is None:
            raise UnknownIdentityError

        search_filter = "(&(objectClass=user))"
        if not connect.search_s(user_dn, ldap.SCOPE_SUBTREE, search_filter):  # pylint: disable=no-member
            raise UnauthorizedUser

    except ldap.INVALID_CREDENTIALS as err:  # pylint: disable=no-member
        raise IncorrectSecretError from err

    finally:
        if connect is not None:
            connect.unbind_s()


@BLUEPRINT.post("/login")
@limiter.limit("5 per minute")
@log_call(action_type="login_attempt")
def login_user():
    """
    Authentication of user via LDAP and Quantum database
    Args:
        identity: LDAP's ID of user
        password: LDAP's password of user

    Returns:
        access_token (string): session token to access dashboard of portal
        force_secret_reset (boolean): This value is used in case user account belongs to QuantumDB
    """
    request_data = request.get_json()

    identity = request_data["identity"]
    secret = request_data["secret"]

    try:
        user = database.users.fetch_user_by_identity(identity)
        if user.blocked:
            raise BlockedIdentityError

        if user.association == "LDAP":
            authenticate_user_by_ldap(identity, secret)

        elif user.association == "QUANTUM":
            database.users.authenticate(identity, secret)

        else:
            raise AuthenticationMechanismUnknownError

    except (UnknownIdentityError, IncorrectSecretError):
        return {
            "error_message": "The identity/password is not valid. Please try again!",
        }, HTTPStatus.UNAUTHORIZED

    except BlockedIdentityError:
        return {
            "error_message": "The identity/password is not valid. Please try again!",
        }, HTTPStatus.UNAUTHORIZED

    is_admin = user.superuser_level is not None

    # generate JWT
    access_token = create_access_token(
        identity=identity, expires_delta=timedelta(minutes=15)
    )

    return {
        "access_token": access_token,
        "force_secret_reset": user.force_secret_reset,
        "is_admin": is_admin,
        "redirect_to": "/admin/panel" if is_admin else "/dashboard",
    }, HTTPStatus.OK
