#!/usr/bin/env python3
"""
Fill the two table placeholders of the unrun-tests PR body from the run results, so no figure is retyped by hand.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (run once on the drafted pr_body.txt; refuses a body without the placeholders)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_d2-data_run.py and ..._mutants.py (write the JSON this reads)

Usage:
    python3 <this> --scratch <the change's tmp/flood4-fix/d2-unrun-tests> [--check]

Replaces ``@@UNIT_LANE_TABLE@@`` with one row per interpreter and venv generation (pytest's own summary line, the
aggregate coverage and both gates' exit status, before and after) and ``@@MUTANT_TABLE@@`` with one row per mutant
(how many newly selected tests fail, and whether main's unit and integration lanes fail with the break in place).
--check only prints the tables. Reads JSON under --scratch and rewrites pr_body.txt there.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MODULE_OF = {"M1": "test_phase1d_security.py", "M2": "test_local_fs_path_traversal.py", "M3": "test_metadata_cache.py", "M4": "test_api_app.py", "M5": "test_r2_1_2_wire_compat.py", "M6": "test_security_integration.py", "M7": "test_batch_operations.py"}
BREAK_OF = {
    "M1": "`api/app.py:191`: `/metrics` is mounted without its trusted-IP wrapper (SEC-16)",
    "M2": "`storage/local_fs.py:54`: `_validate_dataset_id` loses its `..` check (JD-SEC-01)",
    "M3": "`storage/local_fs.py:249`: `LocalFSDatasetStore.save` stops invalidating the metadata cache",
    "M4": "`api/app.py:194`: the `RequestValidationError` handler is never registered (APD-DATA-013)",
    "M5": "`api/routes/health.py:239`: the readiness dependency key is renamed",
    "M6": "`api/middleware.py:246`: `SecurityMiddleware` exempts no path",
    "M7": "`api/routes/datasets.py:705`: batch-create answers 201 after creating nothing (APD-DATA-009)",
}


def _load(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _short(summary: str) -> str:
    return re.sub(r",? \d+ warnings?|,? \d+ subtests passed| \(\d+:\d+:\d+\)", "", summary)


def _lane_rows(scratch: Path) -> list[str]:
    runs = scratch / "runs"
    r1 = {r["job"]: r for r in _load(runs / "unit-lane_r1" / "result.json")["results"]}
    fresh = {r["job"]: r for r in _load(runs / "unit-lane_fresh_before" / "result.json")["results"]}
    for tag in ("unit-lane_fresh_after_py314", "unit-lane_fresh_after_py312"):
        fresh.update({r["job"]: r for r in _load(runs / tag / "result.json")["results"]})
    rows = ["  | Venvs | Python | main `c68e6b4c` | this PR | Aggregate coverage | Gates (aggregate, per-file) |", "  |-------|--------|-----------------|---------|--------------------|-----------------------------|"]
    for label, table in (("built 2026-11-11, side by side", r1), ("built 2026-11-13, one after another", fresh)):
        for py in ("py314", "py312"):
            before, after = table[f"before_{py}"], table[f"after_{py}"]
            cov = f"{before['aggregate_gate']['total_line'].split()[-1]} -> {after['aggregate_gate']['total_line'].split()[-1]}"
            gates = "pass, pass" if all(r["aggregate_gate"]["exit"] == 0 and r["per_file_gate"]["exit"] == 0 and r["exit"] == 0 for r in (before, after)) else "SEE result.json"
            rows.append(f"  | {label} | {before['python_version']} | {_short(before['summary'])} | {_short(after['summary'])} | {cov} | {gates} |")
    return rows


def _mutant_rows(scratch: Path) -> list[str]:
    by_id: dict[str, dict] = {}
    for path in sorted((scratch / "mutants").rglob("mutants_*.json")):
        data = _load(path)
        for m in data["mutants"]:
            by_id.setdefault(m["id"], {})[data["mode"]] = m
    rows = ["  | Module | One-line break | Its newly selected tests | main's unit lane | main's integration lane |", "  |--------|----------------|--------------------------|------------------|-------------------------|"]
    for mid in sorted(by_id):
        new, unit, integ = (by_id[mid].get(k) for k in ("new-tests", "main-lane", "main-integration-lane"))
        if not (new and unit and integ and new["result"] == "killed"):
            raise SystemExit(f"{mid}: a result is missing or the mutant survived")
        cells = [f"{new['failed_count']} fail" if new["failed_count"] != 1 else "1 fails"]
        for res in (unit, integ):
            cells.append("passes" if res["exit"] == 0 else f"fails (`{res['failed_tests'][0].split('::')[-1]}`)" if res["exit"] == 1 else "INCONCLUSIVE")
        rows.append(f"  | `{MODULE_OF[mid]}` | {BREAK_OF[mid]} | {cells[0]} | {cells[1]} | {cells[2]} |")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--scratch", type=Path, required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    scratch = args.scratch.resolve()
    lane = "\n".join(_lane_rows(scratch))
    mutants = "\n".join(_mutant_rows(scratch))
    print(lane)
    print(mutants)
    if args.check:
        return 0
    body_path = scratch / "pr_body.txt"
    with open(body_path, encoding="utf-8") as fh:
        body = fh.read()
    for mark in ("@@UNIT_LANE_TABLE@@", "@@MUTANT_TABLE@@"):
        if body.count(mark) != 1:
            raise SystemExit(f"{mark} occurs {body.count(mark)} times in {body_path}")
    body = body.replace("@@UNIT_LANE_TABLE@@", lane).replace("@@MUTANT_TABLE@@", mutants)
    with open(body_path, "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"filled {body_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
