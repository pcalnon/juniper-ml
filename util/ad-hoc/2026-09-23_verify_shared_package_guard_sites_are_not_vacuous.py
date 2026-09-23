"""Prove SharedPackageGuardTest fails when a guard leaves the shared package's security.py.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation (non-vacuity check for a new always-on test)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: APD-ECO-008; owner ruling 2026-09-23 (the shared package is a site of both key-handling
         guards); tests/test_service_fork_drift.py; notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md

The test reads ``<juniper-ml root>/juniper-service-core/juniper_service_core/security.py``. This
copies the test and that ONE file into a scratch tree with the same layout, applies each mutation
there, and requires ``test_guards_hold_in_the_shared_package`` to FAIL, naming the guard the
mutation removed. The unmutated copy is the control and must PASS. The checkout is never written.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = Path("tests/test_service_fork_drift.py")
SECURITY = Path("juniper-service-core/juniper_service_core/security.py")
TEST_ID = "tests.test_service_fork_drift.SharedPackageGuardTest.test_guards_hold_in_the_shared_package"

# (name, the guard the mutation removes, old text, new text). Each ``old`` must occur exactly once.
MUTATIONS = (
    ("blank keys are no longer filtered", "blank-api-key-filter", "if isinstance(k, str) and k.strip()}", "}"),
    ("the key filter keeps its type check but not the strip", "blank-api-key-filter", "isinstance(k, str) and k.strip()", "isinstance(k, str)"),
    ("the compare short-circuits again", "nonshortcircuit-key-compare", "return matched", "return any(hmac.compare_digest(api_key, c) for c in self._api_keys)"),
)


def _run(tree: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "unittest", TEST_ID], cwd=tree, capture_output=True, text=True, check=False)


def _fresh_tree(parent: Path, name: str) -> Path:
    tree = parent / name
    for rel in (TEST, SECURITY):
        (tree / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, tree / rel)
    (tree / "tests" / "__init__.py").touch()
    return tree


def main() -> int:
    failures = []
    with tempfile.TemporaryDirectory(prefix="shared-guard-nonvacuity-") as tmp:
        control = _run(_fresh_tree(Path(tmp), "control"))
        print(f"control: exit={control.returncode}")
        if control.returncode != 0:
            print(control.stderr[-2000:])
            return 1
        for index, (name, guard_id, old, new) in enumerate(MUTATIONS, start=1):
            tree = _fresh_tree(Path(tmp), f"m{index}")
            source = (tree / SECURITY).read_text(encoding="utf-8")
            if source.count(old) != 1:
                failures.append(f"M{index} ({name}): anchor occurs {source.count(old)} times, expected 1")
                continue
            (tree / SECURITY).write_text(source.replace(old, new), encoding="utf-8")
            result = _run(tree)
            caught = result.returncode != 0 and f"Guard '{guard_id}' is missing" in result.stderr
            print(f"M{index}: {name}: exit={result.returncode} {'CAUGHT' if caught else 'VACUOUS'}")
            if not caught:
                failures.append(f"M{index} ({name}) was not caught as '{guard_id}'")
    if failures:
        print("FAIL:\n  " + "\n  ".join(failures))
        return 1
    print(f"PASS: {len(MUTATIONS)} mutations, each caught and attributed to its guard; control green.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
