import os

bind = "0.0.0.0:5000"
workers = 4
wsgi_app = "mqp_dashboard_backend:create_app()"

if os.getenv("ENV") == "production":
    certfile = os.getenv("CERT_FILE")
    keyfile = os.getenv("KEY_FILE")
else:
    certfile = None
    keyfile = None
