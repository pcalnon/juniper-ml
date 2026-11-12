"""
Snapshot fix N-1's carrier files (copy + sha256), and compare a snapshot with a manifest's recorded hashes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (builder session, flood-4 round 2, fix N-1 round 3)
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11 (juniper-cascor's paused-fit wedge)

Usage:
    python3 <this> snapshot <dest-dir> [--expect <round-2 manifest.json>]
    python3 <this> hashes

``snapshot`` copies every carrier file (the paths ``git status --porcelain`` reports in the N-1
worktree, tmp/ excluded) to <dest-dir>, keeping their repo-relative paths, writes
<dest-dir>/SHA256SUMS, and, with --expect, compares each file's sha256 with the one the given
manifest's ``files_changed`` records. ``hashes`` prints the current sha256 of every carrier file.
Exit 1 on any mismatch or missing file. Never edits the worktree.
"""

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 -- fixed-argv git status
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
TREE = JUNIPER / "worktrees" / "juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c"


def carrier_paths() -> list:
    """Repo-relative paths git reports as changed or untracked, tmp/ excluded."""
    out = subprocess.run(["git", "-C", str(TREE), "status", "--porcelain", "--untracked-files=all"], check=True, capture_output=True, text=True).stdout  # nosec B603 B607
    paths = []
    for line in out.splitlines():
        rel = line[3:]
        if rel.startswith("tmp/"):
            continue
        paths.append(rel)
    return sorted(paths)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("dest")
    snap.add_argument("--expect")
    sub.add_parser("hashes")
    args = parser.parse_args()

    paths = carrier_paths()
    if args.cmd == "hashes":
        for rel in paths:
            print(f"{sha256(TREE / rel)}  {rel}")
        print(f"{len(paths)} carrier files")
        return 0

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    lines = []
    for rel in paths:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TREE / rel, target)
        lines.append(f"{sha256(target)}  {rel}")
    with open(dest / "SHA256SUMS", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"copied {len(paths)} carrier files to {dest}")

    bad = 0
    if args.expect:
        with open(args.expect, encoding="utf-8") as fh:
            recorded = {entry["path"]: entry["sha256"] for entry in json.load(fh)["files_changed"]}
        for rel in sorted(set(recorded) | set(paths)):
            if rel not in paths:
                print(f"MISSING  {rel} (recorded, not in the tree)")
                bad += 1
            elif rel not in recorded:
                print(f"EXTRA    {rel} (in the tree, not recorded)")
                bad += 1
            else:
                now = sha256(TREE / rel)
                verdict = "same" if now == recorded[rel] else "DIFFERS"
                bad += verdict != "same"
                print(f"{verdict:8s} {rel}")
        print(f"{bad} mismatch(es) against {args.expect}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
