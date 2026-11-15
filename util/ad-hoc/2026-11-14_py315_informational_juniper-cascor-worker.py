#!/usr/bin/env python3
"""Apply the Python 3.15 informational-leg edits (phase 1 of the 3.15 migration) to a juniper-cascor-worker worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- migration (phase 1 of the ecosystem's Python 3.15 migration)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_py315_informational_edits.py (the juniper-data pilot, juniper-data#538, whose pattern
         and measurement this reuses); tmp/py315-informational-2026-11-14/survey-ci-2026-11-14.md and
         survey-local-2026-11-14.md (the surveys that list the workflow, doc and test lines touched here)

Why this exists
---------------
The owner's request of 2026-11-14: add Python 3.15 to the tested versions, with the 3.15 checks reporting results but
blocking no commit, merge or deployment. Every edit below is an exact-substring replacement that must match exactly
once, so the set can be re-applied onto a moved ``origin/main`` from a fresh worktree (re-run, never re-type) and a
drifted base fails loudly instead of being half-edited. Nothing is written unless every edit matches.

Design (measured on juniper-data#538, run 43655144734): each matrix job that runs tests over a Python-version list gets
an ``include`` entry, Python "3.15" with ``experimental: true``, and the job-level
``continue-on-error: ${{ matrix.experimental == true }}``, so a failure on that leg leaves the job's result, and so
every gate's ``needs.<job>.result``, unchanged. The new contexts are never added to a ruleset.

In juniper-cascor-worker (base: origin/main 5fbaaf50, 2026-11-10, juniper-cascor-worker#226):

- ``ci.yml`` ``unit-tests`` already carries the expression and a macOS ``experimental: false`` include; it gains the
  3.15 include. Its comment still said the macOS leg was in its soak, which juniper-cascor-worker#40 ended on
  2026-05-01, and "The Linux legs remain required", which the 3.15 leg makes false, so the comment is rewritten.
  ``tests/test_dockerfile_cpu_torch_pin.py`` pins exactly one "Install dependencies" step in this job; no step changes.
- ``ci.yml`` ``integration-tests`` (soft in the Quality Gate) gains the include and the expression. Its name already
  renders ``matrix.python-version``, so the required "Integration Tests (Python 3.12|3.13|3.14)" contexts keep their
  names and the new leg posts "Integration Tests (Python 3.15)".
- ``scheduled-tests.yml`` ``slow-or-integration-tests`` gains the include and the expression, and, as in
  juniper-data#538, its static name spells out the "(<version>)" suffix GitHub appended, so the three existing legs
  keep their names and the new one is "(3.15)", not "(3.15, true)".
- Left alone: ``ci.yml`` ``pre-commit`` (owner ruling: no 3.15 pre-commit in phase 1). ``AGENTS.md``'s
  ``**Python**:`` line (">=3.11 (supports 3.11 ...)") is already stale against ``requires-python >=3.12`` and is about
  support, not the CI matrix: reported, not fixed.

Usage
-----
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-cascor-worker.py --worktree <path>
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-cascor-worker.py --worktree <path> --check

``--check`` applies nothing and reports, per edit, whether its old text occurs exactly once (exit 1 otherwise).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

TODAY_ISO = "2026-11-14"


@dataclass(frozen=True)
class Edit:
    path: str
    old: str
    new: str


# ---------------------------------------------------------------------------------------------------------------------
# .github/workflows/ci.yml -- unit-tests
# ---------------------------------------------------------------------------------------------------------------------

CI_COMMENT_OLD = """\
    # METRICS-MON R3.7 / seed-(R1.3 design): macOS leg runs in
    # continue-on-error mode for the initial 2-week soak (started
    # 2026-04-30). The Linux legs remain required; the macOS leg
    # surfaces platform-divergence failures (cross-platform rss_mb
    # sampling, POSIX-only assumptions) without blocking PRs while
    # we identify environment-specific issues. After the soak, flip
    # the include block's ``experimental`` flag to false to make
    # the macOS leg required.
    continue-on-error: ${{ matrix.experimental == true }}
