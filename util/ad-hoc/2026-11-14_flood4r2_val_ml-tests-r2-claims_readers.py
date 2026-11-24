"""
Run, in a landed tree, every tests/ suite whose source names one of the documents or workflows the ml-tests carrier
changes, plus the suites it carries, one process per suite, at most --workers at a time (claims lens, session 8).
A suite that fails is run again alone. The juniper-ci-tools suite runs under pytest from juniper-ci-tools/, as its
workflow runs it. The child environment is the caller's (run this under the session-8 runenv wrapper, which empties
the six Sentry variables, points the session bus nowhere and puts the interpreter shim first).

Writes <out>/<suite>.log per suite and <out>/summary.json; prints one line per suite and a total.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 disposition, ml-tests carrier validation (claims lens)
"""

import argparse
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: python -m unittest / pytest of the tree's own suites
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

NAMES = (
    "docs/REFERENCE.md",
    "REFERENCE.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "README.md",
    "pyproject.toml",
    "DEVELOPER_CHEATSHEET",
    "ci.yml",
    "main-verify.yml",
    "HOST_TOOLING",
)
RAN = re.compile(r"^Ran (\d+) tests? in", re.M)
PYTEST = re.compile(r"(\d+) passed")


def run_one(tree: Path, suite: str, out: Path, timeout: int) -> dict:
    if suite.startswith("juniper-ci-tools/"):
        argv = [sys.executable, "-m", "pytest", "-q", suite.split("/", 1)[1]]
        cwd = tree / "juniper-ci-tools"
    else:
        argv = [sys.executable, "-m", "unittest", "-v", suite]
        cwd = tree
    try:
        done = subprocess.run(argv, cwd=str(cwd), capture_output=True, timeout=timeout, env=dict(os.environ), check=False)  # nosec B603
        text = done.stdout.decode(errors="replace") + done.stderr.decode(errors="replace")
        code = done.returncode
    except subprocess.TimeoutExpired:
        text, code = "TIMEOUT", -9
    (out / (suite.replace("/", "__") + ".log")).write_text(text)
    match = RAN.search(text) or PYTEST.search(text)
    return {"suite": suite, "exit": code, "tests": int(match.group(1)) if match else None}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the reader suites in a landed tree.")
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--carried", action="append", default=[])
    parser.add_argument("--carried-file", type=Path, default=None, help="one carried suite path per line")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    if args.carried_file:
        args.carried += [line.strip() for line in args.carried_file.read_text().splitlines() if line.strip()]
    args.out.mkdir(parents=True, exist_ok=True)
    readers = []
    for test in sorted((args.tree / "tests").glob("test_*.py")):
        body = test.read_text(errors="replace")
        if any(name in body for name in NAMES):
            readers.append(str(test.relative_to(args.tree)))
    suites = sorted(set(readers) | set(args.carried))
    print(f"{len(suites)} suites ({len(readers)} readers by name, {len(args.carried)} carried); python {sys.version.split()[0]} {sys.executable}")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda s: run_one(args.tree, s, args.out, args.timeout), suites))
    for row in results:
        if row["exit"] != 0:
            again = run_one(args.tree, row["suite"], args.out, args.timeout)
            row["alone_exit"] = again["exit"]
            row["alone_tests"] = again["tests"]
    failed = [r for r in results if r["exit"] != 0 and r.get("alone_exit", 1) != 0]
    for row in results:
        print(json.dumps(row))
    total = sum(r["tests"] or 0 for r in results)
    print(f"TOTAL suites={len(results)} tests={total} failed_alone={len(failed)}: {[r['suite'] for r in failed]}")
    with (args.out / "summary.json").open("w") as handle:
        json.dump({"suites": results, "readers": readers, "carried": args.carried, "failed_alone": [r["suite"] for r in failed], "tests": total}, handle, indent=1)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
