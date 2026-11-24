#!/usr/bin/env python3
"""
Run named unittest suites in one or more juniper-ml trees, one process per suite and at most four at a time, and
record each suite's exit, test count and failing test ids.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (Cursor flood-4 session 8: the ml-docs carrier's claims-lens validation, check F)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/ml-docs-s8/ (the validator's deliverables)

Every child gets the six Sentry DSN variables set to the empty string and a session bus that does not exist, as
the arc's binding rules require; the caller puts the working interpreter first on PATH (runenv.bash does).

Usage:
  2026-11-14_flood4r2_val_ml-docs_suites.py --tree <label>=<dir> [--tree ...] --suites <file> --out <report.json>
"""

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
RAN_RE = re.compile(r"^Ran (\d+) tests?", re.MULTILINE)
FAIL_RE = re.compile(r"^(FAIL|ERROR): (\S+) \(([^)]+)\)", re.MULTILINE)


def run_one(label: str, tree: Path, suite: str) -> dict:
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus", "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        done = subprocess.run([sys.executable, "-m", "unittest", "-v", suite], cwd=str(tree), env=env, capture_output=True, text=True, timeout=1200, check=False)
        out = done.stdout + done.stderr
        code = done.returncode
    except subprocess.TimeoutExpired:
        out, code = "TIMEOUT", -9
    ran = RAN_RE.search(out)
    return {"tree": label, "suite": suite, "exit": code, "ran": int(ran.group(1)) if ran else None, "failing": sorted(f"{m.group(3)}.{m.group(2)}" for m in FAIL_RE.finditer(out)), "tail": out[-600:] if code != 0 else ""}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", action="append", required=True)
    ap.add_argument("--suites", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    suites = [s.strip() for s in Path(args.suites).read_text(encoding="utf-8").split() if s.strip()]
    jobs = []
    for spec in args.tree:
        label, path = spec.split("=", 1)
        jobs += [(label, Path(path), suite) for suite in suites]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda job: run_one(*job), jobs))
    Path(args.out).write_text(json.dumps({"interpreter": sys.version, "executable": sys.executable, "rows": rows}, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        print(row["tree"], row["exit"], row["ran"], row["suite"], " ".join(row["failing"])[:200])
    bad = [r for r in rows if r["exit"] != 0]
    print(f"{len(rows) - len(bad)}/{len(rows)} suite runs passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
