from flask import Blueprint, request
from flask_mail import Message, Mail
from http import HTTPStatus
from . import config
import json
import logging


BLUEPRINT = Blueprint("request_access", __name__)
mail = config.mail

@BLUEPRINT.post("/request_access")
def request_access():
    """
    - Send email to admin
    """
    if request.method == 'POST':
        request_data = request.get_json()
        sender = "noreply-mqp@lrz.de"        
        message = Message(subject="New Request Access", sender=("MQP-Dashboard", sender))
        message.recipients=["mqp-admin@lrz.de", "Laura.Schulz@lrz.de"]
        #message.add_recipient("Laura.Schulz@lrz.de")
        message.html = "<p>Hello Admin,<br/>a new request access has been submitted. Please see the content below.<br/><br/>"
        message.html += "<table><tbody>"
        message.html += "<tr><th align='left'>Name: </th><td>" + request_data["title"] + "&nbsp;" + request_data["name"] + "</td></tr>"
        message.html += "<tr><th align='left'>Email Address: </th><td>" + request_data["email"] + "</td></tr>"
        message.html += "<tr><th align='left'>User-ID: </th><td>" + request_data["userID"] + "</td></tr>"
        message.html += "<tr><th align='left'>Project Name: </th><td>" + request_data["project"] + "</td></tr>"
        message.html += "<tr><th align='left'>Country: </th><td>" + request_data["country"] + "</td></tr>"
        message.html += "<tr><th align='left'>Organization/Institute: </th><td>" + request_data["organization"] + "</td></tr>"
        message.html += "<tr><th align='left'>Message: </th><td>" + request_data["message"] + "</td></tr>"
        message.html += "</tbody></table><br/><br/>"

        message.html += "<small>This email was sent automatically. Please do not reply to it.</small>"
        
        mail.send(message)
        return {"message": "Mail has sent"}, HTTPStatus.OK
