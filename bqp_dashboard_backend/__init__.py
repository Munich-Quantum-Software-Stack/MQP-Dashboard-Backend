from flask import Flask
from pony.flask import Pony

from . import backend

def create_app():
    app = Flask(__name__)
    # app.config.from_pyfile()

    Pony(app)

    app.register_blueprint(backend.backend)

    return app
