import json
import pytest
import os
from pathlib import Path

# from mqp_dashboard_backend import create_app
from bqp_database_access._database import open_database
import bqp_database_access as database_access
from pony.orm import db_session
from http import HTTPStatus
from werkzeug.datastructures import Headers
from ldap_test import LdapServer


TEST_SEED_CONFIG_PATH = Path(__file__).parent / "config" / "test_seed_data.json"
with TEST_SEED_CONFIG_PATH.open(encoding="utf-8") as config_file:
    TEST_SEED_CONFIG = json.load(config_file)


@pytest.fixture(scope="module")
def app():
    create_local_database()
    from mqp_dashboard_backend import create_app

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    server = create_ldap_server()

    yield app

    # clean up / reset resources here

    delete_local_database()
    server.stop()


def create_ldap_server():
    properties = {
        "port": 8888,
        "bind_dn": "cn=ldap_test_user,ou=QuantumComputing,ou=Kennungen,o=example-org,c=de",
        "password": "ldap_test_password",
        "base": {
            "objectclass": ["country"],
            "dn": "c=de",
            "attributes": {"o": "example-org"},
        },
        "entries": [
            {
                "objectclass": ["organization"],
                "dn": "o=example-org,c=de",
                "attributes": {"o": "example-org"},
            },
            {
                "objectclass": ["organizationalunit"],
                "dn": "ou=Kennungen,o=example-org,c=de",
                "attributes": {"ou": "Kennungen"},
            },
            {
                "objectclass": ["organizationalunit"],
                "dn": "ou=Intranet,ou=Kennungen,o=example-org,c=de",
                "attributes": {"ou": "Intranet"},
            },
            {
                "objectclass": ["organizationalunit"],
                "dn": "ou=QuantumComputing,ou=Kennungen,o=example-org,c=de",
                "attributes": {"ou": "QuantumComputing"},
            },
            {
                "objectclass": ["user"],
                "dn": "cn=ldap_test_user,ou=QuantumComputing,ou=Kennungen,o=example-org,c=de",
                "attributes": {"cn": "ldap_test_user"},
            },
        ],
    }
    server = LdapServer(properties, java_delay=0.5)
    server.start()
    return server


def create_local_database():
    delete_local_database()

    quantum_db = open_database(create_tables=True)

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
            "test_user",
            "test_password",
            "BASIC",
            "test@test.mail",
            "TEST_HPC_CENTER",
            "QUANTUM",
        )

        quantum_db.insert("users_in_user_groups", user="test_user", usergroup="MQP_EDU")

        quantum_db.insert("user", **TEST_SEED_CONFIG["blocked_user"])

        database_access.users.create_new_user_with_secret(
            "ldap_test_user",
            "test_password",
            "BASIC",
            "test@test.mail",
            "TEST_HPC_CENTER",
            "LDAP",
        )

        database_access.users.create_new_ldap_user(
            "ldap_test_user",
            "BASIC",
            "ldaptest@test.mail",
            "TEST_HPC_CENTER",
            "LDAP",
        )


def delete_local_database() -> None:
    sqlite_path = Path(os.getenv("QUANTUM_DB_FILENAME", "test_db.sqlite"))

    if sqlite_path.exists():
        sqlite_path.unlink()


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


@pytest.fixture(scope="module")
def active_client_mqp_edu(app):
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
