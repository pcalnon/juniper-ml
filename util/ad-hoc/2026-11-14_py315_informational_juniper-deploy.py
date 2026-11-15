#!/usr/bin/env python3
"""Give juniper-deploy's `Unit Tests` job a Python 3.12-3.15 version matrix, 3.15 informational (one worktree).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- migration (phase 1 of the ecosystem's Python 3.15 migration)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_py315_informational_edits.py (juniper-data#538, the reference implementation);
         tmp/py315/ROLLOUT_BRIEF.md (the rollout brief: the owner's request and rulings of 2026-11-14);
         tmp/py315-informational-2026-11-14/survey-ci-2026-11-14.md and survey-local-2026-11-14.md (the surveys)

Why this exists
---------------
The owner's request of 2026-11-14 adds Python 3.15 to the tested versions, with the 3.15 checks reporting results
but blocking no commit, merge or deployment. The owner ruled the same day that juniper-deploy, whose `tests` job ran
on 3.12 alone, gets a version matrix 3.12-3.15.

juniper-deploy is the one repo where a plain matrix would stop every merge. Ruleset 14715370 requires the
VERSION-LESS context `Unit Tests`. A matrix job with a static name posts `Unit Tests (3.12)` and so on, so the
required context would never report and every pull request would wait for it forever. The job name is therefore an
expression on `matrix.python-version`, which GitHub uses verbatim: the 3.12 leg posts exactly `Unit Tests`, and the
others `Unit Tests (Python 3.13)`, `(Python 3.14)` and `(Python 3.15)`. The ruleset is not edited.

- 3.13 and 3.14 BLOCK, through the Quality Gate's hard check of `needs.tests.result`, like every other repo's
  3.12-3.14 legs. 3.15 is an `include` entry with `experimental: true` under the job-level
  `continue-on-error: ${{ matrix.experimental == true }}`, the pattern juniper-data#538 measured (run 43655144734).
- The job's three repository lints (workflow script paths, the juniper-ci-tools install, the AGENTS.md header)
  run on the 3.12 leg only, so the required `Unit Tests` context runs exactly the steps it ran before.
- `Pre-commit` and every other job stay on `env.PYTHON_VERSION` (3.12). The owner ruled out a 3.15 pre-commit in
  phase 1; whether `Pre-commit` should get 3.13 and 3.14 is open for the owner. `Dockerfile.test` and the images
  are untouched.

Every edit is an exact-substring replacement that must match exactly once, so the set can be re-applied onto a moved
`origin/main` from a fresh worktree (re-run, never re-type) and a drifted base fails loudly instead of being
half-edited. Nothing is written unless every edit matches, and each written file is read back.

Usage
-----
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-deploy.py --worktree <juniper-deploy worktree>
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-deploy.py --worktree <path> --check

``--check`` applies nothing and reports, per edit, whether its old text occurs exactly once (exit 1 otherwise).
Base: juniper-deploy origin/main 1cf20d84 (2026-11-14, juniper-deploy#273).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

TODAY_LONG = "November 14, 2026"
CI = ".github/workflows/ci.yml"
QUICK_START = "docs/testing/TESTING_QUICK_START.md"


@dataclass(frozen=True)
class Edit:
    path: str
    old: str
    new: str


# ---------------------------------------------------------------------------------------------------------------------
# .github/workflows/ci.yml -- the `tests` job only
# ---------------------------------------------------------------------------------------------------------------------

CI_JOB_OLD = """\
  tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1

      - name: Set up Python ${{ env.PYTHON_VERSION }}
        uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
"""

CI_JOB_NEW = """\
  tests:
    # One leg per Python version: the owner ruled on 2026-11-14 that juniper-deploy gets a 3.12-3.15
    # matrix (phase 1 of the ecosystem's Python 3.15 migration). This job alone has one; every other
    # job runs on `env.PYTHON_VERSION`. Ruleset 14715370 requires the VERSION-LESS context
    # `Unit Tests`. A static name would post `Unit Tests (3.12)` and so on, the required context
    # would never report, and every pull request would wait for it forever. A name that references
    # `matrix` is used verbatim, with no values appended: the 3.12 leg posts exactly `Unit Tests`,
    # and the others `Unit Tests (Python 3.13)`, `(Python 3.14)` and `(Python 3.15)`. The ruleset
    # requires none of those three; requiring 3.13 and 3.14 is the owner's call.
    name: ${{ matrix.python-version == '3.12' && 'Unit Tests' || format('Unit Tests (Python {0})', matrix.python-version) }}
    runs-on: ubuntu-latest
    # 3.13 and 3.14 BLOCK all the same: a failure there fails this job, and so the Quality Gate,
    # which reads `needs.tests.result`. The Python 3.15 leg is INFORMATIONAL: its results show, but
    # it must block no merge. It is the only leg with `experimental: true`, so this expression is
    # true on it alone: a failure there leaves the job's result, and so `needs.tests.result`, at
    # `success`. Measured on juniper-data#538 (run 43655144734), where that repo's gate printed
    # "Unit Tests: success" with its 3.15 leg failed on purpose. Its context is in no ruleset. Keep
    # both until the owner makes 3.15 a required version (phase 3 of the migration).
    continue-on-error: ${{ matrix.experimental == true }}
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
        include:
          # Informational, never required: see the comment above `continue-on-error`.
          - python-version: "3.15"
            experimental: true
    steps:
      - name: Checkout Code
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
"""

CI_LINTS_OLD = """\
          pytest tests/ -v --tb=short

      # Catches the failure class that broke 3 juniper-X CIs on
