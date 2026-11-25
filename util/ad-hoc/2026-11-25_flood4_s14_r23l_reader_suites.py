"""
Run the juniper-ml root regression suites that read a changed path, each as ci.yml runs it, and report per suite.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — one-off verification (flood-4 session 14, builder r23l)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23);
         util/ad-hoc/2026-11-09_flood4r2_n2_reader_suites.py (juniper-ml#2557, the same step)

Reads a list of suite paths (one ``tests/<file>.py`` per line), checks each is invoked by ci.yml
(``python3 -m unittest -v tests/<file>.py``), and runs each as its own ``<python> -m unittest -v <path>``
process from ``--repo-root``, at most ``--jobs`` at once, each with a timeout. Writes one log per suite under
``--log-dir`` and a JSON summary (suite, in_ci, exit, tests run, failures, errors, skipped, seconds).

Usage: python3 <this file> --repo-root <checkout> --suites <list file> --log-dir <dir> --json-out <file>
       [--python python3] [--jobs 4] [--timeout 900]
Exit: 0 when every suite passed, 1 otherwise.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import time
from pathlib import Path

_RAN = re.compile(r"^Ran (\d+) tests? in ")
_FAILED = re.compile(r"^FAILED \((.*)\)$")
_OK_SKIPPED = re.compile(r"skipped=(\d+)")


def _run_one(python: str, repo_root: Path, suite: str, log_dir: Path, timeout: int) -> dict:
    log = log_dir / (Path(suite).stem + ".log")
    start = time.monotonic()
    try:
        result = subprocess.run([python, "-m", "unittest", "-v", suite], cwd=repo_root, capture_output=True, text=True, timeout=timeout, check=False)
        rc, out = result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out = -1, f"TIMEOUT after {timeout}s\n{exc.stdout or ''}{exc.stderr or ''}"
    seconds = round(time.monotonic() - start, 1)
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(out)
    ran = failures = errors = skipped = 0
    for line in out.splitlines():
        m = _RAN.match(line)
        if m:
            ran = int(m.group(1))
        m = _FAILED.match(line.strip())
        if m:
            parts = dict(p.split("=") for p in m.group(1).split(", ") if "=" in p)
            failures, errors = int(parts.get("failures", 0)), int(parts.get("errors", 0))
            skipped = int(parts.get("skipped", 0))
        elif line.startswith("OK"):
            m2 = _OK_SKIPPED.search(line)
            skipped = int(m2.group(1)) if m2 else 0
    return {"suite": suite, "exit": rc, "ran": ran, "failures": failures, "errors": errors, "skipped": skipped, "seconds": seconds, "log": str(log)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--suites", required=True, type=Path)
    parser.add_argument("--log-dir", required=True, type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--python", default="python3")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)
    args.log_dir.mkdir(parents=True, exist_ok=True)
    with open(args.suites, encoding="utf-8") as fh:
        suites = [line.strip() for line in fh if line.strip()]
    with open(args.repo_root / ".github" / "workflows" / "ci.yml", encoding="utf-8") as fh:
        ci = fh.read()
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.jobs, 4))) as pool:
        futures = {pool.submit(_run_one, args.python, args.repo_root, s, args.log_dir, args.timeout): s for s in suites}
        for fut in concurrent.futures.as_completed(futures):
            row = fut.result()
            row["in_ci"] = f"python3 -m unittest -v {row['suite']}" in ci
            rows.append(row)
            print(f"{row['suite']}\texit {row['exit']}\tran {row['ran']}\tF {row['failures']}\tE {row['errors']}\tskip {row['skipped']}\t{row['seconds']}s\tin_ci {row['in_ci']}", flush=True)
    rows.sort(key=lambda r: r["suite"])
    with open(args.json_out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)
    bad = [r for r in rows if r["exit"] != 0]
    print(f"RESULT: {len(rows)} suites, {sum(r['ran'] for r in rows)} tests, {sum(r['skipped'] for r in rows)} skipped; {len(rows) - len(bad)} passed, {len(bad)} failed: {[r['suite'] for r in bad]}")
    print(f"not invoked by ci.yml: {[r['suite'] for r in rows if not r['in_ci']]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
