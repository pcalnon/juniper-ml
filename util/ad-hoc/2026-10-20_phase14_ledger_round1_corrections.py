#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-20
# Status      : ad-hoc — one-off correction pass; RETAINED as provenance (owner policy 2026-08-25)
# Retire when : RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : ledger Phase 14 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md);
#               HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md;
#               util/ad-hoc/2026-10-20_phase14_item30_apply.py (the pass this corrects)
# ---------------------------------------------------------------------------
"""Round 1's correction pass on the ledger's Phase 14 and the files that land with it.

Applied to the files as frozen for round 1 (local commit ``a77c1c54``). Round 1's three reports are archived
verbatim in ``reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase14_round1.md``. Every
substitution is anchored to occur exactly once in its file and is credited to the lane that raised it; the
reconciler re-derived each from the record, the transcript, the source or the dash wheels before applying it (the
ledger's round-1 record says what). The pass also writes the round-1 consensus record into the Phase 14 placeholder.

What it changes, in one line each (lane in brackets; MAJOR marked):

* MAJOR [B1, C2, A2] F-CANOPY-028's first "discard" has no surviving artifact: the run-1 transcript reads the SECOND
  pin absent, and the ``["max_iterations"]`` read lived only in a response capture run 2 overwrote. "2 of 8" becomes
  "1 of 8 on the record, with run 1 unrecorded", in the header, the blockquote, the Summary, "cannot support", the
  M-PARAMETERS-06 cell, the handoff, the parent's pointer and the INDEX row. The disposition does not move.
* MAJOR [B2, C3] the handoff's step-1 check printed 3 where it said 5 (two headers wrap); it now uses the triage.
* MAJOR [C1] ``transcripts/`` is gitignored (``*.log``) and was not in the commit; it is force-added at landing, and
  the phase says so. The screenshots are LFS-tracked PNGs the API landing cannot push; they stay on turing.
* [B3] F-CANOPY-001's "+0.3 s" and "+0.9 s" were poll offsets, not latencies from the click or the reload.
* [B4] F-CANOPY-028's store-write range excluded a recorded 6.5 s; the card figure was a settle, not a latency.
* [B5, A] early#2's third writer firing: 2.8 s after the click's request, all 22 pin inputs in its changed props;
  the trigger is stated as inferred; Lane A's four arms (no loss; the second render 8–9.5 s after the mount render,
  landing before each click) are recorded, and the window is named.
* [B6, A1] the "0 lines in the leg's log" sentence was vacuous (alive legs log none either); dropped.
* [B7] the Python-side sentence in F-CANOPY-069 misdescribed dash; corrected (no cross-callback check exists there).
* [B8, A3, C] line cites: ``_utils.py:138-164`` / ``:146-186``; ``execute_restart`` ``:6478-6510``;
  ``_merge_pinned_params`` ``:7320-7349``; the 3.1.1 wheel dropped from the list; 4.4.1's extra branch noted.
* [B9, B] the E2 env was built from a re-specified spec that kept ``dash=3.3.0``; ``docs/QUICK_START.md:492`` is the
  user path to the conda file; ``validate_callbacks`` defaults to ``debug`` and canopy logs ``Debug mode: False``.
* [B10, C6] f032: 30 samples in all.  [B11] run 1's M-06 fixed read.  [B] the readyState probe and the population
  figure are marked as unarchived / the contract's.  [C5, A4] the record's flags for early#2 are named.
* [C7] the handoff names every document it refers to.  [C8] the handoff title's trailing period; the double blank
  line before ``## Phase 14``; the placeholder.

Usage:
    python3 util/ad-hoc/2026-10-20_phase14_ledger_round1_corrections.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
MATRIX = "notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md"
HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md"
PARENT = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md"
INDEX = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md"
RUN = "reports/e2e-canopy-2026-09-02/item30-turing"

LEDGER_SUBS = [
    # --- F-028 header (B1, C2, A2; MAJOR) ---
    (
        ", Phase 14, item 30: a pin was discarded in 2 of 8 drives and the mechanism is re-diagnosed, a table re-render from a stale pin set that the store writer then persists; OPEN; segment 15).**",
        ", Phase 14, item 30: a pin was lost in 1 of 8 drives on the record, run 1 unrecorded, and the mechanism is re-diagnosed, a table re-render from a stale pin set that the store writer then persists; OPEN; segment 15).**",
    ),
    # --- F-028 blockquote: the eight drives (B1, C2, A2; MAJOR) + B4 + B5 + A + C5 ---
    (
        "> their own expectations in every drive: the store write lands in 1.0–2.3 s, the card shows `Learning Rate 0.01`,\n"
        "> the set survives the reload, the checkbox re-renders checked (the rehydration canopy#533 found correct is\n"
        "> correct), and unpinning empties the store and hides the card across a reload.\n",
        "> their own expectations in every drive (run 1's M-06 read the card still shown at a fixed read after the unpin and\n"
        "> hidden after the reload; the polled runs read it hidden in 1.5–2.1 s): the store write lands in 1.0–6.5 s, the\n"
        "> card shows `Learning Rate 0.01` by the next read, the set survives the reload, the checkbox re-renders checked (the\n"
        "> rehydration canopy#533 found correct is correct), and unpinning empties the store and hides the card across a\n"
        "> reload.\n",
    ),
    (
        "> **The finding reproduces, in 2 of 8 drives, and not the way this entry or the fix describe it.** The eight second\n"
        "> pins, by their delay after the reload: run 1 at ~10 s (the first pin, `learning_rate`, DISCARDED: the store\n"
        "> went to `[\"max_iterations\"]`; that run's record was overwritten by run 2 and survives in the run-1 transcript and\n"
        "> in the reconciler's read of the response capture, `pinned-params-store → [\"max_iterations\"]` at 141.5 s); run 2\n"
        "> at 27.9 s (both kept); run 3 settled at 27.9 s and early at 2.5 s (both kept); run 4 mid at 11.5 s, early at\n"
        "> 2.8 s, mid at 8.0 s (all kept) and **early at 3.0 s, where the second pin was DISCARDED after landing**. That\n"
        "> drive's record is complete: the store writer's three requests after the reload, read from the renderer's own\n"
        "> bodies (`arms.early#2.pin_requests_after_reload`), were (1) the mount re-render, 22 checkboxes, `learning_rate`\n"
        "> checked, State `[\"learning_rate\"]`; (2) the click, both checked, State `[\"learning_rate\"]` → the store became\n"
        "> `[\"max_iterations\", \"learning_rate\"]` at +3.2 s; (3) **1.4 s later, a third firing with 22 checkboxes rendered,\n"
        "> `max_iterations` reported UNCHECKED and State `[\"max_iterations\", \"learning_rate\"]`** → the writer returned\n"
        "> `[\"learning_rate\"]` and the pin the user had just made was gone, the card showing `Learning Rate 0.01` alone.\n",
        "> **The finding reproduces, in 1 of 8 drives on the record, and not the way this entry or the fix describe it.** The\n"
        "> eight second pins, by their delay after the reload: run 1 at ~10 s by the driver's design (its only surviving\n"
        "> read, 3.4 s after the click, has the SECOND pin absent, `store=['learning_rate']`, and its M-06 read the card\n"
        "> still shown; the JSON record was overwritten by run 2 before its response capture was saved, so what that run\n"
        "> did to the pins is unrecorded: the reconciler's unarchived read of that capture showed the store at\n"
        "> `[\"max_iterations\"]` 6.5 s after the click, the FIRST pin gone, which no surviving artifact supports and\n"
        "> which stands here as a lead, not a fact); run 2 at 27.9 s (both kept); run 3 settled at 27.9 s and early at\n"
        "> 2.5 s (both kept); run 4 mid at 11.5 s, early at 2.8 s, mid at 8.0 s (all kept) and **early at 3.0 s, where the\n"
        "> second pin was lost after landing** (the record's flags read `SURVIVES: false, DISCARDED: false`: the driver's\n"
        "> `DISCARDED` names the entry's original shape, the first pin gone, and this loss is the other one). That drive's\n"
        "> record is complete: the store writer's three requests after the reload, read from the renderer's own bodies\n"
        "> (`arms.early#2.pin_requests_after_reload`, `pin_request_bodies_after_reload`), were (1) the mount re-render,\n"
        "> 22 checkboxes, `learning_rate` checked, State `[\"learning_rate\"]`; (2) the click, both checked, State\n"
        "> `[\"learning_rate\"]` → the store became `[\"max_iterations\", \"learning_rate\"]` at +3.2 s; (3) **2.8 s after the\n"
        "> click's request, 0.2 s after its response had landed, a third firing whose `changedPropIds` name all 22\n"
        "> `param-pin` inputs (a rebuilt table, not a toggle), `max_iterations` reported UNCHECKED and State\n"
        "> `[\"max_iterations\", \"learning_rate\"]`** → the writer returned `[\"learning_rate\"]` and the pin the user had just\n"
        "> made was gone, the card showing `Learning Rate 0.01` alone. A validator lane's four arms of the same drive (round\n"
        "> 1, Lane 14-A) lost no pin and show the same three firings each time: the mount render, **a second non-user\n"
        "> re-render 8–9.5 s after it**, and the click; in its arms the second render landed 0.8–10.8 s BEFORE the click,\n"
        "> carrying the set it was computed from, and nothing was lost. In `early#2` the click fell 7.9 s after the mount\n"
        "> render and the second render 2.8 s after the click. **The window is that second render**: a pin made in the\n"
        "> seconds before it is computed out of the table it rebuilds.\n",
    ),
    (
        "> **Mechanism.** `update_parameters_tables` (`parameters_panel.py:250-275` at `571743db`) re-renders all three tables\n"
        "> whenever its params store OR `pinned-params-store` changes, and each checkbox is built with `value=key in\n"
        "> pinned_set` from the pin set THAT callback received (`:114-118`). On a fresh session the params store fills late\n"
        "> (the F-CANOPY-004 envelope), so a re-render computed from a pin set older than the user's latest toggle lands\n"
        "> after it, and the toggled checkbox comes back in its old state. The pattern-matched writer\n"
        "> (`dashboard_manager.py:5230-5248`) then fires for the re-rendered components (it fires on every table render:\n"
        "> the two `[]` writes at mount in every drive are those), and `_merge_pinned_params` (`:7320-7348`) does what\n",
        "> **Mechanism.** `update_parameters_tables` (`parameters_panel.py:250-275` at `571743db`) re-renders all three tables\n"
        "> whenever its params store OR `pinned-params-store` changes, and each checkbox is built with `value=key in\n"
        "> pinned_set` from the pin set THAT callback received (`:114-118`). What triggers the second render is inferred,\n"
        "> not captured (the capture keeps only the writer's own bodies): the params store filling late on a fresh session\n"
        "> (the F-CANOPY-004 envelope) fits the sidebar's mirror callback carrying both stores in the same window and the\n"
        "> card's value going from `—` to `0.01`. A re-render computed from a pin set older than the user's latest toggle\n"
        "> lands after it, and the toggled checkbox comes back in its old state. The pattern-matched writer\n"
        "> (`dashboard_manager.py:5230-5248`) then fires for the re-rendered components (it fires on every table render:\n"
        "> the two `[]` writes at mount in every drive are those), and `_merge_pinned_params` (`:7320-7349`) does what\n",
    ),
    (
        "> rendered from a stale set) in place; the entry's own last sentence, \"collects the state of every checkbox\", named\n"
        "> the writer, and the writer is still the half that persists a render the user did not make. Run 1's discard of\n"
        "> the FIRST pin is the same race with the other ordering: the stale render carried `learning_rate` unchecked.\n",
        "> rendered from a stale set) in place; the entry's own last sentence, \"collects the state of every checkbox\", named\n"
        "> the writer, and the writer is still the half that persists a render the user did not make. If run 1's unrecorded\n"
        "> read was right, it was the same race with the other ordering, the stale render carrying `learning_rate`\n"
        "> unchecked; nothing on the record says so.\n",
    ),
    (
        "> the State and apply only the keys whose checkbox differs from it; alternatively make the table re-render carry\n"
        "> the pin set from the store as State and never re-fire the writer. Pin it with a test that re-renders the tables\n"
        "> from a stale pin set after a toggle and asserts the store keeps the toggle. Re-drive the early arm on the fix.\n",
        "> the State and apply only the keys whose checkbox differs from it; alternatively make the table re-render carry\n"
        "> the pin set from the store as State and never re-fire the writer. Pin it with a test that re-renders the tables\n"
        "> from a stale pin set after a toggle and asserts the store keeps the toggle. Re-drive the early arm on the fix,\n"
        "> timing the pin into the window (8–10 s after the mount render), with enough repeats to put a rate on it.\n",
    ),
    # --- F-001 blockquote timings (B3) ---
    (
        "> dash 4.4.1 (`reports/e2e-canopy-2026-09-02/item30-turing/demo_leg_8062_dash441.json`, step `f001`): the click flipped `<html>` to `dark-mode` at +2.3 s and\n"
        "> swapped the glyph at +0.3 s; after a full reload the theme restored dark AND the glyph read ☀️ at +0.9 s (the\n"
        "> layout-default 🌙 this entry measured never showed); the next click flipped back at +5.4 s. The fix, the glyph\n",
        "> dash 4.4.1 (`reports/e2e-canopy-2026-09-02/item30-turing/demo_leg_8062_dash441.json`, step `f001`): the click flipped `<html>` to `dark-mode` at +2.3 s and\n"
        "> the glyph had swapped by +2.6 s (the driver polls the glyph after the html, so the 0.3 s it records is its own\n"
        "> offset); after a full reload the earliest read, at +3 s, already showed the theme dark AND the glyph ☀️ (the\n"
        "> layout-default 🌙 this entry measured never showed); the next click flipped the html back at +5.4 s (the glyph is\n"
        "> not polled there). The fix, the glyph\n",
    ),
    # --- F-032 blockquote sample count (B10, C6) ---
    (
        "> `worker-panel-error-display` rendered **`Worker data degraded: Upstream error`** (900×18, one child) on the first\n"
        "> 2 s sample and on every one of the 30 that followed, the badge reading `NO WORKERS`; the first\n",
        "> `worker-panel-error-display` rendered **`Worker data degraded: Upstream error`** (900×18, one child) on the first\n"
        "> sample and on all 30 samples over 60 s, the badge reading `NO WORKERS`; the first\n",
    ),
    (
        "> `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://bogus.invalid:1`; cascor's log counts four `not in allowlist`\n"
        "> rejections and canopy's the supervisor's reconnects): `/api/stream_health` read `overall: \"degraded\"` with the\n",
        "> `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://bogus.invalid:1`; cascor's log records one `not in allowlist`\n"
        "> rejection per 30 s reconnect and canopy's the supervisor's disconnects): `/api/stream_health` read `overall: \"degraded\"` with the\n",
    ),
    # --- Phase 14 Summary (B1, B3) ---
    (
        "  - **F-CANOPY-028, M-PARAMETERS-04/-05/-06**, demo leg, eight drives: the rows pass on their own expectations\n"
        "    every time; **a pin was discarded in 2 of 8**, once the first pin and once the second, and the complete\n"
        "    record of the second shows the mechanism: a table re-render from a stale pin set, persisted by the store\n"
        "    writer. Re-diagnosed; **OPEN, P1**; fix direction in the entry, carried as item 31.\n",
        "  - **F-CANOPY-028, M-PARAMETERS-04/-05/-06**, demo leg, eight drives: the rows pass on their own expectations\n"
        "    every time; **a pin was lost in 1 of 8 on the record** (run 4's `early#2`, the second pin, with the store\n"
        "    writer's own request bodies showing the mechanism: a table re-render from a stale pin set, persisted by the\n"
        "    writer), and run 1 is unrecorded (its JSON was overwritten; the reconciler's unarchived read of it showed the\n"
        "    first pin gone, a lead). Re-diagnosed; **OPEN, P1**; fix direction in the entry, carried as item 31.\n",
    ),
    (
        "  - **F-CANOPY-001, C2.1-01/-02**, demo leg: after the reload the html carries `dark-mode` and the glyph reads\n"
        "    ☀️ at +0.9 s. **FIXED.**\n",
        "  - **F-CANOPY-001, C2.1-01/-02**, demo leg: after the reload the html carries `dark-mode` and the glyph reads\n"
        "    ☀️ at the earliest read, +3 s. **FIXED.**\n",
    ),
    # --- Summary F-069 bullet (B6, B9) ---
    (
        "  `conda_environment.yaml`), was inert: no welcome modal, empty Parameters tables, no `_dash-update-component`\n"
        "  POST on any click, zero callback POSTs in the leg's log. Cause: three callback pairs claim one\n",
        "  `conda_environment.yaml`), was inert: no welcome modal, empty Parameters tables, no `_dash-update-component`\n"
        "  POST from the page on any click. Cause: three callback pairs claim one\n",
    ),
    (
        "  canopy's CI runs (dash 4.4.1). Measured on five legs, one per dash: 3.0.4, 3.2.0, 3.3.0 and 3.4.0 INERT, 4.4.1\n"
        "  ALIVE (`reports/e2e-canopy-2026-09-02/item30-turing/dash_version_matrix.json`). canopy's floor is `dash>=3.0.0`. Entry below; carried as item 32.\n",
        "  canopy's CI runs (dash 4.4.1). Measured on five legs, one per dash: 3.0.4, 3.2.0, 3.3.0 and 3.4.0 INERT, 4.4.1\n"
        "  ALIVE (`reports/e2e-canopy-2026-09-02/item30-turing/dash_version_matrix.json`). canopy's floor is `dash>=3.0.0`, and its `docs/QUICK_START.md:492`\n"
        "  tells the user to build from the conda file. Entry below; carried as item 32.\n",
    ),
    # --- Who, and from what: records (C1, LFS) ---
    (
        "  `demo_leg_8058.json` (the inert first leg), `transcripts/` (every run, including the overwritten ones) and\n"
        "  `shots/` (20 PNGs). The inert leg's run and this run's run 1 are kept as transcripts: a later run of the same\n"
        "  step overwrites its key in the JSON.\n",
        "  `demo_leg_8058.json` (the inert first leg) and `transcripts/` (every run, including the overwritten ones;\n"
        "  `.gitignore` excludes `*.log`, so the directory is force-added, as earlier phases' logs under `reports/` were).\n"
        "  The 20 screenshots stay on turing under the same directory: PNGs are Git LFS pointers in this repo and the\n"
        "  API landing from this host cannot push LFS objects. The inert leg's run and this run's run 1 are kept as\n"
        "  transcripts: a later run of the same step overwrites its key in the JSON, and run 1's response capture is gone.\n",
    ),
    # --- Who: browser bullet, the probe figures (B inferred) ---
    (
        "  dashboard's one external resource, `dbc.themes.BOOTSTRAP` from `cdn.jsdelivr.net`, never resolves for Chrome\n"
        "  (readyState `loading` for 100 s; the same URL answers curl in 0.1 s). The stylesheet held `DOMContentLoaded`\n",
        "  dashboard's one external resource, `dbc.themes.BOOTSTRAP` from `cdn.jsdelivr.net`, never resolves for Chrome\n"
        "  (the reconciler's probe, not archived: readyState `loading` for 100 s while the same URL answered curl in\n"
        "  0.1 s). The stylesheet held `DOMContentLoaded`\n",
    ),
    # --- The legs section: the log sentence (B6, A1) and cites (B8, A3) ---
    (
        "and `restart-confirm-m…`, and the leg's log had **0** `_dash-update-component` lines. Parsed from\n",
        "and `restart-confirm-m…`, and the page's own request capture carried **0** `_dash-update-component` POSTs in 60 s\n"
        "(the leg's log does not record that route on an alive leg either, so it says nothing). Parsed from\n",
    ),
    (
        "`open_restart_progress`, `:6468-6476`, and `execute_restart`, `:6478-6507`, both on\n",
        "`open_restart_progress`, `:6468-6476`, and `execute_restart`, `:6478-6510`, both on\n",
    ),
    (
        "The Python side is the same everywhere: `create_callback_id` (`dash/_utils.py:138-162`, read in the 3.0.4,\n"
        "3.1.1, 3.2.0, 3.3.0, 3.4.0 and 4.4.1 wheels) suffixes an `allow_duplicate` output with `@sha256(\".\".join(str(x)\n"
        "for x in inputs))`, so two callbacks with the same output and the same inputs get the same id, and the server\n"
        "registers both. The renderer differs in one line: dash 3's `computeGraphs` calls `validateDependencies`\n"
        "unconditionally (`dash_renderer.dev.js:77452` in 3.3.0) and, on any error, returns the empty graphs (\"leave the\n"
        "graphs empty if we found an error, so we don't try to execute the broken callbacks\", `:77488-77492`); dash 4.4.1\n"
        "calls it only `if (config.validate_callbacks)` (`:6810-6812`) and otherwise builds the graph over the colliding\n"
        "ids. Which member of a colliding pair the dash 4 graph runs on a click was not measured (neither the Live Switch\n",
        "The Python side is the same everywhere: `create_callback_id` (`dash/_utils.py:138-164` in 3.0.4, 3.2.0, 3.3.0 and\n"
        "3.4.0, `:146-186` in 4.4.1, which adds a branch for callbacks with no output and no inputs that does not touch\n"
        "this) suffixes an `allow_duplicate` output with `@sha256(\".\".join(str(x) for x in inputs))`, so two callbacks\n"
        "with the same output and the same inputs get the same id, and the server registers both (`callback_map` keyed by\n"
        "that id, `dash/_callback.py:311`, the second overwriting the first's entry; the dependency list served to the\n"
        "renderer keeps both). The renderer differs in one line: dash 3's `computeGraphs` calls `validateDependencies`\n"
        "unconditionally (`dash_renderer.dev.js:77452` in 3.3.0) and, on any error, returns the empty graphs (\"leave the\n"
        "graphs empty if we found an error, so we don't try to execute the broken callbacks\", `:77488-77492`); dash 4.4.1\n"
        "calls it only `if (config.validate_callbacks)` (`:6810-6812`), a dev-tools flag that defaults to `debug`\n"
        "(`dash/dash.py:2062-2066`; canopy's legs log `Debug mode: False`), and otherwise builds the graph over the colliding\n"
        "ids. Which member of a colliding pair the dash 4 graph runs on a click was not measured (neither the Live Switch\n",
    ),
    # --- Row by row (B3, B4) ---
    (
        "- **f001 (C2.1-01/-02).** Run 1 read at a fixed +3 s and missed the click's render (html flipped at +2.3 s, the\n"
        "  glyph at +0.3 s in run 2; the second click's flip took 5.4 s); run 2 polled. After the reload: early read\n"
        "  (+3 s) already `dark-mode` + ☀️; synced at +0.9 s.\n",
        "- **f001 (C2.1-01/-02).** Run 1 read at a fixed +3 s and missed the click's render (in run 2 the html flipped at\n"
        "  +2.3 s and the glyph had swapped by +2.6 s; the second click's html flip took 5.4 s); run 2 polled. After the\n"
        "  reload the earliest read, at +3 s, was already `dark-mode` + ☀️.\n",
    ),
    (
        "  RE-DIAGNOSED blockquote. The rows' own expectations: M-04 store `[\"learning_rate\"]` in 1.0–2.3 s; M-05 the card\n"
        "  shown in 0.5–1.2 s reading `Learning Rate 0.01` (the value arm the matrix had pending lands: the params store\n"
        "  fills); M-06 unpin → `[]` and the card hidden in 1.5–2.1 s, both surviving a reload.\n",
        "  RE-DIAGNOSED blockquote. The rows' own expectations: M-04 store `[\"learning_rate\"]` in 1.0–6.5 s; M-05 the card\n"
        "  shown by the next read, reading `Learning Rate 0.01` (the value arm the matrix had pending lands: the params\n"
        "  store fills); M-06 unpin → `[]` and the card hidden in 1.5–2.1 s on the polled runs, both surviving a reload.\n",
    ),
    # --- F-069 entry (B6, B7, B8, B9) ---
    (
        "welcome modal never opens, the Parameters tables render 0 rows, a click on the theme toggle sends no\n"
        "`_dash-update-component` POST in 30 s, and the leg's log carries no callback POST at all; under dash 4.4.1 the same\n",
        "welcome modal never opens, the Parameters tables render 0 rows, and a click on the theme toggle sends no\n"
        "`_dash-update-component` POST in 30 s (0 such POSTs from the page in the whole visit); under dash 4.4.1 the same\n",
    ),
    (
        "`restart-progress-alert.is_open@b7e1c13f…`, claimed by `open_restart_progress` (`:6468-6476`) and\n"
        "`execute_restart` (`:6478-6507`), both with `restart-confirm-button.n_clicks`. The hash is of the inputs\n"
        "(`dash/_utils.py:138-162`, `create_callback_id`, identical in every wheel read: 3.0.4, 3.1.1, 3.2.0, 3.3.0, 3.4.0,\n"
        "4.4.1), so `allow_duplicate=True` on both members of a pair does not separate them: the server registers both\n"
        "under one id, and what happens next is the renderer's. dash 3's `computeGraphs` validates the dependency list\n"
        "unconditionally and, on any error, returns empty graphs (`dash_renderer.dev.js:77452`, `:77488-77492` in 3.3.0);\n"
        "dash 4.4.1 validates only `if (config.validate_callbacks)` (`:6810-6812`), which is off, so the pairs go unchecked.\n"
        "**Why it is green everywhere:** the Python side raises nothing (the duplicate check that would is what\n"
        "`allow_duplicate` disables); canopy's unit and integration suites (7,947 and 523 passed on turing under dash\n",
        "`restart-progress-alert.is_open@b7e1c13f…`, claimed by `open_restart_progress` (`:6468-6476`) and\n"
        "`execute_restart` (`:6478-6510`), both with `restart-confirm-button.n_clicks`. The hash is of the inputs\n"
        "(`dash/_utils.py:138-164` in 3.0.4, 3.2.0, 3.3.0 and 3.4.0, `:146-186` in 4.4.1; the `allow_duplicate` suffix is\n"
        "the same code in each), so `allow_duplicate=True` on both members of a pair does not separate them: the server\n"
        "registers both under one id, and what happens next is the renderer's. dash 3's `computeGraphs` validates the\n"
        "dependency list unconditionally and, on any error, returns empty graphs (`dash_renderer.dev.js:77452`,\n"
        "`:77488-77492` in 3.3.0); dash 4.4.1 validates only `if (config.validate_callbacks)` (`:6810-6812`), a dev-tools\n"
        "flag whose default is `debug` (`dash/dash.py:2062-2066`), and canopy runs with debug off (`Debug mode: False` in\n"
        "every leg's log), so the pairs go unchecked.\n"
        "**Why it is green everywhere:** no Python-side check exists for an output claimed by two callbacks (the only\n"
        "server-side duplicate validation, `_validate.validate_duplicate_output`, enforces `prevent_initial_call`; the\n"
        "callback registry is a dict keyed by the id, `_callback.py:311`, and the second registration overwrites the\n"
        "first's entry while the dependency list keeps both); canopy's unit and integration suites (7,947 and 523 passed on turing under dash\n",
    ),
    (
        "`dash>=3.0.0` (`pyproject.toml:56`; `requirements.txt:169`) admits and which canopy's own\n"
        "`conda_environment.yaml:93` (`dash=3.3.0=pyhd8ed1ab_0`, conda-forge's current build) produces; the E2 env on\n"
        "turing was built from it. A user there sees a styled, populated-looking page with every control dead and no\n",
        "`dash>=3.0.0` (`pyproject.toml:56`; `requirements.txt:169`) admits and which canopy's own\n"
        "`conda_environment.yaml:93` (`dash=3.3.0=pyhd8ed1ab_0`; the root file is a symlink to `conf/conda_environment.yaml`,\n"
        "and `docs/QUICK_START.md:492` tells the user `conda env create -f conf/conda_environment.yaml`) produces on\n"
        "linux-64; turing's E2 env was built from a re-specified copy of it for osx-64 that kept `dash=3.3.0`\n"
        "(`reports/2026-10-20_turing-e2-envs/JuniperCanopy1.export.yml:37`). A user there sees a styled, populated-looking page with every control dead and no\n",
    ),
    # --- What this phase cannot support (B1, C2, B inferred) ---
    (
        "- **Timing figures are this host's.** turing is a 16 GiB laptop running four other sessions; the latencies here\n"
        "  (a click's render in 0.3–5.4 s, population in 20–30 s) fit F-CANOPY-004's contract and are not comparable with\n"
        "  the trio's.\n"
        "- **F-CANOPY-028's first discard is a transcript, not a record.** Run 1's JSON was overwritten by run 2 before\n"
        "  its response capture was saved; the discard rests on the run-1 transcript's store read and on the reconciler's\n"
        "  read of the response capture before it was lost. The second discard (run 4, early#2) is complete, with the\n"
        "  writer's request bodies.\n",
        "- **Timing figures are this host's, and some are the driver's.** turing is a 16 GiB laptop running four other\n"
        "  sessions; the latencies here (a click's render in 1.4–5.4 s) fit F-CANOPY-004's contract and are not comparable\n"
        "  with the trio's. The 25 s mount settle is the contract's figure (fresh-session population 20–40 s), not a\n"
        "  measurement of this host; the `wait_for` figures are offsets from the poll's own start.\n"
        "- **F-CANOPY-028's first loss is unrecorded.** Run 1's JSON was overwritten by run 2 before its response capture\n"
        "  was saved, and its transcript carries only a store read 3.4 s after the second pin, with that pin absent and\n"
        "  the first present. The reconciler's read of the lost capture (the first pin gone 6.5 s after the click) is a\n"
        "  lead no artifact supports. The loss on the record (run 4, `early#2`) is complete, with the writer's request\n"
        "  bodies, and a validator lane's four arms corroborate the mechanism without reproducing the loss.\n",
    ),
    # --- Matrix effect (B1) ---
    (
        "  -06 → PASS (re-validated @ `571743db`), M-05's pending value arm landed, M-06 carrying the F-CANOPY-028 note.\n",
        "  -06 → PASS (re-validated @ `571743db`), M-05's pending value arm landed, M-06 carrying the F-CANOPY-028 note\n"
        "  (one loss on the record).\n",
    ),
    # --- Still owed, item 31 (A) ---
    (
        "    re-renders the tables from a stale pin set after a toggle and asserts the store keeps the toggle; re-drive\n"
        "    `2026-10-20_item30_fixwave_redrive.py --step f028 --f028-arms early,mid --f028-repeat 3` on the fix.\n",
        "    re-renders the tables from a stale pin set after a toggle and asserts the store keeps the toggle; re-drive\n"
        "    `2026-10-20_item30_fixwave_redrive.py --step f028 --f028-arms early,mid --f028-repeat 3` on the fix, and on\n"
        "    the parent first with the pin timed into the window (8–10 s after the mount render) to put a rate on the\n"
        "    loss, which this phase measured once in eight.\n",
    ),
    # --- the double blank line before ## Phase 14 (C8) ---
    (
        "\n\n\n## Phase 14 — 2026-10-20: item 30,",
        "\n\n## Phase 14 — 2026-10-20: item 30,",
    ),
]

CONSENSUS_OLD = "_(filled by the round scripts)_\n"
CONSENSUS_NEW = """- **Round 1**: three lanes on the frozen `a77c1c54`, briefed separately with different entry points. Briefs are in
  `reports/e2e-canopy-2026-09-02/drafts/lane14{A,B,C}_phase14_ledger_brief.md`, and the reports, verbatim, in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase14_round1.md`.
  - Lane 14-A re-created the measurements from the phase's own scripts on fresh legs (ports 8070–8073, cascor
    8230): the dash matrix at 3.3.0 and 4.4.1 (INERT / ALIVE, the same 181 callbacks and 3 colliding ids, counted
    from raw `_dash-dependencies` with its own parser; both `create_callback_id` sources and both renderer bundles
    read independently), f018, f001, four f028 arms, and the service rows on its own trained network ((2, 3, 2):
    f012's nine cases at (5, 2) = 10 values, f013's refused-then-real append and real remove, f032's cascor-down
    arm). Every scored figure agreed. Its four f028 arms lost no pin, and all four show the second non-user
    re-render 8–9.5 s after the mount render that `early#2` ran into.
  - Lane 14-B was adversarial on the analysis: every figure against the records, every `file:line` against the
    source and the dash wheels, the dispositions, the P0, the counts, and what was stated that was inferred.
  - Lane 14-C replayed the apply pass from `origin/main` (`5a383ae1`, six commits past the merge base): all six
    outputs byte-identical to the worktree's; the counts everywhere they are stated; the handoff's verification
    commands; every path and cite; the matrix cells; the Still-owed list; conventions, lint and the repo's tests
    (24 + 45 OK).
