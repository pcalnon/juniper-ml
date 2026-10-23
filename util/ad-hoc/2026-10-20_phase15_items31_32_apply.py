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
# Related     : ledger Phase 15 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md);
#               HANDOFF_2026-10-20_canopy-phase15-items-31-32-done-f069-f028-fixed.md;
#               util/ad-hoc/2026-10-20_f069_apply_fix.py and 2026-10-20_f028_apply_fix.py (the canopy fixes);
#               util/ad-hoc/2026-10-20_f069_pair_members_probe.py, 2026-10-20_canopy_dash_duplicate_outputs_probe.py
#               and 2026-10-20_item30_fixwave_redrive.py (the drives this records)
# ---------------------------------------------------------------------------
"""Phase 15 of the canopy E2E ledger: items 32 and 31 — F-CANOPY-069 and F-CANOPY-028 are FIXED.

Applies, in one replayable pass anchored to text that must occur exactly once:

* ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` -- the headers of F-CANOPY-069 (P0) and
  F-CANOPY-028 (P1), OPEN -> FIXED, a dated FIXED blockquote under each, and the new ``## Phase 15`` section appended
  at the end (its consensus record is a placeholder the round scripts fill);
* ``notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`` -- M-PARAMETERS-06's status cell, which
  carried "but F-CANOPY-028 stands";
* the new Lane A handoff, the SUPERSEDED banner on the Phase 14 handoff, the parent consolidated handoff's pointer,
  and the INDEX's P2 row.

Why a script: the files are shared with concurrent sessions and land from this host as whole-file uploads, so a
revert costs one re-run on a fresh ``origin/main`` copy plus a small PR. The triage's rules are asserted before
writing: each rewritten header's first severity token is unchanged and its last 170 characters carry FIXED.

Usage:
    python3 util/ad-hoc/2026-10-20_phase15_items31_32_apply.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
MATRIX = "notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts"
HANDOFF_NEW = f"{HANDOFF_DIR}/HANDOFF_2026-10-20_canopy-phase15-items-31-32-done-f069-f028-fixed.md"
HANDOFF_PREV = f"{HANDOFF_DIR}/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md"
HANDOFF_PARENT = f"{HANDOFF_DIR}/HANDOFF_2026-10-03_canopy-consolidated.md"
INDEX = f"{HANDOFF_DIR}/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md"
SHA = "571743db"  # canopy main the phase started from; the parent of both fixes
SHA_760 = "fbf01dff"  # canopy#760's squash on main (F-CANOPY-069)
RUN32 = "reports/e2e-canopy-2026-09-02/item32-turing"
RUN31 = "reports/e2e-canopy-2026-09-02/item31-turing"

_PRI_RE = re.compile(r"\b(P0/P1|P0|P1|P2|CRITICAL|LEDGER)\b")

# ----------------------------------------------------------------------------- item 31's facts (filled after the drives)
SHA_761 = "aeeaf29b"  # canopy#761's squash on main, merged 2026-10-20T19:34:02Z
ITEM31 = {
    "sha_761": SHA_761,
    "parent_forced": "none in 12 (6 at the early timing, 6 at the settled timing)",  # the parent's forced arm
    "fix_forced": "none in 12",  # the fix's forced arm, both timings
    "fix_early_mid": "none in 6",  # the fix's early,mid x3
    "fix_delays": "none in 7",  # the fix's fixed delays
    "prose": None,  # filled in apply() from item31_prose(): pass 2 lost 0 of 6 on the parent and 0 of 6 on the fix
}
P2_PARENT_LOST = 0
P2_FIX_LOST = 0


# ----------------------------------------------------------------------------- the ledger: headers
HEADER_069_OLD = "**F-CANOPY-069 — under every dash 3.x release canopy's dashboard is inert in the browser: three callback pairs claim one `allow_duplicate` output with identical inputs, their ids collide, and the dash 3 renderer drops the whole callback graph; canopy's own `conda_environment.yaml` pins dash 3.3.0 (P0 in any environment resolving dash 3.x, which the floor `dash>=3.0.0` admits; not reached from `requirements.lock`, CI or a fresh pip resolve, all dash 4.x; found 2026-10-20, Phase 14, on turing's E2 env; OPEN).**"
HEADER_069_NEW = (
    "**F-CANOPY-069 — under every dash 3.x release canopy's dashboard is inert in the browser: three callback pairs claim one `allow_duplicate` output with identical inputs, their ids collide, and the dash 3 renderer drops the whole callback graph; canopy's own `conda_environment.yaml` pins dash 3.3.0 (P0 in any environment resolving dash 3.x, which the floor `dash>=3.0.0` admitted; not reached from `requirements.lock`, CI or a fresh pip resolve, all dash 4.x; found 2026-10-20, Phase 14, on turing's E2 env; fixed by canopy#760, merged 2026-10-20 as `"
    + SHA_760
    + "`: the progress alerts are the working callbacks' `running=` specs, the two openers are gone, the floor is `dash>=4.0.0` and the conda file pins 4.4.1; a leg of the fix is ALIVE under dash 3.3.0 and 4.4.1, Phase 15, item 32; FIXED).**"
)
HEADER_028_OLD = "**F-CANOPY-028 — pinned params are silently discarded on the first pin after any reload (P1 since 2026-10-19, Phase 13, by the manual's pin-persistence sentence, the narrowest of that phase's five re-ratings; P2 before that; code change canopy#533, merged 2026-08-28, in canopy 0.7.0; M-PARAMETERS-04/-05/-06 re-driven 2026-10-20 on canopy 571743db, Phase 14, item 30: a pin was lost in 1 of 8 drives on the record, run 1 unrecorded, and the mechanism is re-diagnosed, a table re-render from a stale pin set that the store writer then persists; OPEN; segment 15).**"


def header_028_new() -> str:
    return (
        "**F-CANOPY-028 — pinned params are silently discarded on the first pin after any reload (P1 since 2026-10-19, Phase 13, by the manual's pin-persistence sentence, the narrowest of that phase's five re-ratings; P2 before that; code change canopy#533, merged 2026-08-28, in canopy 0.7.0; M-PARAMETERS-04/-05/-06 re-driven 2026-10-20 on canopy 571743db, Phase 14, item 30: a pin was lost in 1 of 8 drives on the record, run 1 unrecorded, and the mechanism re-diagnosed, a table re-render from a stale pin set that the store writer then persists; fixed by canopy#761, merged 2026-10-20 as `"
        + ITEM31["sha_761"]
        + "`: the writer persists a user's toggle only and a rebuilt table writes nothing; re-driven on a leg of the fix, the forced race included, Phase 15, item 31; FIXED; segment 15).**"
    )


# ----------------------------------------------------------------------------- the ledger: the F-069 blockquote
BQ_069_ANCHOR = "matrix; on dash 4.x: unknown for the two surfaces named.\n"
BQ_069 = (
    """
