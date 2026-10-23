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
#               util/ad-hoc/2026-10-20_phase15_items31_32_apply.py (the pass this corrects);
#               reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase15_round1.md (the reports)
# ---------------------------------------------------------------------------
"""Round 1's correction pass on the ledger's Phase 15 and the files that land with it.

Applied to the files as frozen for round 1 (local commit ``6f933d07``), i.e. after
``2026-10-20_phase15_items31_32_apply.py``. Every substitution is anchored to occur exactly once in its file. The
reconciler re-derived each from the record, the commit or the source before applying it:

* [A, step 2] the inverted response order is REAL: Lane 15-A's two runs on a dash 4.4.1 leg of ``571743db`` had the
  Live Switch worker answer 1 ms before the opener and the progress alert left open
  (``item32-turing/lane15A_pair_members.json``). Recorded in F-CANOPY-069's FIXED blockquote; struck from its "not
  measured" and from "What this phase cannot support".
* [C] the lockfile re-resolve changed ``websockets``, not ``uvloop`` (commit ``a8b519c1``'s patch).
* [C] the settled forced arm's click-writer gap is 18.3–23.6 s over the twelve drives (18.4 was the parent's six).
* [C] F-CANOPY-028's header: "the forced arm included" (no race was produced), not "the forced race included".
* [C] the blob-check provenance claim now cites its records (landed; the third run re-done 2026-10-21).
* [action] item 27's leg must serve canopy ``main``: the E2 tree is still ``571743db``, which predates both fixes.
* [C, MAJOR] the handoff's Changed list lacked ``2026-10-20_item31_f028_drives_pass2.bash``; [C] its Completed
  bullet kept the hypothesis the phase refuted; [C] the SUPERSEDED banner mapped items 4–7 wrongly; [C] the
  venvs comment; [C] forward-looking statements. The handoff is rewritten whole, renamed to its writing date
  (``HANDOFF_2026-10-21_…``), and the pointers to it in the banner, the parent and the INDEX follow the rename.
* The round-1 consensus record replaces the placeholder; round 2 (Lane 15-B, re-run) leaves placeholders that
  ``2026-10-21_phase15_ledger_round2_corrections.py`` fills.

Usage:
    python3 -I util/ad-hoc/2026-10-21_phase15_ledger_round1_corrections.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts"
HANDOFF_OLD = f"{HANDOFF_DIR}/HANDOFF_2026-10-20_canopy-phase15-items-31-32-done-f069-f028-fixed.md"
HANDOFF_NEW = f"{HANDOFF_DIR}/HANDOFF_2026-10-21_canopy-phase15-items-31-32-done-f069-f028-fixed.md"
NAME_OLD = HANDOFF_OLD.rsplit("/", 1)[1]
NAME_NEW = HANDOFF_NEW.rsplit("/", 1)[1]
HANDOFF_PREV = f"{HANDOFF_DIR}/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md"
HANDOFF_PARENT = f"{HANDOFF_DIR}/HANDOFF_2026-10-03_canopy-consolidated.md"
INDEX = f"{HANDOFF_DIR}/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md"

_PRI_RE = re.compile(r"\b(P0/P1|P0|P1|P2|CRITICAL|LEDGER)\b")

# ----------------------------------------------------------------------------- the ledger
LEDGER_SUBS = [
    (
        "F-069: the inversion, observed by Lane 15-A",
        """> The spinner's fate was the order of the two responses: the opener answered first in both pairs, so its `True`
> landed before the worker's `False`; had the worker answered first (a fast refusal), the opener's `True` would
> have landed last and the spinner stuck open. That inversion was not driven.
""",
        """> The spinner's fate was the order of the two responses: on this run the opener answered first in both pairs, so
