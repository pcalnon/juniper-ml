#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-21
# Status      : ad-hoc — one-off correction pass; RETAINED as provenance (owner policy 2026-08-25)
# Retire when : RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : ledger Phase 15 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md);
#               util/ad-hoc/2026-10-21_phase15_ledger_round1_corrections.py (the pass before this one);
#               reports/e2e-canopy-2026-09-02/consensus/2026-10-21_validator_reports_phase15_round2.md (the report)
# ---------------------------------------------------------------------------
"""Round 2's correction pass on the ledger's Phase 15 and the files that land with it.

Applied after ``2026-10-21_phase15_ledger_round1_corrections.py``, to the files as frozen for round 2 (local commit
``f65541a5``). Round 2 was one lane, Lane 15-B (adversarial analysis, re-run after round 1's spawn died on an API
usage-credit error): SOUND-WITH-FIXES, five MAJORs and fifteen MINORs, all applied here. The reconciler re-derived
each before applying it: the click gaps from the drive logs (5.4–8.1 s early, 1.3–3.4 s settled), the parser on the
item 31 tree (``0.1 0.2`` refused), the venv layout, the drive script, the registry (canopy#760's own
``test_callback_map_and_served_list_agree`` passes on ``571743db``).

* MAJOR 1 F-CANOPY-028's account of why the race was not re-created: every click landed after the second render
  (the recorded delay is the pin step, not the click); nothing holds the writer; the forced write cannot stage
  ``early#2``'s order. The F-028 blockquote's "Driven" paragraph, the item 31 section, "cannot support", the handoff.
* MAJOR 2 item 31b's new manual sentence is wrong for the 1-D targets: new item 34.
* MAJOR 3 ledger items 18–21 were in no handoff: the handoff's Remaining list, its goal statement, the INDEX row.
* MAJOR 4 item 33's recipe: re-sync the tree first, then install into the E2 venv.
* MAJOR 5 item 27 extended to click through the modals; the leg wrapper takes a base sha.
* MINORs 1–15: wordings, the M-06 claim, the eviction residual, the provenance sentence, the round-1 record, landing
  statements, ``--expected-head``, screenshots, the driver's arms, M-PARAMETERS-04's Expected cell, and an erratum to
  Phase 14's F-CANOPY-069 text (two pairs and three ids; no registration overwritten).

Round 3's placeholders are left for ``2026-10-21_phase15_ledger_round3_corrections.py``.

Usage:
    python3 -I util/ad-hoc/2026-10-21_phase15_ledger_round2_corrections.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
MATRIX = "notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts"
HANDOFF = f"{HANDOFF_DIR}/HANDOFF_2026-10-21_canopy-phase15-items-31-32-done-f069-f028-fixed.md"
HANDOFF_PREV = f"{HANDOFF_DIR}/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md"
HANDOFF_PARENT = f"{HANDOFF_DIR}/HANDOFF_2026-10-03_canopy-consolidated.md"
INDEX = f"{HANDOFF_DIR}/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md"

_PRI_RE = re.compile(r"\b(P0/P1|P0|P1|P2|CRITICAL|LEDGER)\b")

# ============================================================================= the ledger: exact substitutions
LEDGER_SUBS = [
    (
        "MINOR 15: Phase 14's summary, two pairs",
        "Cause: three callback pairs claim one\n  `allow_duplicate` output with identical inputs, so their ids collide",
        "Cause: two callback pairs (Phase 14 said three; erratum, Phase 15) claim the same\n  `allow_duplicate` outputs with identical inputs, so three output ids collide",
    ),
    (
        "MINOR 15: F-069's header, two pairs",
        "three callback pairs claim one `allow_duplicate` output with identical inputs, their ids collide,",
        "two callback pairs claim the same `allow_duplicate` outputs with identical inputs, three output ids collide,",
    ),
    (
        "MINOR 15: Phase 14's legs paragraph, no overwrite",
        "(`callback_map` keyed by\nthat id, `dash/_callback.py:311` in 3.3.0 and `:338` in 4.4.1, the second overwriting the first's entry; the dependency list served to the\nrenderer keeps both)",
        "(`callback_map`,\n`dash/_callback.py:311` in 3.3.0 and `:338` in 4.4.1, is keyed by each callback's whole output string, which\ndiffers between the two members, so both entries stand, and the dependency list served to the renderer keeps\nboth; erratum, Phase 15: this said the second overwrote the first's entry)",
    ),
    (
        "MINOR 15: F-069's why-green, no overwrite",
        "the\ncallback registry is a dict keyed by the id, `_callback.py:311` in 3.3.0 and `:338` in 4.4.1, and the second registration overwrites the\nfirst's entry while the dependency list keeps both)",
        "the\ncallback registry is a dict keyed by each callback's whole output string, `_callback.py:311` in 3.3.0 and `:338` in\n4.4.1, so both members of a pair register and the dependency list keeps both; erratum, Phase 15: this said the\nsecond registration overwrites the first's entry)",
    ),
    (
        "MINOR 1: the alert's add time",
        "the alert added at the firing and gone 1.9 s later.",
        "the alert added when the opener's answer landed and gone 1.9 s later, with the worker's.",
    ),
    (
        "MINOR 2: response times, not alert lives",
        "> (restart 1.0–1.2 s, Live Switch 0.3–0.7 s), nothing left open.",
        "> (the responses at +1.0–1.2 s for the restart and +0.3–0.7 s for the Live Switch), nothing left open.",
    ),
    (
        "MINOR 5: two of three new run dependencies",
        "with dash 4's two new conda-forge run dependencies,\n> `comm=0.2.3` and `janus=2.0.0`, at the lock's versions.",
        "with the two of the 4.4.1 build's new\n> run dependencies the file lacked, `comm=0.2.3` and `janus=2.0.0`, at the lock's versions (the third, `pydantic>=2.10`,\n> is pinned there at 2.12.5).",
    ),
    (
        "MINOR 6: the floor's counter-position",
        "a floor nothing tests is how this stayed\n> invisible.",
        "a floor nothing tests is how this stayed\n> invisible. The counter-position (canopy#760's body names half of it): the fix is ALIVE on 3.3.0, so the floor is a\n> policy choice, and 4.0.0 is itself untested (CI pins 4.1.0 in its conda lane and resolves 4.4.1 in its pip lane), so\n> `>=4.1.0` or a CI lane at the floor would make it a tested one (round 2, Lane 15-B).",
    ),
    (
        "MINOR 3: the stale input is early#2's third body",
        "On the stale input\n> Phase 14 recorded (`values=[True, False, False, False]` over `learning_rate, max_iterations, patience,\n> output_epochs`, store `[\"learning_rate\", \"max_iterations\"]`) the old handler returns `['learning_rate']`, the pin\n> gone; the new one writes nothing.",
        "On the stale input\n> Phase 14 recorded (`early#2`'s third body: 22 boxes triggered, `learning_rate` checked and `max_iterations` not,\n> State `[\"max_iterations\", \"learning_rate\"]`) the old handler returns `['learning_rate']`, the pin gone; the new one\n> writes nothing (the unit test pins a four-key analogue).",
    ),
    (
        "MAJOR 2: item 31b's sentence is wrong for the 1-D targets",
        "The sentence\nnow states the row idiom and the flat-list reshape; the parser is unchanged, the smaller of the two changes the\nentry offered.",
        "The sentence\nnow states the row idiom and the flat-list reshape for `output_weights`; the parser is unchanged. **Its first clause\nis wrong** (round 2, Lane 15-B; re-derived on the item 31 tree): \"Values are floats separated by commas or spaces\"\n(`aeeaf29b` `docs/USER_MANUAL.md:500`) fails the other three targets, which `_parse_float_list`\n(`network_editor_panel.py:418-434`) splits on commas, semicolons and newlines only, so `0.1 0.2` for `output_bias` is\nrefused (`could not convert string to float: '0.1 0.2'`), and the forms those targets do accept are no longer\ndocumented. Owed as item 34, before the release that ships canopy#761.",
    ),
    (
        "MAJOR 5: cannot support, item 27",
        "Item 27 clicks through\n  the Live Switch modal and will.",
        "Item 27's drive samples\n  only the Live Switch button's gate; clicking through either modal is owed (item 27, extended).",
    ),
    (
        "MAJOR 1: cannot support, F-028",
        "- **F-CANOPY-028's race was not reproduced live.** 0 of 14 at fixed delays and 0 of 12 on the `forced` arm on the\n  parent (a synthetic params-store write 150 ms after the click produced no fourth writer firing at either timing).\n  The one live loss on the record is Phase 14's `early#2`; the fix is derived from its request bodies and pinned\n  by the unit test, and the live drives on the fix (25) show no loss.",
        "- **F-CANOPY-028's race was not reproduced live.** 0 of 14 at driver delays and 0 of 12 on the forced arms on the\n  parent: every click landed after the second render, and the forced write produced no fourth writer firing at\n  either timing. The one live loss on the record is Phase 14's `early#2`; the fix is derived from its request bodies\n  and pinned by the unit test, and the live drives on the fix (25) show no loss, which cannot discriminate: the same\n  instrument lost nothing on the parent.",
    ),
    (
        "MINOR 7a: round 1's record, every other figure",
        "every count, and every item 31 and item 32 figure, matched its",
        "every count, and every other item 31 and item 32 figure, matched its",
    ),
    (
        "MINOR 7b: round 1's record, who agreed",
        "Every figure agreed within\n    run-to-run timing.",
        "The lane reported steps 1, 2\n    and 5 as agreeing; the reconciler found steps 3 and 4 agreeing within run-to-run timing.",
    ),
    (
        "MINOR 7c: round 1's record, why round 2",
        "**Round 1 changed one action's parameter** (item 27's tree), so the review continued.",
        "**Round 1 changed one action's parameter** (item 27's tree, the reconciler's consequence of Lane 15-A's step\n    2, which no lane reported), and its corrections alone require a second round (procedure §4), so the review\n    continued.",
    ),
    (
        "MINOR 14: matrix effect",
        "M-PARAMETERS-06's cell no longer\n  says F-CANOPY-028 stands.",
        "M-PARAMETERS-06's cell no longer\n  says F-CANOPY-028 stands, and M-PARAMETERS-04's Expected cell describes the writer as canopy#761 left it (round 2).",
    ),
    (
        "MAJORs 1-3: still owed, items 31 and 32; items 18-21",
        "- **Items 31 and 32 are DONE** (canopy#761, canopy#760).\n",
        "- **Item 32 is DONE** (canopy#760). **Item 31 is DONE** (canopy#761) except (b)'s first clause: the new sentence is\n  wrong for the 1-D targets (new item 34); (a)'s ask to time a pin before the second render was not met (the\n  driver's clicks land after it) and is dropped now that the fix is merged.\n- **Items 18–21** (canopy code: F-CANOPY-064, -067, -060, -063, -065, -066) stand as Phase 10 wrote them and Phase 13\n  re-stated them; no handoff carried them until this phase's.\n",
    ),
    (
        "MAJOR 5: still owed, item 27 extended",
        "**Item 27** is unchanged; a demo leg on this host\n  serves it (`2026-10-20_turing_canopy_leg.bash up <port> demo` on the dash 4.4.1 venv, or any venv at the floor\n  now), from a tree proved equal to canopy `main` (`aeeaf29b` or later): the E2 tree is still `571743db`, which\n  predates both fixes, and on it the Live Switch spinner sticks open whenever the swap POST outruns the opener.",
        "**Item 27** is extended: a demo leg on this host\n  serves it, from a tree proved equal to canopy `main` (`aeeaf29b` or later; the E2 tree is still `571743db`, which\n  predates both fixes, and on it the Live Switch spinner sticks open whenever the swap POST outruns the opener),\n  launched with `2026-10-20_f069_fix_leg.bash`, whose sixth argument is the base sha its stamp carries. Its drive,\n  `2026-09-23_f055_f025_allow_arm_demo_drive.py`, samples only the switch button's gate (F-CANOPY-025/-055); extend\n  it to click the enabled switch, Accept, and read `live-switch-progress-alert` (it must close after the swap), and\n  drive the restart confirm likewise: that closes F-CANOPY-069's \"fired, not clicked\".",
    ),
    (
        "MAJOR 4: item 33's recipe",
        "Owner: `pip install -e .` in the env upgrades dash (the lock's 4.4.1 resolves there; `comm` and `janus` come\n    with it), or rebuild from the corrected conda file;",
        "Owner: re-sync the E2 tree to canopy `main` (`fbf01dff` or later; at `571743db` its floor\n    is met by 3.3.0), then `pip install -e <tree>` with the E2 venv's interpreter\n    (`~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1`, a system-site venv over the conda env, holds the\n    editable canopy, pointing at the E2 tree); pip takes the newest dash 4.x (4.4.1 today) with `comm` and `janus`.\n    Or rebuild the conda env from a copy of the corrected `conf/conda_environment.yaml` re-specified for osx-64 as\n    juniper-ml#2282 did (the file is a linux-64 `conda create --file` export with `=pypi_0` lines);",
    ),
    (
        "MAJOR 2: new items",
        "New item:\n\n33. **turing's E2 canopy env is below canopy's floor.**",
        "New items:\n\n33. **turing's E2 canopy env is below canopy's floor.**",
    ),
    (
        "MAJOR 2: item 34",
        "    on dash 3.3.0 of a tree whose floor excludes it.\n",
        "    on dash 3.3.0 of a tree whose floor excludes it.\n\n34. **canopy's Patch Weights sentence for the 1-D targets.** `docs/USER_MANUAL.md:500` at `aeeaf29b` says values are\n    floats separated by commas or spaces; `output_bias`, `hidden_unit_weights` and `hidden_unit_bias` refuse spaces\n    and accept semicolons and newlines (`_parse_float_list`). Either say so (one sentence) or have `_parse_float_list`\n    split on whitespace, as its own docstring claims; a canopy PR with a test, before the release that ships\n    canopy#761. If it ships unfixed, file it (Phase 13's manual rule).\n",
    ),
]

# ============================================================================= the ledger: spans (start ... end, inclusive)
DRIVEN_NEW = """> **Driven** on dash 4.4.1 demo legs from this host with `2026-10-20_item30_fixwave_redrive.py --step f028` (pin
> `learning_rate`, read store and card, reload, pin `max_iterations`, read the store), which gained arms for item 31:
> `delay<N>` waits N seconds after the reload before its pin step, and the forced arms write the params store 150 ms
> after the click (`dash_clientside.set_props`, payload `{}`), requesting a table rebuild on purpose: `forcedearly` at
> the early timing (pass 1, `2026-10-20_item31_f028_drives.bash`; the arm was named `forced` when it ran, so its
> records' labels read `forced#N`) and `forced` at the settled timing (pass 2,
> `2026-10-20_item31_f028_drives_pass2.bash`). Records: `reports/e2e-canopy-2026-09-02/item31-turing/` (JSON, `logs/`).
> **The recorded delay is the driver's pin step, not the click**: `second_pin_at_s_after_reload` is taken before three
> page evaluates, a log line and a screenshot of a page still loading, and the click's writer went out 5.4–8.1 s after
> that log line in the 2 s, 4 s and early forced arms (1.3–3.4 s at the settled timing, nothing pending). **On the
> parent `571743db`**, delays of 2, 4, 6, 8, 10, 12 and 14 s, twice each: 0 of 14 lost
> (`parent_8062_dash441_delay_sweep.json`). Every arm shows the same three writer firings: the mount render, the
> second render 6.6–9.0 s after it, and the click's, 0.6–9.5 s after the second render, both keys checked, State
> `["learning_rate"]`, the store `["max_iterations", "learning_rate"]`. **Every click landed after the second
> render**: that render re-created every box with `max_iterations` unchecked, and a render landing after a click
> resets the box (`early#2`'s third body), yet each click's writer read it checked. So the band before the second
> render, which the Phase 14 entry asked this phase to sample, was not sampled; nothing here shows it unreachable. The
> forced arms lost nothing either: 0 of 6 at the early timing (`parent_8062_dash441_forced.json`) and 0 of 6 at the
> settled one, the pin step 26.6–29.9 s after the reload (`parent_8062_dash441_forced_settled.json`), with no fourth
> writer firing in any of the twelve. They cannot stage `early#2`'s order: the renderer holds the render a store write
> requests behind the click's writer, the pin store being the writer's Output and the render's Input (dash 4.4.1
> `getReadyCallbacks`), whereas `early#2`'s stale render was requested before the click's writer and answered after
> it. A params-store write just before the click, or a click timed to the params-store fill, could stage that order,
> and no drive here tried either. So no instrument reproduced the race on this host: Phase 14's one hit in eight
> stands as the only live loss on the record, and its request bodies, not a re-creation, are what the fix was derived
> from.
> **On the fix** (the item 31 tree, `+f069+f028-fix-unlanded`): the forced arms 0 of 6 at each timing
> (`fix_8066_dash441_forced.json`, `fix_8066_dash441_forced_settled.json`), `early,mid` ×3 0 of 6
> (`fix_8066_dash441_early_mid.json`; the pin step 2.3–2.9 s and 9.4–10.8 s after the reload), the delays 0 of 7
> (`fix_8066_dash441_delay_sweep.json`), the store settling at `["learning_rate", "max_iterations"]` in every arm and
> the same three firings per arm, the rebuilds' now writing nothing by construction. These 25 cannot discriminate:
> the same instrument lost nothing on the parent, so they show that a toggle still persists, not that the race is
> closed; the closure rests on the unit test and on `early#2`'s third body mapping to `no_update`. M-PARAMETERS-04
> and -05 pass on their own expectations in every drive; -06 runs only in the driver's `settled` arm, which no Phase
> 15 drive used. **Not measured:** the natural race at a rate (the one live loss on the record stays Phase 14's); a
> click timed before the second render; the Linux host's dash 4.2.0. **A residual the fix leaves** (from the
> renderer source, not driven; round 2, Lane 15-B): if a stale render lands while the click's writer is in flight,
> dash evicts the older executing call (`dash_renderer.dev.js:3379` in 4.4.1), so the click's write is discarded and
> the rebuild's call writes nothing; the new pin does not register (its box re-renders unchecked, as the user sees)
> and no earlier pin can be lost.
"""

ITEM31_NEW = """What this phase adds to Phase 14's record of the
race is a negative result and its limit: **at the driver's timings every click landed after the second render**
(0 of 14 lost at driver delays of 2–14 s on the parent; the driver clicks seconds after its recorded delay, behind a
screenshot), so the loss band the entry asked for was not sampled, and a synthetic params-store write 150 ms after
the click is held behind the click's writer and cannot stage `early#2`'s order (0 of 6 at the early timing, 0 of 6
at the settled one, no fourth writer firing in any of the twelve). The fix's tree lost nothing in 25 drives (forced
12, early/mid 6, delays 7) with the same three writer firings per arm, the rebuild firings now inert by
construction; those 25 cannot discriminate, since the same instrument lost nothing on the parent. The closure rests
on the unit test and on `early#2`'s third body mapping to `no_update`, not on a live re-creation."""

