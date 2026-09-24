"""
Mutation-check canopy's X11 fix (the sidebar summary's unknown-liveness wording) against the full CI
unit lane, in a canopy worktree that carries the fix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc — verification
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-selection-four-rulings-made-x11-f2-f1-x8-to-implement.md
         (work item 1, X11); util/ad-hoc/2026-09-23_mutation_check_m1_m6.py (the pattern this follows)

Each mutant re-introduces one way the fix could be lost:
  m1  the unknown branch is deleted, so ``None`` renders "Active" again (the pre-fix summary).
  m2  the hydrate failure path goes back to ``dash.no_update`` for the summary.
  m3  the first-paint seed claims a backend, so it reads "Active" without asking one.
  m4  the False branch is folded into the unknown one, so a disagreement stops naming the backend
      (the X1 guard must still hold after X11).
  m5  the ruled wording drifts.

Each anchor must match exactly once (else the script refuses); the file is restored byte-for-byte in
a ``finally`` and verified. A mutant that no test kills exits the script non-zero.

Usage:
    python util/ad-hoc/2026-09-24_x11_mutation_check.py <canopy-worktree> [--only m1 m3] [--tests PATH ...]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
DM = "src/frontend/dashboard_manager.py"
CI_LANE = ["src/tests/unit/", "src/tests/regression/", "src/tests/contract/", "src/tests/performance/"]
MARKERS = "not requires_cascor and not requires_server and not slow"

MUTANTS = {
    "m1": (
        "        if live is None:\n            return f\"Selected: {label}{note} · {DashboardManager.UNKNOWN_LIVENESS_NOTE}\"\n",
        "",
    ),
    "m2": (
        "return DEFAULT_MODEL_KEY, dash.no_update, self._initial_model_summary(), dash.no_update,",
        "return DEFAULT_MODEL_KEY, dash.no_update, dash.no_update, dash.no_update,",
    ),
    "m3": (
        'return self._model_summary_text({"nn_model": DEFAULT_MODEL_KEY, "status": status})',
        'return self._model_summary_text({"nn_model": DEFAULT_MODEL_KEY, "status": status, "backend": "service"})',
    ),
    "m4": (
        "        if live is False:\n            return f\"Selected: {label}{note} · NOT ACTIVE — the {data.get('backend')} backend is running\"\n",
        "        if live is False:\n            return f\"Selected: {label}{note} · {DashboardManager.UNKNOWN_LIVENESS_NOTE}\"\n",
    ),
    "m5": (
        'UNKNOWN_LIVENESS_NOTE: str = "backend status unknown"',
        'UNKNOWN_LIVENESS_NOTE: str = "status unknown"',
    ),
}


def run_lane(repo, tests):
    env = dict(os.environ, LIBTORCH="", LD_LIBRARY_PATH="")
    cmd = [PYTHON, "-m", "pytest", "-m", MARKERS, *tests, "--timeout=60", "-q", "--no-header", "-p", "no:cacheprovider", "-rfE"]
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, check=False)
    failed = [line for line in proc.stdout.splitlines() if line.startswith(("FAILED", "ERROR"))]
    lines = proc.stdout.strip().splitlines()
    tail = lines[-1] if lines else proc.stderr.strip()[-300:]
    return proc.returncode, failed, tail


def run_mutant(repo, name, tests):
    anchor, replacement = MUTANTS[name]
    target = repo / DM
    original = target.read_bytes()
    text = original.decode()
    if text.count(anchor) != 1:
        print(f"{name}: anchor found {text.count(anchor)} times, expected 1 -- REFUSING")
        return None
    try:
        target.write_text(text.replace(anchor, replacement))
        code, failed, tail = run_lane(repo, tests)
    finally:
        target.write_bytes(original)
    assert target.read_bytes() == original, "restore failed"
    print(f"{name}: exit={code} :: {tail}")
    for line in failed:
        print(f"  {line}")
    return len(failed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--only", nargs="*", default=None, choices=sorted(MUTANTS))
    ap.add_argument("--tests", nargs="*", default=None)
    ap.add_argument("--skip-baseline", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    tests = a.tests or CI_LANE
    if not a.skip_baseline:
        code, failed, tail = run_lane(repo, tests)
        print(f"baseline: exit={code} :: {tail}")
        for line in failed:
            print(f"  {line}")
        if code != 0:
            print("baseline is not green -- REFUSING to attribute failures to mutants")
            return 2
    survivors = []
    for name in a.only or sorted(MUTANTS):
        killed = run_mutant(repo, name, tests)
        if killed is None:
            return 2
        if killed == 0:
            survivors.append(name)
    print(f"survivors: {survivors or 'none'}")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
