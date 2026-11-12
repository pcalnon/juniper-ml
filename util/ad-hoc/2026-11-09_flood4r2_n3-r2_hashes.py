"""
Record the sha256 of every file the juniper-cascor N-3 carrier (fix/ws-resume-losses) changes, against a given base.

Lists the carrier worktree's changed and untracked files (its own tmp/ excluded) with git, hashes each one, and writes
the list as JSON. Used before and after the round-2 fix-up, and to verify a byte-for-byte restore after a mutant run.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
CARRIER = JUNIPER / "worktrees" / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"


def changed_files(worktree: Path, base: str) -> list:
    """Tracked files that differ from ``base`` plus untracked files, repo-relative, tmp/ excluded."""
    tracked = subprocess.run(["git", "-C", str(worktree), "diff", "--name-status", base], check=True, capture_output=True, text=True).stdout
    untracked = subprocess.run(["git", "-C", str(worktree), "ls-files", "--others", "--exclude-standard"], check=True, capture_output=True, text=True).stdout
    rows = []
    for line in tracked.splitlines():
        status, _, path = line.partition("\t")
        rows.append({"path": path, "status": {"M": "modified", "A": "added", "D": "deleted"}.get(status[:1], status)})
    for path in untracked.splitlines():
        if path and not path.startswith("tmp/"):
            rows.append({"path": path, "status": "added"})
    return sorted(rows, key=lambda r: r["path"])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", default=str(CARRIER))
    ap.add_argument("--base", required=True, help="commit the carrier is diffed against")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    worktree = Path(args.worktree)
    head = subprocess.run(["git", "-C", str(worktree), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    base = subprocess.run(["git", "-C", str(worktree), "rev-parse", args.base], check=True, capture_output=True, text=True).stdout.strip()
    files = changed_files(worktree, base)
    for row in files:
        row["sha256"] = sha256(worktree / row["path"])
    payload = {"worktree": str(worktree), "head": head, "base": base, "files": files}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    print(f"{len(files)} files against {base[:8]} (HEAD {head[:8]}) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
