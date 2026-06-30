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

if os.getenv("QUANTUM_DB_TESTING") is None:
    from eliot.journald import JournaldDestination


from . import login
from . import tokens
from . import jobs
from . import resources
from . import feedbacks
from . import request_access
from . import telemetry
from . import admin

if os.getenv("QUANTUM_DB_TESTING") is None:
    add_destinations(JournaldDestination())


def create_app():
    app = config.app
    try:
        if app.config.get("TESTING") or os.getenv("QUANTUM_DB_TESTING"):
            # Disable rate limiting during tests
            config.limiter.enabled = False

        app.register_blueprint(login.BLUEPRINT)
        app.register_blueprint(tokens.BLUEPRINT)
        app.register_blueprint(jobs.BLUEPRINT)
        app.register_blueprint(resources.BLUEPRINT)
        app.register_blueprint(feedbacks.BLUEPRINT)
        app.register_blueprint(request_access.BLUEPRINT)
        app.register_blueprint(telemetry.BLUEPRINT)
        app.register_blueprint(admin.BLUEPRINT)
    except Exception:
        pass
    return app
