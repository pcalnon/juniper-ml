#!/usr/bin/env python3
"""
Build and prove the claims lens's exact text fixes for the cascor pause fix carrier, on scratch copies.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (a claims-lens validation of one carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the cascor pause check-then-act fix carrier's claims lens (session 9)

Each fix is an exact old -> new pair in one file. Long old strings are read verbatim from the file
by line number (and checked against an expected prefix) so no hand-typed copy can drift. The script
copies every target file into --scratch, checks that each old string occurs exactly once in its file,
applies all the fixes in order to the copies, checks that each non-empty new string then occurs
exactly once and each old string no longer does, writes --out (text_fixes.json) and prints one line
per fix. It never writes to the carrier or to the helper directory it reads from.
Exit 0 when every fix proved out; 1 otherwise.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List


def line_of(path: Path, number: int, prefix: str) -> str:
    """Return line ``number`` (1-based) of ``path`` verbatim, after checking its prefix."""
    line = path.read_text(encoding="utf-8").split("\n")[number - 1]
    if not line.startswith(prefix):
        raise SystemExit(f"{path.name}:{number} does not start with {prefix!r}: {line[:80]!r}")
    return line


def build(carrier: Path, helpers: Path) -> List[Dict[str, str]]:
    texts = carrier / "tmp/flood4-fix/r32-pause-fix"
    pr_body = texts / "pr_body.txt"
    commit_body = texts / "commit_body.txt"
    changelog_entry = texts / "changelog_entry.txt"
    changelog = carrier / "CHANGELOG.md"
    manager = carrier / "src/api/lifecycle/manager.py"
    reference = carrier / "docs/api/JUNIPER_CASCOR_API_REFERENCE.md"
    fix_docs = helpers / "2026-11-15_flood4r2_r32-cascor_fix_docs.py"

    residual_old = line_of(pr_body, 68, "- **`training_state.status` can read `Paused` beside `STOPPED` for up to one pause-loop wake")
    design_old = line_of(pr_body, 53, "`tmp/flood4-fix/r32-pause-fix/DESIGN.md` beside this carrier") + "\n\n"

    ws_old = "on `/ws/control` an `error` ack)"
    ws_new = 'on `/ws/control` an `error` ack, "Command execution failed")'
    step_old = "its close of the gate are one step, and when a `stop`, a `reset` or the run's own settle moves the FSM"
    step_new = "its close of the gate are one step under a lock that a `start`, a `resume` and a live swap also take, and when a `stop`, a `reset` or the run's own settle, which do not take it, moves the FSM"

    return [
        {
            "id": "T1",
            "finding": "F1",
            "file": str(commit_body),
            "old": '  they submit their run. A pause whose transition is refused reopens the gate and is refused\n  ("Training is not active", the route\'s 409), as one sent a moment later is.',
            "new": '  they submit their run. A pause whose transition is refused reopens the gate and is refused\n  (409 "Training cannot be paused in the current state"; on /ws/control an error ack), as one\n  sent a moment later is.',
        },
        {"id": "T2", "finding": "F2", "file": str(pr_body), "old": "| fail (30 findings in 500 trials) |", "new": "| fail (15 findings in 500 trials in the logged run) |"},
        {
            "id": "T3",
            "finding": "F3",
            "file": str(manager),
            "old": "enough: neither this settle nor ``pause_training`` takes a lock, so a second pause could",
            "new": "enough: this settle does not take ``_pause_lock``, which ``pause_training`` holds, so a second pause could",
        },
        {
            "id": "T4",
            "finding": "F4",
            "file": str(pr_body),
            "old": residual_old,
            "new": "- **`training_state.status` can read `Paused` beside `STOPPED` until the stopped fit settles** when a `stop` or `reset` lands between an accepted `pause`'s transition and its `Paused` write (neither takes `_pause_lock`). The fit settles at its next interrupt checkpoint, or within one 0.5 s pause-loop wake if it already waits at one, and its settle writes `Stopped`.",
        },
        {"id": "T5", "finding": "F5", "file": str(pr_body), "old": design_old, "new": ""},
        {"id": "T6a", "finding": "F6", "file": str(reference), "old": step_old, "new": step_new},
        {"id": "T6b", "finding": "F6 (and F9: keep the rebuild helper in step)", "file": str(fix_docs), "old": step_old, "new": step_new},
        {"id": "T7a", "finding": "F7", "file": str(changelog), "old": ws_old, "new": ws_new},
        {"id": "T7b", "finding": "F7", "file": str(changelog_entry), "old": ws_old, "new": ws_new},
        {"id": "T7c", "finding": "F7", "file": str(pr_body), "old": ws_old, "new": ws_new},
        {"id": "T7d", "finding": "F7 (and F9: keep the rebuild helper in step)", "file": str(fix_docs), "old": ws_old, "new": ws_new},
        {
            "id": "T8a",
            "finding": "F8",
            "file": str(manager),
            "old": "held for one FSM transition, one Event operation and one ``training_state`` write, never",
            "new": "held for one FSM check and transition, at most two Event operations and one ``training_state`` write, never",
        },
        {
            "id": "T8b",
            "finding": "F8",
            "file": str(pr_body),
            "old": "The lock is held for one FSM transition, one `Event` operation and one `training_state` write, never across I/O.",
            "new": "The lock is held for one FSM check and transition, at most two `Event` operations and one `training_state` write, never across I/O.",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--helpers", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    fixes = build(args.carrier, args.helpers)
    copies: Dict[str, Path] = {}
    args.scratch.mkdir(parents=True, exist_ok=True)
    for index, fix in enumerate(fixes):
        source = Path(fix["file"])
        if fix["file"] not in copies:
            target = args.scratch / f"{index:02d}_{source.name}"
            shutil.copyfile(source, target)
            copies[fix["file"]] = target

    ok = True
    for fix in fixes:
        text = copies[fix["file"]].read_text(encoding="utf-8")
        before = text.count(fix["old"])
        fix["old_count_before"] = before
        if before != 1:
            ok = False
            print(f"FAIL {fix['id']}: old occurs {before} times in {Path(fix['file']).name}")
            continue
        text = text.replace(fix["old"], fix["new"], 1)
        copies[fix["file"]].write_text(text, encoding="utf-8")

    for fix in fixes:
        text = copies[fix["file"]].read_text(encoding="utf-8")
        fix["old_count_after"] = text.count(fix["old"])
        fix["new_count_after"] = text.count(fix["new"]) if fix["new"] else None
        good = fix["old_count_before"] == 1 and fix["old_count_after"] == 0 and (fix["new"] == "" or fix["new_count_after"] == 1)
        ok = ok and good
        print(f"{'ok  ' if good else 'FAIL'} {fix['id']:<4} {Path(fix['file']).name}: old {fix['old_count_before']} -> {fix['old_count_after']}, new after {fix['new_count_after']}")

    report = {"proved_on": "scratch copies in " + str(args.scratch), "all_ok": ok, "fixes": fixes}
    args.out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
