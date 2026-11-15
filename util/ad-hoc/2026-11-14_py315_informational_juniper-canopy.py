#!/usr/bin/env python3
"""Apply the Python 3.15 informational-check edits (phase 1 of the 3.15 migration) to a juniper-canopy worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- migration (phase 1 of the ecosystem's Python 3.15 migration)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_py315_informational_edits.py (the juniper-data pilot, juniper-data#538, and the
         juniper-ml edits; this script follows its design); tmp/py315/ROLLOUT_BRIEF.md (the rollout brief);
         tmp/py315-informational-2026-11-14/survey-ci-2026-11-14.md and survey-local-2026-11-14.md (the surveys)

Why this exists
---------------
The owner's request of 2026-11-14: add Python 3.15 to the tested versions in CI, with the 3.15 checks reporting
results but blocking no commit, merge or deployment. Every edit below is an exact-substring replacement that must
match exactly once, so the set can be re-applied onto a moved ``origin/main`` from a fresh worktree (re-run, never
re-type) and a drifted base fails loudly instead of being half-edited. Nothing is written unless every edit matches.

Design (measured on juniper-data#538, run 43655144734): the 3.15 leg is a matrix ``include`` entry with
``experimental: true``, and the job's ``continue-on-error: ${{ matrix.experimental == true }}`` makes a failure there
leave the job's result, and so the Quality Gate's ``needs.unit-tests.result``, unchanged. The leg's context is never
added to a ruleset.

What it changes in juniper-canopy (base: origin/main 55ac2168, 2026-11-13, juniper-canopy#817)
-----------------------------------------------------------------------------------------------
- ``.github/workflows/ci.yml``: ``unit-tests`` gains the 3.15 include entry. The job already has the expression
  (from the macOS soak); its comment, which still described the macOS leg as a soak and said "The Linux legs remain
  required", is rewritten. Pre-commit (3.12-3.14) is untouched (owner ruling 2026-11-14), and so are the single-version
  jobs and their commented-out matrices.
- ``.github/workflows/scheduled-tests.yml``: the same leg, plus the job-level expression; the static job name spells
  out the ``(<version>)`` suffix so the existing legs post the same names (juniper-data#538's third commit).
- ``CHANGELOG.md`` and seven docs that describe the CI test matrix; each doc's stamp is bumped once.

Usage
-----
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-canopy.py --worktree <path>
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-canopy.py --worktree <path> --check

``--check`` applies nothing and reports, per edit, whether its old text occurs exactly once (exit 1 otherwise).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

TODAY_ISO = "2026-11-15"  # date -u +%F when the edits were made
TODAY_LONG = "November 15, 2026"


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
    # in the WS / dashboard / dataset paths) without blocking PRs
    # while we identify environment-specific issues. After the soak,
    # flip the include block's ``experimental`` flag to false to make
    # the macOS leg required.
    continue-on-error: ${{ matrix.experimental == true }}
"""

CI_COMMENT_NEW = """\
    # The macOS leg is REQUIRED, like the Linux 3.12, 3.13 and 3.14 legs. METRICS-MON R3.7 /
    # seed-(R1.3 design) added it as a continue-on-error soak (started 2026-04-30), and
    # juniper-canopy#211 ended the soak on 2026-05-01 by setting the include block's
    # ``experimental`` flag to false, so a failing macOS leg fails the job. Ruleset 14249530
    # requires "Unit Tests + Coverage (Python 3.12 on macos-latest)" with the three Linux contexts
    # (read 2026-11-15). The leg surfaces platform-divergence failures (POSIX-only assumptions in
    # the WS / dashboard / dataset paths).
    #
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's 3.15 migration (owner request,
    # 2026-11-14) runs it so its results show, but it must block no merge. It is the only leg with
    # ``experimental: true``, so this expression is true on it alone: a failure there leaves the
    # job's result, which the Quality Gate reads as `needs.unit-tests.result`, unchanged, and the
    # jobs that `needs: [unit-tests]` (integration-tests, build) still run. Measured on
    # juniper-data#538 (run 43655144734), where the gate printed "Unit Tests: success" with the 3.15
    # leg failed on purpose. Its context is in no ruleset. Keep this expression and the leg's include
    # entry until the owner makes 3.15 a required version (phase 3 of the migration).
    continue-on-error: ${{ matrix.experimental == true }}
"""

