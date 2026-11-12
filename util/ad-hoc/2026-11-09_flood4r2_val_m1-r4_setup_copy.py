#!/usr/bin/env python3
"""
Create the round-4 validator's own juniper-data worktree and copy the M-1 carrier's seven changed files into it.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (round-4 validation of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
The validator must never write to the carrier worktree (other validators read it at the same time). Every test,
mutant and probe therefore runs on a detached worktree of juniper-data at the carrier's base, with the carrier's
files copied in and their sha256 compared with the carrier's, so a later reader can tell exactly what was tested.

Usage:
    python3 <this> --carrier <carrier worktree> --base <sha> --dest <new worktree path> --out <scratch dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 - fixed argv: git worktree add on the juniper-data primary
import sys
from pathlib import Path

JD_PRIMARY = Path.home() / "Development" / "python" / "Juniper" / "juniper-data"
FILES = (
    ".github/workflows/ci.yml",
    "CHANGELOG.md",
    "docs/ci_cd/CICD_MANUAL.md",
    "docs/ci_cd/CICD_REFERENCE.md",
    "juniper_data/tests/unit/test_gitleaks_config.py",
    "util/ad-hoc/2026-11-08_reproduce_gitleaks_pr_commit_window.py",
    "util/ad-hoc/2026-11-08_verify_gitleaks_pr_scan_tests_are_not_vacuous.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--carrier", required=True, type=Path)
    ap.add_argument("--base", required=True)
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "-C", str(args.carrier), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()  # nosec B603 B607
    if not head.startswith(args.base):
        print(f"carrier HEAD {head} is not the base {args.base}")
        return 2
    if not args.dest.exists():
        subprocess.run(["git", "-C", str(JD_PRIMARY), "worktree", "add", "--detach", str(args.dest), args.base], check=True)  # nosec B603 B607
    record = {"carrier": str(args.carrier), "carrier_head": head, "dest": str(args.dest), "files": {}}
    ok = True
    for rel in FILES:
        src = args.carrier / rel
        dst = args.dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        a, b = sha256(src), sha256(dst)
        record["files"][rel] = {"carrier": a, "copy": b, "same": a == b}
        ok = ok and a == b
    status = subprocess.run(["git", "-C", str(args.dest), "status", "--short"], capture_output=True, text=True, check=True).stdout  # nosec B603 B607
    record["copy_status"] = status.splitlines()
    record["identical"] = ok
    (args.out / "copy_record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