"""

CI_LINTS_NEW = """\
          pytest tests/ -v --tb=short

      # The three steps below lint the repository, not the interpreter, so they run on the 3.12 leg
      # alone, the one that posts the required `Unit Tests`: that context runs exactly the steps it
      # ran before the matrix, and the 3.13, 3.14 and 3.15 legs run pytest only.
      #
      # Catches the failure class that broke 3 juniper-X CIs on
"""

ONLY_312 = "        if: matrix.python-version == '3.12'\n"


def _only_on_312(step_name: str) -> Edit:
    old = f"      - name: {step_name}\n        run: |\n"
    return Edit(CI, old, f"      - name: {step_name}\n{ONLY_312}        run: |\n")


# ---------------------------------------------------------------------------------------------------------------------
# CHANGELOG.md -- [Unreleased] / Added, newest first (the file's order)
# ---------------------------------------------------------------------------------------------------------------------

CHANGELOG_OLD = """\
## [Unreleased]

### Added

"""

CHANGELOG_NEW = """\
## [Unreleased]

### Added

- **CI runs the unit tests on Python 3.12, 3.13, 3.14 and 3.15, and the 3.15 leg blocks nothing.**
  Phase 1 of the ecosystem's Python 3.15 migration: the owner's request of 2026-11-14 that 3.15
  checks report results without blocking commits, merges or deployments, and the ruling the same
  day that juniper-deploy gets a 3.12-3.15 matrix. `ci.yml`'s `tests` job, which ran on 3.12 alone,
  becomes a matrix:
  - **The 3.12 leg still posts `Unit Tests`**, the version-less context ruleset 14715370 requires.
    The job name is an expression on `matrix.python-version`, which GitHub uses verbatim instead of
    appending the leg's values. The other legs post `Unit Tests (Python 3.13)`, `(Python 3.14)` and
    `(Python 3.15)`. The ruleset is unchanged and requires none of them.
  - **3.13 and 3.14 block merges** through the Quality Gate, which reads `needs.tests.result`. 3.15
    is an `include` entry with `experimental: true` under the job-level
    `continue-on-error: ${{ matrix.experimental == true }}`, so a red 3.15 leg leaves the job's
    result at `success`: the pattern juniper-data#538 measured (run 43655144734).
  - The workflow script-path lint, the juniper-ci-tools install and the AGENTS.md header lint check
    the repository, not the interpreter, so they run on the 3.12 leg only.
  - Unchanged: `Pre-commit` and every other job, which still run on `env.PYTHON_VERSION` (3.12; no
    3.15 pre-commit in phase 1, by the owner's ruling), `Dockerfile.test` (`python:3.12-slim`, what
    `make test` runs) and every image.
  - `docs/testing/TESTING_QUICK_START.md` describes the matrix.

"""

# ---------------------------------------------------------------------------------------------------------------------
# docs/testing/TESTING_QUICK_START.md -- the one line that describes the CI test run, and the stamp (header + footer).
# Its "Python 3.12+" prerequisite is about the supported floor, not the CI matrix, so it stays.
# ---------------------------------------------------------------------------------------------------------------------

QS_CI_OLD = "Keep this list aligned with `requirements-test.txt`; CI installs that file before running `pytest tests/ -v --tb=short`.\n"
QS_CI_NEW = (
    "Keep this list aligned with `requirements-test.txt`; CI installs that file before running `pytest tests/ -v --tb=short`."
    " CI runs the suite on Python 3.12, 3.13 and 3.14, and on 3.15 as an informational leg whose failure blocks nothing"
    " (phase 1 of the Python 3.15 migration). The 3.12 leg is the required `Unit Tests` check; the others post"
    " `Unit Tests (Python 3.13)` and so on.\n"
)

EDITS: list[Edit] = [
    Edit(CI, CI_JOB_OLD, CI_JOB_NEW),
    Edit(CI, CI_LINTS_OLD, CI_LINTS_NEW),
    _only_on_312("Lint .github/workflows/ script paths"),
    _only_on_312("Install juniper-ci-tools (agents-md header-schema lint)"),
    _only_on_312("Lint AGENTS.md header schema"),
    Edit("CHANGELOG.md", CHANGELOG_OLD, CHANGELOG_NEW),
    Edit(QUICK_START, QS_CI_OLD, QS_CI_NEW),
    Edit(
        QUICK_START,
        "**Version:** 0.1.0\n**Status:** Active\n**Last Updated:** May 4, 2026\n",
        f"**Version:** 0.1.1\n**Status:** Active\n**Last Updated:** {TODAY_LONG}\n",
    ),
    Edit(QUICK_START, "**Last Updated:** May 4, 2026\n**Version:** 0.1.0\n", f"**Last Updated:** {TODAY_LONG}\n**Version:** 0.1.1\n"),
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
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--worktree", required=True, type=Path, help="a juniper-deploy checkout (never a primary)")
    ap.add_argument("--check", action="store_true", help="report matches only; write nothing")
    args = ap.parse_args()
    return apply(args.worktree, args.check)


if __name__ == "__main__":
    sys.exit(main())
