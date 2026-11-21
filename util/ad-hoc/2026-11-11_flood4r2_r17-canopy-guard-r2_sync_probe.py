"""
Copy a carrier worktree's uncommitted change set into probe worktrees at the same commit, and verify it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round 2 of the Overtoad's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt)

Usage:
    python3 <this file> --carrier <carrier worktree> --probe <probe worktree> [--probe ...] --record <json>

Tests run in the probes, never in the carrier tree, so a run cannot leave a stray or modified file in the tree
that will be committed. The change set is the carrier's unstaged modifications plus its untracked files (anything
else is refused). Each probe must sit at the carrier's HEAD. After the copy, every file's sha256 must equal the
carrier's and the probe's own change set must name the same files; the record holds every hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(tree: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(tree), *args], check=True, capture_output=True, text=True).stdout  # nosec B603 B607 - fixed argv


def change_set(tree: Path) -> list[str]:
    paths = []
    for entry in [item for item in git(tree, "status", "--porcelain=v1", "--untracked-files=all", "-z").split("\0") if item]:
        if entry[:2] not in (" M", "??"):
            raise SystemExit(f"[sync] refusing status {entry[:2]!r} for {entry[3:]} in {tree}")
        paths.append(entry[3:])
    return sorted(paths)


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy a carrier's uncommitted change set into probe worktrees and verify it.")
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path, action="append")
    parser.add_argument("--record", required=True, type=Path)
    args = parser.parse_args()
    carrier = args.carrier.resolve()
    head = git(carrier, "rev-parse", "HEAD").strip()
    paths = change_set(carrier)
    record = {"carrier": str(carrier), "head": head, "files": {path: sha256(carrier / path) for path in paths}, "probes": {}}
    ok = True
    for probe in [entry.resolve() for entry in args.probe]:
        probe_head = git(probe, "rev-parse", "HEAD").strip()
        if probe_head != head:
            raise SystemExit(f"[sync] {probe} is at {probe_head}, the carrier at {head}")
        for path in paths:
            (probe / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(carrier / path, probe / path)
        same_hashes = all(sha256(probe / path) == record["files"][path] for path in paths)
        same_set = change_set(probe) == paths
        record["probes"][str(probe)] = {"head": probe_head, "sha256_equal": same_hashes, "change_set_equal": same_set}
        ok = ok and same_hashes and same_set
        print(f"[sync] {probe.name}: {len(paths)} files, sha256 equal={same_hashes}, change set equal={same_set}")
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
