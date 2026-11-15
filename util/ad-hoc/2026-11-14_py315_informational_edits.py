#!/usr/bin/env python3
"""Apply the Python 3.15 informational-check edits (phase 1 of the 3.15 migration) to one repo's worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- migration (phase 1 of the ecosystem's Python 3.15 migration)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-14_python-3-15-informational-checks-phase-1-surveyed.md
         (the arc's handoff, which holds the owner's request and the design question this settles);
         tmp/py315-informational-2026-11-14/survey-ci-2026-11-14.md and survey-local-2026-11-14.md (the surveys
         that list every file and line touched here)

Why this exists
---------------
The owner's request of 2026-11-14: add Python 3.15 to the tested versions in CI and in local test infrastructure,
with the 3.15 checks reporting results but blocking no commit, merge or deployment. Every edit below is an
exact-substring replacement that must match exactly once, so the set can be re-applied onto a moved ``origin/main``
from a fresh worktree (re-run, never re-type) and a drifted base fails loudly instead of being half-edited.

Design (settled on the juniper-data pilot): the 3.15 leg is a matrix ``include`` entry with ``experimental: true``,
and the job's ``continue-on-error: ${{ matrix.experimental == true }}`` makes a failure there leave the job's result,
and so every gate's ``needs.<job>.result``, unchanged. The leg's context is never added to a ruleset.

``--probe`` also adds a TEMPORARY step that fails the 3.15 leg on purpose, so one CI run shows what the Quality Gate
reads when only the ``continue-on-error`` leg failed. It must never reach ``main``: re-run without ``--probe`` on a
fresh copy of the files and push that as the next commit.

Usage
-----
    python3 util/ad-hoc/2026-11-14_py315_informational_edits.py --repo juniper-data --worktree <path> [--probe]
    python3 util/ad-hoc/2026-11-14_py315_informational_edits.py --repo juniper-data --worktree <path> --check

``--check`` applies nothing and reports, per edit, whether its old text occurs exactly once (exit 1 otherwise).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

TODAY_LONG = "November 14, 2026"


@dataclass(frozen=True)
class Edit:
    path: str
    old: str
    new: str
    probe_only: bool = False


# ---------------------------------------------------------------------------------------------------------------------
# juniper-data (the pilot). Base: origin/main 3cf8867c (2026-11-12, juniper-data#537).
# ---------------------------------------------------------------------------------------------------------------------

DATA_CI_COMMENT_OLD = """\
    # The macOS leg is REQUIRED, like the three Linux legs. METRICS-MON R3.7 / seed-(R1.3 design)
    # added it as a continue-on-error soak (juniper-data#61), and juniper-data#63 ended the soak on
    # 2026-05-01 by setting the include block's ``experimental`` flag to false, so this expression
    # is false on every leg and a failing macOS leg fails the job. Ruleset 14748749 requires
    # "Unit Tests + Coverage (Python 3.12 on macos-latest)" with the three Linux contexts (read
    # 2026-10-29). The leg catches platform divergence: cross-platform rss_mb sampling, POSIX-only
    # assumptions, and BSD tools (macOS `base64` has no `-w0`; juniper-data#467 and #498 both met it).
    continue-on-error: ${{ matrix.experimental == true }}
"""

DATA_CI_COMMENT_NEW = """\
    # The macOS leg is REQUIRED, like the three Linux legs. METRICS-MON R3.7 / seed-(R1.3 design)
    # added it as a continue-on-error soak (juniper-data#61), and juniper-data#63 ended the soak on
    # 2026-05-01 by setting the include block's ``experimental`` flag to false, so a failing macOS
    # leg fails the job. Ruleset 14748749 requires
    # "Unit Tests + Coverage (Python 3.12 on macos-latest)" with the three Linux contexts (read
    # 2026-10-29). The leg catches platform divergence: cross-platform rss_mb sampling, POSIX-only
    # assumptions, and BSD tools (macOS `base64` has no `-w0`; juniper-data#467 and #498 both met it).
    #
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's 3.15 migration (owner request,
    # 2026-11-14) runs it so its results show, but it must block no merge. It is the only leg with
    # ``experimental: true``, so this expression is true on it alone: a failure there leaves the
    # job's result, which the Quality Gate reads as `needs.unit-tests.result`, unchanged, and the jobs
    # that `needs: [unit-tests]` still run. Measured on juniper-data#538 (run 43655144734): with the
    # 3.15 leg failed on purpose, the gate printed "Unit Tests: success" and build, integration-tests,
    # dependency-docs and docker-build ran. Its context is not in the ruleset. Keep both until the
    # owner makes 3.15 a required version (phase 3 of the migration).
    continue-on-error: ${{ matrix.experimental == true }}