CI_INCLUDE_OLD = """\
        os: [ubuntu-latest]
        python-version: ["3.12", "3.13", "3.14"]
        include:
          - os: macos-latest
            python-version: "3.12"
            experimental: false

    steps:
"""

CI_INCLUDE_NEW = """\
        os: [ubuntu-latest]
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
# .github/workflows/scheduled-tests.yml -- slow-or-integration-tests
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
    # Python 3.15 is INFORMATIONAL (phase 1 of the 3.15 migration, owner request 2026-11-14): its leg
    # reports, but a failure there fails neither the job nor the run. Same pattern as ci.yml's
    # unit-tests job, measured on juniper-data#538 (run 43655144734). No ruleset requires these
    # contexts. Keep it until the owner makes 3.15 a required version.
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

# The comment names the matrix. juniper_cascor_client 0.8.0 is py3-none-any with requires-python >=3.12 (PyPI JSON,
# read 2026-11-15), so it resolves on the 3.15 leg too.
SCHED_EXTRA_OLD = "          # >=3.12), so it resolves on every leg of the 3.12/3.13/3.14 matrix.\n"
SCHED_EXTRA_NEW = "          # >=3.12), so it resolves on every leg of the matrix, the informational 3.15 one included.\n"

# ---------------------------------------------------------------------------------------------------------------------
# CHANGELOG.md -- first entry under [Unreleased] / Added
# ---------------------------------------------------------------------------------------------------------------------

CHANGELOG_OLD = """\
## [Unreleased]

### Added

