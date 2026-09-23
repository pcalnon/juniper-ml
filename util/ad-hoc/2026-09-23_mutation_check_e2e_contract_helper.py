"""
Mutation-check canopy's NPZ contract helper tests (``TestTheContractHelperItself``).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy fix/e2e-test-three-partition-contract (``src/tests/integration/test_juniper_data_e2e.py``)

Each mutation re-introduces one way the helper could be wrong -- the retired contract it was on
until 2026-09-23 among them -- and the helper's own tests must fail for every one. A mutation that
leaves them green means the tests cannot see that defect.

The file is restored byte-for-byte after every mutation (try/finally), and the script refuses to
run if a mutation's anchor text is not found exactly once, so it can never "pass" a mutation it did
not apply.

Usage:
    python util/ad-hoc/2026-09-23_mutation_check_e2e_contract_helper.py <canopy-worktree>
"""

import os
import subprocess
import sys
from pathlib import Path

REL = Path("src/tests/integration/test_juniper_data_e2e.py")
PYTHON = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"

MUTATIONS = {
    "M1 the retired *_full pair is required again": (
        'NPZ_REQUIRED_KEYS = {"X_train", "y_train", "X_val", "y_val", "X_test", "y_test"}',
        'NPZ_REQUIRED_KEYS = {"X_train", "y_train", "X_val", "y_val", "X_test", "y_test", "X_full", "y_full"}',
    ),
    "M2 the val partition is not required": (
        'NPZ_REQUIRED_KEYS = {"X_train", "y_train", "X_val", "y_val", "X_test", "y_test"}',
        'NPZ_REQUIRED_KEYS = {"X_train", "y_train", "X_test", "y_test"}',
    ),
    "M3 the dataset size is train + test (the pre-decision-11 identity)": (
        "    n_total = sum(counts.values())\n",
        '    n_total = counts["train"] + counts["test"]\n',
    ),
    "M4 a legacy *_full pair is not checked against the concatenation": (
        "    if keys & NPZ_LEGACY_KEYS:\n",
        "    if False:\n",
    ),
}


def run_helper_tests(worktree: Path) -> tuple[int, str]:
    env = dict(os.environ, LIBTORCH="", LD_LIBRARY_PATH="")
    proc = subprocess.run(
        [PYTHON, "-m", "pytest", str(REL.relative_to("src")), "-k", "TestTheContractHelperItself", "-p", "no:cacheprovider", "-rA"],
        cwd=worktree / "src",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr.strip()[-300:]
    return proc.returncode, tail


def main() -> int:
    worktree = Path(sys.argv[1]).resolve()
    target = worktree / REL
    original = target.read_bytes()
    text = original.decode()

    code, tail = run_helper_tests(worktree)
    print(f"baseline: exit={code} :: {tail}")
    if code != 0:
        print("baseline is not green; refusing to judge mutations against it")
        return 2

    survivors = []
    for name, (anchor, replacement) in MUTATIONS.items():
        if text.count(anchor) != 1:
            print(f"{name}: anchor found {text.count(anchor)} times, expected 1 -- REFUSING")
            return 2
        try:
            target.write_text(text.replace(anchor, replacement))
            code, tail = run_helper_tests(worktree)
        finally:
            target.write_bytes(original)
        verdict = "KILLED" if code != 0 else "SURVIVED"
        if code == 0:
            survivors.append(name)
        print(f"{name}: {verdict} (exit={code}) :: {tail}")

    assert target.read_bytes() == original, "restore failed"
    print(f"restored byte-for-byte; survivors: {survivors or 'none'}")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