> its `True` landed before the worker's `False`. **The other order happens, and then the spinner sticks.** Round 1's
> Lane 15-A, re-creating the read on its own dash 4.4.1 leg of `571743db` (two runs; its record landed as
> `reports/e2e-canopy-2026-09-02/item32-turing/lane15A_pair_members.json`, labels `lane15A-dash-4.4.1-parent` and
> `lane15A-dash-4.4.1-parent-run2`), saw the Live Switch worker answer 1 ms BEFORE the opener both times (+0.155 s
> against +0.156 s, and +0.286 s against +0.287 s: the demo backend answers the swap in about 40 ms), and the
> progress alert was still open when each probe ended, `Swapping dataset…` with its Cancel button, class `show`.
> Nothing else closes it: the alert is not dismissable, and its only writers were the two members of the pair, so
> it stays up until a later accept or a reload. The restart worker (1.25 s and 1.31 s on Lane 15-A's runs, 2.61 s
> on this one) never outran its opener. So under dash 4 the defect was live on one surface: whenever the swap POST
> came back before the opener's, the Live Switch spinner outlived the swap. That is the dash 4 behaviour Phase 14
> left unmeasured.
""",
    ),
    (
        "F-069: the lock re-resolve's packages",
        "> setuptools, starlette, uvloop), a signed commit of its own.\n",
        "> setuptools, starlette, websockets), a signed commit of its own.\n",
    ),
    (
        "F-069: not measured",
        """**Not measured:** the
> inverted response order under dash 4; the two surfaces clicked through their gated modals (the probe fires the
> Input directly);""",
        """**Not measured:** the
