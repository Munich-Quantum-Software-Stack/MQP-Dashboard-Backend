# Development Guide

## Prerequisites

- Docker
- Docker Compose
- Python 3.11

## Setting Up the Development Environment

### Clone the Repository

```sh
git clone https://github.com/Munich-Quantum-Software-Stack/MQP-Dashboard-Backend.git
cd MQP-Dashboard-Backend
```

### Environment Variables

To run the project locally, you need to configure your environment variables:
1. Locate the .env.example file in the project root
2. Create a copy of this file and rename it to .env
3. Open the .env file and update the configuration values to match your local setup.
4. The application runs inside a container. To make these environment variables affected to the app, run this command:
```sh
make run-image
```

### Run with Docker

```sh
make build
make up
```
Application should be available at: http://localhost:5000

### Unit testing with pytest

In order for the unit-tests to run, following environment-variables need to be set (test_db.db can in principle be anything except already existing files):

```sh
export QUANTUM_DB_TESTING=1
export QUANTUM_DB_FILENAME=test_db.db
export QUANTUM_DS_HOST=ldap://localhost:8888
```

To run the tests, use pytest:
```sh
pdm run pytest tests
```

### Linting

```sh
ruff check .
black --check .
```

### Development Workflow

1. Create a feature branch
2. Make changes
3. Add/update tests
4. Run linting and tests locally
5. Submit a pull request

### Security

- Do not commit secrets
- Use environment variables for configuration
- Review dependencies regularly

### Building Documentation

To build the documentation, follow these steps:\

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
