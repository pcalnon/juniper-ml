"""
Run a list of top-level unittest suites, one process each, a few at a time, and summarize.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier, round-2 validation (corrections and their blast radius)

Usage (from the validator's own worktree root):
    python3 util/ad-hoc/2026-11-07_flood4_val_round2_run_suites.py OUT_DIR JOBS SUITE [SUITE ...]

Each suite runs as `python3 -m unittest <suite>` (the interpreter running this script);
its combined output goes to OUT_DIR/<suite name>.log. A summary with each suite's exit
status and unittest's "Ran N tests" / "OK" / "FAILED" line goes to OUT_DIR/summary.txt.
"""

from __future__ import annotations

import concurrent.futures
import re
import subprocess  # nosec B404 -- fixed argv
import sys
import time
from pathlib import Path


def _run(out_dir: Path, suite: str) -> tuple[str, int, str, float]:
    start = time.monotonic()
    proc = subprocess.run([sys.executable, "-m", "unittest", suite], capture_output=True, text=True, check=False, timeout=1800)  # nosec B603
    elapsed = time.monotonic() - start
    text = proc.stdout + proc.stderr
    (out_dir / (Path(suite).name + ".log")).write_text(text, encoding="utf-8")
    ran = re.findall(r"^Ran (\d+) tests? in", text, re.MULTILINE)
    verdict = re.findall(r"^(OK.*|FAILED.*)$", text, re.MULTILINE)
    return suite, proc.returncode, f"ran={ran[-1] if ran else '?'} {verdict[-1] if verdict else '?'}", elapsed


def main(argv: list[str]) -> int:
    out_dir = Path(argv[0])
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = int(argv[1])
    suites = argv[2:]
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(lambda s: _run(out_dir, s), suites):
            rows.append(row)
    failed = [r for r in rows if r[1] != 0]
    total = 0
    for _, _, info, _ in rows:
        m = re.match(r"ran=(\d+)", info)
        total += int(m.group(1)) if m else 0
    lines = [f"{'FAIL' if rc else 'ok  '} rc={rc} {elapsed:6.1f}s {suite} {info}" for suite, rc, info, elapsed in rows]
    lines.append(f"suites={len(rows)} failed={len(failed)} tests_ran={total} interpreter={sys.executable} {sys.version.split()[0]}")
    text = "\n".join(lines) + "\n"
    (out_dir / "summary.txt").write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
