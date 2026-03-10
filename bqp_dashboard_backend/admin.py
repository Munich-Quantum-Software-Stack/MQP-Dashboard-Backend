from http import HTTPStatus
import os
import psycopg2
import bqp_database_access as database
from bqp_database_access.users import UnknownIdentityError
from flask import Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required

BLUEPRINT = Blueprint("admin", __name__)

ADMIN_USER_GROUP = "Editor"


def is_user_in_admin_group(identity: str) -> bool:
    """Check if user identity exists in the Admin user group."""
    conn = psycopg2.connect(
        dbname="quantumdb",
        user=os.environ["QUANTUM_DB_USER"],
        password=os.environ["QUANTUM_DB_PASS"],
        host=os.environ["QUANTUM_DB_HOST"],
    )
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
    if not is_user_in_admin_group(identity):
        return {"error_message": "Admin access required."}, HTTPStatus.FORBIDDEN

    # Grant access
    return {
        "message": "Admin access granted.",
        "redirect_to": "/admin/panel",
        "identity": identity,
    }, HTTPStatus.OK
    