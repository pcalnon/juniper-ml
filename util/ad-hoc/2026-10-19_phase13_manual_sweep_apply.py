#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-19
# Status      : ad-hoc — one-off apply pass; RETAINED as provenance (owner policy 2026-08-25)
# Retire when : RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : ledger Phase 13 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md);
#               HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md
# ---------------------------------------------------------------------------
"""Phase 13 of the canopy E2E ledger: item 26's first step, every open finding against canopy's manual.

Applies, in one replayable pass anchored to text that must occur exactly once:

* ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` -- the headers of F-CANOPY-012, -013,
  -018, -028 and -032 (P2 -> P1), a dated RE-RATED blockquote under each, a dated Status bullet on F-CANOPY-057
  and F-CANOPY-065, and the new ``## Phase 13`` section appended at the end (its consensus record is a
  placeholder the round scripts fill);
* ``notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`` -- the dated correction
  item 26 requires whatever the owner rules (g-3 never reached cascor ``main``);
* the new Lane A handoff, the SUPERSEDED banner on the Phase 12 handoff, item 4 and O17 of the parent
  consolidated handoff, and the INDEX's P2 row.

Why a script: the files are shared with concurrent sessions and land from this host as whole-file uploads, so a
revert costs one re-run on a fresh ``origin/main`` copy plus a small PR (see the turing landing notes). The
triage's rules are asserted before writing: each new header's first severity token is ``P1`` and its last 170
characters carry no disposition word.

Usage:
    python3 util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2]

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
DESIGN_NOTE = "notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md"
PARENT = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md"
INDEX = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md"
PHASE12_HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md"
NEW_HANDOFF_NAME = "HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md"
NEW_HANDOFF = "prompts/thread-handoff_automated-prompts/" + NEW_HANDOFF_NAME

_PRI_RE = re.compile(r"\b(P0/P1|P0|P1|P2|CRITICAL|LEDGER)\b")
_DISPO_RE = re.compile(r"\bFIXED\b|\bHEALED\b|\bACCEPTED\b|\bWITHDRAWN\b", re.I)

# ---------------------------------------------------------------------------
# Ledger: the five headers
# ---------------------------------------------------------------------------

HEADER_SUBS = [
    (
        "**F-CANOPY-012 — `output_weights`, the Network Editor's DEFAULT patch target, is structurally impossible\n"
        "to patch from the UI: the panel parses a flat 1-D list while the route requires 2-D (P2, OPEN;\n"
        "root-caused).**",
        "**F-CANOPY-012 — `output_weights`, the Network Editor's DEFAULT patch target, is structurally impossible\n"
        "to patch from the UI: the panel parses a flat 1-D list while the route requires 2-D (P1 since 2026-10-19,\n"
        "Phase 13, by the manual's Patch Weights entry; P2 before that; code change canopy#535, merged 2026-08-28, in\n"
        "canopy 0.7.0, its live re-drive owed, item 30; OPEN; root-caused).**",
    ),
    (
        "**F-CANOPY-013 — Network Editor success messages read payload keys off the response ENVELOPE, so a\n"
        "successful append reports `index None (now None hidden units)` (P2, OPEN; root-caused, one latent second\n"
        "instance; re-tagged 2026-08-24 from an out-of-vocabulary \"P3\" — the plan §9 severity scale is P0/P1/P2\n"
        "only, and the untagged state made `e2e_finding_triage.py` report the finding as priority `?`).**",
        "**F-CANOPY-013 — Network Editor success messages read payload keys off the response ENVELOPE, so a\n"
        "successful append reports `index None (now None hidden units)` (P1 since 2026-10-19, Phase 13, by the\n"
        "manual's workflow step 6; P2 before that; code change canopy#532, merged 2026-08-28, in canopy 0.7.0, its\n"
        "live re-drive owed, item 30; OPEN; root-caused, one latent second instance; re-tagged 2026-08-24 from an\n"
        "out-of-vocabulary \"P3\" — the plan §9 severity scale is P0/P1/P2 only, and the untagged state made\n"
        "`e2e_finding_triage.py` report the finding as priority `?`).**",
    ),
    (
        "**F-CANOPY-018 — `params-status` has two writers, so the apply toast is always overwritten (P2, OPEN).**",
        "**F-CANOPY-018 — `params-status` has two writers, so the apply toast is always overwritten (P1 since 2026-10-19, Phase 13, by the manual's Apply-button rule; P2 before that; code change canopy#533, merged 2026-08-28, in canopy 0.7.0, its live re-drive owed, item 30; OPEN).**",
    ),
    (
        "**F-CANOPY-028 — pinned params are silently discarded on the first pin after any reload (P2, OPEN; segment 15).**",
        "**F-CANOPY-028 — pinned params are silently discarded on the first pin after any reload (P1 since 2026-10-19, Phase 13, by the manual's pin-persistence sentence, the narrowest of that phase's five re-ratings; P2 before that; code change canopy#533, merged 2026-08-28, in canopy 0.7.0, its live re-drive owed, item 30; OPEN; segment 15).**",
    ),
    (
        "**F-CANOPY-032 — the worker panel's \"Worker data degraded\" alert never renders even though canopy's own API reports the error (P2, OPEN; segment 16).**",
        "**F-CANOPY-032 — the worker panel's \"Worker data degraded\" alert never renders even though canopy's own API reports the error (P1 since 2026-10-19, Phase 13, by the manual's Workers Tab entry; P2 before that; no code change: canopy#533 added contract pins only and the mechanism is unsettled, so the live re-drive, item 30, decides whether it closes or is re-diagnosed; OPEN; segment 16).**",
    ),
]

# ---------------------------------------------------------------------------
# Ledger: the blockquotes and status bullets, each inserted before a unique anchor
# ---------------------------------------------------------------------------

F012_NOTE = """> **RE-RATED P1 (2026-10-19, Phase 13, item 26's first step).** canopy's manual documents the behaviour this
> finding breaks: `docs/USER_MANUAL.md` § Network Editor Tab lists `output_weights` first among the four groups
> **Patch Weights** patches, with values "entered as comma-, semicolon-, or newline-separated floats" (`:493-501`
> at canopy `main` `571743db`; the same words stood at canopy#535's parent `28da69f8^`, `:407-415`, Phase 11). On
> the code this entry measured, no value a user could type was accepted for that group, so the documented
> operation did not exist, which plan §6.3 rates P1: the rule that made F-CANOPY-056 P1, and F-CANOPY-057 P1 while
> the manual promised its stream. The manual's "lets CasCor validate the exact target shape" does not change that;
> it says who checks a shape, not that an entry form existed that could pass. This entry had weighed the failure's
> being "loud, precise, and non-mutating", not the manual. The fix is in code: canopy#535 (`28da69f8`, merged
> 2026-08-28T04:54:55Z, an ancestor of v0.7.0) accepts one row per line or per `;` for `output_weights`, or a flat
> list reshaped `(I+H, output_size)` from the panel's topology store (`_resolve_patch_values`,
> `network_editor_panel.py:457-507` at `571743db`). The entry stays OPEN until M-NETWORK-EDITOR-17 is re-driven
> on a leg serving that code (item 30). A note, not a finding: the manual's Patch Weights text does not describe
> the row idiom #535 added; every form it names still parses.

