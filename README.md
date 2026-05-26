# MQP-Dashboard-Backend

The Backend component of MQP Dashboard, and it is a part of MQSS Client

## Features

- Flask-based web application
- Dockerized development and deployment workflow
- REST API support
- Configurable environment setup
- Automated testing and CI support

## Tech Stack

- Python 3.11
- Flask
- Docker / Docker Compose
- Pytest
- GitHub Actions

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- Python 3.11

### Clone the Repository

```
git clone https://github.com/Munich-Quantum-Software-Stack/MQP-Dashboard-Backend.git \
cd MQP-Dashboard-Backend
````

### Environment Variables

To run the project locally, you need to configure your environment variables:
1. Locate the .env.example file in the project root
2. Create a copy of this file and rename it to .env
3. Open the .env file and update the configuration values to match your local setup.
4. The application runs inside a container. To make these environment variables affected to the app, run this command: $make run-image

### Run with Docker

```
make build
make up
```
Application should be available at: http://localhost:5000

### Unit testing with pytest

In order for the unit-tests to run, following environment-variables need to be set (test_db.db can in principle be anything except already existing files):

```
export QUANTUM_DB_TESTING=1
export QUANTUM_DB_FILENAME=test_db.db
export QUANTUM_DS_HOST=ldap://localhost:8888
```

### Linting

```
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

### Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

### Code of Conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

### License

Licensed under the Apache License v2.0 with LLVM Exceptions.


### Commit Message Guidelines

Examples:
```
<short_author_name>/feat: add JWT authentication
<short_author_name>/fix: resolve docker startup issue
<short_author_name>/docs: update API documentation
```

### Pull Request Process

Before submitting a PR:
- Ensure tests pass
- Ensure lint checks pass
- Add tests for new functionality
- Update documentation where needed

PRs should include:
- Summary of changes
- Related issue references
- Screenshots/examples if applicable

### Coding Standards

#### Python
- Follow PEP 8
- Use type hints when possible
- Keep functions focused and testable
- Add docstrings for public APIs

#### Flask
- Keep routes lightweight
- Move business logic into services
- Use blueprints for modularity

### Reporting Issues

Please include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Logs/screenshots if applicable

### Read-only / educational access / MQP_EDU user

27-11-2024 In bqp_dashboard_backend/tokens.py, we hardcoded, that users in the user group MQP_EDU (table users_in_user_groups in the quantum database) are returned only
"ThisIsAnEducationalTokenItCannotBeUsedToSubmitJobsThisIsAnEducat" as a token, which is not useable to submit jobs. \
If this token is encountered by the frontend, it will display a banner "This is an educational token, it cannot be used to submit jobs".
