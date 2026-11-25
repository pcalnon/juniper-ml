#!/usr/bin/env python3
"""
Check every "repo#N (date HH:MMZ, `sha`)" citation in the flood-4 record update's added lines against GitHub (validator V1).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11, validator V1 claims lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (validation of the record update's merge times and commits)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md sections 1, 4, 6, 8;
         util/ad-hoc/2026-11-24_flood4_s11_val_claims_prs.py (writes the --prs file)

What it does
------------
Reads the unified diff (``--diff``) of main's record against the drafted record, keeps the added lines, and finds each
pull-request citation followed within the same clause by a parenthesis holding a time: ``repo#N (YYYY-MM-DD HH:MMZ``,
``#N (HH:MMZ`` or ``repo#N (merged YYYY-MM-DD HH:MMZ``. A bare ``#N`` takes the repository of the last named one on
that line (juniper-ml at line start); a time without a date takes the last date seen on that line. Each is compared,
to the minute, with ``mergedAt`` in the ``--prs`` JSON; a sha in backticks inside the same parenthesis is compared with
the merge commit's first 8 hex. Prints one row per citation: OK or DIFF, and a summary.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_val_claims_timecheck.py --diff <record.diff> --prs <prs_v1.json>
"""

from __future__ import annotations

import argparse
import json
import re
import sys

CITE = re.compile(r"(?:(juniper-[a-z-]+)|(?<![\w-]))#(\d+)[^#()]{0,40}?\((?:merged )?((?:20\d\d-\d\d-\d\d )?)(\d\d:\d\dZ)([^)]*)\)")
DATE = re.compile(r"20\d\d-\d\d-\d\d")
SHA = re.compile(r"`([0-9a-f]{8})`")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--diff", required=True)
    ap.add_argument("--prs", required=True)
    args = ap.parse_args()
    with open(args.prs, encoding="utf-8") as fh:
        prs = {r["item"]: r for r in json.load(fh)}
    with open(args.diff, encoding="utf-8") as fh:
        added = [ln[1:] for ln in fh.read().split("\n") if ln.startswith("+") and not ln.startswith("+++")]
    ok = bad = 0
    for ln in added:
        repo = "juniper-ml"
        last_date = None
        pos = 0
        for m in CITE.finditer(ln):
            # carry the last date seen on the line before this match
            for d in DATE.finditer(ln, pos, m.start()):
                last_date = d.group(0)
            pos = m.start()
            if m.group(1):
                repo = m.group(1)
            num = m.group(2)
            date = (m.group(3) or "").strip() or last_date
            if m.group(3):
                last_date = m.group(3).strip()
            hm = m.group(4)[:-1]
            rest = m.group(5)
            item = f"{repo}#{num}"
            rec = prs.get(item)
            if rec is None:
                print(f"NOFETCH | {item} | {date} {hm}")
                continue
            merged = rec.get("mergedAt") or rec.get("closedAt") or rec.get("createdAt") or ""
            gh_date, gh_hm = merged[:10], merged[11:16]
            sha_m = SHA.search(rest)
            sha_ok = True
            if sha_m and rec.get("mergeCommit"):
                sha_ok = rec["mergeCommit"].startswith(sha_m.group(1))
            good = gh_hm == hm and (date is None or date == gh_date) and sha_ok
            ok += good
            bad += not good
            print(f"{'OK  ' if good else 'DIFF'} | {item} | cited {date} {hm} {sha_m.group(1) if sha_m else ''} | github {merged} {(rec.get('mergeCommit') or '')[:8]} | state {rec.get('state')}")
    print(f"summary: {ok} OK, {bad} DIFF", file=sys.stderr)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
