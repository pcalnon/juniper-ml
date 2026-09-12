#!/usr/bin/env python3
"""
Census every live juniper-ci-tools pin and report which ones the drift guard sees.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-11
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#1909, juniper-cascor#646 (the two <0.7.0 pins this found)

Census every live ``juniper-ci-tools>=X,<Y`` pin in the ecosystem and report
which ones ``tests/test_ci_tools_drift.py`` can actually see.

The drift guard reads exactly one file per consumer repo -- ``ci.yml`` -- and
lints juniper-ml itself through a hardcoded four-entry tuple. This script
measures how many live pins that leaves unguarded, so the gap is a number
rather than an argument.

Usage:  python3 util/ad-hoc/2026-09-11_ci_tools_pin_census.py [ecosystem_root]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PIN_RE = re.compile(r"juniper-ci-tools>=([0-9][0-9.]*),<([0-9][0-9.]*)")

# A pin reaches pip in three shapes, and a sweep keyed on "pip install" sees
# only two of them. canopy's main-verify.yml / sequence-safety.yml hoist the
# pin into a workflow-level ``env: CI_TOOLS_PIN:`` and install via "$CI_TOOLS_PIN".
# Match any non-comment line, exactly as the drift guard's own extractor does.

# Mirrors tests/test_ci_tools_drift.py at the version under audit.
GUARD_CONSUMER_REPOS = (
    "juniper-canopy",
    "juniper-cascor",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-data",
    "juniper-data-client",
)
GUARD_ML_WORKFLOWS = (
    "ci.yml",
    "main-verify.yml",
    "lockfile-update.yml",
    "docs-full-check.yml",
)
ALL_REPOS = GUARD_CONSUMER_REPOS + ("juniper-deploy", "juniper-recurrence")


def live_pins(path: Path) -> list[tuple[int, str, str]]:
    """Return (lineno, lower, upper) for each live (non-comment) pin in the file."""
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        for m in PIN_RE.finditer(line):
            out.append((i, m.group(1), m.group(2)))
    return out


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    rows: list[tuple[str, str, int, str, str, bool]] = []

    for repo in ALL_REPOS + ("juniper-ml",):
        wf_dir = root / repo / ".github" / "workflows"
        if not wf_dir.is_dir():
            print(f"WARN: {repo}: no .github/workflows -- skipped")
            continue
        for wf in sorted(wf_dir.glob("*.yml")):
            for lineno, lo, hi in live_pins(wf):
                if repo == "juniper-ml":
                    seen = wf.name in GUARD_ML_WORKFLOWS
                else:
                    seen = repo in GUARD_CONSUMER_REPOS and wf.name == "ci.yml"
                rows.append((repo, wf.name, lineno, lo, hi, seen))

    total = len(rows)
    seen = sum(1 for r in rows if r[5])
    print(f"live pins: {total}   guarded: {seen}   UNGUARDED: {total - seen}")

    ranges = sorted({(r[3], r[4]) for r in rows})
    print(f"distinct ranges in use: {['>=%s,<%s' % r for r in ranges]}")

    print("\n--- pins NOT at the current range >=0.9.0,<0.10.0 ---")
    odd = [r for r in rows if (r[3], r[4]) != ("0.9.0", "0.10.0")]
    for repo, wf, lineno, lo, hi, s in odd:
        print(f"  {repo}/{wf}:{lineno}  >={lo},<{hi}   guard_sees={s}")
    if not odd:
        print("  (none)")

    print("\n--- unguarded pins, by repo ---")
    for repo in ALL_REPOS + ("juniper-ml",):
        un = [r for r in rows if r[0] == repo and not r[5]]
        tot = [r for r in rows if r[0] == repo]
        if not tot:
            continue
        files = sorted({r[1] for r in un})
        print(f"  {repo:<22} {len(un)}/{len(tot)} unguarded  {files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
