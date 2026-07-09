# Development Guide

## Prerequisites

- Docker Compose
- Python 3.11

## Setting Up the Development Environment

### Clone the Repository

```sh
git clone https://github.com/Munich-Quantum-Software-Stack/MQP-Dashboard-Backend.git
cd MQP-Dashboard-Backend
```

### Install dependencies first time

```sh
pdm install
```

### Update project and dependencies
```sh
pdm update
```

### Setting Environment Variables

There are two places that need to be updated environment variables:
- .env (filename is fixed)
- docker-compose.yaml

To run the project locally:

1. Create a copy of file .env.example and rename it to .env
2. The .env file must be at root directory
3. Open the .env file and update the configuration values to match your local setup.

### Build and run Docker Container

**Build Development Container**

in file docker-compose.yaml, make sure environment is `development` value:
```sh
environment:
    ENV: developemnt
```
and mounted volumes:
```sh
volumes:
    - ./mqp_dashboard_backend:/mqp-dashboard-backend-server/mqp_dashboard_backend
```

**Build Production Container**

docker-compose.yaml:
```sh
environment:
    ENV: production
```
disable mounted volumes:
```sh
#volumes:
#    - ./mqp_dashboard_backend:/mqp-dashboard-backend-server/mqp_dashboard_backend
```

After setting environment variables in `.env` and `docker-compose.yaml`, build docker container by command:
```sh
docker compose -f docker-compose.yaml build --no-cache
```
or shortcut:
```sh
make build-app
```

**Start Container**

```sh
docker compose up -d
```
or shortcut:
```sh
make run-app
```

Update environment values from outside of container:
```sh
docker run -e <variable_name=value>
```

More commands will be found in `Makefile`

Application should run at: http://localhost:5000


### Unit Test

This project uses PDM for packages and dependencies management. The public local test suite is intended to run from the `tests/` directory with environment values loaded from a local `.env.test` file.

1. Copy test environment values from file .env.examle to an `.env.test` file
```sh
cp .env.example .env.test
```

2. Build test container from Dockerfile.test locally:
```sh
make build-test
```

4. Run test container:
```sh
make run-test
```

5. Run pytest inside test container:
```sh
docker ps
docker exec -it <container_name/container_ID> /bin/bash
pdm run pytest
```

The `.env.example` file contains placeholder values that are safe for local development and testing.

The `.env` file stores sensitive data, and must not be committed.

The `.env.test` is used only for unit test and CI testing.

If tests try to connect to PostgreSQL through `/var/run/postgresql/.s.PGSQL.5432`, this indicates that test environment variables are not loaded in container. Reload `.env.test` in container and confirm the testing variables are set before rerunning the tests.


### Linting and Ruff check

```sh
pdm run ruff check .
pdm run black --check .
```

### Development Workflow

1. Create a feature branch
2. Make changes
3. Add/update tests
4. Run linting and tests locally
5. Submit a pull request


## Building Documentation

To build the documentation, follow these steps:

**Install MkDocs and the Material theme:**
```sh
uv sync
```

**Build the documentation:**
```sh
uv run mkdocs build
```

**Local deployment:**

Run the following and browse the documentation locally at: http://localhost:8000
```sh
uv run mkdocs serve
```
