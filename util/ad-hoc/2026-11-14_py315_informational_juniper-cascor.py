#!/usr/bin/env python3
"""Apply the Python 3.15 informational-leg edits (phase 1 of the 3.15 migration) to a juniper-cascor worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- migration (phase 1 of the ecosystem's Python 3.15 migration)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_py315_informational_edits.py (the juniper-data pilot, juniper-data#538, whose pattern
         and measurement this reuses); tmp/py315-informational-2026-11-14/survey-ci-2026-11-14.md and
         survey-local-2026-11-14.md (the surveys that list the workflow, doc and test lines touched here)

Why this exists
---------------
The Overtoad's request of 2026-11-14: add Python 3.15 to the tested versions, with the 3.15 checks reporting results but
blocking no commit, merge or deployment. Every edit below is an exact-substring replacement that must match exactly
once, so the set can be re-applied onto a moved ``origin/main`` from a fresh worktree (re-run, never re-type) and a
drifted base fails loudly instead of being half-edited. Nothing is written unless every edit matches.

Design (measured on juniper-data#538, run 43655144734): each matrix job that runs tests over a Python-version list gets
an ``include`` entry, Python "3.15" with ``experimental: true``, and the job-level
``continue-on-error: ${{ matrix.experimental == true }}``, so a failure on that leg leaves the job's result, and so
every gate's ``needs.<job>.result``, unchanged. The new contexts are never added to a ruleset.

In juniper-cascor (base: origin/main 66b39a5c, 2026-11-13, juniper-cascor#757):

- ``ci.yml`` ``unit-tests`` already carries the expression and a macOS ``experimental: false`` include; it gains the
  3.15 include. Its comment still said the macOS leg was in its soak, which juniper-cascor#168 ended on 2026-05-01,
  and "The Linux legs remain required", which the 3.15 leg makes false, so the comment is rewritten.
- The ``test`` jobs of ``ci-protocol.yml`` and ``ci-cascor-model.yml`` (path-filtered, no gate) gain the include and
  the expression. Their version lists are not widened.
- Left alone: ``ci.yml`` ``pre-commit`` (Overtoad ruling: no 3.15 pre-commit in phase 1), ``scheduled-tests.yml`` (every
  job is single-version, on ``PYTHON_TEST_VERSION``), and the WS-6 ``golden-regression.yml`` / ``conformance.yml``
  lanes (one version each, a calibration pin).

The CHANGELOG edit anchors on ``## [Unreleased]`` directly followed by ``### Added``. A release proposal that inserts a
version heading between them (juniper-cascor#758 does) makes it fail to match, which is the point: the entry must not
land silently under a released version.

Usage
-----
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-cascor.py --worktree <path>
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-cascor.py --worktree <path> --check

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
    # surfaces platform-divergence failures (POSIX-only assumptions
    # in the lifecycle / WS / training paths) without blocking PRs
    # while we identify environment-specific issues. After the soak,
    # flip the include block's ``experimental`` flag to false to make
    # the macOS leg required.
    continue-on-error: ${{ matrix.experimental == true }}
"""

CI_COMMENT_NEW = """\
    # METRICS-MON R3.7 / seed-(R1.3 design): the macOS leg ran in
    # continue-on-error mode for a 2-week soak (started 2026-04-30)
    # that surfaced platform-divergence failures (POSIX-only
    # assumptions in the lifecycle / WS / training paths) without
    # blocking PRs. juniper-cascor#168 ended the soak on 2026-05-01 by
    # setting the include block's ``experimental`` flag to false, so a
    # failing macOS leg fails the job; ruleset 15081045 requires its
    # context with the three 3.12-3.14 Linux contexts.
    #
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's
    # 3.15 migration (Overtoad request, 2026-11-14) runs it so its results
    # show, but it must block no merge. It is the only leg with
    # ``experimental: true``, so this expression is true on it alone: a
    # failure there leaves the job's result, which the Quality Gate
    # reads as `needs.unit-tests.result`, unchanged, and the jobs that
    # `needs: [unit-tests]` still run. Measured on juniper-data#538 (run
    # 43655144734): with the 3.15 leg failed on purpose, that gate
    # printed "Unit Tests: success" and its dependent jobs ran. Its
    # context is in no ruleset. Keep both until the Overtoad makes 3.15 a
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
# .github/workflows/ci-cascor-model.yml and ci-protocol.yml -- test (path-filtered, no gate)
# ---------------------------------------------------------------------------------------------------------------------

PKG_COMMENT = """\
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's 3.15
    # migration (Overtoad request, 2026-11-14) runs it so its results show,
    # but it must block nothing. It is the only leg with
    # ``experimental: true``, so this expression is true on it alone: a
    # failure there leaves this job's result at success, so `build`
    # (`needs: test`) still runs, and no ruleset requires its context.
    # Same pattern as ci.yml's unit-tests job, measured on
    # juniper-data#538 (run 43655144734). Keep it until the Overtoad makes
    # 3.15 a required version (phase 3 of the migration).
    continue-on-error: ${{ matrix.experimental == true }}