> **FIXED (2026-10-20, Phase 15, item 32; canopy#760, merged as `"""
    + SHA_760
    + """`).** The dash 4 behaviour was
> measured first, as the entry asked, on a dash 4.4.1 demo leg of `571743db` with
> `util/ad-hoc/2026-10-20_f069_pair_members_probe.py`, which fires each pair's Input from the page with the
> renderer's own `dash_clientside.set_props` (it reaches a button inside a closed modal, which a click cannot) and
> records every `_dash-update-component` POST and the progress alert's DOM life
> (`reports/e2e-canopy-2026-09-02/item32-turing/pair_members.json`, label `dash-4.4.1-571743db`). **Both members of
> each pair ran on one firing.** Restart: the opener's request at +0.28 s answered at +0.64 s, `execute_restart`'s
> at +0.28 s answered at +2.61 s, the alert added at the firing and gone 1.9 s later. Live Switch: `accept_live_switch`
> at +0.17 s answered at +0.93 s, the opener at +0.17 s answered at +0.71 s, the alert added and gone within 0.16 s.
> The spinner's fate was the order of the two responses: the opener answered first in both pairs, so its `True`
> landed before the worker's `False`; had the worker answered first (a fast refusal), the opener's `True` would
> have landed last and the spinner stuck open. That inversion was not driven.
>
> **The fix.** `accept_live_switch` and `execute_restart` carry their progress alerts (and the live-swap in-flight
> store) as `running=`: the renderer sets the props the moment the request leaves and resets them when the response
> lands (`handleServerside`'s `completeJob()` runs `runningOff` before `finishLine`, in dash 3.3.0 and 4.4.1 alike,
> so the callback's own `False` lands after it), with no second callback and no round trip. The two openers and
> `_open_progress_alert_on_accept_handler` are gone. Not F-CANOPY-058's shape: that guard wrote an Interval's
> `disabled` and its release on an evicted request un-gated a poll lane; here an eviction can only close a spinner
> the user re-clicked. `src/tests/unit/frontend/test_f069_duplicate_callback_outputs.py` (9 tests; 7 fail on
> `571743db` under both dash lines) asserts no output id is claimed by two callbacks, with the ids computed as
> `create_callback_id` does over the served dependency list and parsed exactly, that the scan catches the shape that
> bit canopy on a scratch app, that each progress alert has one writer, that each of the two Inputs runs one
> callback, and the two `running` specs; `test_poll_gating.py`'s "no `running=` spec at all" pin became "none on a
> poll lane", with the three props enumerated. **The floor** is `dash>=4.0.0` (`pyproject.toml`;
> `conf/requirements_ci.txt`, the one real requirements file: `requirements.txt`, `requirements_ci.txt` and
> `conf/requirements.txt` are git symlinks into it, as root `conda_environment.yaml` is into `conf/`), and
> `conf/conda_environment.yaml` pins `dash=4.4.1=pyhd8ed1ab_0` with dash 4's two new conda-forge run dependencies,
> `comm=0.2.3` and `janus=2.0.0`, at the lock's versions. Everything canopy tests ran dash 4.x already; the conda
> file was the one environment on 3.x and the one nobody drove, and a floor nothing tests is how this stayed
> invisible. The lockfile workflow re-resolved `requirements.lock` on the branch (certifi, fastapi, pydantic-settings,
> setuptools, starlette, uvloop), a signed commit of its own.
>
> **Verified** on demo legs of the fix tree from this host (`util/ad-hoc/2026-10-20_f069_fix_leg.bash`, the tree
> built from `571743db` by `util/ad-hoc/2026-10-20_f069_apply_fix.py`, stamped `+f069-fix-unlanded`), with the
> probes Phase 14 used (`reports/e2e-canopy-2026-09-02/item32-turing/dash_version_matrix_fix.json`): **dash 3.3.0,
> ALIVE** — 179 callbacks served, 0 colliding ids, 0 renderer errors, the welcome modal open, 9 Parameters rows,
> the theme click's POST at +0.5 s; **dash 4.4.1, ALIVE** — the same, the POST at +0.8 s. The pair-members probe
> on both: one POST per firing, the alert added when the request left and removed when the response landed
> (restart 1.0–1.2 s, Live Switch 0.3–0.7 s), nothing left open. CI's unit-lane selector on the tree under dash
> 4.4.1: 7954 passed, 10 skipped, 2 failed, the two being turing's `requests` 2.32.5 against a floor the tests
> assume (E-REQ, juniper-ml#2282), failing identically on `571743db`. canopy#760's 21 required contexts green,
> Sequence Safety through six `Allow-Symbol-Loss` trailers; main-verify green on `"""
    + SHA_760
    + """`. **Not measured:** the
> inverted response order under dash 4; the two surfaces clicked through their gated modals (the probe fires the
> Input directly); a real cascor swap or restart behind the POSTs (the demo backend answered); dash 4.2.0, the Linux
> host's; the UI sub-suite under 3.x, moot at the new floor. Blast radius on a dash 3.x environment: gone; the E2
> env this phase found it in (`JuniperCanopy1`, dash 3.3.0) is now below canopy's floor, item 33.
"""
)