WHO_NEW = """Every leg served the E2 tree or a copy of it. The E2 tree was proved byte-identical to canopy `main` `571743db`
for the files the item 32 script touches by `util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py` (git blob ids against
the contents API), on 2026-10-20 before that script ran
(`reports/e2e-canopy-2026-09-02/item32-turing/blob_check_e2_tree_vs_571743db_run{1,2}.json`, the second a retry of
the first's three network errors; `requirements.txt` and `requirements_ci.txt` read as mismatches there because they
are git symlinks, whose API sha is the link's own, so their target `conf/requirements_ci.txt` was checked instead,
with `test_poll_gating.py`, in a check the same day that kept no record: re-run against the same unchanged tree and
recorded on 2026-10-21 as `…_run3.json`, with three of the files the item 31 script touches). Item 31's base, the
item 32 tree it was copied from, was proved equal to `fbf01dff` after #760 merged
(`blob_check_f069_tree_vs_fbf01dff.json`), and each script's exact-match anchors were the check when it ran. Legs of
the fix trees were stamped"""

LEDGER_SPANS = [
    ("MAJOR 1 + MINORs 4, 11, 12: F-028's Driven paragraph", "> **Driven** on dash 4.4.1 demo legs from this host", "> params-store refresh timed into the window rather than a synthetic write; the Linux host's dash 4.2.0.\n", DRIVEN_NEW),
    ("MAJOR 1: the item 31 section", "What this phase adds to Phase 14's record of the\nrace is a negative result worth keeping:", "pinned by the unit test rather than by a\nlive re-creation.", ITEM31_NEW),
    ("MINOR 10: the provenance sentence", "Every leg served a tree copied from the E2 tree,", "before the fix scripts ran on the copy, and stamped", WHO_NEW),
]

