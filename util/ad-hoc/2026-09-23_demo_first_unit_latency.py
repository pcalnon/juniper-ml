"""
Measure how long canopy's DemoMode takes to install its FIRST cascade unit, and whether it ever doesn't.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy ``src/tests/unit/test_demo_mode_advanced.py::test_cascade_unit_addition``, whose
         ``len(network.hidden_units) >= 0`` is vacuous (canopy#664's "listed, not changed" follow-up list)

Why: the test slept 1.0 s and asserted ``>= 0``. Replacing that with "at least one unit, polled to a
deadline" is only honest if a unit is in practice ALWAYS installed, and the deadline is only honest if
it sits far above the measured latency. DemoMode's loop stops cascade growth with zero units when no
candidate reaches ``min_correlation`` (0.01 by default), so "always" is an empirical claim this measures.

Each trial runs in a FRESH interpreter (``subprocess``), because DemoMode seeds numpy's GLOBAL RNG and a
shared process would make trials correlated. Optional CPU contention (``--burn N``) approximates a loaded
CI runner.

Usage (canopy env, canopy ``src/`` as cwd or via --src):
    python util/ad-hoc/2026-09-23_demo_first_unit_latency.py --src <canopy>/src [--trials 20] [--burn 0] [--deadline 60]
"""

import argparse
import json
import multiprocessing as mp
import os
import statistics
import subprocess
import sys
import time

PYTHON = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"

CHILD = r"""
import json, sys, time
sys.path.insert(0, ".")
from demo_mode import DemoMode
deadline_s = float(sys.argv[1])
demo = DemoMode(update_interval=0.05)
t0 = time.monotonic()
demo.start()
outcome = "timeout"
try:
    while time.monotonic() - t0 < deadline_s:
        if len(demo.get_network().hidden_units) >= 1:
            outcome = "installed"
            break
        if not demo.is_running:
            outcome = "stopped-without-unit"
            break
        time.sleep(0.01)
finally:
    elapsed = time.monotonic() - t0
    demo.stop()
print(json.dumps({"outcome": outcome, "elapsed_s": round(elapsed, 3), "units": len(demo.get_network().hidden_units)}))
"""


def _burn(seconds: float) -> None:
    end = time.monotonic() + seconds
    x = 0
    while time.monotonic() < end:
        x = (x * 1103515245 + 12345) % 2147483648


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--burn", type=int, default=0, help="busy processes to run alongside")
    ap.add_argument("--deadline", type=float, default=60.0)
    args = ap.parse_args()

    burners = [mp.Process(target=_burn, args=(3600,), daemon=True) for _ in range(args.burn)]
    for p in burners:
        p.start()
    env = dict(os.environ, LIBTORCH="", LD_LIBRARY_PATH="")
    results = []
    try:
        for i in range(args.trials):
            proc = subprocess.run([PYTHON, "-c", CHILD, str(args.deadline)], cwd=args.src, env=env, capture_output=True, text=True, check=False)
            line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                row = {"outcome": "child-error", "stderr_tail": proc.stderr.strip()[-400:]}
            row["trial"] = i
            results.append(row)
            print(json.dumps(row), flush=True)
    finally:
        for p in burners:
            p.terminate()

    outcomes = {}
    for r in results:
        outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
    times = [r["elapsed_s"] for r in results if r["outcome"] == "installed"]
    summary = {"trials": len(results), "burn_procs": args.burn, "outcomes": outcomes}
    if times:
        summary.update({"install_s_min": min(times), "install_s_median": statistics.median(times), "install_s_max": max(times)})
    print("SUMMARY " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
