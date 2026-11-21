#!/usr/bin/env python3
"""
Collect juniper-data's tests per CI lane (--collect-only) and name, with their marks, the ones no lane selects.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — investigation (the census before the change, each lane's delta after it)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#529 (the precedent);
         adapted from 2026-11-09_flood4r2_r17-data_collect.py

WHAT IT DOES
For one juniper-data tree it runs ``python -m pytest --collect-only`` (no test body runs) once per selection a
juniper-data workflow uses, as of juniper-data main c68e6b4c:

    unit         ci.yml unit-tests          -m "unit and not slow" juniper_data/tests/unit
    integration  ci.yml integration-tests   -m "integration and not slow" juniper_data/tests/integration
    gitleaks     ci.yml security            juniper_data/tests/unit/test_gitleaks_config.py (by path, no -m)
    slow         ci.yml slow-tests          -m "slow"                  (testpaths; schedule / dispatch only)
    scheduled    scheduled-tests.yml        -m "slow or integration"   (testpaths; schedule / dispatch only)
    all          no selection (testpaths): the universe

and one more pass over the universe through a small in-process plugin that records every item's marks (module,
class and function level). The node ids of that pass must equal the universe's, or the run fails. It then writes
<out>/collect_<tag>.json: every node's lanes and marks, the nodes no lane selects grouped by file and class with the
reason (no mark a lane asks for, or a directory no pull-request lane collects), and the nodes only a scheduled lane
selects. ``compare`` diffs two tags per lane.

Usage:
    python3 <this> collect --python <venv interpreter> --worktree <juniper-data tree> --out <dir> --tag <name>
    python3 <this> compare --out <dir> <tagA> <tagB> [--rename <old test file>=<new test file> ...]

The interpreter is a dependency-only venv, so ``juniper_data`` is imported from the tree (a probe records the path).
pytest's own addopts carry one ``-q``, so none is added. ``-p no:cacheprovider`` and ``-B`` keep the tree clean, the
six Sentry DSN variables are set to "" and TMPDIR is left exactly as the session gave it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: a chosen interpreter running pytest --collect-only
import sys
from collections import Counter
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
SELECTIONS: dict[str, list[str]] = {
    "unit": ["-m", "unit and not slow", "juniper_data/tests/unit"],
    "integration": ["-m", "integration and not slow", "juniper_data/tests/integration"],
    "gitleaks": ["juniper_data/tests/unit/test_gitleaks_config.py"],
    "slow": ["-m", "slow"],
    "scheduled": ["-m", "slow or integration"],
    "all": [],
}
LANES = ("unit", "integration", "gitleaks", "slow", "scheduled")
PR_LANES = ("unit", "integration", "gitleaks")
LANE_KIND = {
    "unit": "ci.yml unit-tests: pull_request, push to main/develop, daily schedule, dispatch (CPython 3.12, 3.13, 3.14 on Linux; 3.12 on macOS)",
    "integration": "ci.yml integration-tests: pull_request, or any event on main/develop (CPython 3.14)",
    "gitleaks": "ci.yml security: every event but repository_dispatch (CPython 3.12), one file by path",
    "slow": "ci.yml slow-tests: schedule and workflow_dispatch ONLY (CPython 3.14)",
    "scheduled": "scheduled-tests.yml: schedule and workflow_dispatch ONLY (CPython 3.12, 3.13, 3.14)",
}
SUMMARY_RE = re.compile(r"(\d+(?:/\d+)? tests? collected.*|no tests collected.*)")


def _env() -> dict[str, str]:
    return {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **dict.fromkeys(SENTRY_DSN_NAMES, "")}


def _collect(python: str, worktree: Path, out: Path, tag: str, name: str, sel: list[str]) -> dict:
    argv = [python, "-B", "-m", "pytest", "--collect-only", "-p", "no:cacheprovider", *sel]
    proc = subprocess.run(argv, cwd=worktree, env=_env(), capture_output=True, text=True, check=False)  # nosec B603
    log = out / f"collect_{tag}_{name}.log"
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(f"$ (cwd={worktree}) {' '.join(argv)}\n# exit={proc.returncode}\n\n{proc.stdout}\n--- stderr ---\n{proc.stderr}")
    nodes = sorted({ln.strip() for ln in proc.stdout.splitlines() if ln.startswith("juniper_data/tests/") and "::" in ln})
    tail = [m.group(1) for ln in proc.stdout.splitlines() if (m := SUMMARY_RE.search(ln))]
    return {"argv": argv, "exit": proc.returncode, "count": len(nodes), "summary": tail[-1] if tail else "<none>", "log": str(log), "nodes": nodes}


def _marks(python: str, worktree: Path, out: Path, tag: str) -> dict[str, list[str]]:
    dump = out / f"marks_{tag}.json"
    argv = [python, "-B", str(Path(__file__).resolve()), "inner", str(dump)]
    proc = subprocess.run(argv, cwd=worktree, env=_env(), capture_output=True, text=True, check=False)  # nosec B603
    with open(out / f"marks_{tag}.log", "w", encoding="utf-8") as fh:
        fh.write(f"$ (cwd={worktree}) {' '.join(argv)}\n# exit={proc.returncode}\n\n{proc.stdout}\n--- stderr ---\n{proc.stderr}")
    with open(dump, encoding="utf-8") as fh:
        return json.load(fh)


def inner(dump: str) -> int:
    """Runs under the venv interpreter with cwd = the tree: one universe collection that records every item's marks."""
    sys.path[0] = os.getcwd()  # as ``python -m pytest`` has it; this file's directory must not be importable
    import pytest  # noqa: PLC0415 - only the venv interpreter has it

    rows: dict[str, list[str]] = {}

    class _Dump:
        def pytest_collection_finish(self, session) -> None:  # noqa: ANN001
            for item in session.items:
                rows[item.nodeid] = sorted({mark.name for mark in item.iter_markers()})

    rc = int(pytest.main(["--collect-only", "-p", "no:cacheprovider"], plugins=[_Dump()]))
    with open(dump, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=0, sort_keys=True)
    return rc