"""

DATA_CI_INCLUDE_OLD = """\
        python-version: ["3.12", "3.13", "3.14"]
        include:
          - os: macos-latest
            python-version: "3.12"
            experimental: false

    steps:
"""

DATA_CI_INCLUDE_NEW = """\
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

DATA_CI_PROBE_OLD = """\
      - name: Upload Test Results
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9  # v7.0.2
        if: always()
        with:
          name: unit-test-results-py${{ matrix.python-version }}
          path: reports/junit-unit.xml
          retention-days: 30

  # ═══════════════════════════════════════════════════════════════════════════════════════════════
  # Build: Build sdist and wheel artifacts
"""

DATA_CI_PROBE_NEW = """\
      - name: Upload Test Results
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9  # v7.0.2
        if: always()
        with:
          name: unit-test-results-py${{ matrix.python-version }}
          path: reports/junit-unit.xml
          retention-days: 30

      - name: "Pilot probe (TEMPORARY, removed before merge): fail the informational leg"
        # Makes the 3.15 leg fail whatever its tests do, so this pull request's run shows what the
        # Quality Gate reads in `needs.unit-tests.result` when only the continue-on-error leg failed.
        if: always() && matrix.experimental == true
        run: |
          echo "::warning::Deliberate failure of the informational Python 3.15 leg (pilot probe)"
          exit 1

  # ═══════════════════════════════════════════════════════════════════════════════════════════════
  # Build: Build sdist and wheel artifacts
"""

DATA_SCHED_OLD = """\
  slow-or-integration-tests:
    name: Slow / Integration Tests
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
    steps:
"""

DATA_SCHED_NEW = """\
  slow-or-integration-tests:
    # The name spells out the suffix GitHub appended to the old static name ("Slow / Integration
    # Tests (3.14)"), so the three blocking legs post the same names as before, and the 3.15 leg is
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

DATA_CHANGELOG_OLD = """\
### Added

- **Tests pin the coverage gates, the Bandit SARIF upload, the image `Publish manifest` job, the TestPyPI install
"""

DATA_CHANGELOG_NEW = """\
### Added

- **CI runs the unit tests on Python 3.15 as well, as an informational leg that blocks nothing.** Phase 1 of the
  ecosystem's Python 3.15 migration (the owner's request of 2026-11-14): 3.15 results are reported, and no merge,
  commit or deployment waits on them.
  - `unit-tests` gains `Unit Tests + Coverage (Python 3.15 on ubuntu-latest)`, an `include` entry with
    `experimental: true`. The job's existing `continue-on-error: ${{ matrix.experimental == true }}` applies to that
    leg alone, so a red 3.15 leg leaves `needs.unit-tests.result`, the Quality Gate and the jobs that
    `needs: [unit-tests]` unchanged. The context is not in ruleset 14748749.
  - Measured on juniper-data#538 (run 43655144734), with the 3.15 leg failed on purpose by a temporary last step: the
    leg's check read `failure`, the Quality Gate printed `Unit Tests: success` and passed, and `build`,
    `integration-tests`, `dependency-docs` and `docker-build` ran. Every real step of that leg passed on CPython
    3.15.2: 2401 passed, 14 skipped, 98.12% coverage.
  - `scheduled-tests.yml`'s `Slow / Integration Tests` matrix gains the same informational 3.15 leg. Its job name now
    spells out the `(<version>)` suffix GitHub used to append, so the three existing legs post the same names.
  - `requires-python`, the classifiers, the mypy and ruff targets, pre-commit and the Docker base are unchanged.
  - `docs/ci_cd/CICD_MANUAL.md`, `docs/ci_cd/CICD_REFERENCE.md` and `docs/REFERENCE.md` describe the leg.
