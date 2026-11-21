"""
Freeze a landed (uncommitted) tree for the session-6 sequence-safety probe (claims lens, session 8): writes
<out>/paths.txt ("add <path>" / "delete <path>" for every change git status reports against HEAD, untracked files
included), <out>/snapshot/<path> copies and <out>/plan.json {"main_sha": HEAD}. Reads the tree; writes only <out>.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py (reads what this writes)
"""

import argparse
import json
import shutil
import subprocess  # nosec B404 - fixed argv, read-only plumbing in the validator's own landing worktree
import sys
from pathlib import Path


def git(tree: Path, *argv: str) -> str:
    done = subprocess.run(["git", *argv], cwd=str(tree), capture_output=True, check=True)  # nosec B603 B607
    return done.stdout.decode()


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze a landed tree for the probe.")
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    head = git(args.tree, "rev-parse", "HEAD").strip()
    rows = []
    for line in git(args.tree, "status", "--porcelain", "--untracked-files=all", "-z").split("\0"):
        if not line:
            continue
        status, path = line[:2], line[3:]
        if "D" in status:
            rows.append(f"delete {path}")
            continue
        rows.append(f"add {path}")
        target = args.out / "snapshot" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.tree / path, target)
    (args.out / "paths.txt").write_text("\n".join(rows) + "\n")
    (args.out / "plan.json").write_text(json.dumps({"main_sha": head, "paths": len(rows)}, indent=1) + "\n")
    print(f"froze {len(rows)} paths of {args.tree} on HEAD {head[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