def _split(node: str) -> tuple[str, str]:
    parts = node.split("::")
    return parts[0], (parts[1] if len(parts) > 2 else "<module-level functions>")


def _reason(node: str, marks: list[str]) -> str:
    path = node.split("::", 1)[0]
    directory = path.rsplit("/", 1)[0]
    named = ", ".join(m for m in marks if m not in ("parametrize", "usefixtures", "asyncio", "timeout", "filterwarnings", "skipif", "skip", "xfail")) or "none"
    if directory.endswith("tests/unit"):
        return f"in tests/unit without the `unit` mark the unit lane asks for (marks: {named})"
    if directory.endswith("tests/integration"):
        return f"in tests/integration without the `integration` mark both lanes that reach it ask for (marks: {named})"
    return f"in {directory.split('juniper_data/')[-1]}/, a directory no pull-request lane collects, and without `slow` or `integration`, the only marks the testpaths-wide scheduled lanes ask for (marks: {named})"


def collect(python: str, worktree: Path, out: Path, tag: str) -> int:
    out.mkdir(parents=True, exist_ok=True)
    probe = subprocess.run([python, "-B", "-c", "import juniper_data, sys; print(juniper_data.__file__); print(sys.version.split()[0])"], cwd=worktree, env=_env(), capture_output=True, text=True, check=False)  # nosec B603
    where = probe.stdout.strip().splitlines()
    res = {name: _collect(python, worktree, out, tag, name, sel) for name, sel in SELECTIONS.items()}
    sets = {name: set(r["nodes"]) for name, r in res.items()}
    marks = _marks(python, worktree, out, tag)
    marks_match = set(marks) == sets["all"]
    lanes_of = {node: [lane for lane in LANES if node in sets[lane]] for node in sorted(sets["all"])}
    outside = sorted(set().union(*(sets[lane] for lane in LANES)) - sets["all"])
    no_lane = [n for n, lanes in lanes_of.items() if not lanes]
    sched_only = [n for n, lanes in lanes_of.items() if lanes and not set(lanes) & set(PR_LANES)]
    groups: dict[str, dict] = {}
    for node in no_lane:
        path, cls = _split(node)
        key = f"{path}::{cls}"
        entry = groups.setdefault(key, {"file": path, "class": cls, "count": 0, "reasons": Counter()})
        entry["count"] += 1
        entry["reasons"][_reason(node, marks.get(node, []))] += 1
    for entry in groups.values():
        entry["reasons"] = dict(entry["reasons"])
    by_file = Counter(n.split("::", 1)[0] for n in no_lane)
    per_file_all = Counter(n.split("::", 1)[0] for n in sets["all"])
    record = {
        "worktree": str(worktree),
        "tag": tag,
        "interpreter": python,
        "python_version": where[1] if len(where) > 1 else None,
        "juniper_data_from": where[0] if where else None,
        "imported_inside_tree": bool(where) and where[0].startswith(str(worktree) + os.sep),
        "sentry_dsn_names_set_to_empty": list(SENTRY_DSN_NAMES),
        "lane_kinds": LANE_KIND,
        "selections": {name: {k: v for k, v in r.items() if k != "nodes"} for name, r in res.items()},
        "marks_pass_matches_universe": marks_match,
        "lane_nodes_outside_universe": outside,
        "lane_combinations": dict(Counter("+".join(lanes) or "<no lane>" for lanes in lanes_of.values())),
        "no_lane": {"total": len(no_lane), "by_file": {f: {"no_lane": c, "collected": per_file_all[f]} for f, c in sorted(by_file.items())}, "by_class": [groups[k] for k in sorted(groups)]},
        "scheduled_only": {"total": len(sched_only), "by_file": dict(sorted(Counter(n.split("::", 1)[0] for n in sched_only).items())), "by_lanes": dict(Counter("+".join(lanes_of[n]) for n in sched_only))},
        "nodes": {name: r["nodes"] for name, r in res.items()},
        "no_lane_nodes": no_lane,
        "scheduled_only_nodes": sched_only,
        "marks": marks,
    }
    dest = out / f"collect_{tag}.json"
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1)
        fh.write("\n")
    brief = {k: record[k] for k in ("tag", "python_version", "juniper_data_from", "imported_inside_tree", "marks_pass_matches_universe", "lane_nodes_outside_universe", "lane_combinations")}
    brief["selections"] = {n: f"exit={r['exit']} count={r['count']} [{r['summary']}]" for n, r in res.items()}
    brief["no_lane"] = {"total": len(no_lane), "by_file": record["no_lane"]["by_file"]}
    brief["no_lane_by_class"] = {f"{g['file'].split('tests/')[-1]}::{g['class']}": g["count"] for g in record["no_lane"]["by_class"]}
    brief["scheduled_only"] = {k: v for k, v in record["scheduled_only"].items()}
    print(json.dumps(brief, indent=1))
    print(f"wrote {dest}")
    ok = all(r["exit"] == 0 for r in res.values()) and marks_match and not outside and record["imported_inside_tree"]
    return 0 if ok else 1


