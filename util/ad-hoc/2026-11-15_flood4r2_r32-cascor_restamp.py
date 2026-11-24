#!/usr/bin/env python3
"""
Re-date (and, when main moved, re-version) every stamp site a stamps.json lists, in one command.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — one-off (Cursor flood-4 round 2: the r32 pause carriers' freeze)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling of 2026-11-13 ("Fix it + document"); the session-9 brief addendum, section 4

stamps.json carries ``"root"`` (the carrier worktree) and ``"sites"``: a list of
``{"path": <relative to root>, "pattern": <regex with ONE group>, "kind": "date" | "version", "count": N}``.
Each site's group is replaced by ``--date`` (kind date) or ``--version`` (kind version; a site is left
alone when ``--version`` is not given). ``count`` is how many matches the site must have, so a site
that moved or vanished fails loudly instead of being skipped. Without ``--apply`` it only reports.

Usage:
  2026-11-15_flood4r2_r32-cascor_restamp.py --stamps <stamps.json> --date YYYY-MM-DD [--version X.Y.Z] [--apply]
Exit: 0 when every site matched its count (and, with --apply, was written); 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--stamps", required=True, type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--version")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not DATE.match(args.date) or (args.version is not None and not VERSION.match(args.version)):
        print("bad --date or --version", file=sys.stderr)
        return 1
    with open(args.stamps, encoding="utf-8") as fh:
        stamps = json.load(fh)
    root = Path(stamps["root"])
    ok = True
    texts: dict = {}
    for site in stamps["sites"]:
        path = root / site["path"]
        if path not in texts:
            texts[path] = path.read_text(encoding="utf-8")
        pattern = re.compile(site["pattern"], re.MULTILINE)
        found = len(pattern.findall(texts[path]))
        if found != site.get("count", 1):
            print(f"MISMATCH {site['path']} /{site['pattern']}/: {found} matches, expected {site.get('count', 1)}")
            ok = False
            continue
        value = args.date if site["kind"] == "date" else args.version
        if value is None:
            print(f"left    {site['path']} /{site['pattern']}/ (no --version given)")
            continue

        def _swap(match, value=value):
            start, end = match.span(1)
            whole = match.group(0)
            offset = match.start(0)
            return whole[: start - offset] + value + whole[end - offset :]

        texts[path] = pattern.sub(_swap, texts[path])
        print(f"{'set' if args.apply else 'would set'} {site['path']} /{site['pattern']}/ x{found} -> {value}")
    if ok and args.apply:
        for path, text in texts.items():
            path.write_text(text, encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
