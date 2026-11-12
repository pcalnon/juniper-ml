"""
Mutation checks for the ruling-17 unit-lane network guard, run in the census probe worktrees.

Builder helper for the owner's ruling 17 ("canopy: tests hit :8050"). Two modes, both under the census
fence (util/ad-hoc/2026-11-09_flood4r2_r17-canopy-guard_census.py), with LD_LIBRARY_PATH removed and
LIBTORCH empty at exec (see the group runner's docstring), and stale ``__pycache__`` removed before each run.

``--guard``: one-line mutants of src/tests/conftest.py's guard, four at a time (one per probe). Each runs
src/tests/unit/test_unit_lane_network_guard.py and must FAIL at least one of the tests named for it
(killed); the probe's conftest.py is then restored byte-for-byte (sha256 checked against the build tree).

``--revert-fixes``: strips every test fix from every probe while keeping the guard (the scripted edits via
2026-11-09_flood4r2_r17-canopy-guard_apply_fixes.py --revert, and the hand-made one by restoring the base
blob), runs the fixed files, and lists which tests the guard failed: each census-caught test should be among
them, and no other. Every probe file is restored from the build tree afterwards (sha256 checked).

``--revert-one <file> --rounds N``: reverts only that file's scripted fixes in every probe and runs it N rounds
in all four probes at once, to measure a revert whose connect is a race (the relay tests' control-stream dial).

Usage:
  python3 <this file> --build <build worktree> --probes <wt1> <wt2> <wt3> <wt4> --out-dir <dir> (--guard | --revert-fixes | --revert-one <file> [--rounds N])

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 (flood-4 session 4), juniper-canopy unit-lane network guard
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess  # nosec B404 - runs the census helper, apply_fixes and a read-only git show
import sys
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
HERE = Path(__file__).resolve().parent
CENSUS = HERE / "2026-11-09_flood4r2_r17-canopy-guard_census.py"
APPLY_FIXES = HERE / "2026-11-09_flood4r2_r17-canopy-guard_apply_fixes.py"
CONFTEST = "src/tests/conftest.py"
GUARD_TESTS = "src/tests/unit/test_unit_lane_network_guard.py"
LANE_ARGS = ["-p", "no:cacheprovider", "-m", "not requires_cascor and not requires_server and not slow", "--timeout=60", "-q"]
CI_ENV = {"CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0", "LIBTORCH": ""}
HAND_FIXED = "src/tests/unit/frontend/test_dashboard_helpers_coverage.py"
FIXED_FILES = [
    HAND_FIXED,
    "src/tests/unit/frontend/test_dashboard_manager.py",
    "src/tests/unit/frontend/test_dashboard_manager_95.py",
    "src/tests/unit/frontend/test_dashboard_manager_handlers.py",
    "src/tests/unit/test_convergence_ui_regression.py",
    "src/tests/regression/test_availability_unknown_state.py",
    "src/tests/regression/test_model_picker.py",
    "src/tests/unit/backend/test_cascor_service_adapter_boundary.py",
]

# (id, old text in conftest.py, mutant text, tests at least one of which must fail)
GUARD_MUTANTS = [
    ("M1-port-range", "SERVICE_PORTS = frozenset({*range(8050, 8060), ", "SERVICE_PORTS = frozenset({*range(8050, 8059), ", ["test_a_service_port_connect_is_refused[address2]"]),
    ("M2-ipv4-only", "sock.family not in (socket.AF_INET, socket.AF_INET6)", "sock.family not in (socket.AF_INET,)", ["test_an_ipv6_service_port_connect_is_refused"]),
    ("M3-flag-keeps-pass", '            report.outcome = "failed"\n', '            report.outcome = "passed"\n', ["test_flag_fails_a_passing_report_whose_refusal_was_swallowed", "test_the_report_hook_fails_a_phase_that_swallowed_a_refusal"]),
    ("M4-connect-ex-zero", "    if _SERVICE_PORT_GUARD.refuses(sock, address):\n        return errno.ECONNREFUSED\n", "    if _SERVICE_PORT_GUARD.refuses(sock, address):\n        return 0\n", ["test_connect_ex_reports_econnrefused"]),
    ("M5-unit-marker-ignored", "return in_unit_lane or (item.get_closest_marker", "return in_unit_lane and (item.get_closest_marker", ["test_the_guard_is_armed_for_the_unit_lane_only"]),
    ("M6-never-armed", "_SERVICE_PORT_GUARD.armed_for = item.nodeid if ServicePortGuard.applies_to(item) else None", "_SERVICE_PORT_GUARD.armed_for = None", ["test_this_test_is_armed", "test_a_service_port_connect_is_refused"]),
    ("M7-report-hook-inert", "    report = yield\n    _SERVICE_PORT_GUARD.flag(report)\n    return report\n", "    report = yield\n    return report\n", ["test_the_report_hook_fails_a_phase_that_swallowed_a_refusal"]),
    ("M8-opt-out-ignored", '_UNGUARDED_MARKERS = ("allow_service_ports", "e2e",', '_UNGUARDED_MARKERS = ("e2e",', ["test_the_opt_out_marker_disarms_the_guard", "test_the_guard_is_armed_for_the_unit_lane_only"]),
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _env() -> dict[str, str]:
    env = {name: value for name, value in os.environ.items() if name not in ("LD_LIBRARY_PATH", "GITHUB_ACTIONS", "GITHUB_STEP_SUMMARY")}
    env.update(CI_ENV)
    return env


def _clear_pycache(probe: Path) -> None:
    for cache in (probe / "src" / "tests").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def _launch(probe: Path, out: Path, log: Path, paths: list[str]) -> subprocess.Popen:
    command = [PYTHON, "-I", str(CENSUS), "--wt", str(probe), "--out", str(out), "--", *LANE_ARGS, *paths]
    with open(log, "w", encoding="utf-8") as fh:
        return subprocess.Popen(command, stdout=fh, stderr=subprocess.STDOUT, env=_env())  # nosec B603 - fixed argv, no shell


def _failed(out: Path) -> list[str]:
    if not out.exists():
        return ["<no census output>"]
    with open(out, encoding="utf-8") as fh:
        return json.load(fh).get("failed", [])


def _restore(build: Path, probe: Path, relpath: str) -> bool:
    shutil.copy2(build / relpath, probe / relpath)
    return _sha(build / relpath) == _sha(probe / relpath)


def run_guard_mutants(build: Path, probes: list[Path], out_dir: Path) -> list[dict]:
    original = (build / CONFTEST).read_text(encoding="utf-8")
    results = []
    for start in range(0, len(GUARD_MUTANTS), len(probes)):
        batch = list(zip(probes, GUARD_MUTANTS[start : start + len(probes)]))
        running = []
        for probe, (mutant_id, old, new, _expect) in batch:
            if original.count(old) != 1:
                raise SystemExit(f"[r17-mutants] {mutant_id}: the mutated text occurs {original.count(old)} times in {CONFTEST}")
            (probe / CONFTEST).write_text(original.replace(old, new), encoding="utf-8")
            _clear_pycache(probe)
            out = out_dir / f"mutant_{mutant_id}.json"
            running.append((probe, mutant_id, out, _launch(probe, out, out_dir / f"mutant_{mutant_id}.log", [GUARD_TESTS])))
        for probe, mutant_id, out, proc in running:
            code = proc.wait()
            failed = _failed(out)
            expect = next(entry[3] for entry in GUARD_MUTANTS if entry[0] == mutant_id)
            killed = any(any(name in nodeid for nodeid in failed) for name in expect)
            restored = _restore(build, probe, CONFTEST)
            _clear_pycache(probe)
            results.append({"mutant": mutant_id, "exit": code, "failed": failed, "expected_any_of": expect, "result": "killed" if killed else "survived", "restored_sha256_matches_build": restored, "log": str(out_dir / f"mutant_{mutant_id}.log")})
            print(f"[r17-mutants] {mutant_id}: {'killed' if killed else 'SURVIVED'} (exit {code}, {len(failed)} failed), conftest restored={restored}")
    return results


def run_revert_fixes(build: Path, probes: list[Path], out_dir: Path) -> dict:
    for probe in probes:
        subprocess.run([sys.executable, str(APPLY_FIXES), "--wt", str(probe), "--revert"], check=True)  # nosec B603 - fixed argv
        base_blob = subprocess.run(["git", "-C", str(probe), "show", f"HEAD:{HAND_FIXED}"], check=True, capture_output=True).stdout  # nosec B603 B607 - read-only
        (probe / HAND_FIXED).write_bytes(base_blob)
        _clear_pycache(probe)
    groups = [FIXED_FILES[index :: len(probes)] for index in range(len(probes))]
    running = []
    for number, (probe, paths) in enumerate(zip(probes, groups), start=1):
        out = out_dir / f"revert_fixes_g{number}.json"
        running.append((out, _launch(probe, out, out_dir / f"revert_fixes_g{number}.log", paths)))
    failed: list[str] = []
    codes = []
    for out, proc in running:
        codes.append(proc.wait())
        failed.extend(_failed(out))
    restored = {}
    for probe in probes:
        for relpath in FIXED_FILES:
            restored[f"{probe.name}:{relpath}"] = _restore(build, probe, relpath)
        _clear_pycache(probe)
    print(f"[r17-mutants] revert-fixes: exits={codes} failed={len(failed)} all restored={all(restored.values())}")
    return {"exits": codes, "failed": sorted(failed), "all_restored_sha256_match_build": all(restored.values())}


def run_revert_one(build: Path, probes: list[Path], out_dir: Path, relpath: str, rounds: int) -> dict:
    """Revert one file's scripted fixes in every probe and run it ``rounds`` x len(probes) times."""
    for probe in probes:
        subprocess.run([sys.executable, str(APPLY_FIXES), "--wt", str(probe), "--revert", "--only", relpath], check=True)  # nosec B603 - fixed argv
        _clear_pycache(probe)
    runs = []
    for round_number in range(1, rounds + 1):
        running = []
        for number, probe in enumerate(probes, start=1):
            out = out_dir / f"revert_one_r{round_number}_p{number}.json"
            running.append((out, _launch(probe, out, out_dir / f"revert_one_r{round_number}_p{number}.log", [relpath])))
        for out, proc in running:
            runs.append({"run": out.stem, "exit": proc.wait(), "failed": _failed(out)})
    restored = all(_restore(build, probe, relpath) for probe in probes)
    for probe in probes:
        _clear_pycache(probe)
    caught = sum(1 for run in runs if run["failed"])
    print(f"[r17-mutants] revert-one {relpath}: {caught} of {len(runs)} runs failed by the guard; restored={restored}")
    return {"file": relpath, "runs": runs, "runs_failed": caught, "restored_sha256_match_build": restored}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--build", required=True, type=Path)
    parser.add_argument("--probes", required=True, nargs=4, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--rounds", type=int, default=2)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--guard", action="store_true")
    mode.add_argument("--revert-fixes", action="store_true")
    mode.add_argument("--revert-one", help="repo-relative file whose scripted fixes are reverted and re-run --rounds times per probe")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.guard:
        record = {"guard_mutants": run_guard_mutants(args.build, args.probes, args.out_dir)}
        name = "mutants_guard.json"
    elif args.revert_one:
        record = {"revert_one": run_revert_one(args.build, args.probes, args.out_dir, args.revert_one, args.rounds)}
        name = "mutants_revert_one.json"
    else:
        record = {"revert_fixes": run_revert_fixes(args.build, args.probes, args.out_dir)}
        name = "mutants_revert_fixes.json"
    with open(args.out_dir / name, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
