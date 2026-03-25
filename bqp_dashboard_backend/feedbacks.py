from flask import Blueprint, request
from flask_mail import Message
from flask_jwt_extended import jwt_required, get_jwt_identity
from http import HTTPStatus
from eliot import log_call
from . import config
import bqp_database_access as database
import os

BLUEPRINT = Blueprint("feedbacks", __name__)
mail = config.mail


@BLUEPRINT.post("/feedbacks/new")
@jwt_required()
@log_call
def new_feedback():
    """
    - Save a feedback to database
    - Send email to admin
    """
    if request.method == "POST":
        request_data = request.get_json()
        identity = get_jwt_identity()
        # print("feedback data")
        # logging.warning(request_data)

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
        message_recipients = [
            r
            for r in os.getenv(
                "FEEDBACK_RECIPIENTS", "mqp-admin@mail.de, someone@mail.de"
            ).split(",")
        ]
        sender = "noreply-mqp@mail.de"
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
            "<tr><th align='left'>Comment: </th><td>"
            + request_data["note"]
            + "</td></tr>"
        )
        message.html += "</tbody></table><br/><br/>"

        message.html += "<small>This email was sent automatically. Please do not reply to it.</small>"
        mail.send(message)

        return {"message": "Mail has sent"}, HTTPStatus.OK
