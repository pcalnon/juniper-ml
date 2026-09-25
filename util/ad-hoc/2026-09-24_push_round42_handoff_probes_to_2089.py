#!/usr/bin/env python3
"""
Add the probes of session 2fba4397's handoff-validation lanes to juniper-ml#2089, as one signed commit.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use; wraps util/push_signed_commit.py
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

juniper-ml#2089 preserves the probe scripts of session 2fba4397's round-42 lanes, off tmpfs. The lanes
that validated the session's two handoffs (its own, and the consolidated handoff of both round-42 lanes)
wrote probes too, and their reports ship in the consolidation PR (branch docs/handoff-round42-consolidated)
citing those probes by scratch path. util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py
copied them into one new directory per lane (DIRS); this pushes those directories, the README rows that describe them,
the copier and this script onto #2089's branch. util/push_signed_commit.py takes one `--add` per file,
which a session sandbox will not let a shell loop assemble, so this builds the list. `--dry-run` is
forwarded; `--expected-head` must be #2089's FULL head sha, read from gh.

Usage: python3 util/ad-hoc/2026-09-24_push_round42_handoff_probes_to_2089.py --expected-head SHA --message M --commit-body-file F [--dry-run]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROBES = "util/ad-hoc/2026-09-24_round42_probes"
DIRS = [
    "handoff-2fba4397-round1-laneF",
    "handoff-2fba4397-round2-laneF",
    "handoff-2fba4397-round3-laneF",
    "handoff-consolidated-round1-laneF",
    "handoff-consolidated-round2-laneF",
    "handoff-consolidated-round2-laneP",
    "handoff-consolidated-round3-laneF",
    "handoff-consolidated-round3-laneP",
    "handoff-consolidated-round4-laneF",
    "handoff-consolidated-round4-laneO",
]
COPIER = "util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py"
BRANCH = "chore/round42-probe-provenance-session-2fba4397"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    for flag in ("--expected-head", "--message", "--commit-body-file"):
        ap.add_argument(flag, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if len(args.expected_head) != 40:
        raise SystemExit("--expected-head must be the full 40-hex sha of #2089's head, read from gh")
    files = sorted(str(p.relative_to(REPO)) for d in DIRS for p in (REPO / PROBES / d).rglob("*") if p.is_file())
    files += [f"{PROBES}/README.md", COPIER, str(Path(__file__).resolve().relative_to(REPO))]
    missing = [f for f in files if not (REPO / f).is_file()]
    if missing:
        raise SystemExit(f"missing files, nothing pushed: {missing}")
    cmd = [sys.executable, str(REPO / "util/push_signed_commit.py"), "--repo", "juniper-ml", "--branch", BRANCH, "--expected-head", args.expected_head]
    for f in files:
        cmd += ["--add", f"{f}:{f}"]
    cmd += ["--message", args.message, "--commit-body-file", args.commit_body_file]
    if args.dry_run:
        cmd.append("--dry-run")
    print(f"{len(files)} files -> {BRANCH} (on {args.expected_head[:8]})")
    return subprocess.run(cmd, cwd=REPO).returncode


if __name__ == "__main__":
    raise SystemExit(main())
