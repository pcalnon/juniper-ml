#!/usr/bin/env python3
"""Compare main's and the carrier's proposals, scenario by scenario, for regressions outside docs/REFERENCE.md.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (independent validation of the Cursor flood-4 round-2 "ml-propose" carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507; the ml-propose carrier

Reads the ``proposal_<k>.json`` files the validator's simulator wrote for the two variants of each scenario. For
every edited path it compares the CHANGED LINES (difflib, no context), because the carrier's own CHANGELOG and
REFERENCE differ from main's before any proposal runs. Every path but docs/REFERENCE.md must change identically;
REFERENCE's carrier-only changed lines must all be one of the four release sites (the Version cell, the paragraph
line holding the declares sentence and the clause, a matrix row). It also compares the edit-path order and the
checklist items that do not name docs/REFERENCE.md. Read-only; prints a report and writes ``--json``.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

REF = "docs/REFERENCE.md"
_SITE = re.compile(r"^[+-](\| \*\*Version\*\* |`juniper-ml` \d+\.\d+\.\d+ declares|\| \d+\.\d+\.x )")


def changed(old: str, new: str) -> list:
    return [ln for ln in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0) if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", required=True)
    args = ap.parse_args(argv)
    root = Path(args.out) / "sim"
    report: dict = {}
    problems = 0
    for scen_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for pm in sorted((scen_dir / "main").glob("proposal_*.json")):
            pc = scen_dir / "carrier" / pm.name
            with open(pm, encoding="utf-8") as fh:
                m = json.load(fh)
            with open(pc, encoding="utf-8") as fh:
                c = json.load(fh)
            key = f"{scen_dir.name}/{pm.stem}"
            rec: dict = {"order_main": m["edit_paths"], "order_carrier": c["edit_paths"], "paths_only_in_carrier": sorted(set(c["edit_paths"]) - set(m["edit_paths"])), "paths_only_in_main": sorted(set(m["edit_paths"]) - set(c["edit_paths"])), "non_reference_diffs_differ": [], "reference_extra_lines_not_a_site": [], "reference_main_lines_missing_in_carrier": []}
            for path in sorted(set(m["edits"]) | set(c["edits"])):
                cm = changed(m["edits"][path]["old"], m["edits"][path]["new"]) if path in m["edits"] else []
                cc = changed(c["edits"][path]["old"], c["edits"][path]["new"]) if path in c["edits"] else []
                if path != REF:
                    if cm != cc:
                        rec["non_reference_diffs_differ"].append(path)
                    continue
                main_set, car_set = set(cm), set(cc)
                rec["reference_main_lines_missing_in_carrier"] = [ln[:160] for ln in cm if ln not in car_set]
                rec["reference_extra_lines_not_a_site"] = [ln[:160] for ln in cc if ln not in main_set and not _SITE.match(ln)]
            cl_m = [i for i in m["checklist"] if "docs/REFERENCE.md" not in i]
            cl_c = [i for i in c["checklist"] if "docs/REFERENCE.md" not in i]
            rec["non_reference_checklist_equal"] = cl_m == cl_c
            if not rec["non_reference_checklist_equal"]:
                rec["checklist_diff"] = [ln[:200] for ln in difflib.unified_diff(cl_m, cl_c, lineterm="", n=0)]
            rec["order_same_except_reference"] = [p for p in m["edit_paths"] if p != REF] == [p for p in c["edit_paths"] if p != REF]
            bad = rec["paths_only_in_main"] or rec["non_reference_diffs_differ"] or rec["reference_extra_lines_not_a_site"] or rec["reference_main_lines_missing_in_carrier"] or not rec["non_reference_checklist_equal"] or not rec["order_same_except_reference"]
            problems += bool(bad)
            report[key] = rec
            print(f"{key}: {'PROBLEM' if bad else 'ok'}  main={m['edit_paths']}  carrier={c['edit_paths']}")
            if bad:
                print("   ", json.dumps({k: v for k, v in rec.items() if v and k.startswith(('paths_only_in_main', 'non_reference', 'reference_', 'checklist_diff'))})[:1500])
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print("problems:", problems)
    return 0


if __name__ == "__main__":
    sys.exit(main())