> two surfaces clicked through their gated modals (the probe fires the Input directly);""",
    ),
    (
        "cannot support: the inversion",
        "- **The inverted response order under dash 4 was not driven**, and dash 4.2.0 (the Linux host's) was not run.\n",
        """- **dash 4.2.0 (the Linux host's) was not run.** The inverted response order under dash 4 was observed by round
  1's Lane 15-A on its own leg, not by this phase's run (F-CANOPY-069's FIXED blockquote cites its record).
""",
    ),
    (
        "F-028: the settled gap range",
        "> writer went out 18.4–23.6 s after the second render,",
        "> writer went out 18.3–23.6 s after the second render,",
    ),
    (
        "F-028 header: arm, not race",
        "re-driven on a leg of the fix, the forced race included, Phase 15, item 31; FIXED; segment 15).**",
        "re-driven on a leg of the fix, the forced arm included, Phase 15, item 31; FIXED; segment 15).**",
    ),
    (
        "Who: the blob-check records",
        """proved byte-identical to canopy `main` `571743db` for every
file the fixes touch by `util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py` (git blob ids against the contents
API) before the fix scripts ran on the copy,""",
        """proved byte-identical to canopy `main` `571743db` for every
file the fixes touch by `util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py` (git blob ids against the contents
API; `reports/e2e-canopy-2026-09-02/item32-turing/blob_check_e2_tree_vs_571743db_run{1,2,3}.json`, the second a
retry of the first's three network errors and the third re-run on 2026-10-21 against the same unchanged tree, and
`blob_check_f069_tree_vs_fbf01dff.json` for item 31's base; `requirements.txt` and `requirements_ci.txt` read as
mismatches there because they are git symlinks, whose API sha is the link's own, so their target
`conf/requirements_ci.txt` was checked instead) before the fix scripts ran on the copy,""",
    ),
    (
        "Still owed: item 27's leg",
        """**Item 27** is unchanged; a demo leg on this host
  serves it (`2026-10-20_turing_canopy_leg.bash up <port> demo` on the dash 4.4.1 venv, or any venv at the floor
  now).""",
        """**Item 27** is unchanged; a demo leg on this host
  serves it (`2026-10-20_turing_canopy_leg.bash up <port> demo` on the dash 4.4.1 venv, or any venv at the floor
  now), from a tree proved equal to canopy `main` (`aeeaf29b` or later): the E2 tree is still `571743db`, which
  predates both fixes, and on it the Live Switch spinner sticks open whenever the swap POST outruns the opener.""",
    ),
]

CONSENSUS_ROUND1 = """- **Round 1** (2026-10-20): three lanes on the frozen local commit `6f933d07`, briefed separately with different
  entry points (`reports/e2e-canopy-2026-09-02/drafts/lane15{A,B,C}_phase15_ledger_brief.md`). The reports, verbatim,
  are in `reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase15_round1.md`. An API
  usage-credit error stopped two of the three lanes mid-run.
  - **Lane 15-C** (replay, consistency, conventions) finished: SOUND-WITH-FIXES. The apply pass replayed from
    `origin/main` byte-identical for all six files; every count, and every item 31 and item 32 figure, matched its
    record. One MAJOR (a created script missing from the handoff's Changed list) and nine MINORs (a wrong package
    in the lock re-resolve; a range stated for twelve drives from six; the canopy apply script's `--check` false on
    a later `main`; an unrecorded provenance claim; wordings in F-CANOPY-028's header, the handoff's Completed list
    and the SUPERSEDED banner; statements true only at landing; a verification comment).
  - **Lane 15-A** (measurement re-creation) ran all five steps; the error cut it off before its report. Its interim
    status (steps 1, 2 and 5) and its own checkpoint notes are archived; the reconciler read its step 3 and 4
    records, landed as `reports/e2e-canopy-2026-09-02/item31-turing/lane15A_*.json`. Step 1: the fix ALIVE under
    dash 3.3.0 and 4.4.1, 179 callbacks, 0 colliding ids, two `running` entries, one POST per firing. Step 2: on the
    parent under dash 4.4.1 both members of each pair ran, as the phase says, and **the Live Switch pair's order
    inverted in both of its runs, the spinner left open**, the case the phase had predicted and not driven. Step 3:
    6 of 6 on the fix survive (early, mid and forced, twice each). Step 4: 3 of 3 on the parent's forced arm survive.
    Step 5: the old handler drops the pin on the stale input; the new one writes nothing. Every figure agreed within
    run-to-run timing.
  - **Lane 15-B** (adversarial analysis) wrote nothing before the error; it is re-run as round 2.
  - **Corrections** (`util/ad-hoc/2026-10-21_phase15_ledger_round1_corrections.py`; each re-derived from the record,
    the commit or the source before it was applied): the inversion recorded in F-CANOPY-069's FIXED blockquote and
    struck from "not measured" and "cannot support"; `websockets`, not `uvloop`; 18.3–23.6 s over the twelve drives;
    "the forced arm included", not "race", in F-CANOPY-028's header; the blob-check records landed and cited; item
    27's leg must serve canopy `main`, not the E2 tree; the canopy apply script's `--check` recognises its CHANGELOG
    block when a later change lands inside it (`util/ad-hoc/2026-10-20_f069_apply_fix.py`, verified `done` on every
    step against `fbf01dff` and `aeeaf29b`, and a fresh apply still reproduces the landed tree); the handoff renamed
    to its writing date and brought to the state at landing, the missing script listed and the banner's item mapping
    corrected. **Round 1 changed one action's parameter** (item 27's tree), so the review continued.

ROUND2_RECORD_PLACEHOLDER"""

# ----------------------------------------------------------------------------- the banner, the parent, the INDEX
BANNER_OLD = """> **SUPERSEDED 2026-10-20** by `HANDOFF_2026-10-20_canopy-phase15-items-31-32-done-f069-f028-fixed.md`.
> Its item 1 (juniper-ml#2291 merged 2026-10-20T13:59:34Z), item 2 (item 32: canopy#760, F-CANOPY-069 FIXED, the dash
> floor 4.0.0) and item 3 (item 31: canopy#761, F-CANOPY-028 FIXED, the manual's row idiom) are done, recorded as
> Phase 15 of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`; items 4 to 7 carry there as
> items 27, 25, 28, 29 and 26's second step, with new item 33.
"""
BANNER_NEW = """> **SUPERSEDED 2026-10-21** by `HANDOFF_2026-10-21_canopy-phase15-items-31-32-done-f069-f028-fixed.md`.
> Its item 1 (juniper-ml#2291 merged 2026-10-20T13:59:34Z), item 2 (item 32: canopy#760, F-CANOPY-069 FIXED, the dash
> floor 4.0.0) and item 3 (item 31: canopy#761, F-CANOPY-028 FIXED, the manual's row idiom) are done, recorded as
> Phase 15 of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`; its items 4 to 6 carry there as
> items 27, 25, 28, 29 and 26's second step, and its item 7 (the parent's items 5 and 7, the owner batch) as that
> handoff's last remaining item; new item 33.
"""

# ----------------------------------------------------------------------------- the handoff, whole
HANDOFF_TEXT = """# HANDOFF 2026-10-21 — P2 canopy Lane A: Phase 15 recorded. Items 32 and 31 are DONE: F-CANOPY-069 is FIXED (canopy#760; the dash floor is 4.0.0) and F-CANOPY-028 is FIXED (canopy#761). 0 open P0, 4 open P1, 10 open P2. Next are item 27, the Linux host's items 25, 28 and 29, item 26's second step and the owner's item 33

**Written**: 2026-10-21 by the session in juniper-ml worktree `.claude/worktrees/sequential-coalescing-boot` on host
turing (macOS; no trio; throwaway legs from copies of the E2 tree), at a phase boundary, as its PR was opened. The
work ran on 2026-10-20; the consensus and the landing on 2026-10-21.
**Consensus**: round 1 on 2026-10-20, three lanes on the frozen draft. Lane 15-C finished SOUND-WITH-FIXES. An API
usage-credit error cut off Lane 15-A after it had run all five steps (its records were read and landed) and Lane
15-B before it wrote anything. Round 1 changed one action's parameter (item 27's leg must serve canopy `main`).
ROUND2_SUMMARY_PLACEHOLDER (ledger Phase 15, Consensus record).
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`, authoritative for P2.
Its items 5 and 7 and the owner batch O1–O17 carry over. This file supersedes
`HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`.
**Merge approval**: the owner granted it for this session: its two canopy PRs and this PR ("save, merge, and PR
handoff", 2026-10-21). It is NOT carried: ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A (the juniper-canopy E2E validation arc) from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_canopy-phase15-items-31-32-done-f069-f028-fixed.md`
(juniper-ml). Read it in full, then the parent `HANDOFF_2026-10-03_canopy-consolidated.md`. Run the verification
commands first. Merge approval is not carried: ask before the first merge. Item 27 is a demo leg on turing serving
canopy `main` (not the E2 tree, which is still `571743db`) and the Live Switch modal's allow arm; items 25, 28 and 29
need the Linux host and the trio; item 33 is the owner's (turing's E2 canopy env is below canopy's floor); item 26's
second step waits on the owner's O17 ruling; the canopy release that ships both fixes is owner-gated.

