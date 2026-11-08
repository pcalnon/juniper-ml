#!/usr/bin/env python3
"""Consolidated development plan v1.15.13 -> v1.15.14: juniper-ml 0.11.4 is published, with the `[recurrence]` floor.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: publish run 42230617125 (juniper-ml 0.11.4); ml#2482 / ml#2497 (its proposal and archive); ml#2510 (the
         docs/QUICK_START.md refresh, which landed util/ad-hoc/2026-11-07_verify_juniper_ml_0_11_4_published.py);
         util/ad-hoc/2026-11-07_parent_agents_md_juniper_ml_0_11_4.py (the parent AGENTS.md edit this records);
         util/ad-hoc/2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py (the pattern)

Why
---
v1.15.13 left juniper-ml 0.11.4 at the owner's `pypi` gate: the 2026-11-06 block and §5's R-ML-RECURRENCE-FLOOR row
say publish run 42230617125 waits. The owner approved the gate on 2026-11-07, and PyPI serves 0.11.4 from 22:59:23Z,
probed here against PyPI's and TestPyPI's version JSON and files, the run's jobs and approvals, and dry-run resolves.
The owner then approved two edits in session a02ac3a2 (asked 23:08:12Z, answered 23:56:36Z; its transcript's
lines 547 and 558): the parent ``Juniper/AGENTS.md`` RELEASED paragraph, and ``docs/QUICK_START.md``'s sample (ml#2510).

Three statements had gone stale before this revision, and it brings them up to date from the plan's own records:
§2's P4 row stopped at recurrence 0.8.0 and juniper-ml 0.11.3; §2's P12 row left W0.1 to the owner, and XC-P12's
action 5 said W0.1 had not run, though the 2026-11-06 block records its run of 2026-11-04 (v1.15.12).

Usage
-----
    python3 util/ad-hoc/2026-11-07_consolidated_plan_v1_15_14_juniper_ml_0_11_4_published.py [--root DIR] [--check]

An edit already present is skipped, so a re-run is a no-op. An anchor found zero times or more than once refuses the
whole run before anything is written, and so does any rise in the number of lines over 512 characters (19 before
this revision; lines already over may change, but no new one may join them). ``--check`` writes nothing and exits 1
while an edit is pending.
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
_DATE_OLD = "the `[recurrence]` floor, juniper-recurrence#230 and juniper-ml 0.11.4's cut probed later that day)\n"
_DATE_NEW = "the `[recurrence]` floor, juniper-recurrence#230 and juniper-ml 0.11.4's cut probed later that day; 0.11.4's publish, and the parent `AGENTS.md` paragraph it moves, probed 2026-11-07)\n"

_STATUS_ANCHOR = "  - Planning only: this plan changes no code,"
_STATUS_NEW = (
    "  - v1.15.14 (2026-11-07) records juniper-ml 0.11.4's publish, with `[recurrence]` floored at `juniper-recurrence>=0.8.1`: the owner approved its `pypi` gate, and PyPI serves the build TestPyPI took (R-ML-RECURRENCE-FLOOR shipped). "
    "It also records two edits the owner approved that day, the parent `Juniper/AGENTS.md` and `docs/QUICK_START.md`'s sample (ml#2510), and brings §2's P4 and P12 rows and XC-P12's action 5 up to date (§2; XC-P12; §5). Like v1.15.0, no round checks it.\n"
    "  - Planning only: this plan changes no code,"
)

#: §2's P4 row: the same width, so the row stays within 512 characters.
_P4_OLD = "P12 added canopy 0.9.0, recurrence 0.6.0–0.8.0, model 0.5.0–0.6.0, juniper-ml 0.11.0–0.11.3 (10-21 to 10-26) and recurrence-client 0.3.1 (10-27)."
_P4_NEW = "P12 added canopy 0.9.0, recurrence 0.6.0–0.8.1, model 0.5.0–0.6.0, juniper-ml 0.11.0–0.11.4 (10-21 to 11-07) and recurrence-client 0.3.1 (10-27)."

_P12_OLD = "juniper-ml 0.11.0–0.11.3 carry the floors; client 0.3.1 served (10-27). W0.1's service-core half: owner (XC-P12)."
_P12_NEW = "juniper-ml 0.11.0–0.11.4 carry the floors; client 0.3.1 served (10-27). W0.1 ran 11-04 (XC-P12)."

_GATE_OLD = "its archive is ml#2497, and publish run 42230617125 waits at the owner's `pypi` gate (§5, R-ML-RECURRENCE-FLOOR).\n"
_GATE_NEW = (
    "its archive is ml#2497, and publish run 42230617125 waited at the owner's `pypi` gate (§5, R-ML-RECURRENCE-FLOOR).\n"
    "  - **Published 2026-11-07** (v1.15.14): the owner approved the gate, and PyPI serves 0.11.4 from 22:59:23Z, with the sha256 TestPyPI took. ml#2497 merged on 2026-11-06 as `d5152008` (§5).\n"
)

_BLOCK_ANCHOR = "v1.15.11 and v1.15.12 recorded the ruling as covering every primary.\n\n**Actions:**\n"
_BLOCK_NEW = (
    "v1.15.11 and v1.15.12 recorded the ruling as covering every primary.\n\n"
    "**What followed 0.11.4's publish** (v1.15.14; session `a02ac3a2`, on the owner's answers of 2026-11-07 23:56:36Z to its question of 23:08:12Z):\n\n"
    "- **The parent `Juniper/AGENTS.md`** (unversioned) now names juniper-ml 0.11.4 as the latest on PyPI, with its `[recurrence]` floor, and juniper-recurrence 0.8.1's model-core floor. "
    "Its re-probe date moved to 2026-11-07 only after `util/ad-hoc/2026-11-07_parent_agents_released_paragraph_reprobe.py` re-read all eleven packages the paragraph names: exactly those two had moved.\n"
    "  - `util/ad-hoc/2026-11-07_parent_agents_md_juniper_ml_0_11_4.py` made the edit and refuses any input but the approved one (sha256 `29e375ff…`, unchanged since 2026-11-01). "
    "The result is `48e2568a…`; both versions are in `juniper-ml/tmp/2026-11-07-parent-agents-md-backup/`.\n"
    "- **`docs/QUICK_START.md`'s sample `pip list`** shows what `juniper-ml[all]==0.11.4` resolves on 2026-11-07 (ml#2510): `juniper-cascor` 0.13.x and `juniper-ml` 0.11.4; the other 16 lines are unchanged. "
    "It showed 0.10.0's resolution of 2026-10-20, whose cascor 0.11.x is below `[servers]`' floor since 0.11.2.\n"
    "\n**Actions:**\n"
)

#: XC-P12 action 5 still read "It had not run as of 2026-11-04"; the 2026-11-06 block records the run of that day.
_W01_ANCHOR = "Re-run on 2026-11-04, it gives the same.\n"
_W01_NEW = (
    "Re-run on 2026-11-04, it gives the same.\n"
    "   - **Ran 2026-11-04** (~14:40Z, at the owner's word; v1.15.12): it exposed the model-core floor bug that juniper-recurrence 0.8.1 fixes (the 2026-11-06 block above). v1.15.11's \"had not run\" was written earlier that day.\n"
)

_ACTION6_OLD = "0.11.3 and recurrence-client 0.3.1 are published (§5; v1.15.4, v1.15.5),"
_ACTION6_NEW = "0.11.3, recurrence-client 0.3.1 and 0.11.4 are published (§5; v1.15.4, v1.15.5, v1.15.14),"

_ROW_OLD = "| **R-ML-RECURRENCE-FLOOR** (cut as juniper-ml 0.11.4, 2026-11-06, on the owner's ruling of that day; at the owner's `pypi` gate, run 42230617125) |"
_ROW_NEW = "| **R-ML-RECURRENCE-FLOOR** (shipped as juniper-ml 0.11.4, 2026-11-07, cut on the owner's ruling of 2026-11-06; note below) |"
_ROW_GATE_OLD = "| juniper-recurrence 0.8.1 on PyPI (2026-11-06) |"
_ROW_GATE_NEW = "| juniper-recurrence 0.8.1 on PyPI (met 2026-11-06); proposal ml#2482, archive ml#2497; the owner approved the gate (run 42230617125) |"

_NOTES_ANCHOR = "`util/ad-hoc/2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py` passes on the wheel from PyPI, and its 0.3.0 control fails.\n"
_NOTES_NEW = (
    "`util/ad-hoc/2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py` passes on the wheel from PyPI, and its 0.3.0 control fails.\n"
    "- juniper-ml 0.11.4 is published (R-ML-RECURRENCE-FLOOR). Release v0.11.4 was cut at 2026-11-06 14:03:58Z (tag at `957f0e94`; proposal ml#2482, archive ml#2497), and the owner approved the `pypi` gate of publish run 42230617125: "
    "PyPI serves its wheel from 2026-11-07 22:59:23Z, with the sha256 TestPyPI took (v1.15.14).\n"
    "  - Its `requires_dist` carries `juniper-recurrence<0.9.0,>=0.8.1; extra == \"recurrence\"`, and the wheel's own `METADATA` lists the same 17 requirements. "
    "`util/ad-hoc/2026-11-07_verify_juniper_ml_0_11_4_published.py` (ml#2510) passes on the files PyPI serves, and its 0.11.3 control fails on the floor.\n"
    "  - The published `[recurrence]` and `[all]` resolve against real PyPI on Python 3.12, 3.13 and 3.14 in 33 and 96 packages, juniper-ml included: the pre-flight's 32 and 95 plus juniper-ml itself, "
    "with recurrence 0.8.1 and model-core 0.3.2 (2026-11-07).\n"
)

_VALIDATION_ANCHOR = "and session `0b8fa86a`'s transcript lines 2029 and 2033.\n"
_VALIDATION_NEW = (
    "and session `0b8fa86a`'s transcript lines 2029 and 2033.\n"
    "  - v1.15.14 is a record of juniper-ml 0.11.4's publish and the two edits the owner approved on 2026-11-07. No round checks it (owner ruling 2026-10-24); "
    "its facts cite PyPI's and TestPyPI's 0.11.4 metadata and files, run 42230617125's jobs and approvals, Release `v0.11.4`, ml#2497's merge, the dry-run resolutions, "
    "PyPI's newest release of each package the parent paragraph names, and session `a02ac3a2`'s transcript (lines 547 and 558).\n"
)

_SCRIPTS_OLD = (
    "    - and with v1.15.13's, `2026-11-06_consolidated_plan_v1_15_13_floor_0_11_4_o13_narrowed.py`; the floor's `2026-11-06_raise_recurrence_floor_0_8_1.py` "
    "and the cut's `2026-11-06_juniper_ml_0_11_4_cut_cochanges.py` landed with ml#2473 and ml#2482;\n"
)
_SCRIPTS_NEW = (
    "    - with v1.15.13's, `2026-11-06_consolidated_plan_v1_15_13_floor_0_11_4_o13_narrowed.py`; the floor's `2026-11-06_raise_recurrence_floor_0_8_1.py` "
    "and the cut's `2026-11-06_juniper_ml_0_11_4_cut_cochanges.py` landed with ml#2473 and ml#2482;\n"
    "    - and with v1.15.14's, `2026-11-07_consolidated_plan_v1_15_14_juniper_ml_0_11_4_published.py`, `2026-11-07_parent_agents_released_paragraph_reprobe.py` "
    "and `2026-11-07_parent_agents_md_juniper_ml_0_11_4.py`; the publish check `2026-11-07_verify_juniper_ml_0_11_4_published.py` landed with ml#2510;\n"
)

_MEMORY_ANCHOR = "  - by session `61859b4a` (2026-11-06), recorded with v1.15.13: `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description); this session did not change `MEMORY.md`.\n"
_MEMORY_NEW = (
    "  - by session `61859b4a` (2026-11-06), recorded with v1.15.13: `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description); this session did not change `MEMORY.md`.\n"
    "  - by session `a02ac3a2` (2026-11-07), recorded with v1.15.14: the parent `Juniper/AGENTS.md` (juniper-ml 0.11.4, recurrence 0.8.1, the re-probe date and Last Updated; "
    "both versions in `juniper-ml/tmp/2026-11-07-parent-agents-md-backup/`) and `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description); this session did not change `MEMORY.md`.\n"
)

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.13\n", "- **Version**: 1.15.14\n"),
    (_STATUS_ANCHOR, _STATUS_NEW),
    (_P4_OLD, _P4_NEW),
    (_P12_OLD, _P12_NEW),
    (_GATE_OLD, _GATE_NEW),
    (_BLOCK_ANCHOR, _BLOCK_NEW),
    (_W01_ANCHOR, _W01_NEW),
    (_ACTION6_OLD, _ACTION6_NEW),
    (_ROW_OLD, _ROW_NEW),
    (_ROW_GATE_OLD, _ROW_GATE_NEW),
    (_NOTES_ANCHOR, _NOTES_NEW),
    (_VALIDATION_ANCHOR, _VALIDATION_NEW),
    (_SCRIPTS_OLD, _SCRIPTS_NEW),
    (_MEMORY_ANCHOR, _MEMORY_NEW),
]


def long_lines(text: str) -> list[tuple[int, int]]:
    return [(n, len(line)) for n, line in enumerate(text.split("\n"), 1) if len(line) > MAX_LINE]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=_REPO)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    path = args.root / PLAN
    original = path.read_text(encoding="utf-8")
    text = original
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

    before, after = long_lines(original), long_lines(text)
    grown = len(after) > len(before)
    if grown:
        print(f"  ! lines over {MAX_LINE} characters: {len(before)} before, {len(after)} after: {after}")
    if refused or grown:
        print(f"REFUSED: {refused} anchor(s); {len(after) - len(before)} new long line(s); nothing written", file=sys.stderr)
        return 1
    print(f"  lines over {MAX_LINE} characters: {len(before)} before, {len(after)} after")
    if args.check:
        return 1 if pending else 0
    if pending:
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
