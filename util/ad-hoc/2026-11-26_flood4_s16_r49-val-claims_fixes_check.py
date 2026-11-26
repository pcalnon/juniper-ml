#!/usr/bin/env python3
"""
Check the r49 claims lens's fixes.json against carrier r49: each `old` occurs exactly once, and all apply in order.

`file` is repo-relative (resolved under the carrier's final/) or "texts/<name>" (resolved under the carrier's texts/).
Each fix's `old` must occur exactly once in its file as the earlier fixes of the list leave it; the fixes are then
applied in list order to copies written under --out (the carrier is never modified). A repo-relative file is also
checked in the assembled tree on today's main (--assembled), when given. Prints one line per fix and a summary; writes
--report as JSON.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- investigation (flood-4 session 16, carrier r49 claims lens)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 49)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def resolve(carrier: Path, name: str) -> Path:
    return carrier / name if name.startswith("texts/") else carrier / "final" / name


def main() -> int:
    ap = argparse.ArgumentParser(description="check fixes.json against carrier r49")
    ap.add_argument("--fixes", required=True)
    ap.add_argument("--carrier", required=True, help="the carrier directory (holds final/ and texts/)")
    ap.add_argument("--assembled", help="a tree of today's main + the carrier, for repo-relative files")
    ap.add_argument("--out", required=True, help="directory for the patched copies")
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    with open(args.fixes, encoding="utf-8") as fh:
        fixes = json.load(fh)
    carrier, out = Path(args.carrier), Path(args.out)
    current: dict[str, str] = {}
    assembled: dict[str, str] = {}
    rows, problems = [], 0
    for fix in fixes:
        name = fix["file"]
        if name not in current:
            current[name] = resolve(carrier, name).read_text(encoding="utf-8")
            if args.assembled and not name.startswith("texts/"):
                assembled[name] = (Path(args.assembled) / name).read_text(encoding="utf-8")
        count = current[name].count(fix["old"])
        row = {"id": fix["id"], "file": name, "occurrences": count}
        if count == 1:
            current[name] = current[name].replace(fix["old"], fix["new"], 1)
        else:
            problems += 1
        if name in assembled:
            acount = assembled[name].count(fix["old"])
            row["occurrences_in_assembled"] = acount
            if acount == 1:
                assembled[name] = assembled[name].replace(fix["old"], fix["new"], 1)
            else:
                problems += 1
        if fix["old"] == fix["new"]:
            row["error"] = "old == new"
            problems += 1
        rows.append(row)
        print(json.dumps(row), flush=True)
    for name, text in current.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    for name, text in assembled.items():
        target = out / "assembled" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    report = {"fixes": len(fixes), "problems": problems, "rows": rows}
    Path(args.report).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"{len(fixes)} fixes, {problems} problems")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
