#!/usr/bin/env python3
"""
Open the 8 sibling PRs that raise the ``juniper-ci-tools`` floor to ``>=0.9.0``.

Project: juniper-ml
Sub-Project: cross-repo tooling
Author: Paul Calnon
Created: 2026-09-11
Status: ad-hoc -- one fan-out, then retire.
Related: util/ad-hoc/2026-09-11_raise_ci_tools_floor.py (makes the edits this uploads),
         util/ad-hoc/2026-09-10_open_ci_tools_ceiling_prs.py (part 1's opener).

juniper-ml's own floor bump is NOT opened here -- this session edits juniper-ml from its own
worktree and lands it with open_signed_pr.py directly.

Same safety contract as part 1's opener: derives each ``--add`` set from the worktree's own
``git status``, runs the ml#1869 staleness pre-flight per repo (these helpers upload WHOLE
files) and REFUSES a repo whose paths moved on origin/main rather than clobbering.

Usage
-----
    python3 util/ad-hoc/2026-09-11_open_ci_tools_floor_prs.py [--dry-run] [--only REPO]
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess

WORKTREES = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees")
HELPER = pathlib.Path("/home/pcalnon/Development/python/Juniper/juniper-ml/util/open_signed_pr.py")
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
BRANCH = "chore/raise-ci-tools-floor"
MARKER = "widen-ci-tools-ceiling--20260910-2021"

TITLE = "chore(deps): raise the juniper-ci-tools floor to >=0.9.0"

BODY = """## Summary

`juniper-ci-tools` **0.9.0 is on PyPI** (published 2026-09-11 from juniper-ml's
`juniper-ci-tools-v0.9.0` Release). This raises {lines} pin line(s) across {files} file(s) from
`>=X` to `>=0.9.0`, keeping the `<0.10.0` ceiling this repo already carries.

Part 3 — the last step — of the ordered sequence from the 2026-09-05 SemVer ruling:

1. ✅ widen the ceilings to `<0.10.0` (2026-09-10)
2. ✅ cut the Release, owner-approved the `pypi` environment gate (2026-09-11)
3. ✅ raise the floors ← this PR

The order is strict in that direction: a floor pinned at a version PyPI does not serve makes every
`pip install` in the range unsatisfiable, so this step could not run before the wheel existed. The
script that made the edit enforces it — it queries PyPI and refuses outright if 0.9.0 is absent.

## What this changes, honestly: the requirement, not the resolution

Every pin is a range and pip resolves the newest match, so **this repo already installs 0.9.0** —
that happened the moment the wheel published, because the ceiling was already `<0.10.0`. Raising the
floor records the *requirement*: that this repo is entitled to assume the working-directory-aware
`juniper-lint-workflow-paths`, so a later edit cannot silently reintroduce a version whose lint
reports a false positive on a monorepo lane.

## Verified against the published wheel, not the checkout

`juniper-ci-tools==0.9.0` was installed into a clean venv from PyPI and checked there:

- carries `extract_script_references`, `ScriptReference`, and `LintFinding.working_directory`;
- run against the real juniper-recurrence tree — the one the 0.8.0 lint false-positived on — it
  reports **ok, 16 workflows, 0 missing**;
- the `juniper-lint-workflow-paths` console script runs clean against juniper-cascor (18 workflows).

(PyPI's aggregate JSON endpoint still served 0.8.0 for a while after the publish job went green —
the known Fastly edge-cache lag. The version-specific endpoint `/pypi/juniper-ci-tools/0.9.0/json`
is the honest probe and showed both the wheel and the sdist.)

## Testing

- Applied by script (juniper-ml `util/ad-hoc/2026-09-11_raise_ci_tools_floor.py`), so all repos get
  the identical edit. It refuses a repo still capped `<0.9.0` — i.e. one where part 1 never landed.
