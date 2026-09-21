#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc probe
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

Reproduce juniper-canopy's "Scheduled Tests" collection failure without building a
clean venv.

The scheduled lane runs ``pip install -e .`` (``.github/workflows/scheduled-tests.yml``),
with no ``[juniper-cascor]`` extra, while the PR lane runs
``pip install -e ".[juniper-cascor]"`` (``.github/workflows/ci.yml``). So in the
scheduled lane ``juniper_cascor_client`` is absent and ``src/tests/conftest.py``
injects a stub registering only ``juniper_cascor_client``, ``.exceptions`` and
``.client``. ``src/backend/cascor_service_adapter.py`` imports
``ENDPOINT_TRAINING_START`` from ``juniper_cascor_client.constants``, which the stub
does not provide -- so four test modules die at COLLECTION, not at assertion.

This probe installs a meta-path finder that makes the real package unimportable --
exactly what "not installed" means to the conftest's ``try: import ... except
ImportError`` branch -- then collects the four affected files.

Expected: 4 collection errors naming ``juniper_cascor_client.constants``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CANOPY_SRC = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy/src")

TARGETS = [
    "tests/contract/test_param_map_completeness.py",
    "tests/integration/test_apply_dataset_flow.py",
    "tests/integration/test_apply_params_skipped_surfaced.py",
    "tests/regression/test_x7_client_budget.py",
]

BLOCKER = '''
import sys
from importlib.abc import MetaPathFinder


class _BlockCascorClient(MetaPathFinder):
    """Make juniper_cascor_client look uninstalled, as the scheduled lane has it."""

    def find_spec(self, fullname, path=None, target=None):
        if fullname == "juniper_cascor_client" or fullname.startswith("juniper_cascor_client."):
            raise ModuleNotFoundError("No module named %r" % fullname)
        return None


for _name in [m for m in sys.modules if m.startswith("juniper_cascor_client")]:
    del sys.modules[_name]
sys.meta_path.insert(0, _BlockCascorClient())
'''


def main() -> int:
    blocker = CANOPY_SRC / "_scheduled_lane_blocker.py"
    blocker.write_text(BLOCKER)
    try:
        targets = ", ".join(repr(t) for t in TARGETS)
        snippet = (
            "exec(open(%r).read());"
            "import pytest, sys;"
            "sys.exit(pytest.main(['--collect-only', '-q', '-p', 'no:cacheprovider', %s]))"
        ) % (str(blocker), targets)
        proc = subprocess.run(
            ["conda", "run", "-n", "JuniperCanopy1", "python", "-c", snippet],
            cwd=CANOPY_SRC,
            capture_output=True,
            text=True,
        )
        print(proc.stdout[-6000:])
        if proc.stderr.strip():
            print("--- stderr ---", file=sys.stderr)
            print(proc.stderr[-3000:], file=sys.stderr)
        return proc.returncode
    finally:
        blocker.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
