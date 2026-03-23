@nox.session(python=False)
def ci_tests(session: Session) -> None:
    """Run CI-safe syntax tests."""
    session.run("uv", "run", "pytest", "-v", "-s", "ci_tests/", external=True)