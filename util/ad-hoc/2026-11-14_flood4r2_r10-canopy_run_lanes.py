#!/usr/bin/env python3
"""
Count what juniper-canopy's CI test lanes select on two trees (main and the port), and run the tests that read ci.yml.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-canopy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530;
         adapted from 2026-11-11_flood4r2_r10-data-client_run_lanes.py (the pilot's), whose lane_argv is per repository

WHY THIS EXISTS
A test no lane selects is not a test. The port adds src/tests/regression/test_gitleaks_pr_scan.py and edits the Security
Scans job, so this shows, on a pristine main checkout and on the port, (1) what each pytest lane of ci.yml and
scheduled-tests.yml SELECTS, by --collect-only with the lane's own marker expression and paths (collect-only, because
some of these lanes start services and another session's live stack shares this host), and (2) the result of a real run
of every test module that reads ci.yml, which an edit of the workflow can break. The lane commands below are copied
from the workflows at the port's base; nothing here reads them at run time, so a workflow edit is compared against
a fixed lane.

Each run is one pytest process with its own basetemp and junit report under --out; at most four run side by side.
Every run has the six Sentry DSN variables set to the empty string, a dead session bus, no bytecode and no pytest
cache. Nothing is written into either tree. It prints no environment variable.

Usage:
    python3.14 <this> --main <main checkout> --port <port checkout> --python <interpreter with the test extra> --out <new dir>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - runs pytest with fixed argv
import xml.etree.ElementTree as ET  # nosec B405 - parses junit reports this script's own runs wrote
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
NEW_FILE = "src/tests/regression/test_gitleaks_pr_scan.py"
#: ci.yml's lanes at the port's base bab3ec8d, and scheduled-tests.yml's (which runs pyproject's testpaths).
LANES = {
    "unit": ["-m", "not requires_cascor and not requires_server and not slow", "src/tests/unit/", "src/tests/regression/", "src/tests/contract/", "src/tests/performance/"],
    "integration": ["-m", "integration and not requires_cascor and not requires_server and not slow", "src/tests/integration"],
    "ui": ["--override-ini=addopts=", "-m", "ui and not slow", "src/tests/ui"],
    "scheduled": ["-m", "slow or integration"],
}
#: Every test module that reads .github/workflows/ci.yml (a grep of src/tests at the base, plus the new file).
WORKFLOW_READERS = [
    "src/tests/regression/test_bandit_sarif_upload.py",
    "src/tests/regression/test_ci_lane_wiring.py",
    "src/tests/regression/test_codecov_token_upload.py",
    "src/tests/regression/test_gitleaks_config.py",
    "src/tests/unit/test_memory_budget_check.py",
]
COLLECTED = re.compile(r"(\d+)(?:/(\d+))? tests? collected(?: \((\d+) deselected\))?|(\d+) deselected|no tests collected")


def child_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("GITLEAKS_BIN", "GITLEAKS_PARITY_REQUIRED", "GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML")}
    env.update({n: "" for n in SENTRY_DSN_NAMES})
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus", "CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0"})
    return env


def junit_counts(path: Path) -> dict:
    if not path.is_file():
        return {"junit": "missing"}
    root = ET.parse(path).getroot()  # nosec B314 - this script's own report
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    total["passed"] = total["tests"] - total["failures"] - total["errors"] - total["skipped"]
    return total


def collect(tree: Path, python: str, lane: str, out: Path, tag: str) -> dict:
    # pyproject's addopts carry one -q, which makes --collect-only print node ids; a second -q would print per-file
    # counts instead. The ui lane drops addopts, so it gets its -q here.
    argv = [python, "-m", "pytest", "--collect-only", "-p", "no:cacheprovider", *LANES[lane], *(["-q"] if lane == "ui" else [])]
    res = subprocess.run(argv, cwd=tree, env=child_env(), capture_output=True, text=True, timeout=1800, check=False)  # nosec B603
    log = out / f"{tag}-collect-{lane}.log"
    log.write_text(res.stdout + res.stderr, encoding="utf-8")
    node_ids = [ln for ln in res.stdout.splitlines() if "::" in ln and not ln.startswith(("ERROR", "FAILED"))]
    summary = [ln for ln in res.stdout.splitlines() if COLLECTED.search(ln)]
    errors = [ln for ln in res.stdout.splitlines() if ln.startswith("ERROR ")]
    return {"tree": tag, "lane": lane, "argv": argv[1:], "exit": res.returncode, "selected_node_ids": len(node_ids), "new_file_node_ids": sum(1 for n in node_ids if n.startswith(NEW_FILE + "::")), "summary": summary[-1:] if summary else [], "collection_errors": errors}


def run_readers(tree: Path, python: str, out: Path, tag: str) -> dict:
    files = [f for f in [*WORKFLOW_READERS, NEW_FILE] if (tree / f).is_file()]
    junit = out / f"{tag}-workflow-readers.junit.xml"
    argv = [python, "-m", "pytest", "-p", "no:cacheprovider", *LANES["unit"][:2], *files, "--timeout=120", f"--junitxml={junit}", f"--basetemp={out / ('bt-' + tag)}"]
    res = subprocess.run(argv, cwd=tree, env=child_env(), capture_output=True, text=True, timeout=1800, check=False)  # nosec B603
    (out / f"{tag}-workflow-readers.log").write_text(res.stdout + res.stderr, encoding="utf-8")
    return {"tree": tag, "files": files, "exit": res.returncode, "counts": junit_counts(junit)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--main", type=Path, required=True)
    ap.add_argument("--port", type=Path, required=True)
    ap.add_argument("--python", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    trees = {"main": args.main.resolve(), "port": args.port.resolve()}
    jobs = [("collect", tag, lane) for tag in trees for lane in LANES] + [("readers", tag, "") for tag in trees]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda j: collect(trees[j[1]], args.python, j[2], out, j[1]) if j[0] == "collect" else run_readers(trees[j[1]], args.python, out, j[1]), jobs))
    (out / "lanes.json").write_text(json.dumps({"python": args.python, "trees": {k: str(v) for k, v in trees.items()}, "results": results}, indent=1) + "\n", encoding="utf-8")
    for r in results:
        if "lane" in r:
            print(f"{r['tree']:5} collect {r['lane']:12} exit={r['exit']} selected={r['selected_node_ids']} new_file={r['new_file_node_ids']} {r['summary']} collection_errors={len(r['collection_errors'])}")
        else:
            print(f"{r['tree']:5} workflow readers exit={r['exit']} {r['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