- **Tests pin the coverage gates, the Bandit SARIF upload, the image `Publish manifest` job, the TestPyPI install
"""

DATA_EDITS: list[Edit] = [
    Edit(".github/workflows/ci.yml", DATA_CI_COMMENT_OLD, DATA_CI_COMMENT_NEW),
    Edit(".github/workflows/ci.yml", DATA_CI_INCLUDE_OLD, DATA_CI_INCLUDE_NEW),
    Edit(".github/workflows/ci.yml", DATA_CI_PROBE_OLD, DATA_CI_PROBE_NEW, probe_only=True),
    Edit(".github/workflows/scheduled-tests.yml", DATA_SCHED_OLD, DATA_SCHED_NEW),
    Edit(
        "docs/REFERENCE.md",
        '`pytest -m "slow or integration"` on 3.12, 3.13 and 3.14 over a `.[all]` install',
        '`pytest -m "slow or integration"` on 3.12, 3.13 and 3.14, plus an informational 3.15 leg (`continue-on-error`), over a `.[all]` install',
    ),
    Edit("CHANGELOG.md", DATA_CHANGELOG_OLD, DATA_CHANGELOG_NEW),
    # docs/ci_cd/CICD_MANUAL.md
    Edit(
        "docs/ci_cd/CICD_MANUAL.md",
        "- **GitHub Actions CI**: Automated testing across Python 3.12/3.13/3.14 on Ubuntu and 3.12 on macOS, coverage gates",
        "- **GitHub Actions CI**: Automated testing across Python 3.12/3.13/3.14 on Ubuntu and 3.12 on macOS (plus an informational Python 3.15 leg on Ubuntu that reports but never blocks), coverage gates",
    ),
    Edit(
        "docs/ci_cd/CICD_MANUAL.md",
        "Core test execution with coverage enforcement across Python 3.12, 3.13, and 3.14 on Ubuntu, and 3.12 on macOS. All four legs are required contexts; none is allowed to fail.\n",
        "Core test execution with coverage enforcement across Python 3.12, 3.13, and 3.14 on Ubuntu, and 3.12 on macOS. All four legs are required contexts; none is allowed to fail. A fifth leg, Python 3.15 on Ubuntu, is informational (phase 1 of the Python 3.15 migration): it runs the same steps, but its `include` entry sets `experimental: true`, so the job-level `continue-on-error: ${{ matrix.experimental == true }}` lets it fail without failing the job, and no ruleset requires its context.\n",
    ),
    Edit(
        "docs/ci_cd/CICD_MANUAL.md",
        "**CI fails but local passes**: Check Python version matrix. CI tests on 3.12, 3.13, and 3.14. Ensure your local environment matches.",
        "**CI fails but local passes**: Check Python version matrix. CI tests on 3.12, 3.13, and 3.14, plus an informational 3.15 leg whose failure blocks nothing. Ensure your local environment matches.",
    ),
    Edit("docs/ci_cd/CICD_MANUAL.md", "**Version:** 0.4.6\n", "**Version:** 0.4.7\n"),
    Edit("docs/ci_cd/CICD_MANUAL.md", "**Last Updated:** November 12, 2026\n", f"**Last Updated:** {TODAY_LONG}\n"),
    # docs/ci_cd/CICD_REFERENCE.md (the header and the footer both carry the stamp)
    Edit(
        "docs/ci_cd/CICD_REFERENCE.md",
        "| `unit-tests` | pre-commit | 3.12, 3.13, 3.14 on Ubuntu; 3.12 on macOS | Always | Unit tests with the coverage gates |",
        "| `unit-tests` | pre-commit | 3.12, 3.13, 3.14 on Ubuntu; 3.12 on macOS; 3.15 on Ubuntu (informational, never blocks) | Always | Unit tests with the coverage gates |",
    ),
    Edit(
        "docs/ci_cd/CICD_REFERENCE.md",
        "**Version:** 0.4.6\n**Status:** Active\n**Last Updated:** November 12, 2026\n",
        f"**Version:** 0.4.7\n**Status:** Active\n**Last Updated:** {TODAY_LONG}\n",
    ),
    Edit(
        "docs/ci_cd/CICD_REFERENCE.md",
        "**Last Updated:** November 12, 2026\n**Version:** 0.4.6\n",
        f"**Last Updated:** {TODAY_LONG}\n**Version:** 0.4.7\n",
    ),
    # docs/REFERENCE.md (the header and the footer both carry the stamp)
    Edit(
        "docs/REFERENCE.md",
        "unit tests with the coverage gates on Ubuntu 3.12-3.14 and macOS 3.12; build;",
        "unit tests with the coverage gates on Ubuntu 3.12-3.14 and macOS 3.12, plus an informational Ubuntu 3.15 leg that is not required; build;",
    ),
    Edit(
        "docs/REFERENCE.md",
        "- `pr-base-branch-guard.yml` (1): `Guard PR base branch`.\n",
        "- `pr-base-branch-guard.yml` (1): `Guard PR base branch`.\n\n"
        "`Unit Tests + Coverage (Python 3.15 on ubuntu-latest)` is deliberately not among them. The Python 3.15 leg is"
        " informational until 3.15 becomes a required version: its `include` entry sets `experimental: true`, so the"
        " job's `continue-on-error` keeps a failure there from failing `unit-tests` or the Quality Gate.\n",
    ),
    Edit(
        "docs/REFERENCE.md",
        "CI enforces two gates, on each of the four required `Unit Tests + Coverage` legs (Ubuntu 3.12, 3.13 and 3.14; macOS 3.12).",
        "CI enforces two gates, on each of the four required `Unit Tests + Coverage` legs (Ubuntu 3.12, 3.13 and 3.14; macOS 3.12). The informational Ubuntu 3.15 leg runs the same gates, but a failure there blocks nothing.",
    ),
    Edit(
        "docs/REFERENCE.md",
        "**Version:** 0.4.8\n**Status:** Active\n**Last Updated:** November 13, 2026\n",
        f"**Version:** 0.4.9\n**Status:** Active\n**Last Updated:** {TODAY_LONG}\n",
    ),
    Edit(
        "docs/REFERENCE.md",
        "**Last Updated:** November 13, 2026\n**Version:** 0.4.8\n",
        f"**Last Updated:** {TODAY_LONG}\n**Version:** 0.4.9\n",
    ),
]

# ---------------------------------------------------------------------------------------------------------------------
# juniper-ml. Base: origin/main 16f2512b (2026-11-14, juniper-ml#2566).
# ---------------------------------------------------------------------------------------------------------------------

ML_TESTS_OLD = """\
  tests:
    name: Regression Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [pre-commit]
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
    steps:
"""

ML_TESTS_NEW = """\
  tests:
    name: Regression Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [pre-commit]
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's 3.15 migration (owner request,
    # 2026-11-14) runs it so its results show, but it must block no merge. It is the only leg with
    # `experimental: true`, so this expression is true on it alone: a failure there leaves the job's
    # result unchanged, and the Quality Gate's `needs.tests.result` reads `success`. Measured on
    # juniper-data#538 (run 43655144734), where the gate printed "Unit Tests: success" with the 3.15
    # leg failed on purpose. Its context is in no ruleset. Keep both until the owner makes 3.15 a
    # required version (phase 3 of the migration).
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

ML_SUBPACKAGE_VERSIONS = {
    "ci-ci-tools": '["3.11", "3.12", "3.13", "3.14"]',
    "ci-config-tools": '["3.11", "3.12", "3.13", "3.14"]',
    "ci-doc-tools": '["3.12", "3.13", "3.14"]',
    "ci-model-core": '["3.12", "3.13", "3.14"]',
    "ci-observability": '["3.12", "3.13"]',
    "ci-service-core": '["3.12", "3.13"]',
}


def _subpackage_edit(workflow: str, versions: str) -> Edit:
    old = (
        "  test:\n"
        "    name: Test (Python ${{ matrix.python-version }})\n"
        "    runs-on: ubuntu-latest\n"
        "    strategy:\n"
        "      fail-fast: false\n"
        "      matrix:\n"
        f"        python-version: {versions}\n"
    )
    new = (
        "  test:\n"
        "    name: Test (Python ${{ matrix.python-version }})\n"
        "    runs-on: ubuntu-latest\n"
        "    # Python 3.15 is INFORMATIONAL (phase 1 of the 3.15 migration, 2026-11-14): its leg reports, but a\n"
        "    # failure there fails neither this job nor the run. Same pattern as ci.yml's `tests` job.\n"
        "    continue-on-error: ${{ matrix.experimental == true }}\n"
        "    strategy:\n"
        "      fail-fast: false\n"
        "      matrix:\n"
        f"        python-version: {versions}\n"
        "        include:\n"
        '          - python-version: "3.15"\n'
        "            experimental: true\n"
    )
    return Edit(f".github/workflows/{workflow}.yml", old, new)


ML_CHANGELOG_OLD = """\
## [Unreleased]

### Added

"""

ML_CHANGELOG_NEW = """\
## [Unreleased]

### Added

- **CI runs the regression tests and every sub-package's tests on Python 3.15 as well, as informational legs that
  block nothing.** Phase 1 of the ecosystem's Python 3.15 migration (the owner's request of 2026-11-14): 3.15
  results are reported, and no merge, commit or deployment waits on them.
  - `ci.yml`'s `Regression Tests` and the `test` job of all six `ci-<pkg>.yml` workflows gain an `include` entry,
    Python `"3.15"` with `experimental: true`, and the job-level `continue-on-error: ${{ matrix.experimental == true }}`,
    which is true on that leg alone. A red 3.15 leg leaves the job's result, and so the Quality Gate's
    `needs.tests.result`, at `success`; no ruleset requires the new contexts. Measured on juniper-data#538 (run
    43655144734): with the 3.15 leg failed on purpose, the gate printed `Unit Tests: success` and passed.
  - Pre-commit stays on 3.12-3.14 (the owner's ruling the same day), and `requires-python`, the classifiers and the
    tool targets are unchanged: 3.15 is tested, not yet supported.
  - `util/ad-hoc/2026-11-14_py315_informational_edits.py` applies this change and juniper-data#538's as exact,
    re-runnable replacements. `docs/REFERENCE.md` § Shared-Package CI Workflows says so.

"""

