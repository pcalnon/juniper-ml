#!/usr/bin/env python3
"""Consolidated development plan v1.15.4 -> v1.15.5: recurrence-client 0.3.1 published, P12's follow-ups, APD-ML-002's cascor train / val half.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-27
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-recurrence#227 / juniper-ml#2367 (the client cut and archive), publish run 40417898021;
         juniper-ml#2369 (APD-ML-002's cascor train / val half) and juniper-cascor#731 (its test_accuracy producer); juniper-ml#2362 / #2363 (the 0.11.2 erratum);
         util/ad-hoc/2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py (the revision this follows, and the pattern);
         util/ad-hoc/2026-10-27_plan_v1_7_23_client_0_3_1_published_followups_closed.py (the recurrence plan's matching revision);
         util/ad-hoc/2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py (the wheel probe §5 cites)

Why
---
v1.15.4 left four things open that moved on 2026-10-26/27:

- P12: the recurrence-client 0.3.1 cut (§2's P12 row; XC-P12 action 6) is published, the owner having approved its gate;
  §2's P4 row also still stopped at juniper-ml 0.11.2. The index-row residue (§4 Wave 2; Appendix A) was annotated by
  the owner's ruling of 2026-10-26.
- §5: the 0.11.2 erratum, "the owner's call", was made by session "draft PRs" under the owner's ruling.
- P6: APD-ML-002's cascor train / val half (XC-P12 action 4; P6-08) merged as juniper-ml#2369, beside juniper-cascor#731 (the
  ``test_accuracy`` producer), under the
  owner's four rulings of 2026-10-26 recorded in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` §4.9.
  It went in ahead of P5-11 (ml#2064), which §4 Wave 1 and §9 ordered first, and its ruling (1) answers what P6 OD-3
  asked. `test_accuracy` still waits on a cascor release and ml#2064, so the register row stays open.

Each fact was re-probed here: the merges with ``gh pr view``, the publish against PyPI's and TestPyPI's version JSON and
the run's jobs and approvals, the wheel with the probe named above, the Release bodies' ``updated_at``, and the index
rows by reading ``~/.local/state/juniper-experiments/index.jsonl``. Every line stays within 512 characters, the condition
on which the owner approved v1.15.2 (2026-10-26), and the script refuses if any line is over.

Usage
-----
    python3 util/ad-hoc/2026-10-27_consolidated_plan_v1_15_5_client_0_3_1_published.py [--root DIR] [--check]

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
_DATE_OLD = "`[servers]`'s patch path corrected the same day, and 0.11.3's publish probed later that day)\n"
_DATE_NEW = "`[servers]`'s patch path corrected the same day, 0.11.3's publish probed later that day, and juniper-recurrence-client 0.3.1's publish probed 2026-10-27)\n"

_STATUS_ANCHOR = "  - v1.15.4 (2026-10-26) records juniper-ml 0.11.3's publish, which ships ml#2062's fix, ml#2333, and the owner's ruling on P4 D-1 (§4; §5; §6; XC-P12). Like v1.15.0, no round checks it.\n"
_STATUS_ADD = (
    "  - v1.15.5 (2026-10-27) records juniper-recurrence-client 0.3.1's publish and P12's follow-ups of 2026-10-26/27, the owner's rulings of 2026-10-26 on the archive cap and the false `succeeded` index row, "
    "the 0.11.2 erratum, and APD-ML-002's cascor train / val half, merged under the owner's four rulings of 2026-10-26 (§2; XC-P12; §4; §5; §6; §8; §9; Appendices A and B). Like v1.15.0, no round checks it.\n"
)

#: §2's P4 row stopped at 0.11.2 (v1.15.4 did not touch it).
_P4_OLD = "The P12 chain added canopy 0.9.0, recurrence 0.6.0–0.8.0, model 0.5.0 and 0.6.0, and juniper-ml 0.11.0, 0.11.1 and 0.11.2 (10-26)."
_P4_NEW = "P12 added canopy 0.9.0, recurrence 0.6.0–0.8.0, model 0.5.0–0.6.0, juniper-ml 0.11.0–0.11.3 (10-21 to 10-26) and recurrence-client 0.3.1 (10-27)."

_P6_OLD = "PF-3 needs a quiet window. The cascor half of APD-ML-002..006 waits on one owner menu. |"
_P6_NEW = "PF-3 needs a quiet window. APD-ML-002's cascor train / val half merged under the owner's rulings of 10-26 (ml#2369, 10-27; XC-P12); 003..006 wait on one owner menu. |"

_P12_OLD = "and W5.7 (data#486) waits for a data release. juniper-ml 0.11.0 to 0.11.2 (10-26) carry the floors. W0.1's service-core half: owner (XC-P12). | client 0.3.1 (owner); §6 A1, A9's rest |"
_P12_NEW = "and W5.7 (data#486) waits for R-DATA-2. juniper-ml 0.11.0–0.11.3 carry the floors; client 0.3.1 served (10-27). W0.1's service-core half: owner (XC-P12). | R-DATA-2 (owner); §6 A1, A9's rest |"

_ACT4_ANCHOR = "4. **APD-ML-002's cascor half** (P6-08) remains, with a trap: a one-level unwrap harvests 2 of 6 names and looks fixed. Ship it after P6 OD-3, with the first registry-`metrics` tests.\n"
_ACT4_ADD = (
    "   - **Its train / val half landed 2026-10-27 as ml#2369 (`8467225b`), ahead of P5-11 (ml#2064)**, under the owner's four rulings of 2026-10-26, recorded in `…DEFECT-REGISTER.md` §4.9. Ruling (1) answers what P6 OD-3 asked (v1.15.5). "
    "cascor#731 (`752a797f`, 00:11Z), the `test_accuracy` producer, merged the same day.\n"
    "   - ml#2369 reads `train_accuracy` and `val_accuracy` from `cascor.final` (`val_accuracy` keeps its name and is selected-on), refuses `final_accuracy`, adds `run_suite.py --reaggregate`, which re-renders a suite's reports from disk and launches nothing, "
    "and fails every acceptance band on a NaN or infinite value. It ships the column tests the register's sequencing constraint asks for.\n"
    "   - `test_accuracy` stays an accepted band metric with no producer: cascor#731 computes the final evaluation's accuracy and is in no cascor release (the owner's call), and ml#2064's labelled block must carry it into `stats.json`. The register row stays open until then.\n"
)

_ACT6_OLD = (
    "(v1.7.22): an erratum to 0.11.2's notes (the owner's call; §5), the recurrence-client 0.3.1 cut and the owner's open items (§6 A1, A9). "
    "The juniper-ml 0.11.2 cut is done (R-ML-SERVERS; v1.15.2), 0.11.3 is published (§5; v1.15.4), and the W1.11"
)
_ACT6_NEW = (
    "(v1.7.23): R-DATA-2 with W5.7 (§5) and the owner's open items (§6 A1, A9). "
    "The juniper-ml 0.11.2 cut is done (R-ML-SERVERS; v1.15.2), 0.11.3 and recurrence-client 0.3.1 are published (§5; v1.15.4, v1.15.5), and the W1.11"
)

_P511_OLD = "**P5-11 (ml#2064)**: first among the `util/experiments/` items, because P6 OD-3 depends on what it surfaces. Serialize by file (§8).\n"
_P511_NEW = (
    "**P5-11 (ml#2064)**: first among the `util/experiments/` items, because P6 OD-3 depends on what it surfaces. Serialize by file (§8). "
    "**Bypassed 2026-10-27**: APD-ML-002's cascor train / val half (P6-08) merged first, under the owner's rulings of 2026-10-26, which answer OD-3 for it (XC-P12 action 4). ml#2064's labelled block must now also carry `test_accuracy` into `stats.json`.\n"
)

_W2_OLD = "Annotate the false `succeeded` row (`20261003T091414Z-4ba6`) in `~/.local/state/juniper-experiments/index.jsonl` (residue) |"
_W2_NEW = "The false `succeeded` row (`20261003T091414Z-4ba6`) is annotated: `index.jsonl` line 482 (owner, 10-26) |"

_W4_OLD = "- **P6's APD-ML fixes**: P6-07, P6-09, P6-10, and the cascor half of P6-08, after the menu.\n"
_W4_NEW = "- **P6's APD-ML fixes**: P6-07, P6-09 and P6-10, after the menu. P6-08's cascor train / val half merged as ml#2369 (2026-10-27; XC-P12 action 4); its `test_accuracy` waits on a cascor release with cascor#731, and on ml#2064.\n"

_CLIENT_ANCHOR = (
    "  - 0.11.3's `[servers]` requests `juniper-canopy[juniper-cascor,juniper-data]>=0.9.0`, `juniper-cascor[api,juniper-data]>=0.12.0` and `juniper-data[api]>=0.17.1` (PyPI's metadata). "
    "So it installs both clients (ml#2062), and data 0.17.1's `[api]` floors on the shared patches apply to it too.\n"
)
_CLIENT_ADD = (
    "- juniper-recurrence-client 0.3.1 is published: Release `juniper-recurrence-client-v0.3.1` at 2026-10-26 23:10:24Z (tag at `717f2a80`; proposal recurrence#227, archive ml#2367), and the owner approved the `pypi` gate of publish run 40417898021. "
    "PyPI serves its wheel from 2026-10-27 10:20:18Z, with the sha256 TestPyPI took (v1.15.5).\n"
    "  - Its `crossval` no longer sends `embargo: 0`, so recurrence 0.8.0's look-back default (W5.2) applies. `util/ad-hoc/2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py` passes on the wheel from PyPI, and its 0.3.0 control fails.\n"
)

_ERRATUM_OLD = "says they \"arrive through cascor 0.12.0\". An erratum to it, the notes and the Release v0.11.2 body is the owner's call.\n"
_ERRATUM_NEW = (
    "says they \"arrive through cascor 0.12.0\". An erratum to it, the notes and the Release v0.11.2 body is the owner's call. "
    "**Made on 2026-10-26** by session \"draft PRs\" under the owner's ruling: ml#2362 (`682e72fb`; the v0.11.2 notes, with a v0.11.3 clarification), ml#2363 (`40815bb4`; `CHANGELOG.md`) and both Release bodies, v0.11.2 and v0.11.3 (v1.15.5).\n"
)

_A1_OLD = "- **A1, still open**: P6 OD-2, canopy#685 call (a),"
_A1_NEW = "- **A1, still open**: P6 OD-2 (the owner ruled APD-ML-002 itself on 2026-10-26, and its cascor train / val half merged, XC-P12 action 4; the order of 003..006 is open), canopy#685 call (a),"

_OD3_OLD = "  - OD-3 (the metric and split, after P5-11);\n"
_OD3_NEW = "  - OD-3 (the metric and split, after P5-11). **Answered 2026-10-26** by the owner's APD-ML-002 ruling (1), \"A now, test later\": `train_accuracy` / `val_accuracy` from `cascor.final`, `test_*` from ml#2064. P6-08 was its only item (XC-P12 action 4);\n"

_COLL_OLD = "ml#2195 (merged 2026-10-09; its suites pin this file), P6-07, P6-08, P12-52 |"
_COLL_NEW = "ml#2195 (merged 2026-10-09; its suites pin this file), ml#2369 (merged 2026-10-27; P6-08's train / val half), P6-07, P6-08, P12-52 |"

_DEP_OLD = "| P5-11 | — | First: P6 OD-3 depends on what it surfaces |\n"
_DEP_NEW = "| P5-11 | — | First: P6 OD-3 depends on what it surfaces. Bypassed 2026-10-27: P6-08's train / val half merged first, under the owner's rulings (XC-P12 action 4) |\n"

_T5_OLD = "  - **T5**: P6-07, P6-08 (the cascor half; the recurrence half shipped in ml#2145), P6-09, P6-10, P6-32\n"
_T5_NEW = "  - **T5**: P6-07, P6-08 (the cascor `test_accuracy` remainder; the recurrence half shipped in ml#2145, and the cascor train / val half in ml#2369), P6-09, P6-10, P6-32\n"

_T2_OLD = "Residue: annotate the false `succeeded` row (`20261003T091414Z-4ba6`) in the shared run index, `~/.local/state/juniper-experiments/index.jsonl`.\n"
_T2_NEW = "Residue: annotate the false `succeeded` row (`20261003T091414Z-4ba6`) in the shared run index, `~/.local/state/juniper-experiments/index.jsonl`. Done 2026-10-26 by the owner's ruling: a correction row (line 482).\n"

_MENU_OLD = "| 11 | The APD-ML menu | P6-06, P3-36, P12-04 (= APD-ML-002 = P6-08; its recurrence half is merged) |\n"
_MENU_NEW = "| 11 | The APD-ML menu | P6-06, P3-36, P12-04 (= APD-ML-002 = P6-08; its recurrence half is merged, and its cascor train / val half, ml#2369) |\n"

_VALIDATION_ANCHOR = "and `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py`.\n"
_VALIDATION_ADD = (
    "  - v1.15.5 is a record of juniper-recurrence-client 0.3.1's publish (2026-10-27), P12's follow-ups and the owner's rulings of 2026-10-26, the 0.11.2 erratum and APD-ML-002's cascor train / val half. No round checks it (owner ruling 2026-10-24); "
    "its facts cite the PRs it names, PyPI's and TestPyPI's 0.3.1 metadata, run 40417898021's jobs and approvals, `…DEFECT-REGISTER.md` §4.9, and `util/ad-hoc/2026-10-27_consolidated_plan_v1_15_5_client_0_3_1_published.py`.\n"
)

_SCRIPTS_OLD = "; and with v1.15.4's, `2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py`;\n"
_SCRIPTS_NEW = (
    "; with v1.15.4's, `2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py`;\n"
    "    - and with v1.15.5's, `2026-10-27_consolidated_plan_v1_15_5_client_0_3_1_published.py` and `2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py`;\n"
)

_MEMORY_ANCHOR = "  - by session `53dbcc4b` (2026-10-26), with v1.15.4: `project_recurrence_equities_p0_arc_2026-10-04.md` and its line in `MEMORY.md`.\n"
_MEMORY_ADD = "  - by session `77e26938` (2026-10-27), with v1.15.5: the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-recurrence-client 0.3.1), and `project_recurrence_equities_p0_arc_2026-10-04.md` and its line in `MEMORY.md`.\n"

#: MAJOR-1 of the fact-check: the status bullet says v1.15.5 records P12's follow-ups and the archive-cap ruling, so the body must.
_XC_ANCHOR = "  The owner chose ml#2330's option 1 on 2026-10-26 (v1.15.2). ml#2345 (merged as `278c6139`) sets E-C's `execution.max_wall_seconds` to 5400, so its worst-case driver budget is 5,850 s against a 7,200 s `per_run_timeout_seconds`; its cell ids and `config_sha256` are unchanged, and a CI test pins both bounds.\n"
_XC_ADD = (
    "- **P12's follow-ups of 2026-10-26/27** (v1.15.5; `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` v1.7.23). deploy#264 closes deploy#250: the recurrence snapshot smoke pulls a missing image and never builds one. "
    "canopy#776 closes canopy#735 and #736, and canopy#777 closes #737 with a daily juniper-data schema-drift check; neither is in a canopy release yet. cascor#729 corrects a staging comment.\n"
    "  The owner ruled on 2026-10-26 that the release-train archive cap is 1,000,000 B (ml#2364), after a GitHub-hosted runner accepted every GraphQL body it tried, up to 16,777,216 B (run 40410086979).\n"
)

#: XC-P12 stopped at 0.11.2, the staleness v1.15.5 fixes in §2's P4 row too.
_XC_ML_OLD = "- **juniper-ml 0.11.0, 0.11.1 and 0.11.2** carry the meta-package's floors (2026-10-21, 2026-10-25 and 2026-10-26; §5)."
_XC_ML_NEW = "- **juniper-ml 0.11.0 to 0.11.3** carry the meta-package's floors (2026-10-21, 2026-10-25, and 0.11.2 and 0.11.3 on 2026-10-26; §5)."

#: ml#2362 corrected the Priority line in place, so §5's present tense went stale.
_PRIORITY_OLD = "  - 0.11.2's notes repeat the error. The Priority line of `notes/releases/RELEASE_NOTES_v0.11.2.md` reads \"`[tools]` and `[all]` already floor both patches, since 0.11.1\", which under-warns any `[servers]` install that also has `[tools]` (`[all]` included) still on cascor 0.11.0.\n"
_PRIORITY_NEW = "  - 0.11.2's notes repeated the error. The Priority line of `notes/releases/RELEASE_NOTES_v0.11.2.md` read \"`[tools]` and `[all]` already floor both patches, since 0.11.1\", which under-warned any `[servers]` install that also has `[tools]` (`[all]` included) still on cascor 0.11.0, until ml#2362 corrected it (2026-10-26; below).\n"

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.4\n", "- **Version**: 1.15.5\n"),
    (_STATUS_ANCHOR, _STATUS_ANCHOR + _STATUS_ADD),
    (_P4_OLD, _P4_NEW),
    (_P6_OLD, _P6_NEW),
    (_P12_OLD, _P12_NEW),
    (_XC_ML_OLD, _XC_ML_NEW),
    (_XC_ANCHOR, _XC_ANCHOR + _XC_ADD),
    (_ACT4_ANCHOR, _ACT4_ANCHOR + _ACT4_ADD),
    (_ACT6_OLD, _ACT6_NEW),
    (_P511_OLD, _P511_NEW),
    (_W2_OLD, _W2_NEW),
    (_W4_OLD, _W4_NEW),
    (_CLIENT_ANCHOR, _CLIENT_ANCHOR + _CLIENT_ADD),
    (_PRIORITY_OLD, _PRIORITY_NEW),
    (_ERRATUM_OLD, _ERRATUM_NEW),
    (_A1_OLD, _A1_NEW),
    (_OD3_OLD, _OD3_NEW),
    (_COLL_OLD, _COLL_NEW),
    (_DEP_OLD, _DEP_NEW),
    (_T5_OLD, _T5_NEW),
    (_T2_OLD, _T2_NEW),
    (_MENU_OLD, _MENU_NEW),
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
