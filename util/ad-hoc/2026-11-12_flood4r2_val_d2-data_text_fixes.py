#!/usr/bin/env python3
"""
Check and package a validator's exact text fixes: every ``old`` must occur exactly once in its target, in the order
the fixes are applied; the fixed copies and a unified diff per repository file are written beside the list.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 7: validating the d2-unrun-tests carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session7/briefs/VF_validate_data_unrun_tests.txt (deliverable text_fixes.json)

Usage:
  2026-11-12_flood4r2_val_d2-data_text_fixes.py --input <fixes_input.json> --deliverables <dir> --copies <dir>
      --out <text_fixes.json> --fixed <dir> [--diff-base <tree>]

``fixes_input.json`` is a list of ``{"finding", "file", "old", "new"}``. ``file`` is ``DELIVERABLES/<name>`` (read
from --deliverables) or ``COPY/<repo path>`` (read from --copies, the validator's rebuilt copies). Fixes are applied
per file in list order to an in-memory copy; before each one its ``old`` must occur exactly once in that copy, and
``old`` must differ from ``new``. The fixed files go to ``<fixed>/DELIVERABLES/...`` and ``<fixed>/COPY/...``. With
--diff-base, each fixed ``COPY/<repo path>`` is also written as a unified diff against ``<tree>/<repo path>`` (paths
``a/<repo path>`` / ``b/<repo path>``), so it applies with ``patch -p1`` in that tree. Exit 1 on any miss.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    for option in ("input", "deliverables", "copies", "out", "fixed"):
        parser.add_argument(f"--{option}", required=True)
    parser.add_argument("--diff-base")
    ns = parser.parse_args()
    roots = {"DELIVERABLES": Path(ns.deliverables), "COPY": Path(ns.copies)}
    fixes = json.loads(Path(ns.input).read_text(encoding="utf-8"))
    texts: dict[str, str] = {}
    problems = []
    listed = []
    for number, fix in enumerate(fixes, start=1):
        label = fix["file"]
        kind, name = label.split("/", 1)
        if label not in texts:
            texts[label] = (roots[kind] / name).read_text(encoding="utf-8")
        count = texts[label].count(fix["old"])
        if count != 1 or fix["old"] == fix["new"]:
            problems.append(f"fix {number} ({fix['finding']}, {label}): old occurs {count} time(s)" + (" and equals new" if fix["old"] == fix["new"] else ""))
            continue
        texts[label] = texts[label].replace(fix["old"], fix["new"])
        listed.append({"finding": fix["finding"], "file": label, "old": fix["old"], "new": fix["new"]})
    fixed_root = Path(ns.fixed)
    for label, text in texts.items():
        target = fixed_root / label
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        kind, name = label.split("/", 1)
        if kind == "COPY" and ns.diff_base:
            before = (Path(ns.diff_base) / name).read_text(encoding="utf-8").splitlines(keepends=True)
            diff = "".join(difflib.unified_diff(before, text.splitlines(keepends=True), fromfile=f"a/{name}", tofile=f"b/{name}"))
            (fixed_root / (name.replace("/", "__") + ".diff")).write_text(diff, encoding="utf-8")
    Path(ns.out).write_text(json.dumps(listed, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    by_file: dict[str, int] = {}
    for entry in listed:
        by_file[entry["file"]] = by_file.get(entry["file"], 0) + 1
    print(f"{len(listed)} of {len(fixes)} fixes verified (old occurs exactly once at application time)")
    for label, count in sorted(by_file.items()):
        print(f"   {count:2d}  {label}")
    for problem in problems:
        print("PROBLEM:", problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