# The version-history table runs 0.6.61 .. 0.6.69 and is then followed by an out-of-order 0.6.22 row; the new row
# goes directly after 0.6.69, i.e. directly before that 0.6.22 row.
ML_REF_HISTORY_OLD = "\n| 0.6.22  | 2026-09-04 | X7 off-loop census"
ML_REF_HISTORY_NEW = (
    "\n| 0.6.70  | 2026-11-15 | Python 3.15 informational CI legs (phase 1 of the 3.15 migration, owner request"
    " 2026-11-14): `ci.yml`'s `Regression Tests` and the six `ci-<pkg>.yml` test matrices each run a 3.15 leg under"
    " `continue-on-error: ${{ matrix.experimental == true }}`, which reports and blocks nothing (§ Shared-Package CI Workflows) |"
    "\n| 0.6.22  | 2026-09-04 | X7 off-loop census"
)

ML_EDITS: list[Edit] = [
    Edit(".github/workflows/ci.yml", ML_TESTS_OLD, ML_TESTS_NEW),
    *[_subpackage_edit(w, v) for w, v in ML_SUBPACKAGE_VERSIONS.items()],
    Edit("CHANGELOG.md", ML_CHANGELOG_OLD, ML_CHANGELOG_NEW),
    Edit(
        "docs/REFERENCE.md",
        "Matrix rows are **minimum floors** — extra versions are fine.",
        "Matrix rows are **minimum floors** — extra versions are fine. Each workflow also runs an informational Python"
        " 3.15 leg (an `include` entry with `experimental: true`, under the job-level"
        " `continue-on-error: ${{ matrix.experimental == true }}`), and so does `ci.yml`'s `Regression Tests`: it"
        " reports, and a failure there fails neither the job nor the run (phase 1 of the Python 3.15 migration,"
        " 2026-11-14; no ruleset requires a 3.15 context).",
    ),
    Edit(
        "docs/REFERENCE.md",
        "1. `ci-observability.yml` runs package tests on Python 3.12 and 3.13, then builds",
        "1. `ci-observability.yml` runs package tests on Python 3.12 and 3.13 (plus an informational 3.15 leg), then builds",
    ),
    Edit(
        "docs/REFERENCE.md",
        "CI: `ci-config-tools.yml`, Python 3.11–3.14, `--cov-fail-under=85`",
        "CI: `ci-config-tools.yml`, Python 3.11–3.14 plus an informational 3.15 leg, `--cov-fail-under=85`",
    ),
    Edit(
        "docs/REFERENCE.md",
        "**Version:** 0.6.69\n**Status:** Active\n**Last Updated:** 2026-11-13\n",
        "**Version:** 0.6.70\n**Status:** Active\n**Last Updated:** 2026-11-15\n",
    ),
    Edit("docs/REFERENCE.md", "**Last Updated:** 2026-11-13\n**Version:** 0.6.69\n", "**Last Updated:** 2026-11-15\n**Version:** 0.6.70\n"),
    Edit("docs/REFERENCE.md", ML_REF_HISTORY_OLD, ML_REF_HISTORY_NEW),
]

EDITS: dict[str, list[Edit]] = {
    "juniper-data": DATA_EDITS,
    "juniper-ml": ML_EDITS,
}


def apply(repo: str, worktree: Path, probe: bool, check_only: bool) -> int:
    edits = [e for e in EDITS[repo] if probe or not e.probe_only]
    contents: dict[str, str] = {}
    bad = 0
    for e in edits:
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
        print(f"check: all {len(edits)} edit(s) match exactly once")
        return 0
    for rel, text in contents.items():
        path = worktree / rel
        path.write_text(text, encoding="utf-8")
        if path.read_text(encoding="utf-8") != text:  # read back our own write
            print(f"READ-BACK MISMATCH: {rel}", file=sys.stderr)
            return 1
    print(f"wrote {len(contents)} file(s), {len(edits)} edit(s){' (with the pilot probe)' if probe else ''}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True, choices=sorted(EDITS))
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--probe", action="store_true", help="also add the TEMPORARY forced-failure step (pilot only)")
    ap.add_argument("--check", action="store_true", help="report matches only; write nothing")
    args = ap.parse_args()
    return apply(args.repo, args.worktree, args.probe, args.check)


if __name__ == "__main__":
    sys.exit(main())
