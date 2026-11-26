"""
Run juniper-canopy's CI unit-lane step (or a subset) for the r28 code lens, in a CI-like child environment, behind the
r27-val-code2 connect census/fence and the r28-val-code plugin, then (with coverage) CI's per-file gate.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r28-val-code. Reuses child_env, ci_effective_exit, junit_totals and listening_ports
    from util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py (loaded by path, not copied), and that lens's
    census util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_census.py (the fence: refuses every connect to a Juniper
    port, and to any local port listening when the run starts). Plugin: util/ad-hoc/2026-11-25_flood4_s14_r28-val-code_plugin.py

Usage:
    python <this file> --python <venv python> --tree <canopy tree> --out <dir> --label <name>
        [--no-cov] [--no-maxfail] [--env K=V ...] [-- <pytest targets and args>]

Without targets the pytest command is ci.yml's unit-lane command verbatim (juniper-canopy .github/workflows/ci.yml,
"Run Unit Tests with Coverage Gate", COVERAGE_FAIL_UNDER=80), with `-p r27v2_plugin -p r28v_plugin` added. With
targets: <targets> --verbose --timeout=60 [--maxfail=5] --junitxml=... [the coverage flags]. The step's Python 3.12
SIGABRT rule (exit 134 with a clean JUnit file is success) is applied. R28V_OUT is set to <out>/<label>.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess  # nosec B404 - runs pytest under a chosen interpreter
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
R27V2_RUNNER = HERE / "2026-11-25_flood4_s14_r27-val-code2_run_lane.py"
R27V2_CENSUS = HERE / "2026-11-25_flood4_s14_r27-val-code2_census.py"
R28V_PLUGIN = HERE / "2026-11-25_flood4_s14_r28-val-code_plugin.py"
COV = ["--cov=src", "--cov-report=term-missing", "--cov-report=xml:reports/coverage.xml", "--cov-report=json:reports/coverage.json", "--cov-report=html:reports/htmlcov", "--cov-fail-under=80"]


def _load_r27v2():
    spec = importlib.util.spec_from_file_location("r27v2_run_lane", R27V2_RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--no-cov", action="store_true")
    parser.add_argument("--no-maxfail", action="store_true")
    parser.add_argument("--no-census", action="store_true", help="omit the r27v2 connect census/fence (its per-test hook starves under in-process CPU spinners)")
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    lane = _load_r27v2()

    tree, out = Path(args.tree).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    plugins = out / "plugins"
    plugins.mkdir(exist_ok=True)
    for name, target in (("r27v2_census.py", R27V2_CENSUS), ("r27v2_plugin.py", R27V2_CENSUS), ("r28v_plugin.py", R28V_PLUGIN)):
        link = plugins / name
        if not link.exists():
            link.symlink_to(target)
    (plugins / "sitecustomize.py").write_text(lane.SITECUSTOMIZE, encoding="utf-8")
    for sub in ("logs", "src/logs", "reports/junit", "reports/coverage", "reports/htmlcov"):
        (tree / sub).mkdir(parents=True, exist_ok=True)
    targets = [a for a in args.rest if a != "--"]
    listen = lane.listening_ports()
    junit_rel = "reports/junit/junit-unit.xml" if not targets else f"reports/junit/junit-{args.label}.xml"
    command = [args.python, "-m", "pytest", "-p", "r28v_plugin"] if args.no_census else [args.python, "-m", "pytest", "-p", "r27v2_plugin", "-p", "r28v_plugin"]
    command += targets if targets else ["-m", lane.CI_MARKERS, *lane.CI_DIRS]
    command += ["--verbose", "--timeout=60"]
    if not args.no_maxfail:
        command += ["--maxfail=5"]
    command += [f"--junitxml={junit_rel}"]
    if not args.no_cov:
        command += COV
    env, extra_names = lane.child_env(plugins, args.env)
    env.update({"R28V_OUT": str(out / args.label)})
    if not args.no_census:
        env.update({"R27V2_OUT": str(out / args.label), "R27V2_LISTEN": ",".join(map(str, listen)), "R27V2_TREE": str(tree)})
    for stale in out.glob(f"{args.label}.*.jsonl"):
        stale.unlink()
    junit = tree / junit_rel
    if junit.exists():
        junit.unlink()
    log_path = out / f"{args.label}.log"
    start = time.time()
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("COMMAND: " + " ".join(command) + f"\nCWD: {tree}\nEXTRA ENV NAMES: {extra_names}\n")
        log.flush()
        proc = subprocess.run(command, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)  # nosec B603
    seconds = round(time.time() - start, 1)
    bash_exit, effective = lane.ci_effective_exit(proc.returncode, junit)
    record = {"label": args.label, "command": command, "cwd": str(tree), "raw_exit": proc.returncode, "bash_exit": bash_exit, "ci_effective_exit": effective, "seconds": seconds, "junit": lane.junit_totals(junit), "log": str(log_path), "listen_ports_at_start": listen, "env_names_set": ["CASCOR_BACKEND_AVAILABLE", "RUN_SERVER_TESTS", "ENABLE_SLOW_TESTS", "LIBTORCH", "PYTHONPATH", "R27V2_OUT", "R27V2_LISTEN", "R27V2_TREE", "R28V_OUT", *extra_names]}
    if junit.exists():
        shutil.copy2(junit, out / f"{args.label}.junit.xml")
    connects = out / f"{args.label}.connects.jsonl"
    if connects.exists():
        rows = [json.loads(line) for line in connects.read_text(encoding="utf-8").splitlines() if line.strip()]
        record["connects_total"] = len(rows)
        record["connects_juniper_ports"] = sum(1 for r in rows if r.get("refused") == "juniper")
    else:
        record["connects_total"] = None if args.no_census else 0
    record["census"] = not args.no_census
    if not args.no_cov and (tree / "reports/coverage.json").exists():
        shutil.copy2(tree / "reports/coverage.json", out / f"{args.label}.coverage.json")
        with open(tree / "reports/coverage.json", encoding="utf-8") as handle:
            record["coverage_percent"] = json.load(handle)["totals"]["percent_covered"]
        if not targets:
            gap = Path(args.python).parent / "juniper-coverage-gap-map"
            with open(out / f"{args.label}.gapmap.log", "w", encoding="utf-8") as log:
                gate = subprocess.run([str(gap), "--coverage-json", "reports/coverage.json", "--enforce"], cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)  # nosec B603
            record["per_file_gate_exit"] = gate.returncode
    with open(out / f"{args.label}.run.json", "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=1)
    print(json.dumps({k: record.get(k) for k in ("label", "raw_exit", "bash_exit", "ci_effective_exit", "seconds", "junit", "connects_total", "connects_juniper_ports", "coverage_percent", "per_file_gate_exit")}), flush=True)
    return 0 if effective == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