"""

CI_COMMENT_NEW = """\
    # METRICS-MON R3.7 / seed-(R1.3 design): the macOS leg ran in
    # continue-on-error mode for a 2-week soak (started 2026-04-30)
    # that surfaced platform-divergence failures (cross-platform
    # rss_mb sampling, POSIX-only assumptions) without blocking PRs.
    # juniper-cascor-worker#40 ended the soak on 2026-05-01 by setting
    # the include block's ``experimental`` flag to false, so a failing
    # macOS leg fails the job; ruleset 14250447 requires its context
    # with the three 3.12-3.14 Linux contexts.
    #
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's
    # 3.15 migration (owner request, 2026-11-14) runs it so its results
    # show, but it must block no merge. It is the only leg with
    # ``experimental: true``, so this expression is true on it alone: a
    # failure there leaves the job's result, which the Quality Gate
    # reads as `needs.unit-tests.result`, unchanged, and `build`
    # (`needs: [unit-tests]`) still runs. Measured on juniper-data#538
    # (run 43655144734): with the 3.15 leg failed on purpose, that gate
    # printed "Unit Tests: success" and its dependent jobs ran. Its
    # context is in no ruleset. Keep both until the owner makes 3.15 a
    # required version (phase 3 of the migration).
    continue-on-error: ${{ matrix.experimental == true }}
"""

CI_INCLUDE_OLD = """\
        python-version: ["3.12", "3.13", "3.14"]
        include:
          - os: macos-latest
            python-version: "3.12"
            experimental: false

    steps:
"""

CI_INCLUDE_NEW = """\
        python-version: ["3.12", "3.13", "3.14"]
        include:
          - os: macos-latest
            python-version: "3.12"
            experimental: false
          # Informational, never required: see the comment above `continue-on-error`.
          - os: ubuntu-latest
            python-version: "3.15"
            experimental: true

    steps:
"""

# ---------------------------------------------------------------------------------------------------------------------
# .github/workflows/ci.yml -- integration-tests (soft in the Quality Gate; its 3.12-3.14 contexts are required)
# ---------------------------------------------------------------------------------------------------------------------

CI_INTEGRATION_OLD = """\
  integration-tests:
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
  integration-tests:
    name: Integration Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    # The Python 3.15 leg is INFORMATIONAL, as in unit-tests above: it is
    # the only leg with ``experimental: true``, so this expression is true
    # on it alone, and a failure there leaves the job's result, which the
    # Quality Gate reads as `needs.integration-tests.result`, unchanged.
    # Ruleset 14250447 requires "Integration Tests (Python 3.12)",
    # "(Python 3.13)" and "(Python 3.14)", never "(Python 3.15)". Keep it
    # until the owner makes 3.15 a required version.
    continue-on-error: ${{ matrix.experimental == true }}
    needs: [pre-commit]
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

# ---------------------------------------------------------------------------------------------------------------------
# .github/workflows/scheduled-tests.yml -- slow-or-integration-tests (schedule and dispatch only)
# ---------------------------------------------------------------------------------------------------------------------

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
    # Python 3.15 is INFORMATIONAL (phase 1 of the 3.15 migration, 2026-11-14): its leg reports, but a
    # failure there fails neither the job nor the run. Same pattern as ci.yml's unit-tests job.
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

# ---------------------------------------------------------------------------------------------------------------------
# CHANGELOG.md -- [Unreleased] / Added
# ---------------------------------------------------------------------------------------------------------------------

CHANGELOG_OLD = """\
## [Unreleased]

### Added

"""

