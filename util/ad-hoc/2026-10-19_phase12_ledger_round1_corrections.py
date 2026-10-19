#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-19
# Status      : ad-hoc — one-off correction pass; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Round 1's correction pass on the ledger's Phase 12, and on the Phase 12 handoff.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` and
``prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md``
as frozen for round 1 (local commit ``c626e847``). Round 1's three reports are archived verbatim in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase12_round1.md``. Every substitution
is anchored to occur exactly once in its file. Each is credited to the lane that raised it; the orchestrator
re-derived each from the artifact or the code before applying it (the ledger's round-1 record says what).

Usage:
    python3 util/ad-hoc/2026-10-19_phase12_ledger_round1_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
HANDOFF = ROOT / "prompts" / "thread-handoff_automated-prompts" / "HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md"

ROUND1_RECORD = """- **Round 1**: three lanes on the frozen `c626e847`, briefed separately with different entry points. Briefs are in
  `reports/e2e-canopy-2026-09-02/drafts/lane12{A,B,C}_phase12_ledger_brief.md`, and the reports, verbatim, in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase12_round1.md`.
  - Lane 12-A re-derived every number and source claim from the artifacts first, with its own reader of the census
    transcripts before the repo's, then the GitHub API and canopy's source at `25c5c887`.
  - Lane 12-B was adversarial on the dispositions: whether FIXED and "verified live" should stand, what the phase
    took from the PR body rather than from an artifact, the counts, the dropped reader change and the new items.
  - Lane 12-C checked the five changed files against each other, the rest of the ledger, the repo and GitHub, and
    ran the new handoff's verification commands.
  - The lanes' own probes are in their scratch directories and were not archived: each was a reader of the
    archived JSON or a `gh` query, and none produced a figure the ledger now rests on that the archived readers do
    not reproduce.
- **Verdicts.** All three returned SOUND-WITH-FIXES. Lane 12-A's and Lane 12-B's first findings change numbers in
  the phase text (the gate's writes, and the first renderer runs' times), and Lane 12-C's MAJOR changes the stated
  history behind item 27, so §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`
  requires round 2. None refuted a disposition, the counts or an action.
- **What round 1 changed:**
  - the gate's writes on the census legs: 8 or 9 per run in all, of which `false` onto an enabled lane 7, 6, 6
    and 6, with a request in flight at 5, 5, 5 and 2 of those; the draft had counted the clamp's two writes among
    them and said "most" for run 4 (Lanes 12-A and 12-B);
  - the first renderer runs ran 17:29–17:41 CDT; their file names carry their end times (Lane 12-A);
  - item 27's history: the allow arm was last driven on 2026-09-23 on demo legs, where it landed on the unfixed
    parent too, so Phase 8's "inferred regressed" was never established; the draft said it had not been driven
    since canopy#514 (Lane 12-C, MAJOR). It also now names the experimental toggle the gate needs (Lane 12-B);
  - run 3's provenance now rests on its leg's `build_date` against commits 2 and 3, with the page's
    `__junPollPacerLastUnacked` as the secondary basis, since commits 3 to 5 carry that name too (Lane 12-B);
  - a display-mode change's own fetch now waits for the fetch in flight plus up to one tick, measured at 3.0–4.7 s
    to issue in the renderer check, recorded under "Also changed" as a change a user could notice (Lane 12-B);
  - the cost is stated as the re-issue bound plus a tick and a round trip, and the bound as a running maximum
    that only grows (Lane 12-B);
  - item 0 is "closed", with its allow-arm drive converted to item 27 and its scored triggers to item 25, and
    F-CANOPY-055's Status bullet says which half of the entry's own verification rule is still owed (Lane 12-B);
  - the wiring comparison and the mutation check are labelled as the fix session's results, with what this phase
    could confirm from the capture alone (Lanes 12-A and 12-B);
  - the two residual re-request paths and the modulus change are each dispositioned, not filed, with the reason
    (Lane 12-B);
  - the squash: `25c5c887` has one parent, so the merged tree is the head's; CI on the squash (Lane 12-B); the
    merge commits are GitHub-signed too (Lane 12-A);
  - wording: the pacer's rule with no request yet (Lane 12-A); the modulus counts requests issued, `seq`
    (Lanes 12-A and 12-B); `LIBTORCH_LIB` is the handoff's, not the PR's (Lane 12-A); the worktree-cleanup
    procedure's real filename, in item 29 and the handoff (Lane 12-C);
  - the handoff: where items 25, 27 and 28 run, and four references that lacked filenames (Lane 12-C).
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-19_phase12_ledger_round1_corrections.py`,
    SUB_COUNT_LEDGER substitutions in the ledger and SUB_COUNT_HANDOFF in the handoff.
- **Re-derived by the orchestrator before applying:**
  - every gate write in the four transcripts, from `…_analyze.py`'s per-write list: 9, 8, 8 and 8; one `true` and
    one `false` onto the disabled lane per run; the requests in flight at each;
  - the first renderer runs' trigger stamps, 17:38:59–17:40:12 CDT, ten idle minutes after a 17:29 start;
  - Phase 9's allow-arm table (`:8058` LANDS 13.0 s on the first fix, `:8059` LANDS 19.7 s on the parent) and its
    Matrix ruling that F-CANOPY-025 "stays counted FIXED";
  - the legs' `build_date` fields (22:43:05Z, 00:02:18Z, 00:33:31Z) against the five commits' committer dates
    (23:28:34Z, 00:02:02Z, 00:19:57Z, 00:28:03Z, 01:19:15Z);
  - the three `extra` requests of the final renderer run: issued 3,010, 4,693 and 3,687 ms after the switch, landed
    6,695, 8,047 and 7,397 ms after it;
  - `25c5c887`'s one parent `4f69524b`, and its 46 successful and 7 skipped check runs;
  - `_gate_live_switch_button_handler`'s `return not (flags_ok and running)` at `25c5c887`;
  - the pacer's `reason = changed ? 'extra' : (acked ? 'tick' : 'stale')` and `n=seq` at `25c5c887`;
  - `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md` exists and the short name does not.
- **Not applied.** Lane 12-C's lint finding (the markdownlint hook excludes `notes/` and `prompts/`; the two
  headers were over 512 characters before this phase) and its note that the pacer-live README's heading calls
  runs 1–4 the "F-055 census": the README is not under review, and the ledger names the files correctly.
  Lane 12-C's finding 5, that the handoff describes a landing that has not happened, is checked after the PR
  lands, as that finding asks.
- **Slips.** None reported.
"""

LEDGER_SUBS = [
    # --- Summary: squash-merged (B9) ---
    (
        "Input of the pacer, compared by value. It merged on 2026-10-09T02:27:27Z as `25c5c887`, after three review\n"
        "  rounds, and shipped in **canopy 0.9.0**",
        "Input of the pacer, compared by value. It was squash-merged on 2026-10-09T02:27:27Z as `25c5c887`, after three\n"
        "  review rounds, and shipped in **canopy 0.9.0**",
    ),
    # --- Summary: the cost is the re-issue bound plus a tick and a round trip; the bound only grows (B8) ---
    (
        "(a non-OK reply from Dash or a middleware, or a network failure such as a canopy restart) lands no ack, so that\n"
        "  lane waits out its stale bound: at least 30 s, at most 120 s. On `main` the metrics store",
        "(a non-OK reply from Dash or a middleware, or a network failure such as a canopy restart) lands no ack, so that\n"
        "  lane's request is re-issued only after its stale bound, 30 s to 120 s, and answered a tick and a round trip\n"
        "  later (the renderer check's stranded request: re-issued at 31.0 s, applied at 35.0 s). The bound is a running\n"
        "  maximum that only grows for the life of the page: the 16–17 s in-flight times of census runs 1 and 2 would\n"
        "  have set it to 49–52 s (round 1, Lane 12-B). On `main` the metrics store",
    ),
    # --- Who: the merges are signed too (A6); the squash and its CI (B9); the wiring comparison is the session's (A, B5) ---
    (
        "`_PACED_POLLS`) and three merges of `main` into the branch (`13dcc58a`, `d777a86e`, `13834945`, the head at the\n"
        "  merge). Its one review thread, CodeQL's \"unused global variable\" on `_PACED_POLLS`\n"
        "  (`dashboard_manager.py:520`), is resolved; commit 5 answered it. The callback graph of `65ead946` is identical\n"
        "  to the capture taken from the leg serving `2689a207`: 179 callbacks, symmetric difference 0\n"
        "  (`util/ad-hoc/2026-10-08_compare_canopy_wiring.py`). The three merge commits are not in that comparison.",
        "`_PACED_POLLS`) and three merges of `main` into the branch (`13dcc58a`, `d777a86e`, `13834945`, the head at the\n"
        "  merge), GitHub-signed as well. It was squash-merged: `25c5c887` has one parent, `4f69524b`, so the merged tree\n"
        "  is the head's, and CI on the squash passed (46 check runs, 7 skipped). Its one review thread, CodeQL's \"unused\n"
        "  global variable\" on `_PACED_POLLS` (`dashboard_manager.py:520`), is resolved; commit 5 answered it. By that\n"
        "  session's `util/ad-hoc/2026-10-08_compare_canopy_wiring.py`, the callback graph of `65ead946` is identical to\n"
        "  the capture taken from the leg serving `2689a207`, 179 callbacks with a symmetric difference of 0. The\n"
        "  comparison needs a built canopy app, so this phase confirmed the capture's side only: 179 callbacks, no\n"
        "  `running=`, one writer of each paced lane's `disabled`, and one Input per feeder (round 1, Lanes 12-A and\n"
        "  12-B). The three merge commits are not in that comparison.",
    ),
    # --- Design: the pacer's rule with no request yet (A3); a mode change waits for the ack and a tick (B3) ---
    (
        "request and the ack. If the ack has caught up, or no request has been made, it writes request `seq + 1`. If the\n"
        "  ack is behind, it writes nothing, unless the request is older than the stale bound, when it re-issues it as\n"
        "  `stale`. A display-mode change issues an `extra` request at once, after the fetch in flight is acknowledged, and\n"
        "  a lost `extra` request is re-issued as `extra`.",
        "request and the ack. If the ack has caught up, it writes request `seq + 1` (the layout's seq-0 request is\n"
        "  acknowledged by the feeder's own initial call). If the ack is behind, it writes nothing, unless the request is\n"
        "  older than the stale bound, when it re-issues it as `stale`. A display-mode change issues an `extra` request on\n"
        "  the first pacer run after the fetch in flight is acknowledged (the pacer runs on the mode store and on the\n"
        "  1 s tick), and a lost `extra` request is re-issued as `extra`.",
    ),
    # --- Design: the two residual paths are dispositioned (B6) ---
    (
        "lands during that call. Round 1's Lane A found them; the PR and the CHANGELOG disclose them.",
        "lands during that call. Round 1's Lane A found them; the PR and the CHANGELOG disclose them. Neither is filed\n"
        "  as a finding: one lost response, replaced by the initial call's own answer, with no chain, sits below plan\n"
        "  §6.3's drift, and the capture confirms a single writer of each paced lane's `disabled`, so no release can\n"
        "  follow (round 1, Lane 12-B).",
    ),
    # --- Design, Also changed: the modulus counts requests issued, and is not filed (A4, B6, B9); the mode-change wait (B3) ---
    (
        "- **Also changed.** `FULL_HISTORY_POLL_TICK_MODULUS` (5) now counts acknowledged requests, not ticks of the\n"
        "  guarded Interval, so the full views refetch on every fifth request, expected every 5–10 s and not measured\n"
        "  (Phase 9's item 4 is not changed by this, but its measurement would be). `_PACED_POLLS` registers the paced\n"
        "  polls;",
        "- **Also changed.** `FULL_HISTORY_POLL_TICK_MODULUS` (5) now counts requests issued (the feeder passes the\n"
        "  request's `seq`, so a stale re-issue counts too), not ticks of the guarded Interval, so the full views refetch\n"
        "  on every fifth request, expected every 5–10 s and not measured. Not filed: the gate runs on the same 1 s tick,\n"
        "  so the cadence is equivalent until Phase 9's item 4 measures it (round 1, Lane 12-B). A display-mode change\n"
        "  now waits for the fetch in flight and up to one tick before its own fetch is issued, where on `main` the mode\n"
        "  store was an Input of the feeder and the fetch went out at once, evicting the one in flight: in the renderer\n"
        "  check's final run the three `extra` requests were issued 3.0, 4.7 and 3.7 s after the switch and their data\n"
        "  landed 6.7, 8.0 and 7.4 s after it, at a 3.6 s round trip; on a real page the wait runs up to the lane's\n"
        "  in-flight time, 17 s under the load of census runs 1 and 2 (round 1, Lane 12-B). `_PACED_POLLS` registers the\n"
        "  paced polls;",
    ),
    # --- Review: the mutation check is the session's result (B5) ---
    (
        "`extra` sticks forever, survived; commit 4 (`2689a207`) added the test that kills it. Each new node test fails\n"
        "  on its own mutation (`util/ad-hoc/2026-10-08_pacer_round2_mutation_check.py`: shared key, `Date.now()`, no\n"
        "  carry, sticky `extra`).",
        "`extra` sticks forever, survived; commit 4 (`2689a207`) added the test that kills it. By that session's\n"
        "  `util/ad-hoc/2026-10-08_pacer_round2_mutation_check.py`, each new node test fails on its own mutation (shared\n"
        "  key, `Date.now()`, no carry, sticky `extra`); it needs canopy's environment and was not re-run here.",
    ),
    # --- Review: LIBTORCH_LIB is the handoff's (A5) ---
    (
        "failed, run with `LD_LIBRARY_PATH`, `LIBTORCH` and `LIBTORCH_LIB` unset (with them set, 116 tests fail\n"
        "  identically on `main`)",
        "failed, run with `LD_LIBRARY_PATH` and `LIBTORCH` unset (the handoff adds `LIBTORCH_LIB`; with them set, 116\n"
        "  tests fail identically on `main`)",
    ),
    # --- Live checks: what the legs served, by build date (B2) ---
    (
        "under test. Runs 1 and 2 ran the tree before commit 1, by that session's edit history and not by any hash. Run 3\n"
        "  ran commit 2's tree, known from the page carrying `__junPollPacerLastUnacked`, which only commit 2 has. Run 4 and\n"
        "  the final status-bar run served **`2689a207`**, from the leg's `/v1/health`",
        "under test. Runs 1 and 2 ran the tree before commit 1, by that session's edit history and not by any hash; their\n"
        "  leg's `build_date`, 2026-10-08T22:43:05Z, precedes commit 1 (23:28:34Z). Run 3 ran commit 2's tree: its leg's\n"
        "  `build_date` is 00:02:18Z, sixteen seconds after commit 2 (00:02:02Z) and before commit 3 (00:19:57Z), on the\n"
        "  assumption that the leg does not reload its source, and the page carried `__junPollPacerLastUnacked`, which\n"
        "  commit 1 lacks (the README's \"which only commit 2 has\" was true when the leg was built and is false in letter\n"
        "  since commit 3, which kept the name; round 1, Lane 12-B). The build dates are in the status-bar census files,\n"
        "  whose legs are the census runs' legs. Run 4 and\n"
        "  the final status-bar run served **`2689a207`**, from the leg's `/v1/health`",
    ),
    # --- Live checks: the gate's writes (A1, B1) ---
    (
        "  - **The gate wrote `false` onto an enabled lane 8 or 9 times per run**, at page load, at each trigger and at the\n"
        "    clamp's release, with a request in flight at most of them; none evicted anything, because the pacer issues\n"
        "    the next request only on the ack. The gate's one `true` per run is the T-apply clamp, held 58.4–59.9 s.",
        "  - **The gate wrote 8 or 9 times per run**: `false` onto an enabled lane 7, 6, 6 and 6 times (at page load, at\n"
        "    each trigger and at the census's own release after T-apply), once `true` (the T-apply clamp, held\n"
        "    58.4–59.9 s) and once `false` onto the disabled lane (the clamp's release). A request was in flight at 5, 5,\n"
        "    5 and 2 of the enabled-lane writes, and none evicted anything, because the pacer issues the next request\n"
        "    only on the ack (round 1, Lanes 12-A and 12-B; the draft had counted the clamp's two writes among the\n"
        "    enabled-lane writes and said \"most\" for run 4's 2 of 6).",
    ),
    # --- Renderer: the first runs' times (A2) ---
    (
        "| | pacer, final (`2689a207`'s JavaScript; 20:04–20:16 CDT) | pacer, first (the tree before commit 1; 17:41 CDT) | guard + watchdog control (17:40 CDT) |",
        "| | pacer, final (`2689a207`'s JavaScript; 20:04–20:16 CDT) | pacer, first (the tree before commit 1; 17:29–17:41 CDT) | guard + watchdog control (17:29–17:40 CDT) |",
    ),
    (
        "3 changed both, and the final run is on the final JavaScript, which commits 4 and 5 left unchanged. The two runs\n"
        "  started 17:40–17:41 CDT beside two canopy unit suites, at a load read afterwards of 32.7 on 16 cores; the final\n"
        "  run at 9.9 before and 5.9 after.",
        "3 changed both, and the final run is on the final JavaScript, which commits 4 and 5 left unchanged. The two runs\n"
        "  ran 17:29–17:41 CDT (their file names carry their end times; round 1, Lane 12-A) beside two canopy unit suites,\n"
        "  at a load read afterwards, at 18:17, of 32.7 on 16 cores; the final run at 9.9 before and 5.9 after.",
    ),
    # --- Still owed: item 0 closed, two asks converted (B4) ---
    (
        "- **Item 0 is DONE**, both halves: F-CANOPY-058 was confirmed live in Phase 11, and one design for F-CANOPY-055,\n"
        "  F-CANOPY-058 and F-CANOPY-068 merged as canopy#731. Its real-renderer tests ran on the scratch app (the four\n"
        "  triggers mid-request, 10 idle minutes on a lane whose cycle is near 5 s, and a stranded request); its live\n"
        "  verification ran on the branch (the census and the status-bar census); the allow-arm drive it also asked for\n"
        "  did not run (item 27). The canopy text is corrected.",
        "- **Item 0 is closed**, both halves: F-CANOPY-058 was confirmed live in Phase 11, and one design for F-CANOPY-055,\n"
        "  F-CANOPY-058 and F-CANOPY-068 merged as canopy#731. Its real-renderer tests ran on the scratch app (the four\n"
        "  triggers mid-request, 10 idle minutes on a lane whose cycle is near 5 s, and a stranded request); its live\n"
        "  verification ran on the branch (the census and the status-bar census). Two of its asks are converted rather\n"
        "  than done: the allow-arm drive to item 27, and the census's scored triggers on the fix's leg to item 25\n"
        "  (round 1, Lane 12-B). The canopy text is corrected.",
    ),
    # --- Still owed: item 27's history and the gate's toggle (C1, B7) ---
    (
        "27. **F-CANOPY-055's Live Dataset Switch allow arm.** F-CANOPY-025's gate is computed inside the status-bar feeder,\n"
        "    which now applies, so the arm is inferred reachable again; it has not been driven since canopy#514's own\n"
        "    verification. Drive it on a leg serving canopy 0.9.0 or later whose training may be started (not the trio),\n"
        "    expecting the switch enabled while a run is active and disabled after. Record the result in F-CANOPY-025's and\n"
        "    F-CANOPY-055's entries.",
        "27. **F-CANOPY-055's Live Dataset Switch allow arm.** F-CANOPY-025's gate is computed inside the status-bar feeder.\n"
        "    The arm was last driven on 2026-09-23, on demo legs (Phase 9), where it landed on F-CANOPY-055's first fix and\n"
        "    on the unfixed parent alike, so Phase 8's \"inferred regressed\" was never established; it has not been driven\n"
        "    on a page at the trio's latency, nor on the pacer (round 1, Lane 12-C). This is the second half of\n"
        "    F-CANOPY-055's own verification rule, and of Phase 9's item 0. Drive it on a demo leg serving canopy 0.9.0 or\n"
        "    later, whose training may be started (never the trio), with the experimental-functions toggle on (the gate\n"
        "    is `not (flags_ok and running)`, `_gate_live_switch_button_handler`; round 1, Lane 12-B), expecting the\n"
        "    switch enabled while a run is active and disabled after the stop. Record the result in F-CANOPY-025's and\n"
        "    F-CANOPY-055's entries.",
    ),
    # --- Still owed: item 29's filename (C2) ---
    (
        "    `65ead946`), per `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`, and juniper-ml worktree `agile-napping-popcorn`",
        "    `65ead946`), per `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`, and juniper-ml worktree\n"
        "    `agile-napping-popcorn`",
    ),
    # --- F-CANOPY-055's Status bullet: which half of its verification rule is owed (B4, C1) ---
    (
        "  driven: the Live Dataset Switch allow arm, which needs a running training (Phase 12, item 27). The fix direction\n"
        "  below, a `running=` guard on its own lane, is the first fix, refuted in Phase 9; the pacer replaced it.",
        "  driven: the Live Dataset Switch allow arm, the second half of this entry's own verification rule, which needs\n"
        "  a running training (Phase 12, item 27; last driven 2026-09-23 on demo legs, Phase 9). The fix direction below,\n"
        "  a `running=` guard on its own lane, is the first fix, refuted in Phase 9; the pacer replaced it.",
    ),
    # --- the round-1 record ---
    (
        "CONSENSUS_RECORD_PENDING",
        "ROUND1_RECORD",
    ),
]

HANDOFF_SUBS = [
    # --- where items 25, 27 and 28 run (C3) ---
    (
        "commands first. Merge approval is not carried: ask before the first merge. Items 25, 27 and 28 need a host that can\n"
        "run a canopy verify leg against the trio (the Linux host, not turing); item 26 is a documents sweep and runs anywhere.",
        "commands first. Merge approval is not carried: ask before the first merge. Items 25 and 28 need a canopy verify leg\n"
        "against the trio (the Linux host, not turing); item 27 needs a demo leg that trains, never the trio; item 26 is a\n"
        "documents sweep and runs anywhere.",
    ),
    # --- filenames (C4) ---
    (
        "3. **Item 26: the manual sweep.** Every open finding against canopy's manual, F-CANOPY-012 and F-CANOPY-013 first;\n"
        "   then, once the owner rules (O17), the CHANGELOG and the design plans. Whatever the ruling, the CAN-015g/h design\n"
        "   note's \"every CAN-015g item has merged\" needs a dated correction.",
        "3. **Item 26: the manual sweep.** Every open finding against canopy's manual (canopy `docs/USER_MANUAL.md`),\n"
        "   F-CANOPY-012 and F-CANOPY-013 first; then, once the owner rules (O17), canopy's `CHANGELOG.md` and the design\n"
        "   plans. Whatever the ruling, the CAN-015g/h design note\n"
        "   (`notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`) and its \"every CAN-015g\n"
        "   item has merged\" need a dated correction.",
    ),
    # --- item 27's history and the toggle (C1, B7) ---
    (
        "4. **Item 27: F-CANOPY-055's Live Dataset Switch allow arm**, on a leg serving 0.9.0 or later whose training may be\n"
        "   started (never the trio). Record in F-CANOPY-025's and F-CANOPY-055's entries.",
        "4. **Item 27: F-CANOPY-055's Live Dataset Switch allow arm**, last driven 2026-09-23 on demo legs (ledger Phase 9),\n"
        "   never on the pacer: a demo leg serving 0.9.0 or later whose training may be started (never the trio), with the\n"
        "   experimental-functions toggle on. Record in F-CANOPY-025's and F-CANOPY-055's entries.",
    ),
    # --- the cleanup procedure's filename (C2) ---
    (
        "   `agile-napping-popcorn` (once its staged copies are confirmed to be what #2196 merged), per\n"
        "   `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`.",
        "   `agile-napping-popcorn` (once its staged copies are confirmed to be what #2196 merged), per\n"
        "   `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`.",
    ),
    (
        "- **`…_analyze.py` prints the transcript's `served` field**, which is the base commit for an uncommitted tree\n"
        "  (`3029d07d` for runs 1–3); the pacer-live README says what each run actually served and how that is known.",
        "- **`…_analyze.py` prints the transcript's `served` field**, which is the base commit for an uncommitted tree\n"
        "  (`3029d07d` for runs 1–3); `reports/e2e-canopy-2026-09-02/pacer-live/README.md` says what each run actually\n"
        "  served, and the ledger's Phase 12 gives the legs' build dates against the commits.",
    ),
    (
        "- **Outside the repo**, in auto-memory: `MEMORY.md` and a project note on the canopy E2E arc's state.",
        "- **Outside the repo**, in auto-memory: `MEMORY.md` and `canopy-e2e-arc-state.md`.",
    ),
]


def apply(text: str, subs: list, label: str) -> str:
    for old, new in subs:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"{label}: SUB anchor found {n} times: {old[:90]!r}")
        text = text.replace(old, new)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="apply in memory only; write nothing")
    args = ap.parse_args()
    ledger = LEDGER.read_text(encoding="utf-8")
    handoff = HANDOFF.read_text(encoding="utf-8")
    if "CONSENSUS_RECORD_PENDING" not in ledger or "- **Round 1**: three lanes on the frozen `c626e847`" in ledger:
        raise SystemExit("this is not the round-1 freeze (c626e847)")
    new_ledger = apply(ledger, LEDGER_SUBS, "ledger")
    record = ROUND1_RECORD.replace("SUB_COUNT_LEDGER", str(len(LEDGER_SUBS))).replace("SUB_COUNT_HANDOFF", str(len(HANDOFF_SUBS)))
    if new_ledger.count("ROUND1_RECORD") != 1:
        raise SystemExit("round-1 record placeholder not found exactly once")
    new_ledger = new_ledger.replace("ROUND1_RECORD", record)
    new_handoff = apply(handoff, HANDOFF_SUBS, "handoff")
    print(f"ledger: {len(LEDGER_SUBS)} substitutions, {len(ledger)} -> {len(new_ledger)} chars")
    print(f"handoff: {len(HANDOFF_SUBS)} substitutions, {len(handoff)} -> {len(new_handoff)} chars")
    if not args.check:
        LEDGER.write_text(new_ledger, encoding="utf-8")
        HANDOFF.write_text(new_handoff, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