# ----------------------------------------------------------------------------- the ledger: the F-028 blockquote anchor
BQ_028_ANCHOR = "> needs a pin-delay knob, or reads each pin's position from `pin_requests_after_reload` and repeats until the\n> window is sampled, with enough hits to put a rate on it.\n"


def item31_prose(sha_761: str, p2_parent_lost: int, p2_fix_lost: int) -> dict:
    """The F-028 FIXED blockquote and the Phase 15 item 31 section, from the records (pass 2's two counts are the
    only inputs: the ``forced`` arm at the settled timing, parent and fix, 6 drives each)."""
    if p2_parent_lost > 0:
        p2_parent = (
            f"At the SETTLED timing (the click once the tables show their values, nothing pending; `parent_8062_dash441_forced_settled.json`) "
            f"the same write produced the race: **{p2_parent_lost} of 6 drives lost the second pin** (`LOST_B`), each with a fourth writer firing carrying every "
            f"checkbox and the new pin unchecked after the click's own response had landed, the shape of Phase 14's `early#2`; "
            f"the fix's tree under the same arm lost {p2_fix_lost} of 6 (`fix_8066_dash441_forced_settled.json`)."
        )
        p2_summary = f"the settled-timing forced arm lost the second pin in {p2_parent_lost} of 6 drives on the parent and in {p2_fix_lost} of 6 on the fix"
    else:
        p2_parent = (
            "At the SETTLED timing (the click\n"
            "> 26.6–29.9 s after the reload, once the tables show their values and nothing is pending;\n"
            "> `parent_8062_dash441_forced_settled.json`) the same write still lost nothing, 0 of 6 on the parent and "
            f"{p2_fix_lost} of 6 on the fix\n"
            "> (`fix_8066_dash441_forced_settled.json`), and **no fourth writer firing appears in any of the twelve**: the click's\n"
            "> writer went out 18.4–23.6 s after the second render, and the rebuild the write should have dispatched inside its\n"
            "> flight either waited for it (the pin store is the render's Input and the writer's Output) or re-rendered the\n"
            "> checkboxes unchanged, so the writer never saw a stale set. A synthetic store write cannot stage `early#2`'s order;\n"
            "> what did, there, was the params-store REFRESH landing inside the click's own write latency, which no instrument\n"
            "> here times. So neither instrument reproduced the race on this host: Phase 14's one hit in eight stands as the only\n"
            "> live loss on the record, and its request bodies, not a re-creation, are what the fix was derived from."
        )
        p2_summary = (
            "the settled-timing forced arm lost nothing either, 0 of 6 on the parent and "
            f"{p2_fix_lost} of 6 on the fix,\nwith no fourth writer firing in any of the twelve"
        )
    bq = (
        """
> **FIXED (2026-10-20, Phase 15, item 31; canopy#761, merged as `"""
        + sha_761
        + """`).** The writer now persists a user's toggle
> only. `update_pinned_params_store` reads which pin inputs fired the call through
> `CallbackContextAdapter.get_triggered_prop_ids()` (canopy's own seam, F-CANOPY-029's idiom; `dash.ctx.triggered_prop_ids`
> underneath, the pattern-matching ids as dicts) and hands them to `_apply_pin_toggle`, which replaces
> `_merge_pinned_params`: not exactly one `param-pin` id triggered → `no_update` (a rebuilt table arrives with every
> checkbox triggered at once; the mount render too); the toggled key's rendered value decides it alone, appended to the
> stored list if checked and absent, removed if unchecked and present, every other key carried through untouched in
> its stored order whatever its checkbox shows; a toggle the store already reflects → `no_update`. On the stale input
> Phase 14 recorded (`values=[True, False, False, False]` over `learning_rate, max_iterations, patience,
> output_epochs`, store `["learning_rate", "max_iterations"]`) the old handler returns `['learning_rate']`, the pin
> gone; the new one writes nothing. One visible change: a new pin is appended, so the sidebar lists pins in the order
> they were made (the old merge wrote render order, `max_iterations` before `learning_rate`). Pinned by
> `test_p2_wave_batch_b.py` (`TestF028PinnedParamsPreserved`: the stale rebuild after a toggle leaves the store as the
> toggle left it; the mount render writes nothing even with an empty store; the toggle cases re-stated) and
> `test_dashboard_manager_gate_coverage_inner1.py` (the raw callback through the adapter: one trigger writes, every
> trigger writes nothing). The manual's Patch Weights sentence states the row idiom (item 31b, below).
>
> **Driven** on dash 4.4.1 demo legs from this host with `2026-10-20_item30_fixwave_redrive.py --step f028` (pin
> `learning_rate`, read store and card, reload, pin `max_iterations`, read the store), which gained two arms:
> `delay<N>` pins at a fixed N seconds after the reload, and `forced` writes the params store 150 ms after the click
> (`dash_clientside.set_props`, payload `{}`) so a table rebuild is dispatched on purpose. Records:
> `reports/e2e-canopy-2026-09-02/item31-turing/` (JSON, `logs/`). **On the parent `571743db`**, fixed delays 2, 4,
> 6, 8, 10, 12 and 14 s, twice each: 0 of 14 lost (`parent_8062_dash441_delay_sweep.json`). Every arm shows the same
> three writer firings: the mount render, the second render 6.6–9.0 s after it, and the click's, **0.6–9.5 s AFTER
> the second render in every arm**, both keys checked, State `["learning_rate"]`, the store `["max_iterations",
> "learning_rate"]`: the renderer holds a click's writer behind a pending render of the checkboxes it reads, so at the
> driver's timings the click never precedes the second render, and the band the Phase 14 entry asked this phase to
> sample is not reachable by delaying the pin. The `forced` arm at the early timing (the click 2.6–3.2 s after the
> reload, the write 150 ms later) lost nothing in 6 (`parent_8062_dash441_forced.json`): the second render was still
> pending at the write, the renderer absorbed the forced rebuild into it, and no fourth writer firing appears. """
        + p2_parent
        + """
> **On the fix** (the item 31 tree, `+f069+f028-fix-unlanded`): the forced arm at the early timing 0 of 6
> (`fix_8066_dash441_forced.json`), `early,mid` ×3 0 of 6 (`fix_8066_dash441_early_mid.json`; the second pin at
> 2.3–2.9 s and 9.4–10.8 s after the reload), the fixed delays 0 of 7 (`fix_8066_dash441_delay_sweep.json`), the
> store settling at `["learning_rate", "max_iterations"]` in every arm, and the same three firings per arm, the
> rebuilds' now writing nothing by construction. M-PARAMETERS-04, -05 and -06 pass on their own expectations in every
> drive. **Not measured:** the natural race at a rate (the one live loss on the record stays Phase 14's); a real
> params-store refresh timed into the window rather than a synthetic write; the Linux host's dash 4.2.0.
"""
    )
    section = (
        """### Item 31: F-CANOPY-028

The fix is in the F-CANOPY-028 entry's FIXED blockquote: the pin-store writer persists a user's toggle only, read
through `CallbackContextAdapter.get_triggered_prop_ids`, and a rebuilt table writes nothing; `_merge_pinned_params`
became `_apply_pin_toggle`; the stale-rebuild case is a unit test. What this phase adds to Phase 14's record of the
race is a negative result worth keeping: **at the driver's timings the click's writer is held behind the pending
second render in every drive** (0 of 14 lost at fixed delays of 2–14 s on the parent), so the loss band the entry
asked for cannot be sampled by delaying the pin, and a synthetic params-store write 150 ms after the click is
absorbed by the pending render at the early timing (0 of 6); """
        + p2_summary
        + """. The fix's tree lost nothing in 25 drives
(forced 12, early/mid 6, delays 7) with the same three writer firings per arm, the rebuild firings now inert by
construction; the mechanism stays what `early#2`'s request bodies show, pinned by the unit test rather than by a
live re-creation. canopy#761 merged 2026-10-20T19:34Z as `"""
        + sha_761
        + """`, cut from #760's squash, two signed commits, 21
required contexts green.

**Item 31b, the manual.** `docs/USER_MANUAL.md`'s Patch Weights sentence said values could be "comma-, semicolon-,
or newline-separated floats". For `output_weights`, `_parse_float_rows` reads semicolons and newlines as ROW
separators and `_resolve_patch_values` reshapes only a flat comma list (from the topology), so a flat list broken up
by either was refused on any network with more than one output (F-CANOPY-012's cases B and C, Phase 14). The sentence
now states the row idiom and the flat-list reshape; the parser is unchanged, the smaller of the two changes the
entry offered.

"""
    )
    return {"bq_028": bq, "section": section}