CONSENSUS_ROUND2 = """- **Round 2** (2026-10-21): Lane 15-B, the adversarial lane round 1 lost, re-run alone on the round-2 freeze
  `f65541a5` with its brief revised in place (`reports/e2e-canopy-2026-09-02/drafts/lane15B_phase15_ledger_brief.md`:
  the handoff added as a review target, its remaining tasks and its verification commands with it). Its report,
  verbatim, is in `reports/e2e-canopy-2026-09-02/consensus/2026-10-21_validator_reports_phase15_round2.md`:
  SOUND-WITH-FIXES, the dispositions and the counts standing, five MAJORs and fifteen MINORs.
  - MAJOR: F-CANOPY-028's account of why the race was not re-created contradicted the records (the driver's clicks
    land after the second render, behind a screenshot; nothing holds the writer); item 31b's new manual sentence is
    wrong for the three 1-D patch targets; the handoff omitted ledger items 18–21, two of the four open P1s among
    them; item 33's recipe would not upgrade dash; item 27's drive never opens the Live Switch modal, so F-CANOPY-069's
    gated click-through had no owner, and the recipe's leg would have stamped `571743db`.
  - MINOR: wordings in F-CANOPY-069's blockquote (the alert's add time; response times read as alert lives; two of
    three new run dependencies; the floor's counter-position); F-CANOPY-028's stale-input example (a four-key analogue,
    not `early#2`'s 22-box body) and its M-PARAMETERS-06 claim (that row runs only in the `settled` arm); the eviction
    residual the fix leaves; the provenance sentence; the round-1 record's wording; statements true only at landing;
    `--expected-head`'s owner; the screenshots; the driver's forced arm, whose timing changed between the passes;
    M-PARAMETERS-04's Expected cell; and an erratum to Phase 14's F-CANOPY-069 text: two callback pairs and three ids,
    not three pairs, and no registration overwritten (`callback_map` is keyed by each callback's whole output
    string; canopy#760's own `test_callback_map_and_served_list_agree` passes on `571743db`).
  - **Corrections** (`util/ad-hoc/2026-10-21_phase15_ledger_round2_corrections.py`; each re-derived by the reconciler
    from the logs, the request bodies, the parser on the item 31 tree, the venv layout or the drive script before it
    was applied): all five MAJORs and fifteen MINORs as proposed, the click gaps recomputed from the logs (5.4–8.1 s
    early, 1.3–3.4 s settled); new item 34; the driver's arms split (`forcedearly`, `forced`) and pass 1's script
    pointed at `forcedearly`; the fix leg's wrapper takes a base sha; canopy#761's drive comment corrected by a
    follow-up comment. MINOR 6's counter-position is recorded with its second half credited to the lane. **Round 2
    changed actions and items** (new item 34; items 18–21 into the handoff; item 33's recipe; item 27's scope), so a
    third round was run.

ROUND3_RECORD_PLACEHOLDER"""

