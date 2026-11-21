#!/usr/bin/env python3
"""Consolidated development plan v1.15.14 -> v1.15.15: R-OBS-SC-2, from P3-07 to the second lock round, and what it leaves.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: ml#2523 (P3-07), ml#2524 (ml#2514 carried), ml#2525 / ml#2526 (the proposals), ml#2527 / ml#2528 (the archives);
         publish runs 42500706778 (observability 0.4.2) and 42499466753 (service-core 0.7.2); data#525, cascor#748,
         canopy#806 and recurrence#233 (the second lock round);
         util/ad-hoc/2026-11-09_r_obs_sc_2_record_reprobe.py (the facts, re-probed) and
         util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py (the rulings, from the transcripts);
         util/ad-hoc/2026-11-07_consolidated_plan_v1_15_14_juniper_ml_0_11_4_published.py (the pattern)

Why
---
v1.15.14 left R-OBS-SC-2 owed: §5's row, Wave 1's "Security delivery" steps 1-5, the Wave 1 exit list, §9 and §2 all
wait on P3-07 and the cut. Four sessions then ran it (2026-11-08 and 2026-11-09): P3-07 merged after three validation
rounds, ml#2514 was carried, observability 0.4.2 and service-core 0.7.2 were cut and published at the owner's approval
of both `pypi` gates, and the second lock round merged in all four consumers, each PR carrying the per-lock probe the
owner ruled in place of S0.11's relay run, whose tests are unwritten.

This revision records that, the owner's rulings (P3 D-03's lock-PR part among them: its answer, "This arc opens them",
is in session e97264c3's transcript, though the 2026-11-09 handoff said it had none), and what R-OBS-SC-2 leaves:

- 0.4.2 does not end XC-SENTRY: query strings, Sentry Logs and exception values wait for 0.4.3 (a new §5 row,
  R-OBS-SC-3, on the owner's ruling of 2026-11-08);
- no consumer has cut a release from the new locks, so no running image carries the fix;
- the trio's environments differ: JuniperData and JuniperCanopy1 hold observability 0.4.0 and service-core 0.5.0, while
  JuniperCascor1 imports both, as editable installs, from the juniper-ml primary, whose tree held 0.4.2's and 0.7.2's
  code on 2026-11-09 (probed read-only in each environment);
- D-03's floor-PR part was never asked, so P3-17 stays open; the follow-ups go to §6's mid-wave sitting.

Two independent agents reviewed the first draft (a fact re-probe, and an adversarial read of its conclusions and scope);
this version applies their findings.

Usage
-----
    python3 util/ad-hoc/2026-11-09_consolidated_plan_v1_15_15_r_obs_sc_2_shipped.py [--root DIR] [--check]

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

_NOTE = "§5, the note on R-OBS-SC-2"

# --- Header -------------------------------------------------------------------------------------------------------
_DATE_OLD = "0.11.4's publish, and the parent `AGENTS.md` paragraph it moves, probed 2026-11-07)\n"
_DATE_NEW = "0.11.4's publish, and the parent `AGENTS.md` paragraph it moves, probed 2026-11-07; R-OBS-SC-2's cut, publish, second lock round and the trio's environments probed 2026-11-09)\n"

_STATUS_ANCHOR = "  - Planning only: this plan changes no code,"
_STATUS_NEW = (
    "  - v1.15.15 (2026-11-09) records R-OBS-SC-2 from P3-07 to the second lock round: P3-07 merged after three validation rounds (ml#2523), ml#2514's `Retry-After` fix carried (ml#2524), "
    "observability 0.4.2 and service-core 0.7.2 cut on 2026-11-08 and published on 2026-11-09 when the owner approved both `pypi` gates, "
    "and the second lock round merged in all four consumers (data#525, cascor#748, canopy#806, recurrence#233). Like v1.15.0, no round checks it.\n"
    "    - It records the owner's rulings of 2026-11-08 and 2026-11-09, and what R-OBS-SC-2 leaves: query strings, Sentry Logs and exception values wait for 0.4.3 (R-OBS-SC-3); "
    "no consumer has cut a release from the new locks; and the trio's environments differ (Overview; §2; XC-SENTRY; XC-P12; §4; §5; §6; §7; §8; §9; §12; Appendix A).\n"
    "  - Planning only: this plan changes no code,"
)

# --- Overview 2 (Sentry key capture) and 3 (the release train) --------------------------------------------------------
_OV_PRS_OLD = "     - None of round 42's F-fixes is written. Three PRs are owed: juniper-ml with service-core, cascor, and data (P3).\n"
_OV_PRS_NEW = (
    "     - Three PRs were owed for round 42's F-fixes (P3): juniper-ml with service-core (P3-07), cascor (P3-08) and data (P3-09). "
    "P3-07 merged on 2026-11-08 (ml#2523) and ships in R-OBS-SC-2 (v1.15.15); P3-08 and P3-09 have no PR, nor does P3-03, which P3-09 follows (2026-11-09).\n"
)

_OV_LOCKS_OLD = "which stop frame-local capture but not F2 (§5).\n"
_OV_LOCKS_NEW = (
    "which stop frame-local capture but not F2 (§5). "
    "The second lock round moved all five locks to 0.4.2 and 0.7.2 on 2026-11-09 (§5), which stop F2 and the header and cookie leaks found beside it, "
    "but not query strings, Sentry Logs or exception values (0.4.3; v1.15.15).\n"
)

_OV_EXPOSED_OLD = "     - So a running service stays exposed until its image lock or its environment moves to R-OBS-SC-2 and it restarts.\n"
_OV_EXPOSED_NEW = (
    "     - So a running service stays exposed to F2 until it runs an environment holding R-OBS-SC-2, or an image built from a lock on it, and restarts; an image also needs a release and juniper-deploy's pin, "
    "and no consumer has cut a release from the new locks. Even then, 0.4.2 leaves query strings, Sentry Logs and exception values to 0.4.3, so XC-SENTRY's (a) and (b) stay in force (§4 Wave 1; §5; v1.15.15).\n"
)

_OV_TRAIN_OLD = "The fix-forwards are still owed: PyPI has no observability 0.4.2, service-core 0.7.2 or data fix-forward (R-DATA-2, which the owner ruled 0.18.0 on 2026-11-03; §5).\n"
_OV_TRAIN_NEW = (
    "PyPI serves R-OBS-SC-2's fix-forwards, observability 0.4.2 and service-core 0.7.2, since 2026-11-09 (v1.15.15); "
    "the data fix-forward is still owed (R-DATA-2, which the owner ruled 0.18.0 on 2026-11-03; §5).\n"
)

# --- §2 ------------------------------------------------------------------------------------------------------------
_P3_OLD = (
    "| P3 defect register | None of the round-42 F-fixes is written. observability 0.4.1, service-core 0.7.1 and data 0.17.0 shipped without P3-07, P3-03 and P3-09, "
    "and the fix-forwards are owed (owner ruling 2026-10-10; §5)."
)
_P3_NEW = (
    "| P3 defect register | P3-07 merged on 11-08 (ml#2523) and shipped in R-OBS-SC-2 (observability 0.4.2, service-core 0.7.2; 11-09). "
    "data 0.17.0 shipped without P3-03 and P3-09, and R-DATA-2 is owed (owner ruling 2026-10-10; §5)."
)

#: §2's P4 row sits at 508 characters, so the sentence grows by 10 and the "Next item" cell shrinks by 12.
_P4_OLD = "R-OBS-SC-2 and R-DATA-2 are owed. P4's Wave 4 waits on Docker Hub secrets (10-10). | §5 (the fix-forwards) | T1 |"
_P4_NEW = "R-OBS-SC-2 shipped 11-09; R-DATA-2 is owed. P4's Wave 4 waits on Docker Hub secrets (10-10). | §5's cuts | T1 |"

# --- XC-SENTRY and XC-P12 ------------------------------------------------------------------------------------------------
_PATH_OLD = "Images move with their lock PRs; the trio's conda environments move only when upgraded and restarted."
_PATH_NEW = (
    "Images move with their lock PRs, then a release cut from them and juniper-deploy's pin; the trio's conda environments move only when upgraded and restarted "
    "(`JuniperCascor1`'s observability and service-core move with the juniper-ml primary's checkout, being editable installs of it since W0.1; XC-P12)."
)

_LOGS_OLD = "(observability 0.4.0 and 0.4.1 send log records: `enable_logs=True`, `sentry.py` L135);"
_LOGS_NEW = "(observability 0.4.0 to 0.4.2 send log records: `enable_logs=True`, `sentry.py` L135 in 0.4.1 and L186 in 0.4.2);"

_SENTRY_ANCHOR = "whether the trio takes them now as well is the owner's (mid-wave sitting).\n\n**Every session**"
_SENTRY_NEW = (
    "whether the trio takes them now as well is the owner's (mid-wave sitting).\n\n"
    "**R-OBS-SC-2 is on PyPI since 2026-11-09** (v1.15.15) and in every consumer lock, so the 0.4.1-first choice is moot, but it does not end this item. "
    "0.4.2 leaves query strings (canopy's `?api_key=`, sent under the default `send_pii=False`), Sentry Logs and exception values to 0.4.3 (R-OBS-SC-3), so (a) and (b) stay in force.\n\n"
    "- The trio's environments differ: `JuniperData` and `JuniperCanopy1` hold observability 0.4.0 and service-core 0.5.0 and need the upgrade, "
    "while `JuniperCascor1` imports 0.4.2's and 0.7.2's code from the juniper-ml primary (§4 Wave 1, Security step 5).\n"
    "- Whether the per-lock probe may stand in for S0.11's relay run at the restart is the owner's (§6, mid-wave sitting).\n\n"
    "**Every session**"
)

_LOCKGATE_OLD = "- **R-DATA-2's lock gate stands**: data's second image lock PR follows R-OBS-SC-2, so 0.18.0 waits for observability 0.4.2 and service-core 0.7.2 on PyPI (§5).\n"
_LOCKGATE_NEW = (
    "- **R-DATA-2's lock gate stands**: data's second image lock PR follows R-OBS-SC-2, so 0.18.0 waits for observability 0.4.2 and service-core 0.7.2 on PyPI (§5). "
    "**Met 2026-11-09** (v1.15.15): both are on PyPI, and data#525 merged.\n"
)

# --- §4 Wave 0: S0.4 ------------------------------------------------------------------------------------------------------
_S04_OLD = "  1. P3-07: juniper-ml F2 `before_send_transaction`, F6, F9 and F10, plus service-core F3 and F5.\n"
_S04_NEW = (
    "  1. P3-07: juniper-ml F2 `before_send_transaction`, F6, F9 and F10, plus service-core F3 and F5. "
    "**Merged 2026-11-08** as ml#2523, after rounds short of §7.1's top cell (v1.15.15; " + _NOTE + ").\n"
)

# --- §4 Wave 1: Security delivery ----------------------------------------------------------------------------------------
_STEP1_OLD = "1. P3-07 validated and merged.\n"
_STEP1_NEW = "1. P3-07 validated and merged. **Merged 2026-11-08**: ml#2523 (`a67061bd`), after rounds of three, two and one agents, short of §7.1's top cell (" + _NOTE + ").\n"

_STEP2_OLD = "2. Mid-wave sitting: P3 D-03. D-02's version is set by the owner's ruling of 2026-10-10: a patch, which every consumer cap admits, so no cap PR comes first.\n"
_STEP2_NEW = (
    "2. Mid-wave sitting: P3 D-03. D-02's version is set by the owner's ruling of 2026-10-10: a patch, which every consumer cap admits, so no cap PR comes first. "
    '**Ruled 2026-11-08 for the lock PRs**: "This arc opens them" (step 4). Who opens the floor PRs was not asked (' + _NOTE + ").\n"
)

_STEP3_OLD = "3. **R-OBS-SC-2**: observability 0.4.2 and service-core 0.7.2 (§5).\n"
_STEP3_NEW = (
    "3. **R-OBS-SC-2**: observability 0.4.2 and service-core 0.7.2 (§5). "
    '**Shipped 2026-11-09**: a session cut both on 2026-11-08 on the owner\'s "Approve both cuts", where §5\'s rules have the owner cut, '
    "and they were published when the owner approved both `pypi` gates.\n"
)

_STEP4_OLD = (
    "4. The second lock round: each consumer's **image** lock PR (P3-18), each carrying S0.11's relay run. "
    "Cascor moves both `requirements.lock` and `requirements-cpu.lock`.\n"
)
_STEP4_NEW = (
    "4. The second lock round: each consumer's **image** lock PR (P3-18), each carrying S0.11's relay run. "
    "Cascor moves both `requirements.lock` and `requirements-cpu.lock`. "
    "**Merged 2026-11-09**: data#525, cascor#748, canopy#806 and recurrence#233, each carrying the per-lock probe the owner ruled in place of S0.11's relay run, whose tests are unwritten (§5). "
    "It came before any data-client fix; if A1 accepts one, another lock PR follows its release.\n"
)

_STEP5_ANCHOR = "so this applies again only if it restarts before the upgrade.\n"
_STEP5_NEW = (
    "so this applies again only if it restarts before the upgrade.\n"
    "   - **2026-11-09** (v1.15.15): R-OBS-SC-2 is on PyPI, so the 0.4.1-first option is moot, and step 4's PRs carried the per-lock probe, not S0.11's run. "
    "The environments differ: `JuniperData` (its `python3.14t`) and `JuniperCanopy1` hold observability 0.4.0 and service-core 0.5.0 from PyPI, and need the upgrade.\n"
    "   - `JuniperCascor1` holds both as editable installs of the juniper-ml primary (W0.1, 2026-11-04; XC-P12). On 2026-11-09 that checkout, on another session's feature branch, held 0.4.2's and 0.7.2's code, while pip reported 0.4.1 and 0.7.1. "
    "So its input is that checkout, not PyPI: record the commit it runs, not pip's version. O13 does not name the juniper-ml primary, so who may move it is open (§6).\n"
    "   - The restart waits for a recorded pass of S0.11's relay tests, which are unwritten: canopy's needs no A1 ruling, while the data-client and cascor parts wait on A1's open limbs. "
    "A pass for cascor and canopy may also need those fixes or 0.4.3, since 0.4.2 does not scrub exception values. Whether the per-lock probe may stand in is the owner's (§6).\n"
)

# --- §4 Wave 1: the F-S10 images route, Data, Cascor, Canopy, exit --------------------------------------------------------
_IMAGES_OLD = "picks up R-DC-PATCH only if it is on PyPI before its PRs open; otherwise another lock PR follows.\n"
_IMAGES_NEW = "picks up R-DC-PATCH only if it is on PyPI before its PRs open; otherwise another lock PR follows. It was not (v1.15.15).\n"

_DATA5_OLD = "the second follows R-OBS-SC-2 (Security step 4), and gates R-DATA-2 (owner ruling 2026-11-06).\n"
_DATA5_NEW = "the second merged on 2026-11-09 (data#525; Security step 4), so R-DATA-2's lock gate (owner ruling 2026-11-06) is met.\n"

_CASCOR_OLD = "and the second follows R-OBS-SC-2 and waits on neither"
_CASCOR_NEW = "and the second as cascor#748 (2026-11-09, both locks), which waited on neither"

_CASCOR_ANCHOR = "Whether a fix-forward is owed for it is the owner's (mid-wave sitting).\n\n**Canopy**"
_CASCOR_BULLET = (
    "Whether a fix-forward is owed for it is the owner's (mid-wave sitting).\n"
    "- cascor 0.12.0 and 0.13.0 shipped on locks that pin observability 0.4.1 and service-core 0.7.1, so a cascor image carries R-OBS-SC-2 only from a later cascor release; "
    "whether a fix-forward is owed stays the owner's (v1.15.15).\n\n"
    "**Canopy**"
)

_CANOPY_OLD = "(the first merged as canopy#739; the second follows R-OBS-SC-2)"
_CANOPY_NEW = "(the first merged as canopy#739; the second as canopy#806, 2026-11-09)"

_CANOPY_ANCHOR = "At the final census (2026-10-10T21:30Z), canopy#740 proposed canopy 0.9.0, open (§5).\n"
_CANOPY_BULLET = (
    "At the final census (2026-10-10T21:30Z), canopy#740 proposed canopy 0.9.0, open (§5).\n\n"
    "- That earlier cut happened: R-CANOPY-A shipped as canopy 0.9.0 (2026-10-17) on canopy#739's lock, so R-OBS-SC-2 (canopy#806, 2026-11-09) reaches a canopy image only through a later canopy release, "
    "the second cut P4 D-4 contemplates. D-4 is not ruled (v1.15.15).\n"
)

_EXIT_OLD = "- R-OBS-SC-2 cut, and its second lock round merged;\n- R-DATA-2 and R-CANOPY-A cut;\n"
_EXIT_NEW = (
    "- R-OBS-SC-2 cut, and its second lock round merged: done (2026-11-09; v1.15.15);\n"
    "- R-DATA-2 and R-CANOPY-A cut (R-CANOPY-A shipped as canopy 0.9.0 on 2026-10-17, before R-OBS-SC-2; §5);\n"
)

# --- §5: rows ----------------------------------------------------------------------------------------------------------
_ROW_OLD = (
    "| **R-OBS-SC-2** (owed; owner ruling 2026-10-10): juniper-observability 0.4.2 and juniper-service-core 0.7.2 "
    "| P3-07: F2, F6, F9 and F10, and service-core's F3 and F5. F10's sentence shipped at L66 of observability's `CHANGELOG.md` `[0.4.1]` and F9's text at L60 of service-core's `[0.7.1]`; "
    "their corrections go in 0.4.2's and 0.7.2's entries "
    "| P3-07 merged and validated; P3 D-03. Every consumer cap admits a patch, so no cap PR comes first "
    "| The second lock round; XC-SENTRY's upgrade; P2-09; P12-28 |\n"
)
_ROW_NEW = (
    "| **R-OBS-SC-2** (shipped 2026-11-09; owner ruling 2026-10-10; note below): juniper-observability 0.4.2 and juniper-service-core 0.7.2 "
    "| P3-07: F2, F6, F9 and F10, and service-core's F3, F5 and F8, with F10's and F9's corrections; four more scrubbed headers, and parsed cookies; ml#2514's `Retry-After` round-up "
    "| Met: P3-07 merged (ml#2523) and D-03 ruled for the lock PRs, both 2026-11-08; every consumer cap admits a patch "
    "| The second lock round (merged 2026-11-09); XC-SENTRY's upgrade |\n"
    "| **R-OBS-SC-3** (owed; owner ruling 2026-11-08): juniper-observability 0.4.3 "
    "| The owner's: query strings (canopy's `?api_key=` among them) and a Sentry Logs policy; round 1's queue beside them: request bodies, breadcrumbs, exception values and list-shaped headers "
    "| Designed and validated on its own (the owner's ruling); then its own lock round "
    "| XC-SENTRY's end; the trio's restart, if S0.11's pass needs it |\n"
)

_CANOPY_ROW_OLD = "canopy's image lock PR on R-OBS-SC-2 (the first, canopy#739, is merged)"
_CANOPY_ROW_NEW = "canopy's image lock PR on R-OBS-SC-2 (the first, canopy#739, is merged; the second, canopy#806, merged on 2026-11-09, after 0.9.0's cut)"

_DATA_ROW_OLD = "beside data#478's lock and data#479's floors;"
_DATA_ROW_NEW = "beside data#525's lock (data#478's and data#479's floors shipped in 0.17.1);"

_DATA_GATE_OLD = "data's second lock PR (after R-OBS-SC-2)"
_DATA_GATE_NEW = "data's second lock PR (data#525, merged 2026-11-09)"

# --- §5: the R-OBS-SC-2 note, before R-DC-PATCH's ------------------------------------------------------------------------
_NOTE_ANCHOR = "\n**R-DC-PATCH's branch.** "
_NOTE_NEW = (
    "\n**R-OBS-SC-2, shipped 2026-11-09** (v1.15.15; sessions `e97264c3`, `f58cf63e`, `b4208d23` and `e21d1414`). "
    "Each owner answer is dated from its transcript's `tool_result` (`util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py`), "
    "and `util/ad-hoc/2026-11-09_r_obs_sc_2_record_reprobe.py` re-checked the other facts on 2026-11-09 (0 FAIL).\n\n"
    "- **The owner's rulings of 2026-11-08** (session `e97264c3`, answered 08:59:56Z): 0.4.2 is \"P3-07 + header names\", so `Proxy-Authorization`, `Sec-WebSocket-Protocol`, `X-CSRF-Token` and `X-XSRF-Token` join the scrubbed headers; "
    "0.7.2 is \"Include ml#2514, then cut\"; and P3 D-03, asked as who opens the second round's image lock PRs, is \"This arc opens them\".\n"
    "  - Who opens the floor PRs, D-03's third part, was not asked. At 14:42:17Z the owner answered session `f58cf63e` \"Approve both cuts\", so a session cut both Releases, where D-02's options and §5's rules have the owner cut.\n"
    "- **P3-07 is ml#2523** (merged 2026-11-08 15:38:46Z, `a67061bd`), after three rounds that its body records, of three, two and one agents, short of §7.1's top cell. Round 1 ran on the uncommitted draft:\n"
    "  - round 1: the security read found no leak in what P3-07 claimed (sentry-sdk 2.35.0, 2.73.0 and 2.74.0), but pre-existing channels outside it (the four header names, and the 0.4.3 list) "
    "and a false `sentry-sdk>=2.0.0` floor; the fact-check found two MAJORs, and the tests read one;\n"
    "  - round 2, on the fix pass: one MAJOR, `before_send` asserted only at the default sample rate, so a hook installed only above 0.0 leaked an error event's `x-csrf-token`; "
    "and five MINORs, among them that the spy proved `compare_digest` was called, not that its answer decides;\n"
    "  - round 3, one agent on round 2's fix delta only: no MAJOR; two MINORs and five NITs, all fixed. `util/ad-hoc/2026-11-08_p3_07_mutation_check.py` then read 76 of 76 rows as expected.\n"
    "- **ml#2514 was carried as ml#2524** (15:53:33Z, `93fa1f66`): `FailedAuthThrottle`'s `Retry-After` rounds up, keeping its floor of 1. "
    "ml#2514, a Cursor draft whose `[Unreleased]` hunk conflicted with ml#2523's, was closed with a pointer.\n"
    "- **The cuts**: proposals ml#2526 (service-core, `94208d86`) and ml#2525 (observability, `a93de292`, with a carrier commit for `tests/test_public_api.py`'s version pin and the README floor, which `propose.py` misses); "
    "Releases `juniper-service-core-v0.7.2` (published 2026-11-08 16:21:19Z) and `juniper-observability-v0.4.2` (16:35:52Z); archives ml#2527 and ml#2528.\n"
    "  - 0.4.2's CHANGELOG entry carries F10's correction, and 0.7.2's carries F9's. 0.4.2 also floors its `sentry` and `test` extras at `sentry-sdk[fastapi]>=2.35.0`, "
    "which does not reach data, cascor or canopy: each declares `sentry-sdk>=2.0.0` itself.\n"
    "- **Published 2026-11-09.** The owner answered session `e21d1414` at 09:49:26Z (\"Approving now: wait\") and approved both gates. "
    "Observability's `pypi` deployment left `waiting` at 09:51:22Z (run 42500706778; `Publish to PyPI` 09:51:24Z–09:51:39Z), and service-core's at 09:52:23Z (run 42499466753; 09:52:25Z–09:52:50Z). "
    "PyPI serves both `py3-none-any` wheels from 09:51:35Z and 09:52:45Z, with the sha256 TestPyPI took.\n"
    "- **The second lock round** (Security step 4): in each consumer, one signed commit moving exactly the two pins, with a `CHANGELOG.md` `### Security` entry. "
    "recurrence#233 merged at 10:01:54Z (`857efbc5`; `juniper-recurrence/requirements.lock`, with a dated header paragraph), data#525 at 10:07:34Z (`272ff615`), "
    "cascor#748 at 10:14:23Z (`7640d420`; `requirements.lock` and `requirements-cpu.lock`) and canopy#806 at 10:21:36Z (`b4b01904`).\n"
    "  - No `pyproject.toml` moved: the floors stay at observability `>=0.4.1` and service-core `>=0.7.1`. The sessions planned to raise them in each consumer's release PR; "
    "recurrence#199 had moved recurrence's in its lock PR, and recurrence#233's body notes the departure. That plan is a session's, not a ruling (P3-17 stays open; §6).\n"
    "- **The per-lock probe** (the owner's ruling of 2026-11-09 00:24:20Z to session `b4208d23`, \"Per-lock probe\"). S0.11's relay tests were never written: "
    "canopy's needs no A1 ruling, while the data-client and cascor parts wait on A1's open limbs. Each PR body says that its probe is not S0.11's relay run.\n"
    "  - Each probe ran from a venv built from the new lock, with the six Sentry DSNs empty: P3-07's wire probe, which sends secrets in request headers and cookies only; "
    "the consumer's Sentry and security suites (recurrence's whole `tests/`, W1.14's among them); and a record of FastAPI's telemetry setting.\n"
    "  - Before and after, on unchanged `main` SHAs: the wire probe went from LEAK (6 items) to CLEAN in data, cascor and canopy, and is N/A in recurrence, whose lock has no `sentry-sdk`; "
    "the suites passed 247, 290, 454 and 364 tests both times, and no pin drifted. Cascor's probe ran on `requirements-cpu.lock`, the lock its image installs.\n"
    "  - What the pins change: under 0.4.1, `Sec-WebSocket-Protocol`, `X-CSRF-Token` and `X-XSRF-Token` reached every event and transaction of data, cascor and canopy, and only data can turn `send_pii` on, "
    "so the `X-API-Key` and cookie paths were reachable there alone. service-core 0.7.2's round-up reaches recurrence only, whose `SecurityMiddleware` builds the default throttle; "
    "the other three import only `enforce_auth_posture` (canopy also `AuthPostureError` and `enforce_dependency_floors`).\n"
    "- **What it leaves open.** 0.4.2 leaves query strings (canopy's `?api_key=`, sent under the default `send_pii=False`), Sentry Logs (`enable_logs=True` has no `before_send_log`), "
    "request bodies, breadcrumbs and exception values to 0.4.3 (R-OBS-SC-3, above), so XC-SENTRY's (a) and (b) stay in force. "
    "P2-09's and P12-28's service-core halves did not ride 0.7.2, and wait for a later service-core release.\n"
    "- **No running image carries it yet.** Each consumer's newest Release predates its lock PR (data `v0.17.1`, cascor `v0.13.0`, canopy `v0.9.0`, recurrence `juniper-recurrence-v0.8.1`). "
    "The fix reaches a running image only through that repository's next release, juniper-deploy's pin and a restart (§9):\n"
    "  - R-DATA-2 (data 0.18.0): its lock gate is met (XC-P12, the 2026-11-06 rulings); P3-03 and P3-09 remain, and recurrence's two bench caps (`<0.18.0`) widen first;\n"
    "  - cascor: 0.12.0 and 0.13.0 shipped on locks pinning observability 0.4.1, so R-OBS-SC-2 needs a later cascor release; whether a fix-forward is owed is the owner's (§6, mid-wave sitting);\n"
    "  - canopy: R-CANOPY-A shipped as canopy 0.9.0 before R-OBS-SC-2 existed, so R-OBS-SC-2 needs a later canopy release, the second cut P4 D-4 contemplates (§4 Wave 1, Canopy);\n"
    "  - recurrence: its next release carries the pins, though its image has no Sentry path (no `sentry-sdk` in its lock).\n"
    "  - The trio: `JuniperData` and `JuniperCanopy1` hold observability 0.4.0 and service-core 0.5.0, and `JuniperCascor1` imports 0.4.2's and 0.7.2's code from the juniper-ml primary (Security step 5).\n"
    "- **Follow-ups**, asked at §6's mid-wave sitting (none acted on):\n"
    "  - juniper-ml's `[tools]` floors `juniper-observability>=0.4.1`; raising it to `>=0.4.2` needs a meta-package release (0.11.5).\n"
    "  - The forks' `RateLimiter` still truncates with no floor (data `juniper_data/api/security.py:250` and `:254`, cascor `src/api/security.py:229` and `:233`, canopy `src/security.py:270` and `:274`), "
    "so APD-SVCCORE-004's `Retry-After: 0` is live in all three, with no register row. Data `:427` and cascor `:386` keep `FailedAuthThrottle`'s `max(1, int(...))`, the round-down 0.7.2 fixed only in service-core.\n"
    "  - cascor and canopy pass no `telemetry=` to `FastAPI()`, so they run FastAPI 0.162.0's default telemetry. It is inert while their locks hold `opentelemetry-api` and no SDK, but data#454's opt-out is missing in both.\n"
    "  - Separately, canopy legs `:8052` and `:8053` still write their logs to `/tmp/juniper-e2e/` (about 40 MB each on 2026-11-09), against the directive of 2026-10-26; not this arc's.\n"
    "\n**R-DC-PATCH's branch.** "
)

# --- §5: R-CASCOR's notes, the P12 chain's canopy line, the recommended order ------------------------------------------
_RCASCOR_ANCHOR = "    - The unversioned parent `Juniper/AGENTS.md` said juniper-deploy pins the 0.12.0 image until 2026-11-01, when it was edited with the owner's approval (v1.15.10).\n"
_RCASCOR_NEW = (
    "    - The unversioned parent `Juniper/AGENTS.md` said juniper-deploy pins the 0.12.0 image until 2026-11-01, when it was edited with the owner's approval (v1.15.10).\n"
    "- **2026-11-09** (v1.15.15): cascor#748 moved both image locks to observability 0.4.2 and service-core 0.7.2, which meets the row's \"cascor's two image locks\" gate for R-OBS-SC-2; "
    "a data-client fix accepted at A1 would move them again. 0.12.0 and 0.13.0 shipped on 0.4.1 and 0.7.1, so R-OBS-SC-2 needs a later cascor release to reach a cascor image; R-CASCOR's other gates stand.\n"
)

_P12_CANOPY_OLD = "whether P3-06, the O3 wording and A4 were met is not re-probed.\n"
_P12_CANOPY_NEW = (
    "whether P3-06, the O3 wording and A4 were met is not re-probed. "
    "Its lock pins observability 0.4.1 (canopy#739), so R-OBS-SC-2 reaches a canopy image only from a later release (canopy#806; v1.15.15).\n"
)

_ORDER1_OLD = "1. R-OBS-SC-2, once P3-07 validates; and R-DC-PATCH,"
_ORDER1_NEW = "1. R-OBS-SC-2, once P3-07 validates (**shipped 2026-11-09**; v1.15.15); and R-DC-PATCH,"

_ORDER2_OLD = "2. The second lock round. It picks up R-DC-PATCH only if it is on PyPI before its PRs open; otherwise another lock PR follows (§4 Wave 1).\n"
_ORDER2_NEW = (
    "2. The second lock round. It picks up R-DC-PATCH only if it is on PyPI before its PRs open; otherwise another lock PR follows (§4 Wave 1). "
    "**Merged 2026-11-09**, before any data-client fix; if A1 accepts one, another lock PR follows its release (R-DC-PATCH-6, for locks on 0.6.x).\n"
)

_ORDER3_OLD = "3. R-DATA-2, R-CANOPY-A and R-CASCOR, each as soon as it is ready.\n"
_ORDER3_NEW = (
    "3. R-DATA-2, R-CANOPY-A and R-CASCOR, each as soon as it is ready. "
    "R-CANOPY-A shipped as canopy 0.9.0 (2026-10-17), so R-OBS-SC-2 needs a later canopy release too (§4 Wave 1, Canopy; v1.15.15).\n"
)

# --- §6 mid-wave sitting -------------------------------------------------------------------------------------------------
_D03_OLD = "- P3 D-03 (= P4 D-3), for R-OBS-SC-2, once P3-07 validates. D-02's version is set by the owner's ruling of 2026-10-10: R-OBS-SC-2 is a patch.\n"
_D03_NEW = (
    "- P3 D-03 (= P4 D-3), for R-OBS-SC-2, once P3-07 validates. D-02's version is set by the owner's ruling of 2026-10-10: R-OBS-SC-2 is a patch. "
    '**Ruled 2026-11-08 for the lock PRs**: "This arc opens them". Who opens the floor PRs was not asked (' + _NOTE + ").\n"
)

_TRIO_OLD = "- The trio's Sentry upgrade: 0.4.1 and 0.7.1 now and R-OBS-SC-2 later, or R-OBS-SC-2 only (Wave 1's Security step 5).\n"
_TRIO_NEW = (
    "- The trio's Sentry upgrade: 0.4.1 and 0.7.1 now and R-OBS-SC-2 later, or R-OBS-SC-2 only (Wave 1's Security step 5). "
    "**Overtaken in part** (v1.15.15): R-OBS-SC-2 is on PyPI since 2026-11-09, so the 0.4.1-first option is moot. "
    "`JuniperData` and `JuniperCanopy1` hold 0.4.0 and 0.5.0, and `JuniperCascor1` imports the juniper-ml primary's code (Security step 5).\n"
    "- **R-OBS-SC-2's follow-ups** (v1.15.15; " + _NOTE + "):\n"
    "  - whether the per-lock probe may stand in for S0.11's relay run at the trio's restart, and who may move the juniper-ml primary, which `JuniperCascor1` imports (O13 names four other primaries);\n"
    "  - who opens the consumers' floor PRs (D-03's unasked part), and juniper-ml 0.11.5 for the `[tools]` floor;\n"
    "  - a register row for the forks' truncating `RateLimiter` (APD-SVCCORE-004's `Retry-After: 0`) and `FailedAuthThrottle`, data#454's telemetry opt-out for cascor and canopy, and when R-OBS-SC-3 (0.4.3) is designed.\n"
)

# --- §7, §8, §9, §12, Appendix A -----------------------------------------------------------------------------------------
_CAL_OLD = "1. P3-07 (pre-branch) **S**\n"
_CAL_NEW = "1. P3-07 (pre-branch) **S**: merged as ml#2523 (2026-11-08) after rounds of three, two and one agents, short of the top cell; round 1 ran on the uncommitted draft (v1.15.15)\n"

_ARITH_ANCHOR = "on the after-P3-05 route, item 9 joins the exit: 10 items, at least 20 rounds and 100 agent runs (`EX/round10-laneB2-schedule.md` R10B2-12).\n"
_ARITH_NEW = (
    "on the after-P3-05 route, item 9 joins the exit: 10 items, at least 20 rounds and 100 agent runs (`EX/round10-laneB2-schedule.md` R10B2-12).\n"
    "  - Item 1 (P3-07) has merged too (ml#2523, 2026-11-08), short of the top cell, which takes the count to 8 items, at least 16 rounds and 80 agent runs; the figures below are for 9 (v1.15.15).\n"
)

_DATA_SER_OLD = "`[0.17.0]` and `[0.17.1]` are cut, and `[0.17.1]` (data#479) took data#478's entry |"
_DATA_SER_NEW = "`[0.17.0]` and `[0.17.1]` are cut, and `[0.17.1]` (data#479) took data#478's entry. data#525's `### Security` entry went in first (2026-11-09; v1.15.15), so P3-03 rebases over it |"

_CASCOR_SER_OLD = "which includes `CHANGELOG.md` (P3-08's F9 edits it) |"
_CASCOR_SER_NEW = "which includes `CHANGELOG.md` (P3-08's F9 edits it). cascor#748's entry came first (2026-11-09) |"

_DEP_IMAGE_OLD = "| Hard for the fix to reach a running image; otherwise a second cut. Wheels pick up the patch within their caps |\n"
_DEP_IMAGE_NEW = (
    "| Hard for the fix to reach a running image; otherwise a second cut. Wheels pick up the patch within their caps. "
    "The lock half is met (2026-11-09; v1.15.15); the fix reaches a running image only with each repository's next release, juniper-deploy's pin and a restart, and canopy's after R-CANOPY-A's 0.9.0 |\n"
)

_DEP_TRIO_OLD = "the session's recorded test pass, and the owner's restart (§4 Wave 1, Security step 5) | Hard for the fix to reach the trio |\n"
_DEP_TRIO_NEW = (
    "the session's recorded test pass, and the owner's restart (§4 Wave 1, Security step 5) | Hard for the fix to reach the trio. "
    "R-OBS-SC-2 is on PyPI (2026-11-09; v1.15.15); `JuniperCascor1` already imports its code from the juniper-ml primary, and the other two need the upgrade |\n"
)

_DEP_ROW_OLD = "| R-OBS-SC-2 | P3-07 merged and validated; P3 D-03 | Hard |\n"
_DEP_ROW_NEW = "| R-OBS-SC-2 | P3-07 merged and validated; P3 D-03 | Hard. Met 2026-11-08 (ml#2523, short of §7.1's top cell; D-03 ruled for the lock PRs), and shipped 2026-11-09 (v1.15.15) |\n"

_RISK_OLD = "| XC-SENTRY now; the environment upgrade after R-OBS-SC-2 (or 0.4.1 and 0.7.1 now) |\n"
_RISK_NEW = "| XC-SENTRY now and until 0.4.3 (R-OBS-SC-3); the trio's upgrade, now that R-OBS-SC-2 is on PyPI (2026-11-09; v1.15.15); each consumer's next release, pin and restart |\n"

_T0_OLD = "  - **T0**: P3-06, P3-07, P3-08, P3-11; P3-00 →XC-GRANT (a rule)\n"
_T0_NEW = "  - **T0**: P3-06, P3-08, P3-11; P3-00 →XC-GRANT (a rule)\n"

_DONE_OLD = "  - **Done**: P3-20 (= P2-01, ml#2157)\n"
_DONE_NEW = "  - **Done**: P3-20 (= P2-01, ml#2157); P3-07 (ml#2523, 2026-11-08; v1.15.15)\n"

_T1_OLD = "P3-09, P3-17, P3-18 →R-OBS-SC + image lock PRs (the first lock round is done, four PRs on 2026-10-10; the second follows R-OBS-SC-2)"
_T1_NEW = (
    "P3-09, P3-17 (D-02 ruled 2026-10-10; D-03 ruled 2026-11-08 for the lock PRs, its floor part unasked), "
    "P3-18 →R-OBS-SC + image lock PRs (both lock rounds are done, four PRs each on 2026-10-10 and 2026-11-09; the floors are open)"
)

_P4_17_OLD = "P4-17 →R-OBS-SC, "
_P4_17_NEW = "P4-17 →R-OBS-SC (shipped as R-OBS-SC-2, 2026-11-09), "

# --- Validation record and "Changed by this plan" ------------------------------------------------------------------------
_VALIDATION_ANCHOR = "and session `a02ac3a2`'s transcript (lines 547 and 558).\n"
_VALIDATION_NEW = (
    "and session `a02ac3a2`'s transcript (lines 547 and 558).\n"
    "  - v1.15.15 is a record of R-OBS-SC-2, from P3-07 to the second lock round (2026-11-08 and 2026-11-09). No round checks it (owner ruling 2026-10-24). "
    "Its rulings are dated from the four sessions' transcripts (`util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py`), "
    "and `util/ad-hoc/2026-11-09_r_obs_sc_2_record_reprobe.py` re-checked its other facts on 2026-11-09 (0 FAIL).\n"
    "    - Those are the PRs' states, merge commits and files; the two Releases' tags; runs 42500706778 and 42499466753 with their jobs, approvals and `pypi` deployments; "
    "PyPI's and TestPyPI's files; each consumer lock, `pyproject.toml` and newest Release on `main`; and the source lines the follow-ups cite. "
    "The probe's before and after results are in the lock PRs' bodies, and P3-07's rounds in ml#2523's.\n"
    "    - The trio's environments were read in place, read-only: `JuniperCascor1`'s `direct_url.json` files and the juniper-ml primary's `_version.py` and source, and the installed versions in `JuniperData` (`python3.14t`) and `JuniperCanopy1`.\n"
    "    - Two independent agents reviewed the first draft, one re-deriving each fact from its source and one attacking its conclusions and scope. "
    "They found 1 BLOCKER (the draft read as if 0.4.2 ended the Sentry exposure), 8 MAJORs, 9 MINORs and 7 NITs, some found by both; this version applies them.\n"
)

_SCRIPTS_OLD = (
    "    - and with v1.15.14's, `2026-11-07_consolidated_plan_v1_15_14_juniper_ml_0_11_4_published.py`, `2026-11-07_parent_agents_released_paragraph_reprobe.py` "
    "and `2026-11-07_parent_agents_md_juniper_ml_0_11_4.py`; the publish check `2026-11-07_verify_juniper_ml_0_11_4_published.py` landed with ml#2510;\n"
)
_SCRIPTS_NEW = (
    "    - with v1.15.14's, `2026-11-07_consolidated_plan_v1_15_14_juniper_ml_0_11_4_published.py`, `2026-11-07_parent_agents_released_paragraph_reprobe.py` "
    "and `2026-11-07_parent_agents_md_juniper_ml_0_11_4.py`; the publish check `2026-11-07_verify_juniper_ml_0_11_4_published.py` landed with ml#2510;\n"
    "    - and with v1.15.15's, `2026-11-09_consolidated_plan_v1_15_15_r_obs_sc_2_shipped.py`, `2026-11-09_r_obs_sc_2_record_reprobe.py`, `2026-11-09_r_obs_sc_2_owner_answers.py` "
    "and `2026-11-09_wait_for_pypi_gates.py`; P3-07's `2026-11-08_p3_07_sentry_wire_probe.py` and `2026-11-08_p3_07_mutation_check.py` landed with ml#2523;\n"
    "      - and the second lock round's eight, each named `2026-11-09_lock_round_2_` and then `fetch_consumers.py`, `facts.py`, `env_record.py`, `probe.py`, `run_probes.py`, "
    "`refresh.py`, `changelog_insert.py` or `tested_section.py`;\n"
)

_HANDOFFS_ANCHOR = (
    "  - with v1.15.0's PR, the recurrence × equities arc's handoff `HO/HANDOFF_2026-10-25_recurrence-equities-juniper-ml-0-11-1-published-servers-floors-next.md` (P12's, not this plan's).\n"
)
_HANDOFFS_NEW = (
    _HANDOFFS_ANCHOR
    + "  - with v1.15.15's PR, R-OBS-SC-2's handoffs `HO/HANDOFF_2026-11-08_r-obs-sc-2-cut-pypi-gates-lock-round-next.md`, `HO/HANDOFF_2026-11-09_r-obs-sc-2-lock-round-prepped-probe-ruled-gates-pending.md` "
    "and `HO/HANDOFF_2026-11-09_r-obs-sc-2-published-lock-round-merged-plan-v1-15-15-next.md`, and the session's own, `HO/HANDOFF_2026-11-09_r-obs-sc-2-recorded-plan-v1-15-15-owner-items-next.md` (not this plan's).\n"
)

_CREATED_ANCHOR = "  - by session `560c1ec5` (2026-10-10), the auto-memory file `reference_ci_parity_gitleaks_local_scan.md`.\n"
_CREATED_NEW = (
    _CREATED_ANCHOR
    + "  - by session `f58cf63e` (2026-11-08), recorded with v1.15.15, the auto-memory file `reference_host_grep_is_ugrep_honouring_ignore_files.md` (the host's `grep` is ugrep, which honours `.gitignore`).\n"
)

_MEMORY_ANCHOR = (
    "  - by session `a02ac3a2` (2026-11-07), recorded with v1.15.14: the parent `Juniper/AGENTS.md` (juniper-ml 0.11.4, recurrence 0.8.1, the re-probe date and Last Updated; "
    "both versions in `juniper-ml/tmp/2026-11-07-parent-agents-md-backup/`) and `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description); this session did not change `MEMORY.md`.\n"
)
_MEMORY_NEW = (
    _MEMORY_ANCHOR
    + "  - by sessions `e97264c3` and `f58cf63e` (2026-11-08) and `b4208d23` and `e21d1414` (2026-11-09), recorded with v1.15.15: `project_recurrence_equities_p0_arc_2026-10-04.md` (a state block each; "
    "`b4208d23`'s handoff says it changed nothing outside the repository, but its transcript records the write); and by `f58cf63e`, `MEMORY.md` (the new file's pointer, in the verification-hub line).\n"
    "  - by session `09366253` (2026-11-09), with v1.15.15: `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description); this session did not change `MEMORY.md`.\n"
)

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.14\n", "- **Version**: 1.15.15\n"),
    (_STATUS_ANCHOR, _STATUS_NEW),
    (_OV_PRS_OLD, _OV_PRS_NEW),
    (_OV_LOCKS_OLD, _OV_LOCKS_NEW),
    (_OV_EXPOSED_OLD, _OV_EXPOSED_NEW),
    (_OV_TRAIN_OLD, _OV_TRAIN_NEW),
    (_P3_OLD, _P3_NEW),
    (_P4_OLD, _P4_NEW),
    (_PATH_OLD, _PATH_NEW),
    (_LOGS_OLD, _LOGS_NEW),
    (_SENTRY_ANCHOR, _SENTRY_NEW),
    (_LOCKGATE_OLD, _LOCKGATE_NEW),
    (_S04_OLD, _S04_NEW),
    (_STEP1_OLD, _STEP1_NEW),
    (_STEP2_OLD, _STEP2_NEW),
    (_STEP3_OLD, _STEP3_NEW),
    (_STEP4_OLD, _STEP4_NEW),
    (_STEP5_ANCHOR, _STEP5_NEW),
    (_IMAGES_OLD, _IMAGES_NEW),
    (_DATA5_OLD, _DATA5_NEW),
    (_CASCOR_OLD, _CASCOR_NEW),
    (_CASCOR_ANCHOR, _CASCOR_BULLET),
    (_CANOPY_OLD, _CANOPY_NEW),
    (_CANOPY_ANCHOR, _CANOPY_BULLET),
    (_EXIT_OLD, _EXIT_NEW),
    (_ROW_OLD, _ROW_NEW),
    (_CANOPY_ROW_OLD, _CANOPY_ROW_NEW),
    (_DATA_ROW_OLD, _DATA_ROW_NEW),
    (_DATA_GATE_OLD, _DATA_GATE_NEW),
    (_NOTE_ANCHOR, _NOTE_NEW),
    (_RCASCOR_ANCHOR, _RCASCOR_NEW),
    (_P12_CANOPY_OLD, _P12_CANOPY_NEW),
    (_ORDER1_OLD, _ORDER1_NEW),
    (_ORDER2_OLD, _ORDER2_NEW),
    (_ORDER3_OLD, _ORDER3_NEW),
    (_D03_OLD, _D03_NEW),
    (_TRIO_OLD, _TRIO_NEW),
    (_CAL_OLD, _CAL_NEW),
    (_ARITH_ANCHOR, _ARITH_NEW),
    (_DATA_SER_OLD, _DATA_SER_NEW),
    (_CASCOR_SER_OLD, _CASCOR_SER_NEW),
    (_DEP_IMAGE_OLD, _DEP_IMAGE_NEW),
    (_DEP_TRIO_OLD, _DEP_TRIO_NEW),
    (_DEP_ROW_OLD, _DEP_ROW_NEW),
    (_RISK_OLD, _RISK_NEW),
    (_T0_OLD, _T0_NEW),
    (_DONE_OLD, _DONE_NEW),
    (_T1_OLD, _T1_NEW),
    (_P4_17_OLD, _P4_17_NEW),
    (_VALIDATION_ANCHOR, _VALIDATION_NEW),
    (_SCRIPTS_OLD, _SCRIPTS_NEW),
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
