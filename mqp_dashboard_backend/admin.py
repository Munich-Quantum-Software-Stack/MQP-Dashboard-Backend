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

"""MQP Dashboard Admin Panel Module"""

from http import HTTPStatus
import os
import sqlite3
import psycopg2
import bqp_database_access as database
from bqp_database_access._database import open_database
from bqp_database_access.users import IncorrectSecretError, UnknownIdentityError
from eliot import log_message
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from .config import limiter
from .login import authenticate_user_by_ldap, UnauthorizedUser

BLUEPRINT = Blueprint("admin", __name__)

ADMIN_USER_GROUP = "Editor"


class DatabaseUnavailableError(Exception):
    """Raised when the real database can't be reached or credentials are missing."""


def _real_db_connection():
    """Open a connection to the real Postgres DB, raising a clean error if misconfigured."""

    user = os.environ.get("QUANTUM_DB_USER")
    password = os.environ.get("QUANTUM_DB_PASS")
    host = os.environ.get("QUANTUM_DB_HOST")

    if not user or not password or not host:
        raise DatabaseUnavailableError("Database credentials are not configured.")

    try:
        return psycopg2.connect(
            dbname="quantumdb", user=user, password=password, host=host
        )
    except psycopg2.OperationalError as error:
        log_message(message_type="admin_db_connection_error", error=str(error))
        raise DatabaseUnavailableError("Could not connect to the database.") from error


def is_user_in_admin_group(identity: str) -> bool:
    """Check if user identity exists in the Admin user group."""

    # Use in-memory test DB when running tests
    if os.getenv("QUANTUM_DB_TESTING") is not None:
        quantum_db = open_database()
        user = quantum_db.User.get(identity=identity)
        if user is None:
            return False
        group_names = {group.name for group in user.user_groups}
        return ADMIN_USER_GROUP in group_names

    conn = _real_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT 1 FROM users_in_user_groups WHERE "user" = %s AND usergroup = %s LIMIT 1;',
            (identity, ADMIN_USER_GROUP),
        )
        result = cur.fetchone()
        cur.close()
        return result is not None
    finally:
        conn.close()


def fetch_user_group(identity: str) -> str | None:
    """Return the first group a user belongs to or None if none found."""
    if os.getenv("QUANTUM_DB_TESTING") is not None:
        db_filename = os.getenv("QUANTUM_DB_FILENAME", "test_db.sqlite")
        db_path = os.path.join(os.getcwd(), db_filename)
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                'SELECT usergroup FROM users_in_user_groups WHERE "user" = ? ORDER BY usergroup LIMIT 1;',
                (identity,),
            )
            result = cur.fetchone()
            return result[0] if result else None
        finally:
            conn.close()

    conn = _real_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT usergroup FROM users_in_user_groups WHERE "user" = %s ORDER BY usergroup LIMIT 1;',
            (identity,),
        )
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None
    finally:
        conn.close()


@BLUEPRINT.post("/admin/group")
@limiter.limit("5 per minute")
def resolve_user_group():
    request_data = request.get_json() or {}

    identity = request_data.get("identity")
    secret = request_data.get("secret")

    if not identity or not secret:
        return {}, HTTPStatus.BAD_REQUEST

    try:
        authenticate_user_by_ldap(identity, secret)
    except (UnknownIdentityError, IncorrectSecretError, UnauthorizedUser):
        return {}, HTTPStatus.UNAUTHORIZED

    try:
        group = fetch_user_group(identity)
    except DatabaseUnavailableError:
        return {
            "error_message": "Service temporarily unavailable."
        }, HTTPStatus.SERVICE_UNAVAILABLE

    if group is None:
        return {}, HTTPStatus.FORBIDDEN

    return {"group": group}, HTTPStatus.OK


@BLUEPRINT.get("/admin/panel")
@jwt_required()
def admin_panel():
    # Get user identity from JWT token
    identity = get_jwt_identity()

    # Fetch user from database
    try:
        user = database.users.fetch_user_by_identity(identity)
    except UnknownIdentityError:
        return {"error_message": "Unauthorized."}, HTTPStatus.UNAUTHORIZED

    # Check if user is blocked
    if user.blocked:
        return {"error_message": "Unauthorized."}, HTTPStatus.UNAUTHORIZED

    # Check if user is in the Admin user group
    is_superuser = user.superuser_level is not None
    try:
        is_group_admin = is_superuser or is_user_in_admin_group(identity)
    except DatabaseUnavailableError:
        return {
            "error_message": "Service temporarily unavailable."
        }, HTTPStatus.SERVICE_UNAVAILABLE

    if not is_group_admin:
        return {"error_message": "Admin access required."}, HTTPStatus.FORBIDDEN

    # Grant access
    return {
        "message": "Admin access granted.",
        "redirect_to": "/admin/panel",
        "identity": identity,
        "superuser_level": user.superuser_level.name if is_superuser else None,
    }, HTTPStatus.OK
