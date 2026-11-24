"""
Check what the ml-tests carrier's texts say about main-verify.yml's Regression Battery, on a main tree and a landed
tree (claims lens, session 8): the battery's suite list (count, order), each new suite's neighbours, main's lines
out of ci.yml's order (by a longest increasing subsequence), the SYNC NOTE text, and which tests/ files read the
battery's list. Read-only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 disposition, ml-tests carrier validation (claims lens)
"""

import argparse
import json
import re
import sys
from pathlib import Path

RUN = re.compile(r"^\s*python3 -m unittest -v (tests/\S+\.py)\s*$")
CI = ".github/workflows/ci.yml"
MV = ".github/workflows/main-verify.yml"


def suites(path: Path) -> list:
    return [m.group(1) for m in (RUN.match(line) for line in path.read_text().splitlines()) if m]


def ci_regression_list(path: Path) -> list:
    """The suites of ci.yml's regression step: every unittest line between that step's name and the next step."""
    lines = path.read_text().splitlines()
    out = []
    inside = False
    for line in lines:
        if re.match(r"^\s*- name: .*[Rr]egression", line):
            inside = True
            continue
        if inside and re.match(r"^\s*- name: ", line):
            inside = False
        if inside:
            m = RUN.match(line)
            if m:
                out.append(m.group(1))
    return out


def battery(path: Path) -> list:
    lines = path.read_text().splitlines()
    out = []
    inside = False
    for line in lines:
        if re.match(r"^\s*- name: .*[Bb]attery", line):
            inside = True
            continue
        if inside and re.match(r"^\s*- name: ", line):
            inside = False
        if inside:
            m = RUN.match(line)
            if m:
                out.append(m.group(1))
    return out


def lis_outliers(seq: list) -> list:
    """Indices NOT on one longest strictly increasing subsequence of seq."""
    if not seq:
        return []
    n = len(seq)
    best = [1] * n
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if seq[j] < seq[i] and best[j] + 1 > best[i]:
                best[i] = best[j] + 1
                prev[i] = j
    end = max(range(n), key=lambda k: best[k])
    keep = set()
    while end != -1:
        keep.add(end)
        end = prev[end]
    return [i for i in range(n) if i not in keep]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the battery claims.")
    parser.add_argument("--main-tree", required=True, type=Path)
    parser.add_argument("--landed-tree", required=True, type=Path)
    parser.add_argument("--new", action="append", default=[], help="a carried suite path")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report: dict = {}
    for label, tree in (("main", args.main_tree), ("landed", args.landed_tree)):
        ci = ci_regression_list(tree / CI)
        bat = battery(tree / MV)
        pos = {name: i for i, name in enumerate(ci)}
        missing = [name for name in bat if name not in pos]
        seq = [pos[name] for name in bat if name in pos]
        names_in = [name for name in bat if name in pos]
        outliers = [names_in[i] for i in lis_outliers(seq)]
        entry = {
            "ci_list": len(ci),
            "battery": len(bat),
            "battery_unique": len(set(bat)),
            "battery_not_in_ci": missing,
            "out_of_ci_order_by_lis": [(name, pos[name] + 1) for name in outliers],
        }
        if label == "landed":
            neigh = {}
            for name in args.new:
                if name not in bat:
                    neigh[name] = "ABSENT"
                    continue
                k = bat.index(name)
                neigh[name] = {
                    "count": bat.count(name),
                    "after": bat[k - 1] if k else None,
                    "before": bat[k + 1] if k + 1 < len(bat) else None,
                    "ci_pos": pos.get(name, -1) + 1,
                    "after_ci_pos": pos.get(bat[k - 1], -2) + 1 if k else None,
                    "before_ci_pos": pos.get(bat[k + 1], -2) + 1 if k + 1 < len(bat) else None,
                }
            entry["new"] = neigh
            entry["new_in_ci_order"] = [n for n in bat if n in args.new] == [n for n in ci if n in args.new]
        text = (tree / MV).read_text()
        idx = text.find("SYNC NOTE")
        entry["sync_note"] = text[max(0, idx - 200) : idx + 900] if idx >= 0 else None
        report[label] = entry
    readers = []
    for test in sorted((args.landed_tree / "tests").glob("*.py")):
        body = test.read_text(errors="replace")
        if "main-verify.yml" in body or "main_verify" in body:
            hits = [w for w in ("Regression Battery", "battery", "Battery") if w in body]
            readers.append({"file": str(test.relative_to(args.landed_tree)), "names_battery": hits})
    report["tests_naming_main_verify"] = readers
    print(json.dumps(report, indent=1))
    if args.out:
        with args.out.open("w") as handle:
            json.dump(report, handle, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
