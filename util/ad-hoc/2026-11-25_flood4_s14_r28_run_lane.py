"""
Run juniper-canopy's CI unit-lane pytest step (ci.yml "Run Unit Tests with Coverage Gate"), or a subset, in a CI-like
child environment, optionally behind the r28 thread census; repeat it N times and record each run.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 builder r28; modelled on util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py;
    the census plugin is util/ad-hoc/2026-11-25_flood4_s14_r28_thread_census.py

Usage:
    python <this file> --python <venv python> --tree <canopy tree> --out <dir> --label <name>
        [--census <census .py>] [--plugin NAME=<plugin .py> ...] [--no-cov] [--no-maxfail] [--env K=V ...] [--count N]
        [-- <pytest targets and args>]

Without targets the pytest command is ci.yml's (juniper-canopy .github/workflows/ci.yml, unit-tests job), verbatim:
-m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/ src/tests/contract/
src/tests/performance/ --verbose --timeout=60 --maxfail=5 --junitxml=reports/junit/junit-unit.xml --cov=src
--cov-report=term-missing --cov-report=xml:reports/coverage.xml --cov-report=json:reports/coverage.json
--cov-report=html:reports/htmlcov --cov-fail-under=80, with the step's CASCOR_BACKEND_AVAILABLE=0 RUN_SERVER_TESTS=0
ENABLE_SLOW_TESTS=0. The step's exit rule is applied as bash applies it: -N from subprocess.run is mapped to 128+N,
and 134 with junit failures="0" and errors="0" is success. With targets, --cov is dropped unless --cov-on-targets.

The child environment is CI-like: every JUNIPER_/CASCOR_/CANOPY_ variable dropped except the six Sentry DSNs (kept
EMPTY), LD_LIBRARY_PATH and PYTHONPATH dropped (this host's LD_LIBRARY_PATH names a foreign libtorch), LIBTORCH emptied.
With --census, PYTHONPATH names only the plugin dir (the census under the name r28_census). Variable values are never
recorded, only the names this script sets.
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
SENTRY = {"SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN"}
COV = ["--cov=src", "--cov-report=term-missing", "--cov-report=xml:reports/coverage.xml", "--cov-report=json:reports/coverage.json", "--cov-report=html:reports/htmlcov", "--cov-fail-under=80"]


def listening_ports() -> list[int]:
    ports = set()
    for name in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(name, encoding="ascii") as handle:
                lines = handle.readlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            if len(fields) >= 4 and fields[3] == "0A":
                ports.add(int(fields[1].split(":")[1], 16))
    return sorted(ports)


def juniper_ports(ports: list[int]) -> list[int]:
    return [p for p in ports if 8050 <= p <= 8059 or p == 8100 or 8200 <= p <= 8211]


def junit_totals(path: Path) -> dict:
    if not path.exists():
        return {}
    head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    match = re.search(r"<testsuite [^>]*>", head)
    if not match:
        return {}
    return {key: int(value) for key, value in re.findall(r'(tests|failures|errors|skipped)="(\d+)"', match.group(0))}


def ci_effective_exit(raw: int, junit: Path) -> tuple[int, int]:
    bash_exit = 128 - raw if raw < 0 else raw
    if bash_exit == 134 and junit.exists():
        text = junit.read_text(encoding="utf-8", errors="replace")
        if 'failures="0"' in text and 'errors="0"' in text:
            return bash_exit, 0
    return bash_exit, bash_exit


def child_env(plugins: Path | None, extra: list[str]) -> tuple[dict, list[str]]:
    env = {k: v for k, v in os.environ.items() if not ((k.startswith(("JUNIPER_", "CASCOR_", "CANOPY_")) and k not in SENTRY) or k in ("LD_LIBRARY_PATH", "PYTHONPATH"))}
    for name in SENTRY:
        env[name] = ""
    env.update({"LIBTORCH": "", "CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0"})
    names = []
    for pair in extra:
        key, _, value = pair.partition("=")
        env[key] = value
        names.append(key)
    if plugins is not None:
        env["PYTHONPATH"] = str(plugins)
    return env, names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--census", default="")
    parser.add_argument("--plugin", action="append", default=[], help="NAME=PATH: link PATH into the plugin dir as NAME.py and load it with -p NAME")
    parser.add_argument("--no-cov", action="store_true")
    parser.add_argument("--pytest-extra", action="append", default=[], help="an extra pytest argument, kept with CI's default command (e.g. -p no:repeat)")
    parser.add_argument("--cov-on-targets", action="store_true")
    parser.add_argument("--no-maxfail", action="store_true")
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--refuse-live-juniper-ports", action="store_true", default=True)
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    tree, out = Path(args.tree).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    plugins = None
    extra_plugins = []
    if args.census or args.plugin:
        plugins = out / "plugins"
        plugins.mkdir(exist_ok=True)
    if args.census:
        link = plugins / "r28_census.py"
        if not link.exists():
            link.symlink_to(Path(args.census).resolve())
    for spec in args.plugin:
        name, _, path = spec.partition("=")
        link = plugins / f"{name}.py"
        if not link.exists():
            link.symlink_to(Path(path).resolve())
        extra_plugins.append(name)
    for sub in ("logs", "src/logs", "reports/junit", "reports/coverage", "reports/htmlcov"):
        (tree / sub).mkdir(parents=True, exist_ok=True)
    targets = [a for a in args.rest if a != "--"]
    results = []
    for run in range(1, args.count + 1):
        listen = listening_ports()
        live = juniper_ports(listen)
        tag = args.label if args.count == 1 else f"{args.label}.run{run:02d}"
        if live and args.refuse_live_juniper_ports:
            record = {"label": tag, "refused": f"a Juniper port is listening: {live}"}
            results.append(record)
            print(json.dumps(record), flush=True)
            return 3
        junit_rel = "reports/junit/junit-unit.xml" if not targets else f"reports/junit/junit-{tag}.xml"
        command = [args.python, "-m", "pytest"]
        if args.census:
            command += ["-p", "r28_census"]
        for name in extra_plugins:
            command += ["-p", name]
        command += args.pytest_extra
        command += targets if targets else ["-m", CI_MARKERS, *CI_DIRS]
        command += ["--verbose", "--timeout=60"]
        if not args.no_maxfail:
            command += ["--maxfail=5"]
        command += [f"--junitxml={junit_rel}"]
        use_cov = (not args.no_cov) and (not targets or args.cov_on_targets)
        if use_cov:
            command += COV
        env, extra_names = child_env(plugins, args.env)
        census_out = out / f"{tag}.census.jsonl"
        if args.census:
            env["R28_CENSUS_OUT"] = str(census_out)
            if census_out.exists():
                census_out.unlink()
        junit = tree / junit_rel
        if junit.exists():
            junit.unlink()
        log_path = out / f"{tag}.log"
        start = time.time()
        with open(log_path, "w", encoding="utf-8") as log:
            log.write("COMMAND: " + " ".join(command) + f"\nCWD: {tree}\n")
            log.flush()
            proc = subprocess.run(command, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)  # nosec B603
        seconds = round(time.time() - start, 1)
        bash_exit, effective = ci_effective_exit(proc.returncode, junit)
        env_names = ["CASCOR_BACKEND_AVAILABLE", "RUN_SERVER_TESTS", "ENABLE_SLOW_TESTS", "LIBTORCH", *extra_names]
        if plugins is not None:
            env_names += ["PYTHONPATH"]
        if args.census:
            env_names += ["R28_CENSUS_OUT"]
        record = {"label": tag, "command": command, "cwd": str(tree), "raw_exit": proc.returncode, "bash_exit": bash_exit, "ci_effective_exit": effective, "seconds": seconds, "junit": junit_totals(junit), "log": str(log_path), "listen_ports_at_start": listen, "env_names_set": env_names}
        if junit.exists():
            shutil.copy2(junit, out / f"{tag}.junit.xml")
        if use_cov and (tree / "reports/coverage.json").exists():
            shutil.copy2(tree / "reports/coverage.json", out / f"{tag}.coverage.json")
            with open(tree / "reports/coverage.json", encoding="utf-8") as handle:
                record["coverage_percent"] = json.load(handle)["totals"]["percent_covered"]
            gap = Path(args.python).parent / "juniper-coverage-gap-map"
            if gap.exists():
                with open(out / f"{tag}.gapmap.log", "w", encoding="utf-8") as log:
                    gate = subprocess.run([str(gap), "--coverage-json", "reports/coverage.json", "--enforce"], cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)  # nosec B603
                record["per_file_gate_exit"] = gate.returncode
        results.append(record)
        with open(out / f"{tag}.run.json", "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=1)
        print(json.dumps({k: record.get(k) for k in ("label", "raw_exit", "bash_exit", "ci_effective_exit", "seconds", "junit", "coverage_percent", "per_file_gate_exit")}), flush=True)
    return 0 if all(r.get("ci_effective_exit") == 0 for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
