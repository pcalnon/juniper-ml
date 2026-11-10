"""
Run juniper-service-core and juniper-ci-tools suites exactly as ci-service-core.yml / ci-ci-tools.yml
do (same cwd, same pytest args, same --cov-fail-under, then the per-file coverage gate from PyPI
juniper-ci-tools>=0.9.0,<0.10.0), once per CI-matrix interpreter, and summarise per-test outcomes for
a named slice of test files (from a junit xml written under the worktree's tmp/).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 carrier validation, sub-package slice)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (BRIEF_VALIDATE.txt)

Usage: python3 <this> <worktree> <venv root> <scratch dir> [names...]
  names default to sc-3.12 sc-3.13 sc-3.14 ct-3.11 ct-3.12 ct-3.13 ct-3.14
"""

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

SLICE = {
    "juniper-service-core/tests/test_anomaly_detector_edges.py",
    "juniper-service-core/tests/test_attachment_budget_exact.py",
    "juniper-service-core/tests/test_lifecycle_paused_terminal.py",
    "juniper-service-core/tests/test_middleware.py",
    "juniper-service-core/tests/test_registry_measured_zero.py",
    "juniper-service-core/tests/test_replay_speed_range_edges.py",
    "juniper-service-core/tests/test_request_body_limit_boundary.py",
    "juniper-service-core/tests/test_security.py",
    "juniper-service-core/tests/test_submit_result_anomaly_accepts.py",
    "juniper-service-core/tests/test_task_reassignment_timeout_boundary.py",
    "juniper-service-core/tests/test_websocket_control_security.py",
    "juniper-service-core/tests/test_websocket_replay_continuity.py",
    "juniper-service-core/tests/test_workers_coverage.py",
    "juniper-service-core/tests/test_ws_frame_exact_cap.py",
    "juniper-ci-tools/tests/test_docs_additions_check.py",
}


def run(cmd, cwd, log_path, env=None):
    with open(log_path, "w") as log:
        log.write(f"$ (cwd={cwd}) {' '.join(cmd)}\n")
        log.flush()
        proc = subprocess.run(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, env=env)
        log.write(f"\n[exit {proc.returncode}]\n")
    return proc.returncode


def parse_junit(path, prefix):
    out = {}
    tree = ET.parse(path)
    for case in tree.iter("testcase"):
        classname = case.get("classname", "")
        name = case.get("name", "")
        # classname is dotted module path (+ class); map back to a repo-relative file
        parts = classname.split(".")
        mod_parts = []
        for p in parts:
            mod_parts.append(p)
            if p.startswith("test_"):
                break
        rel = prefix + "/".join(mod_parts) + ".py"
        status = "passed"
        for child in case:
            if child.tag in ("failure", "error"):
                status = child.tag
            elif child.tag == "skipped":
                status = "skipped"
        out.setdefault(rel, []).append({"test": f"{classname}::{name}", "status": status})
    return out


def main(argv):
    wt, venv_root, scratch = argv[1:4]
    names = argv[4:] or ["sc-3.12", "sc-3.13", "sc-3.14", "ct-3.11", "ct-3.12", "ct-3.13", "ct-3.14"]
    junit_dir = os.path.join(wt, "tmp", "val-junit")
    os.makedirs(junit_dir, exist_ok=True)
    gate = os.path.join(venv_root, "gate-3.12", "bin", "juniper-coverage-gap-map")
    summary = {}
    for name in names:
        py = os.path.join(venv_root, name, "bin", "python")
        junit = os.path.join(junit_dir, f"junit-{name}.xml")
        cov_json = os.path.join(scratch, f"coverage-{name}.json")
        if name.startswith("sc-"):
            pkg, cwd, prefix = "juniper_service_core", wt, ""
            cmd = [py, "-m", "pytest", "juniper-service-core/tests/", "-v", "--cov=juniper_service_core", "--cov-report=term-missing", f"--cov-report=json:{cov_json}", "--cov-fail-under=80", f"--junitxml={junit}"]
            gate_cmd = [gate, "--coverage-json", cov_json, "--enforce"]
        else:
            pkg, cwd, prefix = "juniper_ci_tools", os.path.join(wt, "juniper-ci-tools"), "juniper-ci-tools/"
            cmd = [py, "-m", "pytest", "--cov=juniper_ci_tools", "--cov-report=term-missing", f"--cov-report=json:{cov_json}", "--cov-fail-under=85", f"--junitxml={junit}"]
            gate_cmd = [gate, "--coverage-json", cov_json, "--enforce", "--omit", "*/__main__.py"]
        where = subprocess.run([py, "-I", "-c", f"import {pkg}, sys; print({pkg}.__file__); print(sys.version.split()[0])"], cwd=wt, capture_output=True, text=True).stdout.split()
        rc = run(cmd, cwd, os.path.join(scratch, f"pytest-{name}.log"))
        grc = run(gate_cmd, cwd, os.path.join(scratch, f"gate-{name}.log"))
        per_file = parse_junit(junit, prefix) if os.path.exists(junit) else {}
        failed_all = sorted(t["test"] for f, ts in per_file.items() for t in ts if t["status"] in ("failure", "error"))
        slice_stats = {}
        for f in sorted(SLICE):
            if f.startswith("juniper-ci-tools/") != name.startswith("ct-"):
                continue
            ts = per_file.get(f, [])
            slice_stats[f] = {s: sum(1 for t in ts if t["status"] == s) for s in ("passed", "failure", "error", "skipped")}
        with open(cov_json) as fh:
            totals = json.load(fh).get("totals", {})
        summary[name] = {"import": where, "pytest_exit": rc, "gate_exit": grc, "coverage_percent": totals.get("percent_covered"), "failed_tests": failed_all, "slice": slice_stats}
        print(f"{name}: import={where} pytest_exit={rc} gate_exit={grc} cov={totals.get('percent_covered')} failed={len(failed_all)}")
    with open(os.path.join(scratch, "ci_parity_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