# ----------------------------------------------------------------------------- the ledger: Phase 15
PHASE15_HEAD = (
    """
## Phase 15 — 2026-10-20: items 32 and 31 — F-CANOPY-069 is FIXED (canopy#760) and F-CANOPY-028 is FIXED (canopy#761); the dash floor is 4.0.0; the open P0 count returns to 0 and the open P1 count falls from 5 to 4

### Who, and from what

The session in juniper-ml worktree `sequential-coalescing-boot` on turing (macOS; Chrome 145 headless under
Playwright's `chrome` channel; the CDN stylesheet aborted in the browser, so every page unstyled; no trio), from
`HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`, with the owner's merge approval for the
session. Every leg served a tree copied from the E2 tree, proved byte-identical to canopy `main` `"""
    + SHA
    + """` for every
file the fixes touch by `util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py` (git blob ids against the contents
API) before the fix scripts ran on the copy, and stamped `+f069-fix-unlanded` or `+f069+f028-fix-unlanded` on
`/v1/health` so no leg of an uncommitted tree reads as a commit. Both fixes landed from this host through the API
as GitHub-signed commits (`util/push_signed_commit.py`, one branch each, the files uploaded whole from the fix
trees), each built by a replayable exact-match script in `util/ad-hoc/` (`2026-10-20_f069_apply_fix.py`,
`2026-10-20_f028_apply_fix.py`) that refuses anything but the expected text. Legs: one at a time (16 GiB),
`util/ad-hoc/2026-10-20_turing_canopy_leg.bash` for the parent and `2026-10-20_f069_fix_leg.bash` for the fix
trees, demo mode, cascor and juniper-data pointed at a closed port. canopy `main` did not move between
`571743db` and canopy#760; canopy#761 was cut from #760's squash.

### Item 32: F-CANOPY-069

What the entry asked for first, which member of each colliding pair dash 4 runs, was measured on a dash 4.4.1 leg
of `"""
    + SHA
    + """` before anything was changed: **both**, with the spinner's fate decided by response order (the F-CANOPY-069
entry's FIXED blockquote has the figures). The fix, the test, the floor and the verification are in that
blockquote; in brief, the two opener callbacks are gone and the two working callbacks carry their alerts as
`running=`, the floor is `dash>=4.0.0`, the conda file pins 4.4.1, and legs of the fix are ALIVE under dash 3.3.0
and 4.4.1 with one callback per Input. canopy#760 merged 2026-10-20T18:58Z as `"""
    + SHA_760
    + """`.

Two facts about the repo found on the way, recorded here because they cost time: `requirements.txt`,
`requirements_ci.txt` and `conf/requirements.txt` are git symlinks resolving to `conf/requirements_ci.txt`, and root
`conda_environment.yaml` is one into `conf/`; the contents API reports each as a `file` whose `sha` is the LINK's own
blob (sha1 of the target path), serving the target's content. A whole-file upload to a symlink's path would replace
the link with a file. And canopy's `addopts` already carries `-q`, so a second `-q` hides pytest's summary line
(the unit-lane count in the F-CANOPY-069 blockquote was read from the progress dots).

"""
)

