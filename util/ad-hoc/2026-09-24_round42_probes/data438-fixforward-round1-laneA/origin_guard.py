"""pytest plugin: prove ``juniper_data`` was imported from the tree under test (EXPECTED_TREE).

Loaded with ``-p origin_guard`` (this directory on PYTHONPATH). At session start and session
finish it imports ``juniper_data`` and every already-imported ``juniper_data.*`` module, and
aborts the run if any resolves outside EXPECTED_TREE -- juniper-data is installed editable from
the main checkout, so outside an extracted tree the import silently resolves there.
"""

import os
import sys
from pathlib import Path

import pytest


def _check(stage: str) -> None:
    expected = Path(os.environ["EXPECTED_TREE"]).resolve()
    import juniper_data

    bad = []
    for name, module in list(sys.modules.items()):
        if name == "juniper_data" or name.startswith("juniper_data."):
            origin = getattr(module, "__file__", None)
            if origin and not Path(origin).resolve().is_relative_to(expected):
                bad.append((name, origin))
    print(f"\n[origin_guard:{stage}] juniper_data.__file__ = {juniper_data.__file__}")
    if bad:
        pytest.exit(f"[origin_guard:{stage}] {len(bad)} juniper_data modules imported from outside {expected}: {bad[:5]}", returncode=99)
    print(f"[origin_guard:{stage}] {sum(1 for n in sys.modules if n == 'juniper_data' or n.startswith('juniper_data.'))} juniper_data modules, all inside {expected}")


def pytest_sessionstart(session: pytest.Session) -> None:
    _check("start")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    _check("finish")