# ============================================================================= the matrix
MATRIX_OLD = "One pattern-matched callback collects every checkbox and writes the pinned key list into `pinned-params-store` (`dashboard_manager.py:3948-3952`), `storage_type=\"local\"` (:1715)."
MATRIX_NEW = "One pattern-matched callback receives every checkbox and persists the one key a user toggled into `pinned-params-store` (`_apply_pin_toggle`, since canopy#761), `storage_type=\"local\"` (:1715)."

# ============================================================================= the pointers
PARENT_SUBS = [
    (
        "parent: items 33 and 34",
        "80/63/1/2/14, 0 open P0, 4 open P1, 10 open P2; new item 33 (turing's E2 canopy env is below the floor).",
        "80/63/1/2/14, 0 open P0, 4 open P1, 10 open P2; new items 33 (turing's E2 canopy env is below the floor) and 34\n   (canopy's Patch Weights sentence for the 1-D targets).",
    ),
]
INDEX_SUBS = [
    (
        "INDEX: two pairs",
        "three `allow_duplicate` callback pairs with identical inputs collide",
        "two `allow_duplicate` callback pairs with identical inputs collide on three output ids",
    ),
    (
        "INDEX: next",
        "Next: items 27 (the Live Switch allow arm, a demo leg on turing can serve it), 25 and 28 (the trio), 29 (the Linux host), 26's second step (O17), 33 (turing's E2 canopy env below the floor; owner).",
        "Next: items 34 (canopy's Patch Weights sentence for the 1-D targets, before the next canopy release), 18–21 (canopy fixes for F-CANOPY-064, -065, -067, -060, -063 and -066), 27 (the Live Switch allow arm extended to click through the modal, a demo leg on turing serving canopy `main`), 25 and 28 (the trio), 29 (the Linux host), 26's second step (O17), 33 (turing's E2 canopy env below the floor; owner).",
    ),
]
BANNER_SUBS = [
    ("banner: items 33 and 34", "handoff's last remaining item; new item 33.\n", "handoff's last remaining item; new items 33 and 34.\n"),
]

