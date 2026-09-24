#!/usr/bin/env python3
"""
Open the round-42 probe-provenance PR: every file under util/ad-hoc/2026-09-24_round42_probes/ plus the copier.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use; wraps util/open_signed_pr.py
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

util/open_signed_pr.py takes one `--add LOCAL:REPOPATH` per file, and this PR has 204 of them, which a
session sandbox will not let a shell loop assemble. This builds the list from the directory and passes the
texts through unchanged. `--dry-run` is forwarded.

Usage: python3 util/ad-hoc/2026-09-24_open_round42_probes_pr.py --title T --message M --commit-body-file F --body-file B [--dry-run]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROBES = "util/ad-hoc/2026-09-24_round42_probes"
COPIER = "util/ad-hoc/2026-09-24_copy_round42_probe_scripts.py"
BRANCH = "chore/round42-probe-provenance"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    for flag in ("--title", "--message", "--commit-body-file", "--body-file"):
        ap.add_argument(flag, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    files = sorted(str(p.relative_to(REPO)) for p in (REPO / PROBES).rglob("*") if p.is_file()) + [COPIER, str(Path(__file__).resolve().relative_to(REPO))]
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
