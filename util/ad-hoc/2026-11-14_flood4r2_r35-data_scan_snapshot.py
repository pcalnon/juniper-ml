#!/usr/bin/env python3
"""Freeze a juniper-data carrier's changed files and its PR texts for a secret scan, beside main's copies of the same paths.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use helper of the Cursor flood-4 disposition arc: the juniper-data back-port of the
             gitleaks pull-request scan's blocking-wiring pins)
Author:      Paul Calnon
Created:     2026-11-14
Status:      ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related:     util/ad-hoc/2026-11-09_flood4r2_land_gitleaks.py (scans <out>/files against <out>/main)
Version:     0.1.0
License:     MIT License

Writes <out>/files/<path> (each changed file as it stands in the worktree, and each text under pr-texts/) and
<out>/main/<path> (main's copy at --base, from `git show`), then prints the scan command. It never writes into the
worktree outside <out>.

Usage:
    python3 util/ad-hoc/2026-11-14_flood4r2_r35-data_scan_snapshot.py --worktree <checkout> --base <sha> --out <dir>
        --texts <file> [<file> ...] -- <path> [<path> ...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 -- runs git show with a fixed argv
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    """Freeze the snapshot and the baseline, and record their hashes."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--texts", nargs="+", default=[])
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    worktree = Path(args.worktree).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    files, main_dir = out / "files", out / "main"
    record: dict[str, dict[str, str]] = {"files": {}, "main": {}}
    for rel in args.paths:
        target = files / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(worktree / rel, target)
        record["files"][rel] = hashlib.sha256(target.read_bytes()).hexdigest()
        proc = subprocess.run(["git", "show", f"{args.base}:{rel}"], cwd=worktree, capture_output=True, check=False)  # nosec B603 B607
        if proc.returncode == 0:
            base_copy = main_dir / rel
            base_copy.parent.mkdir(parents=True, exist_ok=True)
            base_copy.write_bytes(proc.stdout)
            record["main"][rel] = hashlib.sha256(proc.stdout).hexdigest()
    for text in args.texts:
        target = files / "pr-texts" / Path(text).name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(text, target)
        record["files"][f"pr-texts/{Path(text).name}"] = hashlib.sha256(target.read_bytes()).hexdigest()
    (out / "snapshot.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"froze {len(record['files'])} file(s) and {len(record['main'])} main copies under {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
