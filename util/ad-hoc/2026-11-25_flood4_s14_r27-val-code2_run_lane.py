"""
Run juniper-canopy's CI unit-lane step (ci.yml "Run Unit Tests with Coverage Gate"), or a subset, behind the
r27-val-code2 connect census (pytest process and every child Python process), then CI's per-file coverage gate.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 replacement code lens r27-val-code2; the census is
    util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_census.py

Usage:
    python <this file> --python <venv python> --tree <canopy tree> --out <dir> --label <name> --census <census .py>
        [--no-cov] [--no-maxfail] [--allow-ports 1,2] [--env K=V ...] [--count N] [-- <pytest targets and args>]

Without targets the pytest command is ci.yml's (juniper-canopy .github/workflows/ci.yml, unit-tests job), verbatim:
-m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/ src/tests/contract/
src/tests/performance/ --verbose --timeout=60 --maxfail=5 --junitxml=reports/junit/junit-unit.xml --cov=src
--cov-report=term-missing --cov-report=xml:reports/coverage.xml --cov-report=json:reports/coverage.json
--cov-report=html:reports/htmlcov --cov-fail-under=80, with the step's CASCOR_BACKEND_AVAILABLE=0 RUN_SERVER_TESTS=0
ENABLE_SLOW_TESTS=0. The step's Python 3.12 rule is applied as bash applies it: a process killed by SIGABRT is exit 134
in bash ($PIPESTATUS), but -6 from subprocess.run, so -N is mapped to 128+N first; 134 with junit failures="0" and
errors="0" is success. With coverage the per-file gate follows (juniper-coverage-gap-map --coverage-json
reports/coverage.json --enforce, ci.yml's next step).

The child environment is CI-like: every JUNIPER_/CASCOR_/CANOPY_ variable dropped except the six Sentry DSNs (kept
EMPTY), LD_LIBRARY_PATH and PYTHONPATH dropped (this host's LD_LIBRARY_PATH names a foreign libtorch), LIBTORCH emptied.
PYTHONPATH then names only the plugin dir (sitecustomize.py + the census under two names). Variable values are never
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
SITECUSTOMIZE = 'import os\nif os.environ.get("R27V2_OUT"):\n    import r27v2_census  # noqa: F401 - installs the connect fence in this process\n'


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


def junit_totals(path: Path) -> dict:
    if not path.exists():
        return {}
    head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    match = re.search(r"<testsuite [^>]*>", head)
    if not match:
        return {}
    return {key: int(value) for key, value in re.findall(r'(tests|failures|errors|skipped)="(\d+)"', match.group(0))}


def ci_effective_exit(raw: int, junit: Path) -> tuple[int, int]:
    """(bash-style exit, ci.yml's effective exit) for a pytest exit status."""
    bash_exit = 128 - raw if raw < 0 else raw
    if bash_exit == 134 and junit.exists():
        text = junit.read_text(encoding="utf-8", errors="replace")
        if 'failures="0"' in text and 'errors="0"' in text:
            return bash_exit, 0
    return bash_exit, bash_exit


def child_env(plugins: Path, extra: list[str]) -> tuple[dict, list[str]]:
    env = {k: v for k, v in os.environ.items() if not ((k.startswith(("JUNIPER_", "CASCOR_", "CANOPY_")) and k not in SENTRY) or k in ("LD_LIBRARY_PATH", "PYTHONPATH"))}
    for name in SENTRY:
        env[name] = ""
    env.update({"LIBTORCH": "", "CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0"})
    names = []
    for pair in extra:
        key, _, value = pair.partition("=")
        env[key] = value
        names.append(key)
    env["PYTHONPATH"] = str(plugins)
    return env, names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--census", required=True)
    parser.add_argument("--no-cov", action="store_true")
    parser.add_argument("--no-maxfail", action="store_true")
    parser.add_argument("--allow-ports", default="")
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    tree, out = Path(args.tree).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    plugins = out / "plugins"
    plugins.mkdir(exist_ok=True)
    for name in ("r27v2_census.py", "r27v2_plugin.py"):
        link = plugins / name
        if not link.exists():
            link.symlink_to(Path(args.census).resolve())
    (plugins / "sitecustomize.py").write_text(SITECUSTOMIZE, encoding="utf-8")
    for sub in ("logs", "src/logs", "reports/junit", "reports/coverage", "reports/htmlcov"):
        (tree / sub).mkdir(parents=True, exist_ok=True)
    targets = [a for a in args.rest if a != "--"]
    listen = listening_ports()
    results = []
    for run in range(1, args.count + 1):
        tag = args.label if args.count == 1 else f"{args.label}.run{run:02d}"
        junit_rel = "reports/junit/junit-unit.xml" if not targets else f"reports/junit/junit-{tag}.xml"
        command = [args.python, "-m", "pytest", "-p", "r27v2_plugin"]
        command += targets if targets else ["-m", CI_MARKERS, *CI_DIRS]
        command += ["--verbose", "--timeout=60"]
        if not args.no_maxfail:
            command += ["--maxfail=5"]
        command += [f"--junitxml={junit_rel}"]
        if not args.no_cov:
            command += ["--cov=src", "--cov-report=term-missing", "--cov-report=xml:reports/coverage.xml", "--cov-report=json:reports/coverage.json", "--cov-report=html:reports/htmlcov", "--cov-fail-under=80"]
        env, extra_names = child_env(plugins, args.env)
        env.update({"R27V2_OUT": str(out / tag), "R27V2_LISTEN": ",".join(map(str, listen)), "R27V2_TREE": str(tree)})
        if args.allow_ports:
            env["R27V2_ALLOW"] = args.allow_ports
        for kind in ("connects", "fake", "guard"):
            stale = out / f"{tag}.{kind}.jsonl"
            if stale.exists():
                stale.unlink()
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
        record = {"label": tag, "command": command, "cwd": str(tree), "raw_exit": proc.returncode, "bash_exit": bash_exit, "ci_effective_exit": effective, "seconds": seconds, "junit": junit_totals(junit), "log": str(log_path), "listen_ports_at_start": listen, "env_names_set": ["CASCOR_BACKEND_AVAILABLE", "RUN_SERVER_TESTS", "ENABLE_SLOW_TESTS", "LIBTORCH", "PYTHONPATH", "R27V2_OUT", "R27V2_LISTEN", "R27V2_TREE", *extra_names]}
        if junit.exists():
            shutil.copy2(junit, out / f"{tag}.junit.xml")
        connects = out / f"{tag}.connects.jsonl"
        if connects.exists():
            rows = [json.loads(line) for line in connects.read_text(encoding="utf-8").splitlines() if line.strip()]
            record["connects_total"] = len(rows)
            record["connects_8100"] = sum(1 for r in rows if r["port"] == 8100)
            record["connects_juniper_ports"] = sum(1 for r in rows if r["refused"] == "juniper")
            record["connects_child_processes"] = sum(1 for r in rows if r["process"] != "pytest")
            record["connects_child_juniper_ports"] = sum(1 for r in rows if r["process"] != "pytest" and r["refused"] == "juniper")
        if not args.no_cov and (tree / "reports/coverage.json").exists():
            shutil.copy2(tree / "reports/coverage.json", out / f"{tag}.coverage.json")
            with open(tree / "reports/coverage.json", encoding="utf-8") as handle:
                record["coverage_percent"] = json.load(handle)["totals"]["percent_covered"]
            gap = Path(args.python).parent / "juniper-coverage-gap-map"
            with open(out / f"{tag}.gapmap.log", "w", encoding="utf-8") as log:
                gate = subprocess.run([str(gap), "--coverage-json", "reports/coverage.json", "--enforce"], cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)  # nosec B603
            record["per_file_gate_exit"] = gate.returncode
        results.append(record)
        with open(out / f"{tag}.run.json", "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=1)
        print(json.dumps({k: record.get(k) for k in ("label", "raw_exit", "bash_exit", "ci_effective_exit", "seconds", "junit", "connects_8100", "connects_child_processes")}), flush=True)
    return 0 if all(r["ci_effective_exit"] == 0 for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
