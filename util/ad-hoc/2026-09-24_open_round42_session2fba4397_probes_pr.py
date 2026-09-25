#!/usr/bin/env python3
"""
Open the provenance PR for session 2fba4397's round-42 probes: its six lane directories, the README and the copier.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use; wraps util/open_signed_pr.py
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

The sibling util/ad-hoc/2026-09-24_open_round42_probes_pr.py (juniper-ml#2081) uploads every file under
util/ad-hoc/2026-09-24_round42_probes/. This uploads only the six directories
util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py filled, plus the README it extends,
so the whole-file upload cannot touch the directories #2081 shipped. util/open_signed_pr.py takes one
`--add LOCAL:REPOPATH` per file, which a session sandbox will not let a shell loop assemble, so this
builds the list. `--dry-run` is forwarded.

Usage: python3 util/ad-hoc/2026-09-24_open_round42_session2fba4397_probes_pr.py --title T --message M --commit-body-file F --body-file B [--dry-run]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROBES = "util/ad-hoc/2026-09-24_round42_probes"
DIRS = [
    "register-fixforward2-round1-laneA",
    "register-fixforward2-round1-laneB",
    "register-fixforward2-round2-laneA",
    "register-fixforward2-round2-laneB",
    "data438-fixforward-round1-laneA",
    "data438-fixforward-round1-laneB",
]
COPIER = "util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py"
BRANCH = "chore/round42-probe-provenance-session-2fba4397"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    for flag in ("--title", "--message", "--commit-body-file", "--body-file"):
        ap.add_argument(flag, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    files = sorted(str(p.relative_to(REPO)) for d in DIRS for p in (REPO / PROBES / d).rglob("*") if p.is_file())
    files += [f"{PROBES}/README.md", COPIER, str(Path(__file__).resolve().relative_to(REPO))]
    missing = [f for f in files if not (REPO / f).is_file()]
    if missing:
        raise SystemExit(f"missing files, nothing opened: {missing}")
    cmd = [sys.executable, str(REPO / "util/open_signed_pr.py"), "--repo", "juniper-ml", "--branch", BRANCH]
    for f in files:
        cmd += ["--add", f"{f}:{f}"]
    cmd += ["--message", args.message, "--commit-body-file", args.commit_body_file, "--title", args.title, "--body-file", args.body_file]
    if args.dry_run:
        cmd.append("--dry-run")
    print(f"{len(files)} files -> {BRANCH}")
    return subprocess.run(cmd, cwd=REPO).returncode


if __name__ == "__main__":
    raise SystemExit(main())
