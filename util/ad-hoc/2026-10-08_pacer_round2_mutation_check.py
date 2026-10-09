#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-08
# Status      : ad-hoc — one-off mutation check; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Mutation-check the three node tests canopy#731's round-2 fixes added.

Copies the canopy worktree's ``src`` to a scratch directory, applies one mutation at a time to the copy's
``frontend/dashboard_manager.py``, runs ``test_f055_f058_f068_request_ack_pacer.py`` there, and reports which
tests failed. The worktree itself is never modified.

  shared-key  the pacer state is keyed by one constant, not by request store (round 2, R2-A MINOR 2)
  date-now    times come from ``Date.now()`` instead of ``performance.now()`` (R2-A MINOR 1)
  no-carry    a stale re-issue of a lost ``extra`` request is no longer ``extra`` (R2-B)
  sticky-extra  an ACKNOWLEDGED ``extra`` request still makes the next one ``extra`` (round 3)

Usage: python util/ad-hoc/2026-10-08_pacer_round2_mutation_check.py <canopy worktree> <scratch dir>
"""

import os
import shutil
import subprocess  # nosec B404 - runs pytest on a scratch copy
import sys
from pathlib import Path

MUTATIONS = {
    "shared-key": ('key_js = json.dumps(key)', 'key_js = json.dumps("shared")'),
    "date-now": ("var now = (perf && typeof perf.now === 'function') ? perf.now() : Date.now();", "var now = Date.now();"),
    "no-carry": (" || (!acked && req.reason === 'extra')", ""),
    # round 3: an acknowledged extra request must return to ticks
    "sticky-extra": (" || (!acked && req.reason === 'extra')", " || (req.reason === 'extra')"),
}
PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
TEST = "tests/unit/frontend/test_f055_f058_f068_request_ack_pacer.py"


def main(argv):
    worktree, scratch = Path(argv[0]), Path(argv[1])
    env = {k: v for k, v in os.environ.items() if k not in ("LD_LIBRARY_PATH", "LIBTORCH", "LIBTORCH_LIB")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for name, (old, new) in MUTATIONS.items():
        copy = scratch / f"mut-{name}"
        if copy.exists():
            shutil.rmtree(copy)
        shutil.copytree(worktree / "src", copy, ignore=shutil.ignore_patterns("__pycache__", "logs", "*.pyc"))
        target = copy / "frontend" / "dashboard_manager.py"
        src = target.read_text()
        assert src.count(old) == 1, f"{name}: anchor not found exactly once"
        target.write_text(src.replace(old, new))
        proc = subprocess.run([PY, "-B", "-m", "pytest", TEST, "-q", "-p", "no:cacheprovider", "-rf"], cwd=copy, env=env, capture_output=True, text=True, timeout=600, check=False)  # nosec B603 - fixed interpreter
        failed = [line.split("::")[-1].split(" ")[0] for line in proc.stdout.splitlines() if line.startswith("FAILED")]
        print(f"{name}: exit={proc.returncode} {'KILLED by ' + ', '.join(failed) if failed else 'SURVIVED'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
