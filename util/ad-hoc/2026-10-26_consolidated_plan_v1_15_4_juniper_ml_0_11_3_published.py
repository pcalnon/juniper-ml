#!/usr/bin/env python3
"""Consolidated development plan v1.15.3 -> v1.15.4: juniper-ml 0.11.3 is published, with ml#2062's fix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2333 (ml#2062's fix), #2349 / #2350 (the 0.11.3 cut and archive), publish run 40306687867;
         util/ad-hoc/2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py (the revision this follows, and the pattern);
         util/ad-hoc/2026-10-26_plan_v1_7_22_juniper_ml_0_11_3_published.py (the recurrence plan's matching revision)

Why
---
v1.15.3 left §5's 0.11.3 note at the owner's `pypi` gate and pointed XC-P12's item 6 at that gate. §4's and §5's R-ML-a
entries still called ml#2062's fix open, and §6 still asked P4 D-1, which the owner ruled on 2026-10-25 (option (a+),
as juniper-ml's ``CHANGELOG.md`` ``[0.11.3]`` records). The owner approved the gate on 2026-10-26 and PyPI serves 0.11.3
from 17:48Z; the publish was probed here against PyPI's and TestPyPI's version JSON and the run's jobs and approvals.
Every line stays within 512 characters, the condition on which the owner approved v1.15.2 (2026-10-26), and the script
refuses if any line is over.

Usage
-----
    python3 util/ad-hoc/2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py [--root DIR] [--check]

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
_DATE_OLD = "juniper-ml 0.11.2's publish probed 2026-10-26, and `[servers]`'s patch path corrected the same day)\n"
_DATE_NEW = "juniper-ml 0.11.2's publish probed 2026-10-26, `[servers]`'s patch path corrected the same day, and 0.11.3's publish probed later that day)\n"

_STATUS_ANCHOR = "It also points at juniper-ml 0.11.3, at the owner's gate (§5; XC-P12). Like v1.15.0, no round checks it.\n"
_STATUS_ADD = "  - v1.15.4 (2026-10-26) records juniper-ml 0.11.3's publish, which ships ml#2062's fix, ml#2333, and the owner's ruling on P4 D-1 (§4; §5; §6; XC-P12). Like v1.15.0, no round checks it.\n"

_FURTHER_P12_OLD = (
    "`…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.21): juniper-ml 0.11.3's `pypi` gate (the owner's), the recurrence-client 0.3.1 cut and the owner's open items (§6 A1, A9). "
    "The juniper-ml 0.11.2 cut is done (R-ML-SERVERS; v1.15.2), and the W1.11"
)
_FURTHER_P12_NEW = (
    "`…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.22): an erratum to 0.11.2's notes (the owner's call; §5), the recurrence-client 0.3.1 cut and the owner's open items (§6 A1, A9). "
    "The juniper-ml 0.11.2 cut is done (R-ML-SERVERS; v1.15.2), 0.11.3 is published (§5; v1.15.4), and the W1.11"
)

_RMLA_OLD = "ml#2062's `[servers]` fix (P4 D-1; open, and not in 0.11.0);"
_RMLA_NEW = "ml#2062's `[servers]` fix (P4 D-1; not in 0.11.0, and shipped in 0.11.3 as ml#2333, note below);"

#: §4 Wave 1's R-ML-a item points at §5, which now says the fix shipped.
_WAVE1_OLD = "ml#2062's fix did not ride it, and its issue is open (§5).\n"
_WAVE1_NEW = "ml#2062's fix did not ride it; it shipped in 0.11.3 as ml#2333 (§5).\n"

#: §6's mid-wave sitting still asked P4 D-1; juniper-ml's CHANGELOG.md [0.11.3] records the owner's ruling.
_SITTING_OLD = "- P4 D-1 (ml#2062, which shapes R-ML-a).\n"
_SITTING_NEW = "- P4 D-1 (ml#2062, which shapes R-ML-a). **Ruled 2026-10-25: option (a+)** (juniper-ml's `CHANGELOG.md` `[0.11.3]`; v1.15.4). Its fix, ml#2333, shipped in 0.11.3 (§5).\n"

_NOTES_OLD = "  - 0.11.3 is cut: Release v0.11.3 at 10:20:47Z (tag at `a771a5b8`; archive ml#2350), and its publish run 40306687867 waits at the owner's `pypi` gate (2026-10-26; v1.15.3). Its records are session \"draft PRs\"'s.\n"
_NOTES_NEW = (
    "  - 0.11.3 is published. Release v0.11.3 was cut at 10:20:47Z (tag at `a771a5b8`; archive ml#2350; v1.15.3), and the owner approved the `pypi` gate of publish run 40306687867: "
    "PyPI serves its wheel from 17:48:05Z, with the sha256 TestPyPI took (2026-10-26; v1.15.4). Its records are session \"draft PRs\"'s.\n"
    "  - 0.11.3's `[servers]` requests `juniper-canopy[juniper-cascor,juniper-data]>=0.9.0`, `juniper-cascor[api,juniper-data]>=0.12.0` and `juniper-data[api]>=0.17.1` (PyPI's metadata). "
    "So it installs both clients (ml#2062), and data 0.17.1's `[api]` floors on the shared patches apply to it too.\n"
)

_VALIDATION_ANCHOR = "run 40306687867 and `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py`.\n"
_VALIDATION_ADD = (
    "  - v1.15.4 is a record of juniper-ml 0.11.3's publish (2026-10-26) and of the owner's P4 D-1 ruling (2026-10-25). No round checks it (owner ruling 2026-10-24); "
    "its facts cite PyPI's and TestPyPI's 0.11.3 metadata, run 40306687867's jobs and approvals, juniper-ml's `CHANGELOG.md` `[0.11.3]`, and `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py`.\n"
)

_SCRIPTS_OLD = "; and with v1.15.3's, `2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py`;\n"
_SCRIPTS_NEW = (
    "; with v1.15.3's, `2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py`; "
    "and with v1.15.4's, `2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py`;\n"
)

_MEMORY_ANCHOR = "  - by session `53dbcc4b` (2026-10-26), with v1.15.3: `project_recurrence_equities_p0_arc_2026-10-04.md` and its line in `MEMORY.md`.\n"
_MEMORY_ADD = "  - by session `53dbcc4b` (2026-10-26), with v1.15.4: `project_recurrence_equities_p0_arc_2026-10-04.md` and its line in `MEMORY.md`.\n"

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.3\n", "- **Version**: 1.15.4\n"),
    (_STATUS_ANCHOR, _STATUS_ANCHOR + _STATUS_ADD),
    (_FURTHER_P12_OLD, _FURTHER_P12_NEW),
    (_RMLA_OLD, _RMLA_NEW),
    (_WAVE1_OLD, _WAVE1_NEW),
    (_SITTING_OLD, _SITTING_NEW),
    (_NOTES_OLD, _NOTES_NEW),
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
