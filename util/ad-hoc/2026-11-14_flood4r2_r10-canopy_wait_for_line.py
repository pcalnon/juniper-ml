#!/usr/bin/env python3
"""
Wait until a log file holds a line matching a regular expression, or a deadline passes; print the matching lines.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-canopy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10)

WHY THIS EXISTS
The port's mutation check runs alone in the background for many minutes, and nothing else may run while it does. This
reads the check's log every few seconds (it writes nothing and starts nothing) and returns as soon as the log holds a
line matching --pattern, printing every line that matches --show, so the builder learns the result without polling by
hand. Exit 0 when the pattern appeared, 1 at the deadline.

Usage:
    python3 <this> --log <file> --pattern <regex> [--show <regex>] [--timeout <seconds>] [--interval <seconds>]
"""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--pattern", required=True)
    ap.add_argument("--show")
    ap.add_argument("--timeout", type=float, default=540.0)
    ap.add_argument("--interval", type=float, default=5.0)
    args = ap.parse_args()
    done = re.compile(args.pattern, re.MULTILINE)
    show = re.compile(args.show or args.pattern)
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        text = args.log.read_text(encoding="utf-8", errors="replace") if args.log.is_file() else ""
        if done.search(text):
            for line in text.splitlines():
                if show.search(line):
                    print(line)
            return 0
        time.sleep(args.interval)
    print(f"deadline: no line matching {args.pattern!r} in {args.log} after {args.timeout:.0f} s")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
