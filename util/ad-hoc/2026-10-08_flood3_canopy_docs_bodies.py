#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use, read-only (gh GET only). Save the bodies of the canopy docs-slice PRs to one file.
# Usage: 2026-10-08_flood3_canopy_docs_bodies.py <out.md>
"""Dump PR titles + bodies for the canopy docs slice."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PRS = [698, 700, 703, 706, 713, 714, 716, 717, 723, 725, 726]


def main(argv: list[str]) -> int:
    out = Path(argv[0])
    chunks = []
    for n in PRS:
        raw = subprocess.run(
            ["gh", "pr", "view", str(n), "-R", "pcalnon/juniper-canopy", "--json", "number,title,body,createdAt,headRefName,state,isDraft"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        d = json.loads(raw)
        chunks.append(f"=== #{d['number']} [{d['state']} draft={d['isDraft']}] {d['title']} ({d['createdAt']}, {d['headRefName']})\n{d['body']}\n")
    out.write_text("\n".join(chunks), encoding="utf-8")
    print(f"wrote {out} ({sum(c.count(chr(10)) for c in chunks)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
