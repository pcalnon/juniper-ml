#!/usr/bin/env python3
"""
Append one clock-stamped line to a validator's PROGRESS.txt (the message is read from a file or from argv).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (Cursor flood-4 session 8: the ml-docs carrier's claims-lens validation)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/ml-docs-s8/PROGRESS.txt

Usage:
  2026-11-14_flood4r2_val_ml-docs_log.py --progress <PROGRESS.txt> (--message <text> | --message-file <file>)
"""

import argparse
import datetime
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--progress", required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--message")
    group.add_argument("--message-file")
    args = ap.parse_args()
    text = args.message if args.message is not None else Path(args.message_file).read_text(encoding="utf-8")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(args.progress, "a", encoding="utf-8") as fh:
        fh.write(f"{stamp} {' '.join(text.split())}\n")
    print(stamp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