"""

F013_NOTE = """> **RE-RATED P1 (2026-10-19, Phase 13, item 26's first step).** The manual's Network Editor workflow, step 6, reads
> "Use the API response shown in the status alert to confirm the edit" (`docs/USER_MANUAL.md:510` at canopy
> `main` `571743db`; `:424` at `28da69f8^`, Phase 11). The alert this entry measured reported a successful append
> as `index None (now None hidden units)`, and segment 7 saw a successful remove reported the same way, so the
> documented confirmation step gave a false reading on the success path: a documented behaviour broken, P1 under
> plan §6.3, as Phase 11's round 5 lanes read it (that phase's Matrix effect). This entry's "cosmetic only" weighed
> the unharmed state, not the manual. The fix is in code: canopy#532 (`359e1bf7`, merged 2026-08-28T04:16:14Z, an
> ancestor of v0.7.0) unwraps cascor's envelope at both call sites (`_envelope_payload`,
> `network_editor_panel.py:563-585`, called at `:731` and `:828` at `571743db`). The entry stays OPEN until
> M-NETWORK-EDITOR-09 and -13 are re-driven on a leg serving that code (item 30).

"""

F018_NOTE = """
> **RE-RATED P1 (2026-10-19, Phase 13, item 26's first step).** The manual's Configuration Parameters text reads
> "Edits are staged until you click **Apply** — the button enables only when a value differs from the last applied
> set" (`docs/USER_MANUAL.md:266-268` at canopy `main` `571743db`). Segment 12 measured the opposite after a
> successful apply: Apply stayed enabled and `params-status` read `⚠️ Unsaved changes` until a page reload, with
> no value differing (the three-key latch above). That is a documented behaviour broken, P1 under plan §6.3. The
> toast this entry is named for the manual does not describe; canopy's 0.6.0 CHANGELOG does (`CHANGELOG.md:2360-2365`
> at `571743db`), which is the owner's first limb (O17) and is no longer needed for this rating. The fix is in
> code: canopy#533 (`6b55399d`, merged 2026-08-28T05:09:29Z, an ancestor of v0.7.0). The entry stays OPEN until
> C2.9-05 is re-driven on a leg serving that code (item 30); the row was measured in service mode, and the tracker
> and toast are canopy-side, so a demo leg is expected to reach them, to be confirmed on the drive.
"""

F028_NOTE = """
> **RE-RATED P1 (2026-10-19, Phase 13, item 26's first step).** The manual's Parameters Tab text reads "**Pin
> checkboxes** — pinned parameters appear as read-only name + value rows in the sidebar's **Pinned** card; the pin
> set lives in browser local storage, so it survives a reload" (`docs/USER_MANUAL.md:754-755` at canopy `main`
> `571743db`). Segment 15 measured the set surviving the reload itself and being discarded by the first pin after
> it, so the persistence the manual promises lasts until the user next uses the control it is described with: a
> documented behaviour broken, P1 under plan §6.3. This is the narrowest of Phase 13's five re-ratings, and the
> counter-reading is recorded: the sentence promises survival of a reload, which the store did, and says nothing
> of the next pin; by that reading the finding is P2. It is rated on what a user following the manual sees. The
> fix is in code: canopy#533 (`6b55399d`, merged 2026-08-28T05:09:29Z, an ancestor of v0.7.0), which repaired the
> writer, not the rehydration (above), and whose own note says the repro was not reproduced from source. The entry
> stays OPEN until M-PARAMETERS-04/-05/-06 are re-driven on a leg serving that code (item 30).
"""

F032_NOTE = """
> **RE-RATED P1 (2026-10-19, Phase 13, item 26's first step).** The manual's Workers Tab lists, second among its
> display elements, "**Degradation alert** — "Worker data degraded: …" when the upstream call fails
> (dismissable)" (`docs/USER_MANUAL.md:732` at canopy `main` `571743db`). Segment 16 measured the alert absent for
> 60 s under each of two inductions while canopy's own API reported the error. The correction above stands: the
> control-WS-only arm should not have counted, and the cascor-down arm is an upstream failure by any reading; one
> arm suffices. A documented behaviour broken, P1 under plan §6.3. Unlike Phase 13's other four re-ratings,
> nothing in code claims to fix it: canopy#533 pinned the path with four contract tests and changed no behaviour,
> and Phase 4 found the source correct end to end and suspected F-CANOPY-027's filled-store / dead-render class,
> since FIXED. So M-WORKERS-02's re-drive, the cascor-down arm first (item 30), either closes this entry or
> re-diagnoses it; until it runs this is the one open P1 of Phase 13 with no fix in code.
"""

F057_STATUS = """- **Status 2026-10-19 (Phase 13): P2 stands; the manual re-read, the defect re-confirmed at both current `main`s,
  and the design note corrected.** At canopy `main` `571743db` the Replay Tab still says "Today no weight sample
  reaches the page" (`docs/USER_MANUAL.md:820-822`) and the Network Evolution Tab "none do today" (`:714-715`), so
  the manual does not reach this entry. At cascor `main` `4c26919f` (2026-10-16) `_emit_frame`
  (`src/api/lifecycle/manager.py:1260-1297`) still emits no `weights` key and `weights_at` (`:1244`) has no caller
  in the file; `dbc25277` is 3 ahead and 537 behind that `main`. At canopy `571743db` `_to_dashboard_metric`
  (`src/backend/cascor_service_adapter.py:1960-1991`) still rebuilds each row without `weights`. The CAN-015g/h
  design note (`JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`) now carries the dated
  correction item 26 required: g-3 never reached `main`. With that it no longer records the stream as shipped, and
  the owner's first limb (O17) does not reach this entry through it (Phase 13).

"""

F065_STATUS = """- **Status 2026-10-19 (Phase 13): not reached by canopy's manual.** At canopy `main` `571743db` the manual says
  only that edits are staged until **Apply** and that the Parameters tab shows the applied values
  (`docs/USER_MANUAL.md:266-269`); no sentence describes what the toast reports. The rating stays with the owner's
  first limb, which after Phase 13 decides this entry alone (Phase 13, Matrix effect and counts).
"""

INSERTS = [
    # (anchor the text is inserted BEFORE, text)
    ("**F-CANOPY-013 — Network Editor success messages read payload keys off the response ENVELOPE", F012_NOTE),
    ("### W5 steps 16-26 — replay starts perfectly, then cannot be controlled at all", F013_NOTE),
    ("\n**F-CANOPY-022 — the \"Add Top Tier Candidates\" option can never be applied", F018_NOTE),
    ("\n**F-CANOPY-029 — the Dataset View \"Generate Dataset\" modal can never open", F028_NOTE),
    ("\n### Observations (non-finding)", F032_NOTE),
    ("- **Cascor.** The replay frames carry no weights. On `main`, `weights_at` (`src/api/lifecycle/manager.py`) is", F057_STATUS),
    ("- **Observed** (A-N2, `02_gaussian/03_set_params_caps.json`, 2026-09-23T19:38:06.747Z). The request set five", F065_STATUS),
]

# ---------------------------------------------------------------------------
# Ledger: Phase 13
# ---------------------------------------------------------------------------

PHASE13 = """
## Phase 13 — 2026-10-19: item 26's first step, every open finding checked against canopy's manual — five open P2s are P1 by the manual (F-CANOPY-012, -013, -018, -028 and -032), so the open P1 count rises from 4 to 9; four of the five have been fixed in code since canopy 0.7.0 and are owed their live re-drive, restored as item 30

**Summary.**

- **The check.** Phase 11's item 26 asks first, without waiting for the owner's §6.3 ruling (O17), that every open
  finding be checked against canopy's manual, which plan §6.3 already counts as documentation ("P1 (breaks a
  documented behaviour)", `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:357-360`). This phase
  does that for all 20 open findings against `docs/USER_MANUAL.md` at canopy `main` `571743db` (2026-10-17T23:01:09Z,
  the head after the v0.9.0 release), read through the GitHub API; the copy in this host's canopy checkout is
  byte-identical. The precedents applied are the ledger's own: F-CANOPY-056 was P1 because the manual promised a
  behaviour that did not exist; F-CANOPY-057 was P1 while the manual promised its weight stream and P2 once
  canopy#684 corrected the manual; F-CANOPY-064's P1 rests on the manual's Training Metrics text.
