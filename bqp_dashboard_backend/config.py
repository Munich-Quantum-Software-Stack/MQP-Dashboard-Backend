from flask import Flask
from flask import Response
from flask_mail import Mail
from pony.flask import Pony
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from eliot import log_message
import http
import os


def on_no_jwt_provided(message: str):
    log_message(message)

    return Response(status=http.HTTPStatus.UNAUTHORIZED)


app = Flask(__name__)
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MQP_MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MQP_MAIL_PWD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

CORS(app)
jwt = JWTManager(app)
jwt.unauthorized_loader(on_no_jwt_provided)
jwt.invalid_token_loader(on_no_jwt_provided)
Pony(app)
