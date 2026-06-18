# MQP-Dashboard-Backend

The Backend component of Munich Quantum Portal Dashboard, and it is a part of MQSS Client. This repository implements interfaces API of Quantum database and connect to QDMI database.

## Features

- LDAP Authentication
- Manage Access Token
- Query Jobs and Resources from Quantum database
- Query Telemetry Data from QDMI proxy database
- Automated testing and CI support

### Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

### Code of Conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

### License

Licensed under the Apache License v2.0 with LLVM Exceptions.


### Commit Message Guidelines

Examples:
```sh
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
