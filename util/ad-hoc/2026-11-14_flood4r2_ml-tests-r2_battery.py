#!/usr/bin/env python3
"""
Put the flood-4 "ml-tests" carrier's suites into main-verify.yml's Regression Battery in ci.yml's order, and check it.

main-verify.yml's battery (its `Run Python regression battery` step) is a hand-kept, PARTIAL mirror of ci.yml's
regression list (the `Run Python regression tests` step). The workflow's SYNC NOTE asks for every suite ci.yml
gains to be mirrored there in the same pull request, and no test compares the two lists. By the owner's ruling of
2026-11-14 ("Add all fifteen"), every one of the carrier's fifteen suites goes into the battery, in ci.yml's order.

The battery lines are written by the wiring tool, util/ad-hoc/2026-11-09_flood4r2_ml-tests_wire.py, from a spec
entry's `mv_after` (the battery line the suite goes after) and `mv_comment`. This tool never edits a workflow. It
derives `mv_after` from the two lists instead of having it typed, and it checks what the wiring tool wrote.

WHY NOT SIMPLY "AFTER THE NEAREST EARLIER SUITE": main's own battery is not wholly in ci.yml's order. A few of its
lines sit among later suites (on 2026-11-14: ci.yml's #60, #225 and #45, each placed where the pull request that
added it put it). After ci.yml's #225, for one, the carrier's guard suites (ci.yml #234-#238) would land between
#67 and #68. So the order is taken from the battery's SPINE, its longest run of lines in ci.yml's order (a longest
increasing subsequence of their ci.yml positions); a line off the spine is an outlier and never an anchor. Walking
ci.yml's list in order, a spec suite goes after the spine line nearest before it in ci.yml (spec suites already
placed count as spine lines), and past any outlier lines right after that one that ci.yml also puts before it, so
that both of its battery neighbours stand on the side of it where ci.yml puts them.

Run it from the root of a juniper-ml tree:

  --derive --spec SPEC --out OUT
      Read ci.yml's list from the working tree (the wiring tool must already have listed the spec's suites there)
      and the battery from HEAD (main's copy, so suites an earlier wiring put into the working tree do not count),
      then write SPEC with `mv_after` set for every entry and `mv_comment` kept ("" when absent). The spec's own
      order is kept and checked: the wiring tool needs each anchor to exist when it reaches the suite.
  --check --spec SPEC
      After the wiring: the workflow parses as YAML, its battery step's `run` script lists the same suites as its
      text, every battery suite exists in the tree, every spec suite is in the battery exactly once, and each one
      stands between battery neighbours that ci.yml puts before and after it. Exit 1 otherwise.
  --report [--spec SPEC]
      Both lists' sizes, the battery's outliers, every adjacent pair of battery lines that ci.yml orders the other
      way, and the battery with each line's ci.yml position.

Exit 0 when everything holds; 1 on a failed check or derivation; 2 on bad input.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, its session-8 fix-up)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_ml-tests_wire.py (writes the lines), util/ad-hoc/2026-11-14_flood4r2_ml-tests-r2_land.py (runs both)
"""

import argparse
import bisect
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

CI = Path(".github/workflows/ci.yml")
MV = Path(".github/workflows/main-verify.yml")
CI_STEP = "      - name: Run Python regression tests"
MV_STEP = "      - name: Run Python regression battery"
MV_STEP_NAME = "Run Python regression battery"
SUITE_LINE = re.compile(r"^          python3 -m unittest -v (tests/test_[A-Za-z0-9_]+\.py)[ \t]*$", re.M)
RUN_LINE = re.compile(r"^python3 -m unittest -v (tests/test_[A-Za-z0-9_]+\.py)[ \t]*$", re.M)


def _step_suites(text: str, step: str, label: str) -> list:
    start = text.find(step)
    if start < 0 or text.find(step, start + 1) >= 0:
        raise SystemExit(f"{label}: the step {step.strip()!r} is not there exactly once")
    nxt = text.find("\n      - name: ", start + len(step))
    return SUITE_LINE.findall(text[start : nxt if nxt >= 0 else len(text)])