- **Verdicts.** Lane 14-A SOUND; Lanes 14-B and 14-C SOUND-WITH-FIXES, on the same two MAJORs plus one of Lane
  14-C's own. No lane refuted a disposition, a rating, a count or an item; §4 of
  `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires round 2 because round 1
  produced corrections.
- **What round 1 changed** (the pass is `util/ad-hoc/2026-10-20_phase14_ledger_round1_corrections.py`; each item was
  re-derived by the reconciler before it was applied):
  - MAJOR (Lanes 14-B, 14-C; Lane 14-A MINOR): F-CANOPY-028's "2 of 8" rested on a first-pin discard no surviving
    artifact supports: the run-1 transcript reads the SECOND pin absent 3.4 s after the click, and the
    `["max_iterations"]` read lived in a response capture run 2 overwrote. The header, the blockquote, the Summary,
    "cannot support", the M-PARAMETERS-06 cell, the handoff, the parent's pointer and the INDEX row now say one loss
    on the record (run 4's `early#2`) with run 1 unrecorded and the reconciler's read of it a lead. The disposition
    (OPEN, P1) stands on `early#2` alone, and Lane 14-A's four arms corroborate its mechanism.
  - MAJOR (Lanes 14-B, 14-C): the handoff's step-1 check printed 3 where it said 5 (the F-CANOPY-012 and -013
    headers wrap, so their FIXED is on a continuation line); it now counts through the triage.
  - MAJOR (Lane 14-C): `transcripts/` was not in the frozen commit (`.gitignore:52`, `*.log`) while the phase cites
    twelve of its files; it is force-added at landing, and the phase says so. The reconciler adds that the 20
    screenshots cannot land from this host (LFS pointers; the API cannot push LFS objects) and stay on turing.
  - Lane 14-B: F-CANOPY-001's "+0.3 s" and "+0.9 s" were the driver's poll offsets (the glyph had swapped by +2.6 s;
    after the reload the earliest read, +3 s, was already synced); F-CANOPY-028's store-write range excluded a
    recorded 6.5 s and the card figure was a settle; `early#2`'s third firing came 2.8 s after the click's request
    (0.2 s after its response), with all 22 pin inputs in its `changedPropIds`, and the trigger is now stated as
    inferred; the "0 lines in the leg's log" sentence was vacuous (alive legs log none either) and is dropped from
    the Summary, the legs section and the entry (Lane 14-A found the same); the Python-side sentence in
    F-CANOPY-069 misdescribed dash (no cross-callback check exists there; the registry overwrites and the served
    list keeps both); `validate_callbacks` defaults to `debug`, which canopy runs off; `docs/QUICK_START.md:492` is
    the user's path to the conda file, the root file being a symlink, and turing's E2 env came from a re-specified
    osx-64 copy that kept `dash=3.3.0`; f032's 30 samples; run 1's M-06 fixed read; the readyState probe and the
    population figure marked as unarchived and the contract's; line cites (`_utils.py:138-164` / `:146-186`,
    `execute_restart` `:6478-6510`, `_merge_pinned_params` `:7320-7349`); the 3.1.1 wheel dropped from the list.
  - Lane 14-C: the handoff names every document it refers to by filename; the handoff title's trailing period; the
    double blank line before `## Phase 14`; the record's `SURVIVES: false, DISCARDED: false` flags for `early#2`
    named in the blockquote (Lane 14-A found the same).
  - Lane 14-A: 4.4.1's `create_callback_id` is not byte-identical (an extra branch for no-output, no-input
    callbacks); the text now says the `allow_duplicate` suffix is the same code.