def compare(out: Path, tag_a: str, tag_b: str, renames: list[str]) -> int:
    with open(out / f"collect_{tag_a}.json", encoding="utf-8") as fh:
        a = json.load(fh)
    with open(out / f"collect_{tag_b}.json", encoding="utf-8") as fh:
        b = json.load(fh)
    # A moved test file keeps its tests and changes their node ids: read tag A's ids under the new path.
    path_map = dict(item.split("=", 1) for item in renames)

    def renamed(node: str) -> str:
        path, sep, rest = node.partition("::")
        return path_map.get(path, path) + sep + rest

    a["nodes"] = {name: [renamed(n) for n in nodes] for name, nodes in a["nodes"].items()}
    a["no_lane_nodes"] = [renamed(n) for n in a["no_lane_nodes"]]
    report: dict = {"a": tag_a, "b": tag_b, "renames_applied_to_a": path_map, "per_selection": {}}
    for name in SELECTIONS:
        sa, sb = set(a["nodes"][name]), set(b["nodes"][name])
        added, removed = sorted(sb - sa), sorted(sa - sb)
        report["per_selection"][name] = {"a": len(sa), "b": len(sb), "delta": len(sb) - len(sa), "added_by_file": dict(sorted(Counter(n.split("::", 1)[0] for n in added).items())), "removed_by_file": dict(sorted(Counter(n.split("::", 1)[0] for n in removed).items())), "added": added, "removed": removed}
    a_no, b_no = set(a["no_lane_nodes"]), set(b["no_lane_nodes"])
    report["no_lane"] = {"a": len(a_no), "b": len(b_no), "left_no_lane": len(a_no - b_no), "entered_no_lane": sorted(b_no - a_no), "still_no_lane_by_file": dict(sorted(Counter(n.split("::", 1)[0] for n in b_no).items()))}
    moved = a_no - b_no
    b_lanes = {lane: set(b["nodes"][lane]) for lane in LANES}
    report["moved_into"] = dict(Counter("+".join(lane for lane in LANES if n in b_lanes[lane]) for n in moved))
    report["moved_by_file"] = {f: dict(Counter("+".join(lane for lane in LANES if n in b_lanes[lane]) for n in moved if n.split("::", 1)[0] == f)) for f in sorted({n.split("::", 1)[0] for n in moved})}
    newly_selected = sorted(set().union(*(set(report["per_selection"][lane]["added"]) for lane in LANES)))
    report["newly_selected_equals_moved"] = set(newly_selected) == moved
    report["newly_selected_not_from_no_lane"] = sorted(set(newly_selected) - moved)
    report["any_lane_lost_a_node"] = {lane: len(report["per_selection"][lane]["removed"]) for lane in LANES if report["per_selection"][lane]["removed"]}
    dest = out / f"compare_{tag_a}_{tag_b}.json"
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    brief = {n: {k: r[k] for k in ("a", "b", "delta", "added_by_file", "removed_by_file")} for n, r in report["per_selection"].items()}
    print(json.dumps(brief, indent=1))
    print(json.dumps({k: report[k] for k in ("no_lane", "moved_into", "moved_by_file", "newly_selected_equals_moved", "newly_selected_not_from_no_lane", "any_lane_lost_a_node")}, indent=1))
    print(f"wrote {dest}")
    return 0 if not report["any_lane_lost_a_node"] and not report["no_lane"]["entered_no_lane"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--python", required=True)
    c.add_argument("--worktree", type=Path, required=True)
    c.add_argument("--out", type=Path, required=True)
    c.add_argument("--tag", required=True)
    d = sub.add_parser("compare")
    d.add_argument("--out", type=Path, required=True)
    d.add_argument("tags", nargs=2)
    d.add_argument("--rename", action="append", default=[], help="<old test file>=<new test file>, applied to the first tag's node ids")
    i = sub.add_parser("inner")
    i.add_argument("dump")
    args = ap.parse_args()
    if args.cmd == "inner":
        return inner(args.dump)
    if args.cmd == "compare":
        return compare(args.out.resolve(), *args.tags, args.rename)
    return collect(args.python, args.worktree.resolve(), args.out.resolve(), args.tag)


if __name__ == "__main__":
    sys.exit(main())
