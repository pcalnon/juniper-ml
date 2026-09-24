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

DEFECT THIS TOOL SHIPPED WITH, FOUND BY AN INDEPENDENT VALIDATOR 2026-09-24. The first run examined
`--status modified` by CONTENT but the `added` set was checked only by PATH, with `comm` over two
filename lists. A path present on main was reported "already there" without anyone comparing bytes.
On ml#2045 that hid a real divergence: `util/ad-hoc/smart_checks_backup-sda.bash` is listed `added`
(it did not exist at that stale merge-base), exists on main, and differs by 102 lines -- #2045 would
have rewritten the very script it was named for. The reported net effect was "1 file"; it was 2.

The two halves of one comparison were measured in different UNITS -- paths against bytes -- and the
weaker unit silently governed the answer. `--status all` is now the default and every path is
compared by content, whatever GitHub labelled it.
"""

from __future__ import annotations

import argparse
import base64
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
    ap.add_argument(
        "--status", default="all",
        help="which PR file status to examine: added, modified, removed, or all (default). "
             "'all' is the honest choice -- GitHub's label is relative to the stale merge-base, "
             "so an 'added' path may well exist on main with different bytes.",
    )
    args = ap.parse_args()

    meta = gh(["api", f"repos/{OWNER}/{REPO}/pulls/{args.pr}", "--jq", ".head.ref"]).strip()
    if not meta:
        print(f"could not resolve head ref for #{args.pr}", file=sys.stderr)
        return 2
    head = meta

    listing = gh([
        "api", "--paginate", f"repos/{OWNER}/{REPO}/pulls/{args.pr}/files?per_page=100",
        "--jq", ".[] | .filename" if args.status == "all"
                 else ".[] | select(.status==\"" + args.status + "\") | .filename",
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
