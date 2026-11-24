#!/usr/bin/env python3
"""
Close round 3's two Cursor drafts, juniper-ml #2404 and #2406, as superseded, each with a comment naming what on main
supersedes it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — one-off (Cursor flood-4 session 9)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Why: the Overtoad's ruling of 2026-11-16 ("Close both, superseded"). notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
§8 (Open items) lists them as "Round 3: juniper-ml#2404 and #2406, each considered individually". The line numbers below
were re-derived on main 0961e1ab (2026-11-16).
Usage:
    2026-11-16_flood4r2_s9_close_round3.py [--execute]
Without --execute it prints what it would do. With it: refuses a PR whose head moved off the recorded sha or that is no
longer an open draft, posts the comment, closes the PR, and reads its state back.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "pcalnon/juniper-ml"
MAIN = "0961e1ab"
LEAD = f"Closing as superseded, on the Overtoad's ruling of 2026-11-16 for round 3 of the flood-4 disposition (`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` §8 lists this draft for individual consideration). Re-checked on `main` `{MAIN}` (2026-11-16):"

DRAFTS = {
    2404: ("d18f1ac5", "The launcher contract this draft documents changed after it was opened. Worktree and remote control are on by default since the Overtoad's ruling of 2026-11-04 (`scripts/claude_interactive.bash` lines 73-74 and 119-120), so the draft's \"worktree is opt-in\" no longer holds. `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` documents the current contract: `./claudey` and its defaults (lines 139 and 184-188), and the version flags (lines 197-198)."),
    2406: ("33a1fac7", "The `-v` contract this draft documents changed after it was opened. In `scripts/wake_the_claude.bash`, `-v`, `-V`, `--version` and `--claude-version` print Claude Code's version (`MODEL_VERSION_FLAGS`, line 356), and `--script-version` prints the launcher's own (line 360); `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` lines 197-198 say so, and that `--remote-control` never takes a value. The two launch errors the draft records print to stderr whatever the debug setting (`wake_the_claude.bash` lines 1396, 1831 and 1888)."),
}


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    bad = 0
    for num, (head, text) in DRAFTS.items():
        info = json.loads(gh("pr", "view", str(num), "--repo", REPO, "--json", "state,isDraft,headRefOid,title"))
        body = f"{LEAD}\n\n{text}\n"
        ok = info["state"] == "OPEN" and info["isDraft"] and info["headRefOid"].startswith(head)
        print(f"#{num} state={info['state']} draft={info['isDraft']} head={info['headRefOid'][:8]} (recorded {head}) -> {'OK' if ok else 'REFUSED'} | {info['title'][:80]}")
        print(f"    comment ({len(body)} chars): {text[:150]}...")
        if not ok:
            bad += 1
            continue
        if not args.execute:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8", dir=Path(__file__).resolve().parents[2] / "tmp") as handle:
            handle.write(body)
            body_file = handle.name
        gh("pr", "comment", str(num), "--repo", REPO, "--body-file", body_file)
        gh("pr", "close", str(num), "--repo", REPO)
        Path(body_file).unlink()
        after = json.loads(gh("pr", "view", str(num), "--repo", REPO, "--json", "state"))
        print(f"    closed: state now {after['state']}")
        bad += 0 if after["state"] == "CLOSED" else 1
    print(f"{'EXECUTED' if args.execute else 'DRY RUN'}: {len(DRAFTS) - bad} of {len(DRAFTS)} ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
