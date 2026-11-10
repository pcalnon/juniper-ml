#!/usr/bin/env python3
"""Consolidated development plan v1.15.5 -> v1.15.6: P5-11 closed (ml#2381), juniper-cascor 0.13.0 at its pypi gate.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-28
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2381 (closes juniper-ml#2064 = P5-11), juniper-cascor#731 (the test_accuracy producer), juniper-cascor#733 /
         Release v0.13.0 / juniper-ml#2379 (the cut and its archive), publish run 40608671287 (waiting at `pypi`) and image run 40608671351;
         util/ad-hoc/2026-10-27_consolidated_plan_v1_15_5_client_0_3_1_published.py (the revision this follows, and the pattern)

Why
---
v1.15.5 (2026-10-27) left APD-ML-002's ``test_accuracy`` waiting on two things, and both moved on 2026-10-28, outside the P12 arc:

- P5-11 is done. juniper-ml#2381 (``c77b7be5``, merged 03:23:15Z) closed juniper-ml#2064: a cascor run's
  ``cascor.eval_scalars`` is now its labelled final evaluation (stats schema ``juniper-experiment-stats/2``), and
  ``run_suite.py`` fills ``test_accuracy`` / ``test_f1`` / ``test_precision`` / ``test_recall`` / ``test_roc_auc`` only from a
  final block on ``test``. §2's P5 row still said ml#2064 "skews every cascor run's eval scalars"; §4, §6 OD-3, §8, §9 and
  Appendix A still ordered P5-11 first or open.
- juniper-cascor 0.13.0 carries juniper-cascor#731 (``752a797f`` is an ancestor of ``v0.13.0``). The Release was cut at
  ``61a67c53`` (proposal juniper-cascor#733) at 00:25:28Z; its image is on GHCR and its wheel on TestPyPI, and its PyPI leg
  waits at the owner's ``pypi`` gate (run 40608671287, created 00:25:29Z). The working deadline is 2026-11-27 00:25Z, because
  GitHub's Actions limits page caps an environment-approval wait at 30 days ("Gate approval time") and allows a re-run only
  within 30 days; the 35-day run limit (2026-12-02 00:25Z) is the outer bound. ``src/api/secrets.py`` is unchanged from
  ``v0.12.0``, so 0.13.0 names no cascor F-S10 fix either (XC-P12 item 2's "a cascor fix"). Its locks moved data-client
  0.5.0 -> 0.6.0, so the two places that still said they pin 0.5.0 "today" (§4 Wave 1's Images route; §9) are annotated.

Register row ``APD-ML-002`` (``notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md``) is not edited: juniper-ml#2381
left its close to the owner, and this plan only records that.

Validation: one independent read-only fact-check of the first draft against ``gh``, PyPI, TestPyPI, GHCR and GitHub's docs
found 0 BLOCKER, 0 MAJOR and no contradiction, 4 MINOR and some NITs. All four MINORs are applied: the gate's working
deadline is day 30, not day 35; two lines had dropped the test-split condition; the memory edits the plan names had to be
made before landing; and the stale data-client 0.5.0 lock pins. Three NITs are applied (§2's P6 row, §6 A1, and P6-08 no longer
a pending editor of ``run_suite.py`` in §8). §2's P4 row has no room under 512 characters for 0.13.0, and §5 carries it.

Each fact was re-probed here: the merges with ``gh pr view`` (juniper-ml#2381, #2379; juniper-cascor#731, #733), issue
#2064's ``closedAt``, ``gh release view v0.13.0``, run 40608671287's jobs (TestPyPI success, PyPI waiting) and run
40608671351 (Publish Container Image, success), PyPI's 404 and TestPyPI's 200 for ``/juniper-cascor/0.13.0/json``, GHCR's
``tags/list`` (``0.13.0`` and ``0.13``), and ``gh api .../compare/v0.12.0...v0.13.0`` (16 commits, 39 files, no
``src/api/secrets.py``). Every line stays within 512 characters, the condition on which the owner approved v1.15.2
(2026-10-26), and the script refuses if any line is over.

Usage
-----
    python3 util/ad-hoc/2026-10-28_consolidated_plan_v1_15_6_p5_11_closed_cascor_0_13_0_at_gate.py [--root DIR] [--check]

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
_DATE_OLD = "0.11.3's publish probed later that day, and juniper-recurrence-client 0.3.1's publish probed 2026-10-27)\n"
_DATE_NEW = "0.11.3's publish probed later that day, juniper-recurrence-client 0.3.1's publish probed 2026-10-27, and ml#2064's close and juniper-cascor 0.13.0's gate probed 2026-10-28)\n"

_STATUS_ANCHOR = (
    "  - v1.15.5 (2026-10-27) records juniper-recurrence-client 0.3.1's publish and P12's follow-ups of 2026-10-26/27, the owner's rulings of 2026-10-26 on the archive cap and the false `succeeded` index row, "
    "the 0.11.2 erratum, and APD-ML-002's cascor train / val half, merged under the owner's four rulings of 2026-10-26 (§2; XC-P12; §4; §5; §6; §8; §9; Appendices A and B). Like v1.15.0, no round checks it.\n"
)
_STATUS_ADD = (
    "  - v1.15.6 (2026-10-28) records P5-11's close (ml#2381 closed ml#2064) and juniper-cascor 0.13.0, which carries cascor#731, at the owner's `pypi` gate, so APD-ML-002's `test_accuracy` has its producer and its column on `main` "
    "(§2; XC-P12; §4; §5; §6; §8; §9; Appendices A and B). Like v1.15.0, no round checks it.\n"
)

_P5_OLD = "ml#2064 skews every cascor run's eval scalars. | S0.1 row c; P5-11; P5-01 | T1/T2 |"
_P5_NEW = "ml#2064 is fixed: since ml#2381 (10-28), a cascor run's eval scalars are its labelled final evaluation. | S0.1 row c; P5-01 | T1/T2 |"

#: XC-P12 item 2 (W1.14): "a cascor fix" is still open, and 0.13.0 does not carry one either.
_FS10_OLD = "Still open: the source fix in the data client and a cascor fix (cascor 0.12.0, served on 2026-10-25, names none).\n"
_FS10_NEW = "Still open: the source fix in the data client and a cascor fix (cascor 0.12.0, served on 2026-10-25, names none, nor does 0.13.0, cut on 2026-10-28: its `src/api/secrets.py` is unchanged from `v0.12.0`).\n"

_ACT4_OLD = (
    "   - `test_accuracy` stays an accepted band metric with no producer: cascor#731 computes the final evaluation's accuracy and is in no cascor release (the owner's call), "
    "and ml#2064's labelled block must carry it into `stats.json`. The register row stays open until then.\n"
)
_ACT4_NEW = (
    "   - `test_accuracy` stays an accepted band metric with no producer: cascor#731 computes the final evaluation's accuracy and is in no cascor release (the owner's call), "
    "and ml#2064's labelled block must carry it into `stats.json`. The register row stays open until then. **Moved 2026-10-28** (v1.15.6): ml#2064 is closed, and Release v0.13.0 carries cascor#731, its PyPI leg at the owner's gate.\n"
    "   - ml#2381 (`c77b7be5`, 2026-10-28) closed ml#2064. `stats.json`'s `cascor.eval_scalars` is the final evaluation, labelled with its split, n and `held_out` (schema `juniper-experiment-stats/2`), "
    "and the in-loop values are kept, labelled, as `eval_scalars_in_loop`. `run_suite.py` fills `test_accuracy`, `test_f1`, `test_precision`, `test_recall` and `test_roc_auc` only from a final block on `test`.\n"
    "   - juniper-cascor 0.13.0 carries cascor#731: its image is on GHCR, and its wheel waits at the owner's `pypi` gate (run 40608671287; §5). `test_accuracy` fills once a cascor carrying cascor#731 serves a run with a test split. "
    "ml#2381 left the register row's close to the owner.\n"
)

_P511_OLD = "ml#2064's labelled block must now also carry `test_accuracy` into `stats.json`.\n"
_P511_NEW = "ml#2064's labelled block must now also carry `test_accuracy` into `stats.json`. **Done 2026-10-28** as ml#2381 (`c77b7be5`; XC-P12 action 4).\n"

_W4_OLD = "its `test_accuracy` waits on a cascor release with cascor#731, and on ml#2064.\n"
_W4_NEW = "its `test_accuracy` is merged too (cascor#731; ml#2381 closed ml#2064 on 2026-10-28) and fills once a cascor carrying cascor#731 serves a run with a test split: 0.13.0's image is on GHCR, and its wheel waits at the owner's `pypi` gate (§5).\n"

_CASCOR_ANCHOR = "- **Re-probed 2026-10-25**: the owner approved the gate. PyPI serves 0.12.0 from 18:13:28Z (run 38085392643 green), and juniper-deploy pins it since deploy#258 (2026-10-23). The fix-forward question stands.\n"
_CASCOR_ADD = (
    "- **juniper-cascor 0.13.0 is cut (2026-10-28; v1.15.6).** Its proposal, cascor#733, merged as `61a67c53`, and Release `v0.13.0` was published from it at 00:25:28Z (archive ml#2379). "
    "Its image is on GHCR (run 40608671351; tags `0.13.0` and `0.13`) and its wheel on TestPyPI. Its PyPI leg waits at the owner's `pypi` gate: run 40608671287, created 00:25:29Z.\n"
    "  - The working deadline is 2026-11-27 00:25Z: GitHub's Actions limits page caps an environment-approval wait at 30 days, and a run can be re-run only within 30 days of it. Its 35-day run limit, 2026-12-02 00:25Z, is the outer bound.\n"
    "  - It carries cascor#731, the final evaluation's `accuracy` (XC-P12 action 4). Like 0.12.0, it names no cascor F-S10 fix: its notes list none, and `src/api/secrets.py` is unchanged from `v0.12.0`. "
    "Its locks pin data-client 0.6.0, which carries F-S10 too. The fix-forward question stands.\n"
)

#: Fact-check MINOR-4 (stale before v1.15.6): cascor's two locks moved data-client 0.5.0 -> 0.6.0 (the 0.13.0 notes).
_IMG_OLD = "Cascor moves both locks, which pin `juniper-data-client==0.5.0` today;"
_IMG_NEW = "Cascor moves both locks, which pinned `juniper-data-client==0.5.0` (they pin 0.6.0 since the lock moves in cascor 0.13.0, and 0.6.0 carries F-S10 too);"

_HARD_OLD = "| Hard. Both cascor locks pin data-client 0.5.0 |\n"
_HARD_NEW = "| Hard. Both cascor locks pinned data-client 0.5.0; since the lock moves in cascor 0.13.0 they pin 0.6.0, which carries F-S10 too |\n"

#: Fact-check NITs: the P6 row and A1 named only the train / val half.
_P6ROW_OLD = "APD-ML-002's cascor train / val half merged under the owner's rulings of 10-26 (ml#2369, 10-27; XC-P12); 003..006 wait on one owner menu. |"
_P6ROW_NEW = "APD-ML-002's cascor train / val half merged under the owner's rulings of 10-26 (ml#2369, 10-27; XC-P12), and its `test_*` columns (ml#2381, 10-28); 003..006 wait on one owner menu. |"

_A1_OLD = "P6 OD-2 (the owner ruled APD-ML-002 itself on 2026-10-26, and its cascor train / val half merged, XC-P12 action 4;"
_A1_NEW = "P6 OD-2 (the owner ruled APD-ML-002 itself on 2026-10-26, and its cascor train / val half and `test_*` columns merged, ml#2369 and ml#2381, XC-P12 action 4;"

_OD3_OLD = "`test_*` from ml#2064. P6-08 was its only item (XC-P12 action 4);\n"
_OD3_NEW = "`test_*` from ml#2064, closed 2026-10-28 by ml#2381. P6-08 was its only item (XC-P12 action 4);\n"

_COLL_SUITE_OLD = "ml#2369 (merged 2026-10-27; P6-08's train / val half), P6-07, P6-08, P12-52 |"
_COLL_SUITE_NEW = "ml#2369 (merged 2026-10-27; P6-08's train / val half), ml#2381 (merged 2026-10-28; P5-11, with P6-08's `test_*` columns), P6-07, P12-52 |"

_COLL_STATS_OLD = "| juniper-ml `util/experiments/stats_summary.py`, `plots_cascor.py` | P5-11, P6-10, P6-11, P12-53 | P5-11 first |\n"
_COLL_STATS_NEW = "| juniper-ml `util/experiments/stats_summary.py`, `plots_cascor.py` | ml#2381 (merged 2026-10-28; P5-11), P6-10, P6-11, P12-53 | P5-11 went first (ml#2381); then one PR at a time |\n"

_COLL_RUN_OLD = "ml#2195 (merged 2026-10-09; its suites pin this file), P6-09, P6-12, P12-19, P12-31 |"
_COLL_RUN_NEW = "ml#2195 (merged 2026-10-09; its suites pin this file), ml#2381 (merged 2026-10-28; P5-11), P6-09, P6-12, P12-19, P12-31 |"

_DEP_OLD = "Bypassed 2026-10-27: P6-08's train / val half merged first, under the owner's rulings (XC-P12 action 4) |\n"
_DEP_NEW = "Bypassed 2026-10-27: P6-08's train / val half merged first, under the owner's rulings (XC-P12 action 4). Done 2026-10-28 as ml#2381 |\n"

_T1_OLD = "  - **T1**: P5-09 (its PR, after P3-03), P5-11, P5-32 (= P4-06; ran on 0.17.0's publish)\n"
_T1_NEW = "  - **T1**: P5-09 (its PR, after P3-03), P5-11 (done: ml#2381, 2026-10-28), P5-32 (= P4-06; ran on 0.17.0's publish)\n"

_T5_OLD = "P6-08 (the cascor `test_accuracy` remainder; the recurrence half shipped in ml#2145, and the cascor train / val half in ml#2369),"
_T5_NEW = "P6-08 (the cascor `test_accuracy` remainder, merged as cascor#731 and ml#2381: it fills once a cascor carrying cascor#731 serves a run with a test split, and the register row's close is the owner's; the recurrence half shipped in ml#2145, and the cascor train / val half in ml#2369),"

_MENU_OLD = "| 11 | The APD-ML menu | P6-06, P3-36, P12-04 (= APD-ML-002 = P6-08; its recurrence half is merged, and its cascor train / val half, ml#2369) |\n"
_MENU_NEW = "| 11 | The APD-ML menu | P6-06, P3-36, P12-04 (= APD-ML-002 = P6-08; its recurrence half is merged, its cascor train / val half, ml#2369, and its `test_*` columns, ml#2381) |\n"

_VALIDATION_ANCHOR = (
    "  - v1.15.5 is a record of juniper-recurrence-client 0.3.1's publish (2026-10-27), P12's follow-ups and the owner's rulings of 2026-10-26, the 0.11.2 erratum and APD-ML-002's cascor train / val half. "
    "No round checks it (owner ruling 2026-10-24); its facts cite the PRs it names, PyPI's and TestPyPI's 0.3.1 metadata, run 40417898021's jobs and approvals, `…DEFECT-REGISTER.md` §4.9, "
    "and `util/ad-hoc/2026-10-27_consolidated_plan_v1_15_5_client_0_3_1_published.py`.\n"
)
_VALIDATION_ADD = (
    "  - v1.15.6 is a record of P5-11's close (2026-10-28) and of juniper-cascor 0.13.0 at its `pypi` gate. No round checks it (owner ruling 2026-10-24); its facts cite ml#2381 and #2379, cascor#731 and #733, "
    "Release v0.13.0, runs 40608671287 and 40608671351, PyPI's, TestPyPI's and GHCR's answers for 0.13.0, the `v0.12.0...v0.13.0` compare, and `util/ad-hoc/2026-10-28_consolidated_plan_v1_15_6_p5_11_closed_cascor_0_13_0_at_gate.py`.\n"
)

_SCRIPTS_OLD = "    - and with v1.15.5's, `2026-10-27_consolidated_plan_v1_15_5_client_0_3_1_published.py` and `2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py`;\n"
_SCRIPTS_NEW = (
    "    - with v1.15.5's, `2026-10-27_consolidated_plan_v1_15_5_client_0_3_1_published.py` and `2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py`;\n"
    "    - and with v1.15.6's, `2026-10-28_consolidated_plan_v1_15_6_p5_11_closed_cascor_0_13_0_at_gate.py`;\n"
)

_MEMORY_ANCHOR = (
    "  - by session `77e26938` (2026-10-27), with v1.15.5: the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-recurrence-client 0.3.1), "
    "and `project_recurrence_equities_p0_arc_2026-10-04.md` and its line in `MEMORY.md`.\n"
)
_MEMORY_ADD = "  - by session `1fc78df5` (2026-10-28), with v1.15.6: `project_recurrence_equities_p0_arc_2026-10-04.md`, `project_pypi_publish_workflow_dual_gate.md` (a waiting gate's working deadline is day 30) and their lines in `MEMORY.md`.\n"

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.5\n", "- **Version**: 1.15.6\n"),
    (_STATUS_ANCHOR, _STATUS_ANCHOR + _STATUS_ADD),
    (_P5_OLD, _P5_NEW),
    (_P6ROW_OLD, _P6ROW_NEW),
    (_FS10_OLD, _FS10_NEW),
    (_ACT4_OLD, _ACT4_NEW),
    (_IMG_OLD, _IMG_NEW),
    (_P511_OLD, _P511_NEW),
    (_W4_OLD, _W4_NEW),
    (_CASCOR_ANCHOR, _CASCOR_ANCHOR + _CASCOR_ADD),
    (_A1_OLD, _A1_NEW),
    (_OD3_OLD, _OD3_NEW),
    (_COLL_SUITE_OLD, _COLL_SUITE_NEW),
    (_COLL_STATS_OLD, _COLL_STATS_NEW),
    (_COLL_RUN_OLD, _COLL_RUN_NEW),
    (_HARD_OLD, _HARD_NEW),
    (_DEP_OLD, _DEP_NEW),
    (_T1_OLD, _T1_NEW),
    (_T5_OLD, _T5_NEW),
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
