#!/usr/bin/env python3
"""
Mutation check: does tests/test_a0_restore_scripts.py bind its `install` stub's safety net, and does the net stop
the regression it exists for?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (mutation check for the a0 suite's install-stub fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the follow-up PR to juniper-ml#2629 that fixed the stub (it refused every /home path, so 10 of the
suite's 17 tests failed wherever TMPDIR is under /home)

Each mutant replaces one passage, exactly once, in the suite's INSTALL_STUB text or in the restore script, runs the
named tests, and must make them FAIL. The control run, unmutated, must pass. Every mutated file's sha256 is taken
first and checked after the restore, so an interrupted run cannot leave a mutant behind unnoticed; the tests run
with PYTHONDONTWRITEBYTECODE=1 and stale bytecode removed. The last mutant removes the restore script's own
refusal: the net must then refuse the real-home path itself (exit 97), and nothing may be created there.

Usage: ``python3 util/ad-hoc/2026-11-24_a0_install_stub_mutation_check.py``. Exit 0 when the control passes and
every mutant is killed, 1 otherwise.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess  # nosec B404 - runs the suite under test with fixed argv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "tests" / "test_a0_restore_scripts.py"
RESTORE = ROOT / "util" / "ad-hoc" / "2026-09-22_restore_server_db_from_fileset.bash"
# The real-home probe the production-default test uses, read from the suite so the two cannot drift apart.
_PROBE = re.search(r'probe = Path\("([^"]+a0-r7-probe-must-not-exist)"\)', SUITE.read_text(encoding="utf-8"))
if _PROBE is None:
    sys.exit("the suite's real-home probe was not found: has the production-default test changed?")
PROBE = Path(_PROBE.group(1))
T = "tests.test_a0_restore_scripts."

# (name, file, old, new, tests that must fail)
MUTANTS = [
    ("lexical match: no realpath", SUITE, 'p="$(realpath -m -- "$a")"', 'p="$a"', [T + "InstallStubSafetyNet.test_resolves_a_dot_dot_walk_out_of_the_scratch_directory"]),
    ("no scratch exemption", SUITE, '"${STUB_SCRATCH}" | "${STUB_SCRATCH}"/*) ;;', '"${STUB_SCRATCH}/never-matches") ;;', [T + "InstallStubSafetyNet.test_creates_inside_its_scratch_directory_even_when_a_home_holds_it"]),
    ("no real-home check", SUITE, '/home | /home/* | "${STUB_HOME}" | "${STUB_HOME}"/*)', "/home | /home/*)", [T + "InstallStubSafetyNet.test_refuses_the_real_home_wherever_it_is"]),
    ("no /home check", SUITE, '/home | /home/* | "${STUB_HOME}" | "${STUB_HOME}"/*)', '"${STUB_HOME}" | "${STUB_HOME}"/*)', [T + "InstallStubSafetyNet.test_refuses_a_path_under_home"]),
    ("no recorded path", SUITE, '"${STUB_INSTALL_FAKE:-/nonexistent/no-fake-path}") echo "made=$p" >> "${STUB_INSTALL_REPORT:?}"; exit 0 ;;', "", [T + "RestoreServerDbFromFileset.test_the_production_default_root_is_the_real_home"]),
    ("the restore script's refusal removed", RESTORE, '"${SOURCE_ROOT}"/*) echo "refusing:', '"${SOURCE_ROOT}/never-matches"/*) echo "refusing:', [T + "RestoreServerDbFromFileset.test_the_production_default_root_is_the_real_home"]),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(tests: list[str]) -> subprocess.CompletedProcess:
    for cache in (ROOT / "tests" / "__pycache__",):
        shutil.rmtree(cache, ignore_errors=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, "-m", "unittest", *tests], cwd=ROOT, env=env, capture_output=True, text=True, timeout=300, check=False)  # nosec B603


def main() -> int:
    before = {path: digest(path) for path in (SUITE, RESTORE)}
    control = run([T + "InstallStubSafetyNet", T + "RestoreServerDbFromFileset", T + "ConfirmA0Premise"])
    ok = control.returncode == 0
    print(f"{'PASS' if ok else 'FAIL'}  control, unmutated: exit {control.returncode}")
    if not ok:
        print(control.stderr[-2000:])
    for name, path, old, new, tests in MUTANTS:
        text = path.read_text(encoding="utf-8")
        count = text.count(old)
        if count != 1:
            print(f"FAIL  {name}: the passage occurs {count} times in {path.name}, not once")
            ok = False
            continue
        existed = PROBE.exists()
        try:
            path.write_text(text.replace(old, new), encoding="utf-8")
            result = run(tests)
        finally:
            path.write_text(text, encoding="utf-8")
        killed = result.returncode != 0
        created = not existed and PROBE.exists()
        verdict = "PASS" if killed and not created else "FAIL"
        ok = ok and verdict == "PASS"
        detail = "killed" if killed else "SURVIVED"
        if path == RESTORE:
            refused_by_net = "install stub REFUSES a host path" in result.stderr
            detail += f"; the net refused the real-home path: {'yes' if refused_by_net else 'NO'}"
            ok = ok and refused_by_net
        print(f"{verdict}  {name}: {detail}; {PROBE} created: {'YES' if created else 'no'}")
    after = {path: digest(path) for path in (SUITE, RESTORE)}
    restored = after == before
    print(f"{'PASS' if restored else 'FAIL'}  every mutated file is back to its sha256")
    return 0 if ok and restored else 1


if __name__ == "__main__":
    sys.exit(main())
