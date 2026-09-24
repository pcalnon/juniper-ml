"""
Mutation-check cascor's F2 fix (a start-fresh carries the discarded network's applied params onto the
rebuilt one), in a cascor worktree that carries the fix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc — verification
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-selection-four-rulings-made-x11-f2-f1-x8-to-implement.md
         (work item 2, F2); util/ad-hoc/2026-09-24_x11_mutation_check.py (the same pattern, for canopy)

Each mutant re-introduces one way the fix could be lost:
  m1  the re-apply is skipped, so create-on-start's defaults stand (the pre-fix behaviour).
  m2  the reset captures nothing, so there is nothing to re-apply.
  m3  a start-fresh drops the start body's own params.
  m4  the uncarried set is emptied, so the derived ``epochs_max`` and the lifecycle's
      ``auto_snap_*`` flags ride along.
  m5  the carry is applied to the DISCARDED network (before the rebuild), where it is lost again.

Each anchor must match exactly once (else the script refuses); the file is restored byte-for-byte in
a ``finally`` and verified. A mutant that no test kills exits the script non-zero. The default test
set is cascor's unit API directory; pass ``--tests`` for another.

Usage:
    python util/ad-hoc/2026-09-24_f2_start_fresh_mutation_check.py <cascor-worktree> [--only m1 m3] [--tests PATH ...]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
MANAGER = "src/api/lifecycle/manager.py"
DEFAULT_TESTS = ["tests/unit/api/"]

MUTANTS = {
    "m1": ("            if carried_params:\n                self._reapply_carried_params_locked(carried_params)", "            if False:\n                self._reapply_carried_params_locked(carried_params)"),
    "m2": ("        carried = {k: v for k, v in self.get_training_params().items() if k not in self._START_FRESH_UNCARRIED_PARAMS}", "        carried = {}"),
    "m3": ("            if network_kwargs:\n                self._apply_params_unlocked(network_kwargs)", "            if network_kwargs and not carried_params:\n                self._apply_params_unlocked(network_kwargs)"),
    "m4": ('_START_FRESH_UNCARRIED_PARAMS = frozenset({"epochs_max", "auto_snap_best", "auto_snap_min_epochs"})', "_START_FRESH_UNCARRIED_PARAMS = frozenset()"),
    "m5": (
        "            carried_params: Dict[str, Any] = {}\n            if start_fresh:\n                carried_params = self._start_fresh_reset_locked()",
        "            carried_params: Dict[str, Any] = {}\n            if start_fresh:\n                self._apply_params_unlocked({k: v for k, v in self.get_training_params().items() if k not in self._START_FRESH_UNCARRIED_PARAMS})\n                self._start_fresh_reset_locked()",
    ),
}


def run_tests(repo, tests):
    env = {k: v for k, v in os.environ.items() if k != "JUNIPER_CASCOR_LOG_DIR"}
    cmd = [PYTHON, "-m", "pytest", *tests, "--timeout=300", "-q", "--no-header", "-p", "no:cacheprovider", "-rfE"]
    proc = subprocess.run(cmd, cwd=repo / "src", env=env, capture_output=True, text=True, check=False)
    failed = [line for line in proc.stdout.splitlines() if line.startswith(("FAILED", "ERROR"))]
    lines = proc.stdout.strip().splitlines()
    tail = lines[-1] if lines else proc.stderr.strip()[-300:]
    return proc.returncode, failed, tail


def run_mutant(repo, name, tests):
    anchor, replacement = MUTANTS[name]
    target = repo / MANAGER
    original = target.read_bytes()
    text = original.decode()
    if text.count(anchor) != 1:
        print(f"{name}: anchor found {text.count(anchor)} times, expected 1 -- REFUSING", flush=True)
        return None
    try:
        target.write_text(text.replace(anchor, replacement))
        code, failed, tail = run_tests(repo, tests)
    finally:
        target.write_bytes(original)
    assert target.read_bytes() == original, "restore failed"
    print(f"{name}: exit={code} :: {tail}", flush=True)
    for line in failed:
        print(f"  {line}", flush=True)
    return len(failed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--only", nargs="*", default=None, choices=sorted(MUTANTS))
    ap.add_argument("--tests", nargs="*", default=None)
    ap.add_argument("--skip-baseline", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    tests = a.tests or DEFAULT_TESTS
    if not a.skip_baseline:
        code, failed, tail = run_tests(repo, tests)
        print(f"baseline: exit={code} :: {tail}", flush=True)
        for line in failed:
            print(f"  {line}", flush=True)
        if code != 0:
            print("baseline is not green -- REFUSING to attribute failures to mutants", flush=True)
            return 2
    survivors = []
    for name in a.only or sorted(MUTANTS):
        killed = run_mutant(repo, name, tests)
        if killed is None:
            return 2
        if killed == 0:
            survivors.append(name)
    print(f"survivors: {survivors or 'none'}", flush=True)
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
