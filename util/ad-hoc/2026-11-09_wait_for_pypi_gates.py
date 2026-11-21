#!/usr/bin/env python3
"""Wait until each named release is served by PyPI and its publish run's PyPI job succeeded.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use; R-OBS-SC-2's two `pypi` gates, 2026-11-09)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Why
---
The second lock round needs juniper-observability 0.4.2 and juniper-service-core 0.7.2 on PyPI.
Both sat at the owner's ``pypi`` gate. This polls, and never approves anything: approval is the
owner's alone. "Done" is two facts per release, because either alone misleads: the run's
``Publish to PyPI`` job concluded ``success``, and ``/pypi/<pkg>/<ver>/json`` answers 200 (the
per-version endpoint; the aggregate ``/pypi/<pkg>/json`` lags behind the CDN).

It prints one line per state change, with a UTC timestamp, so its output dates the approval.
Exit 0 when every release is done; 1 as soon as any PyPI job concludes other than ``success``
(failure, cancelled, skipped); 2 at ``--timeout`` with the last state of each.

Usage:
    python3 util/ad-hoc/2026-11-09_wait_for_pypi_gates.py \
        --release 42499466753:juniper-service-core:0.7.2 \
        --release 42500706778:juniper-observability:0.4.2 [--interval 30] [--timeout 3300]
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
import time
import urllib.error
import urllib.request

REPO = "pcalnon/juniper-ml"
JOB = "Publish to PyPI"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _job_state(run_id: str) -> str:
    proc = subprocess.run(["gh", "api", f"repos/{REPO}/actions/runs/{run_id}/jobs"], capture_output=True, text=True)  # nosec B603 B607
    if proc.returncode != 0:
        return "gh-error"
    for job in json.loads(proc.stdout).get("jobs", []):
        if job.get("name") == JOB:
            return f"{job.get('status')}/{job.get('conclusion')}"
    return "no-job"


def _pypi_code(package: str, version: str) -> int:
    request = urllib.request.Request(f"https://pypi.org/pypi/{package}/{version}/json", method="GET")  # noqa: S310 -- fixed https host
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # nosec B310
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (urllib.error.URLError, TimeoutError):
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--release", action="append", required=True, help="RUN_ID:PACKAGE:VERSION (repeatable)")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=3300)
    args = parser.parse_args()
    releases = [tuple(item.split(":", 2)) for item in args.release]
    last: dict[str, str] = {}
    deadline = time.monotonic() + args.timeout
    while True:
        done = 0
        for run_id, package, version in releases:
            job = _job_state(run_id)
            code = _pypi_code(package, version)
            state = f"job {job}, PyPI {code}"
            key = f"{package} {version}"
            if last.get(key) != state:
                print(f"{_now()} {key} (run {run_id}): {state}", flush=True)
                last[key] = state
            if job.startswith("completed/") and job != "completed/success":
                print(f"{_now()} STOP: {key}'s {JOB} job ended {job}", flush=True)
                return 1
            if job == "completed/success" and code == 200:
                done += 1
        if done == len(releases):
            print(f"{_now()} ALL SERVED: every release's {JOB} job succeeded and PyPI answers 200", flush=True)
            return 0
        if time.monotonic() >= deadline:
            print(f"{_now()} TIMEOUT after {args.timeout}s; last states: {json.dumps(last)}", flush=True)
            return 2
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
