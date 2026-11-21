#!/usr/bin/env python3
"""
Write the edit spec that applies the round-2 tests validator's F2 to the juniper-data data-tests carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: validator findings -> data-tests carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/data-tests-lens/findings.json F2

Usage:
  2026-11-08_flood4r2_fix_data-tests_edit_spec.py <data-tests worktree> <out edits.json>

tests-F2 is the validator's exact docstring replacement in test_request_body_exact_cap.py (#520). Because the
carrier's CHANGELOG entry lists each draft's docstring fix under "Fixed on the way in", #520's joins them, first
(draft order), re-flowed at the entry's width (118, six-space continuation). Applied with
2026-11-08_flood4r2_fix_apply_edits.py; a re-run reports edits already made as already-applied.
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

ANCHOR = "  - **Fixed on the way in.**\n    - #522 put its pin row above"


def main(argv: list[str]) -> int:
    worktree, out = argv[1], Path(argv[2])
    bullet = (
        "#520's chunked-body docstring said checking each chunk on its own, or using `>=`, \"accepts the cross and rejects "
        "the exact landing\". Each mistake does one of the two: a per-chunk check accepts the cross, and `>=` rejects the "
        "exact landing. The docstring now says which."
    )
    wrapped = "\n".join(textwrap.wrap(bullet, width=118, initial_indent="    - ", subsequent_indent="      ", break_long_words=False, break_on_hyphens=False))
    edits = [
        {
            "id": "tests-F2",
            "file": "juniper_data/tests/unit/test_request_body_exact_cap.py",
            "old": "Checking each chunk on its own, or using ``>=``, accepts\n        the cross and rejects the exact landing.",
            "new": "Checking each chunk on its own accepts\n        the cross; using ``>=`` rejects the exact landing.",
        },
        {
            "id": "tests-F2-changelog",
            "file": "CHANGELOG.md",
            "old": ANCHOR,
            "new": "  - **Fixed on the way in.**\n" + wrapped + "\n    - #522 put its pin row above",
        },
    ]
    out.write_text(json.dumps({"worktree": worktree, "edits": edits}, indent=1) + "\n", encoding="utf-8")
    print(wrapped)
    print(f"line lengths: {[len(line) for line in wrapped.splitlines()]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