PHASE15_TAIL_TEMPLATE = """### What this phase cannot support

- **One host, one browser, no trio, unstyled pages, demo backends.** Every figure is turing's; the POSTs behind
  the Live Switch accept and the restart confirm reached the demo backend or a closed port, not cascor; no VIS half
  of any row was scored.
- **The two F-CANOPY-069 surfaces were fired, not clicked.** `set_props` reaches the buttons inside their closed
  modals; the modals' gates (the experimental flag, a running training) were not exercised. Item 27 clicks through
  the Live Switch modal and will.
- **The inverted response order under dash 4 was not driven**, and dash 4.2.0 (the Linux host's) was not run.
- **F-CANOPY-028's race was not reproduced live.** 0 of 14 at fixed delays and 0 of 12 on the `forced` arm on the
  parent (a synthetic params-store write 150 ms after the click produced no fourth writer firing at either timing).
  The one live loss on the record is Phase 14's `early#2`; the fix is derived from its request bodies and pinned
  by the unit test, and the live drives on the fix (25) show no loss. The rate at which real use hits the race is
  what Phase 14 measured, once in eight, and nothing here refines it.
- **The unit lane's two red tests are the environment's** (E-REQ), on the parent and the fix alike.

### Consensus record (§7 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`)

CONSENSUS_RECORD_PLACEHOLDER

### Matrix effect and counts

- `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`: M-PARAMETERS-06's cell no longer
  says F-CANOPY-028 stands. No row maps to F-CANOPY-069 (on dash 3.x it blocked every row; the matrix was never
  driven on dash 3.x, and the floor now excludes it).
- Triage (`util/ad-hoc/e2e_finding_triage.py`): 80 findings, **63 fixed**, 1 accepted, 2 withdrawn, **14 open: 0 P0,
  4 P1** (F-CANOPY-064, -065, F-CASCOR-001, -002), **10 P2**. F-CANOPY-069's and F-CANOPY-028's tails carry FIXED.

### Still owed after this phase

Phase 14's list stands, items 0 to 32, with these changes:

- **Items 31 and 32 are DONE** (canopy#761, canopy#760).
- **Items 25 and 28** are unchanged (the trio, the Linux host). **Item 27** is unchanged; a demo leg on this host
  serves it (`2026-10-20_turing_canopy_leg.bash up <port> demo` on the dash 4.4.1 venv, or any venv at the floor
  now). **Item 29** is unchanged. **Item 26's second step** is unchanged (O17).
- **Every leg runs dash 4.x by the floor now**; a dash 3.x venv is below it and is not a canopy environment.

New item:

33. **turing's E2 canopy env is below canopy's floor.** `JuniperCanopy1` (conda, dash 3.3.0, built from a
    re-specified `conf/conda_environment.yaml` for osx-64, juniper-ml#2282) no longer satisfies `dash>=4.0.0`; the
    scratch venvs over it that pin a dash (`JuniperCanopy1-dash304/-dash32/-dash34`) are throwaways and can go.
    Owner: `pip install -e .` in the env upgrades dash (the lock's 4.4.1 resolves there; `comm` and `janus` come
    with it), or rebuild from the corrected conda file; then re-run the canopy lanes the E2 record cites and
    record an erratum in the bring-up plan's E2 section. Until then a leg from that env's own interpreter is a leg
    on dash 3.3.0 of a tree whose floor excludes it.
"""

# ----------------------------------------------------------------------------- the matrix
MATRIX_ROWS = [
    (
        "| M-PARAMETERS-06 ",
        "PASS (re-validated @ 571743db, 2026-10-20, item 30; but F-CANOPY-028 stands: a pin made just before the tables re-render from a stale pin set is lost, 1 of 8 drives on the record) |",
        "PASS (re-validated @ 571743db, 2026-10-20, item 30; F-CANOPY-028, a pin made just before the tables re-render from a stale pin set, FIXED by canopy#761, Phase 15, item 31: the writer persists a user's toggle only) |",
    ),
]

# ----------------------------------------------------------------------------- the handoffs
BANNER = """
> **SUPERSEDED 2026-10-20** by `HANDOFF_2026-10-20_canopy-phase15-items-31-32-done-f069-f028-fixed.md`.
> Its item 1 (juniper-ml#2291 merged 2026-10-20T13:59:34Z), item 2 (item 32: canopy#760, F-CANOPY-069 FIXED, the dash
> floor 4.0.0) and item 3 (item 31: canopy#761, F-CANOPY-028 FIXED, the manual's row idiom) are done, recorded as
> Phase 15 of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`; items 4 to 7 carry there as
> items 27, 25, 28, 29 and 26's second step, with new item 33.
"""

PARENT_OLD = """   Current Lane A handoff:
   `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`. The status as of 2026-10-08
   follows, for context."""
PARENT_NEW_TEMPLATE = """   Phase 15 (2026-10-20, on turing) did items 32 and 31: F-CANOPY-069 is FIXED (canopy#760, merged as
   `{sha760}`: the progress alerts are `running=` specs, the two opener callbacks are gone, the dash floor is 4.0.0) and
   F-CANOPY-028 is FIXED (canopy#761, merged as `{sha761}`: the pin writer persists a user's toggle only); triage
   80/63/1/2/14, 0 open P0, 4 open P1, 10 open P2; new item 33 (turing's E2 canopy env is below the floor).
   Current Lane A handoff:
   `HANDOFF_2026-10-20_canopy-phase15-items-31-32-done-f069-f028-fixed.md`. The status as of 2026-10-08
   follows, for context."""

