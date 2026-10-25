"""
Survey every shipped suite's per_run_timeout_seconds against its cells' worst-case driver budgets (juniper-ml#2210).

run_suite refuses a suite before its first --up when `execution.per_run_timeout_seconds` (default
3600) does not exceed a cell's worst-case driver budget: `run_experiment.worst_case_budget`, summed per
cell over the health waits, dataset creation, each wall-bounded phase and save_model / the cascor
teardown and snapshot. This script runs that same check, `run_suite.driver_budgets` and
`run_suite.check_per_run_timeout`, over every suite under util/experiments/suites/ and reports each one
OK, REFUSED, or UNRESOLVED (a base config this checkout cannot read).

Most suites take their base config from a sibling repo (`../../../../../juniper-recurrence/...`), which
resolves only from the canonical checkout or with --project-dir (run_suite's JUNIPER_EXP_PROJECT_DIR
rebase). The HEAD of each sibling tree read is printed, because the verdict is only as current as that
checkout.

Usage:
    python3 -I util/ad-hoc/2026-10-25_driver_budget_survey.py --project-dir /path/to/Juniper [--json]

Exit 0 when no readable suite is refused, 1 when one is, 2 on misuse.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2210; util/ad-hoc/2026-08-20_wall_ordering_survey.py (the wall-only predecessor)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess  # nosec B404 - fixed argv, read-only git query
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUITES_DIR = REPO_ROOT / "util" / "experiments" / "suites"


def _tree_head(config_path: Path) -> "tuple[str, str] | None":
    """``(repo dir, HEAD sha)`` of the git tree holding ``config_path``, or None."""
    for parent in config_path.parents:
        if (parent / ".git").exists():
            proc = subprocess.run(["git", "-C", str(parent), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10, check=False)  # nosec B603 B607
            return str(parent), proc.stdout.strip() or "unknown"
    return None


def survey(run_suite, project_dir: "str | None") -> "list[dict]":
    if project_dir:
        os.environ["JUNIPER_EXP_PROJECT_DIR"] = project_dir
    driver = run_suite._driver_module()
    if driver is None:
        raise SystemExit("the driver module did not import")
    # load_config logs its non-fatal config findings on every call, which would bury the table.
    logging.getLogger(driver.LOGGER_NAME).setLevel(logging.ERROR)
    rows: "list[dict]" = []
    for path in sorted(SUITES_DIR.rglob("*.yaml")):
        doc = run_suite.load_suite(path)
        execution = doc.get("execution") or {}
        timeout = float(execution.get("per_run_timeout_seconds", 3600))
        max_wall = float(execution["max_wall_seconds"]) if execution.get("max_wall_seconds") is not None else None
        dataset = float(execution["dataset_create_timeout_seconds"]) if execution.get("dataset_create_timeout_seconds") is not None else None
        cells = run_suite.expand_cells(doc, path)
        readable = [cell for cell in cells if Path(cell["config_path"]).is_file()]
        unresolved = sorted({cell["config_path"] for cell in cells if not Path(cell["config_path"]).is_file()})
        row = {"suite": path.relative_to(SUITES_DIR).as_posix(), "app": doc["suite"]["app"], "per_run_timeout_seconds": timeout, "cells": len(cells), "judged": len(readable), "unresolved": unresolved, "trees": sorted({head for head in (_tree_head(Path(cell["config_path"])) for cell in readable) if head})}
        if not readable:
            row["verdict"] = "UNRESOLVED"
            rows.append(row)
            continue
        with tempfile.TemporaryDirectory() as tmp:
            configs = {cell["cell_id"]: driver.load_config(run_suite.materialise_cell(cell, doc["suite"], Path(tmp), None)) for cell in readable}
        budgets = run_suite.driver_budgets(driver, configs, max_wall, dataset)
        worst = max(budgets, key=lambda cell_id: sum(budgets[cell_id].values()))
        row.update(worst_cell=worst, worst_budget=sum(budgets[worst].values()), worst_terms=budgets[worst])
        try:
            run_suite.check_per_run_timeout(timeout, budgets, declared="per_run_timeout_seconds" in execution)
            row["verdict"] = "OK" if not unresolved else "OK (partial)"
        except run_suite.SuiteError as exc:
            row["verdict"] = "REFUSED"
            row["refusal"] = str(exc)
        rows.append(row)
    return rows


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--project-dir", default=None, help="the Juniper ecosystem root, for sibling-repo base configs (sets JUNIPER_EXP_PROJECT_DIR)")
    parser.add_argument("--json", action="store_true", help="print the rows as JSON")
    args = parser.parse_args(argv)
    sys.path.insert(0, str(REPO_ROOT / "util" / "experiments"))
    import run_suite  # noqa: E402

    rows = survey(run_suite, args.project_dir)
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        for row in rows:
            budget = f"worst {row['worst_budget']:g}s at {row['worst_cell']} ({' + '.join(f'{k} {v:g}' for k, v in row['worst_terms'].items())})" if "worst_budget" in row else f"{len(row['unresolved'])} base config(s) unreadable"
            print(f"{row['verdict']:<13} {row['suite']:<45} {row['app']:<10} timeout {row['per_run_timeout_seconds']:g}  {budget}")
        trees = sorted({tuple(tree) for row in rows for tree in row["trees"]})
        print("\nbase-config trees read:")
        for tree, head in trees:
            print(f"  {tree} @ {head}")
        counts = {verdict: sum(1 for row in rows if row["verdict"] == verdict) for verdict in sorted({row["verdict"] for row in rows})}
        print("\n" + ", ".join(f"{verdict}: {count}" for verdict, count in counts.items()) + f" -- {len(rows)} suites")
    return 1 if any(row["verdict"] == "REFUSED" for row in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
