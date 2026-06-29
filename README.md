<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Munich-Quantum-Software-Stack/QDMI/develop/docs/_static/mqss_logo_dark.svg" width="20%">
    <img src="https://raw.githubusercontent.com/Munich-Quantum-Software-Stack/QDMI/develop/docs/_static/mqss_logo.svg" width="20%">
  </picture>
</p>

# MQP-Dashboard-Backend

The Backend component of Munich Quantum Portal Dashboard, and it is a part of MQSS Client. This repository implements interfaces API of Quantum database and connect to QDMI database.

## Features

- LDAP Authentication
- Manage Access Token
- Query Jobs and Resources from Quantum database
- Query Telemetry Data from QDMI proxy database
- Automated testing and CI support

## Running tests

This project uses PDM for package and dependency management. The public local test suite is intended to run from the `tests/` directory with environment values loaded from a local `.env` file.

1. Install the development dependencies with PDM:

```bash
pdm install -G dev
```

2. Copy the safe example environment file to a private local `.env` file:

```bash
cp .env.example .env
```

3. Load the variables into your shell before running tests:

```bash
set -a
source .env
set +a
```

4. Run the normal public test suite:

```bash
pdm run python -m pytest tests
```

The `.env.example` file contains placeholder values that are safe for local development and testing.

These placeholder values are for local development/testing only. The `.env` file is local and private, and real `.env` files must not be committed. Do not include private credentials, private LDAP details, or deployment-specific information in this public README.

If tests try to connect to PostgreSQL through `/var/run/postgresql/.s.PGSQL.5432`, the `.env` variables were probably not loaded or `QUANTUM_DB_TESTING=TRUE` is missing. Reload `.env` and confirm the testing variables are set before rerunning the tests.

LDAP integration tests may require an explicitly configured LDAP test server and should not be expected to pass in a normal public/local setup. Run LDAP-dependent tests only when explicitly enabled and configured, for example with `RUN_LDAP_TESTS=TRUE` if that is how the tests are configured.

CI or test workflows may use `uv` for execution, for example:

```bash
UV_PROJECT_ENVIRONMENT=.venv-ci uv run python -m pytest tests
```

This does not replace PDM; PDM remains the project package and dependency manager.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Code of Conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

## License

Licensed under the Apache License v2.0 with LLVM Exceptions.


## Commit Message Guidelines

Examples:
```sh
<short_author_name>/feat: add JWT authentication
<short_author_name>/fix: resolve docker startup issue
<short_author_name>/docs: update API documentation
```

## Pull Request Process

Before submitting a PR:
- Ensure tests pass
- Ensure lint checks pass
- Add tests for new functionality
- Update documentation where needed

PRs should include:
- Summary of changes
- Related issue references
- Screenshots/examples if applicable

## Coding Standards

### Python
- Follow PEP 8
- Use type hints when possible
- Keep functions focused and testable
- Add docstrings for public APIs

### Flask
- Keep routes lightweight
- Move business logic into services
- Use blueprints for modularity

## Reporting Issues

Please include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Logs/screenshots if applicable

## Read-only / educational access / MQP_EDU user

27-11-2024 In bqp_dashboard_backend/tokens.py, we hardcoded, that users in the user group MQP_EDU (table users_in_user_groups in the quantum database) are returned only
"ThisIsAnEducationalTokenItCannotBeUsedToSubmitJobsThisIsAnEducat" as a token, which is not useable to submit jobs. \
If this token is encountered by the frontend, it will display a banner "This is an educational token, it cannot be used to submit jobs".
