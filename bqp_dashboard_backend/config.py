from flask import Flask
from flask import Response
from flask_mail import Mail
from pony.flask import Pony
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from eliot import log_message
import http
import json
import os
from dotenv import load_dotenv
from pathlib import Path


def on_no_jwt_provided(message: str):
    log_message(message)

    return Response(status=http.HTTPStatus.UNAUTHORIZED)

load_dotenv()
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

app.config['MAIL_SERVER'] = os.getenv("MQP_MAIL_SERVER")
app.config['MAIL_PORT'] = os.getenv("MQP_MAIL_PORT")
app.config['MAIL_USE_TLS'] = os.getenv("MQP_MAIL_USE_TLS")
app.config['MAIL_USE_SSL'] = os.getenv("MQP_MAIL_USE_SSL")
app.config['MAIL_USERNAME'] = os.getenv("MQP_MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MQP_MAIL_PWD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MQP_MAIL_DEFAULT_SENDER")

mail = Mail(app)
CORS(app)
jwt = JWTManager(app)
jwt.unauthorized_loader(on_no_jwt_provided)
jwt.invalid_token_loader(on_no_jwt_provided)
Pony(app)
