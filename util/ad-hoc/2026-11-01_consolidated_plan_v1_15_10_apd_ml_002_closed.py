#!/usr/bin/env python3
"""Consolidated development plan v1.15.9 -> v1.15.10: register row APD-ML-002 is closed, and the parent AGENTS.md pin edit.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-01
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-30_consolidated_plan_v1_15_9_deploy_pin_test_accuracy_trio_stopped.py (the revision this follows, and the pattern);
         util/ad-hoc/2026-11-01_register_close_apd_ml_002.py (the close this records)

Why
---
v1.15.9 says in five places that APD-ML-002's close is the owner's, and that the parent ``Juniper/AGENTS.md`` edit needs the
owner's approval. The owner answered both when session ``856140dc`` asked: "Close it (signed PR)" and "Edit it".
``util/ad-hoc/2026-11-01_register_close_apd_ml_002.py`` makes the register's close touches. Afterwards
``util/ad-hoc/register_open_set.py`` reads 137 rows, 102 fixed, 35 open, and ``util/ad-hoc/register_status_crosscheck.py``
reads AGREE (102 / 102 / 102). The parent file's diff against its backup is two hunks: Last Updated, and the cascor 0.13.0
bullet's "juniper-deploy still pins the `0.12.0` image", which now names juniper-deploy#266. v1.15.9's own status line
stays as the record of what v1.15.9 said. The Date line is not extended: it is 510 of 512 characters.

Usage
-----
    python3 util/ad-hoc/2026-11-01_consolidated_plan_v1_15_10_apd_ml_002_closed.py [--root DIR] [--check]

An edit already present is skipped, so a re-run is a no-op. An anchor found zero times or more than once, or a line
over 512 characters after the edits, refuses the whole run before anything is written. ``--check`` writes nothing and
exits 1 while an edit is pending.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md"
MAX_LINE = 512

# Multi-line texts are bound to names here rather than written inside the REPLACEMENTS display: adjacent literals inside
# a list or tuple trip CodeQL's py/implicit-string-concatenation-in-list, whose unresolved thread blocks a merge.
_STATUS_ANCHOR = (
    "  - v1.15.9 (2026-10-30) records the owner's answers of 2026-10-29 and 2026-10-30 and what followed: juniper-deploy pins cascor 0.13.0 (deploy#266), "
    "a run on the cascor primary's `src/` filled `test_accuracy`, so APD-ML-002's close condition is met (the close is the owner's), the trio is stopped, "
    "juniper-data#501 adds juniper-canopy to the notify matrix, and index row 483 says `failed` (Overview; §2; XC-P12; §4; §5; §8; Appendix A). Like v1.15.0, no round checks it.\n"
)
_STATUS_ADD = (
    "  - v1.15.10 (2026-11-01) records register row APD-ML-002's close on the owner's word (35 rows open), and the parent `Juniper/AGENTS.md` edit the owner approved, "
    "which names juniper-deploy#266's cascor 0.13.0 pin (§2; XC-P12; §4; §5; Appendices A and B). Like v1.15.0, no round checks it.\n"
)

_S2_OLD = "a run filled `test_accuracy` on 10-30, and the register row's close is the owner's (XC-P12);"
_S2_NEW = "a run filled `test_accuracy` on 10-30, and the register row closed 11-01 (XC-P12);"

_FILLED_ANCHOR = (
    "   - **Filled 2026-10-30** (v1.15.9): `util/ad-hoc/2026-10-30_test_accuracy_731_smoke_suite.yaml`, one spiral-smoke cell on the cascor primary's `src/` at `e8e8bf4d`, ran as `20261030T084056Z-0ac7` (index row 484). "
    "Its final evaluation is on `test` with `accuracy` 0.575, and the suite's `aggregate.csv` carries it as `test_accuracy`. "
    'So the register row\'s close condition, "until that column exists", is met by a run. The five-touch close is the owner\'s.\n'
)
_CLOSED_ADD = (
    "   - **Closed 2026-11-01** (v1.15.10), on the owner's word: register row APD-ML-002 is FIXED (ml#2145, ml#2369, cascor#731, ml#2381), with a §5.1 verification row on run `20261030T084056Z-0ac7`. "
    "`util/ad-hoc/register_open_set.py` reads 35 open, and `util/ad-hoc/register_status_crosscheck.py` AGREE.\n"
)

_P6_OLD = "juniper-deploy pins 0.13.0 from 2026-10-30, and the register row's close is the owner's (§5; XC-P12 action 4).\n"
_P6_NEW = "juniper-deploy pins 0.13.0 from 2026-10-30, and the register row closed on 2026-11-01 (§5; XC-P12 action 4).\n"

_AGENTS_OLD = "    - The unversioned parent `Juniper/AGENTS.md` still says juniper-deploy pins the 0.12.0 image; its edit needs the owner's approval.\n"
_AGENTS_NEW = "    - The unversioned parent `Juniper/AGENTS.md` said juniper-deploy pins the 0.12.0 image until 2026-11-01, when it was edited with the owner's approval (v1.15.10).\n"

_T5_OLD = "(v1.15.9), and the register row's close is the owner's;"
_T5_NEW = "(v1.15.9), and the register row closed on 2026-11-01 (v1.15.10);"

_B11_OLD = "and its `test_*` columns, ml#2381) |"
_B11_NEW = "and its `test_*` columns, ml#2381; closed 2026-11-01) |"

_VALIDATION_ANCHOR = (
    "    - One independent read-only reviewer checked the first draft: its BLOCKER was the ruling dates (three answers came on 2026-10-29), "
    "its MAJORs a `/proc` claim and the Overview's cascor 0.12.0 pin; all are applied.\n"
)
_VALIDATION_ADD = (
    "  - v1.15.10 is a record of APD-ML-002's close and the parent `AGENTS.md` edit (2026-11-01). No round checks it (owner ruling 2026-10-24); its facts cite the register's §2 line, §4 row and §5.1 row, "
    "`util/ad-hoc/register_open_set.py`, `util/ad-hoc/register_status_crosscheck.py`, the parent file's diff against its backup, and the owner's answers to session `856140dc`'s questions.\n"
)

_SCRIPTS_OLD = (
    "    - and with v1.15.9's, `2026-10-30_consolidated_plan_v1_15_9_deploy_pin_test_accuracy_trio_stopped.py`, which cites `2026-10-30_index_correction_row_failed.py` "
    "and `2026-10-30_test_accuracy_731_smoke_suite.yaml` (both landed by ml#2390);\n"
)
_SCRIPTS_NEW = (
    "    - with v1.15.9's, `2026-10-30_consolidated_plan_v1_15_9_deploy_pin_test_accuracy_trio_stopped.py`, which cites `2026-10-30_index_correction_row_failed.py` "
    "and `2026-10-30_test_accuracy_731_smoke_suite.yaml` (both landed by ml#2390);\n"
    "    - and with v1.15.10's, `2026-11-01_consolidated_plan_v1_15_10_apd_ml_002_closed.py` and `2026-11-01_register_close_apd_ml_002.py`;\n"
)

_MEMORY_ANCHOR = (
    "  - by session `856140dc` (2026-10-30), with v1.15.9: `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description); "
    "this session did not change `MEMORY.md`.\n"
)
_MEMORY_ADD = (
    "  - by session `856140dc` (2026-11-01), with v1.15.10: the parent `Juniper/AGENTS.md` (the cascor 0.13.0 bullet's deploy pin, and Last Updated; both versions in "
    "`juniper-ml/tmp/2026-11-01-parent-agents-md-backup/`) and `project_recurrence_equities_p0_arc_2026-10-04.md`; `MEMORY.md` is unchanged.\n"
)

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    ("- **Version**: 1.15.9\n", "- **Version**: 1.15.10\n"),
    (_STATUS_ANCHOR, _STATUS_ANCHOR + _STATUS_ADD),
    (_S2_OLD, _S2_NEW),
    (_FILLED_ANCHOR, _FILLED_ANCHOR + _CLOSED_ADD),
    (_P6_OLD, _P6_NEW),
    (_AGENTS_OLD, _AGENTS_NEW),
    (_T5_OLD, _T5_NEW),
    (_B11_OLD, _B11_NEW),
    (_VALIDATION_ANCHOR, _VALIDATION_ANCHOR + _VALIDATION_ADD),
    (_SCRIPTS_OLD, _SCRIPTS_NEW),
    (_MEMORY_ANCHOR, _MEMORY_ANCHOR + _MEMORY_ADD),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=_REPO)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    path = args.root / PLAN
    text = path.read_text(encoding="utf-8")
    pending = refused = 0
    for old, new in REPLACEMENTS:
        site = old.strip()[:72]
        if new in text and text.count(old) <= text.count(new):
            # ``new`` may contain ``old`` (an insertion after an anchor); applied means each old sits inside a new.
            print(f"  = {site}... already applied")
            continue
        if text.count(old) != 1:
            print(f"  ! {site}... REFUSED: found {text.count(old)} times, expected 1")
            refused += 1
            continue
        text = text.replace(old, new, 1)
        pending += 1
        print(f"  ~ {site}... {'pending' if args.check else 'applied now'}")

    long_lines = [(n, len(line)) for n, line in enumerate(text.split("\n"), 1) if len(line) > MAX_LINE]
    for n, width in long_lines:
        print(f"  ! line {n} is {width} characters, over {MAX_LINE}")
    if refused or long_lines:
        print(f"REFUSED: {refused} anchor(s), {len(long_lines)} long line(s); nothing written", file=sys.stderr)
        return 1
    if args.check:
        return 1 if pending else 0
    if pending:
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
