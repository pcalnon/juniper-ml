#!/usr/bin/env python3
"""
Check the numbers juniper-cascor's stop-then-start texts quote (second pass) against the result files they come from.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start", carrier round 2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt rule 14 (never claim a check you did not run) and
         DELIVERABLES (no attribution footer, no trailers, no CI-skip marker, every #N exists);
         a copy of util/ad-hoc/2026-11-11_flood4r2_r17-cascor_claims.py (kept as it ran) for the
         second pass's result files, with the paused-fit mutation check's three logs read too
         and four more refusals (below)

Reads the lane, mutant and stress JSON files, the two reproducer logs and the three logs of
juniper-cascor's ``util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py`` (as shipped on the
carrier, with the detector change on the carrier, as shipped on main), derives the figures a text
may quote, and requires each text to quote every figure listed for it. A figure is matched as
written here, with or without a thousands comma.

It also refuses, in every text: a leftover ``PLACEHOLDER``; a CI-skip marker; an attribution
footer or trailer; a ``#<number>`` that is not in ``--known-pr``; the words of a promised later
fix; words that give the fix's design to the Overtoad; and any sha in ``--stale`` (a base the
numbers are no longer measured on). These last three are word lists, so they are tripwires and
not a reading of the text.

Usage:
  2026-11-12_flood4r2_r17-cascor_claims.py --scratch <the r2 result dir> --unit-carrier <lane json> --text <file> [--text ...]
      --known-pr 753 [--known-pr ...] [--stale 9f632ea ...]
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
PROMISES = r"follow-up|follow up|followup|its own change|a change of its own is|separate change|will be fixed|to be fixed|later fix|fixed later|a later pr|future pr|next pr\b|is planned|are planned"
OWNER_DESIGN = r"Overtoad (chose|approved|picked|selected|accepted|endorsed|preferred)|approved by the Overtoad|chosen by the Overtoad|the Overtoad's (design|choice)|ruling 17 (chose|names the|picked|selected|approved)"
N1_VERDICT = re.compile(r"^(\d+)/(\d+) mutations caught, (\d+) not caught\.$", re.MULTILINE)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _percent(total_line: str) -> str:
    return total_line.split()[-1]


def _n1(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    verdict = N1_VERDICT.search(text)
    exits = re.findall(r"^exit=(\d+)$", text, re.MULTILINE)
    return {
        "caught": int(verdict.group(1)) if verdict else None,
        "of": int(verdict.group(2)) if verdict else None,
        "exit": int(exits[-1]) if exits else None,
        "survivors": re.findall(r"^(M\d+) SURVIVED", text, re.MULTILINE),
        "control_green": "CONTROL  exit 0, 0 failed, provenance ok" in text,
    }


def _facts(scratch: Path, unit_carrier: Path) -> dict:
    unit_main = _load(scratch / "lanes-unit-main/unit-main-b9167bdc.json")
    unit_fix = _load(unit_carrier)
    int_main = _load(scratch / "lanes-int-main/integration-main-b9167bdc.json")
    int_fix = _load(scratch / "lanes-int-carrier/integration-carrier-r2.json")
    mutants = _load(scratch / "mutants/mutants.json")["results"]
    by_id = {result["id"]: result for result in mutants}
    fix = [result for result in mutants if result["group"] == "fix" and not result["id"].startswith("control")]
    stress = [_load(scratch / f"stress/stress-{label}.json") for label in ("default", "switch-1e-6")]
    repro = {name: (scratch / name).read_text(encoding="utf-8") for name in ("repro_on_main_b9167bdc.log", "repro_on_carrier.log")}
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
        "controls_green": all(result["verdict"] == "GREEN" for result in mutants if result["id"].startswith("control")),
        "n1_as_shipped_on_carrier": _n1(scratch / "n1_check_as_shipped_on_carrier.log"),
        "n1_with_detector_on_carrier": _n1(scratch / "n1_check_with_detector_on_carrier.log"),
        "n1_as_shipped_on_main": _n1(scratch / "n1_check_as_shipped_on_main.log"),
        "stress": [(run["label"], run["tests"], len(run["failed"]), run["exit"], run["reported_interval"]) for run in stress],
        "repro_exit_main": "main exit=1" in repro["repro_on_main_b9167bdc.log"],
        "repro_exit_fix": "carrier exit=0" in repro["repro_on_carrier.log"],
    }


def _quoted(text: str, figure: object) -> bool:
    plain = str(figure)
    forms = {plain}
    if plain.isdigit() and len(plain) > 3:
        forms.add(f"{int(plain):,}")
    return any(re.search(rf"(?<![\d.,]){re.escape(form)}(?![\d])", text) for form in forms)


def _sound(facts: dict) -> list:
    detector, shipped, control = facts["n1_with_detector_on_carrier"], facts["n1_as_shipped_on_carrier"], facts["n1_as_shipped_on_main"]
    holds = {
        "the mutant campaign's controls are green": facts["controls_green"],
        "the reproducer exits 1 on main and 0 on the carrier": facts["repro_exit_main"] and facts["repro_exit_fix"],
        "every fix mutant is caught": facts["fix_mutants_caught"] == facts["fix_mutants"] and facts["fix_mutants"] > 0,
        "the unit lanes share their one failure": facts["unit_failed_both"] == (1, 1, True),
        "both coverage gates pass": facts["coverage_gates"] == (0, 0),
        "no integration test fails": facts["integration"][2] == 0,
        "both stress runs pass": all(run[2] == 0 and run[3] == 0 for run in facts["stress"]),
        "the paused-fit check with the detector change catches all, exit 0": detector["control_green"] and detector["caught"] == detector["of"] and detector["exit"] == 0 and not detector["survivors"],
        "the paused-fit check as shipped leaves survivors on the carrier, exit 1": shipped["control_green"] and shipped["exit"] == 1 and len(shipped["survivors"]) == shipped["of"] - shipped["caught"] > 0,
        "the paused-fit check as shipped catches all on main, exit 0": control["control_green"] and control["caught"] == control["of"] and control["exit"] == 0,
    }
    return [name for name, ok in holds.items() if not ok]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--unit-carrier", required=True, type=Path, help="the carrier's unit-lane JSON the texts quote")
    parser.add_argument("--text", required=True, type=Path, action="append")
    parser.add_argument("--known-pr", action="append", default=[])
    parser.add_argument("--stale", action="append", default=[], help="a sha no text may still name")
    args = parser.parse_args()
    facts = _facts(args.scratch.resolve(), args.unit_carrier.resolve())
    print(json.dumps(facts, indent=2))
    problems = [f"a result the texts rely on does not hold: {name}" for name in _sound(facts)]
    detector, shipped = facts["n1_with_detector_on_carrier"], facts["n1_as_shipped_on_carrier"]
    n1 = [f"{detector['caught']} of {detector['of']}", f"{shipped['caught']} of {shipped['of']}"]
    full = [facts["unit_fix_passed"], facts["unit_more"], facts["coverage_fix"], facts["integration"][0], facts["new_tests"], facts["new_tests_failing_on_main"], facts["stress"][0][1], *n1]
    figures = {
        "changelog_entry.txt": full,
        "pr_body.txt": full + [facts["unit_main_passed"], facts["coverage_main"], facts["fix_mutants"], *shipped["survivors"]],
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
        for label, pattern in (("a promised later fix", PROMISES), ("the design given to the Overtoad", OWNER_DESIGN)):
            found = sorted({match.group(0).lower() for match in re.finditer(pattern, text, re.IGNORECASE)})
            if found:
                problems.append(f"{path.name}: words of {label}: {found}")
        for sha in args.stale:
            if sha in text:
                problems.append(f"{path.name}: still names {sha}")
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