# ============================================================================= the handoff
REMAINING_NEW = """**Remaining, in order:**

1. **Land this session's PR** if it has not merged: `python3 util/wait_for_checks.py --pr N`, query
   `reviewThreads(isResolved:false)`, ask the owner, then `python3 util/safe_merge.py --pr N --execute` and read its
   `MERGED` line. Afterwards, and again an hour later (a concurrent whole-file upload can revert a merged change, the
   #2262 trap), on a fresh `origin/main`: `python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7` prints 80 / 63 /
   1 / 2 / 14 with no open P0 line, and `git show origin/main:notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md | grep -c '^## Phase 15'`
   prints 1. A revert costs one replay:
   `python3 -I util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py --out-root <dir>` replays every pass
   (its default list carries them all) and prints the `--add` arguments.
   ROUND3_ITEM_PLACEHOLDER
2. **Item 34** (canopy, before the next canopy release): `docs/USER_MANUAL.md:500` says Patch Weights values are
   "floats separated by commas or spaces"; `output_bias`, `hidden_unit_weights` and `hidden_unit_bias` go through
   `_parse_float_list`, which splits on commas, semicolons and newlines only (`0.1 0.2` is refused). Say so in one
   sentence, or make `_parse_float_list` split on whitespace as its docstring claims; a canopy PR with a test.
3. **Items 18–21** (canopy code; Phase 10's list, re-stated by Phase 13; no handoff carried them before this one):
   18 F-CANOPY-064 (P1) and -067 (first decide -067's rating on unfixed `main` with the recurrence leg up and a canopy
   restart on an idle cascor; never the trio), 19 F-CANOPY-060 and -063 with item 16's fixture sweep, 20 F-CANOPY-065
   (P1 on O17's first limb), 21 F-CANOPY-066 with the selection arc's A1-iii. Canopy PRs, each verified on a leg; the
   ledger's Phase 10 "Still owed" has each item's full text (`grep -n '^18\\. \\*\\*F-CANOPY-064'` finds the first).
4. **Item 27** (F-CANOPY-055/-025's Live Switch allow arm, extended): a demo leg on turing serving canopy `main`
   (`aeeaf29b` or later). The E2 tree is still `571743db`: re-sync it from an up-to-date canopy primary (the owner
   pulls primaries; the worktree guard refuses `git -C`), or use `~/.local/state/juniper/turing-e2/trees/juniper-canopy-f028`
   after proving it equal to `main`:
   `python3 -I util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py --repo pcalnon/juniper-canopy --ref main --root ~/.local/state/juniper/turing-e2/trees/juniper-canopy-f028 src/frontend/dashboard_manager.py pyproject.toml conf/requirements_ci.txt conf/conda_environment.yaml CHANGELOG.md docs/USER_MANUAL.md src/tests/unit/frontend/test_f069_duplicate_callback_outputs.py src/tests/unit/frontend/test_live_dataset_switch_handlers.py src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner1.py src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner2.py src/tests/unit/frontend/test_poll_gating.py src/tests/unit/frontend/test_p2_wave_batch_b.py`
   (the files canopy#760 and #761 touch; `requirements.lock`, the lockfile workflow's, is the one that differs). Launch
   `bash util/ad-hoc/2026-10-20_f069_fix_leg.bash up 8062 ~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python ~/.local/state/juniper/turing-e2/trees/juniper-canopy-f028/src +tree-f028 aeeaf29b4f2921bae8c26b61926ca16456ff9b4c`
   (the sixth argument is the base sha the stamp carries; the guard refuses a `CANOPY_LEG_SRC=` prefix). Then
   `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py`, adapted to the chrome channel and the CDN route,
   samples the switch button's gate with the flag on and a demo run live (record it in F-CANOPY-025's and -055's
   entries). It does not open the modal: extend it to click the enabled switch, Accept, and read
   `live-switch-progress-alert` (on `main` it must close after the swap), and drive the restart confirm likewise.
   That closes F-CANOPY-069's "fired, not clicked".
5. **Items 25 and 28** on the Linux host, against the trio (ledger Phase 12). **Item 29**, the Linux host.
6. **Item 33** (owner): bring turing's E2 canopy env to canopy's floor. Re-sync the E2 tree to canopy `main`
   (`fbf01dff` or later; at `571743db` the floor `dash>=3.0.0` is met by 3.3.0), then
   `~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python -m pip install -e ~/.local/state/juniper/turing-e2/trees/juniper-canopy`
   (that venv, a system-site venv over the conda env, holds the editable canopy; pip takes the newest dash 4.x with
   `comm` and `janus`). Or rebuild the conda env from a copy of the corrected `conf/conda_environment.yaml`
   re-specified for osx-64 as juniper-ml#2282 did (the file is a linux-64 `conda create --file` export). Then re-run
   the lanes the E2 record cites and record an erratum in the bring-up plan's E2 section; the dash 3.x scratch venvs
   (`JuniperCanopy1-dash304/-dash32/-dash34`) can go.
7. **Item 26's second step** once the owner rules (O17).
8. **The canopy release** that ships canopy#760 and #761, after item 34 (owner-gated, P4). Until it is cut, PyPI's
   canopy 0.9.0 (the newest release, 2026-10-17) keeps the colliding pairs, the Live Switch spinner that can stick
   under dash 4, the pin loss and the `dash>=3.0.0` floor. Check with `gh release list --repo pcalnon/juniper-canopy --limit 2`.
9. **Cleanup on turing**, after the PR merges: the worktree `sequential-coalescing-boot` holds three local unsigned
   freeze commits (round 1 `6f933d07`, round 2 `f65541a5`, round 3 ROUND3_FREEZE_PLACEHOLDER): never push its branch;
   remove the worktree through `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md` (owner, or a
   later session). Its untracked `reports/e2e-canopy-2026-09-02/item31-turing/shots/` (the last arm's three
   screenshots; each arm overwrote them) goes with it unless copied out. The fix trees
   `~/.local/state/juniper/turing-e2/trees/juniper-canopy-f069` and `-f028` can go once item 27 has its own tree.
   canopy deleted both fix branches on merge.
10. Then the parent's items 5 and 7, and the owner batch O1–O17 (ledger item 22, O9's design question, is the
    parent's C4).
"""

