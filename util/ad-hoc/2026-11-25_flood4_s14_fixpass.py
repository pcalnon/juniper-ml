#!/usr/bin/env python3
"""
Apply validator fixes ({"id", "file", "old", "new", ...}) to a landing copy, keyed by repo-relative path.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition, session 14: rulings 23, 27 and 28)
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- one-off (the session-14 carriers' fix passes)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8;
         util/ad-hoc/2026-11-25_flood4_s13_r7_fixpass.py (the model; it keys a fix by basename, which cannot tell
         juniper-service-core/CHANGELOG.md from the root CHANGELOG.md)

What it does
------------
--work is a directory laid out like the repository (a copy of a carrier's final/ tree, plus texts/ for the PR texts).
Each fix's "file" is a path relative to --work ("src/tests/conftest.py", "texts/pr_body.txt"); a bare basename is
accepted only when exactly one file under --work has it. The fixes of every --fixes file are applied in order (list
order within a file, files in the order given). A fix applies only when its "old" text occurs exactly once in the file
as it stands at its turn; otherwise it is reported MISSING (0) or AMBIGUOUS (>1) and the file is left unchanged for a
hand merge. --skip drops fixes by id, or by FILE:ID (FILE = the basename of the --fixes file) when two lenses share an
id. --dry-run applies nothing and reports what would happen against the current files. Writes nothing outside --work.
Exit 0 when every fix not skipped applied (or would apply), else 1.

Usage
-----
    python3 util/ad-hoc/2026-11-25_flood4_s14_fixpass.py --work DIR --fixes A.json [B.json ...] [--skip ID ...] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _resolve(work: Path, name: str) -> Path | None:
    candidate = work / name
    if candidate.is_file():
        return candidate
    if "/" in name:
        return None
    hits = [p for p in work.rglob(name) if p.is_file()]
    return hits[0] if len(hits) == 1 else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--fixes", type=Path, nargs="+", required=True)
    parser.add_argument("--skip", nargs="*", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    work = args.work.resolve()
    if not work.is_dir():
        print(f"--work {work} is not a directory", file=sys.stderr)
        return 2
    counts = {"APPLIED": 0, "WOULD": 0, "MISSING": 0, "AMBIGUOUS": 0, "NOFILE": 0, "SKIPPED": 0}
    pending: dict[Path, str] = {}
    for fixes_path in args.fixes:
        with fixes_path.open(encoding="utf-8") as fh:
            fixes = json.load(fh)
        tag = fixes_path.name
        for fix in fixes:
            fid = str(fix.get("id"))
            if fid in args.skip or f"{tag}:{fid}" in args.skip:
                counts["SKIPPED"] += 1
                print(f"SKIPPED   {tag}:{fid}")
                continue
            target = _resolve(work, str(fix.get("file", "")))
            if target is None:
                counts["NOFILE"] += 1
                print(f"NOFILE    {tag}:{fid} {fix.get('file')}")
                continue
            text = pending.get(target)
            if text is None:
                text = target.read_text(encoding="utf-8")
            n = text.count(fix["old"])
            rel = target.relative_to(work)
            if n == 1:
                text = text.replace(fix["old"], fix["new"], 1)
                pending[target] = text
                verdict = "WOULD" if args.dry_run else "APPLIED"
            else:
                verdict = "MISSING" if n == 0 else "AMBIGUOUS"
            counts[verdict] += 1
            print(f"{verdict:<9} {tag}:{fid:<6} {rel}  {str(fix.get('why', ''))[:80]}")
    if not args.dry_run:
        for target, text in pending.items():
            target.write_text(text, encoding="utf-8")
    print("summary: " + ", ".join(f"{k} {v}" for k, v in counts.items() if v))
    bad = counts["MISSING"] + counts["AMBIGUOUS"] + counts["NOFILE"]
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
