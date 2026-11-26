"""
Run juniper-canopy tests for the r49 code lens behind the r27-val-code2 connect fence, with the r49v_stall plugin
loaded and configured, then summarise its verdict records.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26), a follow-up of ruling 28
    (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8); flood-4 session 16, code lens
    r49-val-code. Uses util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py (runner) and its census (fence),
    util/ad-hoc/2026-11-26_flood4_s16_r49-val-code_stall.py (plugin) and ..._summarize.py (summary).

Usage:
    python <this file> --adhoc <util/ad-hoc dir> --python <venv python> --tree <canopy tree> --out <dir> --label <name>
        [--stall S] [--at probe,driver,worker,release] [--mech gil|gc|loop] [--heap-m M] [--repeat N] [--only SUBSTR]
        [--cov] [--maxfail] [--count N] [--env K=V ...] -- <pytest targets and args>

Every run goes through the runner, so pytest and every child Python process refuse connects to the Juniper ports
(8050-8059, 8100, 8200-8211) and to any local port listening at the start. The runner's own CI-like environment
applies (Sentry variables empty, JUNIPER_/CASCOR_/CANOPY_ variables dropped).
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - runs the lane runner and the summariser under chosen interpreters
import sys
from pathlib import Path

RUNNER = "2026-11-25_flood4_s14_r27-val-code2_run_lane.py"
CENSUS = "2026-11-25_flood4_s14_r27-val-code2_census.py"
PLUGIN = "2026-11-26_flood4_s16_r49-val-code_stall.py"
SUMMARY = "2026-11-26_flood4_s16_r49-val-code_summarize.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adhoc", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--stall", default="0")
    parser.add_argument("--at", default="probe")
    parser.add_argument("--mech", default="gil")
    parser.add_argument("--heap-m", default="0")
    parser.add_argument("--repeat", default="1")
    parser.add_argument("--only", default="test_health_stays_fast_while_upstream_is_slow")
    parser.add_argument("--cov", action="store_true")
    parser.add_argument("--maxfail", action="store_true")
    parser.add_argument("--count", default="1")
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    adhoc, out = Path(args.adhoc).resolve(), Path(args.out).resolve()
    plugins = out / "plugins"
    plugins.mkdir(parents=True, exist_ok=True)
    link = plugins / "r49v_stall.py"
    if not link.exists():
        link.symlink_to(adhoc / PLUGIN)
    prefix = out / args.label
    stale = Path(str(prefix) + ".r49v.jsonl")
    if stale.exists():
        stale.unlink()
    targets = [a for a in args.rest if a != "--"]
    command = [sys.executable, str(adhoc / RUNNER), "--python", args.python, "--tree", args.tree, "--out", str(out), "--label", args.label, "--census", str(adhoc / CENSUS), "--count", args.count]
    if not args.cov:
        command.append("--no-cov")
    if not args.maxfail:
        command.append("--no-maxfail")
    settings = {"R49V_OUT": str(prefix), "R49V_STALL_S": args.stall, "R49V_AT": args.at, "R49V_MECH": args.mech, "R49V_HEAP_M": args.heap_m, "R49V_REPEAT": args.repeat, "R49V_ONLY": args.only}
    for key, value in settings.items():
        command += ["--env", f"{key}={value}"]
    for pair in args.env:
        command += ["--env", pair]
    command += ["--", "-p", "r49v_stall", *targets]
    with open(out / f"{args.label}.launch.json", "w", encoding="utf-8") as handle:
        json.dump({"command": command, "settings": settings}, handle, indent=1)
    runner = subprocess.run(command, check=False)  # nosec B603 - fixed argv, no shell
    if stale.exists():
        subprocess.run([sys.executable, str(adhoc / SUMMARY), "--json", str(prefix) + ".summary_r49v.json", str(stale)], check=False)  # nosec B603
    else:
        print(json.dumps({"label": args.label, "r49v_records": "none written"}))
    return runner.returncode


if __name__ == "__main__":
    sys.exit(main())
