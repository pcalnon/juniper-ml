#!/usr/bin/env python3
"""Consolidated development plan v1.15.15 -> v1.15.16: R-OBS-SC-2's follow-ups, from 2026-11-09 to 2026-11-15.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: ml#2555 (the [tools] floors), cascor#755 and canopy#816 (telemetry), cascor#757, canopy#817 and data#537
         (Retry-After); ml#2558, ml#2561 and run 43408809021 (juniper-ml 0.11.5); ml#2576 (APD-ECO-016 and its guard);
         cascor#758 and canopy#818, runs 43663237489 and 43664277663 (the two cuts), archives ml#2570 and ml#2572;
         ml#2568 (QUICK_START, the cut tools, the 0.4.3 design's start prompt);
         reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/ (the reviews, this draft's two among them);
         util/ad-hoc/2026-11-15_r_obs_sc_2_followups_record_reprobe.py (the facts, re-probed) and
         util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py (the rulings, from the transcripts);
         util/ad-hoc/2026-11-09_consolidated_plan_v1_15_15_r_obs_sc_2_shipped.py (the pattern)

Why
---
v1.15.15 recorded R-OBS-SC-2 and left its follow-ups at §6's mid-wave sitting. Six sessions then carried them out
(a4e1e914, 6e3bdef0, 218ff61e, 7d425759, 1b4fec84 and b9dfa450, 2026-11-09 to 2026-11-15):

- the owner ruled four items on 2026-11-09 (round 1), seven on 2026-11-13 (round 2 and its re-ask), three on
  2026-11-14 and three on 2026-11-15, each dated from its transcript, and on 2026-11-15 directed that PyPI receive
  the files TestPyPI took;
- the telemetry opt-outs and the forks' Retry-After fixes merged (cascor#755, canopy#816, cascor#757, canopy#817,
  data#537), juniper-ml 0.11.5 floored [tools] on R-OBS-SC-2 and was published, and APD-ECO-016 was filed FIXED with
  an ENFORCED guard (ml#2576);
- juniper-cascor 0.14.0 and juniper-canopy 0.10.0 were cut and, once the owner approved both pypi gates, published
  (2026-11-15); juniper-deploy#278 pinned both images, and the parent Juniper/AGENTS.md was edited for them.

This revision records that, the findings the arc left open (each with its source and next actor), what stays with
the owner, and makes current every passage v1.15.15 left that this record makes stale. Two independent reviews of
the first draft (a fact-check and an adversarial read, session b9dfa450) are applied, each finding re-checked at its
source. The v2 draft is not edited: it says v1 takes the record, and its stale lines are listed here.

Usage
-----
    python3 util/ad-hoc/2026-11-15_consolidated_plan_v1_15_16_r_obs_sc_2_followups.py [--root DIR] [--check]

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

_FNOTE = "§5, the note on R-OBS-SC-2's follow-ups"
_PROMPT = "`prompts/generated/JUNIPER_ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md`"
_REVIEWS = "`reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/`"
_BACKUP = "`juniper-ml/tmp/2026-11-14-parent-agents-md-backup/AGENTS.md.before-2026-11-14-edit`"
# Short forms, defined in "Documents referenced" by this revision.
_HO_RULED = "`…four-ruled-four-open.md`"
_HO_1113 = "`…0-11-5-at-pypi-gate-guard-cuts-plan-next.md`"
_HO_1115 = "`…guard-pr-plan-v1-15-16-next.md`"
_FLOOD4 = "`…CURSOR-FLOOD-4-DISPOSITION.md`"
_FLOOD4_HO = "`…flood4-record-merged-fixes-corrected-landing-next.md`"
#: A re-probe run that read both `pypi` gates open and juniper-deploy pinned (see the Validation record's text).
_GATE_READ = "06:04Z"
_PARENT_TOOL = "`util/ad-hoc/2026-11-15_parent_agents_released_paragraph_cascor_0_14_0_canopy_0_10_0.py`"
_BACKUP2 = "`juniper-ml/tmp/2026-11-15-parent-agents-md-backup/`"
#: The owner's words of 2026-11-15 05:14:10Z (session b9dfa450), quoted verbatim: the second paragraph of that message.
_DIRECTIVE = (
    "\"this needs to be fixed. deploy to pypi should send the same artifact that was already sent to testpypi. "
    "an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to prevent this from slipping through the cracks again.\""
)

# --- Header -------------------------------------------------------------------------------------------------------
_DATE_OLD = "R-OBS-SC-2's cut, publish, second lock round and the trio's environments probed 2026-11-09)\n"
_DATE_NEW = (
    "R-OBS-SC-2's cut, publish, second lock round and the trio's environments probed 2026-11-09; "
    "R-OBS-SC-2's follow-ups, juniper-ml 0.11.5's publish, `APD-ECO-016`, the juniper-cascor 0.14.0 and juniper-canopy 0.10.0 cuts and publishes, juniper-deploy's pins and the parent `AGENTS.md` edit probed 2026-11-15)\n"
)

_STATUS_ANCHOR = "  - Planning only: this plan changes no code,"
_STATUS_NEW = (
    "  - v1.15.16 (2026-11-15) records R-OBS-SC-2's follow-ups (" + _FNOTE + "). The owner ruled on 2026-11-09, 2026-11-13, 2026-11-14 and 2026-11-15; "
    "rulings 6 and 7 of 2026-11-13 change the trio's restart gate and extend O13 to the juniper-ml primary. "
    "juniper-ml 0.11.5 floors `[tools]` on R-OBS-SC-2 (R-ML-TOOLS-2, published 2026-11-14). Like v1.15.0, no round checks it.\n"
    "    - The three services that keep their own copies of service-core's security code (data, cascor and canopy, \"the forks\") gained FastAPI's telemetry opt-out and a `Retry-After` that rounds up "
    "(cascor#755, canopy#816, cascor#757, canopy#817, data#537). `APD-ECO-016`, the register's row for the old truncation, is filed FIXED, with a fork-drift guard ENFORCED (ml#2576).\n"
    "    - Those fixes are on `main`, in cascor 0.14.0 and canopy 0.10.0 (both cut on 2026-11-15 and published the same day, at 05:24Z and 05:17Z, when the owner approved their `pypi` gates), "
    "and in no data release before 0.18.0. juniper-deploy pins both images since deploy#278 (05:48:57Z); restarting the juniper-deploy stack is the owner's.\n"
    "    - On 2026-11-15 the owner directed that PyPI receive the very files TestPyPI took, checked by hash, and ruled that the fix go to juniper-cascor first and then to every other publish workflow "
    "(ruling 2 of 2026-11-15); the fix is a session's work in progress. The parent `Juniper/AGENTS.md` was edited for the two releases (ruling 3 of 2026-11-15).\n"
    "    - v1.15.16 also records the findings the arc left open and what stays with the owner (Overview; §2; XC-SENTRY; XC-P12; §4; §5; §6; §7; §8; §9; §12; Appendix A).\n"
    "    - A draft v2, `notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md` (ml#2550, not validated), proposes to replace §2, §4 and §6; "
    "this plan stays the record until the owner rules (v2's §6.4 item 20). The v2 lines this record makes stale are listed in " + _FNOTE + ".\n"
    "  - Planning only: this plan changes no code,"
)

# --- Documents referenced -------------------------------------------------------------------------------------------
_DOCS_ANCHOR = "| `…ci-tools-0-9-1-at-pypi-gate.md` | `HO/HANDOFF_2026-10-10_flood3-followups-released-ci-tools-0-9-1-at-pypi-gate.md` (the flood-3 follow-ups' handoff) |\n"
_DOCS_NEW = (
    _DOCS_ANCHOR
    + "| `…CURSOR-FLOOD-4-DISPOSITION.md` | `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` (the owner's record of the fourth Cursor flood, \"flood-4\"; its §8 lists rulings 1–14) |\n"
    "| `…flood4-record-merged-fixes-corrected-landing-next.md` | `HO/HANDOFF_2026-11-09_flood4-record-merged-fixes-corrected-landing-next.md` (flood-4's handoff; its item 3 lists the four fixes of flood-4's ruling 17) |\n"
    "| `…four-ruled-four-open.md` | `HO/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md` (R-OBS-SC-2's follow-ups: round 1's rulings and round 2's questions, verbatim) |\n"
    "| `…five-prs-validated-opening-next.md` | `HO/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-five-prs-validated-opening-next.md` (the five PRs of 2026-11-13) |\n"
    "| `…0-11-5-at-pypi-gate-guard-cuts-plan-next.md` | `HO/HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md` (the rulings of 2026-11-13, with its \"Update, 2026-11-14\") |\n"
    "| `…guard-pr-plan-v1-15-16-next.md` | `HO/HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md` (the two cuts of 2026-11-15) |\n"
)

# --- Overview -------------------------------------------------------------------------------------------------------
_OV_CUT_OLD = "and no consumer has cut a release from the new locks."
#: Overview 2's exposure line sits at 407 characters, so the releases and the pin it names fit in 105 more.
_OV_CUT_NEW = "and only cascor and canopy have one (0.14.0 and 0.10.0, 2026-11-15), pinned by deploy#278; its stack's restart is the owner's (v1.15.16)."

_OV_TOOLS_OLD = "since 2026-11-09 (v1.15.15); the data fix-forward is still owed"
_OV_TOOLS_NEW = "since 2026-11-09 (v1.15.15), and juniper-ml 0.11.5's `[tools]` floors both since 2026-11-14 (v1.15.16); the data fix-forward is still owed"

# --- §2 ------------------------------------------------------------------------------------------------------------
#: §2's P2 row sits at exactly 512 characters, so the replacement is no longer than what it replaces.
_P2_OLD = "| P2 canopy | The replay player is fixed on `main`, unreleased (74 commits past v0.8.1, 10-10)."
_P2_NEW = "| P2 canopy | The replay fix shipped in canopy 0.9.0 (10-17) and 0.10.0 (11-15)."

_P3_OLD = "Three S rows are unfiled. | S0.4; P3-01 | T0 |"
_P3_NEW = "Three S rows are unfiled. APD-ECO-016 filed FIXED 11-15 (ml#2576); data's fix waits for 0.18.0. | S0.4; P3-01 | T0 |"

#: §2's P4 row sits at 506 characters, so dates the §5 rows carry make room for the releases since.
_P4_OLD = (
    "The five then at the `pypi` gate are served (re-probed 2026-10-25): model 0.4.0, data-client 0.6.0, ci-tools 0.9.1, data 0.17.1 (10-23) and cascor 0.12.0 (10-25). "
    "P12 added canopy 0.9.0, recurrence 0.6.0–0.8.1, model 0.5.0–0.6.0, juniper-ml 0.11.0–0.11.4 (10-21 to 11-07) and recurrence-client 0.3.1 (10-27). "
    "R-OBS-SC-2 shipped 11-09; R-DATA-2 is owed."
)
_P4_NEW = (
    "All five then gated were served by 10-25: model 0.4.0, data-client 0.6.0, ci-tools 0.9.1, data 0.17.1, cascor 0.12.0. "
    "P12 added canopy 0.9.0, recurrence 0.6.0–0.8.1, model 0.5.0–0.6.0, juniper-ml 0.11.0–0.11.4, recurrence-client 0.3.1. "
    "Then cascor 0.13.0, R-OBS-SC-2 (11-09), juniper-ml 0.11.5, cascor 0.14.0 and canopy 0.10.0 (11-15). R-DATA-2 is owed."
)

_P12_OLD = "juniper-ml 0.11.0–0.11.4 carry the floors"
_P12_NEW = "juniper-ml 0.11.0–0.11.5 carry the floors"

# --- XC-SENTRY -------------------------------------------------------------------------------------------------------
_PASS_OLD = "the session's recorded test pass, then the owner's restart (§4 Wave 1, Security step 5;"
_PASS_NEW = "the session's recorded pass (since ruling 6 of 2026-11-13, the second lock round's per-lock probe, re-run per environment), then the owner's restart on P3-05 with blank DSNs (§4 Wave 1, Security step 5;"

_ENVS_OLD = "while `JuniperCascor1` imports 0.4.2's and 0.7.2's code from the juniper-ml primary (§4 Wave 1, Security step 5).\n"
_ENVS_NEW = (
    "while `JuniperCascor1` imports the juniper-ml primary's code (§4 Wave 1, Security step 5). "
    "On 2026-11-15 that is `eeb5c694` on `main`: observability 0.4.2's code, and service-core 0.7.2's plus ml#2531, #2534, #2547 and #2557, bound for 0.8.0, while pip reports 0.4.1 and 0.7.1 (v1.15.16).\n"
)

_PROBE_OLD = "- Whether the per-lock probe may stand in for S0.11's relay run at the restart is the owner's (§6, mid-wave sitting).\n"
_PROBE_NEW = (
    "- Whether the per-lock probe may stand in for S0.11's relay run at the restart was the owner's: **ruled 2026-11-13** (\"Probe per environment\", ruling 6 of 2026-11-13). "
    "After the owner's upgrade a session re-runs the probe in each environment and records it, and the restart proceeds on that record, on P3-05 and with blank DSNs (v1.15.16).\n"
    "  - That settles (b) for the trio: blank DSNs at its restart. (a), and (b) for the other services, stay open.\n"
    "- R-OBS-SC-3's design goes to its own thread (ruling 4 of 2026-11-13). Its start prompt, " + _PROMPT + ", landed with ml#2568. "
    "No design is on `main` yet, and the owner launches the session that writes it (v1.15.16).\n"
)

_SENTRY_PROBED_OLD = "Whether the running services actually send to Sentry was not probed.\n"
_SENTRY_PROBED_NEW = (
    "Whether the running services actually send to Sentry was not probed until 2026-11-12 (v1.15.16):\n\n"
    "- **Probed 2026-11-12**, by variable name only (" + _HO_RULED + ", Q2's \"New since\"): the juniper-deploy stack's cascor, canopy and data containers run with empty DSNs, and recurrence has none. "
    "cascor `v0.14.0`'s `_resolve_sentry_dsn` still reads environment variables only, as `v0.13.0`'s did, so a mounted DSN file initializes nothing.\n"
    "- The trio is stopped (its ports closed on 2026-11-15). Not probed: the four canopy E2E legs (`:8052`, `:8053`, `:8058`, `:8059`), listening on 2026-11-15.\n"
)

# --- XC-P12 ----------------------------------------------------------------------------------------------------------
_CANOPY_620_OLD = "with a daily juniper-data schema-drift check; neither is in a canopy release yet."
_CANOPY_620_NEW = "with a daily juniper-data schema-drift check; neither is in a canopy release yet (v1.15.16: both ship in canopy 0.10.0, published 2026-11-15)."

_CANOPY_630_OLD = "Canopy `main` still reads 0.9.0, so no release carries it yet.\n"
_CANOPY_630_NEW = "Canopy `main` still reads 0.9.0, so no release carries it yet (v1.15.16: canopy 0.10.0 does, published 2026-11-15).\n"

_O13_OLD = "who may pull the canopy primary stays open under O13 (the owner's answer of 09:40:25Z to session `0b8fa86a`'s question).\n"
_O13_NEW = (
    "who may pull the canopy primary stays open under O13 (the owner's answer of 09:40:25Z to session `0b8fa86a`'s question). "
    "**Extended 2026-11-13** (ruling 7 of 2026-11-13; v1.15.16): guarded pulls of the juniper-ml primary too, only when it is on `main` and clean, and never a branch switch (below, R-OBS-SC-2's follow-ups).\n"
)

_PARENT_OLD = "re-read all eleven packages the paragraph names: exactly those two had moved.\n"
_PARENT_NEW = "re-read all eleven packages the paragraph names: exactly those two had moved. It moved on to 0.11.5 on 2026-11-14 (v1.15.16; below).\n"

_QS_OLD = "It showed 0.10.0's resolution of 2026-10-20, whose cascor 0.11.x is below `[servers]`' floor since 0.11.2.\n"
_QS_NEW = "It showed 0.10.0's resolution of 2026-10-20, whose cascor 0.11.x is below `[servers]`' floor since 0.11.2. ml#2568 moved it to 0.11.5's (v1.15.16; below).\n"

_XCP12_ANCHOR = "\n**Actions:**\n"
_XCP12_NEW = (
    "\n**R-OBS-SC-2's follow-ups** (v1.15.16; " + _FNOTE + "):\n\n"
    "- **O13 extended to the juniper-ml primary** (ruling 7 of 2026-11-13, \"Guarded session pulls (Recommended)\", answered 10:10:51Z to session `218ff61e`'s question of 02:41:20Z). "
    "A session may fast-forward it to `origin/main` only when it is on `main` and clean, after listening ports, process working directories and the run directories' pid files show that no live stack imports it, "
    "and it records the pull (time, from and to commits).\n"
    "  - Sessions never switch its branch. For this primary only, it lifts the pull half of the handoffs' \"never pull or switch a primary checkout\"; "
    "the branch half stands, and who may pull the canopy primary stays open.\n"
    "  - Its reflog (`juniper-ml/.git/logs/HEAD`) shows six fast-forward pulls of `main` since the ruling, the last `4a786c81` → `eeb5c694` at 2026-11-15 02:04:55Z. "
    "None appears in a session transcript written since 2026-11-13 10:00Z, so none is a session pull recorded under ruling 7 of 2026-11-13; the owner's own moves stay free. "
    "`JuniperCascor1` imports that `eeb5c694` (XC-SENTRY).\n"
    "- **The parent `Juniper/AGENTS.md`** (unversioned) names juniper-ml 0.11.5 as the latest on PyPI, with observability 0.4.2 and service-core 0.7.2, since 2026-11-14 23:54:29Z: "
    "`util/ad-hoc/2026-11-14_parent_agents_released_paragraph_0_11_5.py` (ml#2568) made the edit on the owner's \"Edit it (Recommended)\" (22:59:11Z, session `1b4fec84`), sha256 `90df2783…` → `f3f69b34…`.\n"
    "  - `util/ad-hoc/2026-11-07_parent_agents_released_paragraph_reprobe.py` ran first (exit 0, " + _HO_1115 + "). "
    "The prior copy is " + _BACKUP + " (sha256 `90df2783…`), copied there on 2026-11-15 from worktree `buzzing-growing-whale`'s `tmp/s2/`.\n"
    "  - **Edited again 2026-11-15** for cascor 0.14.0 and canopy 0.10.0 (ruling 3 of 2026-11-15, \"Edit it once both publish (Recommended)\"; v1.15.16): " + _PARENT_TOOL + " wrote it at 05:49:09Z (its mtime), "
    "sha256 `f3f69b34…` → `3009c3f4…`, after `util/ad-hoc/2026-11-07_parent_agents_released_paragraph_reprobe.py` with five `--expect` exited 0, and its `--check` then printed \"nothing pending\".\n"
    "    - It dates the paragraph 2026-11-15 (Last Updated and the re-probe date) and says deploy#266 pinned the `0.13.0` image until deploy#278. "
    "Its floors sentence now has cascor 0.14.0, canopy 0.10.0 and juniper-ml 0.11.5's `[tools]` floor the patches, and data 0.17.1 and recurrence 0.8.1 floor 0.4.1 and 0.7.1 until their next releases.\n"
    "    - A new bullet covers the two releases. Both copies, before and after, are in " + _BACKUP2 + ".\n"
    "- **`docs/QUICK_START.md`'s sample `pip list`** shows what `juniper-ml[all]==0.11.5` resolves on 2026-11-15 (ml#2568, `7ce8d365`): only the `juniper-ml` line moved.\n"
    "\n**Actions:**\n"
)

_A1_683_OLD = "nor does 0.13.0, cut on 2026-10-28: its `src/api/secrets.py` is unchanged from `v0.12.0`)."
_A1_683_NEW = "nor do 0.13.0, cut on 2026-10-28, and 0.14.0, cut on 2026-11-15 (v1.15.16): `src/api/secrets.py` is unchanged from `v0.12.0` in both)."

_ACTION6_OLD = "0.11.3, recurrence-client 0.3.1 and 0.11.4 are published (§5; v1.15.4, v1.15.5, v1.15.14)"
_ACTION6_NEW = "0.11.3, recurrence-client 0.3.1, 0.11.4 and 0.11.5 are published (§5; v1.15.4, v1.15.5, v1.15.14, v1.15.16)"

# --- §4 Wave 0 -------------------------------------------------------------------------------------------------------
_SIT6_OLD = "6. **XC-SENTRY** (a) or (b) or both; **XC-CRED**, with S0.14's search counts, or, if they are not ready, as if the count were zero (XC-CRED).\n"
_SIT6_NEW = (
    "6. **XC-SENTRY** (a) or (b) or both; **XC-CRED**, with S0.14's search counts, or, if they are not ready, as if the count were zero (XC-CRED). "
    "Ruling 6 of 2026-11-13 settles (b) for the trio (blank DSNs at its restart); (a), and (b) for the other services, stay open (v1.15.16).\n"
)

_A5_ITEM_OLD = "   - the rest of A5: O2, O7, P4 D-4/D-5;\n"
_A5_ITEM_NEW = "   - the rest of A5: O2, O7, P4 D-4/D-5 (ruling 5 of 2026-11-13 answers D-4, and D-5 for cascor 0.14.0 only; §6 A5);\n"

_S011_TEL_OLD = "so the spans had no exporter; recurrence locked 0.141.1 (`EX/round9-reconciliation.md`, \"Drift taken in\").\n"
_S011_TEL_NEW = (
    "so the spans had no exporter; recurrence locked 0.141.1 (`EX/round9-reconciliation.md`, \"Drift taken in\"). "
    "cascor#755 and canopy#816 set it on 2026-11-13 (v1.15.16).\n"
)

# --- §4 Wave 1: Security delivery ----------------------------------------------------------------------------------------
_STEP2_OLD = "(step 4). Who opens the floor PRs was not asked (§5, the note on R-OBS-SC-2).\n"
_STEP2_NEW = (
    "(step 4). Who opens the floor PRs was not asked then: **ruled 2026-11-09** (\"In release PRs (Recommended)\"), so each consumer's next release PR raises them, "
    "as cascor#758 and canopy#818 did (v1.15.16; " + _FNOTE + ").\n"
)

_STEP5_RUN_OLD = "A session then runs S0.11's relay tests in each upgraded environment,"
_STEP5_RUN_NEW = "A session then runs S0.11's relay tests (since ruling 6 of 2026-11-13, the per-lock probe) in each upgraded environment,"

_STEP5_PASS_OLD = "a smoke import and the relay test's fast subset run in the live environment"
_STEP5_PASS_NEW = "a smoke import and the relay test's fast subset (since ruling 6 of 2026-11-13, the per-lock probe) run in the live environment"

_STEP5_O13_OLD = "O13 does not name the juniper-ml primary, so who may move it is open (§6).\n"
_STEP5_O13_NEW = "O13 did not name the juniper-ml primary. **Ruled 2026-11-13** (ruling 7 of 2026-11-13; XC-P12; v1.15.16): guarded session pulls cover it, on `main` and clean, never a branch switch.\n"

_STEP5_OLD = (
    "   - The restart waits for a recorded pass of S0.11's relay tests, which are unwritten: canopy's needs no A1 ruling, while the data-client and cascor parts wait on A1's open limbs. "
    "A pass for cascor and canopy may also need those fixes or 0.4.3, since 0.4.2 does not scrub exception values. Whether the per-lock probe may stand in is the owner's (§6).\n"
    "\n**F-S10 delivery**"
)
_STEP5_NEW = (
    "   - Until ruling 6 of 2026-11-13, the restart waited for a recorded pass of S0.11's relay tests, which are unwritten: canopy's needs no A1 ruling, while the data-client and cascor parts wait on A1's open limbs. "
    "A pass for cascor and canopy might also have needed those fixes or 0.4.3, since 0.4.2 does not scrub exception values. It now waits for the per-lock probe's recorded pass in each environment (next bullet).\n"
    "   - **Ruled 2026-11-13** (ruling 6 of 2026-11-13, \"Probe per environment\", 02:40:52Z; v1.15.16): after the owner upgrades the three environments, a session re-runs the per-lock probe in each and records the result, "
    "and the restart proceeds on that record, on P3-05, and with the six Sentry DSNs blank. F-S10's relays stay untested until S0.11's tests exist.\n"
    "     - The ruling names only what stands in for the relay tests, so the rest of this step holds: record the commit the editable installs run, not pip's version. "
    "On 2026-11-15 the trio was still stopped, `JuniperData` and `JuniperCanopy1` still held observability 0.4.0 and service-core 0.5.0 (read in place), and `JuniperCascor1` imported the primary at `eeb5c694` (XC-SENTRY).\n"
    "6. **The consumer releases** (ruling 5 of 2026-11-13, \"cascor + canopy now (Recommended)\", 02:28:23Z; v1.15.16). This is the image path: it follows step 4 and runs beside step 5, the trio's. "
    "juniper-cascor 0.14.0 and juniper-canopy 0.10.0 were cut from `main` on 2026-11-15, each raising its floors in its release PR (round 1's ruling 1). "
    "The owner approved both `pypi` gates, and PyPI serves canopy's wheel since 05:17Z and cascor's since 05:24Z. 0.14.0 is not R-CASCOR, whose gates stand.\n"
    "   - **Pinned 2026-11-15** (v1.15.16): cascor's gate was approved on ruling 1 of 2026-11-15, whose file-by-file check passed at 05:41:45Z. juniper-deploy#278 then moved cascor to 0.14.0 and canopy to 0.10.0, "
    "and `util/safe_merge.py` squash-merged it at 05:48:57Z (`db7b7cb4`) under the owner's merge approval, once its required checks were green (" + _FNOTE + ").\n"
    "     - The owner restarts the juniper-deploy stack (ruling 6 of 2026-11-13 governs only the trio's restart).\n"
    "     - data waits for 0.18.0 (R-DATA-2), and recurrence for its next release. #278 left `docker-compose.yml:598` at `juniper-recurrence:0.8.0` while 0.8.1 is published (PyPI since 2026-11-06, and GHCR), "
    "so juniper-deploy's `scripts/verify_published_images.py --fail-on-stale` still exits 1 on it. Whether recurrence's pin moves is the owner's.\n"
    "\n**F-S10 delivery**"
)

# --- §4 Wave 1: Cascor and Canopy --------------------------------------------------------------------------------------
_CASCOR_ANCHOR = (
    "- cascor 0.12.0 and 0.13.0 shipped on locks that pin observability 0.4.1 and service-core 0.7.1, so a cascor image carries R-OBS-SC-2 only from a later cascor release; "
    "whether a fix-forward is owed stays the owner's (v1.15.15).\n"
)
_CASCOR_NEW = (
    _CASCOR_ANCHOR
    + "- That later release is cascor 0.14.0 (v1.15.16): cascor#758 (2026-11-15 01:14:13Z, `bf6f0108`) raised the floors, and Release `v0.14.0` (01:28:19Z) was cut on ruling 5 of 2026-11-13, again ahead of P3-05 and P3-08. "
    "Its image is on GHCR, and its wheel is on PyPI since 05:24Z, the owner having approved the `pypi` gate on ruling 1 of 2026-11-15 (run 43663237489). "
    "Its notes name no F-S10 fix and `src/api/secrets.py` is unchanged from `v0.13.0`, so the fix-forward question stands, now for 0.12.0 to 0.14.0.\n"
    "  - juniper-deploy pins it since deploy#278 (2026-11-15 05:48:57Z).\n"
)

_CANOPY_OLD = "the second cut P4 D-4 contemplates. D-4 is not ruled (v1.15.15).\n"
_CANOPY_NEW = (
    "the second cut P4 D-4 contemplates. D-4 was not ruled then (v1.15.15).\n"
    "- That second cut is canopy 0.10.0 (v1.15.16), and ruling 5 of 2026-11-13 answers D-4. canopy#818 (2026-11-15 01:19:38Z, `57d90dec`) raised the floors, and Release `v0.10.0` was cut at 01:41:30Z. "
    "Its image is on GHCR, and its wheel is on PyPI since 05:17Z, the owner having approved the `pypi` gate (run 43664277663).\n"
    "  - Like 0.9.0, it was cut without P3-06's validation, the O3 wording fix and A4's asks (S0.5 open): its `[0.10.0]` section mentions none of #685, O3 or APD-ECO-009..012.\n"
    "  - juniper-deploy pins it since deploy#278 (2026-11-15 05:48:57Z).\n"
)

# --- §5: rows ----------------------------------------------------------------------------------------------------------
_SC3_OLD = "| Designed and validated on its own (the owner's ruling); then its own lock round | XC-SENTRY's end; the trio's restart, if S0.11's pass needs it |"
_SC3_NEW = (
    "| Designed and validated on its own (the owner's ruling), in a session the owner launches (ruling 4 of 2026-11-13; prompt in ml#2568); then its own lock round "
    "| XC-SENTRY's end (the trio's restart waits no longer: ruling 6 of 2026-11-13) |"
)

#: R-CASCOR's row sits at 507 characters, so its bypass clause shrinks by 22.
_RCASCOR_ROW1_OLD = "| **R-CASCOR**: juniper-cascor (PyPI 0.11.0) |"
_RCASCOR_ROW1_NEW = "| **R-CASCOR**: juniper-cascor (PyPI 0.14.0) |"
_RCASCOR_ROW2_OLD = "Bypassed in part: cascor#712 bumped it to 0.12.0 on 2026-10-10; served 2026-10-25 (note below) |"
_RCASCOR_ROW2_NEW = "Bypassed in part by 0.12.0 (cascor#712), 0.13.0 and 0.14.0 (notes below) |"

_ROW_ANCHOR = "| `pip install -U juniper-ml[recurrence]` moves an environment off recurrence 0.8.0, and so off model-core 0.2.0 |\n"
_ROW_NEW = (
    _ROW_ANCHOR
    + "| **R-ML-TOOLS-2** (shipped as juniper-ml 0.11.5, 2026-11-14, cut on the owner's rulings of 2026-11-09 and 2026-11-13; note below) "
    "| `[tools]`'s `juniper-observability>=0.4.2` and `juniper-service-core>=0.7.2,<0.8.0` (ml#2555), the floors on R-OBS-SC-2 "
    "| R-OBS-SC-2 on PyPI (met 2026-11-09); proposal ml#2558, archive ml#2561; the owner approved the gate (run 43408809021) "
    "| `pip install -U juniper-ml[tools]` moves an environment off observability 0.4.1 and service-core 0.7.1 |\n"
)

# --- §5: the R-OBS-SC-2 note's stale bullets -------------------------------------------------------------------------------
_STAY_OLD = "  - No `pyproject.toml` moved: the floors stay at observability `>=0.4.1` and service-core `>=0.7.1`."
_STAY_NEW = "  - No `pyproject.toml` moved: the floors stayed at observability `>=0.4.1` and service-core `>=0.7.1`."

_PLAN_OLD = "That plan is a session's, not a ruling (P3-17 stays open; §6).\n"
_PLAN_NEW = (
    "That plan was a session's, not a ruling (P3-17 stayed open until round 1's ruling 1 of 2026-11-09; §6). "
    "v1.15.16: cascor#758 and canopy#818 raised them; data's and recurrence's wait for their release PRs.\n"
)

_IMAGE_OLD = (
    "- **No running image carries it yet.** Each consumer's newest Release predates its lock PR (data `v0.17.1`, cascor `v0.13.0`, canopy `v0.9.0`, recurrence `juniper-recurrence-v0.8.1`). "
    "The fix reaches a running image only through that repository's next release, juniper-deploy's pin and a restart (§9):\n"
)
_IMAGE_NEW = (
    "- **No running image carries it yet** (re-probed 2026-11-15; v1.15.16). The published cascor `v0.14.0` and canopy `v0.10.0` images carry it (read by digest; the next note), and deploy#278 pins them, "
    "but no running service has restarted on them. data's and recurrence's newest Releases (`v0.17.1`, `juniper-recurrence-v0.8.1`) predate their lock PRs. "
    "The fix reaches a running image only through that repository's next release, juniper-deploy's pin and a restart (§9):\n"
)

_CASCOR_SUB_OLD = "so R-OBS-SC-2 needs a later cascor release; whether a fix-forward is owed is the owner's (§6, mid-wave sitting);\n"
_CASCOR_SUB_NEW = "so R-OBS-SC-2 needs a later cascor release; whether a fix-forward is owed is the owner's (§6, mid-wave sitting). That release is 0.14.0, cut and published 2026-11-15 on ruling 5 of 2026-11-13 (v1.15.16);\n"

_CANOPY_SUB_OLD = "the second cut P4 D-4 contemplates (§4 Wave 1, Canopy);\n"
_CANOPY_SUB_NEW = "the second cut P4 D-4 contemplates (§4 Wave 1, Canopy). That cut is 0.10.0 (2026-11-15; v1.15.16);\n"

_TRIO_SUB_OLD = "and `JuniperCascor1` imports 0.4.2's and 0.7.2's code from the juniper-ml primary (Security step 5).\n"
_TRIO_SUB_NEW = (
    "and `JuniperCascor1` imports 0.4.2's and 0.7.2's code from the juniper-ml primary (Security step 5). "
    "On 2026-11-15 the first two are unchanged, and `JuniperCascor1` imports the primary at `eeb5c694`, whose service-core is 0.7.2's plus four unreleased fixes (XC-SENTRY; v1.15.16).\n"
)

_FOLLOW_OLD = "- **Follow-ups**, asked at §6's mid-wave sitting (none acted on):\n"
_FOLLOW_NEW = "- **Follow-ups**, asked at §6's mid-wave sitting (none acted on by 2026-11-09; the owner ruled the first three on 2026-11-09, and they were carried out by 2026-11-15: the next note):\n"

_TOOLS_OLD = "  - juniper-ml's `[tools]` floors `juniper-observability>=0.4.1`; raising it to `>=0.4.2` needs a meta-package release (0.11.5).\n"
_TOOLS_NEW = (
    "  - juniper-ml's `[tools]` floored `juniper-observability>=0.4.1` on 2026-11-09; raising it to `>=0.4.2` needed a meta-package release (0.11.5). "
    "**Done**: juniper-ml 0.11.5, published 2026-11-14 (R-ML-TOOLS-2; v1.15.16).\n"
)

_RL_OLD = (
    "  - The forks' `RateLimiter` still truncates with no floor (data `juniper_data/api/security.py:250` and `:254`, cascor `src/api/security.py:229` and `:233`, canopy `src/security.py:270` and `:274`), "
    "so APD-SVCCORE-004's `Retry-After: 0` is live in all three, with no register row. "
    "Data `:427` and cascor `:386` keep `FailedAuthThrottle`'s `max(1, int(...))`, the round-down 0.7.2 fixed only in service-core.\n"
)
_RL_NEW = (
    "  - On 2026-11-09 the forks' `RateLimiter` truncated with no floor (data `juniper_data/api/security.py:250` and `:254`, cascor `src/api/security.py:229` and `:233`, canopy `src/security.py:270` and `:274`), "
    "so APD-SVCCORE-004's `Retry-After: 0` was live in all three, with no register row. "
    "Data `:427` and cascor `:386` kept `FailedAuthThrottle`'s `max(1, int(...))`, the round-down 0.7.2 fixed only in service-core.\n"
    "    - **Fixed 2026-11-13** in all three (data#537, cascor#757, canopy#817), on `main`, in cascor 0.14.0 and canopy 0.10.0 (both on PyPI since 2026-11-15), and in no data release before 0.18.0. "
    "Filed as `APD-ECO-016` on 2026-11-15 (ml#2576), so the register has its row (v1.15.16; the next note).\n"
)

_TEL_OLD = (
    "  - cascor and canopy pass no `telemetry=` to `FastAPI()`, so they run FastAPI 0.162.0's default telemetry. "
    "It is inert while their locks hold `opentelemetry-api` and no SDK, but data#454's opt-out is missing in both.\n"
)
_TEL_NEW = (
    "  - On 2026-11-09 cascor and canopy passed no `telemetry=` to `FastAPI()`, so they ran FastAPI 0.162.0's default telemetry. "
    "It was inert while their locks held `opentelemetry-api` and no SDK, but data#454's opt-out was missing in both. **Done 2026-11-13**: cascor#755 and canopy#816 (v1.15.16).\n"
)

# --- §5: the new note, before R-DC-PATCH's ---------------------------------------------------------------------------------
_N_HEAD = (
    "**R-OBS-SC-2's follow-ups, 2026-11-09 to 2026-11-15** (v1.15.16; sessions `a4e1e914`, `6e3bdef0`, `218ff61e`, `7d425759`, `1b4fec84` and `b9dfa450`). "
    "Option labels are quoted verbatim, \"(Recommended)\" markers included, and each answer is dated from its transcript (`util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py`).\n"
    "`util/ad-hoc/2026-11-15_r_obs_sc_2_followups_record_reprobe.py` re-checked the facts the Validation record lists (0 FAIL); the memory records and the option texts were read by hand. "
    "Each Release below was cut by a session on the owner's rulings, where §5's rules have the owner cut.\n\n"
)
_N_ROUND1 = (
    "- **Round 1** (session `a4e1e914`, asked 2026-11-09 14:27:13Z, answered 14:48:41Z; " + _HO_RULED + "):\n"
    "  1. Floor PRs, \"In release PRs (Recommended)\": each consumer's next `release/` bump PR raises `juniper-observability>=0.4.2` and `juniper-service-core>=0.7.2`, since the lock regen skips `release/` branches. "
    "This answers P3 D-03's third part (P3-17, now done).\n"
    "  2. 0.11.5, \"Floor PR, then 0.11.5 (Recommended)\": the `[tools]` floor PR, then a patch cut, with the owner's `pypi` gate.\n"
    "  3. The forks' `RateLimiter`, \"Row + fix all three (Recommended)\": file `APD-ECO-016`, one fix PR per fork, and a fork-drift guard naming the row (a check in `tests/test_service_fork_drift.py` that every copy keeps the fix).\n"
    "  4. Telemetry, \"Port to both now (Recommended)\": data#454's opt-out in cascor and canopy.\n"
    "  - Round 2 asked four questions at 14:49:42Z: Q1, when the 0.4.3 design starts; Q2, which releases carry the new locks; Q3, whether the per-lock probe may stand in for S0.11's relay tests at the trio's restart; "
    "Q4, who may move the juniper-ml primary. They came back on 2026-11-12 at 00:20:11Z with \"The user wants to clarify these questions.\" and no text, and session `218ff61e` re-asked them.\n"
)
_N_PRS = (
    "- **The five PRs of 2026-11-13** (session `6e3bdef0`, under the owner's grant of 2026-11-12 00:39:16Z, \"approval granted for merging and related git operations for this work arc.\"; "
    "`…five-prs-validated-opening-next.md`), each one GitHub-signed commit, squash-merged: ml#2555, the `[tools]` floors (00:49:00Z, `26ea0ecb`); "
    "cascor#755 (00:27:18Z, `5834709a`) and canopy#816 (00:34:13Z, `b9417b2f`), the telemetry opt-outs.\n"
    "  - cascor#757 (01:07:08Z, `66b39a5c`) and canopy#817 (01:02:07Z, `55ac2168`), whose `Retry-After` and `X-RateLimit-Reset` round up and are never 0.\n"
    "  - juniper-data's fix was data#537 (02:54:07Z, `3cf8867c`), which also rounds up its `FailedAuthThrottle`. It was a carrier (a PR that carries a change on another's behalf) of flood-4, "
    "the session line that disposes of the fourth Cursor-fleet flood (" + _FLOOD4 + ").\n"
)
_N_ROUND2 = (
    "- **The owner's rulings of 2026-11-13** (session `218ff61e`, numbered as " + _HO_1113 + " numbers them; 4 to 7 answer round 2's Q1 to Q4):\n"
    "  1. 0.11.5 (01:57:00Z), \"Yes, as patch 0.11.5 (Recommended)\": session `218ff61e` cuts it as a patch, and the owner approves the `pypi` gate.\n"
    "  2. Worktrees (01:57:00Z), \"Remove after checks (Recommended)\": the four merged fork worktrees, each after its checks. Carried out on 2026-11-13; by the ruling, "
    "the never-opened juniper-data worktree and the two juniper-ml session worktrees stay.\n"
    "  3. How to re-ask round 2 (01:57:00Z), \"One at a time, with background\".\n"
    "  4. Q1, the 0.4.3 design (02:14:33Z), \"Now, in its own thread (Recommended)\": a start prompt for a fresh session, which writes the design to `notes/`, runs its rounds and brings it to the owner.\n"
    "  5. Q2, lock cuts (02:28:23Z), \"cascor + canopy now (Recommended)\": a cascor and a canopy release from `main`, each raising its floors in its release PR, then juniper-deploy's pins and its stack's restart. "
    "cascor is cut ahead of P3-05 and P3-08 again; data waits for 0.18.0, and recurrence for its next release. It answers P4 D-4, and D-5 for this cut (§6 A5).\n"
    "  6. Q3, the restart gate (02:40:52Z), \"Probe per environment\": the per-lock probe, re-run in each upgraded environment and recorded, stands in for S0.11's relay tests at the trio's restart (§4 Wave 1, Security step 5).\n"
    "  7. Q4, the juniper-ml primary (asked 02:41:20Z, answered 10:10:51Z), \"Guarded session pulls (Recommended)\": O13 extends to it (XC-P12).\n"
    "  - `…_owner_answers.py` prints `answered None` for ruling 7 of 2026-11-13 and for session `7d425759`'s dialog: a later copy of each result, an `api-request-blob` entry, has no timestamp and overwrites the first. "
    "The `user` entries that carry them are stamped 10:10:51.412Z and 2026-11-14 22:10:39.373Z (a tool defect: the findings, below).\n"
)
_N_1114 = (
    "- **2026-11-14.** Session `7d425759` asked four questions at 10:20:43Z. The owner sent them back to clarify (22:10:39Z), asked for an update to " + _HO_1113 + " (22:12:40Z), "
    "and wrote at 22:37:55Z: \"the four open questions should be handled by the session working from the updated handoff.\"\n"
    "  - Session `1b4fec84` took them up, reading the owner's opening instruction (22:53:41Z) as the answer to the first, the arc's scope (" + _HO_1115 + ").\n"
    "  - Its three answers: parent docs, \"Edit it (Recommended)\" (22:59:11Z); cascor's version, \"0.14.0 (Recommended)\" (23:36:54Z); canopy's, \"0.10.0 (Recommended)\" (23:42:13Z).\n"
)
_N_0115 = (
    "- **juniper-ml 0.11.5** (R-ML-TOOLS-2, above): proposal ml#2558 (2026-11-13 10:08:14Z, `48b66130`), whose co-change commit took out of `docs/REFERENCE.md` the two clauses ml#2555 had added "
    "to say `main`'s new floors were unreleased; Release `v0.11.5` at 10:24:18Z on `48b66130`; archive ml#2561 (10:38:29Z, `7ae846b6`).\n"
    "  - Run 43408809021: the owner approved its `pypi` gate (\"approved for pypi\"), and `Publish to PyPI` ran 2026-11-14 00:16:06Z–00:16:27Z. "
    "PyPI serves the wheel from 00:16:22Z and the sdist from 00:16:23Z, with the sha256 TestPyPI took; `requires_dist` carries `juniper-observability>=0.4.2; extra == \"tools\"` "
    "and `juniper-service-core<0.8.0,>=0.7.2; extra == \"tools\"`.\n"
    "  - After it: `docs/QUICK_START.md`'s sample (ml#2568, 2026-11-15 02:15:25Z, `7ce8d365`), and the unversioned parent `Juniper/AGENTS.md`'s paragraph, edited 2026-11-14 23:54:29Z outside any PR "
    "and again on 2026-11-15 at 05:49:09Z for the two cuts (XC-P12).\n"
)
_N_ECO016 = (
    "- **`APD-ECO-016`** (`…DEFECT-REGISTER.md` §4.9 and §5.1): ml#2576 (merged 2026-11-15 02:51:37Z, `6befa3ba`) filed it FIXED and made the fork-drift guard `retry-after-rounds-up` ENFORCED: "
    "eleven sites in four copies, each read only inside its named function (\"scoped\"). It replaced ml#2573 (closed 02:40:36Z), the same seven files, which could no longer merge cleanly (\"DIRTY\") once ml#2571 merged first (02:29:06Z).\n"
    "  - Docs Full Check, the only workflow that runs the guard's cross-repo checks (the ones that read sibling checkouts), was dispatched after the merge (run 43669737463, success): its fork-drift step ran 17 tests, OK, with no skips.\n"
    "  - Two Opus reviews read the guard: round 1 on 2026-11-14 (1 MAJOR, 6 MINORs and 6 NITs, no BLOCKER) and round 2 on 2026-11-15 (3 BLOCKERs, false statements in the register text; 1 MAJOR; 12 MINORs and NITs). "
    "All were applied before the merge (ml#2576's body).\n"
    "    - Round 2 also proposed an optional tripwire, a test that fails once canopy gains a `FailedAuthThrottle` so that its sites get added. It was not built; `APD-ECO-010`'s row carries a note of 2026-11-15 instead.\n"
)
_N_CUTS = (
    "- **juniper-cascor 0.14.0** (ruling 5 of 2026-11-13; its version, the owner's ruling in session `1b4fec84`): cascor#758 (2026-11-15 01:14:13Z, `bf6f0108`) raised `juniper-observability>=0.4.2` "
    "and `juniper-service-core>=0.7.2,<0.8.0`; Release `v0.14.0` at 01:28:19Z on `bf6f0108`; archive ml#2570 (03:03:56Z, `bb600136`).\n"
    "  - Publish run 43663237489 (created 01:28:21Z): `Publish to TestPyPI` succeeded. On ruling 1 of 2026-11-15 (below) the owner approved the `pypi` gate as it stood (\"approved for deployment to pypi\"): "
    "the deployment left `waiting` at 05:23:36Z, and `Publish to PyPI` ran 05:23:37Z–05:24:10Z. Image run 43663237432 succeeded, and GHCR serves `0.14.0` and `0.14`.\n"
    "  - **Published 2026-11-15** (v1.15.16): PyPI serves the wheel from 05:24:05Z and the sdist from 05:24:07Z. The run has no shared build job, so each is a second build whose sha256 differs from TestPyPI's "
    "(the wheel's `b70f3d39…` against `c5c9a5dc…`), as 0.13.0's did, while every member is identical (207 in the wheel, 113 in the sdist).\n"
    "  - This corrects " + _HO_1115 + "'s \"each wheel's sha256 equals TestPyPI's\" for cascor: only canopy's run shares one build between the two uploads.\n"
    "- **juniper-canopy 0.10.0** (the same): canopy#818 (01:19:38Z, `57d90dec`) raised `juniper-observability>=0.4.2,<0.5.0` and `juniper-service-core>=0.7.2,<0.8.0`, "
    "and moved its three hard-coded fallback versions (two `__version__` values and `resolve_app_version`'s default) to 0.10.0; Release `v0.10.0` at 01:41:30Z on `57d90dec`; archive ml#2572 (01:57:40Z, `eeb5c694`).\n"
    "  - Publish run 43664277663 (created 01:41:32Z): Build and Validate and `Publish to TestPyPI` succeeded. The owner approved the `pypi` gate (\"approved for pypi\") while the dialog of 05:17:06Z was open: "
    "the deployment left `waiting` at 05:17:31Z, and `Publish to PyPI` ran 05:17:33Z–05:17:58Z. Image run 43664277607 succeeded, and GHCR serves `0.10.0` and `0.10`.\n"
    "  - **Published 2026-11-15** (v1.15.16): PyPI serves the wheel from 05:17:51Z and the sdist from 05:17:53Z, each with the sha256 TestPyPI took.\n"
    "  - Like 0.9.0, it was cut without P3-06's validation, the O3 wording fix and A4's asks (S0.5 open; §4 Wave 1, Canopy).\n"
    "- **Both on PyPI**: the file-by-file check ruling 1 of 2026-11-15 requires before any pin, `util/ad-hoc/2026-11-15_verify_cascor_0_14_0_canopy_0_10_0_published.py`, ran against PyPI at 05:41:45Z (0 failed checks). "
    "cascor's sdist is `79cc0da3…` against TestPyPI's `92f0b146…`, every member identical like the wheel's; canopy's wheel and sdist equal TestPyPI's by hash.\n"
    "  - Each release's `Requires-Dist` floors observability 0.4.2 and service-core 0.7.2, and its limiter holds the round-up.\n"
    "  - Both images were pulled by index digest (cascor `sha256:6b3e64bd…`, canopy `sha256:d9a966ff…`; revision labels `bf6f0108` and `57d90dec`) and run with no network: "
    "each installs observability 0.4.2 and service-core 0.7.2 on Python 3.14.10 (`util/ad-hoc/2026-11-15_probe_published_images_cascor_0_14_0_canopy_0_10_0.py`, 03:33Z, exit 0).\n"
    "- **2026-11-15: the owner's directive and three rulings** (session `b9dfa450`). The owner wrote at 05:14:10Z, after hearing that cascor's PyPI job rebuilds its files: " + _DIRECTIVE + "\n"
    "  - The dialog was asked at 05:17:06Z and answered at 05:24:49Z (the labels from `…_owner_answers.py b9dfa450 --full`, the option texts from the transcript):\n"
    "    1. cascor 0.14.0, \"Approve as is, verify after (Recommended)\": \"You approve the gate when you choose; PyPI gets a rebuild of the same commit. "
    "Before juniper-deploy pins anything, I compare PyPI's wheel and sdist with TestPyPI's file by file and stop if any file differs (for 0.13.0 every file was identical; only the archives' timestamps differed). "
    "The fix applies from cascor's next release.\"\n"
    "    2. Fix scope, \"cascor, then every other (Recommended)\": \"The cascor PR first. Then one PR per repo: the same change wherever the audit finds a per-job rebuild, and the hash check in every publish workflow, "
    "canopy's included (it shares one build but compares no hashes, so a stale TestPyPI upload could still slip through). I merge each once green, under this session's merge approval.\"\n"
    "    3. Parent docs, \"Edit it once both publish (Recommended)\": \"I re-probe the paragraph, keep a backup copy in juniper-ml/tmp/, make the edit, and record the before and after sha256. No PR: the file is unversioned.\"\n"
    "  - **The publish-artifact fix is in progress, a session's work and not an owner item**: one build shared by both publish jobs, plus an identical-hash check against TestPyPI after its upload and again before PyPI's, "
    "for juniper-cascor first, with an audit of every Juniper publish workflow (the dialog's second question); then one PR per repo (ruling 2 of 2026-11-15). No juniper-cascor PR for it was open at 06:05Z.\n"
    "- **juniper-deploy#278** (v1.15.16): one GitHub-signed commit, `a79b3640`, on base `6c9e57f8`, made by `util/ad-hoc/2026-11-15_deploy_pin_cascor_0_14_0_canopy_0_10_0.py` and uploaded by `util/open_signed_pr.py`. "
    "`util/safe_merge.py` squash-merged it at 05:48:57Z (`db7b7cb4`) once its required checks were green.\n"
    "  - `docker-compose.yml` moves cascor 0.13.0 → 0.14.0 in `juniper-cascor` and `juniper-cascor-demo`, and canopy 0.9.0 → 0.10.0 in `juniper-canopy`, `juniper-canopy-demo` and `juniper-canopy-dev`; "
    "`k8s/helm/juniper/values.yaml` moves both DEPLOY-15 tags; `CHANGELOG.md` gains one entry.\n"
    "  - The pre-push gate ran first (`util/ad-hoc/2026-11-15_pre_push_gate_run.bash`; PASS at 05:44:38Z, on its third run). The files scan's one finding, `docker-compose.yml:1204:14` `juniper-env-credential`, "
    "is an environment-variable reference with a default path by its masked shape (`random-looking=0`), byte-identical on deploy `main`, and was accepted after its masked read, so 0 were open.\n"
    "    - The text scan (the PR body and the commit body) found 0, the masked `--names` read of the 40 added lines listed 0, and the canary found 32 of 32 planted classes. "
    "The first run stopped on the open finding, and the second on its acceptance list, which the third confined to the files scan.\n"
    "  - On deploy `main` (`db7b7cb4`), `scripts/verify_published_images.py --fail-on-stale` finds all 6 refs on both architectures and cascor and canopy current, "
    "and still exits 1 for `juniper-recurrence:0.8.0` (0.8.1 published), which #278 left alone. Whether recurrence's pin moves is the owner's.\n"
    "- **The release bodies** were each reviewed twice by an independent Opus reader. Round 1 found 2 BLOCKERs, 4 MAJORs and 5 smaller items in cascor's, and 5 BLOCKERs and 10 smaller items in canopy's, "
    "most of them statements true when their PR merged and false at the release head; 25 of the 26 were applied, and canopy's item 15, the order of its categories, was left as is.\n"
    "  - Round 2 found 24 of the 25 resolved; the 25th (canopy's item 10), whose new wording raised a MINOR, was reworded.\n"
    "- **The reviews are archived** with their briefs in " + _REVIEWS + " (its `README.md`): the guard's two, the bodies' two, this draft's two (the Validation record), "
    "and the five PRs' validation fix pass, `five-prs-validation-fixpass-round-1.md`.\n"
    "- **The 0.4.3 design's start prompt** (ruling 4 of 2026-11-13): " + _PROMPT + " (ml#2568). No design is on `main` yet, and the owner launches its session (R-OBS-SC-3, above; §7.1).\n"
)
_N_FIND1 = (
    "- **Findings, open unless a line says otherwise.** Each one's cited lines were re-read on `main` on 2026-11-15 (the two CHANGELOG lines at the release tags); the behaviour each states is its source's, not re-run here. "
    "\"The fix pass\" is the five PRs' validation fix pass, " + _REVIEWS + "'s `five-prs-validation-fixpass-round-1.md` (a verbatim copy of `tmp/lps/fixpass_r1.md`, sha256 `ad8d9091…`).\n"
    "  - juniper-service-core's app factory passes no `telemetry=` (`juniper_service_core/app.py:56`), and juniper-recurrence builds with it: its lock pins FastAPI 0.141.1, below 0.142, "
    "but its floor `fastapi>=0.110` is uncapped, so a re-resolution crosses 0.142. Source: the fix pass, A-5. Next: the session that prepares service-core 0.8.0, or R-OBS-SC-3's design.\n"
    "  - The ported telemetry tests skip below FastAPI 0.142 (`importorskip(\"fastapi.telemetry\")`: data `test_api_app.py:64`, cascor `test_api_app.py:44`, canopy `test_main_import_and_lifespan.py:330`). "
    "A test that reads `app.extra[\"telemetry\"]` would run there too; one PR could add it to all three. Source: the fix pass, A-4. Next: Hygiene (T6).\n"
    "  - A wall clock stepped backwards makes the wait read above the window in all four limiter copies, which read `time.time()` (data `security.py:257`, cascor `:234`, canopy `:273`, service-core `:250`). "
    "Source: the fix pass, B-8. Next: the owner (its candidate fix is `time.monotonic()` in all four).\n"
    "    - canopy's `_evict_expired` (`:234`) then answers differently from cascor's and service-core's, whose prunes are identical; data's `TTLCache` path was not compared. Source: the fix pass, B-9. Next: with B-8.\n"
    "  - cascor's `docs/api/JUNIPER_CASCOR_API_REFERENCE.md:113` (\"Exempt paths\") still lists `/docs`, `/openapi.json` and `/redoc`, while `src/api/middleware.py`'s `EXEMPT_PATHS` exempts only health and `/metrics`, "
    "a choice its comment ties to `APD-DATA-024` (data's \"securing the service deletes `/openapi.json`\"). Source: the fix pass, B-10. Next: Hygiene (T6).\n"
    "  - The WebSocket control `retry_after` and `HandshakeCooldown.get_block_remaining` round to one decimal, so a wait under 50 ms reads `0.0`: "
    "cascor `src/api/websocket/control_security.py:81` and `:154`, service-core `websocket/control_security.py:112` and `:185`. Source: the fix pass. Next: the owner.\n"
    "    - Still open: flood-4's owner answer of 2026-11-12 23:34:04Z (session `f2b4e7c3`) chose \"WebSocket gaps beside N-4\" (N-4 is flood-4's service-core WebSocket fix, not P1's N-4), "
    "whose option names other gaps (an unserialisable broadcast, `/ws/control` after a server close, a per-IP slot freed early), not these.\n"
)
_N_FIND2 = (
    "  - juniper-ml's `tests/test_release_train_registry.py` walks the checkout for `pyproject.toml` without skipping `tmp/` (`:178`, `:180`), so 3 tests fail locally whenever `tmp/` holds any `pyproject.toml`; "
    "they pass in CI. The owner's 2026-10-26 rulings have a scan choose its scope (`notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md`). Source: the fix pass. Next: the owner.\n"
    "  - juniper-ml#2507's tests, a Cursor draft's, make the compatibility matrix's current row track `pyproject.toml` between a floor PR and its release, "
    "and nothing checks that the paragraph above the matrix in `docs/REFERENCE.md` says so. Source: the fix pass (its item 6). Next: flood-4's session, which takes it to the owner.\n"
    "    - Carried on 2026-11-15 under flood-4's ruling 14 (" + _FLOOD4 + " §8 item 14, \"Carry + extend propose.py\"): ml#2579 (04:25:56Z, `11cac1af`) makes `util/release_train/propose.py` "
    "render the four `docs/REFERENCE.md` sites those tests pin, ml#2581 (05:29:07Z, `4f53e69a`) carries the tests, and #2507 closed at 05:30:31Z. "
    "Whether a check of the paragraph came with them was not re-read here.\n"
    "  - juniper-service-core's next release is a minor, 0.8.0 (its `[Unreleased]`, since ml#2534), so every `<0.8.0` cap widens first: juniper-ml's `[tools]`, data's, recurrence's, cascor's and canopy's, "
    "which juniper-ml 0.11.5, cascor 0.14.0 and canopy 0.10.0 have just set. Source: the fix pass. Next: §5's rule (cap PRs land before the Release), for the session that prepares 0.8.0.\n"
    "  - juniper-ml#2360's merge misfiled `CHANGELOG.md` entries two ways, one bullet under the released `[0.11.4]` and five entries under the wrong category. ml#2558 repaired both, "
    "but `util/ad-hoc/2026-09-23_released_section_drift.py` sees only the first kind. Source: " + _HO_1113 + ". Next: Hygiene (T6).\n"
    "  - canopy's `conf/conda_environment_cpu.yaml:47` pins `dash=3.3.0`, below `pyproject.toml`'s `dash>=4.0.0` (`:56`), which canopy 0.10.0 ships. Source: " + _HO_1115 + ". Next: Hygiene (T6).\n"
    "  - canopy's `.github/workflows/juniper-data-schema-drift.yml:40-41` still says, over two comment lines, that it fires \"only once juniper-data's notify matrix lists juniper-canopy\", "
    "which the matrix has done since data#501 (`notify-consumers.yml:78`). Source: " + _HO_1115 + ". Next: Hygiene (T6).\n"
)
_N_FIND3 = (
    "  - flood-4's \"ruling 17\" is one ruling over four fixes (" + _FLOOD4_HO + ", item 3: data's 44 unmarked tests, cascor's stop-then-start race, canopy's unit-lane port guard and canopy's `lockfile-update.yml` print), "
    "so the CHANGELOGs that cite it agree: cascor `:244` at `v0.14.0`, canopy `:156` and `:221` at `v0.10.0`.\n"
    "    - What is left: " + _FLOOD4 + "'s §8 stops at ruling 14. Source: " + _HO_1115 + ". Next: flood-4's session, in the record's next update.\n"
    "  - ml#2576's body names three plan passages its filing made stale: this plan's \"with no register row\" (the R-OBS-SC-2 note, above) and \"a second passage near its §6 A1 follow-ups\" (the mid-wave sitting's R-OBS-SC-2 follow-ups), both made current here, "
    "and the v2 draft's \"has no APD-ECO-016\" (its line 153; the body gives no line). Source: ml#2576's body. Next: the owner, on whether the v2 draft gets a pointer to the rulings.\n"
    "    - v1.15.16 leaves the v2 draft unedited, though more of it is stale: `:110`, `:150` (\"being carried out by session `6e3bdef0`\"), `:153`, `:315`, `:322`, `:357`, `:358`, `:398-399` (round 2's Q1 to Q4 as open), "
    "`:409`, `:455` (\"No session moves it (Q4)\") and `:480` (H-26, \"Never pull one\"); rulings 4 to 7 of 2026-11-13 contradict the last four.\n"
    "    - The body also names two stale texts it left: the register's §2.3 compare row (\"latest published wheel, 0.7.0 … still short-circuits\") and `docs-full-check.yml`'s \"THIS is where that gate actually bites\". Next: Hygiene (T6).\n"
    "  - `util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py` keeps the last entry carrying each answer, so it prints `answered None` when that entry is an untimed `api-request-blob` copy "
    "(ruling 7 of 2026-11-13; `7d425759`'s dialog). Source: this record, whose re-probe reads the first timestamped entry. Next: Hygiene (T6), a dated successor, since the script is retained as provenance.\n"
)
_N_OPEN = (
    "- **Still open with the owner** (§6):\n"
    "  - the juniper-deploy stack's restart. juniper-deploy's pins after the gates are done: deploy#278 merged at 05:48:57Z under the owner's merge approval "
    "(granted to session `b9dfa450` on 2026-11-15 at 03:14:03Z). Ruling 6 of 2026-11-13 governs only the trio's restart;\n"
    "    - whether juniper-deploy's `juniper-recurrence:0.8.0` (`docker-compose.yml:598`) moves to 0.8.1, published since 2026-11-06: #278 left it, so `--fail-on-stale` still exits 1;\n"
    "  - launching the 0.4.3 design session from " + _PROMPT + " (ruling 4 of 2026-11-13; §7.1);\n"
    "  - the trio's environment upgrade (`JuniperData` and `JuniperCanopy1` still hold observability 0.4.0 and service-core 0.5.0, read 2026-11-15), "
    "then the trio's restart on the condition of ruling 6 of 2026-11-13: the probe's recorded pass in each environment, P3-05, and blank DSNs;\n"
    "  - who may pull the canopy primary (O13), and whether a fix-forward is owed for cascor 0.12.0 to 0.14.0, all cut ahead of P3-05 and P3-08;\n"
    "  - A1's open limbs: the data-client and cascor F-S10 fixes, P6 OD-2, canopy#685 call (a), and whether host recurrence legs take a port of W1.14 (§6 A1);\n"
    "  - whether the v2 draft gets a pointer to the rulings (above);\n"
    "  - the worktree housekeeping, worktree by worktree on the owner's word, as " + _HO_1113 + " (item 6) and " + _HO_1115 + " (item 7) list it. "
    "The parent's prior copy is safe in " + _BACKUP + " before `buzzing-growing-whale` goes.\n"
    "- **Done, so no longer open** (v1.15.16): juniper-deploy's pins after the gates (deploy#278, above) and the parent `Juniper/AGENTS.md`'s second edit (ruling 3 of 2026-11-15; XC-P12). "
    "Not the owner's: the publish-artifact fix (above), a session's work under ruling 2 of 2026-11-15.\n"
)
_NOTE_ANCHOR = "\n**R-DC-PATCH's branch.** "
_NOTE_NEW = "\n" + _N_HEAD + _N_ROUND1 + _N_PRS + _N_ROUND2 + _N_1114 + _N_0115 + _N_ECO016 + _N_CUTS + _N_FIND1 + _N_FIND2 + _N_FIND3 + _N_OPEN + "\n**R-DC-PATCH's branch.** "

# --- §5: R-CASCOR's notes, the P12 chain's canopy line, the recommended order ------------------------------------------
_RCASCOR_ANCHOR = (
    "0.12.0 and 0.13.0 shipped on 0.4.1 and 0.7.1, so R-OBS-SC-2 needs a later cascor release to reach a cascor image; R-CASCOR's other gates stand.\n"
)
_RCASCOR_NEW = (
    _RCASCOR_ANCHOR
    + "- **2026-11-15** (v1.15.16): that release is juniper-cascor 0.14.0, cut on ruling 5 of 2026-11-13 (§4 Wave 1, Cascor; " + _FNOTE + "). Its wheel is on PyPI since 05:24Z (ruling 1 of 2026-11-15), and juniper-deploy pins it since deploy#278 (05:48:57Z). "
    "Like 0.12.0 and 0.13.0 it was cut ahead of P3-05 and P3-08, so R-CASCOR's other gates stand, and the fix-forward question with them.\n"
)

_P12_CANOPY_OLD = "Its lock pins observability 0.4.1 (canopy#739), so R-OBS-SC-2 reaches a canopy image only from a later release (canopy#806; v1.15.15).\n"
_P12_CANOPY_NEW = (
    "Its lock pins observability 0.4.1 (canopy#739), so R-OBS-SC-2 reaches a canopy image only from a later release (canopy#806; v1.15.15). "
    "That release is canopy 0.10.0, cut and published 2026-11-15 (v1.15.16).\n"
)

_ORDER3_OLD = "so R-OBS-SC-2 needs a later canopy release too (§4 Wave 1, Canopy; v1.15.15).\n"
_ORDER3_NEW = (
    "so R-OBS-SC-2 needs a later canopy release too (§4 Wave 1, Canopy; v1.15.15). The later canopy release and a cascor release on the new locks are cut "
    "and published (canopy 0.10.0 and cascor 0.14.0, 2026-11-15); R-CASCOR's own gates stand (v1.15.16).\n"
)

_ORDER6_OLD = "6. R-ML-b: shipped with R-ML-a. R-ML-TOOLS followed as 0.11.1 (2026-10-25).\n"
_ORDER6_NEW = "6. R-ML-b: shipped with R-ML-a. R-ML-TOOLS followed as 0.11.1 (2026-10-25), and R-ML-TOOLS-2 as 0.11.5 (2026-11-14; v1.15.16).\n"

_SECOND_CUT_OLD = "The owner may accept that for canopy's P0 (§6 A5, P4 D-4).\n"
_SECOND_CUT_NEW = "The owner may accept that for canopy's P0 (§6 A5, P4 D-4). Canopy's second cut is 0.10.0 (2026-11-15; v1.15.16).\n"

# --- §6 ------------------------------------------------------------------------------------------------------------------
_A5_O13_OLD = "the canopy primary stays open, the owner's answer of 2026-11-06, v1.15.13)"
_A5_O13_NEW = "the canopy primary stays open, the owner's answer of 2026-11-06, v1.15.13; the juniper-ml primary ruled 2026-11-13: guarded session pulls, ruling 7 of 2026-11-13, v1.15.16)"

_A5_D45_OLD = "and D-5 (cascor cut timing; = P6 OD-14, P7 D7's cascor half) |"
_A5_D45_NEW = (
    "and D-5 (cascor cut timing; = P6 OD-14, P7 D7's cascor half). D-4: answered (0.10.0 is the second cut; ruling 5 of 2026-11-13). "
    "D-5: answered for 0.14.0 only; R-CASCOR's own timing after P3-05 and P3-08 stays open (v1.15.16) |"
)

_D03_OLD = "\"This arc opens them\". Who opens the floor PRs was not asked (§5, the note on R-OBS-SC-2).\n"
_D03_NEW = (
    "\"This arc opens them\". Who opens the floor PRs was not asked then. **Ruled 2026-11-09** (round 1, \"In release PRs (Recommended)\"): each consumer's next release PR raises them, "
    "as cascor#758 and canopy#818 did, so P3-17 is answered (v1.15.16; " + _FNOTE + ").\n"
)

_CASCOR012_OLD = "Its PyPI gate (run 38085392643) waits: approving it publishes the 0.12.0 wheel as cut."
_CASCOR012_NEW = "Its PyPI gate (run 38085392643) waited then; PyPI serves 0.12.0 since 2026-10-25."

_FF_ANCHOR = "the fix-forward question stands either way (`EX/round14-laneA-reprobe.md` R14A-01).\n"
_FF_NEW = (
    _FF_ANCHOR
    + "  - Since, cascor 0.13.0 (2026-10-28) and 0.14.0 (2026-11-15, on ruling 5 of 2026-11-13) were cut ahead of the same gates, "
    "so the question is whether a fix-forward is owed for cascor 0.12.0–0.14.0 (v1.15.16; §4 Wave 1, Cascor).\n"
)

_TRIO_OLD = "and `JuniperCascor1` imports the juniper-ml primary's code (Security step 5).\n- **R-OBS-SC-2's follow-ups** (v1.15.15; §5, the note on R-OBS-SC-2):\n"
_TRIO_NEW = (
    "and `JuniperCascor1` imports the juniper-ml primary's code (Security step 5). The upgrade is still the owner's on 2026-11-15, and the restart's condition is that of ruling 6 of 2026-11-13 (v1.15.16).\n"
    "- **R-OBS-SC-2's follow-ups** (v1.15.15; §5, the note on R-OBS-SC-2), **all ruled** by 2026-11-13 (v1.15.16; " + _FNOTE + "):\n"
)

_FU1_OLD = "which `JuniperCascor1` imports (O13 names four other primaries);\n"
_FU1_NEW = "which `JuniperCascor1` imports (O13 names four other primaries): ruled 2026-11-13, \"Probe per environment\" (ruling 6 of 2026-11-13) and \"Guarded session pulls (Recommended)\" (ruling 7 of 2026-11-13);\n"

_FU2_OLD = "and juniper-ml 0.11.5 for the `[tools]` floor;\n"
_FU2_NEW = "and juniper-ml 0.11.5 for the `[tools]` floor: ruled 2026-11-09, \"In release PRs (Recommended)\" and \"Floor PR, then 0.11.5 (Recommended)\"; 0.11.5 is published (2026-11-14);\n"

_FU3_OLD = "data#454's telemetry opt-out for cascor and canopy, and when R-OBS-SC-3 (0.4.3) is designed.\n"
_FU3_NEW = (
    "data#454's telemetry opt-out for cascor and canopy, and when R-OBS-SC-3 (0.4.3) is designed: all ruled, and the first two done. `APD-ECO-016` is filed FIXED (ml#2576), "
    "the opt-outs merged (cascor#755, canopy#816), and the design goes to its own thread (ruling 4 of 2026-11-13), whose start prompt landed with ml#2568.\n"
    "- **Left with the owner by R-OBS-SC-2's follow-ups** (v1.15.16; " + _FNOTE + "): the juniper-deploy stack's restart (deploy#278 pinned both images) and whether its recurrence pin moves; "
    "launching the 0.4.3 design session; the trio's upgrade, then its restart on ruling 6 of 2026-11-13's condition; "
    "the canopy primary (O13); cascor 0.12.0–0.14.0's fix-forward (above); A1's open limbs (§6 A1); the v2 draft's pointer; and the worktree housekeeping.\n"
    "  - Done since: juniper-deploy's pins (deploy#278) and the parent `Juniper/AGENTS.md`'s second edit (ruling 3 of 2026-11-15).\n"
)

_XCS_OLD = "the owner's environment upgrade and the session's recorded pass (Wave 1's Security step 5;"
_XCS_NEW = "the owner's environment upgrade and the session's recorded pass, which ruling 6 of 2026-11-13 makes the per-lock probe re-run in each environment, on P3-05 and with blank DSNs (Wave 1's Security step 5;"

# --- §7.1 ------------------------------------------------------------------------------------------------------------------
_S71_OLD = "Next, the ledger's Phase 12, in its own rounds (`…phase12-owed.md`)\n"
_S71_NEW = (
    "Next, the ledger's Phase 12, in its own rounds (`…phase12-owed.md`)\n"
    "19. R-OBS-SC-3's 0.4.3 design (ruling 4 of 2026-11-13): its own session, which the owner launches from " + _PROMPT + ", writes it and runs its rounds (v1.15.16) **S**\n"
)

# --- §8, §9, §12, Appendix A -----------------------------------------------------------------------------------------------
_EXTRAS_OLD = "and the `[servers]` floors (ml#2326), released as 0.11.2 (R-ML-SERVERS, §5) |"
_EXTRAS_NEW = "and the `[servers]` floors (ml#2326), released as 0.11.2 (R-ML-SERVERS, §5), and ml#2555's `[tools]` floors, as 0.11.5 |"

#: The JuniperCascor1 row sits at 506 characters, so the pulls it once covered are stated below the table.
_OWNER_ONLY_OLD = "| Owner-only changes, made outside §7.2's windows, and coordinated so that one restart can serve several |"
_OWNER_ONLY_NEW = "| Owner-only env changes, made outside §7.2's windows, and coordinated so that one restart can serve several |"

_S8_ANCHOR = "| The `HO/` archive | P9-04/15, P10-01, P2-27 | Use the post-ml#2117 paths |\n\n"
_S8_NEW = (
    _S8_ANCHOR
    + "**Since v1.15.16**: the `JuniperCascor1` row's \"Owner-only\" covers environment changes. Pulls of the primaries its editable installs map follow O13: guarded session pulls for cascor, data, data-client and recurrence "
    "and, since ruling 7 of 2026-11-13, juniper-ml (on `main` and clean, never a branch switch); canopy's is open.\n"
    "In the juniper-deploy `docker-compose.yml` row: deploy#278 moved cascor and canopy (2026-11-15) and left `:598` at `juniper-recurrence:0.8.0` while 0.8.1 is published (2026-11-06); whether it moves is the owner's.\n\n"
)

_DEP_IMAGE_OLD = "and canopy's after R-CANOPY-A's 0.9.0 |\n"
_DEP_IMAGE_NEW = "and canopy's after R-CANOPY-A's 0.9.0. Cascor's and canopy's are pinned (deploy#278, 2026-11-15; v1.15.16) |\n"

_DEP_TRIO_OLD = "`JuniperCascor1` already imports its code from the juniper-ml primary, and the other two need the upgrade |\n"
_DEP_TRIO_NEW = "`JuniperCascor1` already imports its code from the juniper-ml primary, and the other two need the upgrade. The pass is the per-lock probe per environment, on P3-05 with blank DSNs (ruling 6 of 2026-11-13) |\n"

_CUTAHEAD_OLD = "and canopy#740 proposed canopy 0.9.0 (open) |\n"
_CUTAHEAD_NEW = "and canopy#740 proposed canopy 0.9.0 (open). Since: cascor 0.13.0 and 0.14.0 were cut ahead of P3-05 and P3-08 too, and canopy 0.9.0 and 0.10.0 without P3-06 (v1.15.16) |\n"

_RISK_OLD = "each consumer's next release, pin and restart |\n"
_RISK_NEW = "each consumer's next release, pin and restart (cascor's and canopy's are published, 2026-11-15; v1.15.16) |\n"

_RISK2_OLD = "image published 20:56Z, PyPI at the gate) | §5's \"Ready when\"; the owner's fix-forward ruling (R-OBS-SC-2, R-DATA-2; cascor's at the mid-wave sitting) |\n"
_RISK2_NEW = (
    "image published 20:56Z, PyPI at the gate); then cascor 0.13.0 and 0.14.0, cut ahead of P3-05 and P3-08, and canopy 0.9.0 and 0.10.0, cut without P3-06 (v1.15.16) "
    "| §5's \"Ready when\"; the owner's fix-forward ruling (R-OBS-SC-2, R-DATA-2; cascor's at the mid-wave sitting) |\n"
)

_SENTRY_SUPPORT_OLD = "Phase C status, the trio, whether running services send to Sentry,"
_SENTRY_SUPPORT_NEW = (
    "Phase C status, the trio (stopped on 2026-11-15, its environments read in place; v1.15.16), whether running services send to Sentry "
    "(juniper-deploy's containers were read by DSN name on 2026-11-12, all empty; the canopy E2E legs were not),"
)

_GHCR_OLD = "- GHCR images.\n"
_GHCR_NEW = "- GHCR images, except cascor 0.14.0's and canopy 0.10.0's: pulled by index digest and run with no network on 2026-11-15 (" + _FNOTE + ").\n"

_T1_OLD = (
    "P3-17 (D-02 ruled 2026-10-10; D-03 ruled 2026-11-08 for the lock PRs, its floor part unasked), "
    "P3-18 →R-OBS-SC + image lock PRs (both lock rounds are done, four PRs each on 2026-10-10 and 2026-11-09; the floors are open)"
)
_T1_NEW = (
    "P3-18 →R-OBS-SC + image lock PRs (both lock rounds are done, four PRs each on 2026-10-10 and 2026-11-09; "
    "the floors moved in cascor#758 and canopy#818, and data's and recurrence's wait for their release PRs)"
)

_DONE_OLD = "  - **Done**: P3-20 (= P2-01, ml#2157); P3-07 (ml#2523, 2026-11-08; v1.15.15)\n"
_DONE_NEW = (
    "  - **Done**: P3-20 (= P2-01, ml#2157); P3-07 (ml#2523, 2026-11-08; v1.15.15); "
    "P3-17, asked and answered (D-02 on 2026-10-10; D-03 on 2026-11-08 for the lock PRs and 2026-11-09 for the floors; v1.15.16)\n"
)

# --- Validation record and "Changed by this plan" ------------------------------------------------------------------------
_VALIDATION_ANCHOR = "They found 1 BLOCKER (the draft read as if 0.4.2 ended the Sentry exposure), 8 MAJORs, 9 MINORs and 7 NITs, some found by both; this version applies them.\n"
_VALIDATION_NEW = (
    _VALIDATION_ANCHOR
    + "  - v1.15.16 is a record of R-OBS-SC-2's follow-ups (2026-11-09 to 2026-11-15). No round checks it (owner ruling 2026-10-24). "
    "Its rulings are dated from seven sessions' transcripts, the arc's six (`b9dfa450` among them) and flood-4's `f2b4e7c3` (`util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py`; "
    "the two answers it prints as `None` are dated from the `user` entries that carry them), and the owner's directive of 2026-11-15 from `b9dfa450`'s.\n"
    "    - `util/ad-hoc/2026-11-15_r_obs_sc_2_followups_record_reprobe.py` re-checked these on 2026-11-15 (0 FAIL): the PRs' states, merge commits, times and files; the canopy PRs' and the fixes' ancestry in `v0.10.0` and `v0.14.0`; "
    "the three Releases' tags; the three publish runs' jobs, approvals and `pending_deployments`, the two image runs, GHCR's tags and the images' revision labels; PyPI's and TestPyPI's files (cascor 0.13.0's and 0.14.0's member by member, canopy 0.10.0's by sha256);\n"
    "      - the floors (0.11.5's `[recurrence]` one among them), the caps and juniper-deploy's pins on `main` (`docker-compose.yml:598` among them, against GHCR's highest recurrence tag and the stale-pin check's lines); "
    "the register's `APD-ECO-016` rows; run 43669737463; the source lines each finding cites; "
    "the service-core commits past `juniper-service-core-v0.7.2` at `eeb5c694`; the v2 draft's stale lines; the archived reviews' tallies and the archive's `--check`; and the owner's answers and directive.\n"
    "      - since the gates: deploy#278 and deploy `main`'s pins (cascor 0.14.0 twice, canopy 0.10.0 three times, both helm tags), GHCR's highest cascor and canopy tags against them, "
    "the parent `Juniper/AGENTS.md`'s sha256 and both 2026-11-15 copies', and the 2026-11-15 dialog's three labels and times.\n"
    "    - The two `pypi` gates and the recurrence pin move, so the probe accepts either state and prints the one it read: on its run of 2026-11-15 " + _GATE_READ + ", "
    "both gates PUBLISHED and the recurrence pin BEHIND. "
    "The trio's environments and ports, the primary's reflog, the parent `Juniper/AGENTS.md` and its copies were read in place, read-only. The memory records were read by hand, and the option texts from the transcripts.\n"
    "    - Two independent Opus reviews read the first draft (session `b9dfa450`): a fact-check (agent `a26341d463f77d37d`: 1 BLOCKER, the canopy review tally; 3 MAJORs, 3 MINORs and 10 NITs) "
    "and an adversarial read (agent `a1665ffe2f43192ea`: 1 BLOCKER, `JuniperCascor1` \"Unchanged\"; 9 MAJORs, 19 MINORs and 9 NITs).\n"
    "      - Every finding of both is applied, each re-checked at its source first, and none is declined. Both are archived, briefs and reports, in " + _REVIEWS + ", "
    "beside the four other reviews v1.15.16 cites (the guard's two and the release bodies' two) and the five PRs' fix pass.\n"
)

_SCRIPTS_OLD = "    - and with v1.15.15's, `2026-11-09_consolidated_plan_v1_15_15_r_obs_sc_2_shipped.py`,"
_SCRIPTS_NEW = "    - with v1.15.15's, `2026-11-09_consolidated_plan_v1_15_15_r_obs_sc_2_shipped.py`,"

_LOCKS_ANCHOR = (
    "      - and the second lock round's eight, each named `2026-11-09_lock_round_2_` and then `fetch_consumers.py`, `facts.py`, `env_record.py`, `probe.py`, `run_probes.py`, "
    "`refresh.py`, `changelog_insert.py` or `tested_section.py`;\n"
)
_LOCKS_NEW = (
    _LOCKS_ANCHOR
    + "    - and with v1.15.16's, `2026-11-15_consolidated_plan_v1_15_16_r_obs_sc_2_followups.py` (the writer) and `2026-11-15_r_obs_sc_2_followups_record_reprobe.py` (the re-probe), and eight tools of session `b9dfa450`:\n"
    "      - `2026-11-15_archive_r_obs_sc_2_reviews.py`, which ran and built the reviews' archive (below), and whose `--check` passes;\n"
    "      - `2026-11-15_probe_published_images_cascor_0_14_0_canopy_0_10_0.py`, which ran at 03:33Z (exit 0); and `2026-11-15_verify_cascor_0_14_0_canopy_0_10_0_published.py`, "
    "which ran on TestPyPI (all PASS) and on `--control` (the floors and the round-up FAIL, as designed), and, after both gates, against PyPI (05:41:45Z, 0 failed checks);\n"
    "      - `2026-11-15_image_lock_moves_cascor_canopy.py`, which ran (cascor's CPU lock: 17 pins moved and `six` dropped; canopy's: 21 moved and `lazy-importer` added); "
    "and `2026-11-15_deploy_pin_cascor_0_14_0_canopy_0_10_0.py`, which ran on base `6c9e57f8` and produced juniper-deploy#278;\n"
    "      - `2026-11-15_pre_push_gate_run.bash`, which ran the pre-push gate for #278 and for this plan's PR (PASS both); `2026-11-15_masked_read_random_token_triage.py`, which triaged the masked `--all` read of the review archive (54 random-looking tokens: 40 parts of repository paths, 11 commit shas, 3 path-shaped; none a credential); and `2026-11-15_parent_agents_released_paragraph_cascor_0_14_0_canopy_0_10_0.py`, which ran and made the parent edit (XC-P12);\n"
    "      - and the follow-ups' own tools, landed with their PRs: ml#2555's six `2026-11-12_` tools, `tools_floors_observability_0_4_2_service_core_0_7_2.py`, `run_with_blank_sentry_dsns.py`, "
    "`fastapi_telemetry_opt_out_mutation_check.py`, `fork_retry_after_round_up_mutation_check.py`, `upload_set_hashes.py` and `rehome_worktree_edits_on_new_main.py`; and ml#2576's `2026-11-12_retry_after_guard_mutation_check.py`;\n"
    "      - ml#2558's `2026-11-13_juniper_ml_0_11_5_cut_cochanges.py` and `2026-11-13_juniper_ml_0_11_5_security_notes_header.py`; and ml#2568's `2026-11-14_cascor_canopy_release_cochanges.py`, "
    "`2026-11-14_parent_agents_released_paragraph_0_11_5.py`, `2026-11-15_cascor_0_14_0_canopy_0_10_0_security_notes_header.py` and `2026-11-15_cascor_canopy_release_notes_corrections.py`;\n"
)

_HANDOFFS_ANCHOR = (
    "and the session's own, `HO/HANDOFF_2026-11-09_r-obs-sc-2-recorded-plan-v1-15-15-owner-items-next.md` (not this plan's).\n"
)
_HANDOFFS_NEW = (
    _HANDOFFS_ANCHOR
    + "  - R-OBS-SC-2's follow-up handoffs, each landed by its own PR (not this plan's): " + _HO_RULED + " (ml#2546), `…five-prs-validated-opening-next.md` (ml#2556), "
    + _HO_1113 + " (ml#2563, and its 2026-11-14 update, ml#2565) and " + _HO_1115 + " (ml#2574).\n"
    "  - with v1.15.16's PR, the reviews' archive " + _REVIEWS + ", 14 files: its `README.md`, six reviews' briefs and reports, and the five PRs' fix pass, built by `util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py`.\n"
)

_CREATED_ANCHOR = (
    "  - by session `f58cf63e` (2026-11-08), recorded with v1.15.15, the auto-memory file `reference_host_grep_is_ugrep_honouring_ignore_files.md` (the host's `grep` is ugrep, which honours `.gitignore`).\n"
)
_CREATED_NEW = (
    _CREATED_ANCHOR
    + "  - by session `218ff61e` (2026-11-13), recorded with v1.15.16, the auto-memory file `reference_owner_dialog_blocks_the_session.md` (an owner dialog blocks the session until it is answered).\n"
)

_MEMORY_ANCHOR = (
    "  - by session `09366253` (2026-11-09), with v1.15.15: `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description); this session did not change `MEMORY.md`.\n"
)
_MEMORY_NEW = (
    _MEMORY_ANCHOR
    + "  - by R-OBS-SC-2's follow-up sessions, recorded with v1.15.16 (their transcripts' Write and Edit calls and memory-writing commands): "
    "by `a4e1e914` (2026-11-12), `project_recurrence_equities_p0_arc_2026-10-04.md` and `feedback_validate_handoff_prompts_independently.md`; "
    "by `7d425759` (2026-11-14), `project_recurrence_equities_p0_arc_2026-10-04.md`.\n"
    "    - by `6e3bdef0` (2026-11-13, one command at 00:50:27Z): `reference_commit_pr_mechanics_hub.md`, `reference_mutation_check_stale_pyc_and_piped_exit.md` "
    "and `reference_subagents_killed_by_session_limit_resume_with_sendmessage.md`; it read `MEMORY.md` but did not change it.\n"
    "    - by `218ff61e` (2026-11-13): `reference_release_train_ceremony_traps_2026-09-09.md` (a section appended) and `MEMORY.md` (a line appended, for its new file).\n"
    "    - by `1b4fec84` (2026-11-14 23:54:29Z): the parent `Juniper/AGENTS.md` (juniper-ml 0.11.5, observability 0.4.2 and service-core 0.7.2, the re-probe date; sha256 `90df2783…` → `f3f69b34…`), "
    "whose prior copy is `tmp/s2/parent_AGENTS_before_2026-11-14.md` in worktree `buzzing-growing-whale`.\n"
    "      - and on 2026-11-15 (one command at 02:53:56Z): `reference_worktree_isolated_session_command_refusals.md` (a bullet inserted before its index digest) "
    "and `reference_commit_pr_mechanics_hub.md` (a bullet appended); it did not change `MEMORY.md`.\n"
    "    - by session `b9dfa450` (2026-11-15), with v1.15.16: " + _BACKUP + " (new: the same bytes as that prior copy, sha256 `90df2783…`); "
    "the parent `Juniper/AGENTS.md` (05:49:09Z, `f3f69b34…` → `3009c3f4…`; XC-P12), with both copies in " + _BACKUP2 + " (new).\n"
)

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.15\n", "- **Version**: 1.15.16\n"),
    (_STATUS_ANCHOR, _STATUS_NEW),
    (_DOCS_ANCHOR, _DOCS_NEW),
    (_OV_CUT_OLD, _OV_CUT_NEW),
    (_OV_TOOLS_OLD, _OV_TOOLS_NEW),
    (_P2_OLD, _P2_NEW),
    (_P3_OLD, _P3_NEW),
    (_P4_OLD, _P4_NEW),
    (_P12_OLD, _P12_NEW),
    (_PASS_OLD, _PASS_NEW),
    (_ENVS_OLD, _ENVS_NEW),
    (_PROBE_OLD, _PROBE_NEW),
    (_SENTRY_PROBED_OLD, _SENTRY_PROBED_NEW),
    (_CANOPY_620_OLD, _CANOPY_620_NEW),
    (_CANOPY_630_OLD, _CANOPY_630_NEW),
    (_O13_OLD, _O13_NEW),
    (_PARENT_OLD, _PARENT_NEW),
    (_QS_OLD, _QS_NEW),
    (_XCP12_ANCHOR, _XCP12_NEW),
    (_A1_683_OLD, _A1_683_NEW),
    (_ACTION6_OLD, _ACTION6_NEW),
    (_SIT6_OLD, _SIT6_NEW),
    (_A5_ITEM_OLD, _A5_ITEM_NEW),
    (_S011_TEL_OLD, _S011_TEL_NEW),
    (_STEP2_OLD, _STEP2_NEW),
    (_STEP5_RUN_OLD, _STEP5_RUN_NEW),
    (_STEP5_PASS_OLD, _STEP5_PASS_NEW),
    (_STEP5_O13_OLD, _STEP5_O13_NEW),
    (_STEP5_OLD, _STEP5_NEW),
    (_CASCOR_ANCHOR, _CASCOR_NEW),
    (_CANOPY_OLD, _CANOPY_NEW),
    (_SC3_OLD, _SC3_NEW),
    (_RCASCOR_ROW1_OLD, _RCASCOR_ROW1_NEW),
    (_RCASCOR_ROW2_OLD, _RCASCOR_ROW2_NEW),
    (_ROW_ANCHOR, _ROW_NEW),
    (_STAY_OLD, _STAY_NEW),
    (_PLAN_OLD, _PLAN_NEW),
    (_IMAGE_OLD, _IMAGE_NEW),
    (_CASCOR_SUB_OLD, _CASCOR_SUB_NEW),
    (_CANOPY_SUB_OLD, _CANOPY_SUB_NEW),
    (_TRIO_SUB_OLD, _TRIO_SUB_NEW),
    (_FOLLOW_OLD, _FOLLOW_NEW),
    (_TOOLS_OLD, _TOOLS_NEW),
    (_RL_OLD, _RL_NEW),
    (_TEL_OLD, _TEL_NEW),
    (_NOTE_ANCHOR, _NOTE_NEW),
    (_RCASCOR_ANCHOR, _RCASCOR_NEW),
    (_P12_CANOPY_OLD, _P12_CANOPY_NEW),
    (_ORDER3_OLD, _ORDER3_NEW),
    (_ORDER6_OLD, _ORDER6_NEW),
    (_SECOND_CUT_OLD, _SECOND_CUT_NEW),
    (_A5_O13_OLD, _A5_O13_NEW),
    (_A5_D45_OLD, _A5_D45_NEW),
    (_D03_OLD, _D03_NEW),
    (_CASCOR012_OLD, _CASCOR012_NEW),
    (_FF_ANCHOR, _FF_NEW),
    (_TRIO_OLD, _TRIO_NEW),
    (_FU1_OLD, _FU1_NEW),
    (_FU2_OLD, _FU2_NEW),
    (_FU3_OLD, _FU3_NEW),
    (_XCS_OLD, _XCS_NEW),
    (_S71_OLD, _S71_NEW),
    (_EXTRAS_OLD, _EXTRAS_NEW),
    (_OWNER_ONLY_OLD, _OWNER_ONLY_NEW),
    (_S8_ANCHOR, _S8_NEW),
    (_DEP_IMAGE_OLD, _DEP_IMAGE_NEW),
    (_DEP_TRIO_OLD, _DEP_TRIO_NEW),
    (_CUTAHEAD_OLD, _CUTAHEAD_NEW),
    (_RISK_OLD, _RISK_NEW),
    (_RISK2_OLD, _RISK2_NEW),
    (_SENTRY_SUPPORT_OLD, _SENTRY_SUPPORT_NEW),
    (_GHCR_OLD, _GHCR_NEW),
    (_T1_OLD, _T1_NEW),
    (_DONE_OLD, _DONE_NEW),
    (_VALIDATION_ANCHOR, _VALIDATION_NEW),
    (_SCRIPTS_OLD, _SCRIPTS_NEW),
    (_LOCKS_ANCHOR, _LOCKS_NEW),
    (_HANDOFFS_ANCHOR, _HANDOFFS_NEW),
    (_CREATED_ANCHOR, _CREATED_NEW),
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
