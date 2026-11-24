#!/usr/bin/env python3
"""
Print the secret-scan lines of saved GitHub Actions job logs: the engine's version, its command, its counts and its uploads.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-data-client)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
A port of the pull-request secret scan has to state what the action logged on the repository's own pull requests
(the engine version it resolved, the `--log-opts` range it scanned, how many commits it counted) and what the new
steps log on a live run. This reads job logs that were saved with `gh api --method GET .../actions/jobs/<id>/logs`,
strips the timestamps and colour codes, and prints only the lines that carry those facts. It reads files; it calls
nothing.

Usage:
    python3 <this> <saved job log> [<saved job log> ...] [--extra <regex>]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*m")
STAMP = re.compile("^" + chr(0xFEFF) + r"?\d{4}-\d\d-\d\dT[\d:.]+Z ")
SCAN_LINES = r"gitleaks version|Version to install|restored from cache|Downloading gitleaks|event type|gitleaks cmd|commits scanned|no leaks found|leaks found|executing:|gitleaks config|gitleaksignore"
STEP_LINES = r"Scanning \d+ commit|sha256sum|tar\.gz: OK|^8\.\d+\.\d+$|Artifact .* uploaded|files uploaded|Uploading artifact|passed|skipped|##\[error\]|##\[warning\]|Runner Image|^Image: |^Version: \d|git version \d"
WANTED = re.compile(SCAN_LINES + "|" + STEP_LINES)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("logs", nargs="+", type=Path)
    ap.add_argument("--extra", help="a further regex whose matches are printed too")
    args = ap.parse_args()
    extra = re.compile(args.extra) if args.extra else None
    for log in args.logs:
        print(f"=== {log.name}")
        with open(log, encoding="utf-8", errors="replace") as fh:
            for number, raw in enumerate(fh, start=1):
                line = STAMP.sub("", ANSI.sub("", raw.rstrip("\n")))
                if WANTED.search(line) or (extra is not None and extra.search(line)):
                    print(f"{number:>5}: {line[:320]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
