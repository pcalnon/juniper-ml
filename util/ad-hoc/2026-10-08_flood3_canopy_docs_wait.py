#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use, read-only. Block until every named file exists (or --timeout seconds pass), printing
# each file as it appears. Used to wait on fork outputs without a shell `sleep`.
# Usage: 2026-10-08_flood3_canopy_docs_wait.py --timeout 540 <file> [<file> ...]
"""Wait for files to appear."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=540.0)
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()
    pending = {Path(f) for f in args.files}
    deadline = time.monotonic() + args.timeout
    for p in sorted(pending):
        if p.exists():
            print(f"present: {p.name}", flush=True)
    pending = {p for p in pending if not p.exists()}
    while pending and time.monotonic() < deadline:
        time.sleep(5)
        arrived = {p for p in pending if p.exists()}
        for p in sorted(arrived):
            print(f"arrived: {p.name} at {time.strftime('%H:%M:%S')}", flush=True)
        pending -= arrived
    for p in sorted(pending):
        print(f"still missing: {p.name}", flush=True)
    return 0 if not pending else 1


if __name__ == "__main__":
    sys.exit(main())