CHANGED_NEW = """## Changed by this session

- **Created:**
  - this file;
  - `util/ad-hoc/2026-10-20_f069_pair_members_probe.py`, `util/ad-hoc/2026-10-20_f069_apply_fix.py`,
    `util/ad-hoc/2026-10-20_f069_fix_leg.bash`, `util/ad-hoc/2026-10-20_f028_apply_fix.py`,
    `util/ad-hoc/2026-10-20_item31_f028_drives.bash`, `util/ad-hoc/2026-10-20_item31_f028_drives_pass2.bash`,
    `util/ad-hoc/2026-10-20_phase15_items31_32_apply.py`,
    `util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py`,
    `util/ad-hoc/2026-10-21_phase15_ledger_round1_corrections.py`,
    `util/ad-hoc/2026-10-21_phase15_ledger_round2_corrections.py`,
    `util/ad-hoc/2026-10-21_phase15_ledger_round3_corrections.py`;
  - `reports/e2e-canopy-2026-09-02/item32-turing/` (`pair_members.json`, `dash_version_matrix_fix.json`, four
    `blob_check_*.json`, `lane15A_pair_members.json`, `lane15A_dash_matrix.json`);
  - `reports/e2e-canopy-2026-09-02/item31-turing/` (seven driver records, two `lane15A_*.json`, and their `logs/`; the
    screenshots under `shots/` are LFS PNGs, untracked, and stay on turing);
  - `reports/e2e-canopy-2026-09-02/drafts/lane15{A,B,C}_phase15_ledger_brief.md` (15-B's revised in place for its
    round-2 run) and `lane15R3_phase15_ledger_brief.md`;
  - `reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase15_round1.md`,
    `2026-10-21_validator_reports_phase15_round2.md` and `2026-10-21_validator_reports_phase15_round3.md`.
- **Modified:**
  - `util/ad-hoc/2026-10-20_item30_fixwave_redrive.py`: the `delay<N>`, `forced` and `forcedearly` f028 arms,
    `--f028-forced-gap-ms`, the `LOST_B` verdict;
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: Phase 15; the headers of F-CANOPY-069 and
    F-CANOPY-028 and a dated blockquote under each; an erratum to Phase 14's F-CANOPY-069 text (two callback pairs,
    three ids; no registration overwritten);
  - `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`: M-PARAMETERS-06's status cell and
    M-PARAMETERS-04's Expected cell;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`: the Lane A pointer;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: the P2 row;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`:
    the SUPERSEDED banner.
- **In juniper-canopy** (canopy#760, #761): `src/frontend/dashboard_manager.py`, `pyproject.toml`,
  `conf/requirements_ci.txt`, `conf/conda_environment.yaml`, `CHANGELOG.md`, `docs/USER_MANUAL.md`,
  `src/tests/unit/frontend/test_f069_duplicate_callback_outputs.py` (new), `test_live_dataset_switch_handlers.py`,
  `test_dashboard_manager_gate_coverage_inner1.py`, `test_dashboard_manager_gate_coverage_inner2.py`,
  `test_poll_gating.py`, `test_p2_wave_batch_b.py`; `requirements.lock` by the lockfile workflow. Comments on
  canopy#760 (the unit-lane count) and #761 (the drives, then a correction of their account).
- **Outside the repo**, in auto-memory: `MEMORY.md` (the canopy line), `canopy-e2e-arc-state.md`.
"""