INDEX_OLD_PTR = "(Lane A's current one: `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`)"
INDEX_NEW_PTR = "(Lane A's current one: `HANDOFF_2026-10-20_canopy-phase15-items-31-32-done-f069-f028-fixed.md`)"
INDEX_OLD_TAIL = "Next: items 32 (F-CANOPY-069, canopy code), 31 (F-CANOPY-028, canopy code; the manual's Patch Weights idiom), 27 (the Live Switch allow arm, a demo leg on turing can serve it), 25 and 28 (the trio). Y2 wave 2 is stalled at round 15."
INDEX_NEW_TAIL_TEMPLATE = (
    "Phase 15 (2026-10-20, on turing) did items 32 and 31: F-CANOPY-069 is FIXED (canopy#760, `{sha760}`: the progress alerts are `running=` specs, the opener callbacks are gone, the dash floor is 4.0.0 and the conda file pins 4.4.1; legs of the fix ALIVE under dash 3.3.0 and 4.4.1) and F-CANOPY-028 is FIXED (canopy#761, `{sha761}`: the pin writer persists a user's toggle only and a rebuilt table writes nothing; 25 drives on the fix lose no pin; the race itself was not re-created live, 0 of 26 on the parent); 80/63/1/2/14, 0 open P0, 4 open P1, 10 open P2. "
    "Next: items 27 (the Live Switch allow arm, a demo leg on turing can serve it), 25 and 28 (the trio), 29 (the Linux host), 26's second step (O17), 33 (turing's E2 canopy env below the floor; owner). Y2 wave 2 is stalled at round 15."
)