"""

PKG_INCLUDE = """\
        include:
          - python-version: "3.15"
            experimental: true
"""

MODEL_OLD = """\
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12"]
    defaults:
"""

MODEL_NEW = (
    """\
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
"""
    + PKG_COMMENT
    + """\
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12"]
"""
    + PKG_INCLUDE
    + """\
    defaults:
"""
)

PROTO_OLD = """\
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13"]
    defaults:
"""

PROTO_NEW = (
    """\
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
"""
    + PKG_COMMENT
    + """\
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13"]
"""
    + PKG_INCLUDE
    + """\
    defaults:
"""
)

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
  Python 3.15 migration (the Overtoad's request of 2026-11-14): 3.15 results are reported, and no merge, commit or
  deployment waits on them.
  - `ci.yml`'s `unit-tests` gains `Unit Tests + Coverage (Python 3.15 on ubuntu-latest)`, an `include` entry with
    `experimental: true`. The job's existing `continue-on-error: ${{ matrix.experimental == true }}` applies to that
    leg alone, so a red 3.15 leg leaves `needs.unit-tests.result`, the Quality Gate and the jobs that
    `needs: [unit-tests]` (`quick-integration-tests`, `integration-tests`, `build`) unchanged. The context is not in
    ruleset 15081045. The comment above `continue-on-error` no longer says the macOS leg is in its soak, which #168
    ended on 2026-05-01.
  - The `test` jobs of `ci-protocol.yml` (3.12, 3.13) and `ci-cascor-model.yml` (3.12) gain the same informational
    `Test (Python 3.15)` leg and the job-level expression, so a red 3.15 leg does not stop their `build` jobs. No
    ruleset requires either workflow's contexts.
  - The pattern was measured on juniper-data#538 (run 43655144734): with the 3.15 leg failed on purpose, the leg's
    check read `failure`, that repository's Quality Gate printed `Unit Tests: success` and passed, and every job that
    `needs: [unit-tests]` ran.
  - Unchanged on purpose: `pre-commit` (3.12-3.14; the Overtoad ruled out a 3.15 pre-commit in phase 1), the
    single-version `scheduled-tests.yml`, `golden-regression.yml` and `conformance.yml` lanes, `requires-python`, the
    classifiers, the black, mypy and ruff targets, and the Docker base.
  - `docs/ci_cd/BRANCH_PROTECTION.md` (0.4.5), `docs/ci_cd/MANUAL.md` (0.3.21), `docs/ci_cd/REFERENCE.md` and
    `docs/install/ENVIRONMENT_SETUP.md` describe the legs.
"""

# ---------------------------------------------------------------------------------------------------------------------
# docs/ci_cd/BRANCH_PROTECTION.md (header stamp only; no footer stamp)
# ---------------------------------------------------------------------------------------------------------------------

BP_NOTE_OLD = "| No                       |\n\n**A green Quality Gate does not mean mergeable.**"

BP_NOTE = (
    "`Unit Tests + Coverage (Python 3.15 on ubuntu-latest)` is deliberately not among the 24. Python 3.15 is"
    " informational until the Overtoad makes it a required version (phase 1 of the Python 3.15 migration, 2026-11-14):"
    " the leg's `include` entry sets `experimental: true`, so the job's"
    " `continue-on-error: ${{ matrix.experimental == true }}` keeps a failure there from failing `unit-tests`, and so"
    " from failing the Quality Gate, which reads `needs.unit-tests.result`. The `Test (Python 3.15)` legs of"
    " `ci-protocol.yml` and `ci-cascor-model.yml` work the same way; no context of either workflow is required."
)

BP_NOTE_NEW = "| No                       |\n\n" + BP_NOTE + "\n\n**A green Quality Gate does not mean mergeable.**"

# ---------------------------------------------------------------------------------------------------------------------
# docs/ci_cd/MANUAL.md (header stamp only: **Version**, with a two-space Markdown line break)
# ---------------------------------------------------------------------------------------------------------------------

