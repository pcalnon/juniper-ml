#!/usr/bin/env python3
"""
Validator census for juniper-data's "run the unrun tests" carrier: which CI lane selects which test.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 7: validating the d2-unrun-tests carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-data's .github/workflows/ci.yml and scheduled-tests.yml (the five pytest invocations copied below),
         juniper-data#529 (the precedent), util/ad-hoc/2026-11-12_flood4r2_d2-data_collect.py (the builder's own
         census, deliberately NOT imported: this one is an independent re-derivation)

Two verbs.

  collect --python <venv python> --tree <juniper-data tree> --out <file.json> [--label <text>]
      Runs ``python -m pytest --collect-only -q -p no:cacheprovider`` once per lane with that lane's own path and
      marker arguments (and once with none), from the tree's root, and stores every node id per lane.

  compare --before <file.json> --after <file.json> --out <file.json> [--rename OLD=NEW ...]
      Per lane: counts, added and removed node ids. The set no lane selects, before and after. Whether every newly
      selected node was un-laned before, whether any lane lost a node, and which nodes are selected by more
      pull-request lanes after than before. ``--rename`` maps a moved module's node-id prefix.

Every pytest child runs with the six Sentry DSN variables set to the empty string and a short list of token
variables removed. TMPDIR is left as the session gave it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
DROPPED_NAMES = ("HF_TOKEN", "PYPI_API_TOKEN", "TEST_PYPI_API_TOKEN", "TWINE_PASSWORD", "GITLEAKS_PARITY_REQUIRED")

# name -> (kind, pytest arguments exactly as the workflow writes its selection)
LANES = {
    "unit": ("pull-request", ["-m", "unit and not slow", "juniper_data/tests/unit"]),
    "integration": ("pull-request", ["-m", "integration and not slow", "juniper_data/tests/integration"]),
    "gitleaks": ("pull-request", ["juniper_data/tests/unit/test_gitleaks_config.py"]),
    "slow": ("schedule-or-dispatch", ["-m", "slow"]),
    "scheduled": ("schedule-or-dispatch", ["-m", "slow or integration"]),
    "all": ("none", []),
}
PR_LANES = tuple(name for name, (kind, _args) in LANES.items() if kind == "pull-request")
REAL_LANES = tuple(name for name in LANES if name != "all")


def child_env() -> dict:
    env = {key: value for key, value in os.environ.items() if key not in DROPPED_NAMES}
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def collect_lane(python: str, tree: Path, args: list[str]) -> dict:
    # No -q of our own: pyproject's addopts already carries one, and a second one turns the listing into per-file counts.
    argv = [python, "-m", "pytest", "--collect-only", "-p", "no:cacheprovider", *args]
    done = subprocess.run(argv, cwd=str(tree), env=child_env(), capture_output=True, text=True, check=False, timeout=600)
    nodes = [line.strip() for line in done.stdout.splitlines() if "::" in line and line.startswith("juniper_data/")]
    tail = [line for line in done.stdout.splitlines() if line.strip()]
    summary = tail[-1] if tail else ""
    stated = re.search(r"(\d+)(?:/\d+)? tests? collected", summary)
    return {"argv": argv[3:], "exit": done.returncode, "summary": summary, "summary_selected": int(stated.group(1)) if stated else None, "nodes": nodes, "stderr_tail": done.stderr[-2000:]}


def verb_collect(ns: argparse.Namespace) -> int:
    tree = Path(ns.tree).resolve()
    version = subprocess.run([ns.python, "-c", "import sys, juniper_data; print(sys.version.split()[0]); print(juniper_data.__file__)"], cwd=str(tree), env=child_env(), capture_output=True, text=True, check=False)
    payload = {"label": ns.label, "tree": str(tree), "python": ns.python, "probe": version.stdout.split(), "lanes": {}}
    status = 0
    for name, (kind, args) in LANES.items():
        result = collect_lane(ns.python, tree, args)
        result["kind"] = kind
        result["count"] = len(result["nodes"])
        result["duplicates"] = len(result["nodes"]) - len(set(result["nodes"]))
        payload["lanes"][name] = result
        print(f"{name:12s} exit={result['exit']} count={result['count']:5d} dup={result['duplicates']} | {result['summary']}")
        if result["exit"] != 0 or result["count"] != result["summary_selected"]:
            status = 1
    Path(ns.out).write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    return status


def apply_renames(node: str, renames: list[tuple[str, str]]) -> str:
    for old, new in renames:
        if node.startswith(old + "::"):
            return new + node[len(old) :]
    return node


def lanes_of(payload: dict, renames: list[tuple[str, str]]) -> dict[str, set[str]]:
    return {name: {apply_renames(node, renames) for node in payload["lanes"][name]["nodes"]} for name in LANES}


def by_file(nodes: set[str]) -> dict[str, int]:
    return dict(sorted(Counter(node.split("::", 1)[0] for node in nodes).items()))


def verb_compare(ns: argparse.Namespace) -> int:
    renames = [tuple(item.split("=", 1)) for item in ns.rename]
    before = lanes_of(json.loads(Path(ns.before).read_text(encoding="utf-8")), renames)
    after = lanes_of(json.loads(Path(ns.after).read_text(encoding="utf-8")), [])
    report: dict = {"renames": renames, "lanes": {}}
    for name in LANES:
        added = after[name] - before[name]
        removed = before[name] - after[name]
        report["lanes"][name] = {"before": len(before[name]), "after": len(after[name]), "added": len(added), "removed": len(removed), "added_by_file": by_file(added), "removed_by_file": by_file(removed), "removed_nodes": sorted(removed)}
        print(f"{name:12s} {len(before[name]):5d} -> {len(after[name]):5d}  (+{len(added)} -{len(removed)})")

    def unlaned(side: dict[str, set[str]]) -> set[str]:
        selected: set[str] = set()
        for name in REAL_LANES:
            selected |= side[name]
        return side["all"] - selected

    def pr_count(side: dict[str, set[str]], node: str) -> int:
        return sum(1 for name in PR_LANES if node in side[name])

    none_before = unlaned(before)
    none_after = unlaned(after)
    newly = set()
    for name in REAL_LANES:
        newly |= after[name] - before[name]
    left = none_before - none_after
    more_pr_lanes = sorted(node for node in after["all"] if node in before["all"] and pr_count(after, node) > pr_count(before, node) and pr_count(before, node) >= 1)
    pr_before = {node for node in before["all"] if pr_count(before, node) >= 1}
    pr_after = {node for node in after["all"] if pr_count(after, node) >= 1}
    report.update(
        {
            "no_lane_before": {"total": len(none_before), "by_file": by_file(none_before)},
            "no_lane_after": {"total": len(none_after), "by_file": by_file(none_after), "nodes": sorted(none_after)},
            "left_no_lane": {"total": len(left), "by_file": by_file(left), "nodes": sorted(left)},
            "newly_selected_by_some_lane": {"total": len(newly), "by_file": by_file(newly)},
            "newly_selected_equals_left_no_lane": newly == left,
            "newly_selected_not_unlaned_before": sorted(newly - none_before),
            "entered_no_lane": sorted(none_after - none_before),
            "collected_only_before": sorted(before["all"] - after["all"]),
            "collected_only_after": sorted(after["all"] - before["all"]),
            "selected_by_more_pull_request_lanes_than_before": more_pr_lanes,
            "pull_request_lane_nodes": {"before": len(pr_before), "after": len(pr_after), "gained": len(pr_after - pr_before), "lost": sorted(pr_before - pr_after)},
            "nodes_in_two_pull_request_lanes_after": by_file({node for node in after["all"] if pr_count(after, node) >= 2}),
            "nodes_in_two_pull_request_lanes_before": by_file({node for node in before["all"] if pr_count(before, node) >= 2}),
        }
    )
    print(f"no lane: {len(none_before)} -> {len(none_after)}; left no-lane {len(left)}; newly selected {len(newly)}; equal={newly == left}")
    print(f"no lane after, by file: {by_file(none_after)}")
    print(f"entered no-lane: {len(report['entered_no_lane'])}; lanes that lost a node: {[n for n in LANES if report['lanes'][n]['removed']]}")
    print(f"selected by more PR lanes than before (and by at least one before): {len(more_pr_lanes)}")
    print(f"PR-lane nodes: {len(pr_before)} -> {len(pr_after)}; lost {len(pr_before - pr_after)}")
    Path(ns.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    verbs = parser.add_subparsers(dest="verb", required=True)
    collect = verbs.add_parser("collect")
    collect.add_argument("--python", required=True)
    collect.add_argument("--tree", required=True)
    collect.add_argument("--out", required=True)
    collect.add_argument("--label", default="")
    collect.set_defaults(func=verb_collect)
    compare = verbs.add_parser("compare")
    compare.add_argument("--before", required=True)
    compare.add_argument("--after", required=True)
    compare.add_argument("--out", required=True)
    compare.add_argument("--rename", action="append", default=[])
    compare.set_defaults(func=verb_compare)
    ns = parser.parse_args()
    return ns.func(ns)


if __name__ == "__main__":
    sys.exit(main())
