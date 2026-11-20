#!/usr/bin/env python3
"""Apply the Python 3.15 informational-check edits (phase 1 of the 3.15 migration) to a juniper-harcot worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- migration (phase 1 of the ecosystem's Python 3.15 migration)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_py315_informational_edits.py (the juniper-data pilot, juniper-data#538, and the
         juniper-ml edits; this script follows its design); tmp/py315/ROLLOUT_BRIEF.md (the rollout brief);
         tmp/py315-informational-2026-11-14/survey-ci-2026-11-14.md and survey-local-2026-11-14.md (the surveys)

Why this exists
---------------
The Overtoad's request of 2026-11-14: add Python 3.15 to the tested versions in CI, with the 3.15 checks reporting
results but blocking no commit, merge or deployment; juniper-harcot is in scope (Overtoad ruling the same day). Every
edit below is an exact-substring replacement that must match exactly once, so the set can be re-applied onto a moved
``origin/main`` from a fresh worktree (re-run, never re-type) and a drifted base fails loudly instead of being
half-edited. Nothing is written unless every edit matches.

Design (measured on juniper-data#538, run 43655144734): the 3.15 leg is a matrix ``include`` entry with
``experimental: true``, and the job-level ``continue-on-error: ${{ matrix.experimental == true }}`` makes a failure
there leave the job's result, and so the Quality Gate's ``needs.unit-tests.result``, unchanged.

What it changes in juniper-harcot (base: origin/main b1c35f15, 2026-11-14, juniper-harcot#20)
---------------------------------------------------------------------------------------------
- ``.github/workflows/ci.yml``: ``unit-tests`` (3.12-3.14) gains the 3.15 include entry and the job-level expression,
  which it did not have. Its name already carries ``${{ matrix.python-version }}``, so the existing legs keep their
  names and the new one is ``Unit Tests + Coverage (Python 3.15)``. ``Pre-commit`` and the other single-version jobs
  are untouched (Overtoad ruling 2026-11-14: no 3.15 pre-commit in phase 1). The file header's description line names
  the leg, and its ``Last Modified`` moves to today.
- ``AGENTS.md``: the CI/CD line that lists the unit-test versions, and ``**Last Updated**`` (``date -u +%F``).
- No ``CHANGELOG.md``: the repository has none.

Usage
-----
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-harcot.py --worktree <path>
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-harcot.py --worktree <path> --check

``--check`` applies nothing and reports, per edit, whether its old text occurs exactly once (exit 1 otherwise).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

TODAY_ISO = "2026-11-15"  # date -u +%F when the edits were made


@dataclass(frozen=True)
class Edit:
    path: str
    old: str
    new: str


UNIT_TESTS_OLD = """\
  unit-tests:
    name: Unit Tests + Coverage (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [pre-commit]
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]

    steps:
"""

UNIT_TESTS_NEW = """\
  unit-tests:
    name: Unit Tests + Coverage (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [pre-commit]
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's 3.15 migration (Overtoad request,
    # 2026-11-14) runs it so its results show, but it must block no merge. It is the only leg with
    # `experimental: true`, so this expression is true on it alone: a failure there leaves the job's
    # result unchanged, so the Quality Gate's `needs.unit-tests.result` reads `success` and `build`,
    # which `needs: [unit-tests]`, still runs. Measured on juniper-data#538 (run 43655144734), where
    # the gate printed "Unit Tests: success" with the 3.15 leg failed on purpose. No ruleset governs
    # this private repository (the rulesets API answers 403), so its context is in none. Keep this
    # expression and the leg's include entry until the Overtoad makes 3.15 a required version (phase 3
    # of the migration).
    continue-on-error: ${{ matrix.experimental == true }}
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
        include:
          - python-version: "3.15"
            experimental: true

    steps:
"""

EDITS: list[Edit] = [
    # .github/workflows/ci.yml
    Edit(
        ".github/workflows/ci.yml",
        "#    - Unit tests with the 90% coverage gate on Python 3.12, 3.13 and 3.14\n",
        "#    - Unit tests with the 90% coverage gate on Python 3.12, 3.13 and 3.14, plus an informational 3.15 leg that blocks nothing\n",
    ),
    Edit(".github/workflows/ci.yml", "# Last Modified: 2026-11-10\n", "# Last Modified: " + TODAY_ISO + "\n"),
    Edit(".github/workflows/ci.yml", UNIT_TESTS_OLD, UNIT_TESTS_NEW),
    # AGENTS.md
    Edit(
        "AGENTS.md",
        "- `.github/workflows/ci.yml` — pre-commit, unit tests with the coverage gate on Python 3.12, 3.13 and 3.14, the contract tests",
        "- `.github/workflows/ci.yml` — pre-commit, unit tests with the coverage gate on Python 3.12, 3.13 and 3.14 (plus an informational 3.15 leg that reports and blocks nothing: phase 1 of the Python 3.15 migration, 2026-11-14), the contract tests",
    ),
    Edit("AGENTS.md", "**Last Updated**: 2026-11-12\n", "**Last Updated**: " + TODAY_ISO + "\n"),
]


def apply(worktree: Path, check_only: bool) -> int:
    contents: dict[str, str] = {}
    bad = 0
    for e in EDITS:
        path = worktree / e.path
        if e.path not in contents:
            contents[e.path] = path.read_text(encoding="utf-8")
        text = contents[e.path]
        n = text.count(e.old)
        label = f"{e.path}: {e.old.strip().splitlines()[0][:90]!r}"
        if n != 1:
            print(f"MISMATCH ({n} occurrences, want 1): {label}")
            bad += 1
            continue
        print(f"ok: {label}")
        contents[e.path] = text.replace(e.old, e.new, 1)
    if bad:
        print(f"{bad} edit(s) did not match exactly once; nothing written", file=sys.stderr)
        return 1
    if check_only:
        print(f"check: all {len(EDITS)} edit(s) match exactly once")
        return 0
    for rel, text in contents.items():
        path = worktree / rel
        path.write_text(text, encoding="utf-8")
        if path.read_text(encoding="utf-8") != text:  # read back our own write
            print(f"READ-BACK MISMATCH: {rel}", file=sys.stderr)
            return 1
    print(f"wrote {len(contents)} file(s), {len(EDITS)} edit(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--worktree", required=True, type=Path, help="root of a juniper-harcot worktree based on origin/main")
    ap.add_argument("--check", action="store_true", help="report matches only; write nothing")
    args = ap.parse_args()
    return apply(args.worktree, args.check)


if __name__ == "__main__":
    sys.exit(main())
