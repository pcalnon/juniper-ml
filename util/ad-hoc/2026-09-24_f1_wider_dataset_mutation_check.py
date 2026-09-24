"""
Mutation-check cascor's F1 fix (a Start that continues the current network refuses a wider STAGED
dataset before binding it), in a cascor worktree that carries the fix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc — verification
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-selection-four-rulings-made-x11-f2-f1-x8-to-implement.md
         (work item 3, F1); util/ad-hoc/2026-09-24_f2_start_fresh_mutation_check.py (the same harness)

Each mutant re-introduces one way the fix could be lost:
  m1  start_training passes no bound, so the reload binds first and the pad refuses after (pre-fix).
  m2  only the input width is compared, so a dataset wider in its OUTPUTS is bound and then refused.
  m3  a start-fresh is refused too, which removes the very remedy the message names.
  m4  the machine-readable token is dropped, so canopy can no longer recognise the refusal.
  m5  the bound is ignored inside the reload.

Each anchor must match exactly once (else the script refuses); the file is restored byte-for-byte in
a ``finally`` and verified. A mutant that no test kills exits the script non-zero.

Usage:
    python util/ad-hoc/2026-09-24_f1_wider_dataset_mutation_check.py <cascor-worktree> [--only m1 m3] [--tests PATH ...]
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
    "m1": (
        "self._reload_dataset(refuse_wider_than=self._continued_network_dims_locked(start_fresh), **self._pending_dataset_config)",
        "self._reload_dataset(refuse_wider_than=None, **self._pending_dataset_config)",
    ),
    "m2": ("        if data_input <= net_input and data_output <= net_output:\n            return", "        if data_input <= net_input:\n            return"),
    "m3": (
        '        if start_fresh or network is None or not (hasattr(network, "input_size") and hasattr(network, "output_size")):',
        '        if network is None or not (hasattr(network, "input_size") and hasattr(network, "output_size")):',
    ),
    "m4": ('raise ValueError(f"{_PROJECT_API_START_FRESH_REQUIRED_MARKER} The staged dataset', 'raise ValueError(f"The staged dataset'),
    "m5": ("        if refuse_wider_than is not None:\n            self._refuse_dataset_wider_than_network(", "        if False:\n            self._refuse_dataset_wider_than_network("),
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
