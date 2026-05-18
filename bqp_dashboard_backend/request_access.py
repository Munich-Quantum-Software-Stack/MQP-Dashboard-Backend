import os
from flask import Blueprint, request
from flask_mail import Message
from http import HTTPStatus
from . import config


BLUEPRINT = Blueprint("request_access", __name__)
mail = config.mail


@BLUEPRINT.post("/request_access")
def request_access():
    """
    - Receive a request from user and notify to admin about it
    """
    if request.method == "POST":
        request_data = request.get_json()
        sender = os.getenv("MQP_MAIL_DEFAULT_SENDER")
        message = Message(
            subject="New Request Access", sender=("MQP-Dashboard", sender)
        )
        message.recipients = [os.getenv("MQP_MAIL_ADMIN")]
        # message.add_recipient("")
        message.html = "<p>Hello Admin,<br/>a new request access has been submitted. Please see the content below.<br/><br/>"
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
        return {"message": "Mail has sent"}, HTTPStatus.OK
