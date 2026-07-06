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

"""MQP Dashboard Feedback Module"""

import os
from http import HTTPStatus
from flask import Blueprint, request
from flask_mail import Message
from flask_jwt_extended import jwt_required, get_jwt_identity
from eliot import log_call
import bqp_database_access as database
from . import config

BLUEPRINT = Blueprint("feedbacks", __name__)
mail = config.mail


@BLUEPRINT.post("/feedbacks/new")
@jwt_required()
@log_call
def new_feedback() -> None:
    """
    Save a feedback to database and notify to admin

    Returns:
        HTTPStatus.OK
    """
    request_data = request.get_json()
    identity = get_jwt_identity()

    # validate request data
    # if invalid data, return error
    # save data to database if ok

    database.feedback.create_feedback_for_identity(
        identity,
        request_data["rate"],
        request_data["category"],
        request_data["note"],
    )

    # send email to administrator
    sender = os.getenv("MQP_MAIL_DEFAULT_SENDER")
    message_recipients = list(
        os.getenv("MQP_MAIL_ADMIN", "MQP_MAIL_RECIPIENTS").split(",")
    )
    message = Message(subject="New feedback", sender=("MQP-Dashboard", sender))
    message.recipients = message_recipients
    message.html = "<p>Hello Admin,<br/>you received a feedback from user. Please see the content below.</p>"
    message.html += "<table><tbody>"
    message.html += (
        "<tr><th align='left'>Rating: </th><td>"
        + str(request_data["rate"])
        + "</td></tr>"
    )
    message.html += (
        "<tr><th align='left'>Category: </th><td>"
        + request_data["category"]
        + "</td></tr>"
    )
    message.html += (
        "<tr><th align='left'>Comment: </th><td>" + request_data["note"] + "</td></tr>"
    )
    message.html += "</tbody></table><br/><br/>"

    message.html += (
        "<small>This email was sent automatically. Please do not reply to it.</small>"
    )
    mail.send(message)

    return {"message": "Mail has sent"}, HTTPStatus.OK  # pylint: disable=duplicate-code