def _head(path: Path) -> str:
    done = subprocess.run(["git", "show", f"HEAD:{path.as_posix()}"], capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise SystemExit(f"HEAD:{path.as_posix()} could not be read: {done.stderr.strip()}")
    return done.stdout


def _load_spec(path: str) -> list:
    try:
        spec = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"bad --spec: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    if not isinstance(spec, list) or not spec or not all(isinstance(entry, dict) and "test" in entry for entry in spec):
        print("bad --spec: a list of objects with a `test` key is expected", file=sys.stderr)
        raise SystemExit(2)
    return spec


def spine(battery: list, position: dict) -> list:
    """The battery's longest run of lines in ci.yml's order (as battery indices); a line ci.yml lacks is never on it."""
    usable = [index for index, suite in enumerate(battery) if suite in position]
    best, back = {}, {}
    for at, index in enumerate(usable):
        best[index], back[index] = 1, None
        for earlier in usable[:at]:
            if position[battery[earlier]] < position[battery[index]] and best[earlier] + 1 > best[index]:
                best[index], back[index] = best[earlier] + 1, earlier
    if not best:
        return []
    index = max(usable, key=lambda candidate: (best[candidate], -candidate))
    chain = []
    while index is not None:
        chain.append(index)
        index = back[index]
    return chain[::-1]


def derive(spec: list, ci_list: list, main_battery: list) -> tuple:
    position = {suite: index for index, suite in enumerate(ci_list)}
    wanted = {entry["test"] for entry in spec}
    absent = sorted(wanted - set(position))
    if absent:
        raise SystemExit(f"ci.yml does not list {absent}: run the wiring tool on ci.yml first")
    already = sorted(wanted & set(main_battery))
    if already:
        raise SystemExit(f"HEAD's battery already lists {already}: derive from a HEAD without them")
    battery = list(main_battery)
    on_spine = {battery[index] for index in spine(battery, position)}
    outliers = [suite for suite in battery if suite not in on_spine]
    spine_positions = sorted(position[suite] for suite in on_spine)
    anchor = {}
    for suite in ci_list:
        if suite not in wanted:
            continue
        here = position[suite]
        nearest = bisect.bisect_left(spine_positions, here)
        if nearest == 0:
            raise SystemExit(f"{suite}: no battery line comes before it in ci.yml's order; place it by hand")
        before = ci_list[spine_positions[nearest - 1]]
        at = battery.index(before) + 1
        while at < len(battery) and battery[at] not in on_spine and position.get(battery[at], len(ci_list)) < here:
            at += 1
        anchor[suite] = battery[at - 1]
        battery.insert(at, suite)
        on_spine.add(suite)
        bisect.insort(spine_positions, here)
    placed, out = set(main_battery), []
    for entry in spec:
        if anchor[entry["test"]] not in placed:
            raise SystemExit(f"{entry['test']}: its anchor {anchor[entry['test']]} comes later in the spec; reorder the spec")
        placed.add(entry["test"])
        out.append({**entry, "mv_after": anchor[entry["test"]], "mv_comment": entry.get("mv_comment", "")})
    return out, outliers, battery


def check(spec: list, ci_list: list, battery: list, mv_text: str) -> list:
    problems = []
    try:
        steps = yaml.safe_load(mv_text)["jobs"]["battery"]["steps"]
        runs = [step.get("run", "") for step in steps if step.get("name") == MV_STEP_NAME]
    except (yaml.YAMLError, KeyError, TypeError) as exc:
        return [f"main-verify.yml: does not parse to a battery job with steps: {exc}"]
    if len(runs) != 1:
        problems.append(f"main-verify.yml: {len(runs)} parsed steps named {MV_STEP_NAME!r}")
    elif RUN_LINE.findall(runs[0]) != battery:
        problems.append("main-verify.yml: the parsed battery script and the text list differ")
    problems += [f"{suite}: a battery line names a file this tree lacks" for suite in battery if not Path(suite).is_file()]
    position = {suite: index for index, suite in enumerate(ci_list)}
    for entry in spec:
        suite = entry["test"]
        where = [index for index, name in enumerate(battery) if name == suite]
        if len(where) != 1:
            problems.append(f"{suite}: in the battery {len(where)} times")
            continue
        if suite not in position:
            problems.append(f"{suite}: not in ci.yml's list")
            continue
        index = where[0]
        for neighbour, earlier in ((battery[index - 1] if index > 0 else None, True), (battery[index + 1] if index + 1 < len(battery) else None, False)):
            if neighbour is None:
                continue
            if neighbour not in position:
                problems.append(f"{suite}: its battery neighbour {neighbour} is not in ci.yml's list")
            elif (position[neighbour] < position[suite]) != earlier:
                problems.append(f"{suite} (ci.yml #{position[suite] + 1}): its battery neighbour {neighbour} (ci.yml #{position[neighbour] + 1}) is on the wrong side")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--derive", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--report", action="store_true")
    ap.add_argument("--spec")
    ap.add_argument("--out")
    args = ap.parse_args()
    if (args.derive or args.check) and not args.spec:
        ap.error("--derive and --check need --spec")
    if args.derive and not args.out:
        ap.error("--derive needs --out")
    ci_list = _step_suites(CI.read_text(encoding="utf-8"), CI_STEP, "ci.yml")
    mv_text = MV.read_text(encoding="utf-8")
    battery = _step_suites(mv_text, MV_STEP, "main-verify.yml")
    spec = _load_spec(args.spec) if args.spec else []
    position = {suite: index for index, suite in enumerate(ci_list)}
    if args.derive:
        derived, outliers, planned = derive(spec, ci_list, _step_suites(_head(MV), MV_STEP, "HEAD's main-verify.yml"))
        Path(args.out).write_text(json.dumps(derived, indent=1) + "\n", encoding="utf-8")
        for entry in derived:
            print(f"{entry['test']} (ci.yml #{position[entry['test']] + 1}): after {entry['mv_after']} (ci.yml #{position[entry['mv_after']] + 1})")
        print(f"HEAD's battery: {len(planned) - len(derived)} lines, outliers off its ci.yml-ordered spine: " + (", ".join(f"{suite} (ci.yml #{position[suite] + 1})" if suite in position else suite for suite in outliers) or "none"))
        print(f"the battery after the wiring: {len(planned)} lines")
        return 0
    if args.check:
        problems = check(spec, ci_list, battery, mv_text)
        print("\n".join(problems) if problems else f"battery: parses; {len(battery)} lines, every one an existing file; all {len(spec)} spec suites present once, each between neighbours in ci.yml's order ({len(ci_list)} suites in ci.yml)")
        return 1 if problems else 0
    on_spine = {battery[index] for index in spine(battery, position)}
    pairs = [f"{a} (ci.yml #{position[a] + 1}) is above {b} (ci.yml #{position[b] + 1})" for a, b in zip(battery, battery[1:]) if a in position and b in position and position[a] > position[b]]
    report = {
        "ci_suites": len(ci_list),
        "battery_suites": len(battery),
        "battery_repeats": sorted({suite for suite in battery if battery.count(suite) > 1}),
        "battery_suites_ci_lacks": [suite for suite in battery if suite not in position],
        "battery_outliers_off_the_spine": [suite for suite in battery if suite not in on_spine],
        "battery_pairs_out_of_ci_order": pairs,
        "spec_suites": [{"test": entry["test"], "ci_number": position[entry["test"]] + 1 if entry["test"] in position else None, "battery_number": battery.index(entry["test"]) + 1 if entry["test"] in battery else None} for entry in spec],
        "battery_with_ci_numbers": [f"{index + 1:>3} {suite} (ci.yml #{position[suite] + 1 if suite in position else '-'})" for index, suite in enumerate(battery)],
    }
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
