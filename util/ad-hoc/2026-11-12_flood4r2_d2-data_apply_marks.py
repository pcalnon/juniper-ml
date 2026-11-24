#!/usr/bin/env python3
"""
Apply the module-level marks of the juniper-data unrun-tests change to two files whose edit is mechanical.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (run once per tree; refuses a tree it has already edited)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#529 (the precedent)

Usage:
    python3 <this> --worktree <juniper-data tree>

WHAT IT DOES
1. juniper_data/tests/unit/test_api_app.py: inserts the module-level ``pytestmark = pytest.mark.unit`` (under the same
   comment the sibling modules carry) after the imports, and removes the five ``@pytest.mark.unit`` class decorators it
   makes redundant. ``TestErrorSurfaceContract`` (9 tests) had none.
2. Moves juniper_data/tests/api/test_batch_operations.py to juniper_data/tests/unit/test_batch_operations.py (a plain
   file move, nothing staged), inserts the module-level mark after its imports, and removes the then-empty package
   juniper_data/tests/api/ (its one-line ``__init__.py``).
Every edit asserts that its anchor occurs exactly once, so a tree that already carries the change stops the script.
The other files of the change were edited by hand.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

COMMENT_API_APP = (
    '# CI\'s unit lane runs ``pytest -m "unit and not slow" juniper_data/tests/unit`` with ``--strict-markers``\n'
    "# and no auto-marking conftest, so a class here WITHOUT the ``unit`` mark is silently DESELECTED --\n"
    "# collected, green locally, and never run in CI. ``TestErrorSurfaceContract`` (9 tests) was. The\n"
    "# mark is on the module, not on each class, so a class added later cannot repeat it.\n"
    "pytestmark = pytest.mark.unit\n"
)
COMMENT_BATCH = (
    '# CI\'s unit lane runs ``pytest -m "unit and not slow" juniper_data/tests/unit`` with ``--strict-markers``\n'
    "# and no auto-marking conftest. This module sat in ``juniper_data/tests/api/``, a directory no\n"
    "# pull-request lane collects, and carried ``api`` marks at most, which no lane selects: all of its\n"
    "# tests were green locally and never run in CI. It now sits in the directory the unit lane collects,\n"
    "# with the ``unit`` mark on the module, so a class added later cannot repeat it.\n"
    "pytestmark = pytest.mark.unit\n"
)


def _read(path: Path) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _write(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _replace_once(text: str, old: str, new: str, what: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"anchor for {what} occurs {text.count(old)} times, expected 1")
    return text.replace(old, new)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path, required=True)
    wt = ap.parse_args().worktree.resolve()

    api_app = wt / "juniper_data/tests/unit/test_api_app.py"
    text = _read(api_app)
    if "pytestmark" in text:
        raise SystemExit(f"{api_app} already carries a pytestmark")
    anchor = "from juniper_data.storage.memory import InMemoryDatasetStore\n\n\n@pytest.fixture\ndef test_settings() -> Settings:\n"
    text = _replace_once(text, anchor, anchor.replace("\n\n\n@pytest.fixture", f"\n\n{COMMENT_API_APP}\n\n@pytest.fixture"), "test_api_app.py's module mark")
    for cls in ("TestCreateApp", "TestCorsPreflight", "TestExceptionHandlers", "TestLifespan", "TestGetAppFactory"):
        text = _replace_once(text, f"@pytest.mark.unit\nclass {cls}:\n", f"class {cls}:\n", f"the class decorator of {cls}")
    if "@pytest.mark.unit" in text:
        raise SystemExit("test_api_app.py still carries a @pytest.mark.unit decorator")
    _write(api_app, text)
    print(f"edited {api_app.relative_to(wt)}")

    old = wt / "juniper_data/tests/api/test_batch_operations.py"
    new = wt / "juniper_data/tests/unit/test_batch_operations.py"
    init = wt / "juniper_data/tests/api/__init__.py"
    if new.exists() or not old.is_file():
        raise SystemExit("test_batch_operations.py is not where main has it, or the destination exists")
    text = _read(old)
    if "pytestmark" in text:
        raise SystemExit(f"{old} already carries a pytestmark")
    anchor = "from juniper_data.storage.memory import InMemoryDatasetStore\n\n\n@pytest.fixture\ndef test_settings() -> Settings:\n"
    text = _replace_once(text, anchor, anchor.replace("\n\n\n@pytest.fixture", f"\n\n{COMMENT_BATCH}\n\n@pytest.fixture"), "test_batch_operations.py's module mark")
    _write(new, text)
    old.unlink()
    left = sorted(p.name for p in init.parent.iterdir() if p.name != "__pycache__")
    if left != ["__init__.py"]:
        raise SystemExit(f"juniper_data/tests/api/ holds more than its __init__.py: {left}")
    init.unlink()
    for cache in init.parent.glob("__pycache__/*"):
        cache.unlink()
    for sub in sorted(init.parent.glob("__pycache__")):
        sub.rmdir()
    init.parent.rmdir()
    print(f"moved {old.relative_to(wt)} -> {new.relative_to(wt)} and removed juniper_data/tests/api/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