- **Verified the diff touches nothing else**: every added/removed line is either a
  `juniper-ci-tools>=` pin or, where `AGENTS.md` moved, its `Last Updated` field — checked as
  `git diff -U0 | grep -E '^[-+][^-+]' | grep -v 'juniper-ci-tools>=' | grep -vc 'Last Updated'` → **0**.
- The staleness pre-flight reported no collisions.
{date_note}
🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01VPMWJFR4TWnY1cvgMkR9gZ
"""

DATE_NOTE = """- `AGENTS.md`'s `**Last Updated**` moves to **2026-09-11**, because
  `Verify AGENTS.md Last Updated` compares the field to the runner's UTC date and reddens on any PR
  that edits `AGENTS.md` without it.
"""

COMMIT = """chore(deps): raise the juniper-ci-tools floor to >=0.9.0

juniper-ci-tools 0.9.0 is on PyPI (published 2026-09-11 from juniper-ml's
juniper-ci-tools-v0.9.0 Release). Raises {lines} pin line(s) across {files}
file(s) from >=X to >=0.9.0, keeping the <0.10.0 ceiling already in place.

Part 3 of the ordered sequence from the 2026-09-05 SemVer ruling: ceilings
widened 2026-09-10, Release cut and the pypi gate owner-approved 2026-09-11,
floors last. A floor at an unpublished version makes every pin unsatisfiable,
so the script that made this edit queries PyPI and refuses if 0.9.0 is absent.

This records the requirement, not the resolution: every pin is a range and pip
takes the newest match, so this repo already installs 0.9.0 by virtue of the
widened ceiling. The floor stops a later edit silently reintroducing a version
whose lint false-positives on a monorepo lane.

Verified from the PUBLISHED wheel in a clean venv, not from a checkout: it
carries extract_script_references / ScriptReference /
LintFinding.working_directory, and reports ok on the juniper-recurrence tree
that 0.8.0 false-positived on.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VPMWJFR4TWnY1cvgMkR9gZ
"""


def git(wt: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(wt), *args], capture_output=True, text=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    args = ap.parse_args()

    rc = 0
    for wt in sorted(p for p in WORKTREES.iterdir() if MARKER in p.name):
        repo = wt.name.split("--")[0]
        if args.only and repo != args.only:
            continue
        changed = [line[3:].strip() for line in git(wt, "status", "--porcelain").splitlines() if line.strip()]
        if not changed:
            print(f"{repo}: nothing changed -- skipped")
            continue

        git(wt, "fetch", "origin", "--quiet")
        moved = set(git(wt, "diff", "--name-only", "HEAD", "origin/main").split())
        collision = sorted(moved.intersection(changed))
        if collision:
            print(f"{repo}: REFUSED -- origin/main moved these paths under the worktree: {collision}")
            rc = 2
            continue

        added = [m for f in changed for m in git(wt, "diff", "-U0", "--", f).splitlines() if m.startswith("+") and not m.startswith("+++")]
        lines = len([m for m in added if "juniper-ci-tools>=" in m])
        note = DATE_NOTE if any("Last Updated" in m for m in added) else ""
        body = BODY.format(lines=lines, files=len(changed), date_note=note)
        message = COMMIT.format(lines=lines, files=len(changed))

        adds = []
        for f in changed:
            adds += ["--add", f"{wt / f}:{f}"]

        print(f"\n=== {repo}: {lines} pin lines / {len(changed)} files ===")
        if args.dry_run:
            for f in changed:
                print(f"    {f}")
            continue

        body_file = wt / ".pr-body.md"
        body_file.write_text(body, encoding="utf-8")
        try:
            proc = subprocess.run(
                [PYTHON, str(HELPER), "--repo", repo, "--branch", BRANCH, *adds,
                 "--message", message, "--title", TITLE, "--body-file", str(body_file)],
                capture_output=True, text=True,
            )
            print(proc.stdout.strip() or proc.stderr.strip())
            if proc.returncode:
                rc = proc.returncode
        finally:
            body_file.unlink(missing_ok=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
