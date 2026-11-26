"""
Compare seam-mutant kill sets between juniper-canopy's main and main + carrier r27 (the masked-seam test): a mutant that
a test kills on main but that test no longer kills on the assembled tree is a seam the carrier's fake hides.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 replacement code lens r27-val-code2; harness util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_mutants.py

Usage:
    python <this file> <out.json> --main <results.json> [<results.json> ...] --assembled <results.json> [...]
        [--proposed <results.json>]
"""

from __future__ import annotations

import json
import sys


def load(paths: list[str]) -> dict:
    merged = {}
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            merged.update(json.load(handle))
    return merged


def main() -> int:
    out, args = sys.argv[1], sys.argv[2:]
    groups, current = {"--main": [], "--assembled": [], "--proposed": []}, None
    for arg in args:
        if arg in groups:
            current = arg
        else:
            groups[current].append(arg)
    main_r, asm_r = load(groups["--main"]), load(groups["--assembled"])
    prop_r = load(groups["--proposed"]) if groups["--proposed"] else {}
    rows, masked = [], []
    for mutant in sorted(set(main_r) | set(asm_r), key=lambda k: int(k.split("-")[0][1:])):
        m, a = main_r.get(mutant, {}), asm_r.get(mutant, {})
        mk, ak = set(m.get("killers", [])), set(a.get("killers", []))
        lost = sorted(mk - ak)  # killed on main by a test that no longer kills it with the carrier
        gained = sorted(ak - mk)
        if lost:
            masked.append(mutant)
        rows.append({"mutant": mutant, "main": m.get("status"), "main_tests": m.get("tests"), "assembled": a.get("status"), "assembled_tests": a.get("tests"), "killers_main": sorted(mk), "killers_assembled": sorted(ak), "killers_lost_with_carrier": lost, "killers_gained_with_carrier": gained, "proposed_tests": prop_r.get(mutant, {}).get("status"), "proposed_killers": [k.split("::")[-1] for k in prop_r.get(mutant, {}).get("killers", [])], "restored_everywhere": all(r.get(mutant, {}).get("restored", True) for r in (main_r, asm_r, prop_r))})
    summary = {"mutants": len(rows), "killed_main": sum(r["main"] == "KILLED" for r in rows), "killed_assembled": sum(r["assembled"] == "KILLED" for r in rows), "masked_by_carrier": masked, "rows": rows}
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1)
    for r in rows:
        print(f"{r['mutant']:45s} main={r['main']:9s} assembled={r['assembled']:9s} lost={len(r['killers_lost_with_carrier'])} gained={len(r['killers_gained_with_carrier'])} proposed={r['proposed_tests']}")
    print(json.dumps({k: summary[k] for k in ("mutants", "killed_main", "killed_assembled", "masked_by_carrier")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
