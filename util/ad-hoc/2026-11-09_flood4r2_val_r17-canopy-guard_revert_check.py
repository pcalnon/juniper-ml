"""
Guard ON, fixes OFF: which of the 8 carrier-fixed canopy test files fail under the r17 guard at their base versions.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 round-2 validation of the owner's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/BRIEF_VALIDATE_R2.txt)

Usage:
    python3 util/ad-hoc/2026-11-09_flood4r2_val_r17-canopy-guard_revert_check.py

Copies ONLY the carrier's src/tests/conftest.py and pyproject.toml into the validator's base worktree (whose 8 test
files stay at the base sha, i.e. unfixed), runs those 8 files with CI's unit selector under JuniperCanopy1, and lists
the failed node ids with the guard message's address. The carrier worktree is only read. Run after the base census
lane run in that worktree has finished.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import xml.etree.ElementTree as ET  # nosec B405 - our own pytest junit output
from pathlib import Path

ORCH = Path(__file__).resolve().parents[2]
SCRATCH = ORCH / "tmp" / "flood4r2-val" / "r17-canopy-network-guard"
WORKTREES = Path.home() / "Development" / "python" / "Juniper" / "worktrees"
CARRIER = WORKTREES / "juniper-canopy--test--unit-lane-network-guard--20261109-0827--b4b01904"
BASE_WT = WORKTREES / "juniper-canopy--val--r17-network-guard-base--20261109-0942--b4b01904"
PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
SELECTOR = "not requires_cascor and not requires_server and not slow"
FILES = [
    "src/tests/regression/test_availability_unknown_state.py",
    "src/tests/regression/test_model_picker.py",
    "src/tests/unit/backend/test_cascor_service_adapter_boundary.py",
    "src/tests/unit/frontend/test_dashboard_helpers_coverage.py",
    "src/tests/unit/frontend/test_dashboard_manager.py",
    "src/tests/unit/frontend/test_dashboard_manager_95.py",
    "src/tests/unit/frontend/test_dashboard_manager_handlers.py",
    "src/tests/unit/test_convergence_ui_regression.py",
]


def main() -> int:
    for rel in ("src/tests/conftest.py", "pyproject.toml"):
        shutil.copyfile(CARRIER / rel, BASE_WT / rel)
    env = dict(os.environ)
    env.pop("LD_LIBRARY_PATH", None)
    env.update(LIBTORCH="", CASCOR_BACKEND_AVAILABLE="0", RUN_SERVER_TESTS="0", ENABLE_SLOW_TESTS="0", PYTHONDONTWRITEBYTECODE="1")
    junit = SCRATCH / "revert_check.xml"
    argv = [PY, "-m", "pytest", "-m", SELECTOR, *FILES, "-p", "no:cacheprovider", "--timeout=60", "--no-header", "-q", "-rfE", f"--basetemp={BASE_WT / 'tmp' / 'valbt-revert'}", f"--junitxml={junit}"]
    with (SCRATCH / "revert_check.log").open("w", encoding="utf-8") as log:
        code = subprocess.run(argv, cwd=BASE_WT, env=env, stdout=log, stderr=subprocess.STDOUT).returncode  # nosec B603
    root = ET.parse(junit).getroot()  # nosec B314 - our own pytest junit output
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    failed = []
    for case in suite.iter("testcase"):
        node = case.find("failure") if case.find("failure") is not None else case.find("error")
        if node is not None:
            message = node.get("message") or ""
            addr = message.split("connected to ", 1)[1].split(",", 1)[0] if "connected to " in message else "NOT-A-GUARD-FAILURE: " + message[:120]
            failed.append(f"{case.get('classname')}::{case.get('name')} -> {addr}")
    print(f"exit {code}; tests {suite.get('tests')} failures {suite.get('failures')} errors {suite.get('errors')} skipped {suite.get('skipped')}")
    print("\n".join(sorted(failed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
