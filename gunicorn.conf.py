import json
from pathlib import Path


DEFAULT_CONFIG = {
    "bind": "0.0.0.0:5000",
    "workers": 4,
    "wsgi_app": "bqp_dashboard_backend:create_app()",
    "certfile": "/etc/bqp-certs/portal-test_quantum_lrz_de.crt.pem",
    "keyfile": "/etc/bqp-certs/portal-test-sec-key-ohnepass.pem",
}

config_path = Path(__file__).with_name("config").joinpath("gunicorn.json")

if config_path.exists():
    with config_path.open(encoding="utf-8") as config_file:
        _loaded_config = json.load(config_file)
    _config = {**DEFAULT_CONFIG, **_loaded_config}
else:
    _config = DEFAULT_CONFIG

bind = _config["bind"]
workers = _config["workers"]
wsgi_app = _config["wsgi_app"]
certfile = _config["certfile"]
keyfile = _config["keyfile"]