- **Five re-ratings, P2 to P1**, each on a sentence of the manual that states the behaviour the finding was
  measured to break: **F-CANOPY-012** (Patch Weights lists `output_weights`, entered as separated floats; no entry
  could pass), **F-CANOPY-013** (workflow step 6, "Use the API response shown in the status alert to confirm the
  edit"; the alert reported `index None (now None hidden units)` on a success), **F-CANOPY-018** (Apply "enables
  only when a value differs from the last applied set"; it stayed enabled after an apply until a reload),
  **F-CANOPY-028** (the pin set "survives a reload"; the first pin after a reload discarded it) and **F-CANOPY-032**
  (the "Worker data degraded" alert "when the upstream call fails"; it never rendered). The quotes, the measurements
  they are set against and the counter-readings are under "The five re-ratings". F-CANOPY-028's is the narrowest,
  and is recorded as such.
- **Four of the five are fixed in code, and have been since canopy 0.7.0.** canopy#532 (F-CANOPY-013; `359e1bf7`,
  2026-08-28T04:16:14Z), canopy#535 (F-CANOPY-012; `28da69f8`, 04:54:55Z) and canopy#533 (F-CANOPY-018 and
  F-CANOPY-028; `6b55399d`, 05:09:29Z) are each an ancestor of the v0.7.0 tag (published 2026-09-09T07:15:13Z), so
  every release from 0.7.0 on carries them; canopy's CHANGELOG at `571743db` names none of the three PRs and none of
  the four findings (its one `#532` is the 0.9.0 entry for F-CANOPY-059). Their entries stay OPEN, as Phase 4
  ruled, until each row is re-driven live; that re-drive fell out of the numbered list when Phase 9 renumbered it,
  and is restored here as **item 30**. **F-CANOPY-032 is the exception**: canopy#533 pinned its path with contract
  tests and changed no behaviour, Phase 4 found the source correct end to end, and the entry's one sound arm
  (cascor down) has not been re-driven; it is the one P1 this phase creates with no fix in code.
- **The other fifteen open findings stand where they were.** Ten the manual does not reach (F-CANOPY-001, -033,
  -034, -049, -051, -060, -063, -066, F-ML-002, and F-CANOPY-057, whose Replay Tab text says "Today no weight
  sample reaches the page"). Two were already P1 on other grounds, and the manual bears on neither (F-CASCOR-001,
  F-CASCOR-002). F-CANOPY-064's P1 already rests on the manual; the lines it cites have moved, not changed.
  F-CANOPY-065 is not reached: no manual text describes the apply toast, so its rating stays with the owner's
  first limb. F-CANOPY-067's rating stays "P2 pending a live drive", its own condition; the manual documents the
  plots it would corrupt, so the live drive is all that is left to decide it.
- **The CAN-015g/h design note is corrected**, as item 26 requires whatever the ruling: a dated note under its
  status block records that g-3 never reached cascor `main`, with the merge targets re-derived from the GitHub
  API, and its two g-3 rows are annotated
  (`notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`). F-CANOPY-057's defect was
  re-confirmed at both current `main`s while doing it.
- **The owner's question narrows.** Of the four findings Phase 11 placed within the first limb's reach, three
  (F-CANOPY-012, -013, -018) are P1 by the manual without any ruling, and the fourth (F-CANOPY-057) is no longer
  promised by the design note once corrected. The first limb now decides F-CANOPY-065 alone, as Phase 10 first put
  it; the second limb still decides F-CANOPY-068's rating of record and moves no count. Item 26's second step, the
  CHANGELOG and the design plans for every open finding, still waits on the ruling.
- **Counts** (`e2e_finding_triage.py`): 79 findings, **56 fixed**, 1 accepted, 2 withdrawn, **20 open**; no open
  P0, **9 open P1** and **11 open P2**. By ruling on the first limb alone: 9 and 11 as the triage counts them, or
  8 and 12.

### Who, and from what

- **Who.** This phase was written in juniper-ml worktree `federated-stargazing-blanket` on the same host as
  Phase 12 (no Juniper service listening, no reach to the trio), so it is a reading of documents, source and the
  GitHub API, not a live phase. Nothing ran against a canopy. The owner granted merge approval for this phase's PR
  in the session that wrote it.
- **The instrument** is a reading of one file against twenty ledger entries. For each open finding the manual
  section covering its surface was read in full (the Network Editor Tab for F-CANOPY-012 and -013; Configuration
  Parameters and the Parameters Tab for -018, -028 and -065; the Workers Tab for -032; the Training Metrics Tab for
  -064 and -067; the Replay and Network Evolution Tabs for -057; the Dataset View Tab and "A wider dataset needs
  Start fresh" for -060; Status Indicators, Update Intervals, Troubleshooting 1 and 5 and WebSocket Real-Time
  Updates for -049; Accessing the Dashboard and the Visualization Tabs preamble for -066), and the whole file was
  then scanned, case-insensitively, for each finding's terms: dark, theme, toast, unsaved, applied, skipped,
  declined, degraded, persist, local storage, truncat-, shortfall, network stats, network information, iteration,
  optimizer, learning rate, restore, CUDA, out of memory, stalled, healthy, relay, `isolated_stack`,
  `RESET_COMPONENT`, active tab, tab selection, pinned, cap. The instrument could have produced a different answer
  wherever a sentence was missed; the term scan is the guard against that, and a validator with the file can
  repeat both in minutes.
- **"Reached"** means the manual states, as the product's behaviour, the thing the finding measured to be
  otherwise. A sentence that only names a surface the finding touches does not reach it: the manual names the
  Training Metrics store's one-second updates, and F-CANOPY-049's relay defect does not stop them. A finding fixed
  in code is rated on the behaviour it measured, as the ledger has always done; the disposition token changes on
  the live re-drive, the rating on the evidence.
- **Sources read for the facts below**, all through `gh api` or `gh pr view`: canopy `main` `571743db`
  (`docs/USER_MANUAL.md`, 1,606 lines; `CHANGELOG.md`, 5,887 lines; `src/frontend/components/network_editor_panel.py`;
  `src/backend/cascor_service_adapter.py`); canopy PRs 532, 533 and 535 and the v0.7.0 and v0.9.0 Releases; cascor
  `main` `4c26919f` (2026-10-16T09:33:36Z; `src/api/lifecycle/manager.py`); cascor PRs 187, 189 and 190 and the
  compare of `main` with `dbc25277`.

### The sweep, finding by finding

