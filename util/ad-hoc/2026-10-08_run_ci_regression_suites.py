#!/usr/bin/env python3
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  ad-hoc helper (run CI's regression-suite list locally)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
#
# Ad-hoc. CI's regression step runs every suite as its own `python3 -m unittest -v tests/<suite>.py`
# process, from a hand-maintained list in .github/workflows/ci.yml. A repo-wide lint suite judges
# files a change never touched (tests/test_env_repr_safety.py failed ml#2182 that way), so "the
# suites I edited pass" is not the question CI asks. This runs exactly CI's list, one process per
# suite like CI, and reports every failure with the tail of its output.
"""Usage: 2026-10-08_run_ci_regression_suites.py [--workflow .github/workflows/ci.yml] [--timeout 900] [--out FILE]

Run from the repository root. Exit 0 if every suite passed, 1 if any failed, 2 if no suite was found.
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

_SUITE_RE = re.compile(r"python3 -m unittest -v (tests/[A-Za-z0-9_./-]+\.py)")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workflow", default=".github/workflows/ci.yml")
    ap.add_argument("--timeout", type=int, default=900, help="per-suite timeout in seconds")
    ap.add_argument("--out", help="also write the report here")
    args = ap.parse_args(argv)
    suites = sorted(set(_SUITE_RE.findall(Path(args.workflow).read_text(encoding="utf-8"))))
    if not suites:
        print(f"no `python3 -m unittest -v tests/...` invocations found in {args.workflow}", file=sys.stderr)
        return 2
    failures: list[str] = []
    started = time.monotonic()
    for suite in suites:
        try:
            proc = subprocess.run([sys.executable, "-m", "unittest", suite], capture_output=True, text=True, timeout=args.timeout, check=False)  # nosec B603 -- fixed argv
            ok, tail = proc.returncode == 0, (proc.stdout + proc.stderr).strip().splitlines()[-15:]
        except subprocess.TimeoutExpired:
            ok, tail = False, [f"TIMEOUT after {args.timeout}s"]
        if not ok:
            failures.append(f"FAIL {suite}\n    " + "\n    ".join(tail))
    lines = failures + [f"{len(suites) - len(failures)} passed, {len(failures)} failed, of {len(suites)} suites ({time.monotonic() - started:.0f}s)"]
    report = "\n".join(lines)
    print(report)
    if args.out:
        Path(args.out).write_text(report + "\n", encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
