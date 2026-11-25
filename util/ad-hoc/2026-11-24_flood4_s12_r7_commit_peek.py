#!/usr/bin/env python3
"""Show a commit's parents, dates and subject by reading its LOOSE object file (flood-4 session 12, ruling 7's inventory).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (ruling 7's read-only worktree inventory; tmp/flood4/session12/r7/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_flood4_s12_r7_inventory.py (its HEAD-MOVED and branch-tip checks);
    tmp/flood4/session12/briefs/R7_inventory.txt (git aimed at another checkout is refused: read files instead)

A loose object is ``<repo>/.git/objects/<2 hex>/<38 hex>``, zlib-compressed ``commit <size>\\0<body>``. This prints the
body's parent lines, the author and committer dates (UTC) and the subject line; an object kept only in a pack file is
reported as "packed (not readable here)". Author names and emails are not printed.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s12_r7_commit_peek.py REPO SHA [SHA ...]
It reads only.
"""

from __future__ import annotations

import datetime
import sys
import zlib
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"


def _when(line: str) -> str:
    parts = line.split()
    try:
        ts = int(parts[-2])
    except (ValueError, IndexError):
        return "?"
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def peek(repo: str, sha: str) -> str:
    objdir = JUNIPER / repo / ".git" / "objects"
    if len(sha) < 40:
        cands = list((objdir / sha[:2]).glob(sha[2:] + "*")) if (objdir / sha[:2]).is_dir() else []
        if len(cands) != 1:
            return f"{sha}: packed or ambiguous (not readable here; {len(cands)} loose matches)"
        path = cands[0]
    else:
        path = objdir / sha[:2] / sha[2:]
    if not path.is_file():
        return f"{sha}: packed (not readable here)"
    raw = zlib.decompress(path.read_bytes())
    header, body = raw.split(b"\0", 1)
    if not header.startswith(b"commit "):
        return f"{sha}: {header.decode()} (not a commit)"
    text = body.decode("utf-8", "replace")
    head, _, msg = text.partition("\n\n")
    parents = [ln.split()[1][:12] for ln in head.splitlines() if ln.startswith("parent ")]
    author = next((_when(ln) for ln in head.splitlines() if ln.startswith("author ")), "?")
    committer = next((_when(ln) for ln in head.splitlines() if ln.startswith("committer ")), "?")
    signed = any(ln.startswith("gpgsig") for ln in head.splitlines())
    subject = msg.strip().splitlines()[0] if msg.strip() else ""
    return f"{path.parent.name}{path.name}"[:12] + f": parents={','.join(parents) or '-'} authored={author} committed={committer} signed={signed} | {subject[:140]}"


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    repo = sys.argv[1]
    for sha in sys.argv[2:]:
        print(peek(repo, sha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
