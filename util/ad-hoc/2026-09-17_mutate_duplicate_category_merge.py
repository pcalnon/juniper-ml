#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : release train -- duplicate-category merge
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Mutation-check the duplicate-``### Category`` merge in the two CHANGELOG parsers.

A test that only ever passes is not evidence. This reverts each parser's
``result.setdefault(cat, []).extend(bullets)`` back to the assignment it replaced and
confirms the new tests go RED -- separately, so each test is shown to pin its own parser
rather than both riding on one.

Reads the process exit code rather than grepping output, and sweeps ``__pycache__`` first:
a stale ``.pyc`` makes a mutation look uncaught.
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PY = "/usr/bin/python3"
FIXED = "result.setdefault(current_cat, []).extend(bullets)"
BROKEN = "result[current_cat] = bullets"

TARGETS = {
    "ceremony.py": ("util/release_train/ceremony.py",
                    "tests.test_release_train_ceremony.PureHelperTest."
                    "test_changelog_version_section_merges_a_repeated_category"),
    "notes_render.py": ("util/release_train/notes_render.py",
                        "tests.test_release_train_ceremony.PureHelperTest."
                        "test_parse_unreleased_merges_a_repeated_category"),
}


def run(target: str) -> int:
    for d in REPO.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)
    return subprocess.run([PY, "-m", "unittest", target], cwd=REPO,
                          capture_output=True, text=True).returncode


def main() -> int:
    baseline = run("tests.test_release_train_ceremony")
    print(f"baseline suite: exit={baseline} ({'green' if baseline == 0 else 'RED'})")
    if baseline != 0:
        print("baseline is not green -- fix that before mutating", file=sys.stderr)
        return 2

    failures = 0
    for label, (rel, test) in TARGETS.items():
        path = REPO / rel
        original = path.read_text(encoding="utf-8")
        if FIXED not in original:
            print(f"{label}: anchor missing -- source has drifted", file=sys.stderr)
            return 2
        path.write_text(original.replace(FIXED, BROKEN), encoding="utf-8")
        try:
            code = run(test)
            caught = code != 0
            print(f"  [revert {label:16s}] {test.split('.')[-1]} exit={code} -> "
                  f"{'CAUGHT' if caught else '*** NOT CAUGHT ***'}")
            failures += 0 if caught else 1
        finally:
            path.write_text(original, encoding="utf-8")

    restored = run("tests.test_release_train_ceremony")
    print(f"restored suite: exit={restored} ({'green' if restored == 0 else 'RED'})")
    return 1 if (failures or restored != 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