HANDOFF_TEXT_TEMPLATE = """# HANDOFF 2026-10-20 — P2 canopy Lane A: Phase 15 recorded. Items 32 and 31 are DONE: F-CANOPY-069 is FIXED (canopy#760, the dash floor is 4.0.0) and F-CANOPY-028 is FIXED (canopy#761). 0 open P0, 4 open P1, 10 open P2. Next are items 27, 25, 28, 29, 26's second step and the owner's 33

**Written**: 2026-10-20 by the session in juniper-ml worktree `.claude/worktrees/sequential-coalescing-boot` on host
turing (macOS; no trio; throwaway legs from copies of the E2 tree), at a phase boundary, as its PR was opened.
**Consensus**: CONSENSUS_SUMMARY_PLACEHOLDER (ledger Phase 15, Consensus record).
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`, authoritative for P2.
Its items 5 and 7 and the owner batch O1–O17 carry over. This file supersedes
`HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`.
**Merge approval**: the owner granted it for this session. It is NOT carried: ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A (the juniper-canopy E2E validation arc) from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase15-items-31-32-done-f069-f028-fixed.md`
(juniper-ml). Read it in full, then the parent `HANDOFF_2026-10-03_canopy-consolidated.md`. Run the verification
commands first. Merge approval is not carried: ask before the first merge. Item 27 is a demo leg on this host (any
venv at canopy's floor, dash 4.x) and the Live Switch modal's allow arm; items 25 and 28 need the trio on the Linux
host; item 29 is the Linux host; item 33 is the owner's (turing's E2 canopy env is below canopy's floor).

**Completed:**

- **juniper-ml#2291 merged** on 2026-10-20T13:59:34Z: Phase 14 of
  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` and
  `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`.
- **canopy#760 merged** 2026-10-20T18:58Z as `@@SHA760@@` (item 32, F-CANOPY-069). Measured first on a dash 4.4.1
  leg of `571743db`: both members of each colliding pair run on one firing and the spinner's fate is the order of
  their responses (`reports/e2e-canopy-2026-09-02/item32-turing/pair_members.json`). The fix: `accept_live_switch`
  and `execute_restart` carry their progress alerts (and the live-swap in-flight store) as `running=`; the two
  opener callbacks and `_open_progress_alert_on_accept_handler` are gone; `test_f069_duplicate_callback_outputs.py`
  pins "no output id is claimed by two callbacks" (7 of 9 fail on `571743db`); the floor is `dash>=4.0.0`
  (`pyproject.toml`, `conf/requirements_ci.txt`) and `conf/conda_environment.yaml` pins dash 4.4.1 with `comm` and
  `janus`. Legs of the fix: ALIVE under dash 3.3.0 and 4.4.1, one POST per firing, the alert opening on the request
  and closing on the response (`dash_version_matrix_fix.json`, `pair_members.json`). Unit lane 7954/10/2 (E-REQ).
- **canopy#761 merged** 2026-10-20 as `@@SHA761@@` (item 31, F-CANOPY-028). The pin-store writer persists a user's
  toggle only (exactly one pin input triggered, read through `CallbackContextAdapter.get_triggered_prop_ids`);
  a rebuilt table (every input triggered at once) writes nothing; `_merge_pinned_params` → `_apply_pin_toggle`;
  `TestF028PinnedParamsPreserved` re-stated with the stale-rebuild case; the manual's Patch Weights sentence states
  the row idiom (item 31b). Drives (`reports/e2e-canopy-2026-09-02/item31-turing/`): the parent lost no pin at
  fixed delays (0 of 14) and @@PARENT_FORCED@@ on the `forced` arm (a params-store write 150 ms after the click,
  early#2's order); the fix lost @@FIX_FORCED@@ forced, @@FIX_EARLY_MID@@ early/mid ×3 and @@FIX_DELAYS@@ at the
  fixed delays.
- **The ledger's Phase 15** (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, 2026-10-20)
  records both, with the F-CANOPY-069 and F-CANOPY-028 headers FIXED and a dated blockquote in each; counts 80
  findings, 63 fixed, 1 accepted, 2 withdrawn, 14 open: 0 P0, 4 P1 (F-CANOPY-064, -065, F-CASCOR-001, -002),
  10 P2; new item 33.
- **This session's PR** carries the ledger, the matrix (M-PARAMETERS-06's cell), this file, the SUPERSEDED banner
  on `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`, the pointer in
  `HANDOFF_2026-10-03_canopy-consolidated.md`, the P2 row of `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`,
  the records under `reports/e2e-canopy-2026-09-02/item32-turing/` and `item31-turing/` (JSON and logs; the
  screenshots stay on turing), Phase 15's consensus records and the scripts `util/ad-hoc/2026-10-20_*` named
  below. Find it with `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase15 --state all`.

**Remaining, in order:**

1. **Land this session's PR** if it has not merged: `python3 util/wait_for_checks.py --pr N`, query
   `reviewThreads(isResolved:false)`, ask the owner, then `python3 util/safe_merge.py --pr N --execute` and read its
   `MERGED` line. Afterwards re-check `origin/main`:
   `python3 -B util/ad-hoc/e2e_finding_triage.py | tail -8` should print 80 / 63 / 1 / 2 / 14 with no open P0.
2. **Item 27** (the Live Switch allow arm): a demo leg on this host serves it
   (`bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash up 8062 demo http://127.0.0.1:9 ~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python`,
   then `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py` adapted to the chrome channel and the CDN route);
   it clicks through the Live Switch modal, which Phase 15's probe only fired.
3. **Items 25 and 28** on the Linux host, against the trio (ledger Phase 12). **Item 29**, the Linux host.
4. **Item 33** (owner): bring turing's `JuniperCanopy1` env to canopy's floor (`pip install -e .` there resolves
   dash 4.4.1, `comm`, `janus`), re-run the lanes the E2 record cites, erratum in the bring-up plan's E2 section;
   the dash 3.x scratch venvs can go.
5. **Item 26's second step** once the owner rules (O17).
6. Then the parent's items 5 and 7, and the owner batch O1–O17.

**Traps learned:**

- **`requirements.txt`, `requirements_ci.txt` and `conf/requirements.txt` are git symlinks** resolving to
  `conf/requirements_ci.txt`; root `conda_environment.yaml` is one into `conf/`. The contents API reports a symlink
  as a `file` whose `sha` is the link's own blob (sha1 of the target path) while serving the target's content, so
  the blob check "mismatches" on them. Edit and upload the target; a whole-file upload to the link's path would
  replace the link with a file.
- **The lockfile workflow pushes a signed commit to a PR branch** after a `pyproject.toml` change (canopy#760 got one
  re-resolving `requirements.lock`). Pin `--expected-head` on the PR's current head (`gh pr view N --json headRefOid`),
  not on your last push; `safe_merge.py` merges the head CI passed on.
- **canopy's `addopts` carries `-q`**; a second `-q` hides pytest's summary line. Count the dots, or drop yours.
- **flake8-simplify crashes under Python 3.14** (`ast.Str`), so the src profile cannot run in the E2 env; pyflakes,
  pycodestyle and the tests profile run, and CI's pre-commit (3.12/3.13/3.14 lanes) is the judge.
- **`dash_clientside.set_props` fires callbacks for a component inside a closed modal**, which a click cannot reach;
  that is how the two F-CANOPY-069 surfaces were driven without their gates.
- **The renderer queues a click's writer behind a pending table render**, so a pin at a fixed delay after the reload
  never hits F-CANOPY-028's window, and a synthetic params-store write after the click (the `forced` arm) produces
  no writer firing at all: neither instrument re-creates early#2's order, which came from the params-store REFRESH
  landing inside the click's write latency. Give every driver run its own `--out`.
- **The guard refuses** `for` loops over `$p/bin/python`, `awk` programs, and compound commands naming `.github/`
  paths; one plain command per call, interpreters by path, logic in a script.
- **A dash 3.x venv is below canopy's floor now**; so is the E2 env (item 33). A leg from it runs dash 3.3.0 on a
  tree that excludes it, and a dash 4.x venv over the same tree is what a leg should use.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/<your worktree>   # or the Linux host's path
git status --short; git log --oneline -3
gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase15 --state all --json number,state,mergedAt
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -8   # 80 / 63 / 1 / 2 / 14; P1 4; P2 10; no P0 line
python3 -B util/ad-hoc/e2e_finding_triage.py --open-only | grep -c '^OPEN   P1 '   # 4
grep -n '^## Phase 15' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md
gh pr view 760 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED @@SHA760@@
gh pr view 761 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED @@SHA761@@
python3 -I -c "import json; m=json.load(open('reports/e2e-canopy-2026-09-02/item32-turing/dash_version_matrix_fix.json')); print({k: v['verdict'] for k, v in m.items()})"   # two ALIVE
ls ~/.local/state/juniper/turing-e2/venvs/   # on turing: JuniperCanopy1{,-dash304,-dash32,-dash34,-dash44}
lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8101|8202|8051|8052|8053|806[0-9]|8222) '   # on turing: nothing; on the Linux host: the trio up (never touch it)
```

## Git state

- **juniper-ml:** branch `docs/canopy-e2e-phase15`, landed from turing through the API as signed commits.
  Worktree `sequential-coalescing-boot` holds the same files uncommitted (the frozen drafts the consensus rounds
  reviewed are local commits that never leave the host).
- **juniper-canopy:** `main` `@@SHA761@@` (canopy#761 on canopy#760 `@@SHA760@@` on `571743db`); both branches merged by
  squash. The fix trees `~/.local/state/juniper/turing-e2/trees/juniper-canopy-f069` and `-f028` are copies of
  the E2 tree with the scripts applied (no `.git`).
- **Services:** none left on this host; the legs were torn down (`… down <port>`). The scratch venvs and the
  snapshots under `~/.local/state/juniper/turing-e2/legs/` remain.

## Changed by this session

- **Created:** this file; `util/ad-hoc/2026-10-20_f069_pair_members_probe.py`; `util/ad-hoc/2026-10-20_f069_apply_fix.py`;
  `util/ad-hoc/2026-10-20_f069_fix_leg.bash`; `util/ad-hoc/2026-10-20_f028_apply_fix.py`;
  `util/ad-hoc/2026-10-20_item31_f028_drives.bash`; `util/ad-hoc/2026-10-20_phase15_items31_32_apply.py`;
  `reports/e2e-canopy-2026-09-02/item32-turing/` and `item31-turing/` (records and logs; the screenshots stay on
  turing, LFS); `reports/e2e-canopy-2026-09-02/drafts/lane15*_phase15_ledger_brief.md`;
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase15_round*.md`;
  `util/ad-hoc/2026-10-20_phase15_ledger_round*_corrections.py`.
- **Modified:**
  - `util/ad-hoc/2026-10-20_item30_fixwave_redrive.py`: the `delay<N>` and `forced` f028 arms, `--f028-forced-gap-ms`,
    the `LOST_B` verdict;
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: Phase 15; the headers of F-CANOPY-069
    and F-CANOPY-028 and a dated blockquote in each;
  - `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`: M-PARAMETERS-06's cell;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`: the Lane A pointer;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: the P2 row;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`:
    the SUPERSEDED banner.
- **In juniper-canopy** (canopy#760, #761): `src/frontend/dashboard_manager.py`, `pyproject.toml`,
  `conf/requirements_ci.txt`, `conf/conda_environment.yaml`, `CHANGELOG.md`, `docs/USER_MANUAL.md`,
  `src/tests/unit/frontend/test_f069_duplicate_callback_outputs.py` (new), `test_live_dataset_switch_handlers.py`,
  `test_dashboard_manager_gate_coverage_inner1.py`, `test_dashboard_manager_gate_coverage_inner2.py`,
  `test_poll_gating.py`, `test_p2_wave_batch_b.py`; `requirements.lock` by the lockfile workflow.
- **Outside the repo**, in auto-memory: `MEMORY.md`, `canopy-e2e-arc-state.md`.
"""


