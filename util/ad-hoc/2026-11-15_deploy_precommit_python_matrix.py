#!/usr/bin/env python3
"""Run juniper-deploy's `Pre-commit` job on Python 3.12, 3.13 and 3.14, every leg blocking (one worktree).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- migration (the Python 3.15 migration arc; this is not a 3.15 change)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_py315_informational_juniper-deploy.py (juniper-deploy#274, which gave the `tests`
         job the same version-less-name matrix); prompts/thread-handoff_automated-prompts/
         HANDOFF_2026-11-15_python-3-15-phase-2-approved-deploy-precommit-matrix.md (Task 1, the plan)

Why this exists
---------------
The owner asked on 2026-11-15: "deploy's pre-commit job should also run on 3.13 and 3.14, with these checks treated
the same as the existing 3.12 check." Every other Juniper repo already runs its pre-commit on 3.12-3.14;
juniper-deploy's ran on `env.PYTHON_VERSION` (3.12) alone.

A plain matrix would stop every merge. Ruleset 14715370 requires the VERSION-LESS context `Pre-commit`, and a matrix
job with a static name posts `Pre-commit (3.12)` and so on, so the required context would never report. The job name
is therefore an expression on `matrix.python-version`, which GitHub uses verbatim (the trick juniper-deploy#274 used
for `Unit Tests`): the 3.12 leg posts exactly `Pre-commit`, the others `Pre-commit (Python 3.13)` and
`Pre-commit (Python 3.14)`.

- All three legs BLOCK: no `experimental` key and no `continue-on-error`, so any failed leg fails the job and so the
  Quality Gate's hard check of `needs.pre-commit.result`.
- setup-python and the hook-cache key use `matrix.python-version`: pre-commit builds the Python hook environments
  with the interpreter it runs under, so one cache per version.
- No pre-commit leg runs 3.15 (the owner's phase-1 ruling of 2026-11-14).
- The ruleset is NOT edited here. "Treated the same" makes the two new contexts required too, but adding them before
  `main` posts them would block every open pull request; that PUT is a separate, later step.

Every edit is an exact-substring replacement that must match exactly once, so the set can be re-applied onto a moved
`origin/main` from a fresh worktree (re-run, never re-type) and a drifted base fails loudly instead of being
half-edited. Nothing is written unless every edit matches, and each written file is read back.

Usage
-----
    python3 util/ad-hoc/2026-11-15_deploy_precommit_python_matrix.py --worktree <juniper-deploy worktree>
    python3 util/ad-hoc/2026-11-15_deploy_precommit_python_matrix.py --worktree <path> --check

``--check`` applies nothing and reports, per edit, whether its old text occurs exactly once (exit 1 otherwise).
Base: juniper-deploy origin/main dd299fbf (2026-11-15, juniper-deploy#275).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

TODAY_ISO = "2026-11-15"  # UTC; the AGENTS.md Date Check compares against the UTC date
CI = ".github/workflows/ci.yml"
CHANGELOG = "CHANGELOG.md"
AGENTS = "AGENTS.md"


@dataclass(frozen=True)
class Edit:
    path: str
    old: str
    new: str


# ---------------------------------------------------------------------------------------------------------------------
# .github/workflows/ci.yml -- the `pre-commit` job, and the `tests` job comment it makes false
# ---------------------------------------------------------------------------------------------------------------------

CI_JOB_OLD = """\
  pre-commit:
    name: Pre-commit
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
  pre-commit:
    # One leg per Python version. The owner asked on 2026-11-15 that this job "also run on 3.13 and
    # 3.14, with these checks treated the same as the existing 3.12 check", so all three legs BLOCK:
    # no leg is `experimental` and the job has no `continue-on-error`, so a failure on any leg fails
    # this job, and so the Quality Gate, which reads `needs.pre-commit.result`. Ruleset 14715370
    # requires the VERSION-LESS context `Pre-commit`. A static name would post `Pre-commit (3.12)`
    # and so on, the required context would never report, and every pull request would wait for it
    # forever. A name that references `matrix` is used verbatim, as in the `tests` job below: the
    # 3.12 leg posts exactly `Pre-commit`, and the others `Pre-commit (Python 3.13)` and
    # `Pre-commit (Python 3.14)`. No pre-commit leg runs 3.15 (the owner's ruling of 2026-11-14,
    # phase 1 of the ecosystem's Python 3.15 migration).
    name: ${{ matrix.python-version == '3.12' && 'Pre-commit' || format('Pre-commit (Python {0})', matrix.python-version) }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
    steps:
      - name: Checkout Code
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
"""

CI_CACHE_OLD = """\
          path: ~/.cache/pre-commit
          key: pre-commit-${{ runner.os }}-${{ env.PYTHON_VERSION }}-${{ hashFiles('.pre-commit-config.yaml') }}
          restore-keys: |
            pre-commit-${{ runner.os }}-${{ env.PYTHON_VERSION }}-
"""

CI_CACHE_NEW = """\
          path: ~/.cache/pre-commit
          # One cache per leg: pre-commit builds the Python hook environments with the interpreter
          # it runs under, so a 3.13 leg has no use for the 3.12 leg's environments.
          key: pre-commit-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('.pre-commit-config.yaml') }}
          restore-keys: |
            pre-commit-${{ runner.os }}-${{ matrix.python-version }}-