HANDOFF_SUBS = [
    (
        "title: next",
        "Next are item 27, the Linux host's items 25, 28 and 29, item 26's second step and the owner's item 33",
        "Next are item 34 and items 18–21 (canopy fixes), item 27, the Linux host's items 25, 28 and 29, item 26's second step and the owner's item 33",
    ),
    (
        "consensus line: round 2",
        "Round 1 changed one action's parameter (item 27's leg must serve canopy `main`).\nROUND2_SUMMARY_PLACEHOLDER (ledger Phase 15, Consensus record).",
        "Round 1 changed one action's parameter (item 27's leg must serve canopy `main`).\nRound 2 on 2026-10-21, Lane 15-B re-run alone on the corrected freeze: SOUND-WITH-FIXES, five MAJORs (F-CANOPY-028's\naccount of why its race was not re-created, item 31b's new manual sentence, items 18–21 missing from this list,\nitem 33's recipe, item 27's scope) and fifteen MINORs, all applied; it changed actions and items.\nROUND3_SUMMARY_PLACEHOLDER (ledger Phase 15, Consensus record).",
    ),
    (
        "goal statement",
        "Item 27 is a demo leg on turing serving\ncanopy `main` (not the E2 tree, which is still `571743db`) and the Live Switch modal's allow arm; items 25, 28 and 29\nneed the Linux host and the trio; item 33 is the owner's (turing's E2 canopy env is below canopy's floor); item 26's\nsecond step waits on the owner's O17 ruling; the canopy release that ships both fixes is owner-gated.",
        "Item 34 is a one-sentence canopy manual fix due\nbefore the next canopy release, and items 18–21 are canopy fixes (F-CANOPY-064, -065, -067, -060, -063, -066); item\n27 is a demo leg on turing serving canopy `main` (not the E2 tree, which is still `571743db`), the Live Switch\nbutton's allow arm extended to click through the modal; items 25, 28 and 29 need the Linux host and the trio; item 33\nis the owner's (turing's E2 canopy env is below canopy's floor); item 26's second step waits on the owner's O17\nruling; the canopy release that ships the fixes is owner-gated.",
    ),
    (
        "completed: #761's drives",
        "Drives (`reports/e2e-canopy-2026-09-02/item31-turing/`): the parent lost no pin in 26 (14 at\n  fixed delays of 2–14 s; 12 on the `forced` arm, a params-store write 150 ms after the click, meant to stage\n  early#2's order, which it did not); the fix lost none in 25 (forced 12, early/mid 6, fixed delays 7); Lane 15-A's\n  9 agree (6 on the fix, 3 forced on the parent). The race itself was not re-created live; the one live loss on the\n  record stays Phase 14's `early#2`, whose request bodies the fix was derived from.",
        "Drives (`reports/e2e-canopy-2026-09-02/item31-turing/`): the parent lost no pin in 26 (14 at\n  driver delays of 2–14 s, every click landing after the second render; 12 on the forced arms, a params-store write\n  150 ms after the click, which the renderer holds behind the click's writer, so it cannot stage early#2's order);\n  the fix lost none in 25 (forced 12, early/mid 6, delays 7), which cannot discriminate; Lane 15-A's 9 agree. The\n  race itself was not re-created live; the one live loss on the record stays Phase 14's `early#2`, whose request\n  bodies the fix was derived from and which the unit test pins. Item 31b's new sentence is wrong for the three 1-D\n  targets (item 34).",
    ),
    (
        "completed: new items",
        "10 P2; new item 33.\n",
        "10 P2; new items 33 and 34; an erratum to\n  Phase 14's F-CANOPY-069 text (two callback pairs, three ids; no registration overwritten).\n",
    ),
    (
        "trap: the driver's click",
        "- **The renderer holds a click's writer behind a pending table render**, so a pin at a fixed delay after the reload\n  never hits F-CANOPY-028's window, and a synthetic params-store write after the click (the driver's `forced` arm)\n  produces no writer firing at all: neither instrument re-creates early#2's order, which came from the params-store\n  refresh landing inside the click's write latency. Give every driver run its own `--out`.",
        "- **The driver's click lands seconds after its recorded pin delay**: `second_pin_at_s_after_reload` is taken before\n  three page evaluates, a log line and a screenshot of a page still loading, so at every delay given the click came\n  after the second table render (each click's writer read the new pin checked after the rebuild had re-created it\n  unchecked). A params-store write after the click (the forced arms) is held behind the click's writer by the\n  renderer (the pin store is the render's Input), so it cannot stage early#2's order, which needs the rebuild\n  requested before the click's writer. Give every driver run its own `--out`.",
    ),
    (
        "trap: --expected-head",
        "Pin `--expected-head` on the PR's current head\n  (`gh pr view N --json headRefOid`), not on your last push; `safe_merge.py` merges the head CI passed on.",
        "Pin `util/push_signed_commit.py`'s\n  `--expected-head` on the PR's current head (`gh pr view N --json headRefOid`), not on your last push;\n  `safe_merge.py` (which has no such flag) merges the head CI passed on.",
    ),
    (
        "git state: freeze commits",
        "plus the two local unsigned freeze commits the\n  consensus rounds reviewed; they never leave the host.",
        "plus the three local unsigned freeze commits the\n  consensus rounds reviewed (`6f933d07`, `f65541a5`, ROUND3_FREEZE_PLACEHOLDER); they never leave the host.",
    ),
]
HANDOFF_SPANS = [
    ("MAJORs 3-5, MINORs 8, 13: the Remaining list", "**Remaining, in order:**\n", "9. Then the parent's items 5 and 7, and the owner batch O1–O17.\n", REMAINING_NEW),
    ("MAJOR 2 et al.: the Changed list", "## Changed by this session\n", "- **Outside the repo**, in auto-memory: `MEMORY.md`, `canopy-e2e-arc-state.md`.\n", CHANGED_NEW),
]


