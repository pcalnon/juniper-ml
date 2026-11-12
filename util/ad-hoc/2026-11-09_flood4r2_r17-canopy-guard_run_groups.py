"""
Run juniper-canopy's CI unit lane as four concurrent census processes, one per probe worktree, and merge them.

Builder helper for the owner's ruling 17 ("canopy: tests hit :8050"). The host was at load ~38 on 16 cores, so
one in-process lane run took ~50 minutes; four groups in four detached probe worktrees (the brief's cap of four
workers) take about a quarter of that. Each group runs in its OWN checkout because the suite rewrites tracked
files (``preserve_metrics_layouts`` backs up and restores ``conf/layouts/metrics_layouts.json`` under a fixed
name), so two processes in one tree would race on them.

Groups, from the base lane's per-file collection counts (``pytest --collect-only -q`` output): every file of the
CI lane's four directories, packed greedily (heaviest first) into the least-loaded of four groups, weighing a
src/tests/unit/frontend/ test 1.5x (measured: ~120 frontend tests/min against ~150 elsewhere on this host), each
group's files then sorted so they run in the lane's own alphabetical order. Together they are exactly the lane.

The children are launched with LD_LIBRARY_PATH REMOVED and LIBTORCH empty in their environment AT EXEC. This
host's shell carries both for a Rust project's libtorch, and torch then loads the wrong libtorch_python.so
("undefined symbol: _PyObject_NextNotImplemented"), failing every torch-importing test at import. Setting them
inside an already-running interpreter is too late: the dynamic linker reads LD_LIBRARY_PATH once, at start.

``--balance-junit <junit xml> ...`` replaces those groups with four balanced by MEASURED time: each lane file's
total test time from an earlier run's junit files, packed greedily (longest first) into the least-loaded group,
each group's files then sorted so they run in the lane's own (alphabetical) order. ``--extra-file`` names a lane
file the earlier run did not have (a new test file); it joins the least-loaded group.

``--sync-from <build worktree> --sync <path> ...`` copies the named repo-relative files into every probe first
(and a path absent from the build worktree is removed from the probes), so the probes carry the build tree.
``--inject`` passes the census's lane-wide mutant through.

Usage:
  python3 <this file> --collect <collect -q output> --probes <wt1> <wt2> <wt3> <wt4> --out-dir <dir> --tag <tag>
      [--sync-from <wt> --sync <relpath> ...] [--inject]

Writes <out-dir>/census_<tag>_g<N>.json and .log per group, and <out-dir>/census_<tag>.json, the merge:
{"tag", "groups": [...exit codes], "collected", "outcomes", "failed", "by_port", "by_test", "popen", "getaddrinfo",
"imported_outside_wt", "injected"}.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 (flood-4 session 4), juniper-canopy unit-lane network guard
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess  # nosec B404 - runs the census helper with the canopy interpreter
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree  # nosec B405 - parses junit files this script's own runs wrote

PYTHON = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
CENSUS = Path(__file__).resolve().with_name("2026-11-09_flood4r2_r17-canopy-guard_census.py")
LANE_ARGS = ["-p", "no:cacheprovider", "-m", "not requires_cascor and not requires_server and not slow", "--timeout=60", "-q"]
LANE_DIRS = ("src/tests/unit/", "src/tests/regression/", "src/tests/contract/", "src/tests/performance/")
FRONTEND_DIR = "src/tests/unit/frontend/"
FRONTEND_WEIGHT = 1.5
# CI's unit step environment (ci.yml "Run Unit Tests with Coverage Gate"); LIBTORCH emptied, see the docstring.
CI_ENV = {"CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0", "LIBTORCH": ""}


def _groups(collect_file: Path) -> list[list[str]]:
    weights: dict[str, float] = {}
    for line in collect_file.read_text(encoding="utf-8").splitlines():
        path, sep, count = line.rpartition(": ")
        if sep and path.startswith(LANE_DIRS) and count.isdigit():
            weights[path] = int(count) * (FRONTEND_WEIGHT if path.startswith(FRONTEND_DIR) else 1.0)
    groups: list[list[str]] = [[], [], [], []]
    loads = [0.0, 0.0, 0.0, 0.0]
    for path, weight in sorted(weights.items(), key=lambda pair: (-pair[1], pair[0])):
        lightest = loads.index(min(loads))
        groups[lightest].append(path)
        loads[lightest] += weight
    print(f"[r17-groups] balanced by weighted test count: {[round(load) for load in loads]}, {[len(group) for group in groups]} files")
    return [sorted(group) for group in groups]


def _child_env() -> dict[str, str]:
    env = {name: value for name, value in os.environ.items() if name not in ("LD_LIBRARY_PATH", "GITHUB_ACTIONS", "GITHUB_STEP_SUMMARY")}
    env.update(CI_ENV)
    return env


def _file_of(classname: str, root: Path) -> str | None:
    """Map a junit classname (``src.tests.unit.test_x.TestY``) to its repo-relative test file."""
    parts = classname.split(".")
    for end in range(len(parts), 0, -1):
        candidate = "/".join(parts[:end]) + ".py"
        if (root / candidate).is_file():
            return candidate
    return None


def _balanced_groups(junit_files: list[Path], root: Path, extra: list[str]) -> list[list[str]]:
    seconds: dict[str, float] = {}
    for junit in junit_files:
        for case in ElementTree.parse(junit).getroot().iter("testcase"):  # nosec B314 - our own pytest output
            path = _file_of(case.get("classname", ""), root)
            if path is not None:
                seconds[path] = seconds.get(path, 0.0) + float(case.get("time", "0") or 0)
    groups: list[list[str]] = [[], [], [], []]
    loads = [0.0, 0.0, 0.0, 0.0]
    for path, cost in sorted(seconds.items(), key=lambda pair: (-pair[1], pair[0])):
        lightest = loads.index(min(loads))
        groups[lightest].append(path)
        loads[lightest] += cost
    for path in extra:
        lightest = loads.index(min(loads))
        groups[lightest].append(path)
    print(f"[r17-groups] balanced by junit time: {[round(load) for load in loads]} s, {[len(group) for group in groups]} files")
    return [sorted(group) for group in groups]


def _sync(source: Path, probes: list[Path], relpaths: list[str]) -> None:
    for relpath in relpaths:
        origin = source / relpath
        for probe in probes:
            target = probe / relpath
            if origin.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origin, target)
            elif target.exists():
                target.unlink()


def _merge(tag: str, records: list[dict], codes: list[int]) -> dict:
    merged: dict = {"tag": tag, "groups": codes, "collected": 0, "injected": 0, "armed": [], "not_armed": [], "outcomes": Counter(), "outcome_by_test": {}, "markers": {}, "failed": [], "by_port": {}, "by_test": {}, "popen": [], "getaddrinfo": {}, "imported_outside_wt": {}}
    for record in records:
        merged["collected"] += record.get("collected", 0)
        merged["injected"] += record.get("injected", 0)
        merged["armed"].extend(record.get("armed", []))
        merged["not_armed"].extend(record.get("not_armed", []))
        merged["outcome_by_test"].update(record.get("outcome_by_test", {}))
        merged["markers"].update(record.get("markers", {}))
        merged["outcomes"].update(record.get("outcomes", {}))
        merged["failed"].extend(record.get("failed", []))
        merged["popen"].extend(record.get("popen", []))
        merged["getaddrinfo"].update(record.get("getaddrinfo", {}))
        merged["imported_outside_wt"].update(record.get("imported_outside_wt", {}))
        merged["by_test"].update(record.get("by_test", {}))
        for port, entry in record.get("by_port", {}).items():
            into = merged["by_port"].setdefault(port, {"connects": 0, "tests": [], "verdicts": Counter(), "hosts": Counter()})
            into["connects"] += entry["connects"]
            into["tests"] = sorted(set(into["tests"]) | set(entry["tests"]))
            into["verdicts"].update(entry["verdicts"])
            into["hosts"].update(entry["hosts"])
    for entry in merged["by_port"].values():
        entry["n_tests"] = len(entry["tests"])
    merged["failed"].sort()
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--collect", required=True, type=Path)
    parser.add_argument("--probes", required=True, nargs=4, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--sync-from", type=Path)
    parser.add_argument("--sync", nargs="*", default=[])
    parser.add_argument("--inject", action="store_true")
    parser.add_argument("--probe-guard", action="store_true")
    parser.add_argument("--balance-junit", nargs="*", default=[], type=Path)
    parser.add_argument("--extra-file", nargs="*", default=[])
    args = parser.parse_args()

    if args.sync_from is not None:
        _sync(args.sync_from, args.probes, args.sync)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    groups = _balanced_groups(args.balance_junit, args.probes[0], args.extra_file) if args.balance_junit else _groups(args.collect)
    with open(args.out_dir / f"groups_{args.tag}.json", "w", encoding="utf-8") as fh:
        json.dump(groups, fh, indent=1)
    procs = []
    for number, (probe, paths) in enumerate(zip(args.probes, groups), start=1):
        out = args.out_dir / f"census_{args.tag}_g{number}.json"
        command = [PYTHON, "-I", str(CENSUS), "--wt", str(probe), "--out", str(out)]
        if args.inject:
            command.append("--inject")
        if args.probe_guard:
            command.append("--probe-guard")
        command += ["--", *LANE_ARGS, f"--junitxml={args.out_dir / f'junit_{args.tag}_g{number}.xml'}", *paths]
        with open(args.out_dir / f"census_{args.tag}_g{number}.log", "w", encoding="utf-8") as log:
            procs.append((out, subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=_child_env())))  # nosec B603 - fixed argv, no shell
    codes, records = [], []
    for out, proc in procs:
        codes.append(proc.wait())
        if out.exists():
            with open(out, encoding="utf-8") as fh:
                records.append(json.load(fh))
    merged = _merge(args.tag, records, codes)
    with open(args.out_dir / f"census_{args.tag}.json", "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=1, default=dict)
    ports = {port: (entry["connects"], entry["n_tests"]) for port, entry in merged["by_port"].items()}
    print(f"[r17-groups] tag={args.tag} exits={codes} collected={merged['collected']} outcomes={dict(merged['outcomes'])} injected={merged['injected']} armed={len(merged['armed'])} not_armed={len(merged['not_armed'])} by_port(connects,tests)={ports} failed={len(merged['failed'])} outside_wt={merged['imported_outside_wt']}")
    return 0 if all(code == 0 for code in codes) else 1


if __name__ == "__main__":
    sys.exit(main())
