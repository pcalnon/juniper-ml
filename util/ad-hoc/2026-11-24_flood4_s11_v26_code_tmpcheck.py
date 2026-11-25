#!/usr/bin/env python3
"""List entries newer than a marker file under the given system temp directories (V26 CODE-lens validator, flood-4 session 11).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (validation of the ruling-26 lockfile-print ports; tmp/flood4/session11/r26/val_code/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session11/briefs/V26_ports_validator.txt (CODE lens, the TRAP paragraph);
    notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 26)

The directories to scan are positional arguments, so this file names no system temp path itself. It walks each one to
--maxdepth (default 2, the depth `find DIR -maxdepth 2` reaches), reports every entry whose mtime is newer than --marker
with its owner and mtime, and appends the block (with a label and a UTC timestamp) to --out. It reads only; it never
creates, changes or deletes anything in the scanned directories.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s11_v26_code_tmpcheck.py --marker FILE --out FILE --label TEXT DIR [DIR ...]
Exit 0 always (the listing is the result); 2 when the marker is missing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import pwd
import sys
from pathlib import Path


def _owner(uid: int) -> str:
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def _walk(root: Path, maxdepth: int, newer_than: float) -> list[str]:
    hits: list[str] = []
    stack: list[tuple[Path, int]] = [(root, 0)]
    while stack:
        path, depth = stack.pop()
        try:
            st = path.lstat()
        except OSError:
            continue
        if st.st_mtime > newer_than:
            stamp = dt.datetime.fromtimestamp(st.st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            hits.append(f"{_owner(st.st_uid)} {stamp} {path}")
        if depth >= maxdepth or not path.is_dir() or path.is_symlink():
            continue
        try:
            children = sorted(os.scandir(path), key=lambda entry: entry.name)
        except OSError:
            continue
        for child in children:
            stack.append((Path(child.path), depth + 1))
    return sorted(hits)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--marker", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--maxdepth", type=int, default=2)
    parser.add_argument("dirs", nargs="+", type=Path)
    args = parser.parse_args()
    if not args.marker.is_file():
        print(f"marker missing: {args.marker}", file=sys.stderr)
        return 2
    newer_than = args.marker.stat().st_mtime
    now = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marker_stamp = dt.datetime.fromtimestamp(newer_than, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    lines = [f"== {args.label} -- {now} (marker mtime {marker_stamp}; maxdepth {args.maxdepth}) =="]
    for root in args.dirs:
        hits = _walk(root, args.maxdepth, newer_than)
        lines.append(f"  {root}: {len(hits)} entr{'y' if len(hits) == 1 else 'ies'} newer than the marker")
        lines.extend(f"    {hit}" for hit in hits)
    text = "\n".join(lines) + "\n"
    with args.out.open("a", encoding="utf-8") as fh:
        fh.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
