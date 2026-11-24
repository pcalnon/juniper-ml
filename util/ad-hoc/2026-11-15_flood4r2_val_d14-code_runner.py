"""
Run a list of test jobs, at most four at a time, each with the arc's run environment, and summarise them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (flood-4 round-2 validation, D-14 code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 disposition, D-14 (service-core resume cursor rules + shared answer table)

Usage: python3 <this file> --spec <jobs.json> --logs <dir> --out <summary.json> [--workers 4]
jobs.json: [{"name": ..., "cwd": ..., "argv": [...], "env": {...optional overrides...}, "timeout": 900}]
Every job runs with the six Sentry DSN variables set to "" and DBUS_SESSION_BUS_ADDRESS pointing at no bus, and
without JUNIPER_CASCOR_LOG_DIR. Nothing in the environment is printed.
"""

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
SUMMARY = re.compile(r"=+ (.*(passed|failed|error|skipped|no tests ran).*) =+|^(\d+ (passed|failed).*)$|^(Ran \d+ tests? in .*)$|^(OK.*|FAILED.*)$", re.MULTILINE)


def run_job(job: dict, logs: Path) -> dict:
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus"}
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    env.update(job.get("env", {}))
    log = logs / f"{job['name']}.log"
    started = time.monotonic()
    with open(log, "w", encoding="utf-8") as handle:
        try:
            proc = subprocess.run(job["argv"], cwd=job["cwd"], env=env, stdout=handle, stderr=subprocess.STDOUT, timeout=job.get("timeout", 900), check=False)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
    seconds = round(time.monotonic() - started, 1)
    with open(log, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    found = [next(group for group in match.groups() if group) for match in SUMMARY.finditer(text)]
    return {"name": job["name"], "exit": code, "seconds": seconds, "summary": found[-2:] if found else [], "log": str(log)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    with open(args.spec, encoding="utf-8") as handle:
        jobs = json.load(handle)
    args.logs.mkdir(parents=True, exist_ok=True)
    workers = max(1, min(args.workers, 4))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda job: run_job(job, args.logs), jobs))
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
        handle.write("\n")
    for row in results:
        print(f"{row['name']}\texit={row['exit']}\t{row['seconds']}s\t{' | '.join(row['summary'])}")
    return 0 if all(row["exit"] == 0 for row in results) else 1


if __name__ == "__main__":
    sys.exit(main())