| finding | rating before | manual text at `571743db` | reached? | rating after |
|---|---|---|---|---|
| F-CANOPY-012 | P2 | § Network Editor Tab, Patch Weights: "Patches one parameter group: `output_weights` …"; "Values can be entered as comma-, semicolon-, or newline-separated floats." (`:493-501`) | **yes**: no entry for the listed group could pass | **P1** |
| F-CANOPY-013 | P2 | § Network Editor Tab, Workflow 6: "Use the API response shown in the status alert to confirm the edit." (`:510`) | **yes**: the alert misreported a success | **P1** |
| F-CANOPY-018 | P2 | § Configuration Parameters: "Edits are staged until you click **Apply** — the button enables only when a value differs from the last applied set" (`:266-268`) | **yes**: Apply stayed enabled with nothing differing | **P1** |
| F-CANOPY-028 | P2 | § Parameters Tab: "the pin set lives in browser local storage, so it survives a reload" (`:754-755`) | **yes**, narrowly: the first pin after the reload discarded it | **P1** |
| F-CANOPY-032 | P2 | § Workers Tab: "**Degradation alert** — "Worker data degraded: …" when the upstream call fails (dismissable)" (`:732`) | **yes**: never rendered with cascor down | **P1** |
| F-CANOPY-064 | P1 | § Training Metrics Tab: "loss and accuracy curves" (`:311`), "Training & Validation Accuracy" (`:316`), "Accuracy increases steadily" (`:338`) | already the basis of its P1; the entry cites `:266`, `:271` and `:293`, where the text stood then | P1 |
| F-CANOPY-065 | P1 if a shipped CHANGELOG or design-plan promise counts | § Configuration Parameters says only that edits are staged until Apply and that the Parameters tab shows the applied values (`:266-269`); nothing on what the toast reports | no | unchanged (the first limb) |
| F-CANOPY-067 | P2 pending a live drive | § Training Metrics Tab documents the plots (`:311-316`) | the plots are documented; whether the zeros persist on a real page is the entry's own open question | unchanged |
| F-CANOPY-057 | P2 | § Replay Tab: "Today no weight sample reaches the page" (`:820-822`); § Network Evolution Tab: "none do today" (`:714-715`) | no: the manual withdrew the promise in canopy#684 | P2 |
| F-CANOPY-001 | P2 | no dark-mode or theme text anywhere in the file | no | P2 |
| F-CANOPY-033 | P2 | nothing on component resets | no | P2 |
| F-CANOPY-034 | P2 | nothing (an inert store) | no | P2 |
| F-CANOPY-049 | P2 | § Status Indicators (`:155-171`) and § Update Intervals (`:173-176`) describe the browser's connection count and the one-second metrics updates; Troubleshooting 5 (`:1144`) is the browser's socket. None describes the canopy-to-cascor relay or `/api/state`'s freshness | no | P2 |
| F-CANOPY-051 | P2/P3 | nothing on the active tab's persistence | no | P2 |
| F-CANOPY-060 | P2 | § "A wider dataset needs Start fresh" (`:225-244`) documents the other refusal; nothing on the shortfall prompt or the symbol cap | no | P2 |
| F-CANOPY-063 | P2 | a test's comment; nothing in the manual bears on it | no | P2 |
| F-CANOPY-066 | P2 | "Network Information Panel" is listed (`:121`); nothing says what it shows under the recurrence backend | no | P2 |
| F-CASCOR-001 | P1 | nothing on how cascor classifies a CUDA OOM | not a canopy-manual question | P1 |
| F-CASCOR-002 | P1 | § Snapshots Tab documents Restore (`:777`); nothing on optimizer state | not a canopy-manual question | P1 |
| F-ML-002 | P2 | a juniper-ml script | not a canopy-manual question | P2 |

### The five re-ratings

Each is set against the measurement its entry records, and each entry now carries a dated RE-RATED blockquote
with the same reasoning in brief.

- **F-CANOPY-012.** The manual lists `output_weights` first among the four groups Patch Weights patches and says
  values are "entered as comma-, semicolon-, or newline-separated floats"; the same words stood at canopy#535's
  parent (`28da69f8^`, `:407-415`; Phase 11, round 4). Segment 7 measured every such entry rejected on the wire
  for that group (`shape mismatch: output_weights expects (12, 2), got (24,)`), because the panel parsed a flat
  list for a 2-D target with no reshape anywhere. The documented operation did not exist: P1 by the F-CANOPY-056
  rule. The manual's "lets CasCor validate the exact target shape" does not change that; it says who checks a
  shape, not that an entry form existed that could pass. The entry had weighed the failure's being "loud,
  precise, and non-mutating", not the manual. **In code:** canopy#535's `_resolve_patch_values`
  (`network_editor_panel.py:457-507` at `571743db`) accepts one row per line or per `;` for `output_weights`, or a
  flat list reshaped `(I+H, output_size)` from the panel's topology store, and names what to type when it cannot.
  A note, not a finding: the manual's Patch Weights text does not describe that row idiom; every form it names
  still parses.
- **F-CANOPY-013.** Step 6 of the manual's workflow is the confirmation step, and the entry measured it giving
  `Appended unit at index None (now None hidden units)` on an append that fully succeeded, with segment 7 then
  seeing the remove path do the same (`Removed unit 9 (now None hidden units)`). A user following step 6 is told
  nothing true about the edit, and is told it on the success path. Phase 11's round 5 lanes read the manual's
  step 6 as documenting what this finding breaks (that phase's Matrix effect); this phase agrees. The entry's
  "cosmetic only" weighed the unharmed state. **In code:** canopy#532's `_envelope_payload`
  (`network_editor_panel.py:563-585` at `571743db`), called at both sites (`:731`, `:828`).
- **F-CANOPY-018.** The manual's rule for the Apply button is that it "enables only when a value differs from the
  last applied set". Segment 12 measured, after a successful apply, Apply enabled and `params-status` reading
  `⚠️ Unsaved changes` until a page reload, with nothing differing; Phase 4 traced it to three keys the dirty
  comparison read that the apply payload never wrote. That is the documented rule broken, P1. The toast the entry
  is named for the manual does not describe; canopy's 0.6.0 CHANGELOG does (`CHANGELOG.md:2360-2365` at
  `571743db`), which is the owner's first limb and is no longer needed for this rating. **In code:** canopy#533.
- **F-CANOPY-028.** The manual says the pin set "lives in browser local storage, so it survives a reload".
  Segment 15 measured it surviving the reload and being discarded by the first pin after it, because the writer
  replaced the store with the state of every rendered checkbox (Phase 4: the writer, not the rehydration, and the
  repro "was not reproduced from source", so the re-drive re-checks the symptom). **The counter-reading is
  recorded**: the sentence promises survival of a reload, which the store did, and says nothing of the next pin;
  by that reading the finding is P2. This phase rates on what a user following the manual sees, which is pins
  that persist until the control they are described with is next used, and calls that the promise broken. It is
  the narrowest of the five, and a validator who takes the other reading moves the P1 count from 9 to 8. **In
  code:** canopy#533's `_merge_pinned_params` writes only what it can observe.
- **F-CANOPY-032.** The manual lists the degradation alert as a display element, shown "when the upstream call
  fails". Segment 16 measured it absent for 60 s under each of two inductions while canopy's own API carried the
  error. Phase 4's correction to the entry stands: the control-WS-only arm should not have counted, since
  `list_workers()` succeeds there and no alert is right; the cascor-down arm is an upstream failure by any reading,
  and one arm suffices. P1. **Not in code:** canopy#533 added four contract tests on the path and changed no
  behaviour; Phase 4 traced the path end to end, found it correct in source, and suspected F-CANOPY-027's
  filled-store / dead-render class, since FIXED. So M-WORKERS-02's re-drive decides this entry, and until it runs
  this is the one open P1 of this phase that no code claims to fix.

### The design note's correction

`notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md` said, in its "Revision
2026-05-04 — sprint complete" note, that "every CAN-015g item has merged to `main`", and its delivery log and
PR-breakdown tables carried g-3 (the replay weight emitter) as delivered. Re-derived with `gh` for this phase, as
F-CANOPY-057's History first recorded in Phase 9's validation:

