"""
Check a claims lens's fixes.json against the carrier: each "old" occurs exactly once, and all fixes apply in order.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 claims lens of carrier r28 (juniper-canopy's load-sensitive relay test).

Usage:
    python3 -I <this file> --fixes <fixes.json> --carrier <the carrier dir, e.g. tmp/flood4/session14/r28> [--also <path>]

A fix's "file" is "texts/<name>" (read from <carrier>/texts/) or a repository-relative path (read from
<carrier>/final/). --also names an extra copy of CHANGELOG.md (e.g. the builder's merge onto a newer main) to check the
CHANGELOG fixes against as well. The carrier is never written: fixes are applied to in-memory copies only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def target(carrier: Path, rel: str) -> Path:
    return carrier / rel if rel.startswith("texts/") else carrier / "final" / rel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixes", required=True)
    ap.add_argument("--carrier", required=True)
    ap.add_argument("--also", default="")
    args = ap.parse_args()
    carrier = Path(args.carrier)
    fixes = json.loads(Path(args.fixes).read_text(encoding="utf-8"))
    texts: dict[str, str] = {}
    bad = 0
    for f in fixes:
        p = target(carrier, f["file"])
        texts.setdefault(f["file"], p.read_text(encoding="utf-8"))
        n = texts[f["file"]].count(f["old"])
        status = "OK" if n == 1 else f"BAD (occurs {n} times)"
        if n != 1:
            bad += 1
        print(f"{f['id']:5s} {f['severity']:6s} {f['file']}: old {status}")
    # apply in order, to in-memory copies, to prove they do not conflict
    applied = dict(texts)
    for f in fixes:
        cur = applied[f["file"]]
        if cur.count(f["old"]) != 1:
            print(f"APPLY {f['id']}: old no longer occurs exactly once after earlier fixes ({cur.count(f['old'])})")
            bad += 1
            continue
        applied[f["file"]] = cur.replace(f["old"], f["new"], 1)
    if args.also:
        merged = Path(args.also).read_text(encoding="utf-8")
        for f in fixes:
            if f["file"] == "CHANGELOG.md":
                n = merged.count(f["old"])
                print(f"{f['id']:5s} also {args.also.split('/')[-1]}: old occurs {n} times")
                if n != 1:
                    bad += 1
    print(f"{len(fixes)} fixes, {bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
