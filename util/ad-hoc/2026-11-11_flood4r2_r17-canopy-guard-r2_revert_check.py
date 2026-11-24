"""
Show the round-2 guard still catches every test the fixes cover: main's copies of the 8 fixed files, guard kept.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round 2 of the Overtoad's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt)

Usage:
    python3 <this file> --carrier <carrier worktree> --probe <probe worktree> --out <dir> --python <label>=<interpreter>

In the PROBE (never the carrier) the 8 fixed test files are replaced by their content at HEAD (main, where the
tests still make the connects) while the carrier's conftest.py, with the guard, stays. The 8 files are run through
2026-11-11_flood4r2_r17-canopy-guard-r2_run_lane.py. Expected: each of the 16 tests the round-1 census caught on
:8050 fails, every failure is the guard's ("unit-lane network guard" in its message), and any failure beyond the
16 is one of the four relay tests whose control-stream dial to :8200 is a race. The guard refuses in Python and the
fence refuses at the C level besides, so no connect leaves the process. The 8 files are then restored from the
carrier (sha256 compared). <dir>/revert_check.json records the result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import xml.etree.ElementTree as ET  # nosec B405 - our own pytest junit output
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_LANE = HERE / "2026-11-11_flood4r2_r17-canopy-guard-r2_run_lane.py"
FIXED = [
    "src/tests/regression/test_availability_unknown_state.py",
    "src/tests/regression/test_model_picker.py",
    "src/tests/unit/backend/test_cascor_service_adapter_boundary.py",
    "src/tests/unit/frontend/test_dashboard_helpers_coverage.py",
    "src/tests/unit/frontend/test_dashboard_manager.py",
    "src/tests/unit/frontend/test_dashboard_manager_95.py",
    "src/tests/unit/frontend/test_dashboard_manager_handlers.py",
    "src/tests/unit/test_convergence_ui_regression.py",
]
# file stem :: test name, for the 16 tests round 1's census caught connecting to 127.0.0.1:8050
CENSUS_8050 = [
    "test_dashboard_helpers_coverage::test_apply_parameters_success",
    "test_dashboard_manager::test_apply_parameters_success",
    "test_dashboard_manager_95::test_parameter_handlers_with_edge_values",
    "test_dashboard_manager_handlers::test_apply_parameters_handler_success",
    "test_dashboard_manager_handlers::test_apply_parameters_handler_429_backs_off_then_succeeds",
    "test_dashboard_manager_handlers::test_apply_parameters_handler_429_missing_header_uses_fallback",
    "test_convergence_ui_regression::test_apply_with_unchecked_stores_false",
    "test_convergence_ui_regression::test_apply_custom_threshold_stores_value",
    "test_convergence_ui_regression::test_multiple_apply_cycles_preserve_threshold",
    "test_convergence_ui_regression::test_successful_apply_shows_confirmation",
    "test_availability_unknown_state::test_a_state_change_notice_still_wins_over_the_caveat",
    "test_availability_unknown_state::test_nothing_is_disabled_merely_because_availability_is_unknown",
    "test_availability_unknown_state::test_the_caveat_does_not_claim_anything_is_unavailable",
    "test_availability_unknown_state::test_the_caveat_is_raised_when_availability_is_unknown",
    "test_availability_unknown_state::test_the_caveat_persists_rather_than_auto_dismissing",
    "test_model_picker::test_gate_dataset_options_handler_greys_and_clears_for_recurrence",
]
RELAY = ["test_state_message_forwards_progress_fields", "test_adding_candidate_phase_derives_selecting", "test_idle_phase_derives_idle_pool_phase", "test_candidate_progress_message_forwards_candidate_epoch_fields"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_pycache(probe: Path) -> None:
    for cache in list((probe / "src" / "tests").rglob("__pycache__")):
        shutil.rmtree(cache, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Main's copies of the 8 fixed files under the round-2 guard.")
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python", required=True, help="<label>=<interpreter>")
    args = parser.parse_args()
    carrier, probe, out = args.carrier.resolve(), args.probe.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    tag, python = args.python.split("=", 1)
    label = f"revert-check-{tag}"
    if sha256(probe / "src/tests/conftest.py") != sha256(carrier / "src/tests/conftest.py"):
        raise SystemExit("[revert] the probe's conftest.py differs from the carrier's")
    try:
        for path in FIXED:
            blob = subprocess.run(["git", "-C", str(probe), "show", f"HEAD:{path}"], check=True, capture_output=True).stdout  # nosec B603 B607 - read-only
            (probe / path).write_bytes(blob)
        clear_pycache(probe)
        subprocess.run([sys.executable, str(RUN_LANE), "--tree", str(probe), "--python", python, "--label", label, "--out", str(out), "--mode", "files", "--paths", *FIXED], check=True, capture_output=True)  # nosec B603 - fixed argv
    finally:
        restored = {}
        for path in FIXED:
            shutil.copyfile(carrier / path, probe / path)
            restored[path] = sha256(probe / path) == sha256(carrier / path)
        clear_pycache(probe)
    summary = json.loads((out / f"{label}.summary.json").read_text(encoding="utf-8"))
    failures = []
    for case in ET.parse(out / f"{label}.junit.xml").getroot().iter("testcase"):  # nosec B314 - our own pytest junit output
        for child in case:
            if child.tag in ("failure", "error"):
                text = (child.get("message") or "") + " " + (child.text or "")
                failures.append({"id": f"{case.get('classname').rsplit('.', 1)[0].rsplit('.', 1)[-1] if '.Test' in case.get('classname') else case.get('classname').rsplit('.', 1)[-1]}::{case.get('name')}", "classname": case.get("classname"), "kind": child.tag, "by_the_guard": "unit-lane network guard" in text, "names_a_thread": "(thread " in text})
    failed_ids = [entry["id"] for entry in failures]
    missing = [name for name in CENSUS_8050 if name not in failed_ids]
    extra = [entry["id"] for entry in failures if entry["id"] not in CENSUS_8050]
    extra_not_relay = [name for name in extra if name.split("::", 1)[1] not in RELAY]
    record = {
        "versions": summary["versions"],
        "exit": summary["exit"],
        "junit": {key: summary["junit"].get(key) for key in ("tests", "failures", "errors", "skipped")},
        "failures": failures,
        "census_8050_tests_expected": len(CENSUS_8050),
        "census_8050_tests_not_failed": missing,
        "failures_beyond_the_16": extra,
        "failures_beyond_the_16_that_are_not_relay_tests": extra_not_relay,
        "every_failure_is_the_guards": all(entry["by_the_guard"] for entry in failures),
        "guarded_port_connects_at_c_level": summary["guarded_port_connects_past_the_guard"],
        "restored_sha256_matches_carrier": restored,
        "log": str(out / f"{label}.log"),
    }
    (out / "revert_check.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    good = not missing and not extra_not_relay and record["every_failure_is_the_guards"] and all(restored.values())
    print(f"[revert] {summary['versions']}: exit {summary['exit']}, junit {record['junit']}; 16 census tests all failed={not missing}; beyond the 16: {extra}; every failure the guard's={record['every_failure_is_the_guards']}; restored={all(restored.values())}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
