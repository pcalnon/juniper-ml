"""
Check main-verify.yml's Regression Battery in a landed tree against ci.yml's order, independently of the carrier's tool.

It parses both workflows with PyYAML, takes ci.yml's regression list (job ``tests``, step "Run Python regression
tests") and the battery's (job ``battery``, step "Run Python regression battery") in order, and for the landed tree
and the clean main it reports: every battery line's file on disk; duplicates; the battery lines out of ci.yml's order
(the complement of one longest run in ci.yml's order); which suites the landing added; whether each added suite is
there exactly once, whether the added suites keep ci.yml's order among themselves, and, for each, its battery
neighbours with their ci.yml positions (consistent when prev < it < next). It also syntax-checks the step's script
with ``bash -n`` and reports the shell the step runs under (an explicit ``shell:`` or the job / workflow default).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent L1b, flood-4 session 8)
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --tree <landed tree> --main <clean main tree> --out <json>
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

LINE_RE = re.compile(r"^\s*python3 -m unittest(?: -[A-Za-z]+)* (?P<suite>\S+)\s*$")
WORKFLOWS = Path(".github") / "workflows"


def step(workflow, job, name):
    steps = [item for item in workflow["jobs"][job]["steps"] if item.get("name") == name]
    if len(steps) != 1:
        raise SystemExit("%s/%s: %d steps named %r" % (job, name, len(steps), name))
    return steps[0]


def suites_of(script):
    return [match.group("suite") for match in (LINE_RE.match(line) for line in script.splitlines()) if match]


def longest_in_order(positions):
    """Indices (into positions) of one longest strictly increasing run; patience sort with back-pointers."""
    tails, tails_idx, back = [], [], [None] * len(positions)
    for i, value in enumerate(positions):
        lo, hi = 0, len(tails)
        while lo < hi:
            mid = (lo + hi) // 2
            if tails[mid] < value:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(tails):
            tails.append(value)
            tails_idx.append(i)
        else:
            tails[lo] = value
            tails_idx[lo] = i
        back[i] = tails_idx[lo - 1] if lo > 0 else None
    chain, cursor = [], tails_idx[-1] if tails_idx else None
    while cursor is not None:
        chain.append(cursor)
        cursor = back[cursor]
    return sorted(chain)


def read(tree):
    root = Path(tree)
    ci = yaml.safe_load((root / WORKFLOWS / "ci.yml").read_text(encoding="utf-8"))
    mv_text = (root / WORKFLOWS / "main-verify.yml").read_text(encoding="utf-8")
    mv = yaml.safe_load(mv_text)
    ci_list = suites_of(step(ci, "tests", "Run Python regression tests")["run"])
    battery_step = step(mv, "battery", "Run Python regression battery")
    battery = suites_of(battery_step["run"])
    shell = battery_step.get("shell") or mv["jobs"]["battery"].get("defaults", {}).get("run", {}).get("shell") or (mv.get("defaults") or {}).get("run", {}).get("shell") or "(GitHub default: bash -e {0})"
    syntax = subprocess.run(["bash", "-n"], input=battery_step["run"], capture_output=True, text=True, check=False)
    position = {name: index for index, name in enumerate(ci_list)}
    not_in_ci = [name for name in battery if name not in position]
    in_ci = [name for name in battery if name in position]
    spine = longest_in_order([position[name] for name in in_ci])
    spine_names = {in_ci[i] for i in spine}
    out_of_order = [(battery.index(name) + 1, name) for name in in_ci if name not in spine_names]
    return {
        "ci_list": ci_list,
        "battery": battery,
        "battery_lines": len(battery),
        "battery_duplicates": sorted({name for name in battery if battery.count(name) > 1}),
        "battery_missing_files": [name for name in battery if not (root / name).is_file()],
        "battery_not_in_ci_list": not_in_ci,
        "battery_out_of_ci_order": out_of_order,
        "spine_length": len(spine),
        "step_shell": shell,
        "bash_n_rc": syntax.returncode,
        "bash_n_stderr": syntax.stderr.strip(),
        "position": position,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True)
    parser.add_argument("--main", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    landed, base = read(args.tree), read(args.main)
    added_ci = [name for name in landed["ci_list"] if name not in base["ci_list"]]
    added_battery = [name for name in landed["battery"] if name not in base["battery"]]
    lost_battery = [name for name in base["battery"] if name not in landed["battery"]]
    position = landed["position"]
    rows = []
    for name in added_ci:
        count = landed["battery"].count(name)
        row = {"suite": name, "ci_position": position[name] + 1, "battery_count": count}
        if count == 1:
            index = landed["battery"].index(name)
            prev_name = landed["battery"][index - 1] if index > 0 else None
            next_name = landed["battery"][index + 1] if index + 1 < len(landed["battery"]) else None
            prev_pos = position.get(prev_name, -1) + 1 if prev_name else 0
            next_pos = position.get(next_name, 10**6) + 1 if next_name else 10**6
            row.update({"battery_line": index + 1, "prev": prev_name, "prev_ci_position": prev_pos, "next": next_name, "next_ci_position": next_pos, "locally_in_order": prev_pos < position[name] + 1 < next_pos})
        rows.append(row)
    added_order = [name for name in landed["battery"] if name in added_ci]
    result = {
        "tree": args.tree,
        "main": args.main,
        "ci_list_lines": {"landed": len(landed["ci_list"]), "main": len(base["ci_list"])},
        "ci_added": added_ci,
        "battery_lines": {"landed": landed["battery_lines"], "main": base["battery_lines"]},
        "battery_added": added_battery,
        "battery_lost": lost_battery,
        "added_suites_all_once": all(row["battery_count"] == 1 for row in rows),
        "added_suites_keep_ci_order_among_themselves": [position[name] for name in added_order] == sorted(position[name] for name in added_order),
        "added_rows": rows,
        "landed": {key: value for key, value in landed.items() if key not in ("ci_list", "battery", "position")},
        "main_tree": {key: value for key, value in base.items() if key not in ("ci_list", "battery", "position")},
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print("ci list: main %d -> landed %d (+%d); battery: main %d -> landed %d (+%d, lost %d)" % (len(base["ci_list"]), len(landed["ci_list"]), len(added_ci), base["battery_lines"], landed["battery_lines"], len(added_battery), len(lost_battery)))
    print("added all once: %s; added keep ci order: %s; landed duplicates %s missing %s not-in-ci %s; bash -n rc %s; shell %s" % (result["added_suites_all_once"], result["added_suites_keep_ci_order_among_themselves"], landed["battery_duplicates"], landed["battery_missing_files"], landed["battery_not_in_ci_list"], landed["bash_n_rc"], landed["step_shell"]))
    print("out of ci order: main %s | landed %s (spine main %d, landed %d)" % (base["battery_out_of_ci_order"], landed["battery_out_of_ci_order"], base["spine_length"], landed["spine_length"]))
    for row in rows:
        print("  %-56s ci#%-4s bat#%-3s prev=%s(ci#%s) next=%s(ci#%s) ok=%s" % (row["suite"], row["ci_position"], row.get("battery_line"), (row.get("prev") or "-").replace("tests/", ""), row.get("prev_ci_position"), (row.get("next") or "-").replace("tests/", ""), row.get("next_ci_position"), row.get("locally_in_order")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
