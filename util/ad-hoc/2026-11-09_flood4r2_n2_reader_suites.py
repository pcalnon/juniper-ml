#!/usr/bin/env python3
"""Run the ci.yml regression suites that read what the stop-then-start fix changes, one process each.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use verification)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Status:      ad-hoc -- one-off verification
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md;
             adapted from the flood-4 round-1 runner util/ad-hoc/2026-11-07_flood4_run_ci_regression_suites_parallel.py

Reads ``.github/workflows/ci.yml`` under ``--root``, takes every ``python3 -m unittest -v
tests/<suite>.py`` it invokes, and keeps the suites whose source names a path this change touches
(``--pattern``, a regular expression; the default covers ``docs/REFERENCE.md``,
``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md``, the two ``CHANGELOG.md`` files,
``juniper-service-core`` and ``util/ad-hoc``). Each kept suite runs as its
own ``<python> -m unittest <suite>`` process with ``--root`` as the working directory, as CI runs
it, ``--jobs`` at a time; a suite that fails there is re-run alone, and only a failure that repeats
alone counts. Writes one JSON report.

Exit status: 0 when every kept suite passed, 1 when one failed alone, 2 when none was found.

Usage (from anywhere):
    python3 util/ad-hoc/2026-11-09_flood4r2_n2_reader_suites.py --root <checkout> --python <interpreter> \\
        --out <report.json> [--jobs 4] [--timeout 900]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_SUITE_RE = re.compile(r"python3 -m unittest -v (tests/[A-Za-z0-9_./-]+\.py)")
_DEFAULT_PATTERN = r"REFERENCE\.md|DEVELOPER_CHEATSHEET|CHANGELOG|juniper-service-core|juniper_service_core|util/ad-hoc|ad-hoc/"
_COUNT_RE = re.compile(r"^Ran (\d+) tests? in", re.M)
_SKIP_RE = re.compile(r"skipped=(\d+)")


def _run(python: str, root: Path, suite: str, timeout: int) -> dict[str, object]:
    started = time.monotonic()
    try:
        proc = subprocess.run([python, "-m", "unittest", suite], cwd=root, capture_output=True, text=True, timeout=timeout, check=False)
        output = proc.stdout + proc.stderr
        ok = proc.returncode == 0
    except subprocess.TimeoutExpired:
        output, ok = f"TIMEOUT after {timeout}s", False
    ran = _COUNT_RE.search(output)
    skipped = _SKIP_RE.search(output.splitlines()[-1] if output.splitlines() else "")
    return {"suite": suite, "ok": ok, "tests": int(ran.group(1)) if ran else None, "skipped": int(skipped.group(1)) if skipped else 0, "seconds": round(time.monotonic() - started, 1), "tail": output.strip().splitlines()[-12:]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", required=True, type=Path, help="the juniper-ml checkout to run in")
    parser.add_argument("--python", required=True, help="the interpreter CI's regression job would use")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--pattern", default=_DEFAULT_PATTERN, help="keep suites whose source matches this regex")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=900, help="per-suite timeout in seconds")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    pattern = re.compile(args.pattern)
    suites = sorted({s for s in _SUITE_RE.findall(workflow) if (root / s).is_file() and pattern.search((root / s).read_text(encoding="utf-8"))})
    if not suites:
        print("no suite matched", file=sys.stderr)
        return 2
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        first = list(pool.map(lambda s: _run(args.python, root, s, args.timeout), suites))
    alone = {row["suite"]: _run(args.python, root, row["suite"], args.timeout) for row in first if not row["ok"]}
    failed = sorted(s for s, row in alone.items() if not row["ok"])
    report = {
        "root": str(root),
        "python": args.python,
        "pattern": args.pattern,
        "suites": len(suites),
        "tests": sum(row["tests"] or 0 for row in first),
        "skipped": sum(row["skipped"] for row in first),
        "failed_in_parallel": sorted(alone),
        "failed_alone": failed,
        "rows": first,
        "reruns": list(alone.values()),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print(f"{len(suites)} suites, {report['tests']} tests ({report['skipped']} skipped); failed in parallel {len(alone)}, failed alone {len(failed)}: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
