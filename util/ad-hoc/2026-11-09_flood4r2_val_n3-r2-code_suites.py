"""
Run juniper-cascor's unit suite (with coverage, as CI does) and its integration lane on the N-3 round-2 carrier copy
and on a pristine origin/main control, sequentially, and record JUnit-derived counts for each.

Independent validator (code lens) of the flood-4 round-2 N-3 carrier (juniper-cascor websocket resume losses). Runs
ONLY in the validator's own worktrees (a copy of the carrier's changed files over origin/main 7640d420, and a pristine
7640d420 control); never in the carrier. Output goes to the validator's scratch directory.

Usage:
    python3 2026-11-09_flood4r2_val_n3-r2-code_suites.py [--workers N] [--only LABEL ...]

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
import time
import xml.etree.ElementTree as ET
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
WORKTREES = JUNIPER / "worktrees"
CARRIER_COPY = WORKTREES / "juniper-cascor--val--flood4r2-n3-r2-code--20261109-0916--7640d420"
MAIN_CONTROL = WORKTREES / "juniper-cascor--val--flood4r2-n3-r2-code-main--20261109-0916--7640d420"
OUT = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert" / "tmp" / "flood4r2-val" / "n3-r2-code-lens" / "suites"
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"


def junit_counts(path: Path) -> dict:
    if not path.exists():
        return {"present": False}
    root = ET.parse(path).getroot()
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    failed = []
    for case in root.iter("testcase"):
        counts["tests"] += 1
        if case.find("failure") is not None:
            counts["failures"] += 1
        elif case.find("error") is not None:
            counts["errors"] += 1
        elif case.find("skipped") is not None:
            counts["skipped"] += 1
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(f"{case.get('classname')}::{case.get('name')}")
    counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    counts["failed_ids"] = sorted(failed)
    return {"present": True, **counts}


def run_phase(label: str, tree: Path, workers: int, integration: bool) -> dict:
    pyc = OUT / f"pycache-{label}"
    basetemp = OUT / f"basetemp-{label}"
    for stale in (pyc, basetemp):
        if stale.exists():
            shutil.rmtree(stale)
    pyc.mkdir(parents=True)
    junit = OUT / f"junit-{label}.xml"
    env = dict(os.environ)
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = str(pyc)
    cmd = [PYTHON, "-m", "pytest", "-p", "no:cacheprovider", "--timeout=60", f"--junitxml={junit}", f"--basetemp={basetemp}", "-q", "-rfE"]
    if integration:
        cmd += ["--integration", "-m", "integration and not slow", "src/tests/integration"]
    else:
        (tree / "src" / "tests" / "reports").mkdir(parents=True, exist_ok=True)
        cmd += ["-m", "unit and not slow", "--cov=src", "--cov-report=", "src/tests/unit"]
    if workers:
        cmd += ["-n", str(workers)]
    started = time.time()
    with open(OUT / f"{label}.log", "w", encoding="utf-8") as log:
        log.write(f"$ (cwd {tree}) env -u JUNIPER_CASCOR_LOG_DIR {shlex.join(cmd)}\n")
        log.flush()
        rc = subprocess.run(cmd, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    summary = {"label": label, "tree": str(tree), "command": shlex.join(cmd), "exit_status": rc, "seconds": round(time.time() - started, 1), "counts": junit_counts(junit)}
    if not integration:
        report = subprocess.run([PYTHON, "-m", "coverage", "report", "--fail-under=80"], cwd=tree, env=env, capture_output=True, text=True)
        (OUT / f"{label}.coverage.txt").write_text(report.stdout + report.stderr, encoding="utf-8")
        summary["coverage_gate_exit_status"] = report.returncode
        changed = subprocess.run(
            [PYTHON, "-m", "coverage", "report", "-m", "--include=*/api/websocket/manager.py,*/api/websocket/training_stream.py,*/api/observability.py"],
            cwd=tree,
            env=env,
            capture_output=True,
            text=True,
        )
        (OUT / f"{label}.coverage-changed-files.txt").write_text(changed.stdout + changed.stderr, encoding="utf-8")
    (OUT / f"{label}.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    c = summary["counts"]
    print(f"{label}: exit {rc}, {c.get('passed')} passed, {c.get('failures')} failed, {c.get('errors')} errors, {c.get('skipped')} skipped of {c.get('tests')} ({summary['seconds']}s)", flush=True)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    if args.workers > 4:
        raise SystemExit("parallelism is capped at 4 workers")
    OUT.mkdir(parents=True, exist_ok=True)
    phases = [
        ("unit-carrier-cov", CARRIER_COPY, False),
        ("unit-main-cov", MAIN_CONTROL, False),
        ("integration-carrier", CARRIER_COPY, True),
        ("integration-main", MAIN_CONTROL, True),
    ]
    results = {}
    for label, tree, integration in phases:
        if args.only and label not in args.only:
            continue
        results[label] = run_phase(label, tree, args.workers, integration)
    (OUT / "suites-summary.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
