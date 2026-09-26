"""Smoke test: the package imports and reports its version."""

import antares


def test_package_imports_and_reports_version() -> None:
    assert antares.__version__ == "0.1.0"