**Completed:**

- **juniper-ml#2291 merged** 2026-10-20T13:59:34Z: Phase 14 of
  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` and
  `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`.
- **canopy#760 merged** 2026-10-20T18:58:37Z as `fbf01dff` (item 32, F-CANOPY-069). Measured first on a dash 4.4.1
  leg of `571743db`: both members of each colliding pair run on one firing, and the spinner's fate is the order of
  their responses; round 1's Lane 15-A caught the bad order twice on the Live Switch pair, the spinner left open
  (`reports/e2e-canopy-2026-09-02/item32-turing/pair_members.json`, `lane15A_pair_members.json`). The fix:
  `accept_live_switch` and `execute_restart` carry their progress alerts (and the live-swap in-flight store) as
  `running=`; the two opener callbacks and `_open_progress_alert_on_accept_handler` are gone;
  `test_f069_duplicate_callback_outputs.py` pins "no output id is claimed by two callbacks" (7 of 9 fail on
  `571743db`); the floor is `dash>=4.0.0` (`pyproject.toml`, `conf/requirements_ci.txt`) and
  `conf/conda_environment.yaml` pins dash 4.4.1 with `comm` and `janus`. Legs of the fix: ALIVE under dash 3.3.0 and
  4.4.1, one POST per firing, the alert opening on the request and closing on the response
  (`dash_version_matrix_fix.json`, `pair_members.json`). CI's unit-lane selector on turing: 7954 passed, 10
  skipped, 2 failed, the two being E-REQ (turing's `requests` 2.32.5), red on `571743db` too.
- **canopy#761 merged** 2026-10-20T19:34:02Z as `aeeaf29b` (item 31, F-CANOPY-028). The pin-store writer persists a
  user's toggle only (exactly one pin input triggered, read through `CallbackContextAdapter.get_triggered_prop_ids`);
  a rebuilt table (every input triggered at once) writes nothing; `_merge_pinned_params` became `_apply_pin_toggle`;
  `TestF028PinnedParamsPreserved` carries the stale-rebuild case; the manual's Patch Weights sentence states the row
  idiom (item 31b). Drives (`reports/e2e-canopy-2026-09-02/item31-turing/`): the parent lost no pin in 26 (14 at
  fixed delays of 2–14 s; 12 on the `forced` arm, a params-store write 150 ms after the click, meant to stage
  early#2's order, which it did not); the fix lost none in 25 (forced 12, early/mid 6, fixed delays 7); Lane 15-A's
  9 agree (6 on the fix, 3 forced on the parent). The race itself was not re-created live; the one live loss on the
  record stays Phase 14's `early#2`, whose request bodies the fix was derived from.
