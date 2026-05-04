
#FROM --platform=linux/amd64 python:3.11 AS base
FROM python:3.11

ENV TZ="Europe/Berlin" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/bqp-dashboard-backend-server \
    PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Set workdir
RUN mkdir -p /bqp-dashboard-backend-server
WORKDIR /bqp-dashboard-backend-server

# Install libraries
RUN apt update && apt install -y \
    git \
    build-essential \
    libldap2-dev \
    libsasl2-dev \
    slapd \
    ldap-utils \
    libldap-common \
    libssl-dev \
    sssd-ldap \
    tox \
    lcov \
    valgrind \
    python3-dev

# Install PDM
RUN pip install --no-cache-dir pdm

# Copy dependency files
COPY gunicorn.conf.py /bqp-dashboard-backend-server/
COPY pyproject.toml /bqp-dashboard-backend-server/pyproject.toml
COPY pdm.lock /bqp-dashboard-backend-server/pdm.lock

# Install dependencies
RUN pdm config python.use_venv false
RUN pdm install --prod --no-self
COPY . .

# Install project
RUN pdm install --prod

# Run the server
#CMD ["python3", "-m", "pdm", "run", "gunicorn", "-c", "gunicorn.conf.py"]
CMD ["/usr/local/bin/pdm", "run", "gunicorn", "-c","gunicorn.conf.py"]
#CMD [".venv/bin/gunicorn", "-c", "gunicorn.conf.py"]
