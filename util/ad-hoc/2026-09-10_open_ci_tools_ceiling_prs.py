#!/usr/bin/env python3
"""
Open the 8 consumer PRs that widen the ``juniper-ci-tools`` ceiling to ``<0.10.0``.

Project: juniper-ml
Sub-Project: cross-repo tooling
Author: Paul Calnon
Created: 2026-09-10
Status: ad-hoc -- one fan-out, then retire.
Related: juniper-ml#1869 (the 0.8.0 -> 0.9.0 bump), and
         util/ad-hoc/2026-09-10_widen_ci_tools_ceiling.py, which made the edits this uploads.

Part 1 of the two-part release sequence from the 2026-09-05 SemVer ruling: widen every
consumer CEILING **before** the Release is cut, because the 0.9.0 wheel is otherwise
uninstallable everywhere. Floors move to ``>=0.9.0`` only after the wheel is on PyPI, and
that is a separate pass.

Each PR is inert on merge: a wider ceiling only admits more versions, and CI keeps
resolving 0.8.0 until 0.9.0 publishes. No lockfile refresh is needed either -- the resolved
pin is fixed by ``--constraint requirements.lock``, so a wider ceiling leaves the
sorted-pins diff identical.

Per repo it derives the ``--add`` set from the worktree's own ``git status``, so it uploads
exactly the files the widener touched and nothing else. It runs the staleness pre-flight
first (the ml#1869 clobber: these helpers upload WHOLE files, so a path that moved on
origin/main since the worktree was cut would be silently reverted) and REFUSES that repo
if any path to be uploaded has moved.

Usage
-----
    python3 util/ad-hoc/2026-09-10_open_ci_tools_ceiling_prs.py [--dry-run] [--only REPO]
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess

WORKTREES = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees")
HELPER = pathlib.Path("/home/pcalnon/Development/python/Juniper/juniper-ml/util/open_signed_pr.py")
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
BRANCH = "chore/widen-ci-tools-ceiling"
SUFFIX = "--chore--widen-ci-tools-ceiling--20260910-2021--"

TITLE = "chore(deps): widen the juniper-ci-tools ceiling to <0.10.0"

DATE_NOTE = """
One more line moves: `AGENTS.md`'s `**Last Updated**` is bumped to **2026-09-10**. That is not
cosmetic — `Verify AGENTS.md Last Updated` compares the field to the runner's UTC date and goes red on
any PR that edits `AGENTS.md` without it.
"""

DATE_NOTE_COMMIT = """
AGENTS.md's Last Updated field is bumped to 2026-09-10 as well: the
Verify AGENTS.md Last Updated check compares it to the runner's UTC date and
reddens on any PR that edits AGENTS.md without moving it.
"""

BODY = """## Summary