- **Unresolved dissent.** None on a disposition, a rating, a count or an item. Lane 14-A could not reproduce the
  F-CANOPY-028 loss in four arms and says the claim rests on the phase's own record; the reconciler agrees, and the
  entry now rests it on one complete record plus a corroborated mechanism, with the rate an open measurement (item 31).
- **Instrument and sample.** One host (turing), Chrome 145 headless under Playwright 1.64.0, legs from one tree at
  canopy `571743db`, dash 4.4.1 for every scored row and five dash releases for the matrix; eight f028 drives by the
  reconciler and four by a lane; one service network each for the reconciler ((2, 4, 2)) and the lane ((2, 3, 2)).
  The instrument reads DOM, store, request and cascor state; it cannot score a VIS half here, and it could have
  produced a different answer only on the f028 race, which is timing-dependent by its nature.
"""

MATRIX_SUBS = [
    (
        "| PASS (re-validated @ 571743db, 2026-10-20, item 30: the glyph swapped at +0.3 s, the html class at +2.3 s) |",
        "| PASS (re-validated @ 571743db, 2026-10-20, item 30: the html class at +2.3 s, the glyph swapped by +2.6 s) |",
    ),
    (
        "| PASS (re-validated @ 571743db, 2026-10-20, item 30: the dark theme restored AND the glyph read ☀️ at +0.9 s after the reload — F-CANOPY-001 FIXED) |",
        "| PASS (re-validated @ 571743db, 2026-10-20, item 30: the dark theme restored AND the glyph read ☀️ at the earliest read after the reload, +3 s — F-CANOPY-001 FIXED) |",
    ),
    (
        "| PASS (re-validated @ 571743db, 2026-10-20, item 30: the store write lands in 1.0–2.3 s) |",
        "| PASS (re-validated @ 571743db, 2026-10-20, item 30: the store write lands in 1.0–6.5 s) |",
    ),
    (
        "| PASS (re-validated @ 571743db, 2026-10-20, item 30: name AND value, `Learning Rate 0.01`, the card shown in 0.5–1.2 s) |",
        "| PASS (re-validated @ 571743db, 2026-10-20, item 30: name AND value, `Learning Rate 0.01`, the card shown by the next read after the store write) |",
    ),
    (
        "| PASS (re-validated @ 571743db, 2026-10-20, item 30; but F-CANOPY-028 stands: a pin made while the tables re-render from a stale pin set is discarded, 2 of 8 drives) |",
        "| PASS (re-validated @ 571743db, 2026-10-20, item 30; but F-CANOPY-028 stands: a pin made just before the tables re-render from a stale pin set is lost, 1 of 8 drives on the record) |",
    ),
]

HANDOFF_SUBS = [
    (
        "F-CANOPY-028 reproduced (2 of 8) and is re-diagnosed; F-CANOPY-069 (P0) is filed: canopy's dashboard is inert under every dash 3.x. 1 open P0, 5 open P1, 10 open P2. Next are items 31, 32, 25, 27 and 28.\n",
        "F-CANOPY-028 reproduced (1 of 8 on the record) and is re-diagnosed; F-CANOPY-069 (P0) is filed: canopy's dashboard is inert under every dash 3.x. 1 open P0, 5 open P1, 10 open P2. Next are items 32, 31, 27, 25 and 28\n",
    ),
    (
        "**Consensus**: see the ledger's Phase 14 consensus record.\n",
        "**Consensus**: round 1 on 2026-10-20, three lanes (measurement re-creation, adversarial analysis, replay and\n"
        "conventions): SOUND / SOUND-WITH-FIXES / SOUND-WITH-FIXES; round 2 on the corrections (ledger Phase 14, Consensus record).\n",
    ),
    (
        "- **juniper-ml#2278 merged** on 2026-10-20T02:22:45Z: the ledger's Phase 13 and the previous handoff.\n",
        "- **juniper-ml#2278 merged** on 2026-10-20T02:22:45Z: Phase 13 of\n"
        "  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` and\n"
        "  `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`.\n",
    ),
    (
        "  - **F-CANOPY-028 stays OPEN (P1), re-diagnosed**: 2 of 8 drives discarded a pin; the complete record shows a\n"
        "    table re-render from a stale pin set persisted by the store writer, which canopy#533 did not address.\n",
        "  - **F-CANOPY-028 stays OPEN (P1), re-diagnosed**: 1 of 8 drives on the record lost a pin (run 1 is unrecorded);\n"
        "    the complete record shows a table re-render from a stale pin set persisted by the store writer, which\n"
        "    canopy#533 did not address; a validator lane's four arms found the same second render 8–9.5 s after the\n"
        "    mount render, which is the window.\n",
    ),
    (
        "- **This session's PR** carries the ledger, the matrix, this file, the SUPERSEDED banner, the parent's pointer, the\n"
        "  INDEX's P2 row, the records under `reports/e2e-canopy-2026-09-02/item30-turing/`, Phase 14's consensus records\n"
        "  and the scripts `util/ad-hoc/2026-10-20_*`. Find it with\n",
        "- **This session's PR** carries `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`,\n"
        "  `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`, this file, the SUPERSEDED banner on\n"
        "  `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`, the pointer in\n"
        "  `HANDOFF_2026-10-03_canopy-consolidated.md`, the P2 row of `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`,\n"
        "  the records under `reports/e2e-canopy-2026-09-02/item30-turing/` (JSON and the force-added `transcripts/`; the\n"
        "  screenshots stay on turing, LFS), Phase 14's consensus records and the scripts `util/ad-hoc/2026-10-20_*`. Find it with\n",
    ),
    (
        "   `MERGED` line. Afterwards re-check `origin/main`: `grep -c 'FIXED' <(grep -E '^\\*\\*F-CANOPY-(001|012|013|018|032) ' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md)` should print 5.\n",
        "   `MERGED` line. Afterwards re-check `origin/main`:\n"
        "   `python3 -B util/ad-hoc/e2e_finding_triage.py | grep -c -E '^FIXED +P[012] +F-CANOPY-0(01|12|13|18|32) '` should\n"
        "   print 5 (two of those headers wrap across lines, so a `grep` on the header line alone prints 3).\n",
    ),
    (
        "   (a demo leg on dash 4.x). And the manual's Patch Weights sentence (row idiom for `output_weights`).\n",
        "   (a demo leg on dash 4.x). And canopy's `docs/USER_MANUAL.md` Patch Weights sentence (`:493-501` at `571743db`:\n"
        "   the row idiom for `output_weights`).\n",
    ),
    (
        "- **A later run overwrites a step's key in the record JSON.** Keep the transcripts; name a new `--out` for a run\n"
        "  whose record must survive (run 1's F-CANOPY-028 discard is a transcript only).\n",
        "- **A later run overwrites a step's key in the record JSON.** Name a new `--out` for every run whose record must\n"
        "  survive (run 1's F-CANOPY-028 loss is unrecorded: its JSON was overwritten and its transcript shows only a\n"
        "  store read). `transcripts/*.log` is gitignored: `git add -f` it, or list the files on the landing command.\n",
    ),
    (
        "  `reports/e2e-canopy-2026-09-02/item30-turing/` (records, transcripts, shots);\n",
        "  `reports/e2e-canopy-2026-09-02/item30-turing/` (records and transcripts; the 20 screenshots stay on turing under\n"
        "  the same path, not landed: PNGs are LFS pointers here);\n",
    ),
]

PARENT_SUBS = [
    (
        "   `571743db`, F-CANOPY-028 reproduced (2 of 8 drives) and is re-diagnosed, and F-CANOPY-069 (P0) is filed: the\n",
        "   `571743db`, F-CANOPY-028 reproduced (1 of 8 drives on the record) and is re-diagnosed, and F-CANOPY-069 (P0) is filed: the\n",
    ),
]

INDEX_SUBS = [
    (
        "F-CANOPY-028 reproduced (2 of 8 drives) and is re-diagnosed, and F-CANOPY-069 (P0) is filed",
        "F-CANOPY-028 reproduced (1 of 8 drives on the record) and is re-diagnosed, and F-CANOPY-069 (P0) is filed",
    ),
]


def apply(text: str, subs: list, label: str) -> str:
    for old, new in subs:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"{label}: anchor occurs {n} times, expected 1: {old[:100]!r}")
        text = text.replace(old, new, 1)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    out = {}
    ledger = (root / LEDGER).read_text(encoding="utf-8")
    assert "Round 1**: three lanes on the frozen `a77c1c54`" not in ledger, "round 1 already applied"
    ledger = apply(ledger, LEDGER_SUBS, "ledger")
    ledger = apply(ledger, [(CONSENSUS_OLD, CONSENSUS_NEW)], "ledger consensus")
    out[LEDGER] = ledger
    out[MATRIX] = apply((root / MATRIX).read_text(encoding="utf-8"), MATRIX_SUBS, "matrix")
    out[HANDOFF] = apply((root / HANDOFF).read_text(encoding="utf-8"), HANDOFF_SUBS, "handoff")
    out[PARENT] = apply((root / PARENT).read_text(encoding="utf-8"), PARENT_SUBS, "parent")
    out[INDEX] = apply((root / INDEX).read_text(encoding="utf-8"), INDEX_SUBS, "index")
    if args.check:
        print("check OK: every anchor unique")
        return 0
    for rel, text in out.items():
        (root / rel).write_text(text, encoding="utf-8")
        print("corrected", rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
