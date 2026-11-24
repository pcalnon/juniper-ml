#!/usr/bin/env python3
"""
Derive a mutation spec from another: same mutants, another worktree, and the sha256 each file must have first.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: finishing juniper-data's stage-3 carrier, session 6)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (the predecessor's "before" spec, run again on a byte-identical twin of the carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: 2026-11-11_flood4r2_data-landing_mutants.py (the runner; its ``expect_sha256`` key);
         tmp/flood4/session6/BRIEF_S6_ADDENDUM.txt step 1

Usage:
    python3 <this> --in <spec.json> --out <spec.json> --worktree <absolute path>
                   --expect-sha256 <repo-relative file>=<sha256> [--expect-sha256 ...] [--note <text>]

The mutants are copied unchanged: the output's ``mutants`` equals the input's, and the script exits 1 if it does not.
Only ``worktree`` and ``expect_sha256`` are set, and ``derived_from`` records the input's path and sha256. The
expected hashes are given by the caller (the ones the carrier's record states), never read from the tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--in", dest="source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--expect-sha256", action="append", default=[], help="<repo-relative file>=<sha256>")
    ap.add_argument("--note", default="")
    args = ap.parse_args()
    raw = args.source.read_bytes()
    spec = json.loads(raw.decode("utf-8"))
    derived = dict(spec)
    derived["derived_from"] = {"spec": str(args.source.resolve()), "sha256": hashlib.sha256(raw).hexdigest(), "worktree_there": spec.get("worktree"), "note": args.note}
    derived["worktree"] = args.worktree
    derived["expect_sha256"] = dict(item.split("=", 1) for item in args.expect_sha256)
    same = derived["mutants"] == spec["mutants"]
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(derived, fh, indent=1)
        fh.write("\n")
    print(json.dumps({"out": str(args.out), "mutants": len(derived["mutants"]), "mutants_unchanged": same, "worktree": derived["worktree"], "expect_sha256": derived["expect_sha256"]}, indent=1))
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
