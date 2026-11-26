#!/usr/bin/env python3
"""
Run carrier r49's claims-lens targeted checks of juniper-canopy's X7 health test, in sequence, behind the r27v2 fence.

Each run goes through util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py (CI-like child environment, every
connect to a Juniper port refused and recorded) under the session-14 run wrapper (Sentry variables empty, dead session
bus). The builder's stall plugin (util/ad-hoc/2026-11-26_flood4_s16_r49_stall_plugin.py) must already be copied into
each run's <out>/plugins/r49_stall.py. Runs:

  t1  main's test (tree_main), one gc.collect() over 20 M retained lists on the loop thread at the first request, x10
  t2  the carrier's T-A2 on main + carrier (tree_assembled_t), the same injection, x10
  t4  main's test, no injection, x10 (no coverage)
  t3  main + carrier, the whole file with ci.yml's marker expression, coverage on, 3 separate processes, --durations=0

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- investigation (flood-4 session 16, carrier r49 claims lens)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 49)
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 - runs the fenced run-lane helper
import sys
from pathlib import Path

NODE = "src/tests/regression/test_x7_loop_responsiveness.py::TestLoopStaysAnswerable::test_health_stays_fast_while_upstream_is_slow"
MARKERS = "not requires_cascor and not requires_server and not slow"


def main() -> int:
    ap = argparse.ArgumentParser(description="r49 claims-lens targeted runs")
    ap.add_argument("--worktree", required=True, help="the orchestrator's worktree S")
    ap.add_argument("--lens", required=True, help="the lens directory (holds tree_main, tree_assembled_t, runs/)")
    ap.add_argument("--only", default="t1,t2,t4,t3")
    args = ap.parse_args()
    s, d = Path(args.worktree), Path(args.lens)
    base = [
        "bash", str(s / "tmp/flood4/session14/runenv.bash"),
        sys.executable, "-I", str(s / "util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py"),
        "--python", str(s / "tmp/flood4/session14/r28/venvs/py313/bin/python"),
        "--census", str(s / "util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_census.py"),
    ]
    gc20 = ["--env", "R49_STALL_KIND=gc", "--env", "R49_STALL_AT=request", "--env", "R49_HEAP_M=20"]
    plan = {
        "t1": ["--tree", str(d / "tree_main"), "--out", str(d / "runs/t1_main_gc20req"), "--label", "t1_main_gc20req_x10", "--no-maxfail", "--env", f"R49_OUT={d / 'runs/t1_main_gc20req/t1.r49.jsonl'}", *gc20, "--", "-p", "r49_stall", NODE, "--count=10"],
        "t2": ["--tree", str(d / "tree_assembled_t"), "--out", str(d / "runs/t2_asm_gc20req"), "--label", "t2_asm_gc20req_x10", "--no-maxfail", "--env", f"R49_OUT={d / 'runs/t2_asm_gc20req/t2.r49.jsonl'}", *gc20, "--", "-p", "r49_stall", NODE, "--count=10"],
        "t4": ["--tree", str(d / "tree_main"), "--out", str(d / "runs/t4_main_noload"), "--label", "t4_main_noload_x10", "--no-maxfail", "--no-cov", "--env", f"R49_OUT={d / 'runs/t4_main_noload/t4.r49.jsonl'}", "--", "-p", "r49_stall", NODE, "--count=10"],
        "t3": ["--tree", str(d / "tree_assembled_t"), "--out", str(d / "runs/t3_asm_file"), "--label", "t3_asm_file", "--count", "3", "--no-maxfail", "--env", f"R49_OUT={d / 'runs/t3_asm_file/t3.r49.jsonl'}", "--", "-p", "r49_stall", "-m", MARKERS, "src/tests/regression/test_x7_loop_responsiveness.py", "--durations=0"],
    }
    worst = 0
    for name in args.only.split(","):
        proc = subprocess.run([*base, *plan[name]], check=False, timeout=900)  # nosec B603
        print(f"{name} exit {proc.returncode}", flush=True)
        worst = max(worst, proc.returncode)
    return worst


if __name__ == "__main__":
    sys.exit(main())
