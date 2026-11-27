#!/usr/bin/env python3
"""Consolidated development plan v1.15.17 -> v1.15.18: the template sweep and its ports, 2026-11-23 to 2026-11-26.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor#777 (the sweep); juniper-cascor-client#206 and #207, juniper-data-client#274, juniper-cascor-worker#238,
         juniper-canopy#844, juniper-data#553, juniper-recurrence#241 and juniper-ml#2673 (the ports); handoffs ml#2614, ml#2620,
         ml#2630, ml#2658 and ml#2676; notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md (ml#2619);
         util/ad-hoc/2026-11-23_consolidated_plan_v1_15_17_one_artifact.py (the pattern)

Why
---
v1.15.17 recorded the one-artifact publish and the template sweep's order, and left the sweep, its ports and v1.15.18
as "What remains". Three sessions then carried it out (11a98f94, d935c226 and 3792e0cc, 2026-11-23 to 2026-11-26):

- juniper-cascor#777 carried the sweep to cascor's three publishers on 2026-11-24, after four review rounds of its
  writer's tree;
- the port checker took seven more rounds (6 to 12) and two of the Overtoad's rulings before round 12 found no BLOCKER or
  MAJOR, and fix pass 11 made it final;
- the 15 ports in 7 repositories merged on 2026-11-26, each after an independent review, with juniper-cascor-client#207,
  and the checker then passed all 18 publishers on every ``main``.

This revision records that in the plan's own structure: the Date and Version lines and a header bullet; the arc's
handoffs and the review archive's short form in "Documents referenced"; a note in section 5 after the one-artifact
publish's; ``v1.15.18:`` notes under each passage the arc, or ml#2619's inventory (its group E and section 4's gaps),
shows is done or superseded, the passages that still gave juniper-observability 0.4.3 to R-OBS-SC-3 among them; the
Overtoad's items in section 6's mid-wave sitting; a Validation record entry; and the landed and archived files in
"Changed by this plan". docs/REFERENCE.md needs no row: juniper-ml#2673 added its own (0.6.86).

Draft 1 was read by two independent validators (a fact re-probe and a completeness attack); every finding was re-checked
at its source and applied here (the Validation record's v1.15.18 entry).

Usage
-----
    python3 util/ad-hoc/2026-11-26_consolidated_plan_v1_15_18_template_sweep.py [--tree DIR] [--check]

An edit already present is skipped, so a re-run is a no-op. An anchor found other than once refuses the whole run before
anything is written, and so does any rise in the number of plan lines over 512 characters (28 before this revision).
``--check`` writes nothing and exits 1 while an edit is pending.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md"
MAX_LINE = 512

# Multi-line texts are bound to names here rather than written inside a list display: adjacent literals inside a list
# or tuple trip CodeQL's py/implicit-string-concatenation-in-list and flake8-bugbear's B914.

_TNOTE = "§5, the note on the template sweep"
_ARCHIVE = "reports/2026-11-23_one-artifact-template-sweep-reviews/"
_RECORD = "`SW/dispositions.md`"
_PORT_BRIEF = "`SW/sweep-port_brief.md`"
_PORT_REVIEW_BRIEF = "`SW/sweep-port-review_brief.md`"
_PROOF_ARCHIVE = "`juniper-ml/tmp/worktree-archive-2026-11-26/`"
_REMAINING = "`…REMAINING-TASKS.md`"
_SEVEN = "`…seven-worktrees-archived.md`"
_RENAME_HO = "`…recurrence-deploy-next.md`"
_R44 = "R-OBS-SC-3 is now juniper-observability 0.4.4 (the Overtoad's ruling of 2026-11-24); 0.4.3 is the sentry-sdk 3.x port"

# --- Header ------------------------------------------------------------------------------------------------------------
_DATE_OLD = "and the template sweep's order probed 2026-11-23)\n"
_DATE_NEW = (
    "and the template sweep's order probed 2026-11-23; the template sweep, its port checker and the 15 ports, "
    "and the entries ml#2619 lists as done, probed 2026-11-26)\n"
)

_V17_RELEASE_OLD = "No Release has run them yet. Like v1.15.0, no round checks it.\n"
_V17_RELEASE_NEW = "No Release had run them by 2026-11-23 (v1.15.18: one started on 2026-11-26). Like v1.15.0, no round checks it.\n"

_STATUS_ANCHOR = "  - Planning only: this plan changes no code,"
_STATUS_NEW = (
    "  - v1.15.18 (2026-11-26) records the template sweep and its ports (" + _TNOTE + "). juniper-cascor#777 carried the sweep to cascor's three publishers on 2026-11-24, "
    "after four review rounds of its writer's tree, and the 15 ports in 7 repositories merged on 2026-11-26, each after an independent review. Like v1.15.0, no round checks it.\n"
    "    - The port checker took seven rounds of its own and two of the Overtoad's rulings (\"Pin exact scripts (Recommended)\", \"Pin template SHAs (Recommended)\") "
    "before round 12 found no BLOCKER or MAJOR; on every `main` it then passed all 18 publishers (\"18 of 18 pass\").\n"
    "    - The note also records the residuals the checker and the reviews leave, SWEEP items 28 and 29, and the first Release since the one-artifact publish, "
    "juniper-observability-v0.4.3, whose PyPI job waits at its `pypi` gate.\n"
    "    - It records the entries " + _REMAINING + " (ml#2619) lists as done or superseded: cascor#772 merged, juniper-deploy#284 pins juniper-recurrence 0.8.1, "
    "seven worktrees were archived and removed, the parent `AGENTS.md` backups are restored, and R45 to R52 are done. It marks the passages that still gave 0.4.3 "
    "to R-OBS-SC-3, which the Overtoad moved to 0.4.4 on 2026-11-24.\n"
    "    - The arc's scripts land with it; its record, briefs and reviews, and this record's validation, are archived in `" + _ARCHIVE + "`, and the sweep's proof drivers "
    "in " + _PROOF_ARCHIVE + ". What stays with the Overtoad is in " + _TNOTE + " and in §6's mid-wave sitting.\n"
    + _STATUS_ANCHOR
)

# --- Documents referenced ----------------------------------------------------------------------------------------------
_SHORT_OLD = "Short forms used below. `HO/` = `prompts/thread-handoff_automated-prompts/`.\n"
_SHORT_NEW = "Short forms used below. `HO/` = `prompts/thread-handoff_automated-prompts/`; `SW/` = `" + _ARCHIVE + "` (v1.15.18).\n"

_FLOOD4_OLD = "its §8 lists rulings 1–14) |\n"
_FLOOD4_NEW = "its §8 lists rulings 1–14; v1.15.18: 1–49, since ml#2635 and ml#2677) |\n"

_DOCS_ANCHOR = (
    "| `…sweep-ruled-brief-cascor-plan-v1-15-17-next.md` | `HO/HANDOFF_2026-11-16_one-artifact-ports-merged-verified-sweep-ruled-brief-cascor-plan-v1-15-17-next.md` "
    "(the merges, the identity check, the rulings of 2026-11-16; ml#2603) |\n"
)
_DOCS_NEW = (
    _DOCS_ANCHOR
    + "| `…land-after-cascor-772.md` | `HO/HANDOFF_2026-11-23_one-artifact-sweep-plan-v1-15-17-merged-round-4-majors-fix-pass-3-round-5-land-after-cascor-772.md` "
    "(the sweep's rounds 1 to 4 and fix pass 3's brief; session `11a98f94`; ml#2614) |\n"
    "| `…round-7-then-ports-plan-v1-15-18.md` | `HO/HANDOFF_2026-11-24_one-artifact-sweep-cascor-777-merged-checker-round-6-blocker-fix-pass-5-round-7-then-ports-plan-v1-15-18.md` "
    "(juniper-cascor#777 merged, round 6's BLOCKER; session `d935c226`; ml#2620) |\n"
    "| `…fix-pass-7-round-9-then-ports.md` | `HO/HANDOFF_2026-11-24_one-artifact-sweep-owner-rules-pin-exact-install-scripts-fix-pass-7-round-9-then-ports.md` "
    "(the \"Pin exact scripts\" ruling; ml#2630) |\n"
    "| `…fix-pass-11-final-ports-next.md` | `HO/HANDOFF_2026-11-25_one-artifact-sweep-port-checker-cleared-round-12-fix-pass-11-final-ports-next.md` "
    "(round 12 cleared the checker; ml#2658) |\n"
    "| `…18-of-18-plan-v1-15-18-next.md` | `HO/HANDOFF_2026-11-26_one-artifact-sweep-all-ports-landed-18-of-18-plan-v1-15-18-next.md` "
    "(the ports and juniper-cascor-client#207; session `3792e0cc`, ListAgents `moonlit-percolating-sun-fa` [b71989]; ml#2676) |\n"
    "| " + _SEVEN + " | `HO/HANDOFF_2026-11-23_r-obs-sc-2-owner-items-recurrence-pin-0-8-1-seven-worktrees-archived.md` "
    "(juniper-deploy#284, the housekeeping and the restored backups; session `2222e504`, ListAgents [9660dc]; ml#2616) |\n"
    "| " + _RENAME_HO + " | `HO/HANDOFF_2026-11-23_overtoad-rename-repair-ml-2606-recurrence-deploy-next.md` (the rename-repair line's handoff, with the \"Symlinks\" answer; ml#2624) |\n"
    "| " + _REMAINING + " | `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` "
    "(ml#2619's inventory of R-OBS-SC-2's remaining tasks; its group C's R28 to R41, its group E and §4's gaps 1 to 9 are this lane's (`plan_v1_15_18_inputs.md`), and this record also takes in gaps 11, 16 and 17) |\n"
)

# --- v1.15.18 notes under older passages: the overview, XC-SENTRY and section 4 ------------------------------------------
_SUB_170_OLD = "but not query strings, Sentry Logs or exception values (0.4.3; v1.15.15).\n"
_SUB_170_NEW = "but not query strings, Sentry Logs or exception values (0.4.3; v1.15.15; v1.15.18: 0.4.4).\n"

_SUB_173_OLD = "so XC-SENTRY's (a) and (b) stay in force (§4 Wave 1; §5; v1.15.15).\n"
_SUB_173_NEW = (
    _SUB_173_OLD
    + "       - v1.15.18: " + _R44 + ", at its `pypi` gate since 2026-11-26. Its Release lists three exposures as Known Issues "
    "(the client address in five proxy headers, canopy's `authkey` on sentry-sdk 2.x, Sentry Logs' extra fields), so (a) and (b) outlast 0.4.3 too (" + _REMAINING + ").\n"
)

_SUB_520_OLD = "while pip reports 0.4.1 and 0.7.1 (v1.15.16).\n"
_SUB_520_NEW = (
    _SUB_520_OLD
    + "  - v1.15.18: since R21 (2026-11-24 22:30Z) `JuniperData` and `JuniperCanopy1` hold observability 0.4.2 and service-core 0.7.2; its second pass, to 0.4.3, "
    "and R22's probe follow 0.4.3 on PyPI. At 21:54:57Z on 2026-11-26 the primary is on `main` at `557490fb`, whose observability is 0.4.3's code (" + _TNOTE + ").\n"
)

_SUB_528_OLD = "Not probed: the four canopy E2E legs (`:8052`, `:8053`, `:8058`, `:8059`), listening on 2026-11-15.\n"
_SUB_528_NEW = (
    _SUB_528_OLD
    + "  - v1.15.18: none of those four ports listened at 21:54:57Z on 2026-11-26, and no Juniper container existed at 22:49:02Z (`docker ps -a`) (" + _TNOTE + ", R65).\n"
)

_SUB_530_OLD = "Sentry Logs and exception values to 0.4.3 (R-OBS-SC-3), so (a) and (b) stay in force.\n"
_SUB_530_NEW = _SUB_530_OLD + "\n- v1.15.18: " + _R44 + ", not that design (" + _TNOTE + ").\n"

_SUB_677_OLD = "both versions are in `juniper-ml/tmp/2026-11-07-parent-agents-md-backup/`.\n"
_SUB_677_NEW = (
    _SUB_677_OLD
    + "    - v1.15.18: the rename's substitution rewrote both on disk; they were restored to `29e375ff…` and `48e2568a…` on 2026-11-23, "
    "each rewritten copy kept beside it (" + _TNOTE + ").\n"
)

_SUB_875_OLD = "and `JuniperCascor1` imported the primary at `eeb5c694` (XC-SENTRY).\n"
_SUB_875_NEW = (
    _SUB_875_OLD
    + "       - v1.15.18: `JuniperData` and `JuniperCanopy1` hold observability 0.4.2 and service-core 0.7.2 since R21 (2026-11-24); its second pass, to 0.4.3, "
    "and R22's probe wait for 0.4.3 on PyPI, and the primary's `main` carries 0.4.3's code (" + _TNOTE + ").\n"
)

_SUB_879_OLD = "still exits 1 on it. Whether recurrence's pin moves is the Overtoad's.\n"
_SUB_879_NEW = (
    _SUB_879_OLD
    + "       - v1.15.18: it moved: juniper-deploy#284 (2026-11-23 20:55:09Z, `7e996845`) pins 0.8.1 on the Overtoad's \"Move it now (Recommended)\", "
    "and `--fail-on-stale` exits 0.\n"
)

_SUB_894_OLD = "     - The Overtoad restarts the juniper-deploy stack (ruling 6 of 2026-11-13 governs only the trio's restart).\n"
_SUB_894_NEW = (
    _SUB_894_OLD
    + "       - v1.15.18: no Juniper container exists (`docker ps -a`, 22:49:02Z on 2026-11-26), so this is a bring-up (R25), with the DSNs XC-SENTRY's (b) "
    "decides for those services (R9; " + _REMAINING + ").\n"
)

# --- v1.15.18 notes under section 5 ------------------------------------------------------------------------------------
_SUB_1053_OLD = "| **R-OBS-SC-3** (owed; Overtoad ruling 2026-11-08): juniper-observability 0.4.3 |"
_SUB_1053_NEW = (
    "| **R-OBS-SC-3** (owed; Overtoad ruling 2026-11-08): juniper-observability 0.4.3; v1.15.18: **0.4.4**, by the Overtoad's ruling of 2026-11-24, "
    "since 0.4.3 is the sentry-sdk 3.x port (cut 2026-11-26, at its `pypi` gate) |"
)

_SUB_1078_OLD = "whose service-core is 0.7.2's plus four unreleased fixes (XC-SENTRY; v1.15.16).\n"
_SUB_1078_NEW = (
    _SUB_1078_OLD
    + "    - v1.15.18: since R21 (2026-11-24) the first two hold 0.4.2 and 0.7.2 (a second pass follows 0.4.3 on PyPI), and the primary's `main` carries "
    "0.4.3's code (" + _TNOTE + ").\n"
)

_SUB_1089_OLD = "P2-09's and P12-28's service-core halves did not ride 0.7.2, and wait for a later service-core release.\n"
_SUB_1089_NEW = _SUB_1089_OLD + "  - v1.15.18: " + _R44 + ", cut on 2026-11-26 and at its `pypi` gate (" + _TNOTE + ").\n"

_SUB_1138_OLD = "which #278 left alone. Whether recurrence's pin moves is the Overtoad's.\n"
_SUB_1138_NEW = _SUB_1138_OLD + "    - v1.15.18: it moved: juniper-deploy#284 (2026-11-23 20:55:09Z, `7e996845`); `--fail-on-stale` exits 0.\n"

_SUB_1162_OLD = "(a verbatim copy of `tmp/lps/fixpass_r1.md`, sha256 `ad8d9091…`).\n"
_SUB_1162_NEW = (
    _SUB_1162_OLD
    + "  - v1.15.18: eight of these are done (" + _REMAINING + " § \"Checked and changed, 2026-11-24\"; each PR read MERGED on 2026-11-26): A-5's `telemetry=` "
    "(R52, ml#2627, in service-core's `[Unreleased]`), A-4's telemetry test (R45: data#551, cascor#779, canopy#840), B-10's exempt paths (R46, cascor#778), "
    "the drift tool's second kind and `answered None` (R50 and R51, ml#2637), the `dash` pin (R47, canopy#839), the schema-drift comment (R48, canopy#838) "
    "and the register's compare row (R49, ml#2623).\n"
    "    - Still open: the wall clock (R11, with B-9), the WebSocket rounding (R12), the `tmp/` walk (R13), the `<0.8.0` caps (R53) and the v2 draft's stale lines "
    "(R10, the Overtoad's; §6).\n"
)

_SUB_1153_OLD = "Whether a check of the paragraph came with them was not re-read here.\n"
_SUB_1153_NEW = (
    _SUB_1153_OLD
    + "      - v1.15.18: one came later: juniper-ml#2631 (2026-11-24 13:06:28Z, `9a9ef3fb`; flood-4's ruling 48) makes the paragraph state the rule "
    "its matrix tests enforce, and a test pins it.\n"
)

_SUB_1159_OLD = "Next: flood-4's session, in the record's next update.\n"
_SUB_1159_NEW = (
    _SUB_1159_OLD
    + "      - v1.15.18: done: juniper-ml#2635 (2026-11-24 14:51:35Z, `0a7c602c`) records rulings 15 to 48, ruling 17 as one ruling over its four fixes, "
    "and juniper-ml#2677 (2026-11-26 13:58:08Z, `89e876d2`) ruling 49.\n"
)

_SUB_1161_OLD = "No design is on `main` yet, and the Overtoad launches its session (R-OBS-SC-3, above; §7.1).\n"
_SUB_1161_NEW = (
    _SUB_1161_OLD
    + "  - v1.15.18: the design is now 0.4.4's (the Overtoad's ruling of 2026-11-24). The prompt keeps its file name, with dated addenda of 2026-11-23 (sentry-sdk 3.0.0) "
    "and 2026-11-24 (the move to 0.4.4); no design is on `main` yet.\n"
)

_SUB_1166_OLD = "#278 left it, so `--fail-on-stale` still exits 1;\n"
_SUB_1166_NEW = (
    _SUB_1166_OLD
    + "      - v1.15.18: it moved: juniper-deploy#284 (2026-11-23 20:55:09Z, `7e996845`), and `--fail-on-stale` exits 0;\n"
    "    - v1.15.18: no Juniper container exists (`docker ps -a`, 2026-11-26), so the stack's restart is a bring-up (R25), and XC-SENTRY's (b) for it, blank DSNs, "
    "stays the Overtoad's (R9);\n"
)

_SUB_1189_OLD = "`prompts/generated/JUNIPER_ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md` (ruling 4 of 2026-11-13; §7.1);\n"
_SUB_1189_NEW = (
    _SUB_1189_OLD
    + "    - v1.15.18: the design is now 0.4.4's (the Overtoad's ruling of 2026-11-24; the prompt's addendum of that day), and 0.4.3 is the sentry-sdk 3.x port;\n"
)

_SUB_1190_OLD = "then the trio's restart on the condition of ruling 6 of 2026-11-13: the probe's recorded pass in each environment, P3-05, and blank DSNs;\n"
_SUB_1190_NEW = (
    _SUB_1190_OLD
    + "    - v1.15.18: since R21 (2026-11-24 22:30Z) both hold observability 0.4.2 and service-core 0.7.2, sentry-sdk held below 3; a second pass takes them to 0.4.3 "
    "once it is on PyPI, and R22's per-environment probe follows that pass, before any restart (" + _REMAINING + " § \"Checked and changed, 2026-11-24\");\n"
)

_SUB_1172_OLD = "before `buzzing-growing-whale` goes.\n"
_SUB_1172_NEW = (
    _SUB_1172_OLD
    + "    - v1.15.18: on 2026-11-23 session [9660dc] removed seven worktrees, `buzzing-growing-whale` among them, and four merged branches, "
    "their `tmp/` archived first in `juniper-ml/tmp/worktree-archive-2026-11-23/`. The copy named here had been rewritten by the rename's substitution "
    "and was restored to `90df2783…` the same day (" + _TNOTE + ").\n"
)

_SUB_1198_OLD = "now give PyPI the very files TestPyPI took, checked by sha256; no Release has run them yet.\n"
_SUB_1198_NEW = (
    "now give PyPI the very files TestPyPI took, checked by sha256; no Release has run them yet "
    "(v1.15.18: juniper-observability-v0.4.3's, on 2026-11-26, is the first to start).\n"
)

_SUB_1240_OLD = "no release has been cut since (canopy `v0.10.0`, 2026-11-15 01:41:30Z, is the newest).\n"
_SUB_1240_NEW = (
    _SUB_1240_OLD
    + "      - v1.15.18: juniper-observability-v0.4.3 was cut on 2026-11-26 at 02:04:23Z; TestPyPI serves its files, and its PyPI job waits at the `pypi` gate "
    "(" + _TNOTE + ").\n"
)

_SUB_1243_OLD = "Its answer gates cascor#772.\n"
_SUB_1243_NEW = (
    _SUB_1243_OLD
    + "      - v1.15.18: answered \"Rebuild as one signed commit (Recommended)\" (" + _RENAME_HO + "), and cascor#772 merged at 19:35:14Z as `e9c86f83` (the next note).\n"
)

_SUB_1246_OLD = "and juniper-ml#2606 and juniper-data#547 were open without it.\n"
_SUB_1246_NEW = (
    _SUB_1246_OLD
    + "      - v1.15.18: all but ml#2605 merged: cascor#772 at 19:35:14Z, data#547 at 20:39:16Z, canopy#830 at 21:05:44Z, and ml#2606 on 2026-11-24 at 05:06:27Z. "
    "ml#2605 closed unmerged at 20:54:14Z, and juniper-harcot#28 merged at 20:39:13Z.\n"
)

_SUB_1257_OLD = "A successor to the identity checker, which compares each `uses:` by action name, is being written with it.\n"
_SUB_1257_NEW = (
    _SUB_1257_OLD
    + "    - v1.15.18: both files are archived as `SW/sweep_brief.md` and `SW/sweep_items.md` (item 23, for one: the template blocks' digest pins, which the sweep "
    "made ref-free, normalized), SWEEP items 28 and 29 were added, and the successor checker is written: `util/ad-hoc/2026-11-23_publish_port_template_identity.py` (the next note).\n"
)

_SUB_1281_OLD = "holds those items and the worktree housekeeping. None is done.\n"
_SUB_1281_NEW = (
    _SUB_1281_OLD
    + "- **Since then** (v1.15.18): the first four are done (the next note). Of the Overtoad's items, juniper-deploy's recurrence pin moved (juniper-deploy#284) "
    "and the trio's environments hold 0.4.2 and 0.7.2 (R21's first pass, 2026-11-24); no Juniper container exists, so the stack's restart is a bring-up (R25); "
    "the trusted-publisher check is open; and [9660dc] removed seven worktrees on 2026-11-23.\n"
)

# --- v1.15.18 notes under section 6, section 7, section 11-12 and the Validation record's neighbours --------------------
_SUB_1401_OLD = "the v2 draft's pointer; and the worktree housekeeping.\n"
_SUB_1401_NEW = (
    _SUB_1401_OLD
    + "  - v1.15.18: the recurrence pin moved (juniper-deploy#284); the trio's environments hold 0.4.2 and 0.7.2 (R21's first pass; its second and R22's probe follow "
    "0.4.3 on PyPI); the stack's restart is a bring-up, no container existing (R25); and seven worktrees were removed and archived on 2026-11-23. "
    "The design session to launch is now 0.4.4's (the Overtoad's ruling of 2026-11-24). The rest is open (" + _TNOTE + ").\n"
)

_SUB_1403_OLD = "its fifth, \"Symlinks\", is open and gates juniper-cascor#772.\n"
_SUB_1403_NEW = (
    _SUB_1403_OLD
    + "  - v1.15.18: \"Symlinks\" was answered \"Rebuild as one signed commit (Recommended)\", and juniper-cascor#772 merged on 2026-11-23.\n"
    "- **Left with the Overtoad by the template sweep** (v1.15.18; " + _TNOTE + "):\n"
    "  - two decisions the arc's record leaves to this plan (" + _RECORD + " § \"Fix pass 10\"): whether to pin the build job's steps before the build, as install scripts "
    "are (M11-C, R11-1), and whether to accept in writing that the publish action's container image is named by a re-pushable tag, or to record the image digest "
    "the template's review saw (M11-E);\n"
    "  - the retention of `juniper-ml/tmp/worktree-archive-2026-11-23/` (R18; " + _TNOTE + " records what it backs) and of " + _PROOF_ARCHIVE + "; "
    "R16, removing `giggly-foraging-sunbeam`, `sparkling-percolating-meadow` and `agent-a54a0a279acc3a863`; and R17, `juniper-ml/tmp/retry-after-guard-ssq1mano`;\n"
    "  - and removing the arc's worktrees, `ethereal-munching-peacock` and `moonlit-percolating-sun`, once all of their `tmp/` is archived, which is not done (R41).\n"
)

_SUB_1494_OLD = "and the restart's condition is that of ruling 6 of 2026-11-13 (v1.15.16).\n"
_SUB_1494_NEW = (
    _SUB_1494_OLD
    + "  - v1.15.18: `JuniperData` and `JuniperCanopy1` hold 0.4.2 and 0.7.2 since R21 (2026-11-24); a second pass to 0.4.3, after its `pypi` gate, and R22's probe "
    "come before the restart (" + _TNOTE + ").\n"
)

_SUB_1498_OLD = "and when R-OBS-SC-3 (0.4.3) is designed: all ruled"
_SUB_1498_NEW = "and when R-OBS-SC-3 (0.4.3; v1.15.18: 0.4.4) is designed: all ruled"

_SUB_1584_OLD = "left `:598` at `juniper-recurrence:0.8.0` while 0.8.1 is published (2026-11-06); whether it moves is the Overtoad's.\n"
_SUB_1584_NEW = (
    "left `:598` at `juniper-recurrence:0.8.0` while 0.8.1 is published (2026-11-06); whether it moves is the Overtoad's. "
    "v1.15.18: it moved to 0.8.1 (juniper-deploy#284, 2026-11-23).\n"
)

_SUB_1602_OLD = "19. R-OBS-SC-3's 0.4.3 design (ruling 4 of 2026-11-13):"
_SUB_1602_NEW = "19. R-OBS-SC-3's 0.4.3 design, 0.4.4 since the Overtoad's ruling of 2026-11-24 (v1.15.18) (ruling 4 of 2026-11-13):"

_SUB_1799_OLD = "whether the data API key's env-var value ever had leading whitespace or a line break, and the quiet window.\n"
_SUB_1799_NEW = _SUB_1799_OLD + "  - v1.15.18: at 21:54:57Z on 2026-11-26 no canopy E2E leg listened, and at 22:49:02Z no Juniper container existed (`docker ps -a`).\n"

_SUB_1885_OLD = "XC-SENTRY now and until 0.4.3 (R-OBS-SC-3);"
_SUB_1885_NEW = "XC-SENTRY now and until R-OBS-SC-3 (0.4.3 until the Overtoad's ruling of 2026-11-24, 0.4.4 since; v1.15.18);"

_RESTORED = "    - v1.15.18: the rename's substitution rewrote both copies on disk; they were restored to their recorded sha256 on 2026-11-23 (" + _TNOTE + ").\n"
_SUB_2547_OLD = "both versions in `juniper-ml/tmp/2026-11-01-parent-agents-md-backup/`) and `project_recurrence_equities_p0_arc_2026-10-04.md`; `MEMORY.md` is unchanged.\n"
_SUB_2547_NEW = _SUB_2547_OLD + _RESTORED
_SUB_2550_OLD = (
    "both versions in `juniper-ml/tmp/2026-11-07-parent-agents-md-backup/`) and `project_recurrence_equities_p0_arc_2026-10-04.md` "
    "(a new state block and its description); this session did not change `MEMORY.md`.\n"
)
_SUB_2550_NEW = _SUB_2550_OLD + _RESTORED

_SUB_2670_OLD = "whose prior copy is `tmp/s2/parent_AGENTS_before_2026-11-14.md` in worktree `buzzing-growing-whale`.\n"
_SUB_2670_NEW = (
    _SUB_2670_OLD
    + "      - v1.15.18: that worktree was removed on 2026-11-23. Its copy, `buzzing-growing-whale/tmp/s2/parent_AGENTS_before_2026-11-14.md` in "
    "`juniper-ml/tmp/worktree-archive-2026-11-23/`, is the substituted text (sha256 `d8ab5749…`, the backup's `*.substituted-2026-11-20`), not the prior copy, "
    "whose bytes (`90df2783…`) are the restored backup below (re-read 2026-11-26 23:31:39Z).\n"
)

# --- Section 5: the new note -------------------------------------------------------------------------------------------
_N_HEAD = (
    "**The template sweep and its ports, 2026-11-23 to 2026-11-26** (v1.15.18; sessions `11a98f94` (ListAgents [e71d3e]), which ran the sweep's rounds 1 to 4, "
    "`d935c226` ([ffffd3]), which ran fix passes 3 to 11, rounds 5 to 12 and juniper-cascor#777, and `3792e0cc` (`moonlit-percolating-sun-fa`, [b71989]), "
    "which ran the ports). The sweep (the previous note's last items) is on all 18 publishers: #777 carried it to cascor's three, and 15 ports in 7 repositories copied it.\n"
    "The arc's own record, `REVIEW_DISPOSITIONS.md`, is archived as " + _RECORD + " with the briefs, reviews and executor reports it cites (`SW/README.md`). "
    "Every fact below was re-read on 2026-11-26 from `gh`, from the files it names or from that record, and its rulings are quoted from that record, "
    "where each session wrote them as its dialog returned them, but for three approvals dated from the transcripts (below). Review counts are BLOCKER/MAJOR/MINOR/NIT.\n"
    "\n"
)

_N_ROUNDS = (
    "- **The sweep's review on cascor's tree** (2026-11-23): four review rounds, 1, 2, 4 and 5, since round 3 was the second fix pass. Every fix went into the writer, "
    "`util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py` (it lands with v1.15.18), so a re-run on a cascor base reproduces the tree; "
    "the landed one is the writer `c47940ad…` on `36dd6f2d` with `--date 2026-11-24`.\n"
    "  - Round 1, two lenses. The workflow lens found 0/0/6/7: among them M2 (a \"Re-run failed jobs\" attempt carries copies of earlier jobs; v1.15.17 records the probe "
    "that confirmed it), M4 (a sub-package's plain dispatch took any tag), and M5 and N6, deferred as SWEEP items 28 and 29 (below).\n"
    "  - The test lens: 15 of 55 property-breaking mutations survived the suite, and 21 passed the checker. The fixes pin each install step's whole command list, "
    "each job's keys and `runs-on`, and the build commands (`util/ad-hoc/2026-11-23_publish_one_artifact_test_lens_mutations.py` and `…_test_lens_proposed_fixes.py`).\n"
    "  - Round 2: the workflow fixes held when executed, but the checker was too strict, failing 10 of the 15 faithful port simulations "
    "(F1 and F2, both BLOCKERs: juniper-ml's tag assert and canopy's smoke step, and juniper-ml's two-phase verify), and too weak (F4: `PIP_*` settings "
    "and other pip spellings got round its install rules; `util/ad-hoc/2026-11-23_publish_sweep_r2_review_probes.py`).\n"
    "  - Round 3, the second fix pass: the diff `e02b4da8…` (11 files, +1151/-190); 161 tests, 45 of 45 mutations caught, 15 of 15 port simulations, and the checker's proof 74 of 74.\n"
    "  - Round 4: 0 BLOCKER and 2 MAJORs, neither in cascor's tree. R4-1, a port item: juniper-ml's tests would skip every #384 pin once the install check left "
    "the TestPyPI job (28 tests down to 4, CI green). R4-2: a `| tee` or a `&` after the last import let a failing import exit 0, and the checker passed it "
    "(`util/ad-hoc/2026-11-23_publish_sweep_r4_review_probes.py`).\n"
    "  - Fix pass 3 fixed the checker and the writer's texts on both bases, cascor `802399ab` and `e9c86f83` (#772's merge; the diff `a6399122…`), and accounted for "
    "every file between round 3's tree, built on #772's old head `1e6e877a`, and the rebuilt base (" + _RECORD + " § \"Fix pass 3\").\n"
    "  - Round 5 (22:28Z to 23:32Z): 0/1/5/2. Its MAJOR, R5-F1, was in the checker (an echo's arguments are expanded before it runs, so the plain-echo relaxation "
    "reopened a bypass), and cascor's tree was sound.\n"
    "    - The round's brief let the landing go ahead only after a round with no BLOCKER and no MAJOR. Session `ffffd3` decided that round 5 met that for cascor's tree, "
    "since the MAJOR was in the checker, which gates the ports and is not in the cascor PR; it landed the PR and gave the checker rounds of its own.\n"
    "    - That was the session's decision, recorded in " + _RECORD + ", not a dialog's, though `…fix-pass-11-final-ports-next.md` lists it under "
    "\"The owner's three rulings of this arc\", as \"this session's decision, recorded\".\n"
)

_N_777 = (
    "- **juniper-cascor#777** (\"fix(publish): the install check gets a job that cannot mint, the republish job checks the release run's TestPyPI jobs, and PUBLISH_TAG_PREFIX\"): "
    "one signed commit, `a12b2c5f` on `36dd6f2d`, opened at 00:25:47Z on 2026-11-24, and a fix-up, `74971d3a`, moving three date lines to 2026-11-24 for "
    "`Verify AGENTS.md Last Updated` (the commit had landed after midnight UTC).\n"
    "  - 25 of 25 required checks passed on both heads. `util/safe_merge.py` merged it at 00:56:52Z as `f5ed3017` (11 files), under the merge approval the Overtoad "
    "gave session `ffffd3` at its start, the squash keeping its `Allow-Symbol-Loss:` line. Every post-merge run on `main` succeeded by 01:09:15Z "
    "(`…round-7-then-ports-plan-v1-15-18.md`). The done-check then printed `3 of 18 pass`: cascor's three.\n"
)

_RULING_PINS = (
    "    - The option's text: \"Stop judging port install scripts with a bash reader. Each port's install step must equal, after whitespace normalization, "
    "a pinned reviewed script for that port (seeded from the 15 port simulations, updated in each port's own review). This closes every lexing bypass at once "
    "and matches what each repo's tests already pin. One review round on that change, then the ports.\"\n"
)
_RULING_SHAS = (
    "    - The option's text: \"In the jobs that hold id-token (TestPyPI, PyPI, republish) and the jobs they need, every uses: must equal the template's exact "
    "owner/repo@<40-hex SHA>. A Dependabot bump in a port repo then fails this cross-repo check until cascor's template takes the same bump; each repo's own CI "
    "keeps item 23's ref-free digests, so no repo's CI is affected.\"\n"
)
_N_CHECKER = (
    "- **The port checker**, `util/ad-hoc/2026-11-23_publish_port_template_identity.py` (the identity check's successor; it lands with v1.15.18), had rounds 6 to 12 "
    "of its own, each a fresh agent's, and fix passes 4 to 11. Its sha256 after each pass: `ebeb7556…`, `6b2443c6…`, `789287c5…`, `039e5e6d…`, `9cf16a2f…`, "
    "`23707ac6…`, `b807d3ca…` and `a452db3d…`.\n"
    "  - Fix pass 4 (2026-11-23 23:45Z to 2026-11-24 00:40Z) added a positive allow-list over a bash lexer, in place of more deny rules (the deny rules stayed, as a "
    "second line). Round 6: 1/0/0/2. Its BLOCKER, R6-F1: a line continuation, which the checker joined with a blank where bash deletes it, hid a `$(…)` that ran a PyPI install.\n"
    "  - Fix pass 5 closed it. Round 7 found 0/0/1/4 but was INCOMPLETE (an interruption stopped its executed-mutant step), so it could not clear the ports, "
    "and fix pass 6 followed. Round 8, complete: 0/3/0/5, each MAJOR an executed mutant (a digit against `&>`, the name `_`, a quote that fooled `shlex`).\n"
    "  - Rounds 4 to 8 had each found a bypass of the install-script rules rated MAJOR or worse (R4-2, R5-F1, R6-F1, round 7's R7-1 once fix pass 6 executed it, "
    "and R8-1 to R8-3), every one from the checker reading shell differently from bash. The Overtoad ruled (session `ffffd3`'s dialog, header \"Checker\", "
    "answered by 12:15:11Z on 2026-11-24): **\"Pin exact scripts (Recommended)\"**. Not chosen: \"Keep fixing the reader\" and \"Fix pass 7, then ports\".\n"
    + _RULING_PINS
    + "  - Fix pass 7 (about 12:25Z to 13:15Z) did so. The checker went from 1753 lines to 953, and `util/ad-hoc/2026-11-24_publish_port_install_pins.json` (it lands "
    "with v1.15.18) pins the `run` step of each publisher's `Verify the TestPyPI install` job, 18 in all, keyed by repository, workflow file and step name. "
    "The option's one review round became four: rounds 9 to 11 each found a BLOCKER or a MAJOR outside the install script (round 11's in what the checker prints).\n"
    "  - Round 9: 1/3/2/3: the jobs that hold the upload credential accepted `container:`, `services:` and any `runs-on`; setup-python's `with:` went unread; "
    "and PyYAML typed plain scalars by YAML 1.1 where GitHub uses 1.2. Fix pass 8 held each job to the template's exact keys, typed by YAML 1.2, and refused a non-ASCII pins file.\n"
    "  - Round 10: 3/0/1/2. The upload step's inputs were read under four literal names, while GitHub matches input names case-insensitively and the publish action "
    "also reads a deprecated `repository_url`, so either could send the PyPI job's token to another host; an extra job could replace the build's artifact; "
    "and `uses:` was compared by action name, so another ref passed.\n"
    "  - The Overtoad's ruling on action refs (header \"Action refs\", answered by 2026-11-24 21:16:47Z): **\"Pin template SHAs (Recommended)\"**. "
    "Not chosen: \"Any full SHA\" and \"Accept the residual\".\n"
    + _RULING_SHAS
    + "  - Fix pass 9 (begun just before 21:26:11Z; to 22:23Z) applied it, with an exact allow-list of extra jobs: it admits only juniper-data's `notify-consumers`, "
    "whose called file it pins by sha256 (`e17ddc9b…`), so the checker reads that file beside juniper-data's `publish.yml`.\n"
    "  - Round 11 (22:25Z to 23:05Z): 0/1/4/5. Its MAJOR: a loaded string could print a forged `PASS` line in a terminal through an escape or a newline, while the "
    "exit status stayed right. Fix pass 10 refused unprintable text at load and escaped the values it prints, refused anchors and aliases, confined the build job's upload "
    "to its own step, and fixed the workflow's concurrency group.\n"
    "  - Round 12 (2026-11-25 01:16:47Z to 01:58Z): **0/0/3/7**, the first complete round with no BLOCKER or MAJOR, which cleared the ports; its M12-C, a row "
    "a terminal's soft wrap could show as a PASS (at widths 80, 100 and 200), was a close call that the reviewer and the orchestrator both rated MINOR.\n"
    "  - Fix pass 11 (02:03:56Z to 03:20:19Z) fixed its MINORs and NITs without another round, as the stopping rule allows, and recorded two NITs (n12-c, n12-f) "
    "as residuals: `a452db3d…` (1923 lines) is the checker every port was checked with.\n"
    "  - The checker compares parsed YAML, so comments drop out (the residuals, below). How to run it: " + _RECORD + " § \"Fix pass 11\", \"How to run the checker on a port\".\n"
)

_N_PORTS = (
    "- **The ports, 2026-11-26**: one signed-commit PR per repository, each built by a task-executor from " + _PORT_BRIEF + " and reviewed cold by a fresh agent "
    "(" + _PORT_REVIEW_BRIEF + "). Fix-ups came from the same executor. Before each merge the orchestrator re-ran the checker on the PR's head as GitHub held it "
    "and applied that port's reviewed pin. No review found a BLOCKER; the one MAJOR, data-client's F1, was fixed before its merge.\n"
    "  - juniper-cascor-client#206 (03:13:03Z; `beb6b349`; head `2a1f2a27`), 0/0/1/6: its MINOR, a CHANGELOG sentence carried from cascor that is false here, "
    "fixed with four of the six NITs (one in the writer alone).\n"
    "  - juniper-data-client#274 (04:15:39Z; `4b78d540`; `a93f10d6`), 0/1/3/1. Its MAJOR, F1: its `docs/REFERENCE.md` sent every failed `Verify PyPI serves exactly these files` "
    "to a new patch version, where a timeout is index lag (\"Re-run failed jobs\") and only a mismatch needs one. Fixed.\n"
    "  - juniper-cascor-worker#238 (04:26:48Z; `f9122a8a`; `5b7340f0`), 0/0/1/2; juniper-canopy#844 (05:14:24Z; `aa9ac734`; `704896b4`), 0/0/2/3, after two fix-ups; "
    "and juniper-data#553 (05:24:33Z; `a0bb1558`; `9cf7158d`), 0/0/1/5.\n"
    "  - juniper-recurrence#241, its three publishers (06:12:43Z; `8a5a062e`; `57559a28`), 0/0/2/3, its F1 rated MINOR by its reviewer, who added \"Raise it to MAJOR if you read the guide strictly\". "
    "It also restores line 22 of each, `#        owner       = pcalnon`: PyPI's technical owner field, which the rename (#237) had rewritten, "
    "as the technical-owner sweep (juniper-ml#2632, 2026-11-24 13:20:45Z, `c93914a7`) found.\n"
    "  - juniper-ml#2673, its seven publishers (13:08:46Z; `e2e463ea`; `1730127c`), 0/0/3/5; its review found R4-1 and R5-F5 met. Its branch was synced and auto-merge "
    "armed outside the session (11:42:13Z and 11:42:15Z, the Overtoad's account). `util/safe_merge.py`'s first run refused at 12:52:36Z (`main` went BEHIND three times "
    "while CI ran) and disarmed its net; the retry merged it.\n"
    "  - juniper-cascor-client#207 (11:27:26Z; `7e1399d8`; `faaf6538`), a docs follow-up that the reviews of #238 and #274 pointed at, read by the orchestrator with no "
    "independent review: a `Verify PyPI serves exactly these files` that gave up waiting is index lag, so \"Re-run failed jobs\", and only a mismatch needs a new patch version.\n"
    "  - Each port's squash kept its `Allow-Symbol-Loss:` lines; #207 needed none. The ports' writers land with v1.15.18: `util/ad-hoc/2026-11-26_<repo>_one_artifact_sweep_port.py` "
    "(seven) and `2026-11-26_juniper-cascor-client_pypi_check_two_causes.py`.\n"
    "- **The pins**: each port's review moved its own pins (R4-5's `find_spec` in cascor-client, cascor-worker, data, data-client and juniper-ml's ci-tools and observability; "
    "the install steps' comments; a neutral print before the verdict), and the file became `faa198c2…`, all 18 pins reviewed final scripts.\n"
    "- **Done**: after 13:08:47Z on 2026-11-26 the checker `a452db3d…` with those pins passed every publisher on every `main` (cascor `5e3d9801`, canopy `374c0fb9`, "
    "data `a0bb1558`, data-client `51e34f71`, cascor-client `7e1399d8`, cascor-worker `f9122a8a`, recurrence `8a5a062e`, juniper-ml `e2e463ea`): \"18 of 18 pass\", "
    "every repository exit 0.\n"
    "  - Re-run by this record's session between 21:40:08Z and 21:40:38Z, with juniper-ml `main` at `557490fb`: \"18 of 18 pass\"; and again from the landed copy, "
    "`util/ad-hoc/2026-11-26_publish_port_verify_all_mains.bash`, by this record's landing check.\n"
)

_N_RULINGS = (
    "- **The Overtoad's rulings of the ports** (session `3792e0cc`, and two to this record's session):\n"
    "  - \"Merge ports\" (answered by 01:47:14Z): **\"Approve all 7 (Recommended)\"**: \"I merge each of the 7 port PRs when it meets all three conditions, "
    "and also this arc's juniper-ml docs PRs (handoffs, and the plan v1.15.18 record that lands the sweep's scripts). I stop and ask about anything that falls outside those conditions.\" "
    "Not chosen: \"Ports only\", \"Ask per PR\" and \"You merge\".\n"
    "    - The three conditions, from its question: CI green, no BLOCKER or MAJOR left open in the PR's independent review, and the checker passing the PR's fetched head "
    "with that port's reviewed install pin.\n"
    "  - \"Merge #207\" (asked after 06:13:35Z, answered by 11:27:00Z): **\"Yes, merge it (Recommended)\"**: \"I merge juniper-cascor-client#207 with util/safe_merge.py "
    "once its required checks are green, and record it with the ports.\" Not chosen: \"Leave it for me\" and \"Close it\".\n"
    "  - At 11:26:35Z (that session's transcript), in the Overtoad's own words: \"merge approval granted for this work arc\".\n"
    "  - To this record's session (`d769e173`), at 21:40:06Z and 21:40:15Z (its transcript): \"merge approval granted\" and \"merge approval granted for this work arc\".\n"
)

_N_RESIDUALS = (
    "- **Residuals, open** (fix pass 11's \"What this cannot see\", earlier passes' and the ports' reviews):\n"
    "  - the publish action's container image is named by a registry tag that can be re-pushed, so the SHA pin does not bind the code that handles the token (M11-E);\n"
    "  - the build job's steps before the build are unpinned, and can reach the files the build records by means no text rule sees; only pinning them, "
    "as the install scripts are, closes that (M11-C, R11-1, M12-B). This and the image tag (M11-E, above) are the Overtoad's to decide (§6, mid-wave sitting);\n"
    "  - another workflow of a repository can name a publisher's concurrency group or cancel its run (availability only; M11-D), and two publishers' groups "
    "can coincide for refs a writer crafts (n12-b);\n"
    "  - a terminal that wraps a line inside a value can show a row that begins like a PASS line within a FAIL message; the exit status and the last line, "
    "the summary, stay true (fix pass 11);\n"
    "  - a link among a path's directories (`.github` or `workflows`) is followed, though git holds a link there; equality is all the pins prove; GitHub's "
    "server-side parser was not run; `timeout-minutes` values are not read (n12-f); and a repeated step id passes, though GitHub refuses the file (n12-c);\n"
    "  - from round 3, carried by fix pass 3 and closed by no later pass: in recurrence's client and model install checks, which install runtime dependencies by name "
    "after the TestPyPI install (F3), a later install can pull another version of the target;\n"
    "  - comments: since the checker compares parsed YAML, template comments outside `run:` scripts are guarded only by each repository's digest pins where they exist "
    "(cascor-client, data-client, cascor-worker and juniper-ml, normalized; juniper-data, raw and parsed). canopy and recurrence pin none (#844's M2, #241's F2), "
    "and an edit made alike in recurrence's three copies passes its suite;\n"
    "  - wording, for a later pin round over all the ports together: the pinned `find_spec` comments say \"installs and imports\" where the check imports nothing "
    "(#238's N-1, #553's R-4), and the sub-package banner comments say the check runs the package (cascor's text);\n"
    "  - labels that resolve only with this record and the landed checker: \"R4-5\" (" + _RECORD + " § \"Round-4 review\") and \"SWEEP item 23\" (`SW/sweep_items.md`) "
    "in the ports' tests and CHANGELOGs (#238's N-2), and canopy's test comments citing the checker's path (#844's N2);\n"
    "  - juniper-data's spelled-out try counts (\"five\") are unpinned (#553's R-5), and juniper-ml `ci.yml`'s actionlint with shellcheck and pyflakes does not finish, "
    "on `main` too (#2673's review).\n"
)

_N_SWEEP = (
    "- **SWEEP items 28 and 29** (round 1's M5 and N6, deferred to a template change):\n"
    "  - 28: the install check tests the version the tag names, and no publish job ties the version in `SHA256SUMS` to the release tag; juniper-ml's "
    "`Assert release tag matches built version` step is the model. Round 10 gave it a concrete path (R10-7): an extra job could leave a 0.14.1 artifact that "
    "\"Re-run failed jobs\" then publishes from a v0.14.0 run with no install check. Fix pass 9's N10-6 found a second, through an allow-listed job's called file "
    "and \"Re-run all jobs\".\n"
    "    - The checker now refuses every extra job but juniper-data's `notify-consumers`, whose called file it pins by sha256, which closes both paths for the checker; "
    "the template's own tie of the version to the tag is still to make.\n"
    "  - 29: the republish job's gate runs after the `pypi` approval, so the approver approves blind; a check job before the gate would close it.\n"
)

_N_FIRST = (
    "- **The first Release since the one-artifact publish** is juniper-observability-v0.4.3 (another lane's: " + _REMAINING + " § \"Checked and changed, 2026-11-26\"). "
    "Its GitHub Release was published at 02:04:23Z on 2026-11-26, before juniper-ml's port merged, so its run (45739959764) runs the unswept publisher, with no install job: "
    "no Release has yet run a swept one.\n"
    "  - At 21:55:36Z its `Build and Validate` and `Publish to TestPyPI` had succeeded and `Publish to PyPI` waited at the `pypi` gate, the Overtoad's. "
    "TestPyPI serves the wheel `4817790d…` and the sdist `14c6c7db…`, and PyPI has no 0.4.3. The gate's day 30, its last day to approve or re-run, is 2026-12-26, "
    "and GitHub cancels the run on day 35, 2026-12-31.\n"
    "  - Once the gate is approved, the workflow's own steps check the files against TestPyPI's sha256 before the PyPI upload and against PyPI's after it, "
    "and a session can re-read both indexes; no session holds that check (that document's §4, gap 16).\n"
)

_N_GROUP_E = (
    "- **The entries " + _REMAINING + " (ml#2619) lists as done or superseded** (its group E, R58 to R65, and §4's gaps 1 to 9, 11, 16 and 17), each re-read on 2026-11-26:\n"
    "  - R58 and gap 1: \"Symlinks\" was answered \"Rebuild as one signed commit (Recommended)\" (" + _RENAME_HO + "), and juniper-cascor#772 merged at 19:35:14Z on 2026-11-23 "
    "as `e9c86f83`, from the rebuilt head `31136d64`; fix pass 3 accounted for the difference (above).\n"
    "  - R59: juniper-deploy#284 (20:55:09Z, `7e996845`) pins juniper-recurrence 0.8.1, on the Overtoad's \"Move it now (Recommended)\". 0.8.1's `requirements.lock` "
    "and `Dockerfile` equal 0.8.0's, so its image still holds observability 0.4.1 and service-core 0.7.1, and `--fail-on-stale` went from exit 1 to exit 0 (" + _SEVEN + ").\n"
    "  - R60: on the Overtoad's \"Six finished worktrees, data worktree + 4 branches\", session [9660dc] removed six worktrees, the never-opened juniper-data worktree "
    "and four merged branches of the cascor and canopy primaries, at 20:45:52Z, their `tmp/` moved first to `juniper-ml/tmp/worktree-archive-2026-11-23/` (946 MB).\n"
    "    - That archive holds the files this plan cites in those worktrees, each in its worktree's `tmp/` there (R18's precondition): `humble-humming-flask`'s "
    "`tmp/review-763/` and `tmp/cascor-767/safe_merge_767.log`, `buzzing-growing-whale`'s `tmp/s2/parent_AGENTS_before_2026-11-14.md`, and the two copies "
    "`reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/README.md` names. Three of the five are substituted (re-read 2026-11-26 23:31:39Z to 23:32:35Z):\n"
    "      - the parent copy (`d8ab5749…`; the restored `90df2783…` is in `juniper-ml/tmp/2026-11-14-parent-agents-md-backup/`), `logical-percolating-sparkle`'s "
    "`tmp/lps/fixpass_r1.md` (`76bc0754…`; the verbatim `ad8d9091…` is in the repository as `five-prs-validation-fixpass-round-1.md`) and 44 of `tmp/review-763/`'s "
    "89 files; `toasty-prancing-karp`'s `tmp/s1/guard_review_round1.md` keeps its pinned `37508e48…`, and the merge log holds no \"Overtoad\".\n"
    "  - R61, R64 and gap 3: the rename's substitution had rewritten the parent `AGENTS.md` backups on disk. All nine are back at their recorded sha256 "
    "(`90df2783`, `f3f69b34` and `3009c3f4` by `util/ad-hoc/2026-11-23_restore_parent_agents_backups.py`, the six older by `…_older.py`), each rewritten copy kept beside it "
    "as `*.substituted-2026-11-20`. Re-read at 21:54:57Z; the live parent is `3009c3f4`.\n"
    "  - R62: the rename census moved on. cascor#772 (19:35:14Z), harcot#28 (20:39:13Z), data#547 (20:39:16Z) and canopy#830 (21:05:44Z) merged on 2026-11-23, "
    "and ml#2606 on 2026-11-24 (05:06:27Z, `5a049144`); ml#2605 closed unmerged (2026-11-23 20:54:14Z).\n"
    "  - R63 and gaps 2 and 9: the Overtoad put the juniper-ml primary back on `main` on 2026-11-24 (21:22:29Z; R23). Its reflog shows it on `pcalnon-patch-1-1` "
    "three times since (2026-11-25 19:28:27Z to 20:09:10Z and 20:21:13Z to 2026-11-26 01:16:14Z, and 10:40:08Z to 11:31:37Z), and at 21:54:57Z on 2026-11-26 it is "
    "on `main` at `557490fb`, whose observability is 0.4.3's code.\n"
    "    - Since R21 (2026-11-24 22:30Z) `JuniperData` and `JuniperCanopy1` hold observability 0.4.2 and service-core 0.7.2, read in place at 21:55:36Z; "
    "R21's second pass, to 0.4.3, and R22's probe follow 0.4.3 on PyPI. `JuniperCascor1`'s editable installs still report 0.4.1 and 0.7.1 to pip.\n"
    "  - R65 and gap 11: no canopy E2E leg listened at 21:54:57Z on 2026-11-26, and no Juniper container existed at 22:49:02Z (`docker ps -a`), "
    "so the juniper-deploy stack's restart is a bring-up (R25); the four places that said restart are marked.\n"
    "  - Gap 7, the three findings " + _SEVEN + " sent here:\n"
    "    - the rename's blind substitution also rewrote untracked and ignored files in every juniper-ml worktree that existed on 2026-11-20 to 2026-11-22 (files under `tmp/` "
    "holding \"Overtoad\": 59,976 in `giggly-foraging-sunbeam`, 1,869 in `agent-a54a0a279acc3a863`, 161 in `humble-humming-flask` and 24 in `sparkling-percolating-meadow`). "
    "So `tmp/` evidence older than 2026-11-20, the 2026-11-23 archive's included, reads as possibly substituted; `gh`, git and the transcripts are intact.\n"
    "    - sentry-sdk 3.0.0 (PyPI 2026-11-23 09:30Z) removed `send_default_pii`, so `configure_sentry` with a DSN raises `TypeError` on a fresh install of observability "
    "0.4.2, whose `sentry` extra floors `sentry-sdk[fastapi]>=2.35.0` with no cap. ml#2608 capped it `<3` on `main`, never released (2026-11-23 20:50:42Z, `b2aa9026`), and 0.4.3, the 3.x port "
    "(ml#2647), takes both majors (`>=2.35.0,<4`), at its `pypi` gate.\n"
    "    - juniper-ml registered 447 worktrees after that cleanup, and 478 at 22:44:33Z on 2026-11-26; no task holds them (" + _REMAINING + "'s gap 17).\n"
    "  - Gap 4 is R17's (`tmp/retry-after-guard-ssq1mano` is still there); gap 5 was resolved on 2026-11-24 (0.4.3 is the sentry-sdk 3.x release, and R-OBS-SC-3 "
    "moves to 0.4.4; the passages that said otherwise are marked); gap 6 is R57, done; gap 8's overlap ended when ml#2606 merged; and gap 16 is under the first Release, above.\n"
    "    - The answer that moved R-OBS-SC-3 to 0.4.4 also ruled R15: the consumers port to sentry-sdk 3.x once 0.4.3 is on PyPI. On 2026-11-26 the Overtoad ruled that "
    "cascor's port waits for profiling arguments in a later observability release; SemVer counts them a minor while R-OBS-SC-3 is ruled 0.4.4, so that release's number "
    "is the Overtoad's (" + _REMAINING + " § \"Checked and changed, 2026-11-26\").\n"
    "  - The unattributed write under `/tmp` that session `ffffd3` left as evidence (`/tmp/vFI4WZy/`, created 2026-11-24 00:28:39Z: two byte-identical copies of "  # tmp-path-literal: allow
    "juniper-ml's `.gitignore`, named `4.1.1` and `5.1.1`; `SW/plan_v1_15_18_inputs.md`) was gone at 22:51:36Z on 2026-11-26, with no reboot since 2026-11-17. "
    "Who wrote it and who removed it are unknown.\n"
)

_N_NEXT = (
    "- **What remains**:\n"
    "  - SWEEP items 28 and 29: each a change to the template through cascor and then every port, and each also a change to the checker (it fixes the build window "
    "and the chain's five jobs), which its FINAL note makes a new pass (" + _RECORD + " § \"Fix pass 11\"); and the residuals' wording, for a later pin round: "
    "the template's comments and the pins file, as each port's review moved its pins, not the checker. No session holds them.\n"
    "  - once the Overtoad approves juniper-observability 0.4.3's `pypi` gate (by 2026-12-26), a re-read that PyPI serves TestPyPI's files (gap 16, above); "
    "and the same check of the first Release through a swept publisher, whose install job and republish gate no Release has run. No session holds either;\n"
    "  - with the Overtoad: the items in §6's mid-wave sitting (\"Left with the Overtoad by the template sweep\" and the earlier trusted-publisher check);\n"
    "  - the arc's two worktrees: `ethereal-munching-peacock` and `moonlit-percolating-sun` may go only once all of their `tmp/` is archived (R41), which is not done.\n"
    "    - Archived: `SW/` (the record, the briefs, rounds 6 to 12's reports, the seven ports' reviews and the executor reports) and, in " + _PROOF_ARCHIVE + ", "
    "each of the ten fix-pass directories' top-level files and `evidence/` (`ethereal-munching-peacock/tmp/sweep/cascor-r3`, `cascor-r4` and `checker-r5` to `checker-r12`).\n"
    "    - Not archived, in `ethereal-munching-peacock`: the review rounds' own directories (`tmp/r2review` to `tmp/r12review` and the two lenses', rounds 1, 2, 4 "
    "and 5's reports among them), `tmp/sweep/land/` (#777's landing evidence), `tmp/sweep/cascor`, `cascor-r2` and `cascor-r3-prep`, `tmp/arc/`, and the trees "
    "inside the fix-pass directories;\n"
    "      - and `tmp/ports/` (#777's \"3 of 18 pass\" log, `verify_all_mains_v2.after777.log`, among its done-check runs), `tmp/audit-handoff-r1/`, `tmp/audit-handoff-r2/`, "
    "`tmp/factcheck-2610/`, `tmp/r3val_tree.txt` and the record's 37 `REVIEW_DISPOSITIONS.before-*.md` backups.\n"
    "    - Not archived, in `moonlit-percolating-sun`: all of `tmp/` but what `SW/` copies (its clones, scratch, status notes, merge logs and done-check outputs).\n"
)

_NOTE_ANCHOR = "\n**R-DC-PATCH's branch.** "
_NOTE_NEW = (
    "\n" + _N_HEAD + _N_ROUNDS + _N_777 + _N_CHECKER + _N_PORTS + _N_RULINGS + _N_RESIDUALS + _N_SWEEP + _N_FIRST + _N_GROUP_E + _N_NEXT
    + "\n**R-DC-PATCH's branch.** "
)

# --- Validation record and "Changed by this plan" ----------------------------------------------------------------------
_VALIDATION_ANCHOR = (
    "    - A second independent fact-check, of ml#2610's text, found 1 MAJOR (the rename census missed juniper-recurrence#237 and juniper-deploy#281), 3 MINORs and 2 NITs, "
    "and the sweep's workflow review settled `filter=latest`. Each was re-checked at its source and applied in ml#2610's second commit.\n"
)
_VALIDATION_NEW = (
    _VALIDATION_ANCHOR
    + "  - v1.15.18 is a record of the template sweep and its ports (2026-11-23 to 2026-11-26). No round checks it (Overtoad ruling 2026-10-24). Its rulings are quoted "
    "from the arc's record (" + _RECORD + "), where each session wrote them as its dialog returned them, not re-dated from the transcripts as v1.15.17's were, "
    "but for the three messages it dates from the transcripts' first timestamped entries (11:26:35Z in `3792e0cc`; 21:40:06Z and 21:40:15Z in `d769e173`).\n"
    "    - Its facts were re-read on 2026-11-26: from `gh`, every PR's state, merge time, merge and head commits; from PyPI's and TestPyPI's JSON, juniper-observability 0.4.2 "
    "and 0.4.3; on the host, the primary's HEAD and reflog, the parent backups' sha256, the containers, the listening ports (21:54:57Z to 22:51:36Z) and the trio's "
    "environments (21:55:36Z); and the checker on every `main` (\"18 of 18 pass\").\n"
    "    - Two independent Opus agents of this record's session read its first draft (launched after 22:08:05Z): a fact re-probe (0 BLOCKER, 3 MAJOR, 11 MINOR, 10 NIT) "
    "and a completeness and consequence attack (1 BLOCKER, 8 MAJOR, 18 MINOR, 11 NIT), overlapping on about a dozen items.\n"
    "      - The BLOCKER: the plan still gave juniper-observability 0.4.3 to R-OBS-SC-3 in eleven passages. The MAJORs: the proof archive overstated, "
    "the three findings `…seven-worktrees-archived.md` sends here and the system temp-directory write `plan_v1_15_18_inputs.md` records, R45 to R52, two decisions the record leaves to the Overtoad, SWEEP item 28's second path, gap 16's "
    "owner, and what the 2026-11-23 archive backs.\n"
    "      - Each was re-checked at its source and applied in the writer; none is declined. Both are archived, briefs, findings and fixes, in `SW/`.\n"
    "    - A third independent Opus agent read the corrections, draft 2 (round 2, launched after 22:56:11Z): 0 BLOCKER, 1 MAJOR, 8 MINOR and 14 NIT, and seven round-1 findings "
    "applied wrongly and one part missed. The MAJOR: the archived parent copy in `buzzing-growing-whale` is the substituted text, not the restored backup, as round 1's A09 "
    "had read that archive's README.\n"
    "      - Each was re-checked at its source and applied; none is declined. It is archived, brief, findings and fixes, in `SW/`.\n"
    "    - Gates on the final files: the CodeQL prescreen predicts 0 alerts in the 17 new `.py` files; flake8 reports 0 for B914 and for F and E9; shellcheck is clean; "
    "the tmp- and home-path literal gates pass on the named files; `pre-commit run --files` exits 0 on every changed file outside `reports/`, which the hooks exclude; "
    "the doc-link check passes as CI runs it; and the markdown-structure screen counts 0 problems in the plan before and after.\n"
)

_SCRIPTS_ANCHOR = "`2026-11-15_fetch_pr_files.py` and `2026-11-15_build_gate_payload.py`.\n"
_SCRIPTS_NEW = (
    _SCRIPTS_ANCHOR
    + "    - and with v1.15.18's, `2026-11-26_consolidated_plan_v1_15_18_template_sweep.py` (the writer) and `2026-11-26_archive_one_artifact_sweep_reviews.py` "
    "(the review archive, below), and the template sweep's scripts, uncommitted until then:\n"
    "      - its seven, byte for byte as `tmp/arc/sweep_scripts.sha256` in `ethereal-munching-peacock` lists them: cascor's writer `2026-11-23_cascor_one_artifact_sweep_edits.py`; "
    "the checker `2026-11-23_publish_port_template_identity.py` and its pins `2026-11-24_publish_port_install_pins.json`; `2026-11-23_publish_one_artifact_test_lens_mutations.py` "
    "and `…_test_lens_proposed_fixes.py`; and `2026-11-23_publish_sweep_r2_review_probes.py` and `…_r4_review_probes.py`;\n"
    "      - the eight port writers of 2026-11-26, `<repo>_one_artifact_sweep_port.py` (canopy, cascor-client, cascor-worker, data, data-client, juniper-ml and recurrence) "
    "and `juniper-cascor-client_pypi_check_two_causes.py`, byte for byte but juniper-ml's, whose five unused tuple targets are renamed `_` for CodeQL. "
    "Run on `bceac63c`, the original and the renamed copy write the same 18 files, each equal to `main`'s at `e2e463ea`;\n"
    "      - three of session `3792e0cc`'s tools, promoted with headers and made to run from any juniper-ml checkout (paths from the script's own place, a `PYTHON` override, "
    "a fresh output directory under the checkout's `tmp/`; the pin tool reads earlier pins from git history and no longer rewrites `ethereal-munching-peacock`'s manifest): "
    "`2026-11-26_publish_port_verify_all_mains.bash` (the done-check), `2026-11-26_publish_port_check_pr_head.bash` and `2026-11-26_publish_port_apply_install_pin.py`.\n"
)

_HANDOFFS_ANCHOR = (
    "  - the one-artifact publish's handoffs, each landed by its own PR (not this plan's): `…one-artifact-landed-ports-plan-v1-15-17-next.md` (ml#2591), "
    "`…8-prs-open-reviews-then-merge-plan-v1-15-17-next.md` (ml#2594) and `…sweep-ruled-brief-cascor-plan-v1-15-17-next.md` (ml#2603).\n"
)
_HANDOFFS_NEW = (
    _HANDOFFS_ANCHOR
    + "  - with v1.15.18's PR, the review archive `" + _ARCHIVE + "` (`SW/`): its `README.md`, the arc's record (`dispositions.md`), the briefs of rounds 4 to 12, "
    "of fix passes 3 to 11 and of the landing, the reports of rounds 6 to 12, the sweep's and the ports' briefs, the ports' reviews and executor reports, "
    "and this record's own validation, built by `util/ad-hoc/2026-11-26_archive_one_artifact_sweep_reviews.py`.\n"
    "  - the template sweep's handoffs, each landed by its own PR (not this plan's): `…land-after-cascor-772.md` (ml#2614), `…round-7-then-ports-plan-v1-15-18.md` (ml#2620), "
    "`…fix-pass-7-round-9-then-ports.md` (ml#2630), `…fix-pass-11-final-ports-next.md` (ml#2658) and `…18-of-18-plan-v1-15-18-next.md` (ml#2676).\n"
)

_OUTSIDE_ANCHOR = "- **Modified outside the repository**:\n"
_OUTSIDE_NEW = (
    "  - by session `11a98f94` (2026-11-23), unrecorded by v1.15.17, the auto-memory file `reference_blind_substitution_rewrites_untracked_files_in_sibling_worktrees.md` "
    "(a repo-wide substitution also rewrites untracked and `tmp/` files in sibling worktrees).\n"
    "  - by session `d935c226` (2026-11-24 01:34:13Z), the auto-memory file `reference_agents_md_date_check_crosses_midnight_utc.md` (`Verify AGENTS.md Last Updated` wants "
    "the UTC day at CI time), and at 01:34:15Z its line in `MEMORY.md`.\n"
    "  - by v1.15.18's session (2026-11-26): " + _PROOF_ARCHIVE + " (its `README.md` and `MANIFEST.sha256`, and under `ethereal-munching-peacock/tmp/sweep/` copies of "
    "the sweep's proof drivers and evidence), kept under the 2026-10-26 retention rule; its done-check re-run's output, `tmp/ports/verify-all-mains-v3/20261126T214015Z/` "
    "in `moonlit-percolating-sun`; and `tmp/v1_15_18/` in worktree `purring-hugging-hippo` (its probes, landing proofs and replay trees).\n"
    "    - and beside it there, the landed tools' outputs from the landing check: `tmp/publish-port-verify-all-mains/20261126T220941Z/`, "
    "`tmp/publish-port-check-pr-head/juniper-cascor-client-207/` and `tmp/publish-port-apply-install-pin/20261126T221123Z/`.\n"
    + _OUTSIDE_ANCHOR
)

#: Plan edits: (old, new). ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
PLAN_EDITS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.17\n", "- **Version**: 1.15.18\n"),
    (_V17_RELEASE_OLD, _V17_RELEASE_NEW),
    (_STATUS_ANCHOR, _STATUS_NEW),
    (_SHORT_OLD, _SHORT_NEW),
    (_FLOOD4_OLD, _FLOOD4_NEW),
    (_DOCS_ANCHOR, _DOCS_NEW),
    (_SUB_170_OLD, _SUB_170_NEW),
    (_SUB_173_OLD, _SUB_173_NEW),
    (_SUB_520_OLD, _SUB_520_NEW),
    (_SUB_528_OLD, _SUB_528_NEW),
    (_SUB_530_OLD, _SUB_530_NEW),
    (_SUB_677_OLD, _SUB_677_NEW),
    (_SUB_875_OLD, _SUB_875_NEW),
    (_SUB_879_OLD, _SUB_879_NEW),
    (_SUB_894_OLD, _SUB_894_NEW),
    (_SUB_1053_OLD, _SUB_1053_NEW),
    (_SUB_1078_OLD, _SUB_1078_NEW),
    (_SUB_1089_OLD, _SUB_1089_NEW),
    (_SUB_1138_OLD, _SUB_1138_NEW),
    (_SUB_1162_OLD, _SUB_1162_NEW),
    (_SUB_1153_OLD, _SUB_1153_NEW),
    (_SUB_1159_OLD, _SUB_1159_NEW),
    (_SUB_1161_OLD, _SUB_1161_NEW),
    (_SUB_1166_OLD, _SUB_1166_NEW),
    (_SUB_1189_OLD, _SUB_1189_NEW),
    (_SUB_1190_OLD, _SUB_1190_NEW),
    (_SUB_1172_OLD, _SUB_1172_NEW),
    (_SUB_1198_OLD, _SUB_1198_NEW),
    (_SUB_1240_OLD, _SUB_1240_NEW),
    (_SUB_1243_OLD, _SUB_1243_NEW),
    (_SUB_1246_OLD, _SUB_1246_NEW),
    (_SUB_1257_OLD, _SUB_1257_NEW),
    (_SUB_1281_OLD, _SUB_1281_NEW),
    (_NOTE_ANCHOR, _NOTE_NEW),
    (_SUB_1401_OLD, _SUB_1401_NEW),
    (_SUB_1403_OLD, _SUB_1403_NEW),
    (_SUB_1494_OLD, _SUB_1494_NEW),
    (_SUB_1498_OLD, _SUB_1498_NEW),
    (_SUB_1584_OLD, _SUB_1584_NEW),
    (_SUB_1602_OLD, _SUB_1602_NEW),
    (_SUB_1799_OLD, _SUB_1799_NEW),
    (_SUB_1885_OLD, _SUB_1885_NEW),
    (_VALIDATION_ANCHOR, _VALIDATION_NEW),
    (_SCRIPTS_ANCHOR, _SCRIPTS_NEW),
    (_HANDOFFS_ANCHOR, _HANDOFFS_NEW),
    (_SUB_2547_OLD, _SUB_2547_NEW),
    (_SUB_2550_OLD, _SUB_2550_NEW),
    (_SUB_2670_OLD, _SUB_2670_NEW),
    (_OUTSIDE_ANCHOR, _OUTSIDE_NEW),
]


def long_lines(text: str) -> list[tuple[int, int]]:
    return [(n, len(line)) for n, line in enumerate(text.split("\n"), 1) if len(line) > MAX_LINE]


def apply(text: str, edits: list[tuple[str, str]], check: bool) -> tuple[str, int, int]:
    """Apply each (old, new) edit; return the new text, the pending count and the refused count."""
    pending = refused = 0
    for old, new in edits:
        site = old.strip()[:72]
        if new in text and text.count(old) <= text.count(new):
            # ``new`` may contain ``old`` (an insertion after an anchor); applied means each old sits inside a new.
            print(f"  = plan: {site}... already applied")
            continue
        if text.count(old) != 1:
            print(f"  ! plan: {site}... REFUSED: found {text.count(old)} times, expected 1")
            refused += 1
            continue
        text = text.replace(old, new)
        pending += 1
        print(f"  ~ plan: {site}... {'pending' if check else 'applied now'}")
    return text, pending, refused


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tree", type=Path, default=_REPO, help="the juniper-ml checkout to edit (default: this script's own)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 while an edit is pending")
    args = ap.parse_args()

    plan_path = args.tree / PLAN
    plan0 = plan_path.read_text(encoding="utf-8")
    plan1, pending, refused = apply(plan0, PLAN_EDITS, args.check)

    before, after = long_lines(plan0), long_lines(plan1)
    grown = len(after) > len(before)
    if grown:
        new_long = [n for n, _ in after if n not in {m for m, _ in before}]
        print(f"  ! plan lines over {MAX_LINE} characters: {len(before)} before, {len(after)} after; lines now long: {new_long}")
    if refused or grown:
        print(f"REFUSED: {refused} anchor(s); {len(after) - len(before)} new long plan line(s); nothing written", file=sys.stderr)
        return 1
    print(f"  plan lines over {MAX_LINE} characters: {len(before)} before, {len(after)} after")
    if args.check:
        return 1 if pending else 0
    if pending:
        plan_path.write_text(plan1, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
