"""
Order-dependence and isolation probe for the flood-4 tests carrier's sub-package slice: run each of
the 15 carried test files ALONE (CI-parity venv), then the full juniper-service-core suite and the
juniper-ci-tools docs_additions_check file under pytest-randomly with several seeds, and list the
slowest slice tests from the CI-parity junit (real-time waits are a flake risk under load).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 carrier validation, sub-package slice)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (BRIEF_VALIDATE.txt)

Usage: python3 <this> <worktree> <venv root> <scratch dir>
"""

import ast
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

SC_FILES = [
    "test_anomaly_detector_edges.py",
    "test_attachment_budget_exact.py",
    "test_lifecycle_paused_terminal.py",
    "test_middleware.py",
    "test_registry_measured_zero.py",
    "test_replay_speed_range_edges.py",
    "test_request_body_limit_boundary.py",
    "test_security.py",
    "test_submit_result_anomaly_accepts.py",
    "test_task_reassignment_timeout_boundary.py",
    "test_websocket_control_security.py",
    "test_websocket_replay_continuity.py",
    "test_workers_coverage.py",
    "test_ws_frame_exact_cap.py",
]
SEEDS = ["1", "424242", "987654321"]


def junit_counts(path):
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    failed = []
    for case in ET.parse(path).iter("testcase"):
        counts["tests"] += 1
        for child in case:
            if child.tag == "failure":
                counts["failures"] += 1
                failed.append(f"{case.get('classname')}::{case.get('name')}")
            elif child.tag == "error":
                counts["errors"] += 1
                failed.append(f"{case.get('classname')}::{case.get('name')}")
            elif child.tag == "skipped":
                counts["skipped"] += 1
    return counts, failed


def defined_tests(path):
    with open(path) as fh:
        tree = ast.parse(fh.read())
    n = 0
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            n += 1
        elif isinstance(node, ast.ClassDef):
            n += sum(1 for s in node.body if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)) and s.name.startswith("test_"))
    return n


def run(cmd, cwd, log_path, junit):
    if os.path.exists(junit):
        os.remove(junit)
    with open(log_path, "w") as log:
        log.write(f"$ (cwd={cwd}) {' '.join(cmd)}\n")
        log.flush()
        rc = subprocess.run(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT).returncode
    counts, failed = junit_counts(junit) if os.path.exists(junit) else ({}, [])
    return rc, counts, failed


def main(argv):
    wt, venv_root, scratch = argv[1:4]
    junit_dir = os.path.join(wt, "tmp", "val-junit")
    log_dir = os.path.join(scratch, "order")
    os.makedirs(junit_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    out = {"alone": {}, "random": {}, "slowest": []}
    sc_py = os.path.join(venv_root, "sc-3.12", "bin", "python")
    ct_py = os.path.join(venv_root, "ct-3.12", "bin", "python")
    rnd_py = os.path.join(venv_root, "rand-3.12", "bin", "python")
    for name in SC_FILES:
        rel = f"juniper-service-core/tests/{name}"
        junit = os.path.join(junit_dir, f"alone-{name}.xml")
        rc, counts, failed = run([sc_py, "-m", "pytest", rel, "-p", "no:cacheprovider", "-q", f"--junitxml={junit}"], wt, os.path.join(log_dir, f"alone-{name}.log"), junit)
        out["alone"][rel] = {"exit": rc, "counts": counts, "failed": failed, "defined_test_functions": defined_tests(os.path.join(wt, rel))}
        print(f"alone {rel}: exit={rc} {counts} defined={out['alone'][rel]['defined_test_functions']}")
    rel = "tests/test_docs_additions_check.py"
    junit = os.path.join(junit_dir, "alone-test_docs_additions_check.xml")
    rc, counts, failed = run([ct_py, "-m", "pytest", rel, "-p", "no:cacheprovider", "-q", f"--junitxml={junit}"], os.path.join(wt, "juniper-ci-tools"), os.path.join(log_dir, "alone-test_docs_additions_check.log"), junit)
    out["alone"]["juniper-ci-tools/" + rel] = {"exit": rc, "counts": counts, "failed": failed, "defined_test_functions": defined_tests(os.path.join(wt, "juniper-ci-tools", rel))}
    print(f"alone juniper-ci-tools/{rel}: exit={rc} {counts}")
    for seed in SEEDS:
        junit = os.path.join(junit_dir, f"rand-sc-{seed}.xml")
        rc, counts, failed = run([rnd_py, "-m", "pytest", "juniper-service-core/tests/", "-p", "no:cacheprovider", "-q", "-p", "randomly", f"--randomly-seed={seed}", f"--junitxml={junit}"], wt, os.path.join(log_dir, f"rand-sc-{seed}.log"), junit)
        out["random"][f"service-core seed={seed}"] = {"exit": rc, "counts": counts, "failed": failed}
        print(f"random service-core seed={seed}: exit={rc} {counts} failed={failed}")
        junit = os.path.join(junit_dir, f"rand-ct-{seed}.xml")
        rc, counts, failed = run([rnd_py, "-m", "pytest", "tests/test_docs_additions_check.py", "-p", "no:cacheprovider", "-q", "-p", "randomly", f"--randomly-seed={seed}", f"--junitxml={junit}"], os.path.join(wt, "juniper-ci-tools"), os.path.join(log_dir, f"rand-ct-{seed}.log"), junit)
        out["random"][f"ci-tools docs_additions seed={seed}"] = {"exit": rc, "counts": counts, "failed": failed}
        print(f"random ci-tools seed={seed}: exit={rc} {counts} failed={failed}")
    full = os.path.join(junit_dir, "junit-sc-3.12.xml")
    rows = []
    for case in ET.parse(full).iter("testcase"):
        cls = case.get("classname", "")
        mod = cls.split(".")[1] if cls.count(".") >= 1 else cls
        if f"{mod}.py" in SC_FILES:
            rows.append((float(case.get("time", "0")), f"{cls}::{case.get('name')}"))
    rows.sort(reverse=True)
    out["slowest"] = [{"seconds": t, "test": n} for t, n in rows[:8]]
    out["slice_total_seconds_sc312"] = round(sum(t for t, _ in rows), 3)
    out["slice_collected_sc312"] = len(rows)
    print("slowest:", out["slowest"][:5], "total:", out["slice_total_seconds_sc312"], "collected:", len(rows))
    with open(os.path.join(scratch, "order_isolation_summary.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
