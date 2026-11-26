"""
Build flood-4 r49's manifest.json from its run artifacts: files with status and sha256, the CI failure history, the
reproduction recipe, the checks, the mutants, the 50-run results and the open questions.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26) (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
    section 8); flood-4 session 16 builder r49; run summaries from util/ad-hoc/2026-11-26_flood4_s16_r49_summarize.py

Usage:
    python3 -I <this file> --r49 <the r49 directory> --checks <checks json> [--open-questions <json>]
--checks is a JSON list of {"name", "command", "interpreter", "exit", "log"} written by hand from the logs; everything
else is read from the run directories. Writes <r49>/manifest.json (valid JSON, rewritten whole each time).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

RUN_DIRS = ("repro", "fifty", "mutants", "file312", "file314", "threads", "lane", "lane_final", "lane_final314", "lane_bytes")


def load_summarizer(here: Path):
    spec = importlib.util.spec_from_file_location("r49_summarize", here / "2026-11-26_flood4_s16_r49_summarize.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r49", required=True)
    parser.add_argument("--checks", required=True)
    parser.add_argument("--open-questions", default="")
    args = parser.parse_args()
    root = Path(args.r49)
    summarize = load_summarizer(Path(__file__).resolve().parent)
    paths = [p for p in (root / "paths.txt").read_text(encoding="utf-8").splitlines() if p.strip()]
    files = []
    for rel in paths:
        base = sha(root / "tree_base" / rel)
        final = sha(root / "final" / rel)
        files.append({"path": rel, "status": "modified" if base else "added", "sha256_base": base, "sha256_final": final, "final_copy": str(root / "final" / rel)})
    runs = {}
    for name in RUN_DIRS:
        directory = root / "runs" / name
        if not directory.exists():
            continue
        labels = sorted({p.name[: -len(".run.json")].split(".run")[0] if ".run" in p.name[: -len(".run.json")] else p.name[: -len(".run.json")] for p in directory.glob("*.run.json")})
        runs[name] = [summarize.summarize(directory, label) for label in labels]
    mutant_records = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in sorted((root / "runs" / "mutants").glob("*.mutant.json"))}
    fifty = []
    for name in ("repro", "fifty", "mutants"):
        for item in runs.get(name, []):
            if item["cases"] >= 50 or item["label"].startswith(("M1_", "M2_", "M3_", "base_gc8")):
                fifty.append({"dir": name, "label": item["label"], "cases": item["cases"], "outcomes": item["outcomes"], "failure_messages": item["failure_messages"], "failure_latency_s": item["failure_latency_s"], "stops_s": item["stops_s"], "stop_kinds": item["stop_kinds"], "stub_calls": item["stub_calls"], "stub_calls_on_loop_thread": item["stub_calls_on_main_thread"]})
    health = json.loads((root / "ci" / "health_failures.json").read_text(encoding="utf-8"))
    denominator = json.loads((root / "ci" / "unit_denominator.json").read_text(encoding="utf-8"))
    manifest = {
        "id": "r49",
        "repo": "pcalnon/juniper-canopy",
        "base_sha": (root / "base.txt").read_text(encoding="utf-8").strip(),
        "clone": str(root / "clone"),
        "branch_in_clone": "test/x7-health-test-held-call (local only; probe commit unsigned, never pushed)",
        "ruling": "ruling 49 (2026-11-26), 'Separate follow-up PR (Recommended)'; parent ruling 28; flood-4 record section 8",
        "files": files,
        "failure_history": {"census_summary": health["summary"], "health_failures": health["health_failures"], "unit_lane_jobs_ran": denominator.get("unit_jobs_ran_by_class"), "claims_lens_count": 4, "reconciliation": "the claims lens listed run 45747943199 while it was in_progress (conclusion null), so its failure-or-rerun selection could not include it; it failed later. Its other four match job for job."},
        "reproduction_recipe": {
            "plugin": "util/ad-hoc/2026-11-26_flood4_s16_r49_stall_plugin.py (linked as r49_stall.py into the run dir's plugins/)",
            "runner": "bash S/tmp/flood4/session14/runenv.bash /usr/bin/python3 S/util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py --python S/tmp/flood4/session14/r28/venvs/py313/bin/python --tree <tree> --out <dir> --label <L> --census S/util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_census.py --no-cov --no-maxfail --env R49_OUT=<dir>/<L>.r49.jsonl --env R49_STALL_KIND=gc --env R49_HEAP_M=20 --env R49_STALL_AT=request -- -p r49_stall src/tests/regression/test_x7_loop_responsiveness.py::TestLoopStaysAnswerable::test_health_stays_fast_while_upstream_is_slow --count=50 --cov=src --cov-report= --cov-fail-under=0",
            "what_it_does": "retains 20 million empty lists at configure time, then at the first http request into main.app of each test runs gc.collect() on the event-loop thread before the app handles it (a full collection: every thread stops). No host-wide load.",
            "expected_on_main": "the old test fails 50/50 (runs/repro/base_gc20_request_x50); with R49_HEAP_M=8 it passes 20/20 (base_gc8_request_x20)",
        },
        "fifty_run_results": fifty,
        "runs": runs,
        "mutants": mutant_records,
        "checks": json.loads(Path(args.checks).read_text(encoding="utf-8")),
        "open_questions": json.loads(Path(args.open_questions).read_text(encoding="utf-8")) if args.open_questions else [],
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({"files": len(files), "run_dirs": {k: len(v) for k, v in runs.items()}, "mutants": len(mutant_records)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
