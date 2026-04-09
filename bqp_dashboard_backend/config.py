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
app.config["JWT_SECRET_KEY"] = "7nFVM3TwqmCZeC7goIwM1DtEAQKfAmWF"

app.config['MAIL_SERVER'] = 'postout.lrz.de'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv("MQP_MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MQP_MAIL_PWD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MQP_MAIL_DEFAULT_SENDER")

mail = Mail(app)
CORS(app)
jwt = JWTManager(app)
jwt.unauthorized_loader(on_no_jwt_provided)
jwt.invalid_token_loader(on_no_jwt_provided)
Pony(app)