"""CI-safe tests that avoid private dependencies and DB setup."""

from pathlib import Path


def test_backend_python_sources_are_syntax_valid() -> None:
    """Compile backend sources to catch syntax errors without importing private deps."""

    python_files = sorted(Path("bqp_dashboard_backend").rglob("*.py"))
    assert python_files, "No backend python files found."

    for path in python_files:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