- cascor#187 merged on 2026-05-03T07:31:04Z (`d85c9ddd`) into `feature/can-015g-2-replay-weight-cache`;
- its retarget cascor#190 merged at 20:05:12Z (`dbc25277`) into `feature/can-015g-2-replay-weight-cache-v2`, 13
  minutes after that branch's own PR, cascor#189, had landed on `main` as `b1d19948` (19:52:10Z);
- at cascor `main` `4c26919f` (2026-10-16T09:33:36Z) the compare with `dbc25277` reads diverged, 3 ahead and 537
  behind (Phase 10 measured 512 behind at `0e016a7c`);
- `_ReplaySession._emit_frame` (`src/api/lifecycle/manager.py:1260-1297`) emits `epoch`, `loss`, `accuracy`,
  `validation_loss`, `validation_accuracy`, `phase`, `replay` and `snapshot_id`, and no `weights`; `weights_at`
  (`:1244`) has no caller in the file, and its own docstring still names "g-3's emitter" as the caller to come;
- canopy `571743db`'s `_to_dashboard_metric` (`src/backend/cascor_service_adapter.py:1960-1991`) rebuilds each
  row without a `weights` key, so the page would drop one if it came.

The note now carries a dated correction under its status block, its header's Status points to it, its two g-3
rows say the merges landed in a stacked base and not on `main`, and its "Last updated" is this date. Nothing else
in the note was re-verified; the correction is scoped to g-3 and to the "decision-boundary animation with
per-unit weight evolution" its summary describes, which has not shipped. With that, the note no longer records
the weight stream as implemented, and F-CANOPY-057 is not within reach of the owner's first limb through it; its
P2 rests on the manual's and the FAQ's current text, as since Phase 10.

### What this phase cannot support

- Nothing was driven. Each re-rating rests on a measurement another phase made (segments 7, 12, 15 and 16) and on
  the manual's text today; none of the five symptoms was re-observed, and four of them are expected to be gone on
  any leg serving canopy 0.7.0 or later, which item 30 checks.
- The manual was read at one commit. A sentence added or removed after `571743db` moves nothing here until read.
- The sweep is a reading, not a proof of absence. "Not reached" means no sentence was found by section reading and
  by the term scan; a sentence phrased in terms neither anticipated would be missed. Item 26's second step, the
  CHANGELOG and the design plans, was not done: it waits on the ruling, and this phase read the CHANGELOG only for
  the facts above (the 0.6.0 toast entry, and the absence of the fix-wave PRs).
- Whether the four fixes work on a live page is not known to this ledger. Phase 4 brought up no stack, and no
  later phase drove their rows. Their re-drive is item 30.

### Consensus record (§7 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`)

CONSENSUS_RECORD_PENDING

### Matrix effect and counts

- No matrix row changes: this phase drove no row. The rows whose FAIL halves carry the five re-rated findings are
  C2.9-05 (F-CANOPY-018), M-WORKERS-02 (F-CANOPY-032), M-NETWORK-EDITOR-09 and -13 (F-CANOPY-013) and
  M-NETWORK-EDITOR-17 (F-CANOPY-012); F-CANOPY-028's rows, M-PARAMETERS-04/-05/-06, read PASS with the pin value
  "pending an Apply", and Phase 4 named them for its re-drive.
- **Counts**, from `e2e_finding_triage.py`: **79 findings**, 56 fixed, 1 accepted, 2 withdrawn, **20 open**.
  - **No open P0.**
  - **9 open P1:** F-CANOPY-012, F-CANOPY-013, F-CANOPY-018, F-CANOPY-028, F-CANOPY-032, F-CANOPY-064,
    F-CANOPY-065, F-CASCOR-001 and F-CASCOR-002. Four of the nine (012, 013, 018, 028) are fixed in code since
    canopy 0.7.0 and owed their live re-drive (item 30); F-CANOPY-032 is owed its re-drive or re-diagnosis
    (item 30); F-CANOPY-064 is item 18; F-CANOPY-065 is item 20 and the first limb; the two cascor findings are
    not this arc's to fix.
  - **11 open P2.**
  - **The owner's question** (O17): the first limb now decides F-CANOPY-065 alone: 9 open P1 and 11 open P2 if a
    shipped CHANGELOG or design-plan promise counts as documented, as the triage counts them, else 8 and 12. The
    second limb decides F-CANOPY-068's rating of record and moves no count. F-CANOPY-028 is the one re-rating a
    different reading of the manual would reverse (above), which would make those 8 and 12, or 7 and 13.
- **Plan §6.3's Phase 2 exit criterion**, every P0 and P1 closed or explicitly deferred with owner sign-off, now
  waits on nine P1s instead of four. Five of the nine can move without a design: four re-drives of merged fixes
  and one re-drive that closes or re-diagnoses (item 30).

### Still owed after this phase

Phase 12's list stands, items 0 to 29, with these changes:

- **Item 26's first step is DONE**: every open finding has been checked against canopy's manual. Its second step
  stays, and narrows: once the owner rules, check each open finding not yet rated on canopy's CHANGELOG and the
  design plans for a promise, or, if the ruling counts it, a description of an internal mechanism, of the
  behaviour it breaks; of the four findings Phase 11 named, F-CANOPY-065 is the only one the ruling can still
  move, and the CAN-015g/h design note's correction is applied.
- **Item 18** is unchanged; F-CANOPY-064's P1 stands.
- **Item 20**'s F-CANOPY-065 is P1 conditionally, as before; the manual does not reach it.

New item:

