#!/usr/bin/env python3
"""Extract the RecoveryTool's verb and usage strings from its .NET assembly, without EXECUTING it.

Project:     juniper-ml
Sub-Project: backup infrastructure
Author:      Paul Calnon
Created:     2026-09-22
Status:      ad-hoc -- product capability probe
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-09-22_duplicati_literal_scan.py (found `reencrypt` in this assembly)

WHY NOT JUST RUN IT WITH `help`. On this host a Duplicati binary invoked for information has
already proved willing to do work instead: `duplicati-server --version` STARTS A SERVER on 8200.
The blast radius of a wrong guess here is a live service or a touched destination, and the backup
is already down. Reading the assembly answers the question with no process started at all.

.NET stores user strings in the `#US` heap as UTF-16LE, so an ASCII grep under-reports; this reads
both encodings, exactly as the literal scanner does.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_DLL = "/usr/lib/duplicati/Duplicati.CommandLine.RecoveryTool.Implementation.dll"
PRINTABLE = re.compile(r"[\x20-\x7e]{4,}")


def strings_utf8(blob: bytes) -> list[str]:
    return [m.group(0) for m in PRINTABLE.finditer(blob.decode("latin-1"))]


def strings_utf16le(blob: bytes) -> list[str]:
    # Decode the odd and even byte planes separately so a UTF-16LE run reads as ASCII.
    out: list[str] = []
    for offset in (0, 1):
        plane = blob[offset::2]
        out.extend(m.group(0) for m in PRINTABLE.finditer(plane.decode("latin-1")))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dll", default=DEFAULT_DLL)
    ap.add_argument("--grep", default="reencrypt|recompress|restore|download|index|passphrase|Usage|usage:")
    args = ap.parse_args()

    path = Path(args.dll)
    if not path.is_file():
        print(f"no such assembly: {path}")
        return 1
    blob = path.read_bytes()
    pattern = re.compile(args.grep, re.I)

    seen: set[str] = set()
    for enc, items in (("utf-8", strings_utf8(blob)), ("utf-16le", strings_utf16le(blob))):
        for s in items:
            s = s.strip()
            if len(s) < 5 or not pattern.search(s):
                continue
            key = (enc, s)
            if key in seen:
                continue
            seen.add(key)
            print(f"  [{enc:<8}] {s[:160]}")
    print(f"\n  {len(seen)} matching string(s) in {path.name} ({len(blob):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
