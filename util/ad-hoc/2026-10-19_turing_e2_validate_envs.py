"""
Run a repo's CI test lanes against a freshly created turing conda env (bring-up task E2), without changing the env.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-19
Status: ad-hoc — one-off (the E2 validation runner; all three envs validated 2026-10-20, plan §18.2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: conf/hosts/turing/conda-envs/{JuniperCascor1,JuniperData,JuniperCanopy1}.yml (the specs this validates);
         util/ad-hoc/2026-10-19_turing_e2_derive_conda_envs.py (derives them);
         notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (D8, E2, G-ENV; §17)

Why: the derived specs solve (mamba --dry-run), but on 2026-10-19 no env could be created. Outbound connections from
Miniforge's base python3.13 and from mamba time out on turing, while curl, gh and JuniperPython's python connect to
the same hosts. That is Little Snitch's per-app filtering. Once the owner allows conda.anaconda.org for those
binaries, and pypi.org and files.pythonhosted.org for the new envs' pythons, create each env from its spec, then run:

    python3 -I util/ad-hoc/2026-10-19_turing_e2_validate_envs.py <cascor|data|canopy> [--phase prepare|install|test|all]
        [--lane unit|integration|all] [--work DIR] [--env KEY=VALUE ...]

  prepare  rsync each repo checkout under ~/Development/python/Juniper (and juniper-data-client, which cascor and data
           install) into WORK/trees/, without .git. The owner's checkouts are only read.
  install  create a `venv --system-site-packages` overlay on the conda env and run the repo's CI pip steps in it, so
           the conda env stays exactly what its spec builds.
  test     run the repo's ci.yml unit and integration lanes; write junit, logs and a summary JSON under WORK/logs/.

WORK defaults to ~/.local/state/juniper/turing-e2 (not the session scratchpad, which dies with the session).

--env (added 2026-10-20) puts one more variable into the child environment, for an experiment such as the
OMP_NUM_THREADS run in plan §18.3 E-BLAS. It is repeatable. The summary JSON records the overrides under
"env_overrides", and each lane log records them above the command, so an experiment's numbers cannot pass for a
stock run's.

Deviations from CI, on purpose (from the runner written in the 2026-10-19 session):
  - --maxfail is dropped, so every test runs and the counts are complete;
  - juniper-data-client comes from the WORK copy of the owner's checkout instead of `pip install git+https://...@main`;
  - TMPDIR stays the macOS per-user default, because AF_UNIX socket paths cap at 104 bytes;
  - MPLBACKEND=Agg (CI runners are headless; this host has a desktop session), and CI=true as on Actions;
  - the stray PYTHONPATH (JuniperPython's conda env var, "${CONDA_PREFIX}/lib/python3.9/site-packages") is not
    inherited: the child environment is built from a minimal allow-list.

Exit 0 = the requested phases ran (test failures are reported in the summary, not as the exit code); 1 = a setup step
failed; 2 = the conda env or a checkout is missing.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess  # nosec B404 -- runs rsync, python -m venv/pip/pytest with fixed argv lists
import sys
import time
import xml.etree.ElementTree as ET  # nosec B405 -- parses junit XML that pytest just wrote locally

JUNIPER = pathlib.Path.home() / "Development" / "python" / "Juniper"
ENVS = pathlib.Path("/usr/local/miniforge3/envs")

CFG = {
    "cascor": {
        "env": "JuniperCascor1",
        "repo": "juniper-cascor",
        "needs_data_client": True,
        "pip": [["install", "{data_client}"], ["install", "-e", "{tree}[all]"]],
        "dirs": ["logs", "src/logs", "reports/junit", "reports/htmlcov", "src/tests/reports"],
        "extra_env": {},
        "lanes": {
            "unit": ["-m", "unit and not slow", "src/tests/unit", "--timeout=60", "--cov=src", "--cov-report=json:reports/coverage.json"],
            "integration": ["--integration", "-m", "integration and not slow", "src/tests/integration", "--timeout=120"],
        },
    },
    "data": {
        "env": "JuniperData",
        "repo": "juniper-data",
        "needs_data_client": True,
        "pip": [["install", "{data_client}"], ["install", "{tree}[all]"]],
        "dirs": ["reports/junit", "reports/htmlcov"],
        "extra_env": {},
        "lanes": {
            "unit": ["-m", "unit and not slow", "juniper_data/tests/unit", "--timeout=60", "--cov=juniper_data", "--cov-report=json:reports/coverage.json"],
            "integration": ["-m", "integration and not slow", "juniper_data/tests/integration", "--timeout=120"],
        },
    },
    "canopy": {
        "env": "JuniperCanopy1",
        "repo": "juniper-canopy",
        "needs_data_client": False,
        "pip": [["install", "-e", "{tree}[test,juniper-cascor,observability]"], ["install", "h5py>=3.0"]],
        "dirs": ["logs", "src/logs", "reports/junit", "reports/coverage", "reports/htmlcov"],
        "extra_env": {"CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0"},
        "lanes": {
            "unit": ["-m", "not requires_cascor and not requires_server and not slow", "src/tests/unit/", "src/tests/regression/", "src/tests/contract/", "src/tests/performance/", "--timeout=60", "--cov=src", "--cov-report=json:reports/coverage.json"],
            "integration": ["-m", "integration and not requires_cascor and not requires_server and not slow", "src/tests/integration", "--timeout=120"],
        },
    },
}


def clean_env(venv: pathlib.Path, conda_env: pathlib.Path, extra: dict) -> dict:
    keep = {k: os.environ[k] for k in ("HOME", "USER", "LOGNAME", "TMPDIR", "SHELL") if k in os.environ}
    keep.update({
        "PATH": f"{venv}/bin:{conda_env}/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
        "TERM": "dumb",
        "CI": "true",
        "MPLBACKEND": "Agg",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_INPUT": "1",
        "VIRTUAL_ENV": str(venv),
    })
    keep.update(extra)
    return keep


def run(cmd: list[str], cwd: pathlib.Path, env: dict, log: pathlib.Path) -> int:
    t0 = time.time()
    with log.open("a") as fh:
        fh.write(f"\n$ (cwd={cwd}) {' '.join(cmd)}\n")
        fh.flush()
        rc = subprocess.run(cmd, cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT).returncode  # nosec B603
        fh.write(f"[exit {rc} after {time.time() - t0:.0f}s]\n")
    print(f"  exit {rc} after {time.time() - t0:.0f}s: {' '.join(cmd)[:160]}")
    return rc


def junit_counts(path: pathlib.Path) -> dict:
    root = ET.parse(path).getroot()  # nosec B314 -- local pytest output
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    tot = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    for s in suites:
        for k in ("tests", "failures", "errors", "skipped"):
            tot[k] += int(s.get(k, 0))
        tot["time"] += float(s.get("time", 0))
    tot["passed"] = tot["tests"] - tot["failures"] - tot["errors"] - tot["skipped"]
    bad = []
    for case in root.iter("testcase"):
        for tag in ("failure", "error"):
            el = case.find(tag)
            if el is not None:
                msg = (el.get("message") or "").replace("\n", " ")[:300]
                bad.append(f"{tag.upper()} {case.get('classname')}::{case.get('name')} :: {msg}")
    tot["bad"] = bad
    return tot


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("key", choices=sorted(CFG))
    ap.add_argument("--phase", choices=("prepare", "install", "test", "all"), default="all")
    ap.add_argument("--lane", choices=("unit", "integration", "all"), default="all")
    ap.add_argument("--work", type=pathlib.Path, default=pathlib.Path.home() / ".local" / "state" / "juniper" / "turing-e2")
    ap.add_argument("--env", action="append", default=[], metavar="KEY=VALUE", help="add a variable to the child environment (repeatable)")
    args = ap.parse_args()
    overrides = {}
    for item in args.env:
        key, sep, value = item.partition("=")
        if not sep or not key:
            ap.error(f"--env takes KEY=VALUE, not {item!r}")
        overrides[key] = value
    cfg = CFG[args.key]
    conda_env = ENVS / cfg["env"]
    tree = args.work / "trees" / cfg["repo"]
    data_client = args.work / "trees" / "juniper-data-client"
    venv = args.work / "venvs" / cfg["env"]
    logs = args.work / "logs" / cfg["env"]
    logs.mkdir(parents=True, exist_ok=True)
    env = clean_env(venv, conda_env, cfg["extra_env"])
    env.update(overrides)

    if args.phase in ("prepare", "all"):
        repos = [cfg["repo"]] + (["juniper-data-client"] if cfg["needs_data_client"] else [])
        for repo in repos:
            src = JUNIPER / repo
            if not (src / "pyproject.toml").exists():
                print(f"checkout {src} is missing")
                return 2
            dst = args.work / "trees" / repo
            dst.mkdir(parents=True, exist_ok=True)
            if run(["rsync", "-a", "--delete", "--exclude", ".git", f"{src}/", f"{dst}/"], args.work, env, logs / "prepare.log"):
                return 1
    if args.phase == "prepare":
        return 0

    if not (conda_env / "bin" / "python").exists():
        print(f"conda env {conda_env} does not exist")
        return 2
    if args.phase in ("install", "all"):
        log = logs / "install.log"
        if not (venv / "bin" / "python").exists():
            if run([str(conda_env / "bin" / "python"), "-m", "venv", "--system-site-packages", str(venv)], tree, env, log):
                return 1
        for step in cfg["pip"]:
            if run([str(venv / "bin" / "python"), "-m", "pip", *[s.format(tree=tree, data_client=data_client) for s in step]], tree, env, log):
                return 1
        run([str(venv / "bin" / "python"), "-m", "pip", "list", "--format=freeze"], tree, env, logs / "venv-pip-freeze.txt")
    if args.phase in ("test", "all"):
        for d in cfg["dirs"]:
            (tree / d).mkdir(parents=True, exist_ok=True)
        summary = {"env_overrides": overrides} if overrides else {}
        for lane, lane_args in cfg["lanes"].items():
            if args.lane not in ("all", lane):
                continue
            junit = logs / f"junit-{lane}.xml"
            junit.unlink(missing_ok=True)
            if overrides:
                with (logs / f"pytest-{lane}.log").open("a") as fh:
                    fh.write(f"\n# env overrides: {json.dumps(overrides)}\n")
            rc = run([str(venv / "bin" / "python"), "-m", "pytest", *lane_args, f"--junitxml={junit}"], tree, env, logs / f"pytest-{lane}.log")
            res = junit_counts(junit) if junit.exists() else {"error": "no junit xml"}
            res["exit"] = rc
            cov = tree / "reports" / "coverage.json"
            if lane == "unit" and cov.exists():
                with cov.open() as fh:
                    res["coverage_percent"] = round(json.load(fh)["totals"]["percent_covered"], 2)
            summary[lane] = res
            print(f"  {lane}: " + json.dumps({k: v for k, v in res.items() if k != "bad"}))
            for b in res.get("bad", [])[:200]:
                print(f"    {b}")
        with (logs / f"summary-{args.lane}.json").open("w") as fh:
            json.dump(summary, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
