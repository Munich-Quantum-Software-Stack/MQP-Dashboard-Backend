import nox
from nox.sessions import Session


@nox.session(python=False)
def ci_tests(session: Session) -> None:
    """Run CI-safe syntax tests that avoid private dependencies and DB setup."""
    session.run("uv", "sync", external=True)
    session.run("uv", "run", "pytest", "-v", "-s", "ci_tests/", external=True)