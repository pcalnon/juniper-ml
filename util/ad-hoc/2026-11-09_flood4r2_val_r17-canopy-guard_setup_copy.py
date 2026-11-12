"""
Copy the r17 canopy network-guard carrier's 13 files into the validator's own worktrees, sha256-checked.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 round-2 validation of the owner's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/BRIEF_VALIDATE_R2.txt)

Usage:
    python3 util/ad-hoc/2026-11-09_flood4r2_val_r17-canopy-guard_setup_copy.py

Reads the carrier's manifest.json, verifies every listed file's sha256 in the carrier tree, then copies the files
into two validator worktrees: the base worktree (same base sha as the carrier, a straight copy) and the on-main
worktree (current origin/main). For the on-main worktree, CHANGELOG.md is rebuilt with
`git merge-file -p <carrier> <base> <main>` (main moved CHANGELOG.md after the carrier's base), and every other
carrier file that main changed since the base is reported. The carrier worktree is only read.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path

WORKTREES = Path.home() / "Development" / "python" / "Juniper" / "worktrees"
CARRIER = WORKTREES / "juniper-canopy--test--unit-lane-network-guard--20261109-0827--b4b01904"
VAL_BASE = WORKTREES / "juniper-canopy--val--r17-network-guard--20261109-0942--b4b01904"
VAL_MAIN = WORKTREES / "juniper-canopy--val--r17-network-guard-onmain--20261109-0942--609a26a3"
BASE_SHA = "b4b01904ca7778cafd0297a90fc0a506b511e308"
MAIN_SHA = "609a26a35d0aeadd2f92e4414e59b21eb568b955"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_show(repo: Path, rev: str, rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{rel}"], check=True, capture_output=True).stdout  # nosec B603 B607


def main() -> int:
    manifest = json.loads((CARRIER / "tmp" / "flood4-fix" / "r17-canopy-network-guard" / "manifest.json").read_text())
    files = manifest["files"]
    bad = [f["path"] for f in files if sha256(CARRIER / f["path"]) != f["sha256"]]
    print(f"carrier files: {len(files)}; sha256 mismatches vs manifest: {bad}")
    changed_on_main = subprocess.run(["git", "-C", str(VAL_MAIN), "diff", "--name-only", BASE_SHA, MAIN_SHA], check=True, capture_output=True, text=True).stdout.split()  # nosec B603 B607
    overlap = [f["path"] for f in files if f["path"] in changed_on_main]
    print(f"carrier files main changed since base: {overlap}")
    for entry in files:
        rel = entry["path"]
        src = CARRIER / rel
        dst = VAL_BASE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        if rel in overlap:
            continue
        dst_main = VAL_MAIN / rel
        dst_main.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst_main)
    scratch = Path(__file__).resolve().parents[2] / "tmp" / "flood4r2-val" / "r17-canopy-network-guard" / "merge"
    scratch.mkdir(parents=True, exist_ok=True)
    for rel in overlap:
        base_p = scratch / (Path(rel).name + ".base")
        main_p = scratch / (Path(rel).name + ".main")
        base_p.write_bytes(git_show(VAL_MAIN, BASE_SHA, rel))
        main_p.write_bytes(git_show(VAL_MAIN, MAIN_SHA, rel))
        merged = subprocess.run(["git", "merge-file", "-p", str(CARRIER / rel), str(base_p), str(main_p)], capture_output=True)  # nosec B603 B607
        print(f"merge-file {rel}: exit {merged.returncode} (0 = clean, >0 = conflict count)")
        (VAL_MAIN / rel).write_bytes(merged.stdout)
    after = [entry["path"] for entry in files if entry["path"] not in overlap and sha256(VAL_MAIN / entry["path"]) != entry["sha256"]]
    after += [entry["path"] for entry in files if sha256(VAL_BASE / entry["path"]) != entry["sha256"]]
    print(f"post-copy sha256 mismatches (expected none): {after}")
    return 0 if not bad and not after else 1


if __name__ == "__main__":
    sys.exit(main())
