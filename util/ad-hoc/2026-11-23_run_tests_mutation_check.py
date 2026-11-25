"""
Mutation check for tests/test_run_tests.py: each deliberate break of util/run_tests.py must fail its named test.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2615 (its test plan: eight deliberate breaks of the runner each fail their test)

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: does tests/test_run_tests.py bind util/run_tests.py's key behaviours? Mutate, run the test, restore.

Each mutation must make its named test FAIL. Stale bytecode is removed before every run and PYTHONDONTWRITEBYTECODE
is set, and exit codes are read from the subprocess itself, never through a pipe.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "util" / "run_tests.py"
BACKUP = Path(__file__).with_name("run_tests.py.orig")

MUTATIONS = [
    ("bus guard dropped", '"DBUS_SESSION_BUS_ADDRESS": BUS_GUARD,', '"DBUS_SESSION_BUS_ADDRESS_MUTANT": BUS_GUARD,', "RunTest.test_the_child_environment"),
    ("leftovers not swept", '    """Kill what a finished step left in its process group. True when something was left."""\n', '    """Kill what a finished step left in its process group. True when something was left."""\n    return False\n', "RunTest.test_processes_a_step_leaves_behind_are_killed"),
    ("coverage report not moved", 'token = f"--cov-report={kind}:{lane_dir / Path(target).name}"', "pass", "RunTest.test_the_package_lane_tests_this_checkout_and_writes_coverage_to_the_run_directory"),
    ("no re-run alone", "if failures and not args.no_rerun", "if False and failures and not args.no_rerun", "RunTest.test_a_job_that_passes_alone_after_failing_in_parallel_is_a_rerun_pass"),
    ("PYTHONPATH not injected", 'delta["PYTHONPATH"] = os.pathsep.join(str(path) for path in lane.pythonpath)', "pass", "RunTest.test_the_package_lane_tests_this_checkout_and_writes_coverage_to_the_run_directory"),
    ("system temp TMPDIR kept", "if current and Path(current).is_dir() and not under_system_temp(Path(current)):", "if current:", "RunTest.test_a_tmpdir_under_the_system_temp_directory_is_replaced"),
    ("-x ignored", "if result.status in (FAIL, TIMEOUT) and self.fail_fast:", "if False:", "RunTest.test_fail_fast_starts_nothing_after_the_first_failure"),
    ("shell lines accepted", "        need = shell_need(tokens)\n        if need:\n            raise UsageError(f\"{source}", "        need = None\n        if need:\n            raise UsageError(f\"{source}", "RunTest.test_a_ci_line_that_needs_a_shell_is_refused_by_name"),
]


def clear_bytecode() -> None:
    for cache in (ROOT / "util" / "__pycache__", ROOT / "tests" / "__pycache__"):
        for pyc in cache.glob("run_tests*.pyc"):
            pyc.unlink()
        for pyc in cache.glob("test_run_tests*.pyc"):
            pyc.unlink()


def run_test(name: str) -> int:
    env = {key: value for key, value in os.environ.items()}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run([sys.executable, "-m", "unittest", f"tests.test_run_tests.{name}"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)
    return proc.returncode


def main() -> int:
    shutil.copy2(TARGET, BACKUP)
    original = TARGET.read_text()
    clear_bytecode()
    baseline = {name for *_, name in MUTATIONS}
    bad = 0
    try:
        for name in sorted(baseline):
            rc = run_test(name)
            print(f"baseline {'ok  ' if rc == 0 else 'FAIL'} {name}")
            bad += rc != 0
        for label, old, new, test in MUTATIONS:
            if original.count(old) != 1:
                print(f"SKIP {label}: the anchor occurs {original.count(old)} times")
                bad += 1
                continue
            TARGET.write_text(original.replace(old, new))
            clear_bytecode()
            rc = run_test(test)
            caught = rc != 0
            print(f"{'caught ' if caught else 'MISSED '} {label:28s} -> {test} (rc={rc})")
            bad += not caught
            TARGET.write_text(original)
    finally:
        TARGET.write_text(original)
        clear_bytecode()
        assert TARGET.read_text() == BACKUP.read_text(), "restore failed"
    print("all mutations caught" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
