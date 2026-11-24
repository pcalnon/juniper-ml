#!/usr/bin/env python3
"""
Close the seven round-2 Cursor drafts the flood-4 triage left uncarried (superseded or duplicates), each with a comment
naming what on main covers it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — one-off (Cursor flood-4 session 9)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Why: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (Open items) lists #2471, #2476,
#2477, #2486, #2488, #2500 and #2501 as "to be closed as superseded or duplicates". Each comment below was re-derived
on main edea2eb1 (2026-11-15) by tmp/flood4/session9/none_group_evidence.py; the line numbers are main's at that sha.
Usage:
    2026-11-15_flood4r2_s9_close_none_group.py [--execute]
Without --execute it prints what it would do. With it: refuses a PR whose head moved off the recorded sha or that is
no longer an open draft, posts the comment, closes the PR, and reads its state back.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "pcalnon/juniper-ml"
MAIN = "edea2eb1"
RECORD = "`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` §8 (Open items)"
LEAD = f"Closing as part of the flood-4 round-2 disposition: {RECORD} lists this draft among the seven the triage left uncarried, to be closed as superseded or duplicates. Re-checked on `main` `{MAIN}` (2026-11-15):"

DRAFTS = {
    2471: ("d1f5f989", "Superseded. `main` already has this launcher contract. In `scripts/wake_the_claude.bash`, `-v` is one of the Claude Code version flags (`MODEL_VERSION_FLAGS`, line 356), and `--script-version` prints the script's own version (line 360). `scripts/claude_interactive.bash` turns on `--remote-control` by default (lines 73 and 119-120). `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (lines 184-189) documents those defaults, `--no-remote-control` and `--file <prompt file>`. The triage found #2479 supersedes this draft, and juniper-ml#2584 carried #2479."),
    2476: ("0fcb0a58", "Superseded. `main` builds and documents the alternates scratch: `util/fleet_triage/predict_merge.py` (lines 15 and 334-364: `git init` plus an `objects/info/alternates` entry), `docs/REFERENCE.md` (lines 2683, 2750-2760 and 4215) and `.claude/agents/fleet-supervisor.md` (lines 29-30). The related docs draft #2494 was carried by juniper-ml#2584."),
    2477: ("f1531e0a", "Superseded, and its subject is past: `juniper-ml` 0.11.4 (PyPI 2026-11-07) and 0.11.5 floor the `[recurrence]` extra at `juniper-recurrence>=0.8.1,<0.9.0` (`pyproject.toml` line 110), and `docs/REFERENCE.md` line 6055 says so, citing juniper-ml#2473. #2488 covered the same ground."),
    2486: ("dda53650", "A duplicate. juniper-ml#2517 carried #2413's test, which pins the same two cases: `tests/test_stats_summary_render.py` lines 209-218 hold that an explicit train theta of `0` outranks `service.default_theta`, and that an unset theta with a `default_theta` of `0.0` is labelled the service default."),
    2488: ("d94906b4", "Superseded: this is a 0.11.4 release-cut draft. `juniper-ml` 0.11.4 was released on 2026-11-07 and 0.11.5 is on PyPI since 2026-11-14; `main` is at version 0.11.5 (`pyproject.toml` line 7) with the `[recurrence]` floor `>=0.8.1,<0.9.0` (line 110), and `docs/REFERENCE.md` line 6055 records when that floor was first released."),
    2500: ("9a42c723", "Superseded. `docs/REFERENCE.md` line 6822 documents the `test_accuracy` column as cascor's `accuracy`, new in juniper-cascor#731 and first released in juniper-cascor 0.13.0 (PyPI 2026-10-28); lines 3956-3992 and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` line 753 describe the final-evaluation columns."),
    2501: ("f5b74f48", "Superseded. juniper-ml#2510 (`4be0b0fb`, 2026-11-07) replaced `docs/QUICK_START.md`'s verify sample with what `juniper-ml` 0.11.4 resolves, and juniper-ml#2568 refreshed it for 0.11.5. On `main` it prints `juniper-cascor 0.13.x` (line 92), which meets the `[servers]` extra's `>=0.12.0` floor."),
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
