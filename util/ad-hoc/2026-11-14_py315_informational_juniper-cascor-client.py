#!/usr/bin/env python3
"""Apply the Python 3.15 informational-check edits (phase 1 of the 3.15 migration) to a juniper-cascor-client worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- migration (phase 1 of the ecosystem's Python 3.15 migration)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_py315_informational_edits.py (the juniper-data pilot's script, juniper-data#538,
         whose design, checks and structure this follows); tmp/py315/ROLLOUT_BRIEF.md (the rollout brief);
         tmp/py315-informational-2026-11-14/survey-ci-2026-11-14.md and survey-local-2026-11-14.md (the surveys
         that list the workflow lines, pinning tests and doc lines for this repo)

Why this exists
---------------
The Overtoad's request of 2026-11-14: add Python 3.15 to the tested versions in CI, with the 3.15 checks reporting
results but blocking no commit, merge or deployment. juniper-data#538 piloted and measured the pattern; this script
applies it to juniper-cascor-client. Every edit is an exact-substring replacement that must match exactly once, so
the set can be re-applied onto a moved ``origin/main`` from a fresh worktree (re-run, never re-type), and a drifted
base fails loudly instead of being half-edited. Nothing is written unless every edit matches.

What it changes (base: juniper-cascor-client origin/main f429803e, 2026-11-09, juniper-cascor-client#193)
---------------------------------------------------------------------------------------------------------
* ``.github/workflows/ci.yml``: ``unit-tests`` and ``integration-tests`` each gain a 3.15 ``include`` entry with
  ``experimental: true`` and the job-level ``continue-on-error: ${{ matrix.experimental == true }}``, which neither
  job had. The macOS include keeps its values (``experimental`` unset compares as false). Pre-commit is untouched
  (Overtoad ruling 2026-11-14: no 3.15 pre-commit in phase 1), and so are the gate, its ``needs:``, every
  single-version job and ``PYTHON_TEST_VERSION`` ("3.13").
* ``.github/workflows/scheduled-tests.yml``: the same leg and expression; the static job name spells out the suffix
  GitHub appended, so the existing legs' names stay byte-identical and the new one is ``(3.15)``.
* ``docs/REFERENCE.md`` (the CI table's ``unit-tests`` row, header and footer stamp) and ``CHANGELOG.md``
  (``[Unreleased]`` gains an ``### Added`` section). The ``unit-tests`` row read "Python 3.11, 3.12, 3.13", which is
  not what ``ci.yml`` runs, so the rewritten row gives the actual matrix. The other stale version notes (the
  ``pre-commit`` row, ``AGENTS.md`` § Python Version Support, ``docs/QUICK_START.md``) are left for their Overtoad.

Usage
-----
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-cascor-client.py --worktree <path>
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-cascor-client.py --worktree <path> --check

``--check`` applies nothing and reports, per edit, whether its old text occurs exactly once (exit 1 otherwise).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = "juniper-cascor-client"
TODAY_LONG = "November 14, 2026"


@dataclass(frozen=True)
class Edit:
    path: str
    old: str
    new: str


CI_UNIT_OLD = """\
    name: Unit Tests + Coverage (Python ${{ matrix.python-version }} on ${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    needs: [pre-commit]
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest]
        # CC-05 / CI-01 (Phase 4E): align CI matrix with the pyproject.toml
        # classifier set, which advertises 3.14 support.
        python-version: ["3.12", "3.13", "3.14"]
        include:
          - os: macos-latest
            python-version: "3.12"

    steps:
"""

CI_UNIT_NEW = """\
    name: Unit Tests + Coverage (Python ${{ matrix.python-version }} on ${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    needs: [pre-commit]
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's 3.15 migration (Overtoad request,
    # 2026-11-14) runs it so its results show, but it must block no merge. It is the only leg with
    # `experimental: true` (the macOS leg leaves the flag unset, which compares as false), so this
    # expression is true on it alone: a failure there leaves the job's result, which the Quality Gate
    # reads as `needs.unit-tests.result`, unchanged, so it fails neither the job nor the gate, and
    # `build` and (on a push to `main`) `notify-downstream` still run. Measured on juniper-data#538
    # (run 43655144734). The leg's context is in no ruleset. Keep both until the Overtoad makes 3.15 a
    # required version (phase 3 of the migration).
    continue-on-error: ${{ matrix.experimental == true }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest]
        # CC-05 / CI-01 (Phase 4E): align CI matrix with the pyproject.toml
        # classifier set, which advertises 3.14 support.
        python-version: ["3.12", "3.13", "3.14"]
        include:
          - os: macos-latest
            python-version: "3.12"
          # Informational, never required, and deliberately outside the classifier set the list above
          # follows (a 3.15 classifier would claim support): see the comment above `continue-on-error`.
          - os: ubuntu-latest
            python-version: "3.15"
            experimental: true

    steps:
"""

CI_INTEGRATION_OLD = """\
    name: Integration Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [pre-commit]
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]

    steps:
"""

CI_INTEGRATION_NEW = """\
    name: Integration Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [pre-commit]
    # Python 3.15 is INFORMATIONAL here too (phase 1 of the 3.15 migration, Overtoad request 2026-11-14):
    # `Integration Tests (Python 3.15)` reports, but under this expression a failure there leaves
    # `needs.integration-tests.result` unchanged, so it fails neither the job nor the Quality Gate.
    # Its context is in no ruleset; the 3.12-3.14 contexts stay required. Same pattern as unit-tests
    # (measured on juniper-data#538, run 43655144734); keep it until the Overtoad makes 3.15 required.
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
"""

SCHED_OLD = """\
  slow-or-integration-tests:
    name: Slow / Integration Tests
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
    steps:
"""

SCHED_NEW = """\
  slow-or-integration-tests:
    # The name spells out the suffix GitHub appended to the old static name ("Slow / Integration
    # Tests (3.14)"), so the three existing legs post the same names as before, and the 3.15 leg is
    # "(3.15)" rather than "(3.15, true)".
    name: Slow / Integration Tests (${{ matrix.python-version }})
    runs-on: ubuntu-latest
    # Python 3.15 is INFORMATIONAL (phase 1 of the 3.15 migration, Overtoad request 2026-11-14): its leg
    # reports, but a failure there fails neither the job nor the run. Same pattern as ci.yml's
    # unit-tests job (measured on juniper-data#538, run 43655144734). None of these contexts is in a
    # ruleset; keep the leg informational until the Overtoad makes 3.15 a required version.
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

CHANGELOG_OLD = """\
## [Unreleased]

### Changed

"""

CHANGELOG_NEW = """\
## [Unreleased]

### Added

- **CI runs the unit and integration tests on Python 3.15 as well, as informational legs that block nothing.** Phase 1
  of the ecosystem's Python 3.15 migration (the Overtoad's request of 2026-11-14): 3.15 results are reported, and no
  merge, commit or deployment waits on them.
  - `.github/workflows/ci.yml`: `unit-tests` gains `Unit Tests + Coverage (Python 3.15 on ubuntu-latest)` and
    `integration-tests` gains `Integration Tests (Python 3.15)`, each an `include` entry with `experimental: true`.
    Both jobs gain `continue-on-error: ${{ matrix.experimental == true }}`, true on the 3.15 leg alone (the macOS
    leg leaves the flag unset), so a red 3.15 leg leaves `needs.unit-tests.result` and
    `needs.integration-tests.result` unchanged: the Quality Gate, `build` and, on a push to `main`,
    `notify-downstream` are unaffected. Neither context is in ruleset `juniper-cascor-client-rules`.
  - `.github/workflows/scheduled-tests.yml`: the daily `Slow / Integration Tests` matrix gains the same informational
    3.15 leg. Its job name now spells out the `(<version>)` suffix GitHub used to append, so the three existing legs
    post the same names and the new one is `(3.15)`, not `(3.15, true)`.
  - The pattern was measured on juniper-data#538 (run 43655144734): with the 3.15 leg failed on purpose, its check
    read `failure`, the Quality Gate printed `Unit Tests: success` and passed, and every job that needs
    `unit-tests` ran.
  - `requires-python`, the classifiers, the mypy and black targets, pre-commit (still 3.12-3.14) and the
    single-version jobs (`PYTHON_TEST_VERSION` stays `3.13`) are unchanged.
  - `docs/REFERENCE.md`'s CI table gives `unit-tests` its actual matrix, informational leg included. The row read
    "Python 3.11, 3.12, 3.13"; `ci.yml` runs 3.12, 3.13 and 3.14 on Ubuntu and 3.12 on macOS.

### Changed

"""

EDITS: list[Edit] = [
    Edit(".github/workflows/ci.yml", CI_UNIT_OLD, CI_UNIT_NEW),
    Edit(".github/workflows/ci.yml", CI_INTEGRATION_OLD, CI_INTEGRATION_NEW),
    Edit(".github/workflows/scheduled-tests.yml", SCHED_OLD, SCHED_NEW),
    Edit("CHANGELOG.md", CHANGELOG_OLD, CHANGELOG_NEW),
    # docs/REFERENCE.md: the CI table's unit-tests row (it describes the test matrix), then the header and footer stamp.
    Edit(
        "docs/REFERENCE.md",
        "| **unit-tests** | Python 3.11, 3.12, 3.13 | pytest with 80% coverage gate |",
        "| **unit-tests** | Python 3.12, 3.13, 3.14 on Ubuntu; 3.12 on macOS; 3.15 on Ubuntu (informational, never blocks) | pytest with 80% coverage gate |",
    ),
    Edit(
        "docs/REFERENCE.md",
        "**Version:** 0.1.3\n**Status:** Active\n**Last Updated:** October 8, 2026\n",
        f"**Version:** 0.1.4\n**Status:** Active\n**Last Updated:** {TODAY_LONG}\n",
    ),
    Edit(
        "docs/REFERENCE.md",
        "**Last Updated:** October 8, 2026\n**Version:** 0.1.3\n",
        f"**Last Updated:** {TODAY_LONG}\n**Version:** 0.1.4\n",
    ),
]


def _is_this_repo(worktree: Path) -> bool:
    """Refuse a worktree of another repository: the old texts are juniper-cascor-client's alone."""
    pyproject = worktree / "pyproject.toml"
    return pyproject.is_file() and f'name = "{REPO}"' in pyproject.read_text(encoding="utf-8").splitlines()


def apply(worktree: Path, check_only: bool) -> int:
    if not _is_this_repo(worktree):
        print(f"REFUSED: {worktree} is not a {REPO} checkout (pyproject.toml has no 'name = \"{REPO}\"' line)", file=sys.stderr)
        return 1
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
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--check", action="store_true", help="report matches only; write nothing")
    args = ap.parse_args()
    return apply(args.worktree, args.check)


if __name__ == "__main__":
    sys.exit(main())
