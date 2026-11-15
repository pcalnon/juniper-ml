#!/usr/bin/env python3
"""Check one step added to a matrix job of a repo's `.github/workflows/ci.yml`: position, gating, ids.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- verification helper (phase 2 of the ecosystem's Python 3.15 migration)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_py315_h5py_hdf5_headers.py (the edits this checks)

Takes a WORKTREE, not a workflow path, so the calling command never spells the workflow directory (this host's
worktree-isolated sessions refuse some commands that do). Prints the step's index and neighbours, its `if:`,
`continue-on-error` and `id`, and fails (exit 1) when any step of the job lacks an `id`, when two share one, when
the step is not immediately before --before, or when its `continue-on-error` is not the leg expression.

Usage:
    python3 util/ad-hoc/2026-11-15_py315_check_added_step.py --worktree <wt> --job unit-tests \
        --step "Install the HDF5 headers h5py builds against (Python 3.15 only)" --before "Install dependencies"
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

import yaml

LEG_EXPR = "${{ matrix.experimental == true }}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--workflow", default="ci.yml")
    ap.add_argument("--job", required=True)
    ap.add_argument("--step", required=True)
    ap.add_argument("--before", required=True, help="the step the new one must immediately precede")
    args = ap.parse_args()

    wf = args.worktree / ".github" / "workflows" / args.workflow
    steps = yaml.safe_load(wf.read_text(encoding="utf-8"))["jobs"][args.job]["steps"]
    names = [s.get("name") for s in steps]
    problems: list[str] = []
    if names.count(args.step) != 1:
        print(f"FAIL: step {args.step!r} occurs {names.count(args.step)} times in {args.job}")
        return 1
    i = names.index(args.step)
    s = steps[i]
    print(f"{args.worktree.name}: {args.job} step {i} of {len(steps)}; prev={names[i - 1]!r} next={names[i + 1]!r}")
    print(f"  if={s.get('if')!r} continue-on-error={s.get('continue-on-error')!r} id={s.get('id')!r}")
    print(f"  run: {str(s.get('run', '')).strip()!r}")
    if names[i + 1] != args.before:
        problems.append(f"next step is {names[i + 1]!r}, want {args.before!r}")
    if s.get("continue-on-error") != LEG_EXPR:
        problems.append(f"continue-on-error is {s.get('continue-on-error')!r}, want {LEG_EXPR!r}")
    ids = [x.get("id") for x in steps]
    # The green-legs report step reads `toJSON(steps)` and is deliberately left without an id of its own.
    missing = [n for n, x in zip(names, ids) if not x and not str(n).startswith("Report the informational Python")]
    dup = [k for k, v in collections.Counter(i for i in ids if i).items() if v > 1]
    if missing:
        problems.append(f"steps without an id: {missing}")
    if dup:
        problems.append(f"duplicate ids: {dup}")
    for p in problems:
        print(f"FAIL: {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
