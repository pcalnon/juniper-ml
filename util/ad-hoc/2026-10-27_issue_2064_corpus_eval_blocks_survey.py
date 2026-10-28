#!/usr/bin/env python3
"""
Survey the experiment run corpus for juniper-ml#2064: which cascor runs have a final evaluation, on which split,
and which runs and suite cells the held-out ``test_*`` columns reach. Read-only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-27
Status: ad-hoc — investigation (corpus figures for the juniper-ml#2064 held-out eval-scalars PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/experiments/stats_summary.py (cascor_eval_blocks); util/experiments/run_suite.py (_headline_metrics,
         _row_metrics); util/ad-hoc/2026-10-27_issue_2064_eval_blocks_mutation_check.py

Scope: the run corpus root ONLY -- ``--root``, else ``$JUNIPER_EXP_RUN_ROOT``, else ``~/.local/state/juniper-experiments``.
It searches no repository and no repository ``tmp/``. Nothing is written anywhere.

Every figure comes from the code the PR ships, run on the files as they are:

- each top-level run dir's ``artifacts/results/metrics_final.json`` goes through ``stats_summary.cascor_eval_blocks``,
  the derivation behind ``stats.json`` / ``summary.md`` / ``eval_metrics.png``: final evaluation on ``test``, on
  ``validation``, or absent (and why), whether it carries ``accuracy`` (juniper-cascor#731), the in-loop split, and
  the first and last run-id date of each class;
- each cascor run's ``stats.json`` schema, and what ``run_suite._headline_metrics`` reads from the run dir: how many
  runs gain ``test_*`` columns (a ``/1`` stats.json re-derives them from its ``metrics_final.json``);
- each cascor suite (``suites/*/suite_manifest.json`` with ``app: cascor``): the cells whose registry row
  ``run_suite._row_metrics`` -- what ``--reaggregate`` prints -- gives ``test_*`` columns.

Exit codes: 0 = surveyed; 2 = the root is not a directory.

Usage:
    python3 util/ad-hoc/2026-10-27_issue_2064_corpus_eval_blocks_survey.py [--root DIR] [--json]
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "util"))

from experiments import stats_summary as ss  # noqa: E402  (path-invoked util import)

_spec = importlib.util.spec_from_file_location("run_suite_for_issue_2064_survey", REPO / "util" / "experiments" / "run_suite.py")
assert _spec is not None and _spec.loader is not None  # nosec B101 - the module ships beside this checkout
run_suite = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_suite)


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _final_class(held: dict) -> str:
    return f"final on {held['split']}" if not held["absent"] else f"no final: {held['absent']}"


def survey(root: Path) -> dict:
    classes: "collections.Counter[str]" = collections.Counter()
    dates: "dict[str, list[str]]" = collections.defaultdict(list)
    in_loop: "collections.Counter[str]" = collections.Counter()
    with_accuracy = 0
    for path in sorted(root.glob("*/artifacts/results/metrics_final.json")):
        blocks = ss.cascor_eval_blocks(_read(path))
        held = blocks["eval_scalars"]
        label = _final_class(held)
        classes[label] += 1
        dates[label].append(path.parts[-4][:8])
        in_loop[str(blocks["eval_scalars_in_loop"]["split"])] += 1
        with_accuracy += 1 if held["accuracy"] is not None else 0

    schemas: "collections.Counter[str]" = collections.Counter()
    gaining: "collections.Counter[str]" = collections.Counter()
    cascor_stats = runs_with_test_columns = 0
    for path in sorted(root.glob("*/artifacts/results/stats.json")):
        stats = _read(path)
        if not isinstance(stats, dict) or not isinstance(stats.get("cascor"), dict):
            continue
        cascor_stats += 1
        schemas[str(stats.get("schema"))] += 1
        columns = [column for column in run_suite._headline_metrics(path.parents[2]) if column.startswith("test_")]
        runs_with_test_columns += 1 if columns else 0
        gaining.update(columns)

    suites = cells = cells_with_test_columns = suites_gaining = 0
    for manifest_path in sorted(root.glob("suites/*/suite_manifest.json")):
        manifest = _read(manifest_path)
        if not isinstance(manifest, dict) or (manifest.get("suite") or {}).get("app") != "cascor":
            continue
        suites += 1
        registry = run_suite._read_registry(manifest_path.parent)
        gained = 0
        for row in registry.values():
            cells += 1
            if any(column.startswith("test_") for column in run_suite._row_metrics(row)):
                gained += 1
        cells_with_test_columns += gained
        suites_gaining += 1 if gained else 0

    return {
        "root": str(root),
        "metrics_final": {
            "files": sum(classes.values()),
            "by_final_evaluation": {label: {"runs": count, "first": min(dates[label]), "last": max(dates[label])} for label, count in sorted(classes.items())},
            "with_final_accuracy": with_accuracy,
            "in_loop_split": dict(sorted(in_loop.items())),
        },
        "stats_json": {"cascor_files": cascor_stats, "schema": dict(sorted(schemas.items())), "runs_gaining_test_columns": runs_with_test_columns, "by_column": dict(sorted(gaining.items()))},
        "suites": {"cascor_suites": suites, "registry_cells": cells, "cells_gaining_test_columns": cells_with_test_columns, "suites_gaining_test_columns": suites_gaining},
    }


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(os.environ.get("JUNIPER_EXP_RUN_ROOT", str(Path.home() / ".local" / "state" / "juniper-experiments"))))
    parser.add_argument("--json", action="store_true", help="print the survey as JSON")
    args = parser.parse_args(argv)
    if not args.root.is_dir():
        print(f"not a directory: {args.root}", file=sys.stderr)
        return 2
    result = survey(args.root)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    final = result["metrics_final"]
    print(f"run corpus: {result['root']}")
    print(f"cascor metrics_final.json: {final['files']} (with final.accuracy: {final['with_final_accuracy']}; in-loop split: {final['in_loop_split']})")
    for label, row in final["by_final_evaluation"].items():
        print(f"  {row['runs']:4d}  {label}  [{row['first']} .. {row['last']}]")
    stats = result["stats_json"]
    print(f"cascor stats.json: {stats['cascor_files']} (schema: {stats['schema']}); runs gaining test_* columns: {stats['runs_gaining_test_columns']} {stats['by_column']}")
    suites = result["suites"]
    print(f"cascor suites: {suites['cascor_suites']}, {suites['registry_cells']} registry cells; --reaggregate gives test_* columns to {suites['cells_gaining_test_columns']} cells in {suites['suites_gaining_test_columns']} suites")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
