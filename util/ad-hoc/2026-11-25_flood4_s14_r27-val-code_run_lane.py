"""
Run juniper-canopy's CI unit-lane step (ci.yml "Run Unit Tests with Coverage Gate") behind the r27-val-code connect fence.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r27-val-code; the fence is util/ad-hoc/2026-11-25_flood4_s14_r27-val-code_fence.py

Usage:
    python <this file> --python <venv python> --tree <canopy tree> --out <dir> --label <name> --plugin <fence .py>
        [--no-cov] [--maxfail N | --no-maxfail] [--allow-ports 1,2] [--env K=V ...] [--count N] [-- <pytest targets/args>]

Without targets the command is ci.yml's, verbatim: -m "not requires_cascor and not requires_server and not slow"
src/tests/unit/ src/tests/regression/ src/tests/contract/ src/tests/performance/ --verbose --timeout=60 --maxfail=5
--junitxml=reports/junit/junit-unit.xml --cov=src --cov-report=term-missing --cov-report=xml:reports/coverage.xml
--cov-report=json:reports/coverage.json --cov-report=html:reports/htmlcov --cov-fail-under=80, with the step's
CASCOR_BACKEND_AVAILABLE=0 RUN_SERVER_TESTS=0 ENABLE_SLOW_TESTS=0, and its Python 3.12 SIGABRT (134) rule. With
coverage it then runs the per-file gate (juniper-coverage-gap-map --coverage-json reports/coverage.json --enforce).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess  # nosec B404 - runs pytest under a chosen interpreter
import sys
import time
from pathlib import Path

CI_DIRS = ["src/tests/unit/", "src/tests/regression/", "src/tests/contract/", "src/tests/performance/"]
CI_MARKERS = "not requires_cascor and not requires_server and not slow"


def junit_totals(path: Path) -> dict:
    if not path.exists():
        return {}
    head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    match = re.search(r"<testsuite [^>]*>", head)
    if not match:
        return {}
    return {key: int(value) for key, value in re.findall(r'(tests|failures|errors|skipped)="(\d+)"', match.group(0))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--plugin", required=True)
    parser.add_argument("--no-cov", action="store_true")
    parser.add_argument("--maxfail", type=int, default=5)
    parser.add_argument("--no-maxfail", action="store_true")
    parser.add_argument("--allow-ports", default="")
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--count", type=int, default=1, help="repeat the run N times (flake runs); each run gets its own outputs")
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    tree = Path(args.tree).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    plugins = out / "plugins"
    plugins.mkdir(exist_ok=True)
    link = plugins / "r27v_fence.py"
    if not link.exists():
        link.symlink_to(Path(args.plugin).resolve())
    for sub in ("logs", "src/logs", "reports/junit", "reports/coverage", "reports/htmlcov"):
        (tree / sub).mkdir(parents=True, exist_ok=True)

    targets = [a for a in args.rest if a != "--"]
    results = []
    for run in range(1, args.count + 1):
        tag = args.label if args.count == 1 else f"{args.label}.run{run:02d}"
        junit = f"reports/junit/junit-{tag}.xml"
        command = [args.python, "-m", "pytest", "-p", "r27v_fence"]
        if targets:
            command += targets
        else:
            command += ["-m", CI_MARKERS, *CI_DIRS]
        command += ["--verbose", "--timeout=60"]
        if not args.no_maxfail:
            command += [f"--maxfail={args.maxfail}"]
        command += [f"--junitxml={junit}"]
        if not args.no_cov:
            command += [
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=xml:reports/coverage.xml",
                "--cov-report=json:reports/coverage.json",
                "--cov-report=html:reports/htmlcov",
                "--cov-fail-under=80",
            ]
        # CI-like child environment, as GitHub's runner has: every JUNIPER_/CASCOR_/CANOPY_ variable dropped except the
        # Sentry DSNs the session's run wrapper sets EMPTY, LD_LIBRARY_PATH and PYTHONPATH dropped (this host's
        # LD_LIBRARY_PATH names a foreign libtorch that breaks `import torch`), LIBTORCH emptied. Names are not recorded.
        keep_empty = {"SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN"}
        env = {k: v for k, v in os.environ.items() if not ((k.startswith(("JUNIPER_", "CASCOR_", "CANOPY_")) and k not in keep_empty) or k in ("LD_LIBRARY_PATH", "PYTHONPATH"))}
        dropped = len(os.environ) - len(env)
        env.update({"LIBTORCH": "", "CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0"})
        for pair in args.env:
            key, _, value = pair.partition("=")
            env[key] = value
        env["PYTHONPATH"] = str(plugins) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        env["R27V_OUT"] = str(out / tag)
        if args.allow_ports:
            env["R27V_ALLOW_PORTS"] = args.allow_ports
        log_path = out / f"{tag}.log"
        start = time.time()
        with open(log_path, "w", encoding="utf-8") as log:
            log.write("COMMAND: " + " ".join(command) + "\n")
            log.write(f"CWD: {tree}\n")
            log.flush()
            proc = subprocess.run(command, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)  # nosec B603
        seconds = round(time.time() - start, 1)
        exit_code = proc.returncode
        totals = junit_totals(tree / junit)
        if exit_code == 134 and totals and totals.get("failures") == 0 and totals.get("errors") == 0:
            effective = 0  # ci.yml's Python 3.12 SIGABRT rule
        else:
            effective = exit_code
        if (tree / junit).exists():
            shutil.copy2(tree / junit, out / f"{tag}.junit.xml")
        record = {"label": tag, "command": command, "cwd": str(tree), "exit": exit_code, "effective_exit": effective, "seconds": seconds, "junit": totals, "log": str(log_path), "env_note": f"{dropped} variables dropped (JUNIPER_/CASCOR_/CANOPY_ except empty Sentry DSNs, LD_LIBRARY_PATH, PYTHONPATH); LIBTORCH emptied; CI step variables set; extra --env: {[p.partition('=')[0] for p in args.env]}"}
        if not args.no_cov and (tree / "reports/coverage.json").exists():
            shutil.copy2(tree / "reports/coverage.json", out / f"{tag}.coverage.json")
            with open(tree / "reports/coverage.json", encoding="utf-8") as handle:
                record["coverage_percent"] = json.load(handle)["totals"]["percent_covered"]
            gap = Path(args.python).parent / "juniper-coverage-gap-map"
            if gap.exists():
                with open(out / f"{tag}.gapmap.log", "w", encoding="utf-8") as log:
                    gate = subprocess.run([str(gap), "--coverage-json", "reports/coverage.json", "--enforce"], cwd=tree, stdout=log, stderr=subprocess.STDOUT, check=False)  # nosec B603
                record["per_file_gate_exit"] = gate.returncode
            else:
                record["per_file_gate_exit"] = "juniper-coverage-gap-map not installed"
        results.append(record)
        with open(out / f"{tag}.run.json", "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=1)
        print(json.dumps({k: record[k] for k in ("label", "exit", "effective_exit", "seconds", "junit")}), flush=True)
    return 0 if all(r["effective_exit"] == 0 for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
