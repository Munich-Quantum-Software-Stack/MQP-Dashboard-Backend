# -----------------------------------------------------------------------------
# Runtime Image
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm

ENV TZ="Europe/Berlin" \
    PYTHONUNBUFFERED=1 \
    PDM_VENV_IN_PROJECT=1 \
    #PYTHONPATH=/mqp-dashboard-backend-server \
    PATH="/mqp-dashboard-backend-server/.venv/bin:$PATH"

# Set workdir
WORKDIR /mqp-dashboard-backend-server

# Install libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    build-essential \
    python3-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    sssd-ldap \
    slapd \
    ldap-utils \
    libldap-common \
    && rm -rf /var/lib/apt/lists/*

# Install PDM
RUN pip install --no-cache-dir pdm gunicorn
RUN pdm config python.use_venv true

# Copy dependency files
COPY gunicorn.conf.py pyproject.toml pdm.lock README.md ./

# Copy application
COPY mqp_dashboard_backend ./mqp_dashboard_backend


# Install the project and dependencies into the virtual environment
RUN pdm update

# Run the server
CMD ["pdm", "run", "gunicorn", "-c","gunicorn.conf.py"]