30. **The Phase 4 fix wave's live re-drive**, owed since 2026-08-28 (Phase 4, "Still owed (unchanged, plus)") and
    carried by no numbered item since Phase 9 renumbered the list; now owed at P1 for four of its findings. On a
    leg serving canopy 0.9.0 or later (every release from 0.7.0 carries the fixes), drive:
    - **M-NETWORK-EDITOR-17** for F-CANOPY-012 (all four targets; `output_weights` as rows and as a flat list,
      and a wrong-count flat list for the new message) and **M-NETWORK-EDITOR-09 and -13** for F-CANOPY-013 (the
      alert's index and count on a successful append and remove): a service leg whose cascor can be restored into
      `Investigating`, so a writable cascor, never the trio;
    - **C2.9-05** for F-CANOPY-018 (Apply disabled and `params-status` clean after a successful apply; the toast's
      ~900 ms life, which the fix was not written for, read as it is) and **M-PARAMETERS-04/-05/-06** for
      F-CANOPY-028 (pin, reload, pin again; the first set must survive): the controls are canopy-side and the
      manual says they work in both modes, so a demo leg is expected to reach them, to be confirmed on the drive;
    - **M-WORKERS-02** for F-CANOPY-032, the cascor-down arm first (cascor stopped, canopy up, the Workers tab open
      for 60 s): a service leg whose cascor may be stopped, never the trio. Phase 1 segment 16's `degraded`
      induction (cascor restarted with `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS` at a bogus origin) is the second
      arm, and no alert there is correct;
    - at P2, **C2.1-01/02** for F-CANOPY-001 on the same legs; **M-METRICS-03**, F-CANOPY-026's row, still reads
      FAIL in the matrix though that entry is FIXED, and can be re-validated on the same drive; F-CANOPY-034 has no
      row.
    Each entry's header token changes only on its own row's result. F-CANOPY-032's result either closes the entry
    or re-diagnoses it. The F-CANOPY-012 drive should also say whether the manual's Patch Weights sentence needs
    the row idiom.
"""

# ---------------------------------------------------------------------------
# Design note
# ---------------------------------------------------------------------------

DESIGN_SUBS = [
    (
        "**Owner**: Paul Calnon • **Status**: Implemented (h-6 in review) • **Created**: 2026-05-02 • **Last updated**: 2026-05-04",
        "**Owner**: Paul Calnon • **Status**: Implemented (h-6 in review) — **corrected 2026-10-19: g-3 never reached cascor `main`; see the status note** • **Created**: 2026-05-02 • **Last updated**: 2026-10-19",
    ),
    (
        "> the as-designed sequencing for posterity but are now annotated\n"
        "> with merged-PR + commit-SHA columns.\n",
        "> the as-designed sequencing for posterity but are now annotated\n"
        "> with merged-PR + commit-SHA columns.\n"
        ">\n"
        "> **Correction 2026-10-19** (the canopy E2E arc; ledger\n"
        "> `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, F-CANOPY-057 and\n"
        "> Phase 13): \"every CAN-015g item has merged to `main`\" is wrong for **g-3**.\n"
        "> cascor #187 merged into `feature/can-015g-2-replay-weight-cache`\n"
        "> (2026-05-03T07:31:04Z, `d85c9ddd`) and its retarget #190 into\n"
        "> `feature/can-015g-2-replay-weight-cache-v2` (20:05:12Z, `dbc25277`), thirteen\n"
        "> minutes after that branch's own PR, #189, had landed on `main` as `b1d19948`\n"
        "> (19:52:10Z). Neither merge reached `main`: at cascor `main` `4c26919f`\n"
        "> (2026-10-16) `dbc25277` is 3 ahead and 537 behind, `_ReplaySession._emit_frame`\n"
        "> (`src/api/lifecycle/manager.py:1260`) emits no `weights` key, and `weights_at`\n"
        "> (`:1244`) has no caller outside its tests. canopy's relay would drop the key\n"
        "> anyway (`_to_dashboard_metric`, `src/backend/cascor_service_adapter.py:1960` at\n"
        "> canopy `571743db`). So no replay weight has ever reached the page, and the\n"
        "> \"decision-boundary animation with per-unit weight evolution\" the summary above\n"
        "> describes is not shipped; canopy's `docs/USER_MANUAL.md` and\n"
        "> `notes/development/REPLAY_V2_FAQ.md` have said so since canopy#684 (2026-09-24).\n"
        "> The two g-3 rows below are annotated. Nothing else in this note was re-verified\n"
        "> by this correction.\n",
    ),
    (
        "| `d85c9ddd` (#187), `dbc25277` (#190 retarget) | Same stacked-branch issue as g-2; reopened as #190. |",
        "| `d85c9ddd` (#187), `dbc25277` (#190 retarget) | Same stacked-branch issue as g-2; reopened as #190. **Correction 2026-10-19:** #190's base was `feature/can-015g-2-replay-weight-cache-v2`, which #189 had landed on `main` 13 minutes earlier, so `dbc25277` is not on `main` (3 ahead, 537 behind at `4c26919f`); g-3 is unshipped (F-CANOPY-057). |",
    ),
    (
        "| `lifecycle/monitor.py`, replay driver thread | cascor #187 → #190 (retarget) ✅ |",
        "| `lifecycle/monitor.py`, replay driver thread | cascor #187 → #190 (retarget) ✅ into a stacked base — **not on `main`** (correction 2026-10-19; F-CANOPY-057) |",
    ),
]

# ---------------------------------------------------------------------------
# Handoffs and the INDEX
# ---------------------------------------------------------------------------

PARENT_SUBS = [
    (
        "   failure) and 29 (worktree housekeeping on the Linux host). Current Lane A handoff:\n"
        "   `HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md`. The status as of 2026-10-08\n"
        "   follows, for context.",
        "   failure) and 29 (worktree housekeeping on the Linux host). **Phase 13 (2026-10-19)** did item 26's first step:\n"
        "   every open finding checked against canopy's manual; F-CANOPY-012, -013, -018, -028 and -032 are P1 by it (triage\n"
        "   79/56/1/2/20, 9 open P1, 11 open P2); four are fixed in code since canopy 0.7.0 and owed their live re-drive, new\n"
        "   item 30; the CAN-015g/h design note is corrected. Current Lane A handoff:\n"
        "   `" + NEW_HANDOFF_NAME + "`. The status as of 2026-10-08\n"
        "   follows, for context.",
    ),
    (
        "manual without waiting for the ruling, then sweeps the rest once the owner rules.",
        "manual without waiting for the ruling, then sweeps the rest once the owner rules. **Since Phase 13 (2026-10-19) the manual\n"
        "check is done**: F-CANOPY-012, -013 and -018 are P1 by the manual without a ruling, and the corrected CAN-015g/h design note no\n"
        "longer promises F-CANOPY-057's stream, so the first limb decides F-CANOPY-065 alone: 9/11 or 8/12 open P1/P2.",
    ),
]

INDEX_SUBS = [
    (
        "(Lane A's current one: `HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md`)",
        "(Lane A's current one: `" + NEW_HANDOFF_NAME + "`)",
    ),
    (
        "Phase 12 (2026-10-19) records it: 79/56/1/2/20, 4 open P1. Next: items 25 (census triggers from the page), 26 (the manual sweep) and 27 (the Live Switch allow arm).",
        "Phase 12 (2026-10-19) records it: 79/56/1/2/20, 4 open P1. Phase 13 (2026-10-19, item 26's first step) checked every open finding against canopy's manual: F-CANOPY-012, -013, -018, -028 and -032 are P1 by it, so 9 open P1 / 11 open P2; four are fixed in code since canopy 0.7.0 and owed their live re-drive (new item 30); the CAN-015g/h design note is corrected. Next: items 25 (census triggers from the page), 27 (the Live Switch allow arm), 28 (first live run on the shipped pacer) and 30 (the fix wave's re-drive).",
    ),
]

PHASE12_BANNER_ANCHOR = (
    "\n\n**Written**: 2026-10-19 by the session in juniper-ml worktree `.claude/worktrees/squishy-growing-breeze` on host"
)
PHASE12_BANNER = (
    "\n\n> **SUPERSEDED 2026-10-19** by `" + NEW_HANDOFF_NAME + "`.\n"
    "> Its item 1 (juniper-ml#2263 merged 2026-10-19T08:49:20Z) and item 3 (item 26's first step, the manual sweep, recorded as\n"
    "> the ledger's Phase 13) are done; items 2, 4, 5, 6 and 7 carry there, with a new item 30 (the Phase 4 fix wave's live\n"
    "> re-drive, four of its findings now P1)."
)

HANDOFF_TEXT = """# HANDOFF 2026-10-19 — P2 canopy Lane A: Phase 13 recorded. Item 26's first step is done: every open finding checked against canopy's manual; F-CANOPY-012, -013, -018, -028 and -032 are P1 by it (9 open P1, 11 open P2); four are fixed in code since canopy 0.7.0 and owed their live re-drive (item 30). Next are items 25, 27, 28 and 30.

**Written**: 2026-10-19 by the session in juniper-ml worktree `.claude/worktrees/federated-stargazing-blanket` on host
turing (macOS, no Juniper service, no reach to the trio), at a phase boundary, as its PR was opened.
**Consensus**: CONSENSUS_SUMMARY_PENDING
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`, authoritative for P2.
Its item 4 is DONE; its items 5 and 7 and the owner batch O1–O17 carry over. This file supersedes
`HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md`.
**Merge approval**: the owner granted it in this session for this session's PR. It is NOT carried: ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A (the juniper-canopy E2E validation arc) from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`
(juniper-ml). Read it in full, then the parent `HANDOFF_2026-10-03_canopy-consolidated.md`. Run the verification
commands first. Merge approval is not carried: ask before the first merge. Items 25 and 28 need a canopy verify leg
against the trio (the Linux host, not turing); item 27 needs a demo leg that trains, never the trio; item 30's Network
Editor and Workers rows need a service leg with a writable or stoppable cascor (never the trio), and its Parameters
rows a demo leg; item 26's second step waits on the owner's ruling (O17).

**Completed:**

- **juniper-ml#2263 merged** on 2026-10-19T08:49:20Z: the ledger's Phase 12 and the previous handoff.
- **The ledger's Phase 13** (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, 2026-10-19) does
  item 26's first step: every one of the 20 open findings checked against canopy's `docs/USER_MANUAL.md` at canopy
  `main` `571743db` (2026-10-17, the head after the v0.9.0 release), under plan §6.3's rule (P1 = "breaks a documented
  behaviour") and the ledger's own precedents (F-CANOPY-056, F-CANOPY-057, F-CANOPY-064).
  - **Five re-ratings, P2 to P1**, each with a dated RE-RATED blockquote in its entry: F-CANOPY-012 (Patch Weights
    lists `output_weights`, entered as separated floats), F-CANOPY-013 (workflow step 6, confirm the edit from the
    status alert), F-CANOPY-018 (Apply "enables only when a value differs from the last applied set"), F-CANOPY-028
    (the pin set "survives a reload"; the narrowest, counter-reading recorded) and F-CANOPY-032 (the "Worker data
    degraded" alert "when the upstream call fails").
  - **Four are fixed in code**: canopy#532 (F-013), #533 (F-018, F-028) and #535 (F-012), merged 2026-08-28 and
    ancestors of v0.7.0 (published 2026-09-09); the CHANGELOG names none of them. Their entries stay OPEN until their
    rows are re-driven (item 30). **F-CANOPY-032 has no fix in code** (canopy#533 pinned its path only; Phase 4 found the
    source correct and suspected F-CANOPY-027's class, since FIXED); its re-drive closes or re-diagnoses it.
  - **The other fifteen stand**: ten not reached (F-CANOPY-001, -033, -034, -049, -051, -057, -060, -063, -066,
    F-ML-002); F-CASCOR-001/-002 P1 already; F-CANOPY-064 P1 on the manual already; F-CANOPY-065 not reached (its rating
    stays with the owner's first limb, which now decides it alone); F-CANOPY-067 "P2 pending a live drive", unchanged.
  - **Counts**: 79 findings, 56 fixed, 1 accepted, 2 withdrawn, **20 open**: 0 P0, **9 P1** (F-CANOPY-012, -013, -018,
    -028, -032, -064, -065, F-CASCOR-001, -002), **11 P2**. By the first limb's ruling: 9/11 or 8/12.
  - **The CAN-015g/h design note** (`notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`)
    carries the dated correction item 26 required: g-3 never reached cascor `main` (cascor#187 into
    `feature/can-015g-2-replay-weight-cache`; #190 into `…-v2`, 13 minutes after #189 had landed that branch on `main`;
    `dbc25277` 3 ahead / 537 behind `4c26919f`). F-CANOPY-057 re-confirmed at both current `main`s.
  - **New item 30**: the Phase 4 fix wave's live re-drive, owed since 2026-08-28 and carried by no numbered item since
    Phase 9's renumbering.
- **This session's PR** carries the ledger, this file, the design note's correction, the parent's item 4 and O17, the
  INDEX's P2 row, the SUPERSEDED banner on the Phase 12 handoff, Phase 13's consensus records (briefs, verbatim
  reports, replayable passes) and the apply script `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py`. Find it
  with `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase13 --state all`.

**Remaining, in order:**

1. **Land this session's PR** if it has not merged: `python3 util/wait_for_checks.py`, query
   `reviewThreads(isResolved:false)` (a CodeQL thread blocks the merge while every check is green), ask the owner,
   then `python3 util/safe_merge.py --execute` and read its `MERGED` line. Afterwards re-check `origin/main` for the
   five headers (`grep -c 'P1 since 2026-10-19' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`
   should print 5): a concurrent whole-file upload of a shared file can revert merged lines.
2. **Item 30: the fix wave's live re-drive**, now at P1 for four findings, on a leg serving canopy 0.9.0 or later:
   - M-NETWORK-EDITOR-17 (F-CANOPY-012: all four targets; `output_weights` as rows, as a flat list, and a wrong-count
     flat list) and M-NETWORK-EDITOR-09/-13 (F-CANOPY-013: the alert's index and count on a successful append and
     remove) need a service leg whose cascor can be restored into `Investigating`: a writable cascor, never the trio.
   - C2.9-05 (F-CANOPY-018: Apply disabled and `params-status` clean after a successful apply) and M-PARAMETERS-04/-05/-06
     (F-CANOPY-028: pin, reload, pin again) are canopy-side; a demo leg is expected to reach them.
   - M-WORKERS-02 (F-CANOPY-032): cascor stopped, canopy up, the Workers tab open 60 s, on a leg whose cascor may be
     stopped; then segment 16's `degraded` induction, where no alert is correct. Its result closes or re-diagnoses.
   - At P2: C2.1-01/02 (F-CANOPY-001); M-METRICS-03 (F-CANOPY-026's row, still FAIL in the matrix). F-CANOPY-034 has no row.
   Each header's token changes only on its own row's result; record the drives as a ledger phase with consensus rounds.
3. **Item 25: census triggers fired from the page**, on the merged code (canopy 0.9.0 or later, a verify leg on the
   Linux host). Schedule each trigger as its own task when the shim sees `AddWatched` (`setTimeout(…, 0)`), timestamp
   it in the page, validate on the synthetic check first. Under the pacer every TOOK predicate reads NO-EFFECT by
   construction, so the evictions are the score. **T-apply needs its own design** (Phase 12, Instruments).
4. **Item 26's second step**, once the owner rules (O17): every open finding not yet rated against canopy's
   `CHANGELOG.md` and the design plans for a promise, or, if the ruling counts it, a description of an internal
   mechanism, of the behaviour it breaks. Only F-CANOPY-065's rating can still move among the four Phase 11 named;
   the others may be reached by entries nobody has read for them yet.
5. **Item 27: F-CANOPY-055's Live Dataset Switch allow arm**, on a demo leg serving 0.9.0 or later whose training may
   be started (never the trio), with the experimental-functions toggle on (ledger Phase 12, item 27). Record in
   F-CANOPY-025's and F-CANOPY-055's entries.
6. **Item 28: the first live run on the shipped pacer**, when the trio's canopy is restarted on 0.9.0 (owner, O13) or
   on any leg serving the merged tree (ledger Phase 12, item 28).
7. **Item 29**: worktree housekeeping on the Linux host (ledger Phase 12, item 29).
8. Then the parent's items 5 and 7, and the owner batch O1–O17 (O17's first limb now decides F-CANOPY-065 alone).

**Traps learned:**

- **The triage reads the first severity token anywhere in a header and only the last 170 characters for a
  disposition.** A re-rating must put `P1` before any `P2` in the header, and the word "fixed" must stay out of the
  tail: "fixed in code" would flip an OPEN entry to FIXED. Phase 13's headers say "code change canopy#NNN".
- **The manual's line numbers move between releases.** F-CANOPY-064 cites `:266`, `:271`, `:293`; at `571743db` the
  same sentences are `:311`, `:316`, `:338`. Cite the commit with every line.
- **canopy's CHANGELOG does not name the Phase 4 fix wave.** canopy#532/#533/#535 are in v0.7.0 (the `compare` API
  says `behind`, 0 ahead) but no entry names them or their findings; do not infer "unshipped" from the CHANGELOG.
- **On turing the worktree guard refuses** `awk` with a program, `sed` with a shell variable, loops over variables,
  `$(…)` inside commands, and heredocs that mention `git`. Spell paths and line numbers out; multi-step logic goes in
  a scratchpad or `util/ad-hoc/` script run with `python3 -I`/`-B`.
- **turing has no signing**: land through `util/open_signed_pr.py` (small files) and
  `util/ad-hoc/2026-10-17_push_signed_with_retry.py` (the ~980 KB ledger as its own commit). Run
  `util/ad-hoc/2026-10-17_turing_network_probe.bash` first; on 2026-10-19 the link was healthy (0% loss to the
  gateway, 12.6 Mbps up).
- **Shared files land as whole-file uploads.** Build each from a fresh `origin/main` copy at upload time and re-apply
  with `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py --root <copy>`; re-check `origin/main` an hour after the merge.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/<your worktree>   # or the Linux host's path
git status --short; git log --oneline -3
gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase13 --state all --json number,state,mergedAt
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7   # 79 / 56 / 1 / 2 / 20; P1 9; P2 11
python3 -B util/ad-hoc/e2e_finding_triage.py --open-only | grep -c 'P1 '   # 9
grep -c 'P1 since 2026-10-19' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md   # 5
grep -n '^## Phase 13' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md
grep -c 'Correction 2026-10-19' notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md   # 2
gh api repos/pcalnon/juniper-canopy/compare/v0.7.0...28da69f8 --jq .status   # behind (canopy#535 is in 0.7.0)
gh api -H "Accept: application/vnd.github.raw" "repos/pcalnon/juniper-canopy/contents/docs/USER_MANUAL.md?ref=571743db" | grep -n 'Use the API response'   # :510
lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8101|8202|8051|8052|8053) '   # on turing: nothing; on the Linux host: the trio up (never touch it)
```

## Git state

- **juniper-ml:** branch `docs/canopy-e2e-phase13`, landed from turing through the API as signed commits
  (`util/open_signed_pr.py`; the ledger by `util/ad-hoc/2026-10-17_push_signed_with_retry.py`). Worktree
  `federated-stargazing-blanket` holds the same files as local, unsigned commits that never leave the host (the
  frozen drafts the consensus rounds reviewed).
- **juniper-canopy, cascor, data:** no branches from this session; read through the GitHub API only (canopy `main`
  `571743db`, cascor `main` `4c26919f`).
- **Services:** none on this host. The trio on the Linux host was not touched or reached.

## Changed by this session

- **Created:** this file; `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py`;
  `reports/e2e-canopy-2026-09-02/drafts/lane13*_phase13_ledger_brief.md`;
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round*.md`;
  `util/ad-hoc/2026-10-19_phase13_ledger_round*_corrections.py`.
- **Modified:**
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: Phase 13; the headers of F-CANOPY-012,
    -013, -018, -028 and -032 and a RE-RATED blockquote in each; Status bullets on F-CANOPY-057 and F-CANOPY-065;
  - `notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`: the header's Status and
    Last updated, the dated correction under the status block, the two g-3 rows;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`: item 4; O17;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: the P2 row;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md`:
    the SUPERSEDED banner.
- **Outside the repo**, in auto-memory: `MEMORY.md` and `canopy-e2e-arc-state.md`.
"""


def apply_subs(text: str, subs: list, label: str) -> str:
    for old, new in subs:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"{label}: anchor found {n} times, expected 1: {old[:100]!r}")
        text = text.replace(old, new)
    return text


def insert_before(text: str, anchor: str, insert: str, label: str) -> str:
    n = text.count(anchor)
    if n != 1:
        raise SystemExit(f"{label}: insert anchor found {n} times, expected 1: {anchor[:100]!r}")
    return text.replace(anchor, insert + anchor)


def check_headers() -> None:
    """The triage's two rules, asserted on the new headers before anything is written."""
    for _old, new in HEADER_SUBS:
        m = re.match(r"^\*\*(F-[A-Z0-9]+-\d+[a-z]?) — (.*?)\*\*", new, re.S)
        if not m:
            raise SystemExit(f"new header does not parse as a ledger header: {new[:80]!r}")
        fid, body = m.group(1), " ".join(m.group(2).split())
        pri = _PRI_RE.search(body)
        if not pri or pri.group(1) != "P1":
            raise SystemExit(f"{fid}: first severity token is {pri.group(1) if pri else None!r}, expected P1")
        tail = body[-170:]
        if _DISPO_RE.search(tail):
            raise SystemExit(f"{fid}: a disposition word sits in the header's last 170 characters: {tail!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="apply in memory only; write nothing")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="repo root (default: this script's repo)")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    check_headers()

    ledger_p = root / LEDGER
    ledger = ledger_p.read_text(encoding="utf-8")
    if "## Phase 13 — " in ledger:
        raise SystemExit("the ledger already has a Phase 13: nothing to do")
    if not ledger.endswith("host.\n"):
        raise SystemExit("the ledger does not end where Phase 12's item 29 ends; refusing to append")
    new_ledger = apply_subs(ledger, HEADER_SUBS, "ledger headers")
    for anchor, insert in INSERTS:
        new_ledger = insert_before(new_ledger, anchor, insert, "ledger inserts")
    new_ledger = new_ledger + PHASE13

    design_p = root / DESIGN_NOTE
    new_design = apply_subs(design_p.read_text(encoding="utf-8"), DESIGN_SUBS, "design note")

    parent_p = root / PARENT
    new_parent = apply_subs(parent_p.read_text(encoding="utf-8"), PARENT_SUBS, "parent handoff")

    index_p = root / INDEX
    new_index = apply_subs(index_p.read_text(encoding="utf-8"), INDEX_SUBS, "INDEX")

    p12_p = root / PHASE12_HANDOFF
    p12 = p12_p.read_text(encoding="utf-8")
    if "SUPERSEDED 2026-10-19" in p12:
        raise SystemExit("the Phase 12 handoff already carries a SUPERSEDED banner")
    new_p12 = apply_subs(p12, [(PHASE12_BANNER_ANCHOR, PHASE12_BANNER + PHASE12_BANNER_ANCHOR)], "Phase 12 handoff")

    new_handoff_p = root / NEW_HANDOFF
    if new_handoff_p.exists():
        raise SystemExit(f"{NEW_HANDOFF} already exists")

    print(f"ledger: {len(HEADER_SUBS)} headers, {len(INSERTS)} inserts, Phase 13 appended; {len(ledger)} -> {len(new_ledger)} chars")
    print(f"design note: {len(DESIGN_SUBS)} substitutions")
    print(f"parent handoff: {len(PARENT_SUBS)}; INDEX: {len(INDEX_SUBS)}; Phase 12 handoff: banner; new handoff: {len(HANDOFF_TEXT)} chars")
    if args.check:
        print("--check: nothing written")
        return 0
    ledger_p.write_text(new_ledger, encoding="utf-8")
    design_p.write_text(new_design, encoding="utf-8")
    parent_p.write_text(new_parent, encoding="utf-8")
    index_p.write_text(new_index, encoding="utf-8")
    p12_p.write_text(new_p12, encoding="utf-8")
    new_handoff_p.write_text(HANDOFF_TEXT, encoding="utf-8")
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
