#!/usr/bin/env python3
"""
List the carrier's files (what the worktree changes against HEAD) with sha256, and optionally save or check a copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3: the manifest's file list and restore points)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4r2/ml-code/r3/manifest.json (its "files"); the move of the worktree from one origin/main to the
         next during the build (``save`` before, ``check`` after: the carrier's files must not have changed).

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_snapshot.py list <out.json>
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_snapshot.py save <snapshot dir>
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_snapshot.py check <snapshot dir>

The carrier is uncommitted, so its files are what ``git status --porcelain --untracked-files=all`` reports:
modified tracked files, and untracked files (the ignored tmp/ is not reported). ``list`` writes
[{"path", "status", "sha256", "mode"}]. ``save`` copies each file under <snapshot dir>/tree/ and writes
<snapshot dir>/files.json. ``check`` compares the worktree with a saved snapshot: exit 0 when the same paths are
changed and every sha256 is equal, 1 otherwise (each difference is printed). Nothing is ever written outside
<out.json> or <snapshot dir>.
"""
import hashlib
import json
import shutil
import subprocess  # nosec B404 -- fixed git argv, run in this worktree
import sys
from pathlib import Path


def carrier_files() -> list:
    out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True).stdout  # nosec B603 B607
    rows = []
    for line in out.splitlines():
        code, rel = line[:2], line[3:]
        status = {"??": "added", " M": "modified", "M ": "modified", "MM": "modified", " D": "deleted", "D ": "deleted", "A ": "added", "AM": "added"}.get(code)
        if status is None:
            raise SystemExit("unexpected git status line: %r" % line)
        path = Path(rel)
        rows.append({"path": rel, "status": status, "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if status != "deleted" else None, "mode": oct(path.stat().st_mode & 0o777) if status != "deleted" else None})
    return sorted(rows, key=lambda row: row["path"])


def main() -> int:
    action, target = sys.argv[1], Path(sys.argv[2])
    rows = carrier_files()
    if action == "list":
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1)
        print("%d files: %d modified, %d added, %d deleted" % (len(rows), sum(r["status"] == "modified" for r in rows), sum(r["status"] == "added" for r in rows), sum(r["status"] == "deleted" for r in rows)))
        return 0
    if action == "save":
        for row in rows:
            if row["status"] != "deleted":
                dest = target / "tree" / row["path"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(row["path"], dest)
        with open(target / "files.json", "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1)
        print("saved %d files under %s" % (len(rows), target))
        return 0
    if action == "check":
        with open(target / "files.json", encoding="utf-8") as fh:
            saved = {row["path"]: row for row in json.load(fh)}
        now = {row["path"]: row for row in rows}
        problems = ["only in the snapshot: %s" % p for p in sorted(set(saved) - set(now))] + ["only in the worktree: %s" % p for p in sorted(set(now) - set(saved))]
        problems += ["differs: %s" % p for p in sorted(set(saved) & set(now)) if saved[p]["sha256"] != now[p]["sha256"] or saved[p]["status"] != now[p]["status"]]
        for line in problems:
            print(line)
        print("%d files in the snapshot, %d in the worktree, %d differences" % (len(saved), len(now), len(problems)))
        return 1 if problems else 0
    print("usage: list <out.json> | save <snapshot dir> | check <snapshot dir>")
    return 2


if __name__ == "__main__":
    sys.exit(main())