- **The ledger's Phase 15** (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) records both, the
  F-CANOPY-069 and F-CANOPY-028 headers FIXED with a dated blockquote under each; counts 80 findings, 63 fixed, 1
  accepted, 2 withdrawn, 14 open: 0 P0, 4 P1 (F-CANOPY-064, -065, F-CASCOR-001, -002), 10 P2; new item 33.
- **This session's PR** carries the ledger, the matrix (M-PARAMETERS-06's cell), this file, the SUPERSEDED banner on
  `HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`, the pointer in
  `HANDOFF_2026-10-03_canopy-consolidated.md`, the P2 row of `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`,
  the records under `reports/e2e-canopy-2026-09-02/item32-turing/` and `item31-turing/` (JSON and `logs/`; the
  screenshots stay on turing), the briefs and the consensus reports, and the scripts listed under "Changed by this
  session". Find it with `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase15 --state all`.

**Remaining, in order:**

1. **Land this session's PR** if it has not merged: `python3 util/wait_for_checks.py --pr N`, query
   `reviewThreads(isResolved:false)`, ask the owner, then `python3 util/safe_merge.py --pr N --execute` and read its
   `MERGED` line. Afterwards, and again an hour later (a concurrent whole-file upload can revert a merged change, the
   #2262 trap), on a fresh `origin/main`: `python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7` prints 80 / 63 /
   1 / 2 / 14 with no open P0 line, and `git show origin/main:notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md | grep -c '^## Phase 15'`
   prints 1. A revert costs one replay: `util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py`.
ROUND3_ITEM_PLACEHOLDER
3. **Item 27** (the Live Switch allow arm, F-CANOPY-055/-025): a demo leg on turing serving canopy `main`
   (`aeeaf29b` or later). The E2 tree is still `571743db`; re-sync it from an up-to-date canopy primary (the owner
   pulls primaries; the worktree guard refuses `git -C`), or use `~/.local/state/juniper/turing-e2/trees/juniper-canopy-f028`
   after proving it equal to `main` with `util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py --ref main` (it differs
   only in `requirements.lock`). Then
   `bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash up 8062 demo http://127.0.0.1:9 ~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python`
   (with `CANOPY_LEG_SRC` pointing at that tree's `src`, or `util/ad-hoc/2026-10-20_f069_fix_leg.bash`, which sets
   it) and `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py` adapted to the chrome channel and the CDN route.
   It clicks through the Live Switch modal, which Phase 15's probe only fired; on `main` the spinner must close
   after the swap.
4. **Items 25 and 28** on the Linux host, against the trio (ledger Phase 12). **Item 29**, the Linux host.
5. **Item 33** (owner): bring turing's `JuniperCanopy1` env to canopy's floor (`pip install -e .` there resolves
   dash 4.4.1, `comm` and `janus`; or rebuild from the corrected `conf/conda_environment.yaml`), re-run the lanes the
   E2 record cites, and record an erratum in the bring-up plan's E2 section; the dash 3.x scratch venvs
   (`JuniperCanopy1-dash304/-dash32/-dash34`) can go then.
6. **Item 26's second step** once the owner rules (O17).
7. **The canopy release** that ships canopy#760 and #761 (owner-gated, P4). Until it is cut, PyPI's canopy 0.9.0 (the
   newest release, 2026-10-17) keeps the colliding pairs, the Live Switch spinner that can stick under dash 4, the
   pin loss and the `dash>=3.0.0` floor. Check with `gh release list --repo pcalnon/juniper-canopy --limit 2`.