"""

CI_TESTS_COMMENT_OLD = """\
    # matrix (phase 1 of the ecosystem's Python 3.15 migration). This job alone has one; every other
    # job runs on `env.PYTHON_VERSION`. Ruleset 14715370 requires the VERSION-LESS context
"""

CI_TESTS_COMMENT_NEW = """\
    # matrix (phase 1 of the ecosystem's Python 3.15 migration). This job and `pre-commit` have one;
    # every other job runs on `env.PYTHON_VERSION`. Ruleset 14715370 requires the VERSION-LESS context
"""

# ---------------------------------------------------------------------------------------------------------------------
# CHANGELOG.md -- a new [Unreleased] entry after juniper-deploy#274's, and that entry's now-false "Unchanged" bullet
# ---------------------------------------------------------------------------------------------------------------------

CHANGELOG_UNCHANGED_OLD = """\
  - Unchanged: `Pre-commit` and every other job, which still run on `env.PYTHON_VERSION` (3.12; no
    3.15 pre-commit in phase 1, by the owner's ruling), `Dockerfile.test` (`python:3.12-slim`, what
    `make test` runs) and every image.
"""

CHANGELOG_UNCHANGED_NEW = """\
  - Unchanged: every other job, which still runs on `env.PYTHON_VERSION` (3.12), `Dockerfile.test`
    (`python:3.12-slim`, what `make test` runs) and every image. `Pre-commit` has since gained 3.13
    and 3.14 legs (the next entry); no pre-commit leg runs 3.15 in phase 1, by the owner's ruling.
"""

CHANGELOG_ENTRY_OLD = """\
  - `docs/testing/TESTING_QUICK_START.md` describes the matrix.

- **An AppArmor-interface preflight runs before every bring-up"""

CHANGELOG_ENTRY_NEW = """\
  - `docs/testing/TESTING_QUICK_START.md` describes the matrix.

- **CI's `Pre-commit` job runs on Python 3.12, 3.13 and 3.14, and every leg blocks merges.** The
  owner asked on 2026-11-15 that it "also run on 3.13 and 3.14, with these checks treated the same
  as the existing 3.12 check"; every other Juniper repository already runs its pre-commit on
  3.12-3.14. `ci.yml`'s `pre-commit` job, which ran on `env.PYTHON_VERSION` (3.12) alone, becomes a
  three-leg matrix:
  - **The 3.12 leg still posts `Pre-commit`**, the version-less context ruleset 14715370 requires.
    The job name is an expression on `matrix.python-version`, as the `tests` job's is. The other legs
    post `Pre-commit (Python 3.13)` and `Pre-commit (Python 3.14)`.
  - **All three legs block**, through the Quality Gate's hard check of `needs.pre-commit.result`:
    no leg is `experimental`, and the job has no `continue-on-error`.
  - Each leg sets up its own Python and keys its hook cache on that version, because pre-commit
    builds the Python hook environments (pre-commit-hooks, shellcheck-py, yamllint) with the
    interpreter it runs under.
  - No pre-commit leg runs 3.15 (the owner's phase-1 ruling of 2026-11-14). `AGENTS.md` § CI/CD
    Pipeline names the three contexts.

- **An AppArmor-interface preflight runs before every bring-up"""

# ---------------------------------------------------------------------------------------------------------------------
# AGENTS.md -- the CI/CD Pipeline table's `pre-commit` row, and the Last Updated date the AGENTS.md Date Check requires
# ---------------------------------------------------------------------------------------------------------------------

AGENTS_ROW_OLD = "| `pre-commit` | YAML, shell, markdown, Python validation | — |\n"
AGENTS_ROW_NEW = (
    "| `pre-commit` | YAML, shell, markdown, Python validation, on Python 3.12, 3.13 and 3.14: one blocking leg each,"
    " posting `Pre-commit`, `Pre-commit (Python 3.13)` and `Pre-commit (Python 3.14)` | — |\n"
)

EDITS: list[Edit] = [
    Edit(CI, CI_JOB_OLD, CI_JOB_NEW),
    Edit(CI, CI_CACHE_OLD, CI_CACHE_NEW),
    Edit(CI, CI_TESTS_COMMENT_OLD, CI_TESTS_COMMENT_NEW),
    Edit(CHANGELOG, CHANGELOG_UNCHANGED_OLD, CHANGELOG_UNCHANGED_NEW),
    Edit(CHANGELOG, CHANGELOG_ENTRY_OLD, CHANGELOG_ENTRY_NEW),
    Edit(AGENTS, AGENTS_ROW_OLD, AGENTS_ROW_NEW),
    Edit(AGENTS, "**Last Updated**: 2026-10-26\n", f"**Last Updated**: {TODAY_ISO}\n"),
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
