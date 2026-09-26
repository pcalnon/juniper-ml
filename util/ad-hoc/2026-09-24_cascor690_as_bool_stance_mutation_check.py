#!/usr/bin/env python
"""Mutation-check #690's fixup (``_as_bool_stance`` reads ``allow_truncation`` as juniper-data does) on a SCRATCH copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#690; round 3's harness, util/ad-hoc/2026-09-24_cascor688_fixforward_mutation_check.py,
         which this EXTENDS rather than copies -- its 64 mutants run again here, unchanged, beside the
         new ones; the producer's rule was measured by
         util/ad-hoc/2026-09-24_cascor690_bool_stance_producer_table.py.

usage: 2026-09-24_cascor690_as_bool_stance_mutation_check.py <cascor-worktree> <scratch-dir> [MUTANT ...] [--base-dir DIR] [--base-label LABEL]

Same contract as round 3 (it runs round 3's own ``main``): the worktree is copied ONCE to
<scratch-dir>/tree, every edit's anchor must occur exactly once or the mutant is SKIPPED, files are
restored after every run, and an unmutated CONTROL comes first and must be green. ``--base-dir`` holds
``manager.py`` / ``app.py`` as they were at #690's first head (c4e002d); the base pseudo-mutant then asks
whether the new arms fail against the reader they fix.

New here:

* ``FLIP_<spelling>`` -- each of pydantic's twelve strings moved to the OTHER polarity ("flip one
  spelling, and the test must fail"), and ``DROP_<spelling>`` -- each removed, so it reads as no stance;
* ``S*`` -- the reader's other rules: no strip, case-insensitive, 0 / 1 only (int or float), and no
  truthiness fallback for anything else.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND3 = os.path.join(HERE, "2026-09-24_cascor688_fixforward_mutation_check.py")

MGR = "src/api/lifecycle/manager.py"
TRUE_LINE = '_PRODUCER_BOOL_TRUE = frozenset({"1", "on", "t", "true", "y", "yes"})\n'
FALSE_LINE = '_PRODUCER_BOOL_FALSE = frozenset({"0", "off", "f", "false", "n", "no"})\n'
TRUE_SET = ["1", "on", "t", "true", "y", "yes"]
FALSE_SET = ["0", "off", "f", "false", "n", "no"]
FOLD = "            folded = value.lower()\n"
STR_NONE = "            if folded in _PRODUCER_BOOL_FALSE:\n                return False\n            return None\n"
NUMBERS = "        if isinstance(value, (int, float)) and value in (0, 1):\n"
TAIL = "            return bool(value)\n        return None\n"

Edit = Tuple[str, str, str]


def _line(name: str, members: List[str]) -> str:
    return f"{name} = frozenset({{{', '.join(repr(m).replace(chr(39), chr(34)) for m in members)}}})\n"


def new_mutants() -> Dict[str, List[Edit]]:
    out: Dict[str, List[Edit]] = {}
    for spelling in TRUE_SET + FALSE_SET:
        in_true = spelling in TRUE_SET
        true_now = [m for m in TRUE_SET if m != spelling] + ([] if in_true else [spelling])
        false_now = [m for m in FALSE_SET if m != spelling] + ([spelling] if in_true else [])
        out[f"FLIP_{spelling}"] = [(MGR, TRUE_LINE, _line("_PRODUCER_BOOL_TRUE", true_now)), (MGR, FALSE_LINE, _line("_PRODUCER_BOOL_FALSE", false_now))]
        if in_true:
            out[f"DROP_{spelling}"] = [(MGR, TRUE_LINE, _line("_PRODUCER_BOOL_TRUE", [m for m in TRUE_SET if m != spelling]))]
        else:
            out[f"DROP_{spelling}"] = [(MGR, FALSE_LINE, _line("_PRODUCER_BOOL_FALSE", [m for m in FALSE_SET if m != spelling]))]
    out["S1_strips_whitespace_again"] = [(MGR, FOLD, "            folded = value.strip().lower()\n")]
    out["S2_case_sensitive"] = [(MGR, FOLD, "            folded = value\n")]
    out["S3_unlisted_string_by_truthiness"] = [(MGR, STR_NONE, STR_NONE.replace("            return None\n", "            return bool(value)\n"))]
    out["S4_numbers_by_truthiness"] = [(MGR, NUMBERS, "        if isinstance(value, (int, float)):\n")]
    out["S5_numbers_ignored"] = [(MGR, NUMBERS, "        if False:\n")]
    out["S6_floats_ignored"] = [(MGR, NUMBERS, "        if isinstance(value, int) and value in (0, 1):\n")]
    out["S7_anything_else_by_truthiness"] = [(MGR, TAIL, "            return bool(value)\n        return bool(value)\n")]
    return out


def main(argv: List[str]) -> int:
    spec = importlib.util.spec_from_file_location("cascor688_round3", ROUND3)
    if spec is None or spec.loader is None:
        print(f"cannot load round 3's harness from {ROUND3}")
        return 2
    round3 = importlib.util.module_from_spec(spec)
    sys.modules["cascor688_round3"] = round3
    spec.loader.exec_module(round3)
    added = new_mutants()
    clash = sorted(set(added) & set(round3.MUTANTS))
    if clash:
        print(f"mutant names collide with round 3's: {clash}")
        return 2
    round3.MUTANTS.update(added)
    if "--base-label" not in argv:
        argv = [*argv, "--base-label", "BASE_690_first_head_c4e002d"]
    return round3.main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