8. **Cleanup on turing**, after the PR merges: the worktree `sequential-coalescing-boot` holds two local unsigned
   freeze commits (round 1 `6f933d07`, round 2 ROUND2_FREEZE_PLACEHOLDER): never push its branch; remove the
   worktree through `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md` (owner, or a later session).
   The fix trees `~/.local/state/juniper/turing-e2/trees/juniper-canopy-f069` and `-f028` can go once item 27 has its
   own tree. canopy deleted both fix branches on merge.
9. Then the parent's items 5 and 7, and the owner batch O1–O17.

**Traps learned:**

- **turing has no signing**: land through `util/open_signed_pr.py` and `util/push_signed_commit.py` (one large file
  per commit). Build every shared file from a fresh `origin/main` copy:
  `util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py` replays the apply and round passes and
  byte-checks the result against the worktree.
- **`requirements.txt`, `requirements_ci.txt` and `conf/requirements.txt` are git symlinks** resolving to
  `conf/requirements_ci.txt`; root `conda_environment.yaml` is one into `conf/`. The contents API reports a symlink as
  a `file` whose `sha` is the link's own blob (sha1 of the target path) while serving the target's content, so a blob
  check "mismatches" on them. Edit and upload the target; a whole-file upload to the link's path would replace the
  link with a file.
- **The lockfile workflow pushes a signed commit to a canopy PR branch** after a `pyproject.toml` change (canopy#760
  got one re-resolving `requirements.lock`). Pin `--expected-head` on the PR's current head
  (`gh pr view N --json headRefOid`), not on your last push; `safe_merge.py` merges the head CI passed on.
- **canopy's `addopts` carries `-q`**; a second `-q` hides pytest's summary line. Count the dots, or drop yours.
- **flake8-simplify crashes under Python 3.14** (`ast.Str`), so canopy's src flake8 profile cannot run in the E2
  env; pyflakes, pycodestyle and the tests profile run, and CI's pre-commit lanes are the judge.
- **`dash_clientside.set_props` fires callbacks for a component inside a closed modal**, which a click cannot reach;
  that is how the two F-CANOPY-069 surfaces were driven without their gates.
- **The renderer holds a click's writer behind a pending table render**, so a pin at a fixed delay after the reload
  never hits F-CANOPY-028's window, and a synthetic params-store write after the click (the driver's `forced` arm)
  produces no writer firing at all: neither instrument re-creates early#2's order, which came from the params-store
  refresh landing inside the click's write latency. Give every driver run its own `--out`.
