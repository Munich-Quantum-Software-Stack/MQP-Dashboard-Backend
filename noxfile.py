import nox
from nox.sessions import Session


@nox.session(python=False)
def ci_tests(session: Session) -> None:
    """Run CI-safe syntax tests."""
    session.run("python", "-m", "pytest", "-v", "-s", "ci_tests/", external=True)
