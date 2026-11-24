#!/usr/bin/env python3
"""
Census and run of juniper-data's scheduled test lane, its selector read from each tree's OWN workflow file, so a
main tree and a changed tree are each measured by the command that tree would run.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, juniper-data benchmark smoke run)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 session 8: the Overtoad's ruling of 2026-11-14, a daily smoke run of the 41 benchmarks)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_val_d2-data_census.py (a census with the lanes copied in, not read from the
         workflow files; deliberately not imported)

Three verbs. Run them with a venv interpreter that has PyYAML (the venvs of
util/ad-hoc/2026-11-14_flood4r2_r33-data_build_venvs.py do).

  collect --python <venv python> --tree <juniper-data tree> --out <file.json>
      Reads four pytest calls from the tree's workflow files: the scheduled lane (scheduled-tests.yml, job
      slow-or-integration-tests, step "Run slow / integration tests"), and ci.yml's unit lane ("Run Unit Tests"),
      integration lane ("Run Integration Tests (Fast Only)") and slow lane ("Run Slow Tests"). Each is collected with
      its own selection arguments plus `--collect-only -p no:cacheprovider` (addopts supply `-q`); the options that
      only write output (`--junitxml`, `--cov*`) and `--verbose` (which turns -q's node-id list back into a tree)
      are dropped and recorded. Also collected: `-m performance` alone and the whole testpaths (no selector).

  compare --main <file.json> --tree <file.json> --out <file.json> [--new-test <node-id prefix>]
      Scheduled lane, main -> tree: added and lost node ids. Passes when nothing is lost, the added set equals the
      tree's `-m performance` set, and every added node is under juniper_data/tests/performance/. With --new-test:
      which pull-request lanes of the tree select the nodes under that prefix.

  run-step --python <venv python> --tree <juniper-data tree> --label <name> --out-dir <dir> [--workflow-from <tree>]
      Runs the scheduled step's `run:` block exactly as written (read from --workflow-from's workflow, default the
      tree's own) under `bash -e -c`, from the tree's root, with the venv's bin first on PATH. Copies the step's JUnit
      file to <out-dir>/junit_<label>.xml and reports the wall time, the totals, and the performance nodes' count,
      outcomes and summed time.

Every child runs with the six Sentry DSN variables set to the empty string, a dead session bus, and a short list of
token variables removed. TMPDIR is left as the session gave it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess  # nosec B404 - fixed argv: pytest from the caller's venv, and the workflow's own step shell
import sys
import time
import xml.etree.ElementTree as ET  # nosec B405 - parses the JUnit file this helper's own pytest run wrote
from pathlib import Path

import yaml

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
DROPPED_NAMES = ("HF_TOKEN", "PYPI_API_TOKEN", "TEST_PYPI_API_TOKEN", "TWINE_PASSWORD", "GITLEAKS_PARITY_REQUIRED", "PYTEST_ADDOPTS", "VIRTUAL_ENV")
PERF_PREFIX = "juniper_data/tests/performance/"
# lane -> (workflow file, job id, step name, kind)
LANES = {
    "scheduled": ("scheduled-tests.yml", "slow-or-integration-tests", "Run slow / integration tests", "schedule-or-dispatch"),
    "unit": ("ci.yml", "unit-tests", "Run Unit Tests", "pull-request"),
    "integration": ("ci.yml", "integration-tests", "Run Integration Tests (Fast Only)", "pull-request"),
    "slow": ("ci.yml", "slow-tests", "Run Slow Tests", "schedule-or-dispatch"),
}
OUTPUT_ONLY = ("--junitxml", "--cov", "--cov-report", "--verbose", "-v")


def child_env(venv_bin: Path | None = None) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in DROPPED_NAMES}
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/nonexistent/no-session-bus"
    if venv_bin is not None:
        env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '/usr/bin:/bin')}"
    return env


def workflow(tree: Path, name: str) -> dict:
    data = yaml.safe_load((tree / ".github" / "workflows" / name).read_text(encoding="utf-8"))
    if True in data and "on" not in data:
        data["on"] = data.pop(True)
    return data


def step_run(tree: Path, lane: str) -> str:
    name, job, step, _kind = LANES[lane]
    steps = workflow(tree, name)["jobs"][job]["steps"]
    return next(s for s in steps if s.get("name") == step)["run"]


def pytest_argv(run_block: str) -> list[str]:
    """The arguments after `python -m pytest` in a run block (continuation lines joined; exactly one such call)."""
    joined = re.sub(r"\\\n", " ", run_block)
    calls = [shlex.split(line, comments=False) for line in joined.splitlines() if line.strip().startswith("python -m pytest")]
    if len(calls) != 1:
        raise SystemExit(f"expected exactly one `python -m pytest` call, found {len(calls)}")
    words = calls[0][3:]
    for index, word in enumerate(words):
        if word in ("||", "&&", ";", "|"):
            return words[:index]
    return words


def selection_only(argv: list[str]) -> tuple[list[str], list[str]]:
    kept: list[str] = []
    dropped: list[str] = []
    for word in argv:
        if word in OUTPUT_ONLY or any(word.startswith(prefix + "=") for prefix in OUTPUT_ONLY):
            dropped.append(word)
        else:
            kept.append(word)
    return kept, dropped


def collect_args(python: str, tree: Path, args: list[str]) -> dict:
    # No `-q` here: pyproject.toml's addopts already pass `-q`, which makes --collect-only list node ids; a second `-q`
    # would list per-file counts instead.
    argv = [python, "-m", "pytest", *args, "--collect-only", "-p", "no:cacheprovider"]
    started = time.monotonic()
    done = subprocess.run(argv, cwd=tree, env={**child_env(), "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, check=False, timeout=900)  # nosec B603
    nodes = sorted({line for line in done.stdout.splitlines() if line == line.strip() and line.startswith("juniper_data/") and "::" in line})
    summary = [line for line in done.stdout.splitlines() if re.search(r"\d+ (tests? )?(collected|selected|deselected)|no tests", line)]
    return {"argv": argv[1:], "exit": done.returncode, "count": len(nodes), "nodes": nodes, "summary": summary[-1:] if summary else [], "seconds": round(time.monotonic() - started, 2), "stdout_tail": done.stdout[-600:], "stderr_tail": done.stderr[-600:]}


def verb_collect(ns: argparse.Namespace) -> int:
    tree = ns.tree.resolve()
    payload: dict = {"tree": str(tree), "python": ns.python, "lanes": {}}
    for lane in LANES:
        kept, dropped = selection_only(pytest_argv(step_run(tree, lane)))
        row = collect_args(ns.python, tree, kept)
        row.update({"workflow": LANES[lane][0], "job": LANES[lane][1], "step": LANES[lane][2], "kind": LANES[lane][3], "dropped_output_options": dropped})
        payload["lanes"][lane] = row
    payload["lanes"]["performance_only"] = collect_args(ns.python, tree, ["-m", "performance"])
    payload["lanes"]["all"] = collect_args(ns.python, tree, [])
    ns.out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    for lane, row in payload["lanes"].items():
        print(f"{lane:17} exit {row['exit']} count {row['count']:5} {row['summary']} argv {row['argv'][2:]}")
    return 0 if all(row["exit"] == 0 for row in payload["lanes"].values()) else 1


def verb_compare(ns: argparse.Namespace) -> int:
    main = json.loads(ns.main.read_text(encoding="utf-8"))["lanes"]
    tree = json.loads(ns.tree.read_text(encoding="utf-8"))["lanes"]
    before, after = set(main["scheduled"]["nodes"]), set(tree["scheduled"]["nodes"])
    perf = set(tree["performance_only"]["nodes"])
    added, lost = sorted(after - before), sorted(before - after)
    result: dict = {
        "scheduled_argv_main": main["scheduled"]["argv"],
        "scheduled_argv_tree": tree["scheduled"]["argv"],
        "scheduled_count_main": len(before),
        "scheduled_count_tree": len(after),
        "added_count": len(added),
        "lost_count": len(lost),
        "performance_only_count_tree": len(perf),
        "added_equals_performance_only": set(added) == perf,
        "added_all_under_performance_dir": all(node.startswith(PERF_PREFIX) for node in added),
        "performance_nodes_already_in_main_scheduled": sorted(perf & before),
        "all_count_main": main["all"]["count"],
        "all_count_tree": tree["all"]["count"],
        "all_added": sorted(set(tree["all"]["nodes"]) - set(main["all"]["nodes"])),
        "all_lost": sorted(set(main["all"]["nodes"]) - set(tree["all"]["nodes"])),
        "per_lane_counts": {lane: [main[lane]["count"], tree[lane]["count"]] for lane in tree},
        "added": added,
        "lost": lost,
    }
    if ns.new_test:
        new_nodes = sorted(node for node in tree["all"]["nodes"] if node.startswith(ns.new_test))
        result["new_test_nodes"] = new_nodes
        result["new_test_lanes"] = {lane: sorted(set(new_nodes) & set(tree[lane]["nodes"])) == new_nodes and bool(new_nodes) for lane in LANES}
    result["ok"] = bool(not lost and added and result["added_equals_performance_only"] and result["added_all_under_performance_dir"] and not result["performance_nodes_already_in_main_scheduled"])
    ns.out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in ("added", "lost", "all_added", "all_lost", "new_test_nodes")}, indent=1))
    return 0 if result["ok"] else 1


def tally(rows: list[dict]) -> dict[str, int]:
    return {key: sum(1 for row in rows if row["outcome"] == key) for key in ("passed", "failure", "error", "skipped")}


def junit_summary(path: Path) -> dict:
    root = ET.parse(path).getroot()  # nosec B314 - this helper's own pytest output
    cases = []
    for case in root.iter("testcase"):
        outcome = "passed"
        for child in case:
            if child.tag in ("failure", "error", "skipped"):
                outcome = child.tag
        classname = case.get("classname", "")
        cases.append({"classname": classname, "name": case.get("name", ""), "time": float(case.get("time", "0") or 0), "outcome": outcome})
    perf = [case for case in cases if case["classname"].startswith("juniper_data.tests.performance.")]
    return {
        "tests": len(cases),
        "outcomes": tally(cases),
        "performance_tests": len(perf),
        "performance_outcomes": tally(perf),
        "performance_seconds_sum": round(sum(case["time"] for case in perf), 3),
        "all_seconds_sum": round(sum(case["time"] for case in cases), 3),
        "performance_cases": perf,
        "not_passed": [case for case in cases if case["outcome"] != "passed"],
    }


def verb_run_step(ns: argparse.Namespace) -> int:
    tree = ns.tree.resolve()
    source = (ns.workflow_from or ns.tree).resolve()
    run_block = step_run(source, "scheduled")
    venv_bin = Path(ns.python).parent
    junit = tree / "reports" / "junit" / "junit-slow.xml"
    if junit.exists():
        junit.unlink()
    log = ns.out_dir / f"run_{ns.label}.log"
    started = time.monotonic()
    with log.open("w", encoding="utf-8") as handle:
        handle.write(f"# run block from {source}/.github/workflows/scheduled-tests.yml, cwd {tree}, PATH head {venv_bin}\n{run_block}\n# ---\n")
        handle.flush()
        done = subprocess.run(["bash", "-e", "-c", run_block], cwd=tree, env=child_env(venv_bin), stdout=handle, stderr=subprocess.STDOUT, check=False, timeout=1800)  # nosec B603 B607
    wall = round(time.monotonic() - started, 2)
    result: dict = {"label": ns.label, "tree": str(tree), "workflow_from": str(source), "python": ns.python, "run_block": run_block, "exit": done.returncode, "wall_seconds": wall, "log": str(log)}
    probe = subprocess.run([ns.python, "-I", "-c", "import sys; print(sys.version.split()[0], sys.executable, sys.base_prefix)"], capture_output=True, text=True, check=False, timeout=60)  # nosec B603
    result["interpreter"] = probe.stdout.strip()
    if junit.exists():
        kept = ns.out_dir / f"junit_{ns.label}.xml"
        shutil.copyfile(junit, kept)
        result["junit"] = str(kept)
        result.update(junit_summary(kept))
    tail = [line for line in log.read_text(encoding="utf-8").splitlines() if re.search(r"\d+ (passed|failed)", line)]
    result["pytest_summary_line"] = tail[-1] if tail else None
    (ns.out_dir / f"run_{ns.label}.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in ("performance_cases", "run_block")}, indent=1))
    return done.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="verb", required=True)
    collect = sub.add_parser("collect")
    collect.add_argument("--python", required=True)
    collect.add_argument("--tree", required=True, type=Path)
    collect.add_argument("--out", required=True, type=Path)
    compare = sub.add_parser("compare")
    compare.add_argument("--main", required=True, type=Path)
    compare.add_argument("--tree", required=True, type=Path)
    compare.add_argument("--out", required=True, type=Path)
    compare.add_argument("--new-test")
    run_step = sub.add_parser("run-step")
    run_step.add_argument("--python", required=True)
    run_step.add_argument("--tree", required=True, type=Path)
    run_step.add_argument("--label", required=True)
    run_step.add_argument("--out-dir", required=True, type=Path)
    run_step.add_argument("--workflow-from", type=Path)
    ns = parser.parse_args()
    return {"collect": verb_collect, "compare": verb_compare, "run-step": verb_run_step}[ns.verb](ns)


if __name__ == "__main__":
    sys.exit(main())