- **An API usage-credit error stops validator lanes mid-run, and their legs keep running.** After a lane dies, check
  `lsof` on its ports and stop its legs by pidfile (`… down <port>`; Lane 15-A's leg on 8084 ran for nine hours), and
  read its scratch (`/private/tmp/claude-501/lane15*/`) before re-spawning it: Lane 15-A had run every step.
- **The archive tool takes a lane's LAST text**, and a lane cut off mid-run ends with the error string.
  `--marker "[SYSTEM NOTIFICATION - NOT USER INPUT]"` splits at the lane's first background-task notification and
  recovers the status it wrote before it.
- **The guard refuses** `for` loops over `$p/bin/python`, `awk` programs, `$(…)` in command text, env prefixes and
  compound commands naming `.github/` paths; one plain command per call, interpreters by path, logic in a script.
- **A dash 3.x venv is below canopy's floor now**; so is the E2 env (item 33). A leg from it runs dash 3.3.0 on a
  tree that excludes it.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/<your worktree>   # or the Linux host's path
git status --short; git log --oneline -3
gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase15 --state all --json number,state,mergedAt
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7   # 80 / 63 / 1 / 2 / 14; open P1 4; open P2 10; no open P0 line
python3 -B util/ad-hoc/e2e_finding_triage.py --open-only | grep -c '^OPEN   P1 '   # 4
grep -c '^## Phase 15' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md   # 1
gh pr view 760 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED fbf01dff
gh pr view 761 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED aeeaf29b
gh release list --repo pcalnon/juniper-canopy --limit 2   # v0.9.0 Latest (2026-10-17) means item 7 is still owed
python3 -I -c "import json; m=json.load(open('reports/e2e-canopy-2026-09-02/item32-turing/dash_version_matrix_fix.json')); print({k: v['verdict'] for k, v in m.items()})"   # two ALIVE
python3 -I -c "import json; m=json.load(open('reports/e2e-canopy-2026-09-02/item32-turing/lane15A_pair_members.json')); print({k: v['pairs']['live_switch']['alert_after'].get('present') for k, v in m.items()})"   # True on the two parent labels (the stuck spinner), False on the fix
ls ~/.local/state/juniper/turing-e2/venvs/   # on turing: JuniperCanopy1{,-dash304,-dash32,-dash34,-dash44}, JuniperCascor1, JuniperData
lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8101|8202|8051|8052|8053|80[5-9][0-9]|8222|8230) '   # on turing: nothing; on the Linux host: the trio up (never touch it)
```

## Git state

- **juniper-ml:** branch `docs/canopy-e2e-phase15`, landed from turing through the API as signed commits. The
  worktree `sequential-coalescing-boot` holds the same files plus the two local unsigned freeze commits the
  consensus rounds reviewed; they never leave the host.
- **juniper-canopy:** `main` `aeeaf29b` (canopy#761 on canopy#760 `fbf01dff` on `571743db`); both squash-merged, both
  branches deleted by the repo. The fix trees `~/.local/state/juniper/turing-e2/trees/juniper-canopy-f069` and
  `-f028` are copies of the E2 tree with the apply scripts run (no `.git`); `-f028` equals canopy `main` except
  `requirements.lock`.
- **Services:** none left on this host. Lane 15-A's leftover leg on 8084 was stopped by pid on 2026-10-21. The
  scratch venvs and the legs' logs under `~/.local/state/juniper/turing-e2/legs/` remain.

## Changed by this session

- **Created:**
  - this file;
  - `util/ad-hoc/2026-10-20_f069_pair_members_probe.py`, `util/ad-hoc/2026-10-20_f069_apply_fix.py`,
    `util/ad-hoc/2026-10-20_f069_fix_leg.bash`, `util/ad-hoc/2026-10-20_f028_apply_fix.py`,
    `util/ad-hoc/2026-10-20_item31_f028_drives.bash`, `util/ad-hoc/2026-10-20_item31_f028_drives_pass2.bash`,
    `util/ad-hoc/2026-10-20_phase15_items31_32_apply.py`,
    `util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py`,
    `util/ad-hoc/2026-10-21_phase15_ledger_round1_corrections.py`,
    `util/ad-hoc/2026-10-21_phase15_ledger_round2_corrections.py`;
  - `reports/e2e-canopy-2026-09-02/item32-turing/` (`pair_members.json`, `dash_version_matrix_fix.json`, four
    `blob_check_*.json`, `lane15A_pair_members.json`, `lane15A_dash_matrix.json`);
  - `reports/e2e-canopy-2026-09-02/item31-turing/` (seven driver records, two `lane15A_*.json` and their `logs/`;
    the screenshots under `shots/` are LFS PNGs and stay on turing);
  - `reports/e2e-canopy-2026-09-02/drafts/lane15{A,B,C}_phase15_ledger_brief.md`;
  - `reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase15_round1.md` and
    `2026-10-21_validator_reports_phase15_round2.md`.
- **Modified:**
  - `util/ad-hoc/2026-10-20_item30_fixwave_redrive.py`: the `delay<N>` and `forced` f028 arms,
    `--f028-forced-gap-ms`, the `LOST_B` verdict;
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: Phase 15; the headers of F-CANOPY-069 and
    F-CANOPY-028 and a dated blockquote under each;
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


# ----------------------------------------------------------------------------- mechanics
def replace_once(text: str, old: str, new: str, what: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"anchor for {what} occurs {n} times, expected 1: {old[:90]!r}")
    return text.replace(old, new, 1)


def check_header_028(ledger: str) -> None:
    m = re.search(r"^\*\*(F-CANOPY-028) — (.*?)\*\*", ledger, re.M | re.S)
    assert m, "F-028 header not found"
    body = " ".join(m.group(2).split())
    assert _PRI_RE.search(body).group(1) == "P1", body[:80]
    assert re.search(r"\bFIXED\b", body[-170:]), body[-170:]


def apply(root: Path, check_only: bool) -> None:
    ledger_p = root / LEDGER
    ledger = ledger_p.read_text(encoding="utf-8")
    assert "CONSENSUS_RECORD_PLACEHOLDER" in ledger, "round 1 is already applied (or the apply pass is missing)"
    for what, old, new in LEDGER_SUBS:
        ledger = replace_once(ledger, old, new, what)
    ledger = replace_once(ledger, "CONSENSUS_RECORD_PLACEHOLDER", CONSENSUS_ROUND1, "consensus placeholder")
    check_header_028(ledger)

    prev_p = root / HANDOFF_PREV
    prev = replace_once(prev_p.read_text(encoding="utf-8"), BANNER_OLD, BANNER_NEW, "SUPERSEDED banner")
    parent_p = root / HANDOFF_PARENT
    parent = replace_once(parent_p.read_text(encoding="utf-8"), NAME_OLD, NAME_NEW, "parent pointer")
    index_p = root / INDEX
    index = replace_once(index_p.read_text(encoding="utf-8"), NAME_OLD, NAME_NEW, "INDEX pointer")
    old_handoff_p = root / HANDOFF_OLD
    assert old_handoff_p.exists(), f"{HANDOFF_OLD} is missing: the apply pass did not run here"
    for p, t in ((ledger_p, ledger), (prev_p, prev), (parent_p, parent), (index_p, index)):
        assert NAME_OLD not in t, f"{p.name} still names {NAME_OLD}"

    if check_only:
        print("check OK: every anchor is unique; F-CANOPY-028's header still triages P1 FIXED")
        return
    ledger_p.write_text(ledger, encoding="utf-8")
    prev_p.write_text(prev, encoding="utf-8")
    parent_p.write_text(parent, encoding="utf-8")
    index_p.write_text(index, encoding="utf-8")
    (root / HANDOFF_NEW).write_text(HANDOFF_TEXT, encoding="utf-8")
    old_handoff_p.unlink()
    print("applied:", LEDGER, HANDOFF_PREV, HANDOFF_PARENT, INDEX, f"{HANDOFF_NEW} (replaces {NAME_OLD})", sep="\n  ")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    apply(Path(args.root).resolve(), args.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())
