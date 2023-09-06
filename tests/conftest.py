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


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here
    create_local_database()

    yield app

    # clean up / reset resources here
    os.remove(os.getcwd() + "/" + os.environ["QUANTUM_DB_FILENAME"])


# @pytest.fixture(autouse=True)
def create_local_database():
    db = open_database(create_tables=True)
    print(db.provider.pool.filename)

    try:
        with db_session:
            database_access.users.create_new_security_level(
                "BASIC", 10, 30, 1, 100, 100, 1, 365
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

            quantum_db = open_database()

            user = quantum_db.User["blocked_test_user"]
            user.blocked = True
            user.block_reason = f"testing dashboard behaviour: {str(datetime.now())}"

            quantum_db.commit()

    except TransactionError as error:
        pass


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
