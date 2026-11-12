#!/usr/bin/env python3
"""
Assemble manifest.json for the juniper-data unit-mark fix from the tree and the run results.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4, owner ruling 17: "data: 44 unrun tests")
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (the deliverable manifest for the orchestrator's validation and landing)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 17 is recorded in the record-update PR)

Reads, from --out: collect/compare_before_after.json, result_*.json, mutants.json, mutants_main_lane.json (if
present), checks_extra.json (hand-recorded checks: pre-commit, prescreen, G-PATH) and open_questions.json. File
status comes from ``git status --porcelain`` in the worktree; each changed file is hashed. Writes <out>/manifest.json.

Usage:
    python3 <this> --worktree <juniper-data worktree> --out <dir> --base-sha <sha>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed argv: git status in the named worktree
import sys
from pathlib import Path

STATUS = {"M": "modified", "A": "added", "D": "deleted", "?": "added"}


def _load(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--base-sha", required=True)
    args = ap.parse_args()
    wt, out = args.worktree.resolve(), args.out.resolve()
    porcelain = subprocess.run(["git", "-C", str(wt), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout  # nosec B603 B607
    files = []
    for line in porcelain.splitlines():
        code, rel = line[:2].strip() or "?", line[3:]
        with open(wt / rel, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        files.append({"path": rel, "status": STATUS.get(code[0], code), "sha256": digest})

    checks = []
    cmp_ = _load(out / "collect" / "compare_before_after.json")
    unit = cmp_["per_selection"]["unit"]
    others = {k: v["delta"] for k, v in cmp_["per_selection"].items() if k != "unit"}
    checks.append({
        "what": f"collect-only per CI lane, before vs after: unit {unit['a']} -> {unit['b']} (delta {unit['delta']}); added == the {len(unit['added'])} previously deselected test_security.py nodes: {cmp_['unit_added_equals_a_unselected_security_nodes']}; removed {len(unit['removed'])}; other selections' deltas {others}",
        "command": "python3 util/ad-hoc/2026-11-09_flood4r2_r17-data_collect.py --worktree <wt> --out <out>/collect --tag before|after; --compare before after",
        "result": "pass" if cmp_["unit_added_equals_a_unselected_security_nodes"] and not unit["removed"] and unit["delta"] == 44 and not any(others.values()) else "fail",
        "log": str(out / "collect" / "compare_before_after.json"),
    })
    for res_path in sorted(out.glob("result_*.json")):
        res = _load(res_path)
        if res["mode"] == "repeat":
            what = f"repeat x{res['runs_total']} (<=4 concurrent) of the 44 under the unit lane's -m/--timeout, -p no:randomly, {res['python']}: {res['runs_all_passed']}/{res['runs_total']} exit 0; summaries {res['distinct_summaries']}"
            ok = res["runs_all_passed"] == res["runs_total"] and set(res["distinct_summaries"]) <= {"44 passed", "<no summary line>"}
        elif res["mode"] == "lane":
            gate = res["coverage_gate"]
            what = f"CI unit-lane command verbatim (reports redirected) on the fixed tree, {res['python']}: {res['summary']}; aggregate coverage gate exit {gate['exit']} ({gate['total_line'].split()[-1]})"
            ok = res["exit"] == 0 and gate["exit"] == 0
        else:
            what = f"{res['mode']} ({'the 44 newly selected' if res['mode'] == 'new44' else 'all of test_security.py'}) under the unit lane's -m/--timeout, {res['python']}: {res['summary']}"
            ok = res["exit"] == 0
        if res["mode"] == "repeat" and res["distinct_summaries"] == ["<no summary line>"]:
            what += " (first attempt: every run exited 0 and printed 44 dots, but a doubled -q suppressed pytest's summary line; the _v2 run repeats it with the line)"
        checks.append({"what": what, "command": f"python3 util/ad-hoc/2026-11-09_flood4r2_r17-data_run_lane.py --mode {res['mode']} --tag {res['tag']}", "result": "pass" if ok else "fail", "log": res.get("log", str(res_path))})
    extra = out / "checks_extra.json"
    if extra.exists():
        checks.extend(_load(extra))

    mutations = []
    main_lane = {}
    if (out / "mutants_main_lane.json").exists():
        main_lane = {m["id"]: m for m in _load(out / "mutants_main_lane.json")}
    for m in _load(out / "mutants.json"):
        ml = main_lane.get(m["id"])
        entry = {
            "test_file": "juniper_data/tests/unit/test_security.py (the four newly marked classes)",
            "mutant": f"{m['file']}:{m['line']}, {m['what']}: `{m['old']}` -> `{m['new']}`",
            "result": "killed" if m["killed_by_new44"] else "survived",
            "detail": f"{m['new44']['summary']}; failed: {m['new44']['failed']}; restored byte-for-byte: {m['restored_byte_for_byte']} (sha256 {m['sha256_before']})",
            "log": m["new44"]["log"],
        }
        if ml:
            lane = ml["main_selection_lane"]
            entry["main_selection_lane"] = {
                "what": "CI's whole unit-lane selection as main had it (fixed tree, the four classes --deselect-ed), no coverage",
                "result": "survived (CI's unit lane, as main selected it, could not see this break; other lanes not run)" if ml["survives_main_selection_lane"] else "killed by an already-selected test",
                "summary": lane["summary"],
                "failed": lane["failed"],
                "restored_byte_for_byte": ml["restored_byte_for_byte"],
                "log": lane["log"],
            }
        mutations.append(entry)

    manifest = {
        "repo": "juniper-data",
        "carrier": "r17-data-unit-marks",
        "ruling": "the owner's ruling 17 (2026-11-09, recorded in the record-update PR), option label \"data: 44 unrun tests\"",
        "base_sha": args.base_sha,
        "worktree": str(wt),
        "branch": "fix/test-security-unit-marks",
        "files": files,
        "carried": [],
        "carried_note": "No draft is carried: this is an owner-ruled defect fix on main (found by the round-2 data-tests validation lens, F3).",
        "checks": checks,
        "mutations": mutations,
        "open_questions": _load(out / "open_questions.json") if (out / "open_questions.json").exists() else [],
    }
    dest = out / "manifest.json"
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
        fh.write("\n")
    print(json.dumps({"files": files, "checks": [(c["result"], c["what"][:110]) for c in checks], "mutations": [(x["result"], x.get("main_selection_lane", {}).get("result")) for x in mutations]}, indent=1))
    print(f"wrote {dest}")
    return 0 if all(c["result"] == "pass" for c in checks) and all(x["result"] == "killed" for x in mutations) else 1


if __name__ == "__main__":
    sys.exit(main())
