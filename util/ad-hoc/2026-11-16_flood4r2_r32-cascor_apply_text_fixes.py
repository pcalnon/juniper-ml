#!/usr/bin/env python3
"""
Apply a claims lens's text_fixes.json (old -> new pairs) file by file, all or nothing per file.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — one-off (Cursor flood-4 round 2: the r32 pause fix carrier's fix-up)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor#764; the r32 claims lens's text_fixes.json (13 pairs)

For each target file: every ``old`` of that file must occur exactly once before anything is written;
the pairs are then applied in the order given, and after the last one every ``old`` must be gone and
every non-empty ``new`` must occur exactly once. A file whose checks fail is left untouched (the other
files are still written). The sha256 of each file before and after is recorded.

Usage:
  2026-11-16_flood4r2_r32-cascor_apply_text_fixes.py --fixes <text_fixes.json> --log <out.json> [--apply]
Without --apply nothing is written (a dry run that reports what would happen).
Exit: 0 when every file passed its checks; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import OrderedDict
from pathlib import Path


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _apply_file(path: Path, fixes: list) -> dict:
    """Check and apply one file's pairs; return the report (the new text under "_text" when all passed)."""
    before = path.read_text(encoding="utf-8")
    report = {"file": str(path), "sha256_before": _sha256(before), "fixes": [], "ok": True}
    for fix in fixes:
        count = before.count(fix["old"])
        report["fixes"].append({"id": fix["id"], "old_count_before": count})
        if count != 1:
            report["ok"] = False
    if not report["ok"]:
        return report
    text = before
    for fix in fixes:
        text = text.replace(fix["old"], fix["new"], 1)
    for row, fix in zip(report["fixes"], fixes):
        row["old_count_after"] = text.count(fix["old"])
        row["new_count_after"] = text.count(fix["new"]) if fix["new"] else None
        if row["old_count_after"] != 0 or (fix["new"] and row["new_count_after"] != 1):
            report["ok"] = False
    report["sha256_after"] = _sha256(text)
    if report["ok"]:
        report["_text"] = text
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--fixes", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.fixes.read_text(encoding="utf-8"))
    by_file: "OrderedDict[str, list]" = OrderedDict()
    for fix in data["fixes"]:
        by_file.setdefault(fix["file"], []).append(fix)
    reports = []
    all_ok = True
    for name, fixes in by_file.items():
        report = _apply_file(Path(name), fixes)
        text = report.pop("_text", None)
        if report["ok"] and args.apply and text is not None:
            Path(name).write_text(text, encoding="utf-8")
            report["written"] = True
        else:
            report["written"] = False
        all_ok = all_ok and report["ok"]
        reports.append(report)
        print(json.dumps({k: report[k] for k in ("file", "ok", "written")}), flush=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)
    args.log.write_text(json.dumps({"applied": args.apply, "all_ok": all_ok, "files": reports}, indent=2) + "\n", encoding="utf-8")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