def handoff_text() -> str:
    text = HANDOFF_TEXT_TEMPLATE
    for token, value in (
        ("@@SHA760@@", SHA_760),
        ("@@SHA761@@", ITEM31["sha_761"]),
        ("@@PARENT_FORCED@@", ITEM31["parent_forced"]),
        ("@@FIX_FORCED@@", ITEM31["fix_forced"]),
        ("@@FIX_EARLY_MID@@", ITEM31["fix_early_mid"]),
        ("@@FIX_DELAYS@@", ITEM31["fix_delays"]),
    ):
        text = text.replace(token, value)
    assert "@@" not in text, "an unfilled token remains in the handoff"
    return text


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
    ITEM31["prose"] = item31_prose(SHA_761, P2_PARENT_LOST, P2_FIX_LOST)
    missing = [k for k, v in ITEM31.items() if v is None]
    if missing:
        raise SystemExit(f"ITEM31 facts not filled: {missing}")
    ledger_p = root / LEDGER
    ledger = ledger_p.read_text(encoding="utf-8")
    assert "## Phase 15" not in ledger, "Phase 15 is already applied"
    check_header(HEADER_069_NEW, "P0", "FIXED")
    check_header(header_028_new(), "P1", "FIXED")
    ledger = replace_once(ledger, HEADER_069_OLD, HEADER_069_NEW, "F-069 header")
    ledger = replace_once(ledger, HEADER_028_OLD, header_028_new(), "F-028 header")
    ledger = replace_once(ledger, BQ_069_ANCHOR, BQ_069_ANCHOR + BQ_069, "F-069 blockquote")
    bq_028 = ITEM31["prose"]["bq_028"]
    ledger = replace_once(ledger, BQ_028_ANCHOR, BQ_028_ANCHOR + bq_028, "F-028 blockquote")
    phase15 = PHASE15_HEAD + ITEM31["prose"]["section"] + PHASE15_TAIL_TEMPLATE
    ledger = ledger.rstrip("\n") + "\n" + phase15

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
    assert "SUPERSEDED 2026-10-20** by `HANDOFF_2026-10-20_canopy-phase15" not in prev
    first_nl = prev.index("\n")
    prev = prev[: first_nl + 1] + BANNER + prev[first_nl + 1 :]

    subs = {"sha760": SHA_760, "sha761": ITEM31["sha_761"]}
    parent_p = root / HANDOFF_PARENT
    parent = replace_once(parent_p.read_text(encoding="utf-8"), PARENT_OLD, PARENT_NEW_TEMPLATE.format(**subs), "parent pointer")

    index_p = root / INDEX
    index = index_p.read_text(encoding="utf-8")
    index = replace_once(index, INDEX_OLD_PTR, INDEX_NEW_PTR, "INDEX pointer")
    index = replace_once(index, INDEX_OLD_TAIL, INDEX_NEW_TAIL_TEMPLATE.format(**subs), "INDEX tail")

    new_handoff = handoff_text()

    if check_only:
        print("check OK: every anchor is unique and every rewritten header triages as intended")
        return
    ledger_p.write_text(ledger, encoding="utf-8")
    matrix_p.write_text(matrix, encoding="utf-8")
    prev_p.write_text(prev, encoding="utf-8")
    parent_p.write_text(parent, encoding="utf-8")
    index_p.write_text(index, encoding="utf-8")
    (root / HANDOFF_NEW).write_text(new_handoff, encoding="utf-8")
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
