#!/usr/bin/env python3
"""Apply the Python 3.15 informational-check edits (phase 1 of the 3.15 migration) to a juniper-recurrence worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- migration (phase 1 of the ecosystem's Python 3.15 migration), juniper-recurrence rollout
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_py315_informational_edits.py (the juniper-data pilot this is modelled on; the
         design was measured on juniper-data#538, run 43655144734); tmp/py315/ROLLOUT_BRIEF.md (the rollout brief);
         tmp/py315-informational-2026-11-14/survey-ci-2026-11-14.md and survey-local-2026-11-14.md (the surveys,
         whose juniper-recurrence sections list the workflow and doc lines touched here)

Why this exists
---------------
The Overtoad's request of 2026-11-14: add Python 3.15 to the tested versions in CI, with the 3.15 checks reporting
results but blocking no commit, merge or deployment. Every edit below is an exact-substring replacement that must
match exactly once, so the set can be re-applied onto a moved ``origin/main`` from a fresh worktree (re-run, never
re-type) and a drifted base fails loudly instead of being half-edited.

Design (settled on the juniper-data pilot): each Python-version matrix gains an ``include`` entry, ``"3.15"`` with
``experimental: true``, and its job gains ``continue-on-error: ${{ matrix.experimental == true }}``, so a failure on
that leg leaves the job's result, and so the lane gate's ``needs.test.result``, unchanged. The leg's context is
never added to a ruleset.

juniper-recurrence has four such matrices, the ``test`` job of each per-package lane: ``ci-recurrence-app.yml``,
``ci-recurrence-client.yml``, ``ci-recurrence-model.yml`` (``Test (Python ...)``) and ``ci-recurrence-bench.yml``
(``Bench smoke (Python ...)``). Each job name already interpolates ``matrix.python-version``, so GitHub posts it
verbatim and no existing context name changes. Left alone on purpose: ``ci-pre-commit.yml`` (the Overtoad ruled no
3.15 pre-commit in phase 1), the model lane's single-version ``test-torch`` job and its comments, every other
single-version job, ``requires-python``, the classifiers, the ruff / mypy targets and the Dockerfile base.

The repo has no root CHANGELOG: the app's ``juniper-recurrence/CHANGELOG.md`` records repo-wide changes ("recorded
here as the bench is", its 0.8.1 entry), so the one entry goes there. ``AGENTS.md``'s ``**Version**`` is the app
version (``scripts/check_version_drift.py`` invariant 3), so only its ``**Last Updated**`` moves, to today's UTC date.
``AGENTS.md`` is metered by the ``Memory Budget`` check (20,000 characters), so its addition is kept short.

Usage
-----
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-recurrence.py --worktree <path>
    python3 util/ad-hoc/2026-11-14_py315_informational_juniper-recurrence.py --worktree <path> --check

``--check`` applies nothing and reports, per edit, whether its old text occurs exactly once (exit 1 otherwise).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# ``date -u +%F`` at the time of the run: the AGENTS.md ``**Last Updated**`` the rollout brief asks for.
TODAY_UTC = datetime.now(timezone.utc).date().isoformat()


@dataclass(frozen=True)
class Edit:
    path: str
    old: str
    new: str


# ---------------------------------------------------------------------------------------------------------------------
# juniper-recurrence. Base: origin/main 0e0c93a6 (2026-11-09, juniper-recurrence#231).
# ---------------------------------------------------------------------------------------------------------------------

APP_TEST_OLD = """\
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [changes]
    if: needs.changes.outputs.app == 'true'
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
    defaults:
"""

APP_TEST_NEW = """\
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [changes]
    if: needs.changes.outputs.app == 'true'
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's 3.15 migration (Overtoad request,
    # 2026-11-14) runs it so its results show, but it must block no merge. It is the only leg with
    # `experimental: true`, so this expression is true on it alone: a failure there leaves the job's
    # result, which `App required checks` reads as `needs.test.result`, unchanged, and `build` and
    # `docker` still run. Measured on juniper-data#538 (run 43655144734): with its 3.15 leg failed on
    # purpose, that repo's gate read the job's result as success and every job that needed it ran.
    # `Test (Python 3.15)` is in no ruleset. Keep both until the Overtoad makes 3.15 a required version
    # (phase 3 of the migration).
    continue-on-error: ${{ matrix.experimental == true }}
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
        include:
          # Informational, never required: see the comment above `continue-on-error`.
          - python-version: "3.15"
            experimental: true
    defaults:
"""

CLIENT_TEST_OLD = """\
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [changes]
    if: needs.changes.outputs.client == 'true'
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
    defaults:
"""

CLIENT_TEST_NEW = """\
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [changes]
    if: needs.changes.outputs.client == 'true'
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's 3.15 migration (Overtoad request,
    # 2026-11-14) runs it so its results show, but it must block no merge. It is the only leg with
    # `experimental: true`, so this expression is true on it alone: a failure there leaves the job's
    # result, which `Client required checks` reads as `needs.test.result`, unchanged, and `build`
    # still runs. Measured on juniper-data#538 (run 43655144734): with its 3.15 leg failed on purpose,
    # that repo's gate read the job's result as success and every job that needed it ran.
    # `Test (Python 3.15)` is in no ruleset. Keep both until the Overtoad makes 3.15 a required version
    # (phase 3 of the migration).
    continue-on-error: ${{ matrix.experimental == true }}
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
        include:
          # Informational, never required: see the comment above `continue-on-error`.
          - python-version: "3.15"
            experimental: true
    defaults:
"""

MODEL_TEST_OLD = """\
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [changes]
    if: needs.changes.outputs.model == 'true'
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
    defaults:
"""

MODEL_TEST_NEW = """\
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [changes]
    if: needs.changes.outputs.model == 'true'
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's 3.15 migration (Overtoad request,
    # 2026-11-14) runs it so its results show, but it must block no merge. It is the only leg with
    # `experimental: true`, so this expression is true on it alone: a failure there leaves the job's
    # result, which `Model required checks` reads as `needs.test.result`, unchanged, and `build`
    # still runs. Measured on juniper-data#538 (run 43655144734): with its 3.15 leg failed on purpose,
    # that repo's gate read the job's result as success and every job that needed it ran.
    # `Test (Python 3.15)` is in no ruleset. Keep both until the Overtoad makes 3.15 a required version
    # (phase 3 of the migration).
    continue-on-error: ${{ matrix.experimental == true }}
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
        include:
          # Informational, never required: see the comment above `continue-on-error`.
          - python-version: "3.15"
            experimental: true
    defaults:
"""

BENCH_TEST_OLD = """\
  test:
    name: Bench smoke (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [changes]
    if: needs.changes.outputs.bench == 'true'
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
    steps:
"""

BENCH_TEST_NEW = """\
  test:
    name: Bench smoke (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [changes]
    if: needs.changes.outputs.bench == 'true'
    # The Python 3.15 leg is INFORMATIONAL: phase 1 of the ecosystem's 3.15 migration (Overtoad request,
    # 2026-11-14) runs it so its results show, but it must block no merge. It is the only leg with
    # `experimental: true`, so this expression is true on it alone: a failure there leaves the job's
    # result, which `Bench required checks` reads as `needs.test.result`, unchanged. The expression
    # does not depend on the event, so on a `juniper-data-published` dispatch a red 3.15 leg leaves
    # the run's conclusion unchanged too. Measured on juniper-data#538 (run 43655144734): with its 3.15
    # leg failed on purpose, that repo's gate read the job's result as success and every job that
    # needed it ran. `Bench smoke (Python 3.15)` is in no ruleset. Keep both until the Overtoad makes
    # 3.15 a required version (phase 3 of the migration).
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

# The aggregate's comment said a matrix job's result is success "only when every leg succeeds"; with the
# continue-on-error 3.15 leg that is no longer true, so it names the exception.
BENCH_GATE_COMMENT_OLD = """\
  # single job depends on the whole matrix (a matrix job's `result` is `success` only when every leg
  # succeeds), so branch protection can require one stable check for the bench lane. `if: always()` so
  # it runs even when `test` fails and reports that failure rather than being skipped. Mirrors the
"""

BENCH_GATE_COMMENT_NEW = """\
  # single job depends on the whole matrix (a matrix job's `result` is `success` only when every leg
  # succeeds, except the informational Python 3.15 leg, whose `continue-on-error` keeps its failure out
  # of the result), so branch protection can require one stable check for the bench lane. `if: always()`
  # so it runs even when `test` fails and reports that failure rather than being skipped. Mirrors the
"""

CHANGELOG_OLD = """\
## [Unreleased]

### Security

- **The image picks up R-OBS-SC-2's two security patches.**"""

CHANGELOG_NEW = """\
## [Unreleased]

### Added

- **CI runs every lane's tests on Python 3.15 as well, as an informational leg that blocks nothing** (repo-wide,
  recorded here as the bench is). Phase 1 of the ecosystem's Python 3.15 migration (the Overtoad's request of
  2026-11-14): 3.15 results are reported, and no merge, commit or deployment waits on them.
  - The `test` jobs of `ci-recurrence-app.yml`, `ci-recurrence-model.yml` and `ci-recurrence-client.yml` gain
    `Test (Python 3.15)`, and `ci-recurrence-bench.yml`'s gains `Bench smoke (Python 3.15)`: an `include` entry
    with `experimental: true`, plus a job-level `continue-on-error: ${{ matrix.experimental == true }}` that is
    true on that leg alone. A red 3.15 leg leaves `needs.test.result` unchanged, so `App`, `Model`, `Client` and
    `Bench required checks`, and the `build` / `docker` jobs that need `test`, are unaffected. No 3.15 context is
    in ruleset `20634527`.
  - The pattern was measured on juniper-data#538 (run 43655144734), with its 3.15 leg failed on purpose: the leg's
    check read `failure`, that repo's gate read the job's result as `success`, and every job that needed it ran.
  - The bench's 3.15 leg also runs on a `juniper-data-published` dispatch. The expression does not depend on the
    event, so a red 3.15 leg leaves that run's conclusion unchanged too.
  - `requires-python`, the classifiers, the ruff and mypy targets, the single-version `Pre-commit (all-files)` and
    `test-torch` jobs, and the image's `python:3.13-slim` base are unchanged.
  - `AGENTS.md` § Testing and the README's Development section describe the leg.

### Security

- **The image picks up R-OBS-SC-2's two security patches.**"""

AGENTS_TESTING_OLD = (
    "CI mirrors these per-package invocations across the Python 3.12 / 3.13 / 3.14 matrix and enforces"
    " `--cov-fail-under=90`. The pytest `addopts` carry"
)

AGENTS_TESTING_NEW = (
    "CI mirrors these per-package invocations across the Python 3.12 / 3.13 / 3.14 matrix and enforces"
    " `--cov-fail-under=90`. Each lane also runs an informational Python 3.15 leg (`experimental: true`,"
    " job-level `continue-on-error`): it reports, but a failure there blocks no gate or merge."
    " The pytest `addopts` carry"
)

README_OLD = """\
Each package is tested from its own subdirectory (CI runs the Python 3.12 / 3.13 / 3.14 matrix at 90%
coverage):
"""

README_NEW = """\
Each package is tested from its own subdirectory (CI runs the Python 3.12 / 3.13 / 3.14 matrix at 90%
coverage, plus an informational Python 3.15 leg that reports results but blocks no merge):
"""

EDITS: list[Edit] = [
    Edit(".github/workflows/ci-recurrence-app.yml", APP_TEST_OLD, APP_TEST_NEW),
    Edit(".github/workflows/ci-recurrence-client.yml", CLIENT_TEST_OLD, CLIENT_TEST_NEW),
    Edit(".github/workflows/ci-recurrence-model.yml", MODEL_TEST_OLD, MODEL_TEST_NEW),
    Edit(".github/workflows/ci-recurrence-bench.yml", BENCH_TEST_OLD, BENCH_TEST_NEW),
    Edit(".github/workflows/ci-recurrence-bench.yml", BENCH_GATE_COMMENT_OLD, BENCH_GATE_COMMENT_NEW),
    Edit("juniper-recurrence/CHANGELOG.md", CHANGELOG_OLD, CHANGELOG_NEW),
    Edit("AGENTS.md", AGENTS_TESTING_OLD, AGENTS_TESTING_NEW),
    Edit("AGENTS.md", "**Last Updated**: 2026-11-04\n", f"**Last Updated**: {TODAY_UTC}\n"),
    Edit("README.md", README_OLD, README_NEW),
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
    print(f"wrote {len(contents)} file(s), {len(EDITS)} edit(s); AGENTS.md **Last Updated** = {TODAY_UTC}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--check", action="store_true", help="report matches only; write nothing")
    args = ap.parse_args()
    return apply(args.worktree, args.check)


if __name__ == "__main__":
    sys.exit(main())
