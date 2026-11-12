"""
Run the r17 guard's xfail probe (pytest 8.4.2 and 9.2.0) and the guard + fixed test files under pytest 9.2.0.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 round-2 validation of the owner's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/BRIEF_VALIDATE_R2.txt)

Usage:
    python3 util/ad-hoc/2026-11-09_flood4r2_val_r17-canopy-guard_pt9_and_xfail.py [<file to wait for>]

Runs, one at a time, in the validator's base+carrier canopy worktree:
  1. src/tests/unit/test_zz_val_guard_xfail_probe.py under JuniperCanopy1 (pytest 8.4.2);
  2. the same under the worktree's tmp/venv-pt9 (pytest 9.2.0, pytest-asyncio 1.4.1.post1; CI floors pytest>=9.0);
  3. the guard's own test file and the 8 fixed test files under tmp/venv-pt9, with CI's unit selector.
Child env: LD_LIBRARY_PATH dropped, LIBTORCH empty, CI's three step variables. Logs, junit and exit codes land in the
validator's scratch dir. If a file path is given, waits until it exists first (a free worker slot).
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import time
from pathlib import Path

ORCH = Path(__file__).resolve().parents[2]
SCRATCH = ORCH / "tmp" / "flood4r2-val" / "r17-canopy-network-guard"
WT = Path.home() / "Development" / "python" / "Juniper" / "worktrees" / "juniper-canopy--val--r17-network-guard--20261109-0942--b4b01904"
PY8 = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
PY9 = str(WT / "tmp" / "venv-pt9" / "bin" / "python")
SELECTOR = "not requires_cascor and not requires_server and not slow"
FIXED = [
    "src/tests/unit/test_unit_lane_network_guard.py",
    "src/tests/regression/test_availability_unknown_state.py",
    "src/tests/regression/test_model_picker.py",
    "src/tests/unit/backend/test_cascor_service_adapter_boundary.py",
    "src/tests/unit/frontend/test_dashboard_helpers_coverage.py",
    "src/tests/unit/frontend/test_dashboard_manager.py",
    "src/tests/unit/frontend/test_dashboard_manager_95.py",
    "src/tests/unit/frontend/test_dashboard_manager_handlers.py",
    "src/tests/unit/test_convergence_ui_regression.py",
]


def run(label: str, python: str, args: list[str]) -> int:
    env = dict(os.environ)
    env.pop("LD_LIBRARY_PATH", None)
    env.update(LIBTORCH="", CASCOR_BACKEND_AVAILABLE="0", RUN_SERVER_TESTS="0", ENABLE_SLOW_TESTS="0", PYTHONDONTWRITEBYTECODE="1")
    argv = [python, "-m", "pytest", *args, "-p", "no:cacheprovider", "--timeout=60", "--no-header", "-rA", f"--basetemp={WT / 'tmp' / ('valbt-' + label)}", f"--junitxml={SCRATCH / (label + '.xml')}"]
    with (SCRATCH / f"{label}.log").open("w", encoding="utf-8") as log:
        code = subprocess.run(argv, cwd=WT, env=env, stdout=log, stderr=subprocess.STDOUT).returncode  # nosec B603
    with (SCRATCH / f"{label}.log").open("a", encoding="utf-8") as log:
        log.write(f"\nEXIT {code}\n")
    print(f"{label}: exit {code}")
    return code


def main() -> int:
    if len(sys.argv) > 1:
        while not Path(sys.argv[1]).exists():
            time.sleep(2)
    run("xfail_pt8", PY8, ["src/tests/unit/test_zz_val_guard_xfail_probe.py"])
    run("xfail_pt9", PY9, ["src/tests/unit/test_zz_val_guard_xfail_probe.py"])
    run("pt9_guard_and_fixed", PY9, ["-m", SELECTOR, *FIXED])
    return 0


if __name__ == "__main__":
    sys.exit(main())
