"""
Run one pytest lane against a juniper-cascor tree for the N-3 round-2 fix-up and record its exact command, exit status
and JUnit counts.

The environment is the one cascor's AGENTS.md asks for: the JuniperCascor1 interpreter, JUNIPER_CASCOR_LOG_DIR unset,
no bytecode written (a fresh, empty PYTHONPYCACHEPREFIX per run, so a mutant is never served stale bytecode) and no
cache provider. TMPDIR is left as the session set it. Every output (log, JUnit XML, basetemp, summary JSON) goes under
--out-dir, which must be the carrier worktree's tmp/flood4-fix/n3-r2/ or a directory below it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"


def junit_counts(path: Path) -> dict:
    """Counts by <testcase> element (one per test id), plus the ids of failed / errored tests.

    The <testsuite> ``tests`` attribute also counts subtest reports, so it can exceed the number of test ids; it is
    kept separately as ``suite_tests_attribute``.
    """
    if not path.exists():
        return {"present": False}
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    failed = []
    for case in root.iter("testcase"):
        totals["tests"] += 1
        if case.find("failure") is not None:
            totals["failures"] += 1
        elif case.find("error") is not None:
            totals["errors"] += 1
        elif case.find("skipped") is not None:
            totals["skipped"] += 1
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(f"{case.get('classname')}::{case.get('name')}")
    totals["passed"] = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    suite_attr = sum(int(suite.get("tests", 0)) for suite in suites)
    return {"present": True, **totals, "suite_tests_attribute": suite_attr, "failed_ids": sorted(failed)}


def recount(summary_path: Path) -> int:
    """Re-derive ``counts`` in an existing summary JSON from its own JUnit file (no test is re-run)."""
    with open(summary_path, encoding="utf-8") as fh:
        summary = json.load(fh)
    summary["counts"] = junit_counts(Path(summary["junit"]))
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    c = summary["counts"]
    print(f"{summary['label']}: recounted {c['passed']} passed, {c['failures']} failed, {c['errors']} errors, {c['skipped']} skipped of {c['tests']} test ids")
    return 0


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--recount":
        return recount(Path(sys.argv[2]))
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True, help="the cascor worktree to run in")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--marker", default="unit and not slow")
    ap.add_argument("--workers", type=int, default=0, help="xdist workers; 0 runs without xdist (cap: 4)")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--integration", action="store_true")
    ap.add_argument("--cov", action="store_true", help="--cov=src as CI does, then coverage report")
    ap.add_argument("--count", type=int, default=0, help="pytest-repeat --count")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()
    if args.workers > 4:
        raise SystemExit("parallelism is capped at 4 workers")
    tree = Path(args.tree)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pyc = out / f"pycache-{args.label}"
    basetemp = out / f"basetemp-{args.label}"
    for stale in (pyc, basetemp):
        if stale.exists():
            shutil.rmtree(stale)
    pyc.mkdir(parents=True)
    junit = out / f"junit-{args.label}.xml"
    env = dict(os.environ)
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = str(pyc)
    cmd = [PYTHON, "-m", "pytest", "-p", "no:cacheprovider", "-m", args.marker, f"--timeout={args.timeout}", f"--junitxml={junit}", f"--basetemp={basetemp}", "-q", "-rfE"]
    if args.integration:
        cmd.append("--integration")
    if args.workers:
        cmd += ["-n", str(args.workers)]
    if args.count:
        cmd += [f"--count={args.count}"]
    if args.cov:
        (tree / "src" / "tests" / "reports").mkdir(parents=True, exist_ok=True)
        cmd += ["--cov=src", "--cov-report="]
    cmd += args.paths
    started = time.time()
    with open(out / f"{args.label}.log", "w", encoding="utf-8") as log:
        log.write("$ (cwd " + str(tree) + ") env -u JUNIPER_CASCOR_LOG_DIR PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=" + str(pyc) + " " + shlex.join(cmd) + "\n")
        log.flush()
        rc = subprocess.run(cmd, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    summary = {
        "label": args.label,
        "tree": str(tree),
        "command": "env -u JUNIPER_CASCOR_LOG_DIR PYTHONDONTWRITEBYTECODE=1 " + shlex.join(cmd),
        "interpreter": PYTHON,
        "exit_status": rc,
        "seconds": round(time.time() - started, 1),
        "load_average_end": os.getloadavg(),
        "junit": str(junit),
        "counts": junit_counts(junit),
        "log": str(out / f"{args.label}.log"),
    }
    if args.cov:
        report = subprocess.run([PYTHON, "-m", "coverage", "report", "--fail-under=80"], cwd=tree, env=env, capture_output=True, text=True)
        with open(out / f"{args.label}.coverage.txt", "w", encoding="utf-8") as fh:
            fh.write(report.stdout + report.stderr)
        summary["coverage_gate_exit_status"] = report.returncode
        summary["coverage_report"] = str(out / f"{args.label}.coverage.txt")
    with open(out / f"{args.label}.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    c = summary["counts"]
    print(f"{args.label}: exit {rc}; {c.get('passed')} passed, {c.get('failures')} failed, {c.get('errors')} errors, {c.get('skipped')} skipped ({summary['seconds']} s)")
    for failed in c.get("failed_ids", [])[:40]:
        print("  FAILED", failed)
    return rc


if __name__ == "__main__":
    sys.exit(main())
