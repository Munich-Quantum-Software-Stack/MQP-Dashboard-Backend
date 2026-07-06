FROM python:3.11-slim

ENV TZ="Europe/Berlin" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/mqp-dashboard-backend-server \
    PATH="/mqp-dashboard-backend-server/.venv/bin:$PATH"

# Set workdir
RUN mkdir -p /mqp-dashboard-backend-server
WORKDIR /mqp-dashboard-backend-server

# Install libraries
RUN apt update && apt install -y \
    git \
    gcc \
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
    python3-dev \
    --no-install-recommends openjdk-21-jre \
    && rm -rf /var/lib/apt/lists/*

# Install PDM
RUN pip install --no-cache-dir pdm

# Install Gunicorn
RUN pip install gunicorn

# Copy dependency files
COPY gunicorn.conf.py pyproject.toml pdm.lock ./
COPY mqp_dashboard_backend ./mqp_dashboard_backend

RUN pdm config python.use_venv true

# Install ALL dependencies + project into .venv
#RUN pdm sync --prod
# Install ALL dependencies
RUN pdm update

# Run the server
CMD ["gunicorn", "-c","gunicorn.conf.py"]
