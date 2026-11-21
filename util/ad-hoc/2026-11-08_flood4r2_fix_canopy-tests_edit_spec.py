#!/usr/bin/env python3
"""
Write the edit spec that applies the round-2 validators' findings to the canopy-tests carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: validator findings -> canopy-tests carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/canopy-tests-lens/findings.json F1, F2; tmp/flood4r2-val/canopy-claims-lens/findings.json F7

Usage:
  2026-11-08_flood4r2_fix_canopy-tests_edit_spec.py <canopy-tests worktree> <out edits.json>

The output is applied with 2026-11-08_flood4r2_fix_apply_edits.py. Each finding's text is the validator's EXACT
replacement. Where the replacement lengthens a hard-wrapped line, only the carrier's own lines are re-flowed, at
the width the surrounding text already uses (CHANGELOG entry: 115; the script's module docstring: 116), so no
line main owns is touched.
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path


def _reflow(old: str, find: str, replace: str, width: int, indent: str) -> str:
    joined = " ".join(line.strip() for line in old.splitlines())
    if joined.count(find) != 1:
        raise SystemExit(f"finding text occurs {joined.count(find)} times: {find!r}")
    fixed = joined.replace(find, replace)
    return "\n".join(textwrap.wrap(fixed, width=width, initial_indent=indent, subsequent_indent=indent, break_long_words=False, break_on_hyphens=False)) + "\n"


def main(argv: list[str]) -> int:
    worktree, out = argv[1], Path(argv[2])
    edits = [
        {
            "id": "tests-F1",
            "file": "src/tests/unit/backend/test_apply_partition_flat_legs.py",
            "old": '    def test_a_dict_whose_data_is_not_an_envelope_passes_through(self):\n        frame = {"applied": ["learning_rate"], "data": ["not-an-envelope"]}\n',
            "new": '    @pytest.mark.parametrize("data", [["not-an-envelope"], {"status": "success", "applied": ["learning_rate"]}])\n    def test_a_dict_whose_data_is_not_an_envelope_passes_through(self, data):\n        frame = {"applied": ["learning_rate"], "data": data}\n',
        },
        {
            "id": "tests-F2a",
            "file": "src/tests/unit/test_schema_drift_nested_equality.py",
            "old": "``NaN`` rule, not the list branch.\n",
            "new": "``NaN`` rule, but cannot catch a list branch that compares whole arrays with ``==``.\n",
        },
    ]
    changelog_tail = (
        "  `NaN` equals `NaN` at any depth, and the drift report's `NaN` case pins that rule, not the array branch: `json`\n"
        "  parses every `NaN` to one shared float, which list equality matches by identity, so an `==` over arrays would\n"
        "  not report a matching `NaN` as drift, contrary to the draft's text. The script's docstrings now state the rule\n"
        "  for arrays, with that correction. Tests and docstrings only.\n"
    )
    edits.append(
        {
            "id": "tests-F2b",
            "file": "CHANGELOG.md",
            "old": changelog_tail,
            "new": _reflow(changelog_tail, "case pins that rule, not the array branch: `json`", "case pins that rule but cannot catch an `==` over whole arrays: `json`", 115, "  "),
        }
    )
    module_doc = (
        "``==`` says it is). That rule holds inside arrays, which the comparison does not walk itself: ``[0]`` is not\n"
        "``[false]``, and ``NaN`` equals ``NaN`` at any depth. A generator juniper-data no longer registers is drift as well.\n"
    )
    edits.append(
        {
            "id": "claims-F7",
            "file": "util/check_juniper_data_generator_schemas.py",
            "old": module_doc,
            "new": _reflow(module_doc, "which the comparison does not walk itself", "which the key-by-key walk (``diff_json``) does not enter", 116, ""),
        }
    )
    out.write_text(json.dumps({"worktree": worktree, "edits": edits}, indent=1) + "\n", encoding="utf-8")
    for edit in edits:
        print(f"--- {edit['id']} ({edit['file']})")
        print(edit["new"], end="")
        print(f"    line lengths: {[len(line) for line in edit['new'].splitlines()]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