CHANGELOG_NEW = """\
## [Unreleased]

### Added

- **CI runs the tests on Python 3.15 as well, as informational legs that block nothing.** Phase 1 of the ecosystem's
  Python 3.15 migration (the owner's request of 2026-11-14): 3.15 results are reported, and no merge, commit or
  deployment waits on them.
  - `ci.yml`'s `unit-tests` gains `Unit Tests + Coverage (Python 3.15 on ubuntu-latest)`, an `include` entry with
    `experimental: true`. The job's existing `continue-on-error: ${{ matrix.experimental == true }}` applies to that
    leg alone, so a red 3.15 leg leaves `needs.unit-tests.result`, the Quality Gate and `build` unchanged. The context
    is not in ruleset 14250447. The comment above `continue-on-error` no longer says the macOS leg is in its soak,
    which #40 ended on 2026-05-01.
  - `ci.yml`'s `integration-tests` gains `Integration Tests (Python 3.15)` the same way, with a new job-level
    `continue-on-error: ${{ matrix.experimental == true }}`. The ruleset requires the 3.12, 3.13 and 3.14 contexts,
    whose names are unchanged.
  - `scheduled-tests.yml`'s `Slow / Integration Tests` matrix gains the same informational 3.15 leg. Its job name now
    spells out the `(<version>)` suffix GitHub used to append, so the three existing legs post the same names.
  - The pattern was measured on juniper-data#538 (run 43655144734): with the 3.15 leg failed on purpose, the leg's
    check read `failure`, that repository's Quality Gate printed `Unit Tests: success` and passed, and every job that
    `needs: [unit-tests]` ran.
  - Unchanged on purpose: `pre-commit` (3.12-3.14; the owner ruled out a 3.15 pre-commit in phase 1),
    `requires-python`, the classifiers, the black, mypy and ruff targets, and the Docker base.
  - `AGENTS.md` (§ CI/CD) and `docs/DEVELOPER_CHEATSHEET.md` (1.1.2) describe the legs.
"""

# ---------------------------------------------------------------------------------------------------------------------
# The edit list
# ---------------------------------------------------------------------------------------------------------------------

EDITS: list[Edit] = [
    Edit(".github/workflows/ci.yml", CI_COMMENT_OLD, CI_COMMENT_NEW),
    Edit(".github/workflows/ci.yml", CI_INCLUDE_OLD, CI_INCLUDE_NEW),
    Edit(".github/workflows/ci.yml", CI_INTEGRATION_OLD, CI_INTEGRATION_NEW),
    Edit(".github/workflows/scheduled-tests.yml", SCHED_OLD, SCHED_NEW),
    Edit("CHANGELOG.md", CHANGELOG_OLD, CHANGELOG_NEW),
    # AGENTS.md: the CI/CD job table and the date stamp. **Version** tracks pyproject.toml (linted), so it stays.
    Edit(
        "AGENTS.md",
        "| **unit-tests** | 3.12, 3.13, 3.14 | Unit tests with aggregate coverage enforcement |",
        "| **unit-tests** | 3.12, 3.13, 3.14; 3.15 informational (never blocks) | Unit tests with aggregate coverage enforcement |",
    ),
    Edit(
        "AGENTS.md",
        "| **integration-tests** | 3.12, 3.13, 3.14 | Integration-marker test pass",
        "| **integration-tests** | 3.12, 3.13, 3.14; 3.15 informational (never blocks) | Integration-marker test pass",
    ),
    Edit("AGENTS.md", "**Last Updated**: 2026-10-26\n", f"**Last Updated**: {TODAY_ISO}\n"),
    # docs/DEVELOPER_CHEATSHEET.md (header stamp only: **Version** and **Date**)
    Edit(
        "docs/DEVELOPER_CHEATSHEET.md",
        "3. `unit-tests` on Linux for Python 3.12, 3.13, and 3.14 plus macOS Python 3.12.\n",
        "3. `unit-tests` on Linux for Python 3.12, 3.13, and 3.14 plus macOS Python 3.12, and an informational Linux Python 3.15 leg whose failure blocks nothing (phase 1 of the Python 3.15 migration).\n",
    ),
    Edit(
        "docs/DEVELOPER_CHEATSHEET.md",
        "4. `integration-tests` on Python 3.12, 3.13, and 3.14. Failures are reported",
        "4. `integration-tests` on Python 3.12, 3.13, and 3.14, plus an informational Python 3.15 leg whose failure blocks nothing. Failures are reported",
    ),
    Edit(
        "docs/DEVELOPER_CHEATSHEET.md",
        "**Version**: 1.1.1\n**Date**: 2026-10-08\n",
        f"**Version**: 1.1.2\n**Date**: {TODAY_ISO}\n",
    ),
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
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--check", action="store_true", help="report matches only; write nothing")
    args = ap.parse_args()
    return apply(args.worktree, args.check)


if __name__ == "__main__":
    sys.exit(main())
