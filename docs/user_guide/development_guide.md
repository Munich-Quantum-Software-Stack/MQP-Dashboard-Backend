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

### Install dependencies

```sh
pdm install
```

### Update project
```sh
pdm update
```

### Environment Variables

To run the project locally, update the environment variables in file .env:

1. Locate the .env.example file in the project root 
2. Create a copy of this file and rename it to .env 
3. Open the .env file and update the configuration values to match your local setup.

### Build and run Docker Container

**Build Docker Container**

To build Docker Container for developed environment, first enable mounted volumes in docker-compose.yaml. This action helps developer avoiding to build container in every update.

replace in docker-compose.yaml:
```sh
#volumes:
#    - ./mqp_dashboard_backend:/mqp-dashboard-backend-server/mqp_dashboard_backend
#    - ./.env:/mqp-dashboard-backend-server/.env
```
by:
```sh
volumes:
    - ./mqp_dashboard_backend:/mqp-dashboard-backend-server/mqp_dashboard_backend
    - ./.env:/mqp-dashboard-backend-server/.env
```
For building a production version, this mounted volumes should be disabled again.

Command to build container:
```sh
docker compose -f docker-compose.yaml build --no-cache
```
or
```sh
make build
```

**Start Container**
```sh
docker compose up -d
```
or
```sh
make up
```

To make environment variables affected to the application inside container, run this command:
```sh
make run-image
```

More commands will be found in `Makefile`

Application should run at: http://localhost:5000


### Unit testing with pytest

In order for the unit-tests to run, following environment variables need to be set (test_db.db can in principle be anything except already existing files):

```sh
export QUANTUM_DB_TESTING=TRUE
export QUANTUM_DB_FILENAME=test_db.db
export QUANTUM_DS_HOST=ldap://localhost:8888
```

To run the tests, use pytest:
```sh
pdm run pytest
```

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
