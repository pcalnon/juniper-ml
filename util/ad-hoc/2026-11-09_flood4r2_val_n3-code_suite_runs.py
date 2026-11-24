"""
Validator n3: the full cascor unit suite on the fix (scratch worktree, Python 3.14), and N separate-process runs of
the fix's new test file.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-cascor fix/ws-resume-losses
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WT =  Path(Path.home(), "Development/python/Juniper/worktrees/juniper-cascor--validate--ws-resume-losses-n3-code--20261109-0324--f3dfee8c")
OUT = Path(Path.home(), "Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert/tmp/flood4r2-val/n3-code-lens")
PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
NEW = "src/tests/unit/api/test_websocket_resume_continuity.py"
EXTRA = "src/tests/unit/api/test_n3_validator_extra.py"


def env() -> dict:
    e = dict(os.environ)
    e.pop("JUNIPER_CASCOR_LOG_DIR", None)
    e["GIT_CEILING_DIRECTORIES"] = str(WT / "tmp")
    # A bytecode prefix of this script's own: no .pyc compiled from a mutant (the mutant runner edits this
    # worktree) can ever be imported here.
    e["PYTHONPYCACHEPREFIX"] = str(WT / "tmp" / "pycache-suite-runs")
    return e


def assert_fix_intact() -> None:
    import hashlib

    frozen = Path(Path.home(), "Development/python/Juniper/worktrees/juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c")
    for rel in ("src/api/websocket/manager.py", "src/api/websocket/training_stream.py", "src/api/observability.py", NEW):
        a = hashlib.sha256((WT / rel).read_bytes()).hexdigest()
        b = hashlib.sha256((frozen / rel).read_bytes()).hexdigest()
        if a != b:
            raise SystemExit(f"scratch {rel} differs from the frozen artifact; refusing to run")


def full_suite(workers: int) -> int:
    bt = WT / "tmp" / "bt-unit"
    xml = OUT / "junit-unit-fix-n3.xml"
    cmd = [PY, "-m", "pytest", "src/tests/unit", "-n", str(workers), "-p", "no:cacheprovider", f"--ignore={EXTRA}", f"--basetemp={bt}", f"--junitxml={xml}", "-q", "-rfE"]
    t0 = time.monotonic()
    proc = subprocess.run(cmd, cwd=WT, env=env(), capture_output=True, text=True)
    (OUT / "full_unit_suite_fix.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    summary = next((ln for ln in reversed(proc.stdout.splitlines()) if re.search(r"\d+ (passed|failed)", ln)), "")
    failed = sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+)", proc.stdout, re.M)))
    res = {"rc": proc.returncode, "secs": round(time.monotonic() - t0, 1), "summary": summary.strip("= "), "failed": failed, "python": subprocess.run([PY, "-V"], capture_output=True, text=True).stdout.strip()}
    (OUT / "full_unit_suite_fix.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res))
    return 0


def one_run(i: int) -> dict:
    # addopts already carries -q; a second -q (-qq) suppresses the summary line, so count from JUnit XML.
    xml = WT / "tmp" / f"rep-{i}.xml"
    cmd = [PY, "-m", "pytest", NEW, "-p", "no:cacheprovider", "-rfE", "-p", "no:xdist", f"--basetemp={WT / 'tmp' / f'bt-rep-{i}'}", f"--junitxml={xml}"]
    proc = subprocess.run(cmd, cwd=WT, env=env(), capture_output=True, text=True)
    import xml.etree.ElementTree as ET

    passed = failed_n = 0
    try:
        root = ET.parse(xml).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        for tc in suite.iter("testcase"):
            kinds = {c.tag for c in tc}
            if kinds & {"failure", "error"}:
                failed_n += 1
            elif "skipped" not in kinds:
                passed += 1
    except Exception:  # a run that wrote no XML counts as failed below via rc
        pass
    failed = sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+)", proc.stdout, re.M)))
    if failed or proc.returncode:
        (OUT / f"repeat_fail_{i}.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return {"i": i, "rc": proc.returncode, "passed": passed, "failed": failed_n, "failed_ids": failed}


def repeats(n: int, parallel: int) -> int:
    assert_fix_intact()
    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=parallel) as ex:
        runs = list(ex.map(one_run, range(n)))
    assert_fix_intact()
    res = {
        "runs": n,
        "parallel": parallel,
        "secs": round(time.monotonic() - t0, 1),
        "runs_all_green": sum(1 for r in runs if r["rc"] == 0),
        "total_passed": sum(r["passed"] for r in runs),
        "total_failed": sum(r["failed"] for r in runs),
        "per_run_passed": sorted({r["passed"] for r in runs}),
        "failing_runs": [r for r in runs if r["rc"] != 0][:10],
    }
    (OUT / "repeat_new_test_file.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res))
    return 0


def count(xml_path: Path) -> int:
    import xml.etree.ElementTree as ET

    root = ET.parse(xml_path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    tally = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    failures = []
    for tc in suite.iter("testcase"):
        kinds = {c.tag for c in tc}
        if "failure" in kinds:
            tally["failed"] += 1
            msg = next(c for c in tc if c.tag == "failure").get("message") or ""
            failures.append({"test": f"{tc.get('classname')}::{tc.get('name')}", "message": msg[:400]})
        elif "error" in kinds:
            tally["errors"] += 1
        elif "skipped" in kinds:
            tally["skipped"] += 1
        else:
            tally["passed"] += 1
    res = {"xml": str(xml_path), "header": {k: suite.get(k) for k in ("tests", "failures", "errors", "skipped", "time")}, **tally, "failures": failures}
    (OUT / "full_unit_suite_fix_counts.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--what", choices=["full", "repeat", "count"], required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--parallel", type=int, default=4)
    a = ap.parse_args()
    if a.what == "count":
        return count(OUT / "junit-unit-fix-n3.xml")
    return full_suite(a.workers) if a.what == "full" else repeats(a.n, a.parallel)


if __name__ == "__main__":
    sys.exit(main())
