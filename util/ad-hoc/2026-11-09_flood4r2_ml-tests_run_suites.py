#!/usr/bin/env python3
"""
Run regression suites one process per suite, in parallel, in a chosen tree, then re-run each failure alone.

A copy of `2026-11-08_flood4r2_ml_code_run_suites.py` (itself round 1's parallel runner) with three additions:
  * `--root` runs the suites in another checkout (the clean-main baseline, or the main + ml-code overlay);
  * a `juniper-ci-tools/tests/...` suite runs as CI's `ci-ci-tools.yml` does, under pytest from inside
    `juniper-ci-tools/`, so the tree's source is imported and not an installed juniper-ci-tools;
  * every suite's full output is kept, one log per suite, under `--logs`, and a JSON summary beside the report.
Each `tests/...` suite is its own `python3 -m unittest -v <suite>` process, as CI runs it. A suite that fails in
the parallel pass is re-run ALONE, and only a failure that repeats there is reported as a failure.

Usage: 2026-11-09_flood4r2_ml-tests_run_suites.py [--root DIR] [--workflow .github/workflows/ci.yml]
       [--only SUITE ...] [--jobs 4] [--timeout 900] --out FILE --logs DIR

Exit 0 if every suite passed (in either pass), 1 if any failed alone, 2 if no suite was found.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_flood4_run_ci_regression_suites_parallel.py (round 1's runner)
"""

import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_SUITE_RE = re.compile(r"python3 -m unittest -v (tests/[A-Za-z0-9_./-]+\.py)")
_CI_TOOLS = "juniper-ci-tools/"


def _argv_and_cwd(root: Path, suite: str) -> tuple:
    if suite.startswith(_CI_TOOLS):
        return [sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider", suite[len(_CI_TOOLS) :]], root / "juniper-ci-tools"
    return [sys.executable, "-m", "unittest", "-v", suite], root


def _run(root: Path, logs: Path, suite: str, timeout: int, tag: str) -> dict:
    argv, cwd = _argv_and_cwd(root, suite)
    started = time.monotonic()
    try:
        proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603 -- fixed argv
        rc, out = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        rc, out = 124, f"TIMEOUT after {timeout}s"
    log = logs / (suite.replace("/", "__") + f".{tag}.log")
    log.write_text(out, encoding="utf-8")
    ran = re.findall(r"^Ran (\d+) tests? in", out, re.M) or re.findall(r"(\d+) passed", out)
    return {"suite": suite, "rc": rc, "ok": rc == 0, "ran": int(ran[-1]) if ran else None, "secs": round(time.monotonic() - started, 1), "log": str(log), "tail": out.strip().splitlines()[-12:]}


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--workflow", default=".github/workflows/ci.yml")
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--out", required=True)
    ap.add_argument("--logs", required=True)
    args = ap.parse_args(argv)
    root, logs = Path(args.root).resolve(), Path(args.logs)
    logs.mkdir(parents=True, exist_ok=True)
    if args.only:
        suites = list(dict.fromkeys(args.only))
    else:
        suites = sorted(set(_SUITE_RE.findall((root / args.workflow).read_text(encoding="utf-8"))))
    if not suites:
        print("no suites", file=sys.stderr)
        return 2
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        first = list(pool.map(lambda s: _run(root, logs, s, args.timeout, "parallel"), suites))
    failed = [r for r in first if not r["ok"]]
    lines = [f"root: {root}", f"interpreter: {sys.executable} ({sys.version.split()[0]})", f"PARALLEL PASS (--jobs {args.jobs}): {len(suites) - len(failed)} passed, {len(failed)} failed, of {len(suites)} suites ({time.monotonic() - started:.0f}s)"]
    alone = []
    for r in failed:
        lines.append(f"  parallel FAIL {r['suite']} rc={r['rc']} ({r['secs']}s)\n      " + "\n      ".join(r["tail"]))
        again = _run(root, logs, r["suite"], args.timeout, "alone")
        lines.append(f"  re-run ALONE {r['suite']}: {'pass' if again['ok'] else 'FAIL'} rc={again['rc']} ({again['secs']}s)")
        if not again["ok"]:
            alone.append(again)
    lines.append(f"FINAL: {len(suites) - len(alone)} passed, {len(alone)} failed alone, of {len(suites)} suites ({time.monotonic() - started:.0f}s)")
    lines += [f"FAIL {r['suite']}" for r in alone]
    report = "\n".join(lines)
    print(report)
    Path(args.out).write_text(report + "\n", encoding="utf-8")
    with open(Path(args.out).with_suffix(".json"), "w", encoding="utf-8") as fh:
        json.dump({"root": str(root), "suites": first, "failed_alone": [r["suite"] for r in alone]}, fh, indent=2)
    return 1 if alone else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
