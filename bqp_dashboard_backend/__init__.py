from eliot import add_destinations
import os
from . import config

if os.getenv("QUANTUM_DB_TESTING") is None:
    from eliot.journald import JournaldDestination


from . import login
from . import tokens
from . import jobs
from . import resources
from . import feedbacks
from . import request_access

if os.getenv("QUANTUM_DB_TESTING") is None:
    add_destinations(JournaldDestination())


def create_app():
    app = config.app
    blueprints = [
        login.BLUEPRINT,
        tokens.BLUEPRINT,
        jobs.BLUEPRINT,
        resources.BLUEPRINT,
        feedbacks.BLUEPRINT,
        request_access.BLUEPRINT,
    ]

    for blueprint in blueprints:
        if blueprint.name not in app.blueprints:
            app.register_blueprint(blueprint)

    return app
