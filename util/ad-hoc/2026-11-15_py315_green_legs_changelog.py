#!/usr/bin/env python3
"""Add the green-informational-Python-3.15-legs CHANGELOG entry to a juniper-data-client, juniper-cascor-client or juniper-deploy worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- migration (phase 1 of the ecosystem's Python 3.15 migration, the green-legs follow-up)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_py315_informational_green_legs.py (juniper-ml#2578; it makes the workflow edits this
         entry describes); util/ad-hoc/2026-11-14_py315_informational_juniper-data-client.py (the phase-1 script whose
         checks and structure this follows); tmp/py315/GREEN_LEGS_BRIEF.md (the rollout brief)

Why this exists
---------------
The owner's report of 2026-11-15: the Python 3.15 checks "are supposed to produce an informational message without
affecting the ability of code to commit, push, PR, or merge". juniper-ml#2578 makes each informational 3.15 leg
conclude green and report its failures as a warning; ``2026-11-15_py315_informational_green_legs.py`` applies that to
these three repos' workflows, and this script adds the matching ``[Unreleased]`` / ``### Fixed`` entry to each one's
CHANGELOG. The entry is an exact-substring insertion that must match exactly once, above the first released
section, so it can be re-applied onto a moved ``origin/main`` (re-run, never re-type). Nothing is written unless the
anchor matches.

Usage
-----
    python3 util/ad-hoc/2026-11-15_py315_green_legs_changelog.py --repo <repo> --worktree <path> [--check]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

CLIENT_ENTRY = """\
- **The informational Python 3.15 legs no longer show as failed checks when they fail** (the owner's report of
  2026-11-15: the 3.15 checks "are supposed to produce an informational message without affecting the ability of
  code to commit, push, PR, or merge"). {pr}'s job-level `continue-on-error` keeps the Quality Gate green, but a
  failing 3.15 leg's own check still concluded `failure`: a red X and "Some checks were not successful" on the pull
  request, a merge state of `UNSTABLE`, and a failure for `gh pr checks` and any tool that reads every check. Here
  the 3.15 unit and integration legs pass, but the daily `Slow / Integration Tests (3.15)` leg fails, as every leg of
  `scheduled-tests.yml` does, on the pre-existing `Unknown marker(s) in '-m' expression: slow` error. The run
  dispatched on {pr}'s head put that red check on the pull request.
  - Every step of `.github/workflows/ci.yml`'s `unit-tests` and `integration-tests` jobs and of
    `.github/workflows/scheduled-tests.yml`'s `slow-or-integration-tests` job now carries an `id` and
    `continue-on-error: ${{{{ matrix.experimental == true }}}}`, so on the 3.15 leg a failing step neither stops the
    job nor turns its check red. A last step, `Report the informational Python 3.15 result`, reports each failed step
    as a `::warning` annotation and as a table in the job summary, and emits a `::notice` when every step passed.
  - The blocking legs are unchanged, because the expression is false on them, and no check changes its name. The
    3.12-3.14 legs of `scheduled-tests.yml` stay red until the marker error is fixed, which this change does not do.
  - Measured on juniper-ml#2578 (head `91591864`): its `Regression Tests (Python 3.15)` check concluded `success`
    while two of its steps failed, and carried a warning annotation naming them.
  - Applied with the script juniper-ml#2578 adds, `util/ad-hoc/2026-11-15_py315_informational_green_legs.py`. It
    edits each workflow as text and re-parses it, and refuses unless the job keeps the same steps in the same order
    plus the report step, every step carries the expression, the ids are unique and no other job changed.

"""

DEPLOY_ENTRY = """\
- **The informational Python 3.15 leg no longer shows as a failed check when it fails** (the
  owner's report of 2026-11-15: the 3.15 checks "are supposed to produce an informational message
  without affecting the ability of code to commit, push, PR, or merge"). #274's job-level
  `continue-on-error` keeps the Quality Gate green, but a failing `Unit Tests (Python 3.15)` check
  still concluded `failure`: a red X and "Some checks were not successful" on the pull request, a
  merge state of `UNSTABLE`, and a failure for `gh pr checks` and any tool that reads every check.
  The 3.15 leg passed on #274 and passes on `main`, so the symptom is latent here.
  - Every step of `ci.yml`'s `tests` job now carries an `id` and
    `continue-on-error: ${{ matrix.experimental == true }}`, so on the 3.15 leg a failing step
    neither stops the job nor turns its check red. A last step,
    `Report the informational Python 3.15 result`, reports each failed step as a `::warning`
    annotation and as a table in the job summary, and emits a `::notice` when every step passed.
  - The three lint steps still run on the 3.12 leg alone. On the 3.15 leg they are `skipped`,
    which the report does not count as a failure.
  - The 3.12, 3.13 and 3.14 legs are unchanged, because the expression is false on them: the 3.12
    leg still posts the required `Unit Tests`, and no check changes its name.
  - Measured on juniper-ml#2578 (head `91591864`): its `Regression Tests (Python 3.15)` check
    concluded `success` while two of its steps failed, and carried a warning annotation naming
    them.
  - Applied with the script juniper-ml#2578 adds,
    `util/ad-hoc/2026-11-15_py315_informational_green_legs.py`. It edits the workflow as text and
    re-parses it, and refuses unless the job keeps the same steps in the same order plus the report
    step, every step carries the expression, the ids are unique and no other job changed.

"""

#: repo -> (the text the entry goes in front of, the entry, the widest line the file's own entries use)
REPOS = {
    "juniper-data-client": (
        "### Fixed\n\n- **`lockfile-update.yml` could commit an empty lockfile.**",
        CLIENT_ENTRY.format(pr="#261"),
        118,
    ),
    "juniper-cascor-client": (
        "### Fixed\n\n- **`lockfile-update.yml` committed the regenerated lockfile UNSIGNED**",
        CLIENT_ENTRY.format(pr="#195"),
        118,
    ),
    "juniper-deploy": (
        "### Fixed\n\n- **`scripts/test_recurrence_snapshots.sh` pulls a missing image instead of building it from a\n",
        DEPLOY_ENTRY,
        100,
    ),
}


def apply(repo: str, worktree: Path, check_only: bool) -> int:
    anchor, entry, width = REPOS[repo]
    path = worktree / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if f"All notable changes to `{repo}` will be documented in this file." not in text:
        print(f"REFUSED: {path} is not {repo}'s CHANGELOG", file=sys.stderr)
        return 1
    wide = [line for line in entry.splitlines() if len(line) > width]
    if wide:
        print(f"REFUSED: {len(wide)} entry line(s) wider than {width}: {wide[0]!r}", file=sys.stderr)
        return 1
    if entry.strip() in text:
        print(f"REFUSED: {path} already carries the entry", file=sys.stderr)
        return 1
    n = text.count(anchor)
    if n != 1:
        print(f"MISMATCH ({n} occurrences, want 1): {anchor.splitlines()[-1][:90]!r}", file=sys.stderr)
        return 1
    at = text.index(anchor)
    unreleased = text.find("## [Unreleased]")
    released = text.find("\n## [", unreleased + 1)
    if unreleased < 0 or not unreleased < at < (released if released >= 0 else len(text)):
        print("REFUSED: the anchor is not inside the [Unreleased] section", file=sys.stderr)
        return 1
    head = "### Fixed\n\n"
    new = text.replace(anchor, head + entry + anchor[len(head):], 1)
    print(f"ok: {repo}: entry goes at the top of [Unreleased] / ### Fixed ({len(entry.splitlines()) - 1} lines)")
    if check_only:
        return 0
    path.write_text(new, encoding="utf-8")
    if path.read_text(encoding="utf-8") != new:  # read back our own write
        print(f"READ-BACK MISMATCH: {path}", file=sys.stderr)
        return 1
    print(f"wrote {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True, choices=sorted(REPOS))
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--check", action="store_true", help="report the match only; write nothing")
    args = ap.parse_args()
    return apply(args.repo, args.worktree, args.check)


if __name__ == "__main__":
    sys.exit(main())
