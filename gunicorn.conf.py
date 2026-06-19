import os

bind = "0.0.0.0:5000"
workers = 4
wsgi_app = "mqp_dashboard_backend:create_app()"

if os.getenv("ENV") == "production":
    certfile = "/etc/bqp-certs/portal-test_quantum_lrz_de.crt.pem"
    keyfile = "/etc/bqp-certs/portal-test-sec-key-ohnepass.pem"
else:
    certfile = None
    keyfile = None
