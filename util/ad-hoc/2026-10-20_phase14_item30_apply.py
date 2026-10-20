#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-20
# Status      : ad-hoc — one-off apply pass; RETAINED as provenance (owner policy 2026-08-25)
# Retire when : RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : ledger Phase 14 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md);
#               HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md;
#               util/ad-hoc/2026-10-20_item30_fixwave_redrive.py (the drives this records)
# ---------------------------------------------------------------------------
"""Phase 14 of the canopy E2E ledger: item 30, the Phase 4 fix wave's live re-drive, and F-CANOPY-069.

Applies, in one replayable pass anchored to text that must occur exactly once:

* ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` -- the headers of F-CANOPY-001, -012,
  -013, -018 and -032 (OPEN -> FIXED) with a dated RE-DRIVEN blockquote under each, F-CANOPY-028's header and a
  dated RE-DIAGNOSED blockquote (it stays OPEN), and the new ``## Phase 14`` section appended at the end, which
  carries the F-CANOPY-069 entry (its consensus record is a placeholder the round scripts fill);
* ``notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`` -- the status cells of C2.1-01/-02,
  C2.9-05, M-METRICS-03, M-WORKERS-02, M-PARAMETERS-04/-05/-06 and M-NETWORK-EDITOR-09/-13/-17;
* the new Lane A handoff, the SUPERSEDED banner on the Phase 13 handoff, the parent consolidated handoff's
  pointer, and the INDEX's P2 row.

Why a script: the files are shared with concurrent sessions and land from this host as whole-file uploads, so a
revert costs one re-run on a fresh ``origin/main`` copy plus a small PR. The triage's rules are asserted before
writing: each rewritten header's first severity token is unchanged and its last 170 characters carry FIXED for
the five that close, and no disposition word but OPEN for the two that stay open.

Usage:
    python3 util/ad-hoc/2026-10-20_phase14_item30_apply.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
MATRIX = "notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts"
HANDOFF_NEW = f"{HANDOFF_DIR}/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md"
HANDOFF_PREV = f"{HANDOFF_DIR}/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md"
HANDOFF_PARENT = f"{HANDOFF_DIR}/HANDOFF_2026-10-03_canopy-consolidated.md"
INDEX = f"{HANDOFF_DIR}/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md"
SHA = "571743db"
RUN = "reports/e2e-canopy-2026-09-02/item30-turing"

_PRI_RE = re.compile(r"\b(P0/P1|P0|P1|P2|CRITICAL|LEDGER)\b")


# ----------------------------------------------------------------------------- the ledger: headers
HEADERS = [
    # (old header text, new header text, expected first severity token, expected disposition in the tail)
    (
        "**F-CANOPY-001 — dark-mode toggle glyph not synced from the persisted store on mount (P2, OPEN).**",
        "**F-CANOPY-001 — dark-mode toggle glyph not synced from the persisted store on mount (P2; code change canopy#532, merged 2026-08-28, in canopy 0.7.0; C2.1-01 and C2.1-02 re-driven 2026-10-20 on canopy "
        + SHA
        + ", Phase 14, item 30: after a reload the dark theme restores and the glyph reads ☀️; FIXED).**",
        "P2",
        "FIXED",
    ),
    (
        "**F-CANOPY-018 — `params-status` has two writers, so the apply toast is always overwritten (P1 since 2026-10-19, Phase 13, by the manual's Apply-button rule; P2 before that; code change canopy#533, merged 2026-08-28, in canopy 0.7.0, its live re-drive owed, item 30; OPEN).**",
        "**F-CANOPY-018 — `params-status` has two writers, so the apply toast is always overwritten (P1 since 2026-10-19, Phase 13, by the manual's Apply-button rule; P2 before that; code change canopy#533, merged 2026-08-28, in canopy 0.7.0; C2.9-05 re-driven 2026-10-20 on canopy "
        + SHA
        + ", Phase 14, item 30, on a demo leg: the toast stands for the whole window, Apply disables and nothing latches; FIXED).**",
        "P1",
        "FIXED",
    ),
    (
        "**F-CANOPY-028 — pinned params are silently discarded on the first pin after any reload (P1 since 2026-10-19, Phase 13, by the manual's pin-persistence sentence, the narrowest of that phase's five re-ratings; P2 before that; code change canopy#533, merged 2026-08-28, in canopy 0.7.0, its live re-drive owed, item 30; OPEN; segment 15).**",
        "**F-CANOPY-028 — pinned params are silently discarded on the first pin after any reload (P1 since 2026-10-19, Phase 13, by the manual's pin-persistence sentence, the narrowest of that phase's five re-ratings; P2 before that; code change canopy#533, merged 2026-08-28, in canopy 0.7.0; M-PARAMETERS-04/-05/-06 re-driven 2026-10-20 on canopy "
        + SHA
        + ", Phase 14, item 30: a pin was discarded in 2 of 8 drives and the mechanism is re-diagnosed, a table re-render from a stale pin set that the store writer then persists; OPEN; segment 15).**",
        "P1",
        "OPEN",
    ),
    (
        "**F-CANOPY-032 — the worker panel's \"Worker data degraded\" alert never renders even though canopy's own API reports the error (P1 since 2026-10-19, Phase 13, by the manual's Workers Tab entry; P2 before that; no code change: canopy#533 added contract pins only and the mechanism is unsettled, so the live re-drive, item 30, decides whether it closes or is re-diagnosed; OPEN; segment 16).**",
        "**F-CANOPY-032 — the worker panel's \"Worker data degraded\" alert never renders even though canopy's own API reports the error (P1 since 2026-10-19, Phase 13, by the manual's Workers Tab entry; P2 before that; no code change of its own: canopy#533 added contract pins only; M-WORKERS-02 re-driven 2026-10-20 on canopy "
        + SHA
        + ", Phase 14, item 30, both arms: the alert renders on the first sample with cascor stopped and is correctly absent under the control-stream induction, so the entry closes on the F-CANOPY-027 reading, that fix's wave having repaired it; FIXED; segment 16).**",
        "P1",
        "FIXED",
    ),
    (
        "**F-CANOPY-012 — `output_weights`, the Network Editor's DEFAULT patch target, is structurally impossible\nto patch from the UI: the panel parses a flat 1-D list while the route requires 2-D (P1 since 2026-10-19,\nPhase 13, by the manual's Patch Weights entry; P2 before that; code change canopy#535, merged 2026-08-28, in\ncanopy 0.7.0, its live re-drive owed, item 30; OPEN; root-caused).**",
        "**F-CANOPY-012 — `output_weights`, the Network Editor's DEFAULT patch target, is structurally impossible\nto patch from the UI: the panel parses a flat 1-D list while the route requires 2-D (P1 since 2026-10-19,\nPhase 13, by the manual's Patch Weights entry; P2 before that; code change canopy#535, merged 2026-08-28, in\ncanopy 0.7.0; M-NETWORK-EDITOR-17 re-driven 2026-10-20 on canopy "
        + SHA
        + ", Phase 14, item 30: all four targets\npatch and land in cascor, the flat comma form and both row forms included, and the residue holds; FIXED;\nroot-caused).**",
        "P1",
        "FIXED",
    ),
    (
        "**F-CANOPY-013 — Network Editor success messages read payload keys off the response ENVELOPE, so a\nsuccessful append reports `index None (now None hidden units)` (P1 since 2026-10-19, Phase 13, by the\nmanual's workflow step 6; P2 before that; code change canopy#532, merged 2026-08-28, in canopy 0.7.0, its\nlive re-drive owed, item 30; OPEN; root-caused, one latent second instance; re-tagged 2026-08-24 from an\nout-of-vocabulary \"P3\" — the plan §9 severity scale is P0/P1/P2 only, and the untagged state made\n`e2e_finding_triage.py` report the finding as priority `?`).**",
        "**F-CANOPY-013 — Network Editor success messages read payload keys off the response ENVELOPE, so a\nsuccessful append reports `index None (now None hidden units)` (P1 since 2026-10-19, Phase 13, by the\nmanual's workflow step 6; P2 before that; code change canopy#532, merged 2026-08-28, in canopy 0.7.0;\nre-tagged 2026-08-24 from an out-of-vocabulary \"P3\" — the plan §9 severity scale is P0/P1/P2 only, and the\nuntagged state made `e2e_finding_triage.py` report the finding as priority `?`; root-caused, one latent second\ninstance; M-NETWORK-EDITOR-09 and -13 re-driven 2026-10-20 on canopy "
        + SHA
        + ", Phase 14, item 30: the alert reports\nthe real index and count on an append and on a remove; FIXED).**",
        "P1",
        "FIXED",
    ),
]

# ----------------------------------------------------------------------------- the ledger: dated blockquotes
BQ_001 = f"""
> **RE-DRIVEN, FIXED (2026-10-20, Phase 14, item 30).** C2.1-01 and C2.1-02 on a demo leg serving canopy `{SHA}` under
> dash 4.4.1 (`{RUN}/demo_leg_8062_dash441.json`, step `f001`): the click flipped `<html>` to `dark-mode` at +2.3 s and
> swapped the glyph at +0.3 s; after a full reload the theme restored dark AND the glyph read ☀️ at +0.9 s (the
> layout-default 🌙 this entry measured never showed); the next click flipped back at +5.4 s. The fix, the glyph
> derived from the store by the mount-capable callback (canopy#532, `_toggle_dark_mode_handler`'s note at
> `dashboard_manager.py:7350-7372` at `{SHA}`), holds live. Shots `{RUN}/shots/f001_dark.png`,
> `f001_after_reload.png`.
"""

BQ_018 = f"""
> **RE-DRIVEN, FIXED (2026-10-20, Phase 14, item 30).** C2.9-05 on a demo leg serving canopy `{SHA}` under dash
> 4.4.1 (`{RUN}/demo_leg_8062_dash441.json`, step `f018`, run 2; the transcript is
> `{RUN}/transcripts/demo_leg_8062_dash441_run2.log`). The form was dirtied by a dropdown change (optimizer Adam →
> AdamW; Apply enabled, `⚠️ Unsaved changes`), Apply was clicked, and `params-status` and the button's `disabled`
> were sampled every 100 ms for 15 s. The row's own expectation: the toast `Applied 22 of 25 parameter(s); 3 not yet
> supported by the backend: nn_activation_function_name, nn_optimizer_type, nn_output_epochs` (the first of
> `_compose_apply_toast`'s three forms; the demo backend declines those three keys) appeared at +0.66 s and stood
> for the remaining 14.3 s of the window. The added expectation, scored separately: from +5 s to the end Apply read
> `disabled` and the status never read `Unsaved changes`; the ~900 ms overwrite this entry measured did not occur.
> A second dropdown change re-enabled Apply (the tracker still tracks). Run 1 of the same step, under a 3 s mount
> settle, read the same toast; its "latched" flag was the pre-click status still on screen before the toast landed,
> and the rule now counts only `Unsaved changes` after the toast. The demo leg does not discriminate the
> `cn_training_complete` and dataset keys the fix removed from the comparison set, which travel the same way in
> both modes; the latch, which was the symptom, is gone on the code that carries the fix.
"""

BQ_028 = f"""
> **RE-DRIVEN, RE-DIAGNOSED, STAYS OPEN (2026-10-20, Phase 14, item 30).** M-PARAMETERS-04/-05/-06 on a demo leg
> serving canopy `{SHA}` under dash 4.4.1 (`{RUN}/demo_leg_8062_dash441.json`, step `f028`; transcripts
> `{RUN}/transcripts/demo_leg_8062_dash441_run{{1,2,3,4}}*.log`). Each drive: a fresh browser context, pin
> `learning_rate`, read the store and the sidebar card (M-04, M-05), reload, read the checkbox and the store, pin
> `max_iterations`, read the store; the settled arm also unpins both and reloads (M-06). The three rows pass on
> their own expectations in every drive: the store write lands in 1.0–2.3 s, the card shows `Learning Rate 0.01`,
> the set survives the reload, the checkbox re-renders checked (the rehydration canopy#533 found correct is
> correct), and unpinning empties the store and hides the card across a reload.
>
> **The finding reproduces, in 2 of 8 drives, and not the way this entry or the fix describe it.** The eight second
> pins, by their delay after the reload: run 1 at ~10 s (the first pin, `learning_rate`, DISCARDED: the store
> went to `["max_iterations"]`; that run's record was overwritten by run 2 and survives in the run-1 transcript and
> in the reconciler's read of the response capture, `pinned-params-store → ["max_iterations"]` at 141.5 s); run 2
> at 27.9 s (both kept); run 3 settled at 27.9 s and early at 2.5 s (both kept); run 4 mid at 11.5 s, early at
> 2.8 s, mid at 8.0 s (all kept) and **early at 3.0 s, where the second pin was DISCARDED after landing**. That
> drive's record is complete: the store writer's three requests after the reload, read from the renderer's own
> bodies (`arms.early#2.pin_requests_after_reload`), were (1) the mount re-render, 22 checkboxes, `learning_rate`
> checked, State `["learning_rate"]`; (2) the click, both checked, State `["learning_rate"]` → the store became
> `["max_iterations", "learning_rate"]` at +3.2 s; (3) **1.4 s later, a third firing with 22 checkboxes rendered,
> `max_iterations` reported UNCHECKED and State `["max_iterations", "learning_rate"]`** → the writer returned
> `["learning_rate"]` and the pin the user had just made was gone, the card showing `Learning Rate 0.01` alone.
>
> **Mechanism.** `update_parameters_tables` (`parameters_panel.py:250-275` at `{SHA}`) re-renders all three tables
> whenever its params store OR `pinned-params-store` changes, and each checkbox is built with `value=key in
> pinned_set` from the pin set THAT callback received (`:114-118`). On a fresh session the params store fills late
> (the F-CANOPY-004 envelope), so a re-render computed from a pin set older than the user's latest toggle lands
> after it, and the toggled checkbox comes back in its old state. The pattern-matched writer
> (`dashboard_manager.py:5230-5248`) then fires for the re-rendered components (it fires on every table render:
> the two `[]` writes at mount in every drive are those), and `_merge_pinned_params` (`:7320-7348`) does what
> canopy#533 made it do: a rendered checkbox is authoritative for its own key, so the stale render is persisted
> and the pin is dropped. The fix repaired under-reporting (keys not rendered) and left over-reporting (keys
> rendered from a stale set) in place; the entry's own last sentence, "collects the state of every checkbox", named
> the writer, and the writer is still the half that persists a render the user did not make. Run 1's discard of
> the FIRST pin is the same race with the other ordering: the stale render carried `learning_rate` unchecked.
>
> **Rating.** P1 stands on the manual's sentence read as Phase 13 read it: the set survives the reload and a pin
> made in the next seconds, while the page is still populating, can lose it or be lost. The window is the
> F-CANOPY-004 population lag (20–40 s on a fresh session), so a user who pins right after a reload is the user it
> hits. **Fix direction (item 31):** the writer must act only on a user toggle, not on a render: take
> `dash.ctx.triggered` and return `no_update` when no checkbox value changed, or diff the rendered values against
> the State and apply only the keys whose checkbox differs from it; alternatively make the table re-render carry
> the pin set from the store as State and never re-fire the writer. Pin it with a test that re-renders the tables
> from a stale pin set after a toggle and asserts the store keeps the toggle. Re-drive the early arm on the fix.
"""

BQ_032 = f"""
> **RE-DRIVEN, FIXED (2026-10-20, Phase 14, item 30).** M-WORKERS-02 on a service leg serving canopy `{SHA}` under
> dash 4.4.1, against a throwaway cascor 0.12.0 on this host (`{RUN}/service_leg_8064_dash441.json`, steps `f032`
> and `f032_degraded`). **Arm 1, cascor stopped** (canopy had attached to it at boot; canopy falls back to demo
> mode when cascor is unreachable at ITS boot, `main.py:439-447`, so the order was cascor up, canopy up, cascor
> down): canopy's own `/api/v1/workers/list` answered HTTP 200 `{{"workers": [], "count": 0, "local_reported":
> false, "error": "Upstream error", "error_id": "4c7d6e4bcc5d"}}` and `/stats` likewise; with the Workers tab open,
> `worker-panel-error-display` rendered **`Worker data degraded: Upstream error`** (900×18, one child) on the first
> 2 s sample and on every one of the 30 that followed, the badge reading `NO WORKERS`; the first
> `_dash-update-component` response carrying `worker-panel-workers-store` held `error: "Upstream error"` (the store
> was FILLED and the render followed it). **Arm 2, the control-stream induction** (cascor restarted with
> `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://bogus.invalid:1`; cascor's log counts four `not in allowlist`
> rejections and canopy's the supervisor's reconnects): `/api/stream_health` read `overall: "degraded"` with the
> relay connected, the list route answered with no `error` key, and **no alert rendered** for 60 s, which the
> 2026-08-27 correction above calls the right behaviour. So the path this entry said never fired fires, and the
> arm that should not fire does not. Nothing in canopy's worker code changed between the measurement and now
> (canopy#533 pinned it); the render that did not happen in segment 16 is the filled-store / dead-render class
> this entry itself allowed for, F-CANOPY-027, whose fix wave (canopy#507+#509+#511) landed before the first
> re-drive could run. The entry closes on that reading; nothing here identifies which of those three repaired it.
"""

BQ_012 = f"""
> **RE-DRIVEN, FIXED (2026-10-20, Phase 14, item 30).** M-NETWORK-EDITOR-17 on a service leg serving canopy `{SHA}`
> under dash 4.4.1 against a throwaway cascor 0.12.0 on this host, restored into `Investigating` through its own
> API with a (2 inputs, 4 hidden, 2 outputs) spiral network (`{RUN}/cascor_8222_prepare.json`;
> `{RUN}/service_leg_8064_dash441.json`, step `f012`; shots `{RUN}/shots/f012_*.png`). The editor's active block
> showed `FSM: Investigating` and `Inputs: 2 Outputs: 2 Hidden units: 4`, so `output_weights` is (6, 2) = 12
> values. Nine submits, each read from the status alert AND from cascor's `/v1/network/topology` afterwards:
>
> | case | entered | status alert | landed in cascor |
> |---|---|---|---|
> | A, the manual's comma-separated floats, flat, 12 values | `0.101, 0.102, …` | `Patched output.weights (12 values, 6x2).` | yes, all 12 |
> | B, the manual's semicolon-separated floats, flat | `0.201; 0.202; …` | `Patch failed: patch_weights failed: shape mismatch: output_weights expects (6, 2), got (12, 1)` | no (unchanged) |
> | C, the manual's newline-separated floats, flat | one value per line | the same `got (12, 1)` rejection | no |
> | D, rows, one line per input/hidden unit | `0.401, 0.402` × 6 lines | `Patched output.weights (12 values, 6x2).` | yes |
> | E, rows separated by semicolons | `0.501, 0.502; …` | `Patched output.weights (12 values, 6x2).` | yes |
> | F, wrong count, flat, 11 values | | `output_weights expects (6, 2) = 12 values for this network; got 11.` | no |
> | G, `output_bias` | `0.701, 0.702` | `Patched output.bias (2 values).` | yes |
> | H, `hidden_unit_weights`, unit 0 | `0.801, 0.802` | `Patched hidden_unit.weights (2 values).` | yes |
> | I, `hidden_unit_bias`, unit 0 | `0.9` | `Patched hidden_unit.bias (1 values).` | yes |
>
> All four targets patch (the entry measured 2 of 4), the default target among them, so the documented operation
> exists. Phase 13's residue holds exactly as stated: `_parse_float_rows` reads the manual's semicolon- and
> newline-separated flat forms as one row per value and the wire rejects them, loudly and without mutating; the
> comma form reaches the reshape, and either row idiom lands. The manual's Patch Weights sentence still describes
> B and C as accepted entries, which goes to item 31. Two cases (C and E) produced no status transition in the
> driver because their message was identical to the previous case's; their outcome is read from cascor.
"""

BQ_013 = f"""
> **RE-DRIVEN, FIXED (2026-10-20, Phase 14, item 30).** M-NETWORK-EDITOR-09 and -13 on the same service leg and
> cascor as F-CANOPY-012's re-drive (`{RUN}/service_leg_8064_dash441.json`, step `f013`, run 2; run 1's append was
> refused by cascor at its own cap, `Add failed: add_hidden_unit failed: network is at max_hidden_units cap (4)`,
> a true message, after which run 1's remove made room). **M-09:** weights `0.1, 0.2, 0.3, 0.4, 0.5`, bias `0.05`,
> `Append unit` → `Appended unit at index 3 (now 4 hidden units).` at +0.4 s, cascor's topology going from 3 to 4
> hidden units: the index and the count are real. **M-13:** `Unit 3` selected, `Delete unit` → the modal (`Delete
> hidden unit #3? Subsequent units shift down by one…`), confirm → `Snapshot taken; Removed unit 3 (now 3 hidden
> units).` at +0.6 s, cascor's snapshot list 7 → 8 and its hidden units 4 → 3: the sequence (`POST
> /api/v1/snapshots` first, then the `DELETE`) and both figures are real, and the latent second instance this
> entry named is cleared with the first. The manual's step 6, "Use the API response shown in the status alert to
> confirm the edit", now confirms what happened. Shots `{RUN}/shots/f013_append.png`, `f013_remove.png`.
"""

# ----------------------------------------------------------------------------- the ledger: Phase 14
PHASE14 = f"""

## Phase 14 — 2026-10-20: item 30, the Phase 4 fix wave's live re-drive — F-CANOPY-001, -012, -013, -018 and -032 are FIXED on canopy {SHA}, F-CANOPY-028 reproduces and is re-diagnosed, and F-CANOPY-069 is filed: under every dash 3.x canopy's dashboard is inert in the browser; the open P1 count falls from 9 to 5 and the ledger carries its first open P0 since F-CANOPY-059

**Summary.**

- **The drives.** On turing (macOS; the trio is on the Linux host and was not reached), from canopy `main`
  `{SHA}` (the head after v0.9.0; every file the drives read is byte-identical to that commit by git blob id,
  `{RUN}/e2_tree_blob_sha_check.json`), on throwaway legs launched by
  `util/ad-hoc/2026-10-20_turing_canopy_leg.bash`, with the host's Google Chrome 145 driven headless by
  Playwright 1.64.0 (`util/ad-hoc/2026-10-20_item30_fixwave_redrive.py`), each row polled for its transition with
  a 30 s budget under F-CANOPY-004's contract:
  - **F-CANOPY-018, C2.9-05**, demo leg: the toast at +0.66 s, standing 14.3 s to the end of the window; Apply
    disabled and no `Unsaved changes` after it; a second edit re-enables Apply. **FIXED.**
  - **F-CANOPY-028, M-PARAMETERS-04/-05/-06**, demo leg, eight drives: the rows pass on their own expectations
    every time; **a pin was discarded in 2 of 8**, once the first pin and once the second, and the complete
    record of the second shows the mechanism: a table re-render from a stale pin set, persisted by the store
    writer. Re-diagnosed; **OPEN, P1**; fix direction in the entry, carried as item 31.
  - **F-CANOPY-001, C2.1-01/-02**, demo leg: after the reload the html carries `dark-mode` and the glyph reads
    ☀️ at +0.9 s. **FIXED.**
  - **F-CANOPY-012, M-NETWORK-EDITOR-17**, service leg against a writable cascor 0.12.0 in `Investigating` with a
    (2, 4, 2) network: all four targets patch and land; `output_weights` lands as a flat comma list and as rows
    by newline or semicolon; the manual's semicolon- and newline-separated flat forms are rejected `shape
    mismatch: output_weights expects (6, 2), got (12, 1)`, as Phase 13's residue said; a wrong count reads the
    fix's own message. **FIXED**; the residue goes to canopy's manual (item 31).
  - **F-CANOPY-013, M-NETWORK-EDITOR-09 and -13**: `Appended unit at index 3 (now 4 hidden units).` and
    `Snapshot taken; Removed unit 3 (now 3 hidden units).`, both true against cascor's topology and snapshot
    list. **FIXED.**
  - **F-CANOPY-032, M-WORKERS-02**, both arms: with cascor stopped, `Worker data degraded: Upstream error` on
    the first sample, the store carrying the error; under the control-stream-only induction, stream health
    `degraded`, no error key on the list, and no alert, which the corrected entry calls right. **FIXED** on the
    F-CANOPY-027 reading.
  - **M-METRICS-03** (F-CANOPY-026's row, already FIXED): `Phase Duration: 0m 47s` → `1m 19s` → `0m 1s` across a
    phase change of a real cascor run on a UTC−4 host, no offset inflation. **PASS.**
- **F-CANOPY-069 (P0, new).** The first leg stood up here, canopy `{SHA}` on turing's E2 env (dash 3.3.0 from
  `conda_environment.yaml`), was inert: no welcome modal, empty Parameters tables, no `_dash-update-component`
  POST on any click, zero callback POSTs in the leg's log. Cause: three callback pairs claim one
  `allow_duplicate` output with identical inputs, so their ids collide (`<id>.<prop>@sha256(inputs)`,
  `dash/_utils.py:138-162`, the same code in every dash from 3.0.4 to 4.4.1); dash 3's renderer validates the
  dependency list unconditionally, logs `Duplicate callback outputs` three times and leaves the callback graph
  empty; dash 4 runs that validation only behind `config.validate_callbacks`, so the same list passes and the
  dashboard works, which is where every earlier drive ran (the Linux host's env ships dash 4.2.0) and where
  canopy's CI runs (dash 4.4.1). Measured on five legs, one per dash: 3.0.4, 3.2.0, 3.3.0 and 3.4.0 INERT, 4.4.1
  ALIVE (`{RUN}/dash_version_matrix.json`). canopy's floor is `dash>=3.0.0`. Entry below; carried as item 32.
- **Counts.** 80 findings, 61 fixed, 1 accepted, 2 withdrawn, **16 open: 1 P0** (F-CANOPY-069), **5 P1**
  (F-CANOPY-028, -064, -065, F-CASCOR-001, -002), **10 P2**.
- **Item 30 is DONE.** Items 31 (F-CANOPY-028's fix, the manual's row idiom) and 32 (F-CANOPY-069) replace what
  it leaves. Every future leg runs dash 4.x until 32 lands.

### Who, and from what

- **Host and tree.** turing (macOS 15.7, Intel), the E2 bring-up's canopy tree
  `~/.local/state/juniper/turing-e2/trees/juniper-canopy`, an rsync of the primary checkout with `.git`
  excluded. Its serving commit is proved, not assumed: `util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py`
  computes each file's git blob id (sha1 over `blob <len>\\0<bytes>`, no git binary) and compares it with the
  GitHub contents API at `{SHA}`; `src/frontend/dashboard_manager.py`, the four panels the drives read,
  `src/main.py`, `src/demo_mode.py`, `src/settings.py`, `pyproject.toml` and `docs/USER_MANUAL.md` all MATCH
  (`{RUN}/e2_tree_blob_sha_check.json`). The legs stamp that sha on `/v1/health` (`git_sha`), and every record
  carries the leg's own report of it.
- **Legs.** `util/ad-hoc/2026-10-20_turing_canopy_leg.bash` (mirrors the Linux-host launcher's env, nested
  `SERVER__` names included; demo legs point cascor and juniper-data at a closed port; a service leg names its
  cascor) and `util/ad-hoc/2026-10-20_turing_cascor_leg.bash` (cascor 0.12.0 from the E2 tree, no juniper-data,
  every auto-start off, its WS control allowlist naming the canopy leg). Five scratch venvs over the E2 conda env
  (`~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1{{,-dash32,-dash34,-dash44,-dash304}}`), one dash each.
  The drives ran on dash 4.4.1 (`requirements.lock:32`; canopy's CI UI lane installs it too), ports 8062 (demo)
  and 8064 (service, cascor on 8222). `util/ad-hoc/2026-10-20_cascor_leg_prepare_investigating.py` trained the
  in-process spiral fallback (max 4 hidden units, 1500 epochs, 555 s), snapshotted it
  (`snapshot_20261020T121441Z`) and restored it: FSM `INVESTIGATING`, topology (2, 4, 2). The restore went
  through cascor's API, not the Snapshots tab (W5-07 is PASS since Phase 2 and is not an item 30 row).
- **Browser.** Playwright 1.64.0 over the installed Google Chrome 145 (`channel="chrome"`; no browser download).
  On turing outbound connections are filtered per application (Little Snitch, see the turing notes), and the
  dashboard's one external resource, `dbc.themes.BOOTSTRAP` from `cdn.jsdelivr.net`, never resolves for Chrome
  (readyState `loading` for 100 s; the same URL answers curl in 0.1 s). The stylesheet held `DOMContentLoaded`
  for the whole navigation timeout, so the harness aborts that one request in the browser (`_route_cdn`): the
  page runs unstyled, nothing is fetched on Chrome's behalf by another binary, and **the VIS halves of the rows
  are not scored by this phase**; every verdict here is DOM, store, request/response or cascor state.
- **Records.** `{RUN}/`: `demo_leg_8062_dash441.json` (f018 run 2, f001 run 2, f028's six arms, m03 on demo),
  `service_leg_8064_dash441.json` (m03 during the run, f012, f013 run 2, f032, f032_degraded),
  `cascor_8222_prepare.json`, `dash_version_matrix.json`, `e2_tree_blob_sha_check.json`,
  `demo_leg_8058.json` (the inert first leg), `transcripts/` (every run, including the overwritten ones) and
  `shots/` (20 PNGs). The inert leg's run and this run's run 1 are kept as transcripts: a later run of the same
  step overwrites its key in the JSON.

### The legs, and why the first one was inert

The first leg (port 8058, the E2 venv, dash 3.3.0) answered `/v1/health` and served the page, and nothing on it
worked: `f018` read Apply disabled with an empty status and could not find the optimizer's options; `f028` found
0 pin checkboxes and tables with 0 rows; `f001`'s click changed nothing; `m03` read an empty duration. The
renderer's console carried three errors at load, `Duplicate callback outputs` for `live-switch-progr…` (twice)
and `restart-confirm-m…`, and the leg's log had **0** `_dash-update-component` lines. Parsed from
`GET /dashboard/_dash-dependencies` (181 callbacks), three output ids are claimed twice:
`live-switch-progress-alert.is_open@fc8c1589…` and `live-swap-in-flight-store.data@fc8c1589…` (by
`accept_live_switch`, `dashboard_manager.py:6310-6331`, and `open_progress_alert_on_accept`, `:6333-6342`, both
on the single Input `live-switch-accept-button.n_clicks`) and `restart-progress-alert.is_open@b7e1c13f…` (by
`open_restart_progress`, `:6468-6476`, and `execute_restart`, `:6478-6507`, both on
`restart-confirm-button.n_clicks`). `util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py` then measured
one leg per dash, the same tree and the same ids on every one:

| dash | duplicate ids served | renderer errors | welcome modal | Parameters rows | POST after a click | verdict |
|---|---|---|---|---|---|---|
| 3.0.4 | 3 | 3 | no | 0 | none in 30 s | INERT |
| 3.2.0 | 3 | 3 | no | 0 | none | INERT |
| 3.3.0 (canopy's `conda_environment.yaml:93`; turing's E2 env) | 3 | 3 | no | 0 | none | INERT |
| 3.4.0 | 3 | 3 | no | 0 | none | INERT |
| 4.4.1 (`requirements.lock:32`; CI) | 3 | 0 | yes | 9 | +0.3 s | ALIVE |

The Python side is the same everywhere: `create_callback_id` (`dash/_utils.py:138-162`, read in the 3.0.4,
3.1.1, 3.2.0, 3.3.0, 3.4.0 and 4.4.1 wheels) suffixes an `allow_duplicate` output with `@sha256(".".join(str(x)
for x in inputs))`, so two callbacks with the same output and the same inputs get the same id, and the server
registers both. The renderer differs in one line: dash 3's `computeGraphs` calls `validateDependencies`
unconditionally (`dash_renderer.dev.js:77452` in 3.3.0) and, on any error, returns the empty graphs ("leave the
graphs empty if we found an error, so we don't try to execute the broken callbacks", `:77488-77492`); dash 4.4.1
calls it only `if (config.validate_callbacks)` (`:6810-6812`) and otherwise builds the graph over the colliding
ids. Which member of a colliding pair the dash 4 graph runs on a click was not measured (neither the Live Switch
accept nor the restart confirm is an item 30 row); every earlier drive in this ledger ran under dash 4.2.0
(canopy `CHANGELOG.md:702`, `:1507`, the Linux host's `JuniperCanopy1`), and canopy's CI UI lane under 4.4.1
(`33 passed, 1 deselected, 1 xfailed` at `{SHA}`, run 39339405624), which is why nothing green ever showed it.

### The drives, row by row

- **f018 (C2.9-05).** Run 1 under a 3 s mount settle: toast `Applied 22 of 25 parameter(s); 3 not yet supported
  by the backend: …` at +1.9 s, standing 13.0 s; Apply disabled from +5 s on; the pre-click `⚠️ Unsaved changes`
  still on screen at +0.3 s tripped a first "latched" rule, corrected to count only `Unsaved changes` after the
  toast. Run 2 under the 25 s settle: toast at +0.66 s, standing 14.3 s; CLEAN; RETRACK (a second dropdown change
  re-enabled Apply at once). `/api/state` does not report `nn_optimizer_type` on the demo backend, so "the apply
  landed" is read from the toast's own accounting (22 of 25) rather than from state.
- **f028 (M-PARAMETERS-04/-05/-06).** Eight drives in four runs; the arms and their outcomes are in F-CANOPY-028's
  RE-DIAGNOSED blockquote. The rows' own expectations: M-04 store `["learning_rate"]` in 1.0–2.3 s; M-05 the card
  shown in 0.5–1.2 s reading `Learning Rate 0.01` (the value arm the matrix had pending lands: the params store
  fills); M-06 unpin → `[]` and the card hidden in 1.5–2.1 s, both surviving a reload.
- **f001 (C2.1-01/-02).** Run 1 read at a fixed +3 s and missed the click's render (html flipped at +2.3 s, the
  glyph at +0.3 s in run 2; the second click's flip took 5.4 s); run 2 polled. After the reload: early read
  (+3 s) already `dark-mode` + ☀️; synced at +0.9 s.
- **m03 (M-METRICS-03).** On the demo leg, `Phase Duration: 0m 7s` → `0m 34s` over 30 s (an observation; the
  demo backend stamps its own clock). On the service leg, sampled every 5 s while cascor trained the entry
  network: six empty reads while the panel populated, then `0m 47s`, `0m 59s`, `1m 3s`, `1m 9s`, `1m 15s`,
  `1m 19s`, then `0m 1s` and `0m 5s` after a phase change. This host is UTC−4; the inflation F-CANOPY-026
  measured would read about four hours. PASS, cascor#594 + canopy#534 both halves on cascor 0.12.0.
- **f012 (M-NETWORK-EDITOR-17)** and **f013 (M-NETWORK-EDITOR-09, -13).** In the entries. One point of method:
  canopy's editor POSTs cascor from its Dash callback, so the browser sees only `_dash-update-component`; every
  effect is read from cascor's `/v1/network/topology` and `/v1/snapshots` before and after each submit.
- **f032 (M-WORKERS-02).** In the entry. The cascor-down arm needed the order cascor up → canopy up → cascor down:
  a service-mode canopy whose cascor is unreachable at boot falls back to demo mode (`main.py:439-447`), and the
  leg first stood up for this arm did exactly that (`/v1/health` `demo_mode: true` with `JUNIPER_CANOPY_DEMO_MODE=0`),
  which is a note for any future cascor-down leg, not a finding: it is the documented fallback.

### F-CANOPY-069

**F-CANOPY-069 — under every dash 3.x release canopy's dashboard is inert in the browser: three callback pairs claim one `allow_duplicate` output with identical inputs, their ids collide, and the dash 3 renderer drops the whole callback graph; canopy's own `conda_environment.yaml` pins dash 3.3.0 (P0 in any environment resolving dash 3.x, which the floor `dash>=3.0.0` admits; not reached from `requirements.lock`, CI or a fresh pip resolve, all dash 4.x; found 2026-10-20, Phase 14, on turing's E2 env; OPEN).**
Measured on canopy `main` `{SHA}` on five legs from one tree, one per dash release
(`{RUN}/dash_version_matrix.json`; `util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py`): under
dash 3.0.4, 3.2.0, 3.3.0 and 3.4.0 the page loads, the renderer logs `Duplicate callback outputs` three times, the
welcome modal never opens, the Parameters tables render 0 rows, a click on the theme toggle sends no
`_dash-update-component` POST in 30 s, and the leg's log carries no callback POST at all; under dash 4.4.1 the same
tree serves the same 181 callbacks with the same three colliding ids, logs nothing, opens the modal, renders 9
rows and POSTs 0.3 s after the click. The colliding ids, from `GET /dashboard/_dash-dependencies`:
`live-switch-progress-alert.is_open@fc8c1589…` and `live-swap-in-flight-store.data@fc8c1589…`, claimed by
`accept_live_switch` (`src/frontend/dashboard_manager.py:6310-6331`) and `open_progress_alert_on_accept`
(`:6333-6342`), both with the single Input `live-switch-accept-button.n_clicks`; and
`restart-progress-alert.is_open@b7e1c13f…`, claimed by `open_restart_progress` (`:6468-6476`) and
`execute_restart` (`:6478-6507`), both with `restart-confirm-button.n_clicks`. The hash is of the inputs
(`dash/_utils.py:138-162`, `create_callback_id`, identical in every wheel read: 3.0.4, 3.1.1, 3.2.0, 3.3.0, 3.4.0,
4.4.1), so `allow_duplicate=True` on both members of a pair does not separate them: the server registers both
under one id, and what happens next is the renderer's. dash 3's `computeGraphs` validates the dependency list
unconditionally and, on any error, returns empty graphs (`dash_renderer.dev.js:77452`, `:77488-77492` in 3.3.0);
dash 4.4.1 validates only `if (config.validate_callbacks)` (`:6810-6812`), which is off, so the pairs go unchecked.
**Why it is green everywhere:** the Python side raises nothing (the duplicate check that would is what
`allow_duplicate` disables); canopy's unit and integration suites (7,947 and 523 passed on turing under dash
3.3.0, E2) never render; the UI sub-suite runs in CI under dash 4.4.1 (`conda_environment_ci.yaml:126` pins 4.1.0
for the conda lane; `requirements_ci.txt:169` is `dash>=3.0` and resolves to 4.4.1) where the validation is off;
and every live drive this ledger records ran on the Linux host's `JuniperCanopy1`, dash 4.2.0 (canopy
`CHANGELOG.md:702`, `:1507`). **Where it bites:** any environment that resolves dash to 3.x, which the floor
`dash>=3.0.0` (`pyproject.toml:56`; `requirements.txt:169`) admits and which canopy's own
`conda_environment.yaml:93` (`dash=3.3.0=pyhd8ed1ab_0`, conda-forge's current build) produces; the E2 env on
turing was built from it. A user there sees a styled, populated-looking page with every control dead and no
message on screen (the errors go to the console; dev tools are off). **Rating:** P0, "blocks a mandate-named
workflow": every workflow, in that environment. The counter-reading is recorded: by the pip path a fresh install
resolves dash 4.4.1 and works, and the floor is a declaration, so P1 ("breaks a documented behaviour", the
declared compatibility). It is rated on the repo's own conda file. **Not measured:** which member of each pair
dash 4's graph runs on a click, and whether the other ever fires (the Live Switch accept and the restart confirm
are not item 30 rows); that is the same pair of callbacks under the version that works, and it is the first thing
item 32 should read. **Fix direction (item 32):** give each pair distinct inputs or make it one callback (the
progress alert is what Dash's `running=` argument on the long callback exists for), raise the floor to the dash
the lock and CI already use if dash 3 is not to be supported, and correct `conda_environment.yaml` either way;
pin it with a test that computes the ids as `create_callback_id` does over `app.callback_map` and asserts no two
callbacks share one, which fails on this tree under every dash. Blast radius on dash 3.x: every row of the
matrix; on dash 4.x: unknown for the two surfaces named.

### What this phase cannot support

- **One host, one browser, no trio.** Every figure is from turing, Chrome 145 headless under Playwright, legs
  launched from the E2 tree. The trio on the Linux host was not reached; items 25 and 28 still need it.
- **dash 4.4.1, not 4.2.0.** The drives ran under the dash canopy's lock and CI use, not the 4.2.0 the Linux
  host's env ships. Nothing here says the two differ for these rows; nothing here measured it.
- **Unstyled pages.** With the CDN stylesheet aborted, no VIS half of any row is scored; the modal, the alerts
  and the card were read by DOM, text, computed display and store, and the screenshots show an unstyled page.
- **Timing figures are this host's.** turing is a 16 GiB laptop running four other sessions; the latencies here
  (a click's render in 0.3–5.4 s, population in 20–30 s) fit F-CANOPY-004's contract and are not comparable with
  the trio's.
- **F-CANOPY-028's first discard is a transcript, not a record.** Run 1's JSON was overwritten by run 2 before
  its response capture was saved; the discard rests on the run-1 transcript's store read and on the reconciler's
  read of the response capture before it was lost. The second discard (run 4, early#2) is complete, with the
  writer's request bodies.
- **F-CANOPY-032 closes on a reading.** The alert renders now and did not in segment 16; nothing here names
  which of canopy#507, #509 or #511 repaired it, and the cascor-down arm here used a cascor stopped by `kill`,
  not the trio's.
- **F-CANOPY-069's dash 4 behaviour is not measured.** The dashboard works under dash 4 for every row driven;
  the two surfaces whose callbacks collide were not driven.
- **F-CANOPY-018's demo leg** does not exercise the three keys the fix removed from the comparison against a
  backend that applies them; the latch, which was the symptom, is gone.

### Consensus record (§7 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`)

_(filled by the round scripts)_

### Matrix effect and counts

- `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`: C2.9-05 FAIL → PASS (re-validated @
  `{SHA}`); M-NETWORK-EDITOR-09, -13 and -17 → PASS (re-validated @ `{SHA}`), the FAIL halves gone; M-WORKERS-02
  FAIL → PASS (re-validated @ `{SHA}`); M-METRICS-03 FAIL → PASS (re-validated @ `{SHA}` + cascor 0.12.0);
  C2.1-01 and C2.1-02 → PASS (re-validated @ `{SHA}`), the F-CANOPY-001 note cleared; M-PARAMETERS-04, -05 and
  -06 → PASS (re-validated @ `{SHA}`), M-05's pending value arm landed, M-06 carrying the F-CANOPY-028 note.
- `python3 util/ad-hoc/e2e_finding_triage.py`: 80 findings, 61 fixed, 1 accepted, 2 withdrawn, 16 open; open P0
  1 (F-CANOPY-069), open P1 5 (F-CANOPY-028, -064, -065, F-CASCOR-001, -002), open P2 10.
- The five closed entries' headers carry FIXED in their last 170 characters and their first severity token is
  unchanged; F-CANOPY-028's and F-CANOPY-069's tails carry OPEN and no other disposition word.

### Still owed after this phase

Phase 13's list stands, items 0 to 30, with these changes:

- **Item 30 is DONE**: every row it names was driven on a leg serving canopy 0.9.0's head, and each entry's
  header changed on its own row's result. What it leaves is below as items 31 and 32.
- **Items 25 and 28** are unchanged (the trio, the Linux host). **Item 27** is unchanged; a demo leg on this host
  under dash 4.x can serve it now (`2026-10-20_turing_canopy_leg.bash up <port> demo`, the experimental toggle
  on). **Item 29** is unchanged. **Item 26's second step** is unchanged; its F-CANOPY-012 and F-CANOPY-013 leads
  are moot, both FIXED.
- **Every leg runs dash 4.x until item 32 lands.** A leg on dash 3.x drives nothing (F-CANOPY-069); the launcher
  takes the interpreter as its fifth argument and prints the dash it found.

New items:

31. **F-CANOPY-028's fix, and the manual's row idiom.** (a) The pin-store writer must act on a user toggle only
    (F-CANOPY-028's RE-DIAGNOSED blockquote: `ctx.triggered`, or a diff against the State), with a test that
    re-renders the tables from a stale pin set after a toggle and asserts the store keeps the toggle; re-drive
    `2026-10-20_item30_fixwave_redrive.py --step f028 --f028-arms early,mid --f028-repeat 3` on the fix.
    (b) canopy's `docs/USER_MANUAL.md` Patch Weights sentence (`:493-501` at `{SHA}`) says `output_weights`
    takes "comma-, semicolon-, or newline-separated floats"; on the fix the semicolon and newline forms are
    rows, and a flat list in either is rejected on any network with more than one output (F-CANOPY-012's
    table, cases B and C). Either the sentence gets the row idiom or `_parse_float_rows` a single-width rule;
    the former is the smaller change and matches what the panel does.
32. **F-CANOPY-069.** First read which member of each colliding pair dash 4's graph runs on a click (the Live
    Switch accept, the restart confirm) on a dash 4.4.1 leg; then the fix (distinct inputs or one callback per
    pair, the `running=` idiom for the progress alerts), the floor (`dash>=3.0.0` admits what does not work;
    the lock and CI are on 4.4.1), `conda_environment.yaml` (dash 3.3.0 today), and a test over
    `app.callback_map` that fails on this tree. Re-run `2026-10-20_canopy_dash_duplicate_outputs_probe.py` on a
    dash 3.3.0 leg of the fix: ALIVE closes it.
"""

# ----------------------------------------------------------------------------- the matrix
MATRIX_ROWS = [
    ("| C2.1-01 |", "| PASS |", f"| PASS (re-validated @ {SHA}, 2026-10-20, item 30: the glyph swapped at +0.3 s, the html class at +2.3 s) |"),
    ("| C2.1-02 |", "| PASS(stated expectation) — F-CANOPY-001 re-confirmed live on d11bfcd |", f"| PASS (re-validated @ {SHA}, 2026-10-20, item 30: the dark theme restored AND the glyph read ☀️ at +0.9 s after the reload — F-CANOPY-001 FIXED) |"),
    ("| C2.9-05 |", "| FAIL (F-CANOPY-018) |", f"| PASS (re-validated @ {SHA}, 2026-10-20, item 30, demo leg: `Applied 22 of 25 parameter(s); 3 not yet supported by the backend: …` at +0.7 s, standing 14 s to the end of the window; Apply disabled and no `Unsaved changes` after it — F-CANOPY-018 FIXED) |"),
    ("| M-METRICS-03 |", "| FAIL |", f"| PASS (re-validated @ {SHA} + cascor 0.12.0, 2026-10-20, item 30: `Phase Duration: 0m 47s` → `1m 19s` → `0m 1s` across a phase change of a live run on a UTC−4 host, no offset inflation — F-CANOPY-026) |"),
    ("| M-WORKERS-02 |", "| FAIL |", f"| PASS (re-validated @ {SHA}, 2026-10-20, item 30: `Worker data degraded: Upstream error` on the first sample with cascor stopped; correctly absent under the control-stream-only induction — F-CANOPY-032 FIXED) |"),
    ("| M-PARAMETERS-04 |", "| PASS |", f"| PASS (re-validated @ {SHA}, 2026-10-20, item 30: the store write lands in 1.0–2.3 s) |"),
    ("| M-PARAMETERS-05 |", "| PASS (name arm; value pending an Apply) |", f"| PASS (re-validated @ {SHA}, 2026-10-20, item 30: name AND value, `Learning Rate 0.01`, the card shown in 0.5–1.2 s) |"),
    ("| M-PARAMETERS-06 |", "| PASS |", f"| PASS (re-validated @ {SHA}, 2026-10-20, item 30; but F-CANOPY-028 stands: a pin made while the tables re-render from a stale pin set is discarded, 2 of 8 drives) |"),
    ("| M-NETWORK-EDITOR-09 |", "| PASS(request path) / FAIL(status message -- F-CANOPY-013) |", f"| PASS (re-validated @ {SHA}, 2026-10-20, item 30: `Appended unit at index 3 (now 4 hidden units).`, cascor 3 → 4 — F-CANOPY-013 FIXED; at cascor's cap the alert reads `network is at max_hidden_units cap (4)`) |"),
    ("| M-NETWORK-EDITOR-13 |", "| PASS(sequence + effect) / FAIL(status message -- F-CANOPY-013) |", f"| PASS (re-validated @ {SHA}, 2026-10-20, item 30: `Snapshot taken; Removed unit 3 (now 3 hidden units).`, snapshots 7 → 8, cascor 4 → 3 — F-CANOPY-013 FIXED) |"),
    ("| M-NETWORK-EDITOR-17 |", "| PASS(2 of 4 targets) / FAIL(default target -- F-CANOPY-012) |", f"| PASS (re-validated @ {SHA}, 2026-10-20, item 30: 4 of 4 targets; `output_weights` lands as a flat comma list and as rows by newline or semicolon; the manual's semicolon- and newline-separated flat forms are rejected `shape mismatch: output_weights expects (6, 2), got (12, 1)`; a wrong count reads `output_weights expects (6, 2) = 12 values for this network; got 11.` — F-CANOPY-012 FIXED, the residue stands, item 31) |"),
]

# ----------------------------------------------------------------------------- the handoffs
HANDOFF_TEXT = f"""# HANDOFF 2026-10-20 — P2 canopy Lane A: Phase 14 recorded. Item 30 is DONE: F-CANOPY-001, -012, -013, -018 and -032 are FIXED on canopy {SHA}; F-CANOPY-028 reproduced (2 of 8) and is re-diagnosed; F-CANOPY-069 (P0) is filed: canopy's dashboard is inert under every dash 3.x. 1 open P0, 5 open P1, 10 open P2. Next are items 31, 32, 25, 27 and 28.

**Written**: 2026-10-20 by the session in juniper-ml worktree `.claude/worktrees/serialized-noodling-cray` on host
turing (macOS; no trio; throwaway legs from the E2 tree), at a phase boundary, as its PR was opened.
**Consensus**: see the ledger's Phase 14 consensus record.
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`, authoritative for P2.
Its items 5 and 7 and the owner batch O1–O17 carry over. This file supersedes
`HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`.
**Merge approval**: the owner granted it for this session's PR. It is NOT carried: ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A (the juniper-canopy E2E validation arc) from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`
(juniper-ml). Read it in full, then the parent `HANDOFF_2026-10-03_canopy-consolidated.md`. Run the verification
commands first. Merge approval is not carried: ask before the first merge. Items 31 and 32 are canopy code (fix
PRs on juniper-canopy, verified on a leg; a leg on this host runs dash 4.x until 32 lands); items 25 and 28 need
the trio on the Linux host; item 27 needs a demo leg that trains (this host can serve it).

**Completed:**

- **juniper-ml#2278 merged** on 2026-10-20T02:22:45Z: the ledger's Phase 13 and the previous handoff.
- **The ledger's Phase 14** (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, 2026-10-20) does
  item 30 on turing, from canopy `main` `{SHA}` proved by git blob id, on legs under dash 4.4.1 with Chrome 145
  under Playwright:
  - **FIXED**: F-CANOPY-018 (C2.9-05: the toast stands, Apply disables, no latch), F-CANOPY-001 (C2.1-01/-02: the
    glyph syncs after a reload), F-CANOPY-012 (M-NETWORK-EDITOR-17: 4 of 4 targets; the manual's semicolon and
    newline flat forms are rejected as Phase 13's residue said), F-CANOPY-013 (M-NETWORK-EDITOR-09/-13: real index
    and count), F-CANOPY-032 (M-WORKERS-02: the alert renders with cascor down, not under the control-stream
    induction; closed on the F-CANOPY-027 reading). M-METRICS-03 PASS on a live cascor run.
  - **F-CANOPY-028 stays OPEN (P1), re-diagnosed**: 2 of 8 drives discarded a pin; the complete record shows a
    table re-render from a stale pin set persisted by the store writer, which canopy#533 did not address.
  - **F-CANOPY-069 (P0, new)**: three callback pairs with one `allow_duplicate` output and identical inputs collide;
    dash 3's renderer drops the whole graph, dash 4 does not validate. Inert on 3.0.4/3.2.0/3.3.0/3.4.0, alive on
    4.4.1 (`reports/e2e-canopy-2026-09-02/item30-turing/dash_version_matrix.json`). canopy's floor is
    `dash>=3.0.0`; its `conda_environment.yaml` pins 3.3.0; the lock, CI and the Linux host are on 4.x.
  - **Counts**: 80 findings, 61 fixed, 1 accepted, 2 withdrawn, 16 open: 1 P0 (F-CANOPY-069), 5 P1 (F-CANOPY-028,
    -064, -065, F-CASCOR-001, -002), 10 P2.
- **This session's PR** carries the ledger, the matrix, this file, the SUPERSEDED banner, the parent's pointer, the
  INDEX's P2 row, the records under `reports/e2e-canopy-2026-09-02/item30-turing/`, Phase 14's consensus records
  and the scripts `util/ad-hoc/2026-10-20_*`. Find it with
  `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase14 --state all`.

**Remaining, in order:**

1. **Land this session's PR** if it has not merged: `python3 util/wait_for_checks.py`, query
   `reviewThreads(isResolved:false)`, ask the owner, then `python3 util/safe_merge.py --execute` and read its
   `MERGED` line. Afterwards re-check `origin/main`: `grep -c 'FIXED' <(grep -E '^\\*\\*F-CANOPY-(001|012|013|018|032) ' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md)` should print 5.
2. **Item 32, F-CANOPY-069** (canopy code): read which member of each colliding pair runs under dash 4.4.1; fix the
   pairs (distinct inputs or one callback; `running=` for the progress alerts); decide the floor; correct
   `conda_environment.yaml`; a test over `app.callback_map`; verify with
   `util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py` on a dash 3.3.0 leg of the fix (ALIVE closes it).
3. **Item 31, F-CANOPY-028** (canopy code): the writer acts on a user toggle only; a stale-re-render test; re-drive
   `util/ad-hoc/2026-10-20_item30_fixwave_redrive.py --step f028 --f028-arms early,mid --f028-repeat 3` on the fix
   (a demo leg on dash 4.x). And the manual's Patch Weights sentence (row idiom for `output_weights`).
4. **Item 27** (the Live Switch allow arm): a demo leg on this host serves it
   (`bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash up 8062 demo http://127.0.0.1:9 ~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python`,
   then `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py` adapted to the chrome channel and the CDN route).
5. **Items 25 and 28** on the Linux host, against the trio (ledger Phase 12). **Item 29**, the Linux host.
6. **Item 26's second step** once the owner rules (O17).
7. Then the parent's items 5 and 7, and the owner batch O1–O17.

**Traps learned:**

- **A leg on dash 3.x drives nothing** (F-CANOPY-069). Check `/dashboard/_dash-dependencies` for duplicate ids and
  the console for `Duplicate callback outputs` before blaming a driver; the launcher prints the dash it found.
- **canopy falls back to demo mode when cascor is unreachable at boot** (`main.py:439-447`): a cascor-down arm is
  cascor up → canopy up → cascor down, never canopy up against nothing.
- **On turing Chrome cannot fetch cdn.jsdelivr.net** (per-app filter; curl can). The drivers abort that one request
  in the browser; pages are unstyled; VIS halves are not scored. Do not fetch it through another binary.
- **Wait for the mount.** An edit before the mount seed lands is overwritten by it (a typed learning rate reverted
  at +2 s); the drivers settle 25 s and poll every transition with a 30 s budget.
- **A later run overwrites a step's key in the record JSON.** Keep the transcripts; name a new `--out` for a run
  whose record must survive (run 1's F-CANOPY-028 discard is a transcript only).
- **The guard refuses** `for` loops with `gh`/`unzip`, `awk` programs, `$(…)` in command text and env prefixes;
  one plain command per call, interpreters by path, logic in a script.
- **turing has no signing**: land through `util/open_signed_pr.py` (small files) and
  `util/ad-hoc/2026-10-17_push_signed_with_retry.py` (the ledger); build shared files from a fresh `origin/main`
  copy and re-apply with `util/ad-hoc/2026-10-20_phase14_item30_apply.py --root <copy>` plus the round scripts.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/<your worktree>   # or the Linux host's path
git status --short; git log --oneline -3
gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase14 --state all --json number,state,mergedAt
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -8   # 80 / 61 / 1 / 2 / 16; P0 1; P1 5; P2 10
python3 -B util/ad-hoc/e2e_finding_triage.py --open-only | grep -c '^OPEN   P1 '   # 5
grep -n '^## Phase 14' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md
grep -c 'F-CANOPY-069' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md
python3 -I -c "import json; m=json.load(open('reports/e2e-canopy-2026-09-02/item30-turing/dash_version_matrix.json')); print({{k: v['verdict'] for k, v in m.items()}})"   # four INERT, one ALIVE
ls ~/.local/state/juniper/turing-e2/venvs/   # on turing: JuniperCanopy1{{,-dash304,-dash32,-dash34,-dash44}}
lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8101|8202|8051|8052|8053|806[0-9]|8222) '   # on turing: nothing; on the Linux host: the trio up (never touch it)
```

## Git state

- **juniper-ml:** branch `docs/canopy-e2e-phase14`, landed from turing through the API as signed commits.
  Worktree `serialized-noodling-cray` holds the same files uncommitted (the frozen drafts the consensus rounds
  reviewed are local commits that never leave the host).
- **juniper-canopy, cascor:** no branches from this session; read through the GitHub API and the E2 tree
  (canopy `main` `{SHA}`; cascor 0.12.0 as rsynced on 2026-10-19).
- **Services:** none left on this host; the legs were torn down (`… down <port>`). The scratch venvs and the
  snapshots under `~/.local/state/juniper/turing-e2/legs/` remain.

## Changed by this session

- **Created:** this file; `util/ad-hoc/2026-10-20_turing_canopy_leg.bash`;
  `util/ad-hoc/2026-10-20_turing_cascor_leg.bash`; `util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py`;
  `util/ad-hoc/2026-10-20_item30_fixwave_redrive.py`; `util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py`;
  `util/ad-hoc/2026-10-20_cascor_leg_prepare_investigating.py`; `util/ad-hoc/2026-10-20_phase14_item30_apply.py`;
  `reports/e2e-canopy-2026-09-02/item30-turing/` (records, transcripts, shots);
  `reports/e2e-canopy-2026-09-02/drafts/lane14*_phase14_ledger_brief.md`;
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase14_round*.md`;
  `util/ad-hoc/2026-10-20_phase14_ledger_round*_corrections.py`.
- **Modified:**
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: Phase 14; the headers of F-CANOPY-001,
    -012, -013, -018, -028 and -032 and a dated blockquote in each; the F-CANOPY-069 entry;
  - `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`: eleven status cells;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`: the Lane A pointer;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: the P2 row;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`:
    the SUPERSEDED banner.
- **Outside the repo**, in auto-memory: `MEMORY.md`, `canopy-e2e-arc-state.md`, `turing-host-profile.md`,
  `turing-little-snitch-per-app-filter.md`.
"""

BANNER = """
> **SUPERSEDED 2026-10-20** by `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`.
> Its item 1 (juniper-ml#2278 merged 2026-10-20T02:22:45Z) and item 2 (item 30, the fix wave's live re-drive, recorded
> as Phase 14 of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: F-CANOPY-001, -012, -013, -018
> and -032 FIXED, F-CANOPY-028 re-diagnosed and open, F-CANOPY-069 filed) are done; items 3 to 8 carry there as items
> 25, 26, 27, 28 and 29 with new items 31 and 32.
"""

PARENT_OLD = """   Current Lane A handoff:
   `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`. The status as of 2026-10-08
   follows, for context."""
PARENT_NEW = f"""   Phase 14 (2026-10-20, on turing) did item 30: F-CANOPY-001, -012, -013, -018 and -032 are FIXED on canopy
   `{SHA}`, F-CANOPY-028 reproduced (2 of 8 drives) and is re-diagnosed, and F-CANOPY-069 (P0) is filed: the
   dashboard is inert under every dash 3.x (triage 80/61/1/2/16, 1 open P0, 5 open P1, 10 open P2).
   Current Lane A handoff:
   `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`. The status as of 2026-10-08
   follows, for context."""

INDEX_OLD_PTR = "(Lane A's current one: `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`)"
INDEX_NEW_PTR = "(Lane A's current one: `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`)"
INDEX_OLD_TAIL = "Next: items 25 (census triggers from the page), 27 (the Live Switch allow arm), 28 (first live run on the shipped pacer) and 30 (the fix wave's re-drive). Y2 wave 2 is stalled at round 15."
INDEX_NEW_TAIL = (
    f"Phase 14 (2026-10-20, on turing, legs from canopy `{SHA}` under dash 4.4.1) did item 30: F-CANOPY-001, -012, -013, -018 and -032 are FIXED, F-CANOPY-028 reproduced (2 of 8 drives) and is re-diagnosed, and F-CANOPY-069 (P0) is filed: canopy's dashboard is inert under every dash 3.x (three `allow_duplicate` callback pairs with identical inputs collide; dash 4 does not validate); 80/61/1/2/16, 1 open P0, 5 open P1, 10 open P2. "
    "Next: items 32 (F-CANOPY-069, canopy code), 31 (F-CANOPY-028, canopy code; the manual's Patch Weights idiom), 27 (the Live Switch allow arm, a demo leg on turing can serve it), 25 and 28 (the trio). Y2 wave 2 is stalled at round 15."
)


# ----------------------------------------------------------------------------- mechanics
def replace_once(text: str, old: str, new: str, what: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"anchor for {what} occurs {n} times, expected 1: {old[:90]!r}")
    return text.replace(old, new, 1)


def first_pri(body: str) -> str:
    m = _PRI_RE.search(body)
    return m.group(1) if m else "?"


def check_header(new_header: str, want_pri: str, want_disp: str) -> None:
    body = new_header[2:-2]
    assert first_pri(body) == want_pri, (first_pri(body), want_pri, new_header[:80])
    tail = body[-170:]
    fixed = bool(re.search(r"\bFIXED\b|\bHEALED\b", tail, re.I))
    if want_disp == "FIXED":
        assert fixed, f"tail lacks FIXED: {tail!r}"
    else:
        assert not fixed, f"tail carries fixed: {tail!r}"
        assert not re.search(r"\bACCEPTED\b|\bWITHDRAWN\b", tail, re.I), tail


def apply(root: Path, check_only: bool) -> None:
    ledger_p = root / LEDGER
    ledger = ledger_p.read_text(encoding="utf-8")
    assert "## Phase 14" not in ledger, "Phase 14 is already applied"
    assert "F-CANOPY-069" not in ledger, "F-CANOPY-069 already present"
    for old, new, pri, disp in HEADERS:
        check_header(new, pri, disp)
        ledger = replace_once(ledger, old, new, f"header {old[:20]}")
    # blockquotes: after the last line of each entry's existing closing text
    anchors = [
        ("Screenshots: `C2.1-01__dark.png` (correct ☀️ pre-reload), `C2.1-02__reload-glyph-desync.png` (dark theme + 🌙). Matrix rows C2.1-01/02 — both PASS on their stated expectations; this is a ledger finding, not a row FAIL.\n", BQ_001, "F-001 blockquote"),
        ("> and toast are canopy-side, so a demo leg is expected to reach them, to be confirmed on the drive.\n", BQ_018, "F-018 blockquote"),
        ("> stays OPEN until M-PARAMETERS-04/-05/-06 are re-driven on a leg serving that code (item 30).\n", BQ_028, "F-028 blockquote"),
        ("> re-diagnoses it; until it runs this is the one open P1 of Phase 13 with no fix in code.\n", BQ_032, "F-032 blockquote"),
        ("> then needs the row idiom, or the parser a single-width rule.\n", BQ_012, "F-012 blockquote"),
        ("> M-NETWORK-EDITOR-09 and -13 are re-driven on a leg serving that code (item 30).\n", BQ_013, "F-013 blockquote"),
    ]
    for anchor, bq, what in anchors:
        ledger = replace_once(ledger, anchor, anchor + bq, what)
    ledger = ledger.rstrip("\n") + "\n" + PHASE14
    # the F-069 header must triage as P0 OPEN
    m = re.search(r"^\*\*(F-CANOPY-069) — (.*?)\*\*", ledger, re.M | re.S)
    assert m, "F-069 header not found after apply"
    check_header("**" + m.group(2) + "**", "P0", "OPEN")

    matrix_p = root / MATRIX
    matrix = matrix_p.read_text(encoding="utf-8")
    lines = matrix.split("\n")
    for row_prefix, old_cell, new_cell in MATRIX_ROWS:
        idx = [i for i, ln in enumerate(lines) if ln.startswith(row_prefix)]
        assert len(idx) == 1, (row_prefix, len(idx))
        ln = lines[idx[0]]
        assert ln.endswith(old_cell), (row_prefix, ln[-120:])
        lines[idx[0]] = ln[: -len(old_cell)] + new_cell
    matrix = "\n".join(lines)

    prev_p = root / HANDOFF_PREV
    prev = prev_p.read_text(encoding="utf-8")
    assert "SUPERSEDED 2026-10-20" not in prev
    first_nl = prev.index("\n")
    prev = prev[: first_nl + 1] + BANNER + prev[first_nl + 1 :]

    parent_p = root / HANDOFF_PARENT
    parent = replace_once(parent_p.read_text(encoding="utf-8"), PARENT_OLD, PARENT_NEW, "parent pointer")

    index_p = root / INDEX
    index = index_p.read_text(encoding="utf-8")
    index = replace_once(index, INDEX_OLD_PTR, INDEX_NEW_PTR, "INDEX pointer")
    index = replace_once(index, INDEX_OLD_TAIL, INDEX_NEW_TAIL, "INDEX tail")

    if check_only:
        print("check OK: every anchor is unique and every rewritten header triages as intended")
        return
    ledger_p.write_text(ledger, encoding="utf-8")
    matrix_p.write_text(matrix, encoding="utf-8")
    prev_p.write_text(prev, encoding="utf-8")
    parent_p.write_text(parent, encoding="utf-8")
    index_p.write_text(index, encoding="utf-8")
    (root / HANDOFF_NEW).write_text(HANDOFF_TEXT, encoding="utf-8")
    print("applied:", LEDGER, MATRIX, HANDOFF_PREV, HANDOFF_PARENT, INDEX, HANDOFF_NEW, sep="\n  ")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    apply(Path(args.root).resolve(), args.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())