MANUAL_PKG_PARA_OLD = """\
Both trigger on `paths:` for their package tree (and their workflow file) plus
`workflow_dispatch`. They do **not** replace server `ci.yml`.
"""

MANUAL_PKG_PARA_NEW = """\
Both trigger on `paths:` for their package tree (and their workflow file) plus
`workflow_dispatch`. They do **not** replace server `ci.yml`.

The Python 3.15 legs are informational (phase 1 of the Python 3.15 migration):
each `test` job's `include` entry sets `experimental: true`, and the job-level
`continue-on-error: ${{ matrix.experimental == true }}` lets that leg fail
without failing the job or skipping `build`.
"""

# ---------------------------------------------------------------------------------------------------------------------
# The edit list
# ---------------------------------------------------------------------------------------------------------------------

EDITS: list[Edit] = [
    Edit(".github/workflows/ci.yml", CI_COMMENT_OLD, CI_COMMENT_NEW),
    Edit(".github/workflows/ci.yml", CI_INCLUDE_OLD, CI_INCLUDE_NEW),
    Edit(".github/workflows/ci-cascor-model.yml", MODEL_OLD, MODEL_NEW),
    Edit(".github/workflows/ci-protocol.yml", PROTO_OLD, PROTO_NEW),
    Edit("CHANGELOG.md", CHANGELOG_OLD, CHANGELOG_NEW),
    # docs/ci_cd/BRANCH_PROTECTION.md
    Edit("docs/ci_cd/BRANCH_PROTECTION.md", BP_NOTE_OLD, BP_NOTE_NEW),
    Edit(
        "docs/ci_cd/BRANCH_PROTECTION.md",
        "**Version**: 0.4.4\n**Last Updated**: 2026-10-29\n",
        f"**Version**: 0.4.5\n**Last Updated**: {TODAY_ISO}\n",
    ),
    # docs/ci_cd/MANUAL.md
    Edit(
        "docs/ci_cd/MANUAL.md",
        "| `ci-protocol.yml` | `juniper-cascor-protocol/` | Python 3.12, 3.13 | ",
        "| `ci-protocol.yml` | `juniper-cascor-protocol/` | Python 3.12, 3.13; 3.15 informational (never blocks) | ",
    ),
    Edit(
        "docs/ci_cd/MANUAL.md",
        "| `ci-cascor-model.yml` | `juniper-cascor-model/` | Python 3.12 | ",
        "| `ci-cascor-model.yml` | `juniper-cascor-model/` | Python 3.12; 3.15 informational (never blocks) | ",
    ),
    Edit("docs/ci_cd/MANUAL.md", MANUAL_PKG_PARA_OLD, MANUAL_PKG_PARA_NEW),
    Edit("docs/ci_cd/MANUAL.md", "**Version**: 0.3.20  \n", "**Version**: 0.3.21  \n"),
    # docs/ci_cd/REFERENCE.md (header stamp only: **Last Updated**)
    Edit(
        "docs/ci_cd/REFERENCE.md",
        "| `ci-protocol.yml` | `juniper-cascor-protocol/**` | 3.12, 3.13 | ",
        "| `ci-protocol.yml` | `juniper-cascor-protocol/**` | 3.12, 3.13; 3.15 informational (never blocks) | ",
    ),
    Edit(
        "docs/ci_cd/REFERENCE.md",
        "| `ci-cascor-model.yml` | `juniper-cascor-model/**` | 3.12 | ",
        "| `ci-cascor-model.yml` | `juniper-cascor-model/**` | 3.12; 3.15 informational (never blocks) | ",
    ),
    Edit(
        "docs/ci_cd/REFERENCE.md",
        "- **Matrix Testing**: Single version (expandable)\n",
        "- **Matrix Testing**: `unit-tests` runs Python 3.12, 3.13 and 3.14 on Ubuntu and 3.12 on macOS (all four required), plus an informational Python 3.15 leg on Ubuntu that reports but never blocks; `pre-commit` runs 3.12, 3.13 and 3.14\n",
    ),
    Edit("docs/ci_cd/REFERENCE.md", "**Last Updated**: 2026-10-29\n", f"**Last Updated**: {TODAY_ISO}\n"),
    # docs/install/ENVIRONMENT_SETUP.md (no version or date stamp)
    Edit(
        "docs/install/ENVIRONMENT_SETUP.md",
        "- **CI Uses**: Python 3.14\n",
        "- **CI Uses**: Python 3.14, plus an informational Python 3.15 unit-test leg that reports but blocks nothing (phase 1 of the Python 3.15 migration; 3.15 is not yet a supported version)\n",
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
