"""
Mutation-check juniper-data's X8 change (``equities_seq`` declared ``regression``, VERSION 6.0.0), in a
juniper-data worktree that carries it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc — verification
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-selection-four-rulings-made-x11-f2-f1-x8-to-implement.md
         (work item 4, X8); util/ad-hoc/2026-09-24_f2_start_fresh_mutation_check.py (the same harness)

Each mutant re-introduces one way the change could be lost or overreach:
  m1  the registry goes back to ``classification`` (the pre-ruling label).
  m2  the relabel ships WITHOUT the version bump (the arc_agi #402 failure: stale cached meta).
  m3  flat ``equities`` is relabelled too, which the ruling did not ask for.

Each anchor must match exactly once (else the script refuses); every file is restored byte-for-byte
in a ``finally`` and verified. A mutant that no test kills exits the script non-zero.

Usage:
    python util/ad-hoc/2026-09-24_x8_task_type_mutation_check.py <juniper-data-worktree> [--only m1] [--tests PATH ...]
"""

import argparse
import subprocess
import sys
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperData/bin/python"
REGISTRY = "juniper_data/api/routes/generators.py"
SEQ_GENERATOR = "juniper_data/generators/equities_seq/generator.py"
DEFAULT_TESTS = ["juniper_data/tests/unit/"]

MUTANTS = {
    "m1": (REGISTRY, '        "task_type": "regression",\n        "time_unit": "calendar_days",', '        "task_type": "classification",\n        "time_unit": "calendar_days",'),
    "m2": (SEQ_GENERATOR, 'VERSION = "6.0.0"', 'VERSION = "5.0.0"'),
    "m3": (
        REGISTRY,
        '        "version": EQUITIES_VERSION,\n        "task_type": "classification",',
        '        "version": EQUITIES_VERSION,\n        "task_type": "regression",',
    ),
}


def run_tests(repo, tests):
    cmd = [PYTHON, "-m", "pytest", *tests, "-q", "--no-header", "-p", "no:cacheprovider", "-rfE"]
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=False)
    failed = [line for line in proc.stdout.splitlines() if line.startswith(("FAILED", "ERROR"))]
    lines = proc.stdout.strip().splitlines()
    tail = lines[-1] if lines else proc.stderr.strip()[-300:]
    return proc.returncode, failed, tail


def run_mutant(repo, name, tests):
    rel, anchor, replacement = MUTANTS[name]
    target = repo / rel
    original = target.read_bytes()
    text = original.decode()
    if text.count(anchor) != 1:
        print(f"{name}: anchor found {text.count(anchor)} times in {rel}, expected 1 -- REFUSING", flush=True)
        return None
    try:
        target.write_text(text.replace(anchor, replacement))
        code, failed, tail = run_tests(repo, tests)
    finally:
        target.write_bytes(original)
    assert target.read_bytes() == original, "restore failed"
    print(f"{name}: exit={code} :: {tail}", flush=True)
    for line in sorted(set(failed)):
        print(f"  {line}", flush=True)
    return len(set(failed))


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
