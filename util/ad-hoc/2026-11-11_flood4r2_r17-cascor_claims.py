#!/usr/bin/env python3
"""
Check the numbers juniper-cascor's stop-then-start texts quote against the result files they come from.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt rule 14 (never claim a check you did not run) and
         DELIVERABLES (no attribution footer, no trailers, no CI-skip marker, every #N exists)

Reads the lane, mutant and stress JSON files and the two reproducer logs, derives the figures a
text may quote (passed counts, coverage, the new tests' failures on main, mutants caught, stress
totals, exit codes), and requires each text to quote every figure listed for it. A figure is
matched as written here, with or without a thousands comma. It also refuses, in every text: a
leftover ``PLACEHOLDER``, a CI-skip marker, an attribution footer or trailer, and a ``#<number>``
that is not in ``--known-pr`` (the pull requests the caller has checked exist).

Usage:
  2026-11-11_flood4r2_r17-cascor_claims.py --scratch <dir with the result files> --text <file> [--text ...] --known-pr 753 [--known-pr ...]
Exit: 0 when every text quotes every figure and holds nothing refused; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_MARKERS = ("[skip ci]", "[ci skip]", "[no ci]", "[skip actions]", "[actions skip]", "skip-checks:")
FOOTERS = ("Generated with", "Co-Authored-By", "Claude-Session", "claude.ai/code")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _percent(total_line: str) -> str:
    return total_line.split()[-1]


def _facts(scratch: Path) -> dict:
    unit_main = _load(scratch / "lanes/unit-main-9f632eac.json")
    unit_fix = _load(scratch / "lanes-unit-fix-final/unit-carrier-final.json")
    int_main = _load(scratch / "lanes-int-main/integration-main-9f632eac.json")
    int_fix = _load(scratch / "lanes-int-fix/integration-fix-on-9f632eac.json")
    mutants = _load(scratch / "mutants-all-final/mutants.json")["results"]
    by_id = {result["id"]: result for result in mutants}
    fix = [result for result in mutants if result["group"] == "fix" and not result["id"].startswith("control")]
    extended = [result for result in mutants if result["id"].endswith("-extended") and not result["id"].startswith("control")]
    alone = [result for result in mutants if result["id"].endswith("-n1-alone") and not result["id"].startswith("control")]
    stress = [_load(scratch / f"stress/stress-{label}.json") for label in ("default", "switch-1e-6")]
    repro = {name: (scratch / name).read_text(encoding="utf-8") for name in ("repro_on_main_9f632eac.log", "repro_on_fix.log")}
    return {
        "unit_main_passed": unit_main["counts"]["passed"],
        "unit_fix_passed": unit_fix["counts"]["passed"],
        "unit_more": unit_fix["counts"]["passed"] - unit_main["counts"]["passed"],
        "unit_failed_both": (unit_main["counts"]["failures"], unit_fix["counts"]["failures"], unit_main["failing"] == unit_fix["failing"]),
        "coverage_main": _percent(unit_main["coverage_total_line"]),
        "coverage_fix": _percent(unit_fix["coverage_total_line"]),
        "coverage_gates": (unit_main["coverage_gate_exit"], unit_fix["coverage_gate_exit"]),
        "integration": (int_main["counts"]["passed"], int_fix["counts"]["passed"], int_main["counts"]["failures"] + int_fix["counts"]["failures"]),
        "new_tests": by_id["control-new"]["tests"],
        "new_tests_failing_on_main": len(by_id["main-new-tests"]["failed"]),
        "fix_mutants": len(fix),
        "fix_mutants_caught": sum(1 for result in fix if result["verdict"] == "CAUGHT"),
        "n1_mutants": len(extended),
        "n1_caught_extended": sum(1 for result in extended if result["verdict"] == "CAUGHT"),
        "n1_caught_alone": sum(1 for result in alone if result["verdict"] == "CAUGHT"),
        "n1_survivors_alone": sorted(result["id"].split("-")[0] for result in alone if result["verdict"] != "CAUGHT"),
        "controls_green": all(result["verdict"] == "GREEN" for result in mutants if result["id"].startswith("control")),
        "stress": [(run["label"], run["tests"], len(run["failed"]), run["exit"], run["reported_interval"]) for run in stress],
        "repro_exit_main": "main exit=1" in repro["repro_on_main_9f632eac.log"],
        "repro_exit_fix": "fix exit=0" in repro["repro_on_fix.log"],
    }


def _quoted(text: str, figure: object) -> bool:
    plain = str(figure)
    forms = {plain}
    if plain.isdigit() and len(plain) > 3:
        forms.add(f"{int(plain):,}")
    return any(re.search(rf"(?<![\d.,]){re.escape(form)}(?![\d])", text) for form in forms)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--text", required=True, type=Path, action="append")
    parser.add_argument("--known-pr", action="append", default=[])
    args = parser.parse_args()
    facts = _facts(args.scratch.resolve())
    print(json.dumps(facts, indent=2))
    sound = facts["controls_green"] and facts["repro_exit_main"] and facts["repro_exit_fix"] and facts["fix_mutants_caught"] == facts["fix_mutants"] and facts["n1_caught_extended"] == facts["n1_mutants"] and facts["unit_failed_both"] == (1, 1, True) and facts["coverage_gates"] == (0, 0) and facts["integration"][2] == 0 and all(run[2] == 0 and run[3] == 0 for run in facts["stress"])
    problems = [] if sound else ["a result the texts rely on does not hold (see the facts above)"]
    full = [facts["unit_fix_passed"], facts["unit_more"], facts["coverage_fix"], facts["integration"][0], facts["new_tests"], facts["new_tests_failing_on_main"], facts["n1_mutants"], facts["n1_caught_alone"], facts["stress"][0][1]]
    figures = {
        "changelog_entry.txt": full,
        "pr_body.txt": full + [facts["unit_main_passed"], facts["coverage_main"], facts["fix_mutants"], *facts["n1_survivors_alone"]],
        "commit_body.txt": [facts["new_tests"], facts["new_tests_failing_on_main"]],
    }
    for path in args.text:
        text = path.read_text(encoding="utf-8")
        for figure in figures.get(path.name, []):
            if not _quoted(text, figure):
                problems.append(f"{path.name}: does not quote {figure!r}")
        if "PLACEHOLDER" in text or re.search(r"\b[A-Z][A-Z_]*_RESULT\b", text):
            problems.append(f"{path.name}: a placeholder is left")
        for marker in SKIP_MARKERS + FOOTERS:
            if marker.lower() in text.lower():
                problems.append(f"{path.name}: holds {marker!r}")
        unknown = sorted({number for number in re.findall(r"#(\d+)\b", text) if number not in args.known_pr})
        if unknown:
            problems.append(f"{path.name}: names pull requests not in --known-pr: {unknown}")
        print(f"{path.name}: {len(figures.get(path.name, []))} figures required; pull requests named: {sorted(set(re.findall(r'#(\d+)', text)))}")
    for problem in problems:
        print(f"FAIL: {problem}")
    print("ok: every text quotes its figures and holds nothing refused" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
