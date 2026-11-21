#!/usr/bin/env python3
"""
Write a freeze directory (paths.txt, snapshot/, plan.json) from a landed worktree, for the sequence-safety probe.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py (reads the directory this writes)

WHY THIS EXISTS
CI's two sequence-safety screens read a commit: its tree and its message. The probe builds that commit from a
freeze directory. This writes one from the validator's landed worktree: every path `git status` names there is an
`add` (the carrier deletes nothing; a deleted path stops the run), its bytes are copied under snapshot/, and
plan.json records the main the worktree is detached at.

Usage:
    python3 <this> --landed <landing worktree> --out <freeze dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 - fixed argv: read-only plumbing in the validator's own landing worktree
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--landed", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    landed, out = args.landed.resolve(), args.out.resolve()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=landed, capture_output=True, text=True, check=True).stdout.strip()  # nosec B603 B607
    status = subprocess.run(["git", "status", "--porcelain"], cwd=landed, capture_output=True, text=True, check=True).stdout.splitlines()  # nosec B603 B607
    if out.exists():
        shutil.rmtree(out)
    (out / "snapshot").mkdir(parents=True)
    lines, files = [], {}
    for row in status:
        code, path = row[:2], row[3:]
        if "D" in code or not (landed / path).is_file():
            raise SystemExit(f"unexpected status row: {row!r}")
        target = out / "snapshot" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(landed / path, target)
        lines.append(f"add {path}")
        files[path] = hashlib.sha256(target.read_bytes()).hexdigest()
    (out / "paths.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "plan.json").write_text(json.dumps({"main_sha": head, "source": str(landed), "files": files}, indent=2) + "\n", encoding="utf-8")
    print(f"{len(lines)} paths frozen from {landed} at {head[:8]} into {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
