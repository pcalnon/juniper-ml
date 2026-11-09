#!/usr/bin/env python3
# Project:      juniper-ml
# Sub-Project:  util/ad-hoc
# Application:  flood-4 docs-carrier validation (fidelity lens)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Purpose:      Read-only: one GraphQL query returning headRefOid/state for the named juniper-ml PRs,
#               compared against the local refs/flood4/pr/<N> refs. No mutation of any kind.
"""
Read-only: compare the named juniper-ml PRs' GitHub head SHAs, state and draft flag (one GraphQL query) with the local refs/flood4/pr/<N> refs.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 1, structure-and-fidelity lens (findings: tmp/flood4/ml-docs/val-fidelity/)
"""

import json
import subprocess
import sys

prs = [int(a) for a in sys.argv[1:]]
fields = " ".join(f"p{n}: pullRequest(number: {n}) {{ number headRefOid state isDraft }}" for n in prs)
query = f'query {{ repository(owner: "pcalnon", name: "juniper-ml") {{ {fields} }} }}'
out = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"], capture_output=True, text=True, check=True)
data = json.loads(out.stdout)["data"]["repository"]
for n in prs:
    pr = data[f"p{n}"]
    local = subprocess.run(["git", "rev-parse", f"refs/flood4/pr/{n}"], capture_output=True, text=True).stdout.strip()
    print(n, pr["headRefOid"][:10], local[:10], "SAME" if local == pr["headRefOid"] else "DIFF", pr["state"], "draft" if pr["isDraft"] else "ready")
