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

"""MQP Dashboard Backend Python Package"""

import os
from eliot import add_destinations
from . import config
from . import login
from . import tokens
from . import jobs
from . import resources
from . import feedbacks
from . import request_access
from . import telemetry
from . import admin


if os.getenv("QUANTUM_DB_TESTING") is None:
    from eliot.journald import JournaldDestination
if os.getenv("QUANTUM_DB_TESTING") is None:
    add_destinations(JournaldDestination())


def create_app():
    """
    Create and configure the application.
    """
    app = config.app

    if app.config.get("TESTING") or os.getenv("QUANTUM_DB_TESTING"):
        config.limiter.enabled = False

    for blueprint in (
        login.BLUEPRINT,
        tokens.BLUEPRINT,
        jobs.BLUEPRINT,
        resources.BLUEPRINT,
        feedbacks.BLUEPRINT,
        request_access.BLUEPRINT,
        telemetry.BLUEPRINT,
        admin.BLUEPRINT,
    ):
        if blueprint.name in app.blueprints:
            continue

        if getattr(app, "_got_first_request", False):
            continue

        app.register_blueprint(blueprint)
    return app
