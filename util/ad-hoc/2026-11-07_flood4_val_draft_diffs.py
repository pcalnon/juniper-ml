#!/usr/bin/env python3
# Project:      juniper-ml
# Sub-Project:  util/ad-hoc
# Application:  flood-4 docs-carrier validation (fidelity lens)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Purpose:      Read-only: for each draft PR N (local ref refs/flood4/pr/N), compute merge-base with
#               origin/main and write the draft's OWN diff (merge-base..head, -U4) to
#               <outdir>/draft_<N>.diff.patch, plus a one-line summary per draft (merge-base, files).
"""
Save each draft PR's own diff (its merge-base with origin/main to the local refs/flood4/pr/<N> head, -U4) as <outdir>/draft_<N>.diff.patch and print one summary line per draft (merge-base, files).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 1, structure-and-fidelity lens (findings: tmp/flood4/ml-docs/val-fidelity/)
"""

import os
import subprocess
import sys

outdir = sys.argv[1]
prs = sys.argv[2:]
os.makedirs(outdir, exist_ok=True)


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


for n in prs:
    ref = f"refs/flood4/pr/{n}"
    mb = git("merge-base", "origin/main", ref).strip()
    files = git("diff", "--name-only", mb, ref).split()
    diff = git("diff", "-U4", mb, ref)
    with open(os.path.join(outdir, f"draft_{n}.diff.patch"), "w", encoding="utf-8") as fh:
        fh.write(diff)
    print(n, mb[:10], len(files), " ".join(files))
