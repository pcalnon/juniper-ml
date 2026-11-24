#!/usr/bin/env python3
"""Summarise a run of the twelve-mutant runner into the per-mutation verdict file a builder ships.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use helper of the Cursor flood-4 disposition arc: the juniper-data back-port of the
             gitleaks pull-request scan's blocking-wiring pins)
Author:      Paul Calnon
Created:     2026-11-14
Status:      ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related:     juniper-data#530, juniper-data-client#260; util/ad-hoc/2026-11-14_flood4r2_r35-data_step1_mutants.py
Version:     0.1.0
License:     MIT License

It refuses (exit 1) a run in which a mutant's anchor did not occur exactly once, a mutated file hashed the same as the
original (an edit that changed nothing), a restore was not exact, or the baseline was not green in both lanes.

Usage:
    python3 util/ad-hoc/2026-11-14_flood4r2_r35-data_summarize_mutants.py <runner's mutants.json> <out json> <label>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def lane_line(lane: dict) -> str:
    """One lane as `exit N: P passed, F failed, S skipped`."""
    return f"exit {lane['exit']}: {lane.get('passed')} passed, {len(lane.get('failed', []))} failed, {lane.get('skipped_count')} skipped"


def main(argv: list[str]) -> int:
    """Write the summary; exit 1 when the run cannot be trusted."""
    if len(argv) != 3:
        print("usage: <runner's mutants.json> <out json> <label>", file=sys.stderr)
        return 2
    run = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    problems: list[str] = []
    base = run["baseline"]
    for name, lane in base.items():
        if lane["exit"] != 0 or lane.get("failed"):
            problems.append(f"baseline {name} lane is not green")
    rows = []
    for mutant in run["mutants"]:
        if mutant.get("anchor_count") != 1:
            problems.append(f"{mutant['id']}: anchor occurs {mutant.get('anchor_count')} times")
            continue
        if mutant.get("mutated_sha256") == run["ci_yml_sha256"]:
            problems.append(f"{mutant['id']}: the mutated file hashes as the original")
        if mutant.get("restored_sha256") != run["ci_yml_sha256"]:
            problems.append(f"{mutant['id']}: restore not exact")
        lanes = mutant["lanes"]
        rows.append(
            {
                "id": mutant["id"],
                "mutation": mutant["what"],
                "edit": {"exact_text_once": mutant["anchor"], "replacement": mutant["replacement"]},
                "verdict": mutant["verdict"],
                "killed_by": mutant.get("killed_by", {}),
                "unit_lane": lane_line(lanes["unit"]),
                "self_test_lane": lane_line(lanes["self-test"]),
                "mutated_ci_yml_sha256": mutant.get("mutated_sha256"),
                "restored_ci_yml_sha256": mutant.get("restored_sha256"),
                "logs": {name: lane["log"] for name, lane in lanes.items()},
            }
        )
    summary = {
        "label": argv[2],
        "worktree": run["worktree"],
        "interpreter": run["python"],
        "engine": run["engine"],
        "ci_yml_sha256": run["ci_yml_sha256"],
        "test_file_sha256": run["test_file_sha256"],
        "commands": {
            "unit": f"{run['python']} {run['lanes']['unit']}  (env: GITLEAKS_BIN unset, no gitleaks on PATH, GITLEAKS_PARITY_REQUIRED unset; PYTHONDONTWRITEBYTECODE=1; six Sentry variables empty)",
            "self-test": f"{run['python']} {run['lanes']['self-test']}  (env: the engine first on PATH, GITLEAKS_PARITY_REQUIRED=1; PYTHONDONTWRITEBYTECODE=1; six Sentry variables empty)",
            "runner": "util/ad-hoc/2026-11-14_flood4r2_r35-data_step1_mutants.py in the orchestrator worktree (each lane a fresh pytest process; ci.yml restored and its sha256 verified after every mutant)",
        },
        "rule": "killed = any case fails in either lane; survived = both lanes green",
        "baseline": {name: lane_line(lane) for name, lane in base.items()},
        "mutants": rows,
        "survived": [r["id"] for r in rows if r["verdict"] == "survived"],
        "killed": [r["id"] for r in rows if r["verdict"] == "killed"],
        "restores_exact": run.get("restores_exact"),
        "ci_yml_sha256_after": run.get("ci_yml_sha256_after"),
        "test_file_sha256_after": run.get("test_file_sha256_after"),
        "problems": problems,
    }
    Path(argv[1]).write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(f"{argv[2]}: survived {summary['survived']}; killed {summary['killed']}; problems {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
