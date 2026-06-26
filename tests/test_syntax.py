"""Syntax tests for backend Python sources."""

from pathlib import Path


def test_backend_python_sources_are_syntax_valid() -> None:
    """Compile backend sources to catch syntax errors without importing them."""

    python_files = sorted(Path("mqp_dashboard_backend").rglob("*.py"))

    for path in python_files:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")

    assert python_files, "No backend python files found."
