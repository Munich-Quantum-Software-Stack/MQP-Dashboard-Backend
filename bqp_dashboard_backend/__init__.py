from flask import Flask
from pony.flask import Pony
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from . import backend


def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "7nFVM3TwqmCZeC7goIwM1DtEAQKfAmWF"

    CORS(app)
    JWTManager(app)
    Pony(app)

    app.register_blueprint(backend.backend)

    return app