- **Regression tests harvested from the Cursor flood-4 test PRs** (canopy#789, #792, #794, #795): four new test
"""

CHANGELOG_NEW = """\
## [Unreleased]

### Added

- **CI runs the unit tests on Python 3.15 as well, as an informational leg that blocks nothing.** Phase 1 of the
  ecosystem's Python 3.15 migration (the owner's request of 2026-11-14): 3.15 results are reported, and no merge,
  commit or deployment waits on them.
  - `ci.yml`'s `unit-tests` gains `Unit Tests + Coverage (Python 3.15 on ubuntu-latest)`, an `include` entry with
    `experimental: true`. The job already carries `continue-on-error: ${{ matrix.experimental == true }}` from the
    macOS soak, and every other leg sets or defaults the flag to false, so the expression is true on the 3.15 leg
    alone: a red 3.15 leg leaves `needs.unit-tests.result`, the Quality Gate and the jobs that `needs: [unit-tests]`
    (`integration-tests`, `build`) unchanged. The context is not in ruleset 14249530. The comment above
    `continue-on-error`, which still described the macOS leg as a soak, now says it has been required since
    juniper-canopy#211 (2026-05-01).
  - `scheduled-tests.yml`'s `Slow / Integration Tests` matrix gains the same informational 3.15 leg. Its job name now
    spells out the `(<version>)` suffix GitHub used to append, so the three existing legs post the same names.
  - The pattern was measured on juniper-data#538 (run 43655144734), with the 3.15 leg failed on purpose: the leg's
    check read `failure`, the Quality Gate printed `Unit Tests: success` and passed, and the jobs behind
    `unit-tests` ran.
  - Pre-commit stays on 3.12-3.14 (the owner's ruling the same day). `requires-python`, the classifiers, the black,
    mypy and ruff targets, the Docker base and the lockfile are unchanged: 3.15 is tested, not yet supported.
  - `docs/REFERENCE.md`, `docs/ci_cd/CICD_REFERENCE.md`, `docs/ci_cd/CICD_QUICK_START.md`,
    `docs/ci_cd/CICD_ENVIRONMENT_SETUP.md`, `docs/ci_cd/CICD_MANUAL.md`, `docs/testing/TESTING_ENVIRONMENT_SETUP.md`
    and `docs/testing/TESTING_MANUAL.md` describe the leg.

- **Regression tests harvested from the Cursor flood-4 test PRs** (canopy#789, #792, #794, #795): four new test
"""

# ---------------------------------------------------------------------------------------------------------------------
# docs/ci_cd/CICD_QUICK_START.md -- the gate list a contributor watches
# ---------------------------------------------------------------------------------------------------------------------

QUICK_START_OLD = """\
- `Sequence Safety` and `Guard PR base branch` (standalone required checks)

`Quality Gate` does **not** include CodeQL."""

QUICK_START_NEW = """\
- `Sequence Safety` and `Guard PR base branch` (standalone required checks)

`Unit Tests + Coverage (Python 3.15 on ubuntu-latest)` runs too and is not a gate: the Python 3.15 leg is informational (phase 1 of the Python 3.15 migration), so a red result there blocks no merge.

`Quality Gate` does **not** include CodeQL."""

# ---------------------------------------------------------------------------------------------------------------------
# docs/ci_cd/CICD_ENVIRONMENT_SETUP.md -- the "Example from ci.yml" snippet
# ---------------------------------------------------------------------------------------------------------------------

ENV_SETUP_SNIPPET_OLD = """\
```yaml
strategy:
  matrix:
    os: [ubuntu-latest]
    python-version: ["3.12", "3.13", "3.14"]
    include:
      - os: macos-latest
        python-version: "3.12"
        experimental: false
```
"""

ENV_SETUP_SNIPPET_NEW = """\
```yaml
continue-on-error: ${{ matrix.experimental == true }}  # true on the 3.15 leg alone
strategy:
  matrix:
    os: [ubuntu-latest]
    python-version: ["3.12", "3.13", "3.14"]
    include:
      - os: macos-latest
        python-version: "3.12"
        experimental: false
      - os: ubuntu-latest  # informational, never required
        python-version: "3.15"
        experimental: true
```
"""

EDITS: list[Edit] = [
    # Workflows
    Edit(".github/workflows/ci.yml", CI_COMMENT_OLD, CI_COMMENT_NEW),
    Edit(".github/workflows/ci.yml", CI_INCLUDE_OLD, CI_INCLUDE_NEW),
    Edit(".github/workflows/scheduled-tests.yml", SCHED_OLD, SCHED_NEW),
    Edit(".github/workflows/scheduled-tests.yml", SCHED_EXTRA_OLD, SCHED_EXTRA_NEW),
    # CHANGELOG
    Edit("CHANGELOG.md", CHANGELOG_OLD, CHANGELOG_NEW),
    # docs/REFERENCE.md (header and footer both carry the stamp)
    Edit(
        "docs/REFERENCE.md",
        "**CI pipeline:** GitHub Actions with multi-version Python testing (3.12-3.14)\n",
        "**CI pipeline:** GitHub Actions with multi-version Python testing (3.12-3.14, plus an informational 3.15 unit-test leg that blocks nothing)\n",
    ),
    Edit(
        "docs/REFERENCE.md",
        "**Version:** 0.26.0\n**Status:** Active\n**Last Updated:** November 7, 2026\n",
        "**Version:** 0.26.1\n**Status:** Active\n**Last Updated:** " + TODAY_LONG + "\n",
    ),
    Edit(
        "docs/REFERENCE.md",
        "**Last Updated:** November 7, 2026\n**Version:** 0.26.0\n",
        "**Last Updated:** " + TODAY_LONG + "\n**Version:** 0.26.1\n",
    ),
    # docs/ci_cd/CICD_REFERENCE.md (header and footer both carry the stamp)
    Edit(
        "docs/ci_cd/CICD_REFERENCE.md",
        "| `unit-tests`        | `pre-commit`      | Ubuntu matrix `3.12/3.13/3.14` + macOS `3.12` | Runs unit + regression markers with coverage gate |\n",
        "| `unit-tests`        | `pre-commit`      | Ubuntu matrix `3.12/3.13/3.14` + macOS `3.12`; Ubuntu `3.15` informational (never blocks) | Runs unit + regression markers with coverage gate |\n",
    ),
    Edit(
        "docs/ci_cd/CICD_REFERENCE.md",
        "**Last Updated:** 2026-11-12\n**Version:** 0.30.2\n**Status:** Current\n",
        "**Last Updated:** " + TODAY_ISO + "\n**Version:** 0.30.3\n**Status:** Current\n",
    ),
    Edit(
        "docs/ci_cd/CICD_REFERENCE.md",
        "**Last Updated:** 2026-11-12\n**Version:** 0.30.2\n**Maintained By:**",
        "**Last Updated:** " + TODAY_ISO + "\n**Version:** 0.30.3\n**Maintained By:**",
    ),
    # docs/ci_cd/CICD_QUICK_START.md (the stamp lines end in two spaces: markdown line breaks)
    Edit("docs/ci_cd/CICD_QUICK_START.md", QUICK_START_OLD, QUICK_START_NEW),
    Edit(
        "docs/ci_cd/CICD_QUICK_START.md",
        "**Last Updated:** 2026-11-12  \n**Time to Complete:** ~5 minutes  \n**Version:** 0.27.4  \n",
        "**Last Updated:** " + TODAY_ISO + "  \n**Time to Complete:** ~5 minutes  \n**Version:** 0.27.5  \n",
    ),
    # docs/ci_cd/CICD_ENVIRONMENT_SETUP.md
    Edit(
        "docs/ci_cd/CICD_ENVIRONMENT_SETUP.md",
        "- Matrix jobs (`pre-commit`, `unit-tests`): Ubuntu Python `3.12`, `3.13`, `3.14`; unit tests also run on required macOS Python `3.12`\n",
        "- Matrix jobs (`pre-commit`, `unit-tests`): Ubuntu Python `3.12`, `3.13`, `3.14`; unit tests also run on required macOS Python `3.12`, and on an informational Ubuntu Python `3.15` leg that blocks nothing (phase 1 of the Python 3.15 migration)\n",
    ),
    Edit("docs/ci_cd/CICD_ENVIRONMENT_SETUP.md", ENV_SETUP_SNIPPET_OLD, ENV_SETUP_SNIPPET_NEW),
    Edit(
        "docs/ci_cd/CICD_ENVIRONMENT_SETUP.md",
        "**Last Updated:** 2026-11-09\n**Version:** 0.28.4\n",
        "**Last Updated:** " + TODAY_ISO + "\n**Version:** 0.28.5\n",
    ),
    # docs/ci_cd/CICD_MANUAL.md
    Edit(
        "docs/ci_cd/CICD_MANUAL.md",
        "   - ✓ Unit Tests Python 3.12/3.13/3.14 (~8 min each)\n",
        "   - ✓ Unit Tests Python 3.12/3.13/3.14 (~8 min each); the informational Python 3.15 leg can fail without blocking the PR\n",
    ),
    Edit(
        "docs/ci_cd/CICD_MANUAL.md",
        "**Last Updated:** 2026-11-12\n**Version:** 0.29.1\n",
        "**Last Updated:** " + TODAY_ISO + "\n**Version:** 0.29.2\n",
    ),
    # docs/testing/TESTING_ENVIRONMENT_SETUP.md
    Edit(
        "docs/testing/TESTING_ENVIRONMENT_SETUP.md",
        "- **Python**: 3.11 or newer (CI parity targets 3.12, 3.13, and 3.14)\n",
        "- **Python**: 3.11 or newer (CI parity targets 3.12, 3.13, and 3.14; CI's Python 3.15 unit-test leg is informational and blocks nothing)\n",
    ),
    Edit(
        "docs/testing/TESTING_ENVIRONMENT_SETUP.md",
        "- Python `3.12+` (CI validates on `3.12`, `3.13`, `3.14`)\n",
        "- Python `3.12+` (CI validates on `3.12`, `3.13`, `3.14`, plus an informational `3.15` unit-test leg that blocks nothing)\n",
    ),
    Edit(
        "docs/testing/TESTING_ENVIRONMENT_SETUP.md",
        "# Should be: Python 3.11+ (CI parity: 3.12/3.13/3.14)\n",
        "# Should be: Python 3.11+ (CI parity: 3.12/3.13/3.14; CI's 3.15 leg is informational)\n",
    ),
    Edit(
        "docs/testing/TESTING_ENVIRONMENT_SETUP.md",
        "**Last Updated:** April 5, 2026\n**Version:** v0.26.0\n",
        "**Last Updated:** " + TODAY_LONG + "\n**Version:** v0.26.1\n",
    ),
    # docs/testing/TESTING_MANUAL.md (the date line ends in two spaces: a markdown line break)
    Edit(
        "docs/testing/TESTING_MANUAL.md",
        "- Python matrix `3.12`, `3.13`, `3.14` for `pre-commit` and `unit-tests`\n",
        "- Python matrix `3.12`, `3.13`, `3.14` for `pre-commit` and `unit-tests`, plus an informational `3.15` leg in `unit-tests` that blocks nothing\n",
    ),
    Edit(
        "docs/testing/TESTING_MANUAL.md",
        "**Last Updated:** 2026-09-05  \n**Version:** v0.26.2\n",
        "**Last Updated:** " + TODAY_ISO + "  \n**Version:** v0.26.3\n",
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
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--worktree", required=True, type=Path, help="root of a juniper-canopy worktree based on origin/main")
    ap.add_argument("--check", action="store_true", help="report matches only; write nothing")
    args = ap.parse_args()
    return apply(args.worktree, args.check)


if __name__ == "__main__":
    sys.exit(main())
