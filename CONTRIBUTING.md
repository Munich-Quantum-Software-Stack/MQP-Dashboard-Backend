# Contributing to MQP Dashboard Backend

Thank you for your interest in contributing to our project! We welcome any and all contributions.

## 📜 Code of Conduct

Please note that all participants are required to adhere to our [Code of Conduct](./CODE_OF_CONDUCT.md).

## ❓ How Can I Contribute?

Using the following [Issue Tracker][issues] you can:

- Report bugs in the project.
- Propose new features or improvements.
- Write code and documentation.

[issues]: https://github.com/Munich-Quantum-Software-Stack/MQP-Dashboard-Backend/issues

## 🐛 Submitting a Bug Report

Before submitting, please search the issues to see if your bug has been reported.

- **Check Environment:** Note your OS and browser version.
- **Provide Steps:** Describe the exact, minimal steps to reproduce the bug.
- **Expected vs. Actual:** Clearly state what you expected to happen and what actually happened.

## 💻 Code Contribution Workflow

1. **Fork** the repo and clone your fork.
2. **Build Container:** `make build`
3. **Run Container:** `make up``
4. **Run application:** `pdm install` and `pdm run flask --app mqp_dashboard_backend --debug run`
5. **Create a branch.**
6. **Make changes.**
7. **Run tests and linting:** `pytest`
8. **Run pre-commit checks** before committing changes.
9. **Commit your changes:** Use clear, descriptive commit messages.
10. **Push your branch** and open a Pull Request.

## ✅ Pre-commit checks

CI uses `.pre-commit-config-ci.yaml` for pre-commit checks. PDM remains the project package and dependency manager; `uv` is used only for CI/testing commands.
To run the same pre-commit check locally, use:

```bash
UV_PROJECT_ENVIRONMENT=.venv-ci uv run pre-commit run --all-files --config .pre-commit-config-ci.yaml
```

## ✅ Pull Request Guidelines

- **Title:** Be descriptive (e.g., `FEAT: add a new feature`).
- **Reference Issues:** Add `Closes #XYZ` to the description if it fixes
  an issue.
- **Single Focus:** Keep the PR limited to one concern or feature.
- **Tests:** New features must have corresponding tests.
