#!/usr/bin/env python3
"""
Run CI's regression-suite list (or an explicit subset) locally, several suites at a time, then re-run every failure alone.

A copy of `2026-11-07_flood4_run_ci_regression_suites_parallel.py` with one addition: `--only` runs the named
suites instead of the workflow's list (the carrier's touched suites). Each suite is still its own
`python3 -m unittest <suite>` process, exactly as CI runs it; only the scheduling differs. Every suite
that fails in the parallel pass is re-run ALONE afterwards, and only a failure that repeats there is
reported as a failure. Both passes are written to the report, with each suite's runtime.

Usage: 2026-11-08_flood4r2_ml_code_run_suites.py [--workflow .github/workflows/ci.yml] [--only tests/a.py ...]
       [--jobs 6] [--timeout 900] --out FILE

Run from the repository root. Exit 0 if every suite passed (in either pass), 1 if any failed alone,
2 if no suite was found.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 round-2 ml-code carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_flood4_run_ci_regression_suites_parallel.py (the original)
"""

import argparse
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_SUITE_RE = re.compile(r"python3 -m unittest -v (tests/[A-Za-z0-9_./-]+\.py)")


def _run(suite: str, timeout: int) -> tuple:
    started = time.monotonic()
    try:
        proc = subprocess.run([sys.executable, "-m", "unittest", suite], capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603 -- fixed argv
        ok, tail = proc.returncode == 0, (proc.stdout + proc.stderr).strip().splitlines()[-15:]
    except subprocess.TimeoutExpired:
        ok, tail = False, [f"TIMEOUT after {timeout}s"]
    return suite, ok, tail, time.monotonic() - started


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workflow", default=".github/workflows/ci.yml")
    ap.add_argument("--only", nargs="*", default=None, help="run these suites instead of the workflow's list")
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=900, help="per-suite timeout in seconds")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.only:
        suites = list(dict.fromkeys(args.only))
    else:
        suites = sorted(set(_SUITE_RE.findall(Path(args.workflow).read_text(encoding="utf-8"))))
    if not suites:
        print(f"no `python3 -m unittest -v tests/...` invocations found in {args.workflow}", file=sys.stderr)
        return 2
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        first = list(pool.map(lambda s: _run(s, args.timeout), suites))
    parallel_failures = [row for row in first if not row[1]]
    lines = [f"interpreter: {sys.executable} ({sys.version.split()[0]})"]
    lines.append(f"PARALLEL PASS (--jobs {args.jobs}): {len(suites) - len(parallel_failures)} passed, {len(parallel_failures)} failed, of {len(suites)} suites ({time.monotonic() - started:.0f}s)")
    for suite, ok, tail, secs in first:
        lines.append(f"  {'pass' if ok else 'FAIL'} {suite} ({secs:.0f}s)" + ("" if ok else "\n      " + "\n      ".join(tail)))
    alone_failures = []
    for suite, _ok, _tail, _secs in parallel_failures:
        s, ok, tail, secs = _run(suite, args.timeout)
        lines.append(f"  re-run ALONE {s}: {'pass' if ok else 'FAIL'} ({secs:.0f}s)" + ("" if ok else "\n      " + "\n      ".join(tail)))
        if not ok:
            alone_failures.append(s)
    lines.append(f"FINAL: {len(suites) - len(alone_failures)} passed, {len(alone_failures)} failed alone, of {len(suites)} suites ({time.monotonic() - started:.0f}s)")
    lines += [f"FAIL {s}" for s in alone_failures]
    report = "\n".join(lines)
    print(report)
    Path(args.out).write_text(report + "\n", encoding="utf-8")
    return 1 if alone_failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
