"""
Pytest plugin: prove a juniper-canopy test run imports from the worktree under test, not the primary's editable install.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy tests carrier (JuniperCanopy1 carries an editable juniper-canopy 0.6.0 install of the primary)

Load with: PYTHONPATH=<this dir> python -m pytest -p 2026-11-07_flood4_canopy_import_origin ...
At the end of the session it prints, under "IMPORT-ORIGIN", the file of each canopy top-level
module that was imported, the distinct directories the collected test modules came from, and
every loaded module whose file lies inside the PRIMARY checkout (expected: none).
"""

import os
import sys

PRIMARY = os.path.expanduser("~/Development/python/Juniper/juniper-canopy") + os.sep
CANOPY_MODULES = ("main", "settings", "dataset_schema", "config_manager", "canopy_constants", "conftest", "tests.conftest")

_test_dirs: set = set()


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        _test_dirs.add(os.path.dirname(str(item.path)))


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    write = terminalreporter.write_line
    write("IMPORT-ORIGIN cwd=" + os.getcwd())
    for name in CANOPY_MODULES:
        mod = sys.modules.get(name)
        if mod is not None:
            write(f"IMPORT-ORIGIN module {name} -> {getattr(mod, '__file__', None)}")
    for path in sorted(_test_dirs):
        write("IMPORT-ORIGIN test-dir " + path)
    from_primary = sorted(
        name for name, mod in list(sys.modules.items()) if str(getattr(mod, "__file__", "") or "").startswith(PRIMARY)
    )
    write(f"IMPORT-ORIGIN modules-from-primary count={len(from_primary)} {from_primary[:20]}")
