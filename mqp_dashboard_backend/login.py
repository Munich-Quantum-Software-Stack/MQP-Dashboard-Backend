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
import ldap
from datetime import timedelta
from http import HTTPStatus
import bqp_database_access as database
from bqp_database_access.users import (
    BlockedIdentityError,
    IncorrectSecretError,
    UnknownIdentityError,
)
from eliot import log_call
from flask import Blueprint, request
from flask_jwt_extended import create_access_token


BLUEPRINT = Blueprint("login", __name__)


class AuthenticationError(Exception):
    pass


class AuthenticationMechanismUnknownError(AuthenticationError):
    pass


class UnauthorizedUser(Exception):
    pass


@log_call(include_args=["identity"])
def authenticate_user_by_ldap(identity: str, secret: str):
    """ """

    connect = None
    ldap_base_dn = os.getenv(
        "LDAP_BASE_DN", "ou=QuantumComputing,ou=People,o=example,c=de"
    )

    try:
        connect = ldap.initialize(os.environ.get("QUANTUM_DS_HOST"))
        connect.protocol_version = ldap.VERSION3
        connect.set_option(ldap.OPT_REFERRALS, 0)

        # authenticate user
        user_dn = f"cn={identity},{ldap_base_dn}"
        if connect.simple_bind_s(user_dn, secret) is None:
            raise UnknownIdentityError

        # check if part of ou=QuantumComputing
        search_filter = "(&(objectClass=user))"
        search_dn = user_dn
        if not connect.search_s(search_dn, ldap.SCOPE_SUBTREE, search_filter):
            raise UnauthorizedUser

    except ldap.INVALID_CREDENTIALS:
        raise IncorrectSecretError

    finally:
        if connect is not None:
            connect.unbind_s()


@BLUEPRINT.post("/login")
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
        # TODO log error
        return {
            "error_message": "The identity/password is not valid. Please try again!",
        }, HTTPStatus.UNAUTHORIZED

    except BlockedIdentityError:
        # TODO log error
        # NOTE should we tell them they are blocked? this would leak information
        #      confirming a user account exists
        #      otherwise merge with above
        return {
            "error_message": "The identity/password is not valid. Please try again!",
        }, HTTPStatus.UNAUTHORIZED

    else:
        # generate JWT
        access_token = create_access_token(
            identity=identity, expires_delta=timedelta(minutes=15)
        )

        return {
            "access_token": access_token,
            "force_secret_reset": user.force_secret_reset,
        }, HTTPStatus.OK