# ============================================================================= mechanics
def replace_once(text: str, old: str, new: str, what: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"anchor for {what} occurs {n} times, expected 1: {old[:90]!r}")
    return text.replace(old, new, 1)


def replace_span(text: str, start: str, end: str, new: str, what: str) -> str:
    if text.count(start) != 1:
        raise SystemExit(f"start anchor for {what} occurs {text.count(start)} times: {start[:80]!r}")
    i = text.index(start)
    j = text.find(end, i)
    if j < 0 or text.count(end) != 1:
        raise SystemExit(f"end anchor for {what} occurs {text.count(end)} times or precedes the start: {end[:80]!r}")
    return text[:i] + new + text[j + len(end) :]


def check_headers(ledger: str) -> None:
    for fid, want in (("F-CANOPY-069", "P0"), ("F-CANOPY-028", "P1")):
        m = re.search(r"^\*\*(" + fid + r") — (.*?)\*\*", ledger, re.M | re.S)
        assert m, f"{fid} header not found"
        body = " ".join(m.group(2).split())
        assert _PRI_RE.search(body).group(1) == want, (fid, body[:80])
        assert re.search(r"\bFIXED\b", body[-170:]), (fid, body[-170:])


def apply(root: Path, check_only: bool) -> None:
    ledger_p = root / LEDGER
    ledger = ledger_p.read_text(encoding="utf-8")
    assert "ROUND2_RECORD_PLACEHOLDER" in ledger, "round 2 is already applied (or round 1 is missing)"
    for what, old, new in LEDGER_SUBS:
        ledger = replace_once(ledger, old, new, what)
    for what, start, end, new in LEDGER_SPANS:
        ledger = replace_span(ledger, start, end, new, what)
    ledger = replace_once(ledger, "ROUND2_RECORD_PLACEHOLDER", CONSENSUS_ROUND2, "round-2 record placeholder")
    check_headers(ledger)

    matrix_p = root / MATRIX
    matrix = replace_once(matrix_p.read_text(encoding="utf-8"), MATRIX_OLD, MATRIX_NEW, "M-PARAMETERS-04 Expected cell")

    parent_p, index_p, prev_p, handoff_p = root / HANDOFF_PARENT, root / INDEX, root / HANDOFF_PREV, root / HANDOFF
    parent = parent_p.read_text(encoding="utf-8")
    for what, old, new in PARENT_SUBS:
        parent = replace_once(parent, old, new, what)
    index = index_p.read_text(encoding="utf-8")
    for what, old, new in INDEX_SUBS:
        index = replace_once(index, old, new, what)
    prev = prev_p.read_text(encoding="utf-8")
    for what, old, new in BANNER_SUBS:
        prev = replace_once(prev, old, new, what)
    handoff = handoff_p.read_text(encoding="utf-8")
    for what, old, new in HANDOFF_SUBS:
        handoff = replace_once(handoff, old, new, what)
    for what, start, end, new in HANDOFF_SPANS:
        handoff = replace_span(handoff, start, end, new, what)
    for token in ("ROUND3_SUMMARY_PLACEHOLDER", "ROUND3_ITEM_PLACEHOLDER", "ROUND3_FREEZE_PLACEHOLDER"):
        assert token in handoff, f"{token} missing from the handoff"
    assert "ROUND2_" not in handoff, "a round-2 placeholder survived in the handoff"

    if check_only:
        print("check OK: every anchor is unique; F-CANOPY-069 and -028 still triage P0/P1 FIXED")
        return
    ledger_p.write_text(ledger, encoding="utf-8")
    matrix_p.write_text(matrix, encoding="utf-8")
    parent_p.write_text(parent, encoding="utf-8")
    index_p.write_text(index, encoding="utf-8")
    prev_p.write_text(prev, encoding="utf-8")
    handoff_p.write_text(handoff, encoding="utf-8")
    print("applied:", LEDGER, MATRIX, HANDOFF_PARENT, INDEX, HANDOFF_PREV, HANDOFF, sep="\n  ")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    apply(Path(args.root).resolve(), args.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())
