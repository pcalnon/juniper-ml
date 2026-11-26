"""
Run the r23w code lens's wire probe over trees x venvs x uvicorn ws implementations x scenarios, at most N at a time.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

Each cell runs `bash RUNENV PYTHON WIRE --ws IMPL --scenario S --out OUT.json [--hold H]` with PYTHONPATH set to the
tree's juniper-service-core directory for the "main" tree (the "fix" tree is the venv's editable install).

Usage:
  python -I <this file> --val VAL_DIR --wire WIRE_SCRIPT --runenv RUNENV --jobs 4 [--only-scenarios a,b] [--hold 45]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import pathlib
import subprocess
import sys
import time

SCENARIOS = [
    "a_unsendable", "a_deliverable", "b_hb_pong", "b_hb_command", "b_hb_inflight", "b_hb_then_idle", "b_idle_command",
    "b_idle_pong", "b_oversize_command", "b_malformed_command", "b_auth", "c_stall", "c_take_close",
]
VENV_IMPLS = {"probe313": ["websockets", "websockets-sansio", "wsproto"], "old312": ["websockets", "wsproto"]}


def run_cell(cell: dict) -> dict:
    env = dict(os.environ)
    if cell["tree"] == "main":
        env["PYTHONPATH"] = cell["main_path"]
    else:
        env.pop("PYTHONPATH", None)
    out = pathlib.Path(cell["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["bash", cell["runenv"], cell["python"], cell["wire"], "--ws", cell["impl"], "--scenario", cell["scenario"], "--out", str(out), "--hold", str(cell["hold"])]
    started = time.monotonic()
    with open(out.with_suffix(".log"), "w", encoding="utf-8") as log:
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env=env, cwd=cell["cwd"], timeout=cell["hold"] + 120, check=False)
    return {"cell": f'{cell["tree"]}/{cell["venv"]}/{cell["scenario"]}/{cell["impl"]}', "exit": proc.returncode, "wall_s": round(time.monotonic() - started, 1)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--val", required=True, type=pathlib.Path)
    parser.add_argument("--wire", required=True)
    parser.add_argument("--runenv", required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--hold", type=float, default=45.0)
    parser.add_argument("--only-scenarios", default="")
    parser.add_argument("--only-venvs", default="")
    parser.add_argument("--only-impls", default="")
    parser.add_argument("--trees", default="main,fix")
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    scenarios = [s for s in args.only_scenarios.split(",") if s] or SCENARIOS
    venvs = [v for v in args.only_venvs.split(",") if v] or list(VENV_IMPLS)
    impls_filter = {i for i in args.only_impls.split(",") if i}
    cells = []
    for tree in args.trees.split(","):
        for venv in venvs:
            for impl in VENV_IMPLS[venv]:
                if impls_filter and impl not in impls_filter:
                    continue
                for scenario in scenarios:
                    cells.append({
                        "tree": tree, "venv": venv, "impl": impl, "scenario": scenario, "hold": args.hold,
                        "python": str(args.val / "venvs" / venv / "bin" / "python"), "wire": args.wire, "runenv": args.runenv,
                        "main_path": str(args.val / "main_tree" / "juniper-service-core"), "cwd": str(args.val),
                        "out": str(args.val / "wire" / tree / venv / f"{scenario}_{impl}{args.tag}.json"),
                    })
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.jobs, 4))) as pool:
        for res in pool.map(run_cell, cells):
            results.append(res)
            print(json.dumps(res), flush=True)
    bad = [r for r in results if r["exit"] != 0]
    print(f"cells={len(results)} nonzero_exit={len(bad)}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
