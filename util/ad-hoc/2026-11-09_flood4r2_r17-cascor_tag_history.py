#!/usr/bin/env python3
"""
Report, per juniper-cascor release tag, whether a start clears the stop signal a checkpoint reads.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: owner ruling 17, "cascor: stop-then-start")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#753's "How far back" method (per-tag reading of the tag's own manager.py)

For every ``v*`` tag (and the given extra refs) it reads that ref's
``src/api/lifecycle/manager.py`` and reports:
  - checkpoint: an interrupt checkpoint exists (``def _check_for_interrupt``), i.e. a stop can
    interrupt a running fit at all;
  - start_clears: ``start_training``'s body calls ``self._stop_event.clear()``;
  - swap_clears: ``swap_dataset_live``'s body calls ``self._stop_event.clear()``.
A ref has the stop-then-start race exactly when checkpoint and start_clears are both true.

Usage:
  2026-11-09_flood4r2_r17-cascor_tag_history.py --repo <juniper-cascor checkout> [--ref <extra ref> ...]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 -- fixed-argv git reads
import sys
from pathlib import Path

MANAGER = "src/api/lifecycle/manager.py"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)  # nosec B603 B607 -- fixed argv


def _method_body(source: str, name: str) -> str:
    """The text of ``def <name>(`` up to the next method at the same indent, or "" when absent."""
    match = re.search(rf"^    def {re.escape(name)}\(", source, re.MULTILINE)
    if match is None:
        return ""
    rest = source[match.end():]
    following = re.search(r"^    def \w+\(", rest, re.MULTILINE)
    return rest[: following.start()] if following else rest


def _version_key(tag: str) -> tuple:
    return tuple(int(part) if part.isdigit() else 0 for part in tag.lstrip("v").split("."))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--ref", action="append", default=[], help="an extra ref to report (repeatable)")
    args = parser.parse_args()
    tags = sorted((line for line in _git(args.repo, "tag", "-l", "v*").stdout.split() if re.fullmatch(r"v\d+\.\d+\.\d+", line)), key=_version_key)
    rows = []
    for ref in [*tags, *args.ref]:
        shown = _git(args.repo, "show", f"{ref}:{MANAGER}")
        if shown.returncode != 0:
            rows.append({"ref": ref, "manager": False})
            continue
        source = shown.stdout
        # The signal the checkpoint reads: ``_stop_requested`` in v0.5.0, ``_stop_event`` later.
        read = re.search(r"if self\.(_stop_\w+)\.is_set\(\):", _method_body(source, "_check_for_interrupt"))
        name = read.group(1) if read else None
        row = {
            "ref": ref,
            "manager": True,
            "checkpoint": name is not None,
            "signal": name,
            "start_clears": name is not None and f"self.{name}.clear()" in _method_body(source, "start_training"),
            "swap_clears": name is not None and f"self.{name}.clear()" in _method_body(source, "swap_dataset_live"),
        }
        row["race"] = row["checkpoint"] and row["start_clears"]
        rows.append(row)
    for row in rows:
        print(json.dumps(row))
    racing = [row["ref"] for row in rows if row.get("race")]
    print(f"RACE in {len(racing)} ref(s): {racing[0] if racing else '-'} .. {racing[-1] if racing else '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
