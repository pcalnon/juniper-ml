#!/usr/bin/env python3
"""
Count what juniper-deploy's CI lanes collect on a pristine main tree and on the port, and run the new file against main's workflow.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-deploy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530;
         2026-11-14_flood4r2_r10-cascor-client_run_lanes.py (the sibling port's lane runner)

WHY THIS EXISTS
A test no lane selects is the defect ruling 17 fixed in juniper-data, so the port has to show which lane selects the
new file and count its cases there. juniper-deploy's lanes are read from its ci.yml: the Unit Tests job's one
`pytest tests/ -v --tb=short` (every leg of its matrix), and the Gitleaks job's two self-test steps. The unit lane is
COLLECTED, not run: on this host its live-service tests would reach whatever stack listens on the default ports, and
two of its files render the Helm chart, so running it here could touch the host's running stacks. `--collect-only`
runs no test; `-v` and `--tb=short` change no selection, so the lane's selection is `pytest tests/ --collect-only -q`.
The script also copies the port's new test file into the pristine main tree, runs it there with the real engine
(GITLEAKS_PARITY_REQUIRED=1) to show which cases fail on main's workflow, and deletes the copy (sha256 of every main
file it touches, before and after).

Every child has the six Sentry DSN variables set to the empty string, PYTHONDONTWRITEBYTECODE=1 and no pytest cache.

Usage:
  2026-11-14_flood4r2_r10-deploy_lanes.py --main <pristine main tree> --port <port tree> --python <interpreter>
      --engine <gitleaks binary> --out <dir>

Exit 0 = the port's unit-lane collection is main's plus exactly the new file's cases, the self-test lanes collect what
their steps name, and main's tree is byte-identical afterwards; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess  # nosec B404 - fixed argv: the chosen interpreter running pytest
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
ENGINE_NAMES = ("GITLEAKS_BIN", "GITLEAKS_PARITY_REQUIRED", "GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML")
NEW_FILE = "tests/test_gitleaks_pr_scan.py"
CONFIG_FILE = "tests/test_gitleaks_config.py"


def child_env(engine: str | None = None) -> dict:
    env = {name: value for name, value in os.environ.items() if name not in ENGINE_NAMES}
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if engine is not None:
        env["GITLEAKS_BIN"] = engine
        env["GITLEAKS_PARITY_REQUIRED"] = "1"
    return env


def collect(python: str, tree: Path, targets: list[str], log: Path) -> list[str]:
    argv = [python, "-m", "pytest", *targets, "--collect-only", "-q", "-p", "no:cacheprovider"]
    res = subprocess.run(argv, cwd=tree, capture_output=True, text=True, env=child_env(), check=False, timeout=600)  # nosec B603
    log.write_text("$ " + " ".join(argv) + f"\n[cwd {tree}]\n" + res.stdout + "\n--- stderr ---\n" + res.stderr + f"\n[exit {res.returncode}]\n", encoding="utf-8")
    if res.returncode != 0:
        raise SystemExit(f"collection failed in {tree}: exit {res.returncode}; see {log}")
    return [line.strip() for line in res.stdout.splitlines() if "::" in line and not line.startswith(" ")]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--main", required=True, type=Path)
    ap.add_argument("--port", required=True, type=Path)
    ap.add_argument("--python", required=True)
    ap.add_argument("--engine", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    main_tree, port_tree, out = args.main.resolve(), args.port.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    assert not (main_tree / NEW_FILE).exists(), f"{main_tree / NEW_FILE} exists: the main tree is not pristine"
    main_ci_before = sha(main_tree / ".github" / "workflows" / "ci.yml")

    unit_main = collect(args.python, main_tree, ["tests/"], out / "collect-unit-main.log")
    unit_port = collect(args.python, port_tree, ["tests/"], out / "collect-unit-port.log")
    config_main = collect(args.python, main_tree, [CONFIG_FILE], out / "collect-config-selftest-main.log")
    config_port = collect(args.python, port_tree, [CONFIG_FILE], out / "collect-config-selftest-port.log")
    pr_scan_port = collect(args.python, port_tree, [NEW_FILE], out / "collect-prscan-selftest-port.log")
    added = sorted(set(unit_port) - set(unit_main))
    removed = sorted(set(unit_main) - set(unit_port))

    # The port's test file against MAIN's workflow, with the real engine: copy in, run, delete.
    copy = main_tree / NEW_FILE
    junit = out / "newfile-on-main.junit.xml"
    argv = [args.python, "-m", "pytest", NEW_FILE, "-v", "--tb=line", "-p", "no:cacheprovider", f"--basetemp={out / 'basetemp-on-main'}", f"--junitxml={junit}"]
    (out / "basetemp-on-main").mkdir(parents=True, exist_ok=True)
    copy.write_bytes((port_tree / NEW_FILE).read_bytes())
    try:
        res = subprocess.run(argv, cwd=main_tree, capture_output=True, text=True, env=child_env(args.engine), check=False, timeout=1500)  # nosec B603
    finally:
        copy.unlink()
    (out / "newfile-on-main.log").write_text("$ " + " ".join(argv) + "\n" + res.stdout + "\n--- stderr ---\n" + res.stderr + f"\n[exit {res.returncode}]\n", encoding="utf-8")
    on_main = {"passed": [], "failed": []}
    for case in ElementTree.parse(junit).getroot().iter("testcase"):
        bad = case.find("failure") is not None or case.find("error") is not None
        on_main["failed" if bad else "passed"].append(case.get("name"))
    main_ci_after = sha(main_tree / ".github" / "workflows" / "ci.yml")

    record = {
        "interpreter": args.python,
        "unit_lane": {"command": "pytest tests/ -v --tb=short (collected as: pytest tests/ --collect-only -q)", "main": len(unit_main), "port": len(unit_port), "added": added, "removed": removed, "added_all_in_new_file": all(a.startswith(NEW_FILE + "::") for a in added)},
        "gitleaks_config_selftest": {"command": f"pytest {CONFIG_FILE} -v --tb=short", "main": len(config_main), "port": len(config_port)},
        "gitleaks_pr_scan_selftest": {"command": f"pytest {NEW_FILE} -v --tb=short", "port": len(pr_scan_port)},
        "new_file_on_mains_workflow": {"exit": res.returncode, "passed": on_main["passed"], "failed_count": len(on_main["failed"]), "failed": on_main["failed"]},
        "main_tree_unchanged": main_ci_before == main_ci_after and not copy.exists(),
    }
    (out / "lanes.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: (v if k != "unit_lane" else {kk: vv for kk, vv in v.items() if kk not in ("added", "removed")}) for k, v in record.items() if k != "new_file_on_mains_workflow"}, indent=1))
    print("new file on main's workflow:", res.returncode, "passed", on_main["passed"], "failed", len(on_main["failed"]))
    ok = (
        len(added) == len(pr_scan_port)
        and not removed
        and record["unit_lane"]["added_all_in_new_file"]
        and len(config_main) == len(config_port)
        and record["main_tree_unchanged"]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
