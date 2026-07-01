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
"""MQP Dashboard Application's Configuration"""

import http
import os
from flask import Flask, Response
from flask_mail import Mail
from pony.flask import Pony
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from eliot import log_message
from dotenv import load_dotenv


def _on_no_jwt_provided(message: str):
    log_message(message)
    return Response(status=http.HTTPStatus.UNAUTHORIZED)

<<<<<<< HEAD

=======
>>>>>>> origin/th/public_repo
load_dotenv()
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["MAIL_SERVER"] = os.getenv("MQP_MAIL_SERVER")
app.config["MAIL_PORT"] = os.getenv("MQP_MAIL_PORT")
app.config["MAIL_USE_TLS"] = os.getenv("MQP_MAIL_USE_TLS")
app.config["MAIL_USE_SSL"] = os.getenv("MQP_MAIL_USE_SSL")
app.config["MAIL_USERNAME"] = os.getenv("MQP_MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MQP_MAIL_PWD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MQP_MAIL_DEFAULT_SENDER")

mail = Mail(app)
CORS(app)
jwt = JWTManager(app)
jwt.unauthorized_loader(_on_no_jwt_provided)
jwt.invalid_token_loader(_on_no_jwt_provided)
Pony(app)
