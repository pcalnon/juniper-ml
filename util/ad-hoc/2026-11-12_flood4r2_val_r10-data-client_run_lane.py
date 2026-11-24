"""
Run one of juniper-data-client's CI lanes locally, with the command read from the tree's own ci.yml.

unit               the unit-tests job's one pytest command, its selection arguments untouched (only the report paths
                   move to --out); no gitleaks binary on PATH, as on the runner's unit legs
unit-m-unit        ``pytest tests/ -m unit``, the documented unit run
integration        the integration-tests job's selection (``-m integration tests/``)
selftest           the Security Scans self-test step's own ``run:`` under ``bash -e`` with the step's ``env:``, and the
                   engine directory first on PATH
selftest-nobinary  the same with no engine on PATH: what CI does when neither path installed the binary

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_run_lane.py --tree <checkout> --python-bin <dir holding python> --out <dir> --lane <name> [--engine-dir <dir holding gitleaks>]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 session 5)
Created: 2026-11-12
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import yaml

TEST_FILE = "tests/test_gitleaks_pr_scan.py"


def workflow(tree: Path) -> dict:
    return yaml.safe_load((tree / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))


def unit_argv(tree: Path) -> list[str]:
    steps = workflow(tree)["jobs"]["unit-tests"]["steps"]
    runs = [str(step["run"]) for step in steps if "python -m pytest" in str(step.get("run", ""))]
    if len(runs) != 1:
        raise SystemExit(f"expected one pytest command in unit-tests, found {len(runs)}")
    command = runs[0][runs[0].index("python -m pytest") :].replace("\\\n", " ").splitlines()[0]
    return shlex.split(command)


def junit_counts(junit: Path) -> dict:
    counts = {"cases": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0, "this_file": {"cases": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}, "not_passed": []}
    if not junit.is_file():
        return counts
    for case in ElementTree.parse(junit).getroot().iter("testcase"):
        kind = "failed" if case.find("failure") is not None else "errors" if case.find("error") is not None else "skipped" if case.find("skipped") is not None else "passed"
        counts["cases"] += 1
        counts[kind] += 1
        if case.get("classname", "").endswith("test_gitleaks_pr_scan"):
            counts["this_file"]["cases"] += 1
            counts["this_file"][kind] += 1
        if kind in ("failed", "errors"):
            counts["not_passed"].append(f"{case.get('classname')}::{case.get('name')} ({kind})")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--python-bin", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--lane", required=True, choices=["unit", "unit-m-unit", "integration", "selftest", "selftest-nobinary"])
    parser.add_argument("--engine-dir", type=Path)
    args = parser.parse_args()
    tree, out = args.tree.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    label = f"{tree.name.split('--')[2]}-{args.lane}"
    junit = out / f"{label}.junit.xml"
    basetemp = out / "basetemp" / label
    basetemp.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("gitleaks", path=os.environ.get("PATH", "")):
        raise SystemExit("a gitleaks binary is on this shell's PATH: the no-binary lanes would not be what they claim")
    path = f"{args.python_bin}{os.pathsep}{os.environ.get('PATH', os.defpath)}"
    env = {key: value for key, value in os.environ.items() if not key.startswith("GITLEAKS_")}
    env.update({"PATH": path, "PYTHONDONTWRITEBYTECODE": "1", "COVERAGE_FILE": str(out / f"{label}.coverage")})
    extra = ["-p", "no:cacheprovider", f"--basetemp={basetemp}"]

    if args.lane == "unit":
        argv = []
        for arg in unit_argv(tree):
            if arg.startswith("--junitxml="):
                arg = f"--junitxml={junit}"
            elif arg.startswith("--cov-report=xml:"):
                arg = f"--cov-report=xml:{out / (label + '.coverage.xml')}"
            elif arg.startswith("--cov-report=json:"):
                arg = f"--cov-report=json:{out / (label + '.coverage.json')}"
            elif arg.startswith("--cov-report=html:"):
                continue
            argv.append(arg)
        argv += extra
        shown = " ".join(shlex.quote(arg) for arg in argv)
    elif args.lane == "unit-m-unit":
        argv = ["python", "-m", "pytest", "tests/", "-m", "unit", "-v", f"--junitxml={junit}", *extra]
        shown = " ".join(shlex.quote(arg) for arg in argv)
    elif args.lane == "integration":
        argv = ["python", "-m", "pytest", "-m", "integration", "tests/", "--verbose", "--timeout=120", "--maxfail=5", f"--junitxml={junit}", *extra]
        shown = " ".join(shlex.quote(arg) for arg in argv)
    else:
        steps = workflow(tree)["jobs"]["security"]["steps"]
        matching = [step for step in steps if TEST_FILE in str(step.get("run", ""))]
        if len(matching) != 1:
            raise SystemExit(f"expected one Security Scans step running {TEST_FILE}, found {len(matching)}")
        step = matching[0]
        env.update({key: str(value) for key, value in step.get("env", {}).items()})
        if args.lane == "selftest":
            if args.engine_dir is None:
                raise SystemExit("--engine-dir is required for the selftest lane")
            env["PATH"] = f"{args.engine_dir.resolve()}{os.pathsep}{path}"
        # pytest reads PYTEST_ADDOPTS; it only adds the report and scratch paths, never a selection argument.
        env["PYTEST_ADDOPTS"] = " ".join(shlex.quote(arg) for arg in [f"--junitxml={junit}", *extra])
        argv = ["bash", "-e", "-c", str(step["run"])]
        shown = f"bash -e -c {str(step['run'])!r} with env {step.get('env', {})} and PYTEST_ADDOPTS={env['PYTEST_ADDOPTS']!r}"

    res = subprocess.run(argv, cwd=tree, env=env, capture_output=True, text=True, check=False)
    (out / f"{label}.log").write_text(f"$ {shown}\n" + res.stdout + "\n--- stderr ---\n" + res.stderr + f"\n[exit {res.returncode}]\n", encoding="utf-8")
    tail = [line for line in res.stdout.splitlines() if line.strip()][-1:] or [""]
    file_line = [line for line in res.stdout.splitlines() if line.startswith(TEST_FILE + " ")]
    python = subprocess.run(["python", "-c", "import sys, pytest; print(sys.version.split()[0], 'pytest', pytest.__version__)"], env=env, capture_output=True, text=True, check=False).stdout.strip()
    report = {"lane": args.lane, "tree": str(tree), "python": python, "command": shown, "exit": res.returncode, "last_line": tail[0], "progress_line_of_the_new_file": file_line, **junit_counts(junit), "log": str(out / f"{label}.log")}
    with open(out / f"{label}.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
