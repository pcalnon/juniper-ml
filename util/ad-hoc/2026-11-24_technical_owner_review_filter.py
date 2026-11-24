#!/usr/bin/env python3
"""
Print slices of the technical-owner candidate list for review: by the word after or before the token, its position or its nets.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — investigation (the technical-owner sweep that follows juniper-ml#2606)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_technical_owner_candidates.py (writes the TSV this reads)

Usage
-----
    python3 util/ad-hoc/2026-11-24_technical_owner_review_filter.py TSV [--after W ...] [--before W ...]
        [--kind K ...] [--net N ...] [--path-glob G] [--width 55]

Each selector narrows the rows; repeated values of one selector are alternatives. Words compare lowercased.
The token is shown as [[owner]] in its BASE line.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("tsv")
    ap.add_argument("--after", nargs="*", default=[])
    ap.add_argument("--before", nargs="*", default=[])
    ap.add_argument("--kind", nargs="*", default=[])
    ap.add_argument("--net", nargs="*", default=[])
    ap.add_argument("--path-glob")
    ap.add_argument("--width", type=int, default=55)
    args = ap.parse_args(argv)
    after = {w.lower() for w in args.after}
    before = {w.lower() for w in args.before}
    shown = 0
    with open(args.tsv, encoding="utf-8") as handle:
        for raw in handle:
            row = raw.rstrip("\n").split("\t")  # status, where, occurrence, orig, got, nets, kind, window
            where, occurrence, nets, kind, window = row[1], row[2], row[5], row[6], row[7]
            if args.kind and kind not in args.kind:
                continue
            if args.net and not any(n == f or f.startswith(n) for f in nets.split(",") for n in args.net):
                continue
            if args.path_glob and not fnmatch.fnmatch(where.rsplit(":", 1)[0], args.path_glob):
                continue
            i, j = window.find("[["), window.find("]]")
            match_after = re.match(r"[\s*_`'’-]*([A-Za-z]+)", window[j + 2 :])
            match_before = re.search(r"([A-Za-z]+)[^A-Za-z]*$", window[:i])
            word_after = match_after.group(1).lower() if match_after else ""
            word_before = match_before.group(1).lower() if match_before else ""
            if after and word_after not in after:
                continue
            if before and word_before not in before:
                continue
            print(f"{where}\t{occurrence}\t{kind}\t{window[max(0, i - args.width) : j + 2 + args.width]}")
            shown += 1
    print(f"-- {shown} row(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
