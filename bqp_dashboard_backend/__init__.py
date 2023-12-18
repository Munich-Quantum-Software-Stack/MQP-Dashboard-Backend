from flask import Flask
from flask import Response
from pony.flask import Pony
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from eliot import add_destinations, log_message
import os

if os.getenv("QUANTUM_DB_TESTING") is None:
    from eliot.journald import JournaldDestination
import http

from . import login
from . import tokens
from . import jobs
from . import resources


if os.getenv("QUANTUM_DB_TESTING") is None:
    add_destinations(JournaldDestination())


def on_no_jwt_provided(message: str):
    log_message(message)

    return Response(status=http.HTTPStatus.UNAUTHORIZED)


def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "7nFVM3TwqmCZeC7goIwM1DtEAQKfAmWF"

    CORS(app)
    jwt = JWTManager(app)
    jwt.unauthorized_loader(on_no_jwt_provided)
    jwt.invalid_token_loader(on_no_jwt_provided)
    Pony(app)

    app.register_blueprint(login.BLUEPRINT)
    app.register_blueprint(tokens.BLUEPRINT)
    app.register_blueprint(jobs.BLUEPRINT)
    app.register_blueprint(resources.BLUEPRINT)

    return app
