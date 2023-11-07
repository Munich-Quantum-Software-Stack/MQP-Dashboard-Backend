import pytest
import os
from bqp_dashboard_backend import create_app
from bqp_database_access._database import open_database
import bqp_database_access as database_access
from pony.orm import db_session
from pony.orm import count
from pony.orm import TransactionError
from pony.orm import select
from datetime import datetime
from http import HTTPStatus
from werkzeug.datastructures import Headers

from ldap_test import LdapServer


@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here
    create_local_database()
    server = create_ldap_server()

    yield app

    # clean up / reset resources here

    delete_local_database()
    server.stop()


def create_ldap_server():
    properties = {
        "port": 8888,
        "bind_dn": "cn=ldap_test_user,ou=Intranet,ou=Kennungen,o=lrz-muenchen,c=de",
        "password": "ldap_test_password",
        "base": {
            "objectclass": ["country"],
            "dn": "c=de",
            "attributes": {"o": "lrz-muenchen"},
        },
        "entries": [
            {
                "objectclass": ["organization"],
                "dn": "o=lrz-muenchen,c=de",
                "attributes": {"o": "lrz-muenchen"},
            },
            {
                "objectclass": ["organizationalunit"],
                "dn": "ou=Kennungen,o=lrz-muenchen,c=de",
                "attributes": {"ou": "Kennungen"},
            },
            {
                "objectclass": ["organizationalunit"],
                "dn": "ou=Intranet,ou=Kennungen,o=lrz-muenchen,c=de",
                "attributes": {"ou": "Intranet"},
            },
            {
                "objectclass": ["organizationalunit"],
                "dn": "ou=quantumcomputing,ou=Kennungen,o=lrz-muenchen,c=de",
                "attributes": {"ou": "quantumcomputing"},
            },
            {
                "objectclass": ["user"],
                "dn": "cn=ldap_test_user,ou=quantumcomputing,ou=Kennungen,o=lrz-muenchen,c=de",
                "attributes": {"cn": "ldap_test_user"},
            },
        ],
    }

    server = LdapServer(properties, java_delay=0.5)
    server.start()

    return server


def create_local_database():
    db = open_database(create_tables=True)
    db.disconnect()

    try:
        with db_session:
            database_access.users.create_new_security_level(
                "BASIC",
                token_max_live_count=1,
                token_max_lifetime=30,
                token_min_creation_interval=1,
                token_max_jobs=100,
                token_max_budget=100,
                token_max_rate=1,
                login_max_interval=365,
            )
            database_access.users.create_new_user_with_secret(
                "test_user", "test_password", "BASIC", "test@lrz.de", "LRZ", "quantum"
            )

            database_access.users.create_new_user_with_secret(
                "blocked_test_user",
                "test_password",
                "BASIC",
                "test@lrz.de",
                "LRZ",
                "quantum",
            )

            database_access.users.create_new_ldap_user(
                "ldap_test_user", "BASIC", "ldaptest@lrz.de", "LRZ", "LDAP"
            )

            quantum_db = open_database()

            user = quantum_db.User["blocked_test_user"]
            user.blocked = True
            user.block_reason = f"testing dashboard behaviour: {str(datetime.now())}"

            quantum_db.commit()

    except TransactionError as error:
        pass


def delete_local_database() -> None:
    db = open_database()
    path = db.provider.pool.filename
    db.disconnect()
    os.remove(path)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def inactive_client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def active_client(app):
    client = app.test_client()

    user_data = {"identity": "test_user", "secret": "test_password"}
    login_response = client.post("/login", json=user_data)

    assert (
        login_response.status_code == HTTPStatus.OK
        and login_response.json["access_token"] is not None
    )

    client.headers = Headers()
    client.headers.add("Content-Type", "application/json")
    client.headers.add("Authorization", "Bearer " + login_response.json["access_token"])

    return client


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
