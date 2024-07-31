FROM python:3.10 as bqp-dashboard-backend-server

ENV TZ="Europe/Berlin"

ARG PYTHONUNBUFFERED
ARG QUANTUM_DB_USER
ARG QUANTUM_DB_PASS
ARG QUANTUM_DB_HOST
ARG QUANTUM_DS_HOST

RUN apt update && apt install -y git
RUN apt-get install -y build-essential libldap2-dev libsasl2-dev slapd ldap-utils libldap-common sssd-ldap tox lcov valgrind

RUN mkdir -p /bqp-dashboard-backend-server/bqp_dashboard_backend
COPY bqp_dashboard_backend /bqp-dashboard-backend-server/bqp_dashboard_backend/
COPY gunicorn.conf.py /bqp-dashboard-backend-server/
COPY pyproject.toml /bqp-dashboard-backend-server/
WORKDIR /bqp-dashboard-backend-server

RUN pip install pdm
RUN pdm install
RUN pdm update
ENV PYTHONPATH=.

# Run the server
ENTRYPOINT [".venv/bin/gunicorn", "-c","gunicorn.conf.py"] 
