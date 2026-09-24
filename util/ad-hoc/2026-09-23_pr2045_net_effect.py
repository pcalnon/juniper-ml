#!/usr/bin/env python3
"""Compute what juniper-ml#2045 would ACTUALLY change against current main, file by file.

Project:     juniper-ml
Sub-Project: PR triage
Author:      Paul Calnon
Created:     2026-09-23
Status:      ad-hoc -- PR triage
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

WHY THIS IS NOT THE PR'S OWN FILE LIST. GitHub computes `added`/`modified` against the MERGE-BASE.
When a branch is cut from a stale point and main then moves, that list describes the branch's
history, not its effect: #2045 lists 669 files, yet `util/safe_merge.py` and `.github/workflows/ci.yml`
are byte-identical to main. Reading the PR's own counts as "what will change" is exactly the
stale-checkout misread that nearly shipped a 10,000-line revert earlier in this arc.

So: fetch each file's blob AT THE BRANCH HEAD and compare it to the same path on main. Three
outcomes per path -- SAME (no effect), DIFFERS (a real change to review), ABSENT-ON-MAIN (a genuine
addition). Read-only; touches nothing.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys

OWNER, REPO = "pcalnon", "juniper-ml"


def gh(args: list[str]) -> str:
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode != 0:
        return ""
    return out.stdout


def blob_at(path: str, ref: str) -> bytes | None:
    raw = gh(["api", f"repos/{OWNER}/{REPO}/contents/{path}?ref={ref}", "--jq", ".content"])
    if not raw.strip():
        return None
    try:
        return base64.b64decode(raw)
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--status", default="modified", help="which PR file status to examine")
    args = ap.parse_args()

    meta = gh(["api", f"repos/{OWNER}/{REPO}/pulls/{args.pr}", "--jq", ".head.ref"]).strip()
    if not meta:
        print(f"could not resolve head ref for #{args.pr}", file=sys.stderr)
        return 2
    head = meta

    listing = gh([
        "api", "--paginate", f"repos/{OWNER}/{REPO}/pulls/{args.pr}/files?per_page=100",
        "--jq", ".[] | select(.status==\"" + args.status + "\") | .filename",
    ])
    paths = [p for p in listing.splitlines() if p.strip()]
    print(f"#{args.pr} head={head}  examining {len(paths)} '{args.status}' file(s) against main\n")

    same = differs = absent = 0
    changed: list[str] = []
    for p in paths:
        b_head, b_main = blob_at(p, head), blob_at(p, "main")
        if b_main is None:
            absent += 1
            print(f"  NEW-ON-MAIN   {p}")
        elif b_head == b_main:
            same += 1
        else:
            differs += 1
            changed.append(p)
            print(f"  DIFFERS       {p}")

    print(f"\n  identical to main : {same}")
    print(f"  differs from main : {differs}")
    print(f"  absent on main    : {absent}")
    if differs == 0 and absent == 0:
        print("\n  NET EFFECT: none. Every examined path already matches main.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
