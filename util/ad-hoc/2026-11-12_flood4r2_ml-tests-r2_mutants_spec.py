#!/usr/bin/env python3
"""
Build round 2's mutant spec for the flood-4 "ml-tests" carrier: round 1's 34 mutants, re-pointed, plus the new ones.

Round 1 recorded one-line mutants of the code each carried test file pins. Main has since changed three of the
mutated files (juniper-ml#2554: the agent guard, the launchers, predict_merge), so each `old` string is counted
in today's target first: a string that no longer occurs exactly once is REPORTED and its mutant is replaced by
the entry in REDERIVED below (same intent, today's line), never silently dropped.

Added for round 2 (one per test changed, as the round's brief asks):
  * the two parser tests of tests/test_pyproject_extras.py whose fixtures became non-live (finding F6 of the
    ml-propose validation): each still fails on the mutant it was written for, a parser that keeps the extras
    marker, and a parser that hands an older row's cells to the current series;
  * tests/test_ci_host_tooling_macos.py: an agent-guard suite dropped from HOST_TOOLING_SUITES fails both the
    list pin and the new on-disk comparison; a guard suite dropped from the Linux regression step fails the
    "also runs on Linux" pin;
  * the current-series row's juniper-observability cell put back to the floor before juniper-ml#2555.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_mutants_spec.py --round1 <mutants.json>
        --control-root <clean-main worktree> --out <mutants.json>

Exit 0 when every mutant's `old` string occurs exactly once in its target; 1 otherwise (nothing usable is written).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_ml-tests_mutation_check.py (the runner this spec feeds)
"""

import argparse
import json
import sys
from pathlib import Path

EXTRAS = "tests/test_pyproject_extras.py"
MACOS = "tests/test_ci_host_tooling_macos.py"
CI = ".github/workflows/ci.yml"
# (pr, test_file, old) of a round-1 mutant whose `old` no longer occurs once -> today's line, same intent.
REDERIVED = {
    # juniper-ml#2554 moved the push --signed off-switch into _git_push_requests_signature; the mutant still inverts the membership test.
    (2489, "tests/test_claude_agent_guard_push_signed.py", 'text.split("=", 1)[1].casefold() not in ("false", "no", "off", "0")'): {
        "old": 'return text.partition("=")[2].casefold() not in _PUSH_SIGNED_OFF',
        "new": 'return text.partition("=")[2].casefold() in _PUSH_SIGNED_OFF',
    },
}

ADDED = [
    {
        "pr": 2507,
        "test_file": EXTRAS,
        "target": EXTRAS,
        "old": 'r"^(?P<pkg>juniper-[a-z0-9-]+)(?:\\[[^\\]]*\\])?(?P<spec>>=.+)$"',
        "new": 'r"^(?P<pkg>juniper-[a-z0-9-]+(?:\\[[^\\]]*\\])?)(?P<spec>>=.+)$"',
        "names": ["test_spec_drops_the_extras_marker"],
        "why": "F6: the parser keeps the extras marker in the package name",
    },
    {
        "pr": 2507,
        "test_file": EXTRAS,
        "target": EXTRAS,
        "old": "            rows[cells[0]] = cells\n",
        "new": "            rows[cells[0]] = next(iter(rows.values()), cells)\n",
        "names": ["test_parser_reads_the_current_series_row_not_an_older_one"],
        "why": "F6: the parser hands the oldest row's cells to every later series",
    },
    {
        "pr": 2507,
        "test_file": EXTRAS,
        "target": "docs/REFERENCE.md",
        "old": "| >=0.1.0,<0.2.0     | >=0.4.2               |\n",
        "new": "| >=0.1.0,<0.2.0     | >=0.4.1               |\n",
        "names": ["test_current_series_row_matches_pyproject_floors"],
        "why": "the 0.11.x row's juniper-observability cell put back to the floor before juniper-ml#2555",
    },
    {
        "pr": 0,
        "test_file": MACOS,
        "target": CI,
        "old": "claude_agent_guard_gpgsign_off claude_agent_guard_sign_edges\n",
        "new": "claude_agent_guard_gpgsign_off\n",
        "names": ["test_the_suites_are_the_host_tooling_set_and_exist"],
        "why": "the Overtoad's ruling of 2026-11-12: a guard suite dropped from HOST_TOOLING_SUITES (the list pin)",
    },
    {
        "pr": 0,
        "test_file": MACOS,
        "target": CI,
        "old": "claude_agent_guard_gpgsign_off claude_agent_guard_sign_edges\n",
        "new": "claude_agent_guard_gpgsign_off\n",
        "names": ["test_every_agent_guard_suite_on_disk_is_listed"],
        "why": "the Overtoad's ruling of 2026-11-12: a guard suite dropped from HOST_TOOLING_SUITES (the on-disk comparison)",
    },
    {
        "pr": 0,
        "test_file": MACOS,
        "target": CI,
        "old": "          python3 -m unittest -v tests/test_claude_agent_guard_nest_depth.py\n",
        "new": "",
        "names": ["test_each_suite_also_runs_in_the_linux_regression_step"],
        "why": "a guard suite of the macOS list dropped from the Linux regression step",
    },
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--round1", required=True)
    ap.add_argument("--control-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with open(args.round1, encoding="utf-8") as fh:
        round1 = json.load(fh)
    spec, problems = [], []
    for index, mutant in enumerate(round1):
        entry = dict(mutant)
        entry["origin"] = f"round 1 #{index:02d}"
        if entry.get("control_root"):
            entry["control_root"] = args.control_root
        text = Path(entry["target"]).read_bytes()
        count = text.count(entry["old"].encode())
        if count != 1:
            key = (entry["pr"], entry["test_file"], entry["old"])
            replacement = REDERIVED.get(key)
            if replacement is None:
                problems.append(f"round 1 #{index:02d} (#{entry['pr']} {entry['test_file']}): old occurs {count} times in {entry['target']}: {entry['old']!r}")
                continue
            entry["round1_old"], entry["round1_new"] = entry["old"], entry["new"]
            entry.update(replacement)
            entry["origin"] += " (re-derived on today's main)"
            recount = text.count(entry["old"].encode())
            if recount != 1:
                problems.append(f"round 1 #{index:02d} re-derived: old occurs {recount} times in {entry['target']}: {entry['old']!r}")
                continue
        spec.append(entry)
    for mutant in ADDED:
        entry = dict(mutant)
        entry["origin"] = "round 2"
        count = Path(entry["target"]).read_bytes().count(entry["old"].encode())
        if count != 1:
            problems.append(f"round 2 ({entry['why']}): old occurs {count} times in {entry['target']}: {entry['old']!r}")
        spec.append(entry)
    print(f"{len(round1)} round-1 mutants, {len(ADDED)} added, {len(spec)} in the spec")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=2)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
