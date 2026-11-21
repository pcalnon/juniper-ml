#!/usr/bin/env python3
"""
Save each juniper-cascor release tag's lifecycle manager and state machine, and report what the texts claim per tag.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2 validation: Overtoad ruling 17, "cascor: stop-then-start", claims lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_VALIDATE_R2.txt; the carrier's CHANGELOG entry ("How far back") and API_SCHEMAS.md text

For every ``v*`` tag of the repository given by ``--repo`` (read-only: ``git tag`` and ``git show`` only) the
script writes ``<out>/<tag>/manager.py`` and ``state_machine.py`` and prints one JSON line with the facts the
carrier's texts attribute to "0.5.0 to 0.13.0": an interrupt checkpoint, a start that clears the stop signal,
a live swap that clears it, and the three consequences (``mark_completed`` exists, the completion writes
``Completed`` without reading its answer, and a terminal session counter exists).

Usage:
  2026-11-12_flood4r2_val_r17-cascor-claims_tag_files.py --repo <juniper-cascor checkout> --out <dir>
Exit: 0.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 -- fixed-argv read-only git calls
import sys
from pathlib import Path

FILES = ("src/api/lifecycle/manager.py", "src/api/lifecycle/state_machine.py")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)  # nosec B603 B607 -- fixed argv


def _body(source: str, name: str) -> str:
    """Return the text of ``def <name>`` up to the next def at the same indentation, or ''."""
    match = re.search(rf"^(\s*)def {re.escape(name)}\(", source, flags=re.MULTILINE)
    if not match:
        return ""
    indent = match.group(1)
    rest = source[match.end() :]
    nxt = re.search(rf"^{indent}def \w+\(", rest, flags=re.MULTILINE)
    return source[match.start() : match.end() + (nxt.start() if nxt else len(rest))]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    tags = [t for t in _git(args.repo, "tag", "--list", "v*", "--sort=version:refname").stdout.split() if t]
    for tag in tags:
        row: dict[str, object] = {"tag": tag}
        sources: dict[str, str] = {}
        for path in FILES:
            shown = _git(args.repo, "show", f"{tag}:{path}")
            if shown.returncode == 0:
                target = args.out / tag / Path(path).name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(shown.stdout, encoding="utf-8")
                sources[Path(path).name] = shown.stdout
        manager = sources.get("manager.py", "")
        machine = sources.get("state_machine.py", "")
        start = _body(manager, "start_training")
        swap = _body(manager, "swap_dataset_live")
        clear = re.compile(r"self\._stop_(event|requested)\.clear\(\)")
        row["has_swap_dataset_live"] = bool(swap)
        row["start_clears"] = bool(clear.search(start))
        row["swap_clears"] = bool(clear.search(swap))
        row["checkpoint_def"] = bool(re.search(r"def _check_for_interrupt\(", manager))
        row["mark_completed_in_fsm"] = "def mark_completed" in machine
        row["mark_completed_calls_in_manager"] = len(re.findall(r"mark_completed\(\)", manager))
        row["completed_write_lines"] = [i + 1 for i, line in enumerate(manager.splitlines()) if re.search(r"status=\"Completed\"", line)]
        row["session_counter"] = "inc_training_session_completed" in manager
        row["stop_is_set_reads"] = len(re.findall(r"_stop_(event|requested)\.is_set\(\)", manager))
        print(json.dumps(row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
