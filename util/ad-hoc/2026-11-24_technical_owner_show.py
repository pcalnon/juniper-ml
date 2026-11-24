#!/usr/bin/env python3
"""
Show the base (pre-#2606) text around a line, so a technical-owner candidate can be judged in context.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — investigation (the technical-owner sweep that follows juniper-ml#2606)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_technical_owner_candidates.py

Usage
-----
    python3 util/ad-hoc/2026-11-24_technical_owner_show.py [--ref 515e16a0] [--context N] PATH:LINE [PATH:LINE ...]

Prints lines LINE-N .. LINE+N of PATH at REF (default ``515e16a0``, main just before #2606), each cut to 400
characters, with the asked-for line marked ``>``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--ref", default="515e16a0")
    ap.add_argument("--context", type=int, default=1)
    ap.add_argument("where", nargs="+")
    args = ap.parse_args(argv)
    for where in args.where:
        path, _, number = where.rpartition(":")
        line = int(number)
        proc = subprocess.run(["git", "show", f"{args.ref}:{path}"], capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"== {where}: not at {args.ref}")
            continue
        lines = proc.stdout.split("\n")
        print(f"== {where}")
        for n in range(max(1, line - args.context), min(len(lines), line + args.context) + 1):
            print(f"{'>' if n == line else ' '}{n:6d}  {lines[n - 1][:400]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