`juniper-ci-tools` is going **0.8.0 → 0.9.0** (juniper-ml#1869): a MINOR bump, because it adds public
API alongside the fix for the [`juniper-lint-workflow-paths` working-directory false
positive](https://github.com/pcalnon/juniper-ml/issues/1836). This repo pins the dependency
`<0.9.0`, so **the 0.9.0 wheel would not install here at all**.

Widens {lines} pin line(s) across {files} file(s) to `<0.10.0`. The lower bound of each pin is
untouched — `>=0.1.0`, `>=0.6.0` and `>=0.8.0` all occur and all are preserved exactly.
{date_note}

## Why a ceiling widen and not a smaller version number

Per the 2026-09-05 ruling on juniper-cascor-client 0.7.1 → 0.8.0: **version from the change, then fix
whatever the number breaks — never the reverse.** A downstream cap is a fact about the consumer, not
about the semantics of the change; letting it pick the version number makes the version lie to every
consumer. So the bump stays 0.9.0 and the caps move.

That makes this **part 1 of an ordered two-part change**, and part 1 must land *before* the Release is
cut or the artefact is uninstallable:

1. **widen the ceilings** ← this PR
2. cut the Release (owner-only)
3. raise the **floors** to `>=0.9.0` — only *after* the wheel is on PyPI, because a floor pinned at an
   unpublished version resolves nothing. Separate pass.

## This is inert on merge

A wider ceiling only admits more versions. Until 0.9.0 publishes, CI resolves 0.8.0 exactly as it does
today — nothing about the installed toolchain changes when this merges.

It also needs **no lockfile refresh**: the resolved pin is fixed by `--constraint requirements.lock`,
so a wider ceiling leaves the sorted-pins diff identical. (Only a *floor* bump forces a regen — that
is step 3's problem, not this one's.)

## Testing

- Applied by script (juniper-ml `util/ad-hoc/2026-09-10_widen_ci_tools_ceiling.py`), not by hand, so
  all 8 repos get the identical edit. It refuses to report success while any `<0.9.0` survives in the
  files it owns.
- **Verified the diff touches nothing else**: every added/removed line in this PR contains
  `juniper-ci-tools>=` — checked as `git diff -U0 | grep -E '^[-+][^-+]' | grep -cv 'juniper-ci-tools>='`
  → **0**.
- Checked for hidden test pins on the literal string before editing: no test file in any of the 8
  repos asserts `juniper-ci-tools>=…,<0.9.0`. The drift gates that *do* read these pins check "the
  range admits the current version", which `>=X,<0.10.0` satisfies for 0.9.0.
- `notes/`, `reports/`, `prompts/` and `util/fleet_triage/predict_merge.py` also contain the old
  string across the ecosystem and are **deliberately not touched** — historical records of what a pin
  was, not live pins. The script's target set is `.github/workflows/*.yml` plus `AGENTS.md`.
- `CLAUDE.md` is a symlink to `AGENTS.md` in every repo that has one, so only `AGENTS.md` is written —
  writing both would replace the symlink with a regular file.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01VPMWJFR4TWnY1cvgMkR9gZ
"""

COMMIT = """chore(deps): widen the juniper-ci-tools ceiling to <0.10.0

juniper-ci-tools is going 0.8.0 -> 0.9.0 (juniper-ml#1869) -- a MINOR bump,
because it adds public API alongside the juniper-lint-workflow-paths
working-directory fix (juniper-ml#1836). This repo caps the dependency <0.9.0,
so the 0.9.0 wheel would not install here at all.

Widens {lines} pin line(s) across {files} file(s); every lower bound is preserved
exactly. Part 1 of the ordered two-part change from the 2026-09-05 SemVer ruling:
ceilings widen BEFORE the Release is cut, floors move to >=0.9.0 only after the
wheel is on PyPI.
{date_note}

Inert on merge -- a wider ceiling only admits more versions, so CI keeps
resolving 0.8.0 until 0.9.0 publishes, and no lockfile refresh is needed because
--constraint requirements.lock fixes the resolved pin regardless.

Applied by juniper-ml util/ad-hoc/2026-09-10_widen_ci_tools_ceiling.py so all
eight repos get the identical edit. Every changed line in this diff contains
juniper-ci-tools>= -- verified, nothing else moved.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VPMWJFR4TWnY1cvgMkR9gZ
"""


def git(wt: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(wt), *args], capture_output=True, text=True).stdout


def worktrees() -> list[tuple[str, pathlib.Path]]:
    found = []
    for path in sorted(WORKTREES.iterdir()):
        if SUFFIX in path.name:
            found.append((path.name.split("--")[0], path))
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    args = ap.parse_args()

    rc = 0
    for repo, wt in worktrees():
        if args.only and repo != args.only:
            continue
        changed = [line[3:].strip() for line in git(wt, "status", "--porcelain").splitlines() if line.strip()]
        if not changed:
            print(f"{repo}: nothing changed -- skipped")
            continue

        # Staleness pre-flight (the ml#1869 clobber): these helpers upload WHOLE files.
        git(wt, "fetch", "origin", "--quiet")
        moved = set(git(wt, "diff", "--name-only", "HEAD", "origin/main").split())
        collision = sorted(moved.intersection(changed))
        if collision:
            print(f"{repo}: REFUSED -- origin/main moved these paths under the worktree: {collision}")
            print("  take origin/main's copy, re-apply the widen, then re-run.")
            rc = 2
            continue

        # Count only the pin lines. An AGENTS.md in the set also carries a `Last Updated`
        # bump, which is required by the `Verify AGENTS.md Last Updated` check (it compares
        # to the runner's UTC date) but is not a pin and must not be counted as one.
        added = [m for f in changed for m in git(wt, "diff", "-U0", "--", f).splitlines() if m.startswith("+") and not m.startswith("+++")]
        lines = len([m for m in added if "juniper-ci-tools>=" in m])
        dated = [m for m in added if "Last Updated" in m]
        note = DATE_NOTE if dated else ""
        body = BODY.format(lines=lines, files=len(changed), date_note=note)
        message = COMMIT.format(lines=lines, files=len(changed), date_note=(DATE_NOTE_COMMIT if dated else ""))

        adds = []
        for f in changed:
            adds += ["--add", f"{wt / f}:{f}"]

        print(f"\n=== {repo}: {lines} pin lines / {len(changed)} files ===")
        for f in changed:
            print(f"    {f}")
        if args.dry_run:
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
