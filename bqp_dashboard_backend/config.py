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
import re
from pathlib import Path


def on_no_jwt_provided(message: str):
    log_message(message)

    return Response(status=http.HTTPStatus.UNAUTHORIZED)


ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
STATIC_DEFAULTS = {
    "MAIL_SERVER": "localhost",
    "MAIL_DEFAULT_SENDER": "noreply@example.com",
}


def resolve_env_placeholders(value):
    if isinstance(value, dict):
        return {key: resolve_env_placeholders(item) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_env_placeholders(item) for item in value]
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), ""), value)
    return value


def load_mail_config():
    config_path = Path(__file__).with_name("config.json")
    with config_path.open("r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)

    resolved_config = resolve_env_placeholders(config_data)
    for config_key, default_value in STATIC_DEFAULTS.items():
        if resolved_config.get(config_key) in (None, ""):
            resolved_config[config_key] = default_value

    return resolved_config


app = Flask(__name__)

mail_config = load_mail_config()

app.config["MAIL_SERVER"] = mail_config["MAIL_SERVER"]
app.config["MAIL_PORT"] = mail_config["MAIL_PORT"]
app.config["MAIL_USE_TLS"] = mail_config["MAIL_USE_TLS"]
app.config["MAIL_USE_SSL"] = mail_config["MAIL_USE_SSL"]
app.config["MAIL_USERNAME"] = mail_config["MAIL_USERNAME"]
app.config["MAIL_PASSWORD"] = mail_config["MAIL_PASSWORD"]
app.config["MAIL_DEFAULT_SENDER"] = mail_config["MAIL_DEFAULT_SENDER"]

mail = Mail(app)

CORS(app)
jwt = JWTManager(app)
jwt.unauthorized_loader(on_no_jwt_provided)
jwt.invalid_token_loader(on_no_jwt_provided)
Pony(app)
