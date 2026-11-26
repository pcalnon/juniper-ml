"""
From each CI job log of a failed juniper-canopy X7 health test, read the captured-log timestamps of the test's setup,
its ten /v1/health/live answers and its three /api/status answers, and report where the stall sat.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26) (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
    section 8); flood-4 session 16 builder r49; logs fetched by util/ad-hoc/2026-11-26_flood4_s16_r49_ci_census.py

Usage:
    python3 -I <this file> --census-dir <dir with health_failures.json and logs/> [--out <json>]
For each health failure it parses the failure block's "Captured stderr setup" / "Captured stderr call" lines (the
app's own log format, "YYYY-MM-DD HH:MM:SS,mmm [LEVEL] ..."), and reports: probes answered after setup (min, max),
the spread of the ten probe answers, and the drivers' answers after the last probe. Drivers answering about one stub
sleep (2.0 s) after the probes mean the stall came before the drivers' upstream sleep had begun.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

APP_TS = re.compile(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) \[(\w+)\] (.*)$")
BLOCK_START = "TestLoopStaysAnswerable.test_health_stays_fast_while_upstream_is_slow"


def parse_ts(text: str) -> dt.datetime:
    return dt.datetime.strptime(text, "%Y-%m-%d %H:%M:%S,%f")


def shape(log: str) -> dict:
    lines = log.splitlines()
    start = next((i for i, line in enumerate(lines) if BLOCK_START in line and "____" in line), None)
    if start is None:
        return {"error": "failure block not found"}
    setup = None
    probes, drivers = [], []
    section = None
    for line in lines[start + 1 :]:
        if "Captured stderr setup" in line:
            section = "setup"
            continue
        if "Captured stderr call" in line:
            section = "call"
            continue
        if "Captured log" in line or (line.rstrip().endswith("_") and "____" in line):
            if section == "call":
                break
            section = None
            continue
        match = APP_TS.search(line)
        if not match:
            continue
        stamp = parse_ts(match.group(1))
        if section == "setup" and setup is None:
            setup = stamp
        elif section == "call":
            if "/v1/health/live" in match.group(3):
                probes.append(stamp)
            elif "/api/status" in match.group(3):
                drivers.append(stamp)
    if setup is None or not probes or not drivers:
        return {"error": "timestamps not found", "probes": len(probes), "drivers": len(drivers)}
    return {
        "probes": len(probes),
        "drivers": len(drivers),
        "probes_after_setup_s": [round((min(probes) - setup).total_seconds(), 3), round((max(probes) - setup).total_seconds(), 3)],
        "probe_spread_s": round((max(probes) - min(probes)).total_seconds(), 3),
        "drivers_after_last_probe_s": [round((min(drivers) - max(probes)).total_seconds(), 3), round((max(drivers) - max(probes)).total_seconds(), 3)],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census-dir", required=True)
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = Path(args.census_dir)
    failures = json.loads((root / "health_failures.json").read_text(encoding="utf-8"))["health_failures"]
    results = []
    for failure in failures:
        log = (root / "logs" / f"job_{failure['job']}.log").read_text(encoding="utf-8", errors="replace")
        results.append({"job": failure["job"], "python": failure["python"], "image": f"{failure['image']} {failure['image_version']}", "latency_s": failure["health_latency_s"], **shape(log)})
    for result in results:
        print(json.dumps(result))
    if args.out:
        Path(args.out).write_text(json.dumps(results, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
