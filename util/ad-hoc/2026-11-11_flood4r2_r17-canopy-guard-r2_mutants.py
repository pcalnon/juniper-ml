"""
Mutation checks for round 2 of the ruling-17 unit-lane network guard: the F1 and F2 edits, and round 1's eight.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round 2 of the Overtoad's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt)

Usage:
    python3 <this file> --carrier <carrier worktree> --probe <probe worktree> --out <dir> --python <label>=<interpreter> [--python ...] [--only r2|r1|all]

Each mutant is one textual replacement in the PROBE's src/tests/conftest.py (the old text must occur exactly once in
the carrier's copy, which is never written). Stale __pycache__ directories under the probe's src/tests are deleted,
src/tests/unit/test_unit_lane_network_guard.py is run through 2026-11-11_flood4r2_r17-canopy-guard-r2_run_lane.py
(the CI-like environment and the fence), and the mutant is KILLED when every test named for it fails. The probe's
conftest.py is then restored from the carrier and its sha256 compared. The round-2 mutants (the F1 and F2 edits of
the validator's findings) run under every interpreter given; round 1's eight run under the first only. A last
unmutated run per interpreter shows the restored tree passes. <dir>/mutants.json holds every result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_LANE = HERE / "2026-11-11_flood4r2_r17-canopy-guard-r2_run_lane.py"
CONFTEST = "src/tests/conftest.py"
GUARD_TESTS = "src/tests/unit/test_unit_lane_network_guard.py"

RECORD_OLD = 'self.refused.append(f"{address[0]}:{address[1]}" if thread is threading.main_thread() else f"{address[0]}:{address[1]} (thread {thread.name})")'
MESSAGE_OLD = "a connect to {', '.join(sorted(set(refused)))}, a Juniper service port, was refused while this test ran (made by this test, or by a thread or task an earlier test left running). A unit test"
XFAIL_OLD = '        if hasattr(report, "wasxfail"):\n            del report.wasxfail  # an xfail marker must not turn the guard\'s failure back into a skip (exit 0, junit "skipped")\n'
TAKE_OLD = "        refused = self.take()\n        if not refused:\n            return\n"

# (id, what it undoes, old text, mutant text, tests that must ALL fail)
R2_MUTANTS = [
    ("R2-F1-thread-name-dropped", "F1 edit 2 reverted: a refusal off the main thread is recorded without its thread", RECORD_OLD, 'self.refused.append(f"{address[0]}:{address[1]}")', ["test_a_refusal_off_the_main_thread_names_the_thread"]),
    ("R2-F1-thread-name-always", "F1 edit 2 over-applied: the main thread's refusals carry a thread name too", RECORD_OLD, 'self.refused.append(f"{address[0]}:{address[1]} (thread {thread.name})")', ["test_a_service_port_connect_is_refused", "test_connect_ex_reports_econnrefused"]),
    ("R2-F1-message-blames-the-test", "F1 edit 3 reverted: the message says this test connected", MESSAGE_OLD, "this test connected to {', '.join(sorted(set(refused)))}, a Juniper service port. A unit test", ["test_the_failure_message_does_not_blame_the_running_test"]),
    ("R2-F2-wasxfail-kept", "F2 reverted: flag() leaves wasxfail on the report", XFAIL_OLD, "", ["test_flag_fails_an_xfailed_report_too", "test_the_report_hook_fails_an_xfailed_phase_too"]),
    ("R2-F2-wasxfail-always-dropped", "F2 over-applied: wasxfail is dropped even when no connect was refused", TAKE_OLD, '        refused = self.take()\n        if hasattr(report, "wasxfail"):\n            del report.wasxfail\n        if not refused:\n            return\n', ["test_flag_leaves_an_xfailed_report_without_refusals_alone"]),
]
R1_MUTANTS = [
    ("M1-port-range", "round 1", "SERVICE_PORTS = frozenset({*range(8050, 8060), ", "SERVICE_PORTS = frozenset({*range(8050, 8059), ", ["test_a_service_port_connect_is_refused[address2]"]),
    ("M2-ipv4-only", "round 1", "sock.family not in (socket.AF_INET, socket.AF_INET6)", "sock.family not in (socket.AF_INET,)", ["test_an_ipv6_service_port_connect_is_refused"]),
    ("M3-flag-keeps-pass", "round 1", '            report.outcome = "failed"\n', '            report.outcome = "passed"\n', ["test_flag_fails_a_passing_report_whose_refusal_was_swallowed", "test_the_report_hook_fails_a_phase_that_swallowed_a_refusal"]),
    ("M4-connect-ex-zero", "round 1", "    if _SERVICE_PORT_GUARD.refuses(sock, address):\n        return errno.ECONNREFUSED\n", "    if _SERVICE_PORT_GUARD.refuses(sock, address):\n        return 0\n", ["test_connect_ex_reports_econnrefused"]),
    ("M5-unit-marker-ignored", "round 1", "return in_unit_lane or (item.get_closest_marker", "return in_unit_lane and (item.get_closest_marker", ["test_the_guard_is_armed_for_the_unit_lane_only"]),
    ("M6-never-armed", "round 1", "_SERVICE_PORT_GUARD.armed_for = item.nodeid if ServicePortGuard.applies_to(item) else None", "_SERVICE_PORT_GUARD.armed_for = None", ["test_this_test_is_armed", "test_a_service_port_connect_is_refused"]),
    ("M7-report-hook-inert", "round 1", "    report = yield\n    _SERVICE_PORT_GUARD.flag(report)\n    return report\n", "    report = yield\n    return report\n", ["test_the_report_hook_fails_a_phase_that_swallowed_a_refusal"]),
    ("M8-opt-out-ignored", "round 1", '_UNGUARDED_MARKERS = ("allow_service_ports", "e2e",', '_UNGUARDED_MARKERS = ("e2e",', ["test_the_opt_out_marker_disarms_the_guard", "test_the_guard_is_armed_for_the_unit_lane_only"]),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_pycache(probe: Path) -> int:
    caches = list((probe / "src" / "tests").rglob("__pycache__"))
    for cache in caches:
        shutil.rmtree(cache, ignore_errors=True)
    return len(caches)


def run_guard_tests(probe: Path, python: str, label: str, out: Path) -> dict:
    subprocess.run([sys.executable, str(RUN_LANE), "--tree", str(probe), "--python", python, "--label", label, "--out", str(out), "--mode", "files", "--paths", GUARD_TESTS], check=True, capture_output=True)  # nosec B603 - fixed argv
    return json.loads((out / f"{label}.summary.json").read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Mutation checks for round 2 of the ruling-17 unit-lane network guard.")
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python", required=True, action="append", help="<label>=<interpreter>")
    parser.add_argument("--only", choices=("r2", "r1", "all"), default="all")
    args = parser.parse_args()
    carrier, probe, out = args.carrier.resolve(), args.probe.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    interpreters = [entry.split("=", 1) for entry in args.python]
    original = (carrier / CONFTEST).read_text(encoding="utf-8")
    pristine = sha256(carrier / CONFTEST)
    if sha256(probe / CONFTEST) != pristine:
        raise SystemExit("[mutants] the probe's conftest.py differs from the carrier's before any mutation")
    plan = []
    if args.only in ("r2", "all"):
        plan += [(mutant, interpreter) for mutant in R2_MUTANTS for interpreter in interpreters]
    if args.only in ("r1", "all"):
        plan += [(mutant, interpreters[0]) for mutant in R1_MUTANTS]
    results = []
    for (mutant_id, undoes, old, new, expect), (tag, python) in plan:
        if original.count(old) != 1:
            raise SystemExit(f"[mutants] {mutant_id}: the mutated text occurs {original.count(old)} times in the carrier's {CONFTEST}")
        (probe / CONFTEST).write_text(original.replace(old, new), encoding="utf-8")
        cleared = clear_pycache(probe)
        label = f"mut-{mutant_id}-{tag}"
        summary = run_guard_tests(probe, python, label, out)
        failed = [entry["id"] for entry in summary["junit"].get("failed", [])]
        missing = [name for name in expect if not any(name in nodeid for nodeid in failed)]
        shutil.copyfile(carrier / CONFTEST, probe / CONFTEST)
        restored = sha256(probe / CONFTEST) == pristine
        clear_pycache(probe)
        result = {"mutant": mutant_id, "undoes": undoes, "interpreter": tag, "versions": summary["versions"], "exit": summary["exit"], "tests": summary["junit"].get("tests"), "failed": failed, "must_all_fail": expect, "not_failed": missing, "result": "killed" if not missing and failed else "survived", "pycache_dirs_cleared_before": cleared, "restored_sha256_matches_carrier": restored, "log": str(out / f"{label}.log")}
        results.append(result)
        print(f"[mutants] {mutant_id} [{tag}]: {result['result']} (exit {summary['exit']}, {len(failed)} failed of {result['tests']}), restored={restored}")
        if not restored:
            raise SystemExit("[mutants] restore FAILED; stopping")
    baseline = []
    for tag, python in interpreters:
        summary = run_guard_tests(probe, python, f"mut-baseline-after-{tag}", out)
        baseline.append({"interpreter": tag, "versions": summary["versions"], "exit": summary["exit"], "junit": {key: summary["junit"].get(key) for key in ("tests", "failures", "errors", "skipped")}})
        print(f"[mutants] unmutated after restore [{tag}]: exit {summary['exit']}, {baseline[-1]['junit']}")
    record = {"carrier_conftest_sha256": pristine, "probe_conftest_sha256_after": sha256(probe / CONFTEST), "mutants": results, "unmutated_after_restore": baseline}
    (out / "mutants.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    survived = [entry["mutant"] for entry in results if entry["result"] != "killed"]
    print(f"[mutants] {len(results) - len(survived)} of {len(results)} killed; survived: {survived}")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
