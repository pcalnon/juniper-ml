#!/usr/bin/env python3
"""
Tighten the comment above six new ``pytestmark`` lines: "WITHOUT the unit mark" becomes "UNMARKED".

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (a comment-only edit of six test modules; no code line changes)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_d2-data_apply_marks.py; juniper-data#529 (whose comment says "UNMARKED")

Usage:
    python3 <this> --worktree <juniper-data tree>

WHY
The first wording said a test "WITHOUT the ``unit`` mark is ... never run in CI". That is true of an unmarked test and
too broad as a rule: a test marked only ``slow`` or ``integration`` is deselected by its pull-request lane and still
selected by a scheduled lane. juniper-data#529's comment says "an UNMARKED class", which is exact, so the six comments
now say the same. Each replacement asserts that its old text occurs exactly once; a tree already reworded stops the
script. Only comment lines change, so every test and every collected node id is as before.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

UNIT_HEAD = '# CI\'s unit lane runs ``pytest -m "unit and not slow" juniper_data/tests/unit`` with ``--strict-markers``\n'
EDITS: dict[str, tuple[str, str]] = {
    "juniper_data/tests/unit/test_phase1d_security.py": (
        UNIT_HEAD + "# and no auto-marking conftest, so a test here WITHOUT the ``unit`` mark is silently DESELECTED --\n# collected, green locally, and never run in CI. Every test of this module was. The mark is on the\n# module, not on each class, so a class added later cannot repeat it.\n",
        UNIT_HEAD + "# and no auto-marking conftest, so an UNMARKED test here is silently DESELECTED -- collected, green\n# locally, and never run in CI. Every test of this module was. The mark is on the module, not on each\n# class, so a class added later cannot repeat it.\n",
    ),
    "juniper_data/tests/unit/test_local_fs_path_traversal.py": (
        UNIT_HEAD + "# and no auto-marking conftest, so a test here WITHOUT the ``unit`` mark is silently DESELECTED --\n# collected, green locally, and never run in CI. Every test of this module was. The mark is on the\n# module, not on each class, so a class added later cannot repeat it.\n",
        UNIT_HEAD + "# and no auto-marking conftest, so an UNMARKED test here is silently DESELECTED -- collected, green\n# locally, and never run in CI. Every test of this module was. The mark is on the module, not on each\n# class, so a class added later cannot repeat it.\n",
    ),
    "juniper_data/tests/unit/test_r2_1_2_wire_compat.py": (
        UNIT_HEAD + "# and no auto-marking conftest, so a test here WITHOUT the ``unit`` mark is silently DESELECTED --\n# collected, green locally, and never run in CI. Every test of this module was. The mark is on the\n# module, not on the class, so a class added later cannot repeat it.\n",
        UNIT_HEAD + "# and no auto-marking conftest, so an UNMARKED test here is silently DESELECTED -- collected, green\n# locally, and never run in CI. Every test of this module was. The mark is on the module, not on the\n# class, so a class added later cannot repeat it.\n",
    ),
    "juniper_data/tests/unit/test_metadata_cache.py": (
        UNIT_HEAD + "# and no auto-marking conftest, so a class here WITHOUT the ``unit`` mark is silently DESELECTED --\n# collected, green locally, and never run in CI. ``TestCacheAgainstRealStores`` (17 tests) was. The\n# mark is on the module, not on each class, so a class added later cannot repeat it.\n",
        UNIT_HEAD + "# and no auto-marking conftest, so an UNMARKED class here is silently DESELECTED -- collected, green\n# locally, and never run in CI. ``TestCacheAgainstRealStores`` (17 tests) was. The mark is on the\n# module, not on each class, so a class added later cannot repeat it.\n",
    ),
    "juniper_data/tests/unit/test_api_app.py": (
        UNIT_HEAD + "# and no auto-marking conftest, so a class here WITHOUT the ``unit`` mark is silently DESELECTED --\n# collected, green locally, and never run in CI. ``TestErrorSurfaceContract`` (9 tests) was. The\n# mark is on the module, not on each class, so a class added later cannot repeat it.\n",
        UNIT_HEAD + "# and no auto-marking conftest, so an UNMARKED class here is silently DESELECTED -- collected, green\n# locally, and never run in CI. ``TestErrorSurfaceContract`` (9 tests) was. The mark is on the\n# module, not on each class, so a class added later cannot repeat it.\n",
    ),
    "juniper_data/tests/integration/test_security_integration.py": (
        "# conftest, so a test here WITHOUT the ``integration`` mark is silently DESELECTED -- collected, green\n# locally, and never run in CI. Every test of this module was. The mark is on the module, not on each\n# class, so a class added later cannot repeat it.\n",
        "# conftest, so an UNMARKED test here is silently DESELECTED -- collected, green locally, and never run\n# in CI. Every test of this module was. The mark is on the module, not on each class, so a class added\n# later cannot repeat it.\n",
    ),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path, required=True)
    wt = ap.parse_args().worktree.resolve()
    texts = {}
    for rel, (old, _new) in EDITS.items():
        with open(wt / rel, encoding="utf-8") as fh:
            text = fh.read()
        if text.count(old) != 1:
            raise SystemExit(f"{rel}: the old comment occurs {text.count(old)} times, expected 1; nothing was written")
        texts[rel] = text
    for rel, (old, new) in EDITS.items():
        code_before = [ln for ln in texts[rel].splitlines() if not ln.lstrip().startswith("#")]
        after = texts[rel].replace(old, new)
        code_after = [ln for ln in after.splitlines() if not ln.lstrip().startswith("#")]
        if code_before != code_after or after.count("\n") != texts[rel].count("\n"):
            raise SystemExit(f"{rel}: the edit would change a code line or the line count; nothing more was written")
        with open(wt / rel, "w", encoding="utf-8") as fh:
            fh.write(after)
        print(f"reworded {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
