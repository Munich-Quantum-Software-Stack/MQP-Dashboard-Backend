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

"""MQP Dashboard Request Access Module"""

import os
from http import HTTPStatus
from flask import Blueprint, request
from flask_mail import Message
from . import config


BLUEPRINT = Blueprint("request_access", __name__)
mail = config.mail


@BLUEPRINT.post("/request_access")
def request_access() -> None:
    """
    Receive a request from user and notify to admin about it
    """
    request_data = request.get_json()
    sender = os.getenv("MQP_MAIL_DEFAULT_SENDER")
    message = Message(
        subject="New Request Access", sender=("MQP-Dashboard", sender)
    )
    message.recipients = [os.getenv("MQP_MAIL_ADMIN")]
    # message.add_recipient("")
    message.html = (
        "<p>Hello Admin,<br/>a new request access has been submitted. "
        + "Please see the content below.<br/><br/>"
    )
    message.html += "<table><tbody>"
    message.html += (
        "<tr><th align='left'>Name: </th><td>"
        + request_data["title"]
        + "&nbsp;"
        + request_data["name"]
        + "</td></tr>"
    )
    message.html += (
        "<tr><th align='left'>Email Address: </th><td>"
        + request_data["email"]
        + "</td></tr>"
    )
    message.html += (
        "<tr><th align='left'>User-ID: </th><td>"
        + request_data["userID"]
        + "</td></tr>"
    )
    message.html += (
        "<tr><th align='left'>Project Name: </th><td>"
        + request_data["project"]
        + "</td></tr>"
    )
    message.html += (
        "<tr><th align='left'>Country: </th><td>"
        + request_data["country"]
        + "</td></tr>"
    )
    message.html += (
        "<tr><th align='left'>Organization/Institute: </th><td>"
        + request_data["organization"]
        + "</td></tr>"
    )
    message.html += (
        "<tr><th align='left'>Message: </th><td>"
        + request_data["message"]
        + "</td></tr>"
    )
    message.html += "</tbody></table><br/><br/>"

    message.html += "<small>This email was sent automatically. Please do not reply to it.</small>"

    mail.send(message)
    return {"message": "Mail has sent"}, HTTPStatus.OK  # pylint: disable=duplicate-code
