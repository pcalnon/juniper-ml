#!/usr/bin/env python3
"""
Mutation check of juniper-data's scheduled-lane selector pin (juniper_data/tests/unit/test_scheduled_tests_selector.py),
run in a COPY of the carrier tree, never in the carrier itself.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, juniper-data benchmark smoke run)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 session 8: the Overtoad's ruling of 2026-11-14, a daily smoke run of the 41 benchmarks)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_flood4r2_r33-data_lanes.py (the census and the exact-step runs)

WHY THIS EXISTS
A pin that cannot fail pins nothing. This copies the carrier tree (without its `.git` file, caches, reports or tmp/)
to --copy, records the sha256 of every file a mutant touches, then, one mutant at a time: writes the mutated bytes,
runs the pin's module with the given interpreter, restores the original bytes in a `finally:` block and verifies the
sha256. A mutant is KILLED when pytest exits 1 and every test the mutant names failed. The unmutated copy must pass
first (exit 0), and the carrier's own copies of the touched files are hashed before and after, to show they never
changed.

Usage:
    python3 <this> --tree <carrier tree> --copy <new scratch dir> --python <venv python> --out <file.json>
Exit 0 = baseline passed and every mutant was killed; 1 = otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess  # nosec B404 - fixed argv: pytest from the caller's venv
import sys
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
WORKFLOW = ".github/workflows/scheduled-tests.yml"
PYPROJECT = "pyproject.toml"
TEST = "juniper_data/tests/unit/test_scheduled_tests_selector.py"
SELECTOR_LINE = '            -m "slow or integration or performance" \\\n'
STEP_NAME_LINE = "      - name: Run slow / integration tests\n"
TRIGGER_LINE = "  workflow_dispatch:\n"
ADDOPTS_LINE = '    "--benchmark-disable",\n'

# name -> (file, old text, new text, tests that must fail)
MUTANTS = {
    "selector_reverted_to_main": (WORKFLOW, SELECTOR_LINE, '            -m "slow or integration" \\\n', ["test_the_step_selects_slow_integration_and_performance"]),
    "selector_performance_only": (WORKFLOW, SELECTOR_LINE, '            -m "performance" \\\n', ["test_the_step_selects_slow_integration_and_performance"]),
    "timing_enabled_on_the_command": (WORKFLOW, SELECTOR_LINE, SELECTOR_LINE + "            --benchmark-enable \\\n", ["test_the_step_selects_slow_integration_and_performance", "test_the_benchmarks_run_untimed"]),
    "timing_enabled_by_step_env": (WORKFLOW, STEP_NAME_LINE, STEP_NAME_LINE + "        env:\n          PYTEST_ADDOPTS: --benchmark-enable\n", ["test_the_benchmarks_run_untimed"]),
    "addopts_lose_benchmark_disable": (PYPROJECT, ADDOPTS_LINE, "", ["test_the_benchmarks_run_untimed"]),
    "pull_request_trigger_added": (WORKFLOW, TRIGGER_LINE, TRIGGER_LINE + "  pull_request:\n", ["test_the_lane_gates_no_pull_request"]),
    "step_names_a_shell": (WORKFLOW, STEP_NAME_LINE, STEP_NAME_LINE + "        shell: bash\n", ["test_the_step_runs_under_the_default_shell"]),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_pin(python: str, copy: Path, log: Path) -> tuple[int, list[str]]:
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("PYTEST_ADDOPTS", None)
    done = subprocess.run([python, "-m", "pytest", TEST, "-p", "no:cacheprovider", "-rA"], cwd=copy, env=env, capture_output=True, text=True, check=False, timeout=300)  # nosec B603
    log.write_text(done.stdout + done.stderr, encoding="utf-8")
    failed = sorted(set(re.findall(r"^FAILED \S+::(\w+)", done.stdout, flags=re.MULTILINE)))
    return done.returncode, failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--copy", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    ns = parser.parse_args()
    tree, copy = ns.tree.resolve(), ns.copy.resolve()
    if copy.exists():
        print(f"refused: {copy} exists (a fresh copy is made each time)")
        return 1
    touched = sorted({spec[0] for spec in MUTANTS.values()} | {TEST})
    carrier_before = {rel: sha256(tree / rel) for rel in touched}
    shutil.copytree(tree, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "reports", "tmp"))
    copy_before = {rel: sha256(copy / rel) for rel in touched}
    result: dict = {"tree": str(tree), "copy": str(copy), "python": ns.python, "carrier_sha256_before": carrier_before, "copy_sha256_before": copy_before, "mutants": []}
    logs = ns.out.parent / "mutant_logs"
    logs.mkdir(exist_ok=True)
    status, failed = run_pin(ns.python, copy, logs / "baseline.log")
    result["baseline"] = {"exit": status, "failed": failed, "log": str(logs / "baseline.log")}
    ok = status == 0
    for name, (rel, old, new, must_fail) in MUTANTS.items():
        target = copy / rel
        original = target.read_bytes()
        row: dict = {"mutant": name, "file": rel, "old": old, "new": new, "must_fail": must_fail}
        try:
            text = original.decode("utf-8")
            if text.count(old) != 1:
                row["error"] = f"anchor occurs {text.count(old)} times"
                ok = False
                continue
            target.write_bytes(text.replace(old, new, 1).encode("utf-8"))
            row["mutated_sha256"] = sha256(target)
            status, failed = run_pin(ns.python, copy, logs / f"{name}.log")
            row.update({"exit": status, "failed": failed, "log": str(logs / f"{name}.log")})
            row["result"] = "killed" if status == 1 and set(must_fail) <= set(failed) else "survived"
            ok = ok and row["result"] == "killed"
        finally:
            target.write_bytes(original)
            row["restored_sha256_matches"] = sha256(target) == copy_before[rel]
            ok = ok and row["restored_sha256_matches"]
            result["mutants"].append(row)
    result["copy_sha256_after"] = {rel: sha256(copy / rel) for rel in touched}
    result["carrier_sha256_after"] = {rel: sha256(tree / rel) for rel in touched}
    result["carrier_unchanged"] = result["carrier_sha256_after"] == carrier_before
    result["ok"] = bool(ok and result["carrier_unchanged"] and result["copy_sha256_after"] == copy_before)
    ns.out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(f"baseline exit {result['baseline']['exit']} failed {result['baseline']['failed']}")
    for row in result["mutants"]:
        print(f"{row['mutant']:32} {row.get('result', row.get('error'))} exit {row.get('exit')} failed {row.get('failed')} restored {row['restored_sha256_matches']}")
    print(f"carrier unchanged {result['carrier_unchanged']}; ok {result['ok']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
