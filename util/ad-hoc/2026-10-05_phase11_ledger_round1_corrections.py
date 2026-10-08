#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-05
# Status      : ad-hoc — one-off correction pass; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Round 1's correction pass on the ledger's Phase 11 (and the evidence README), its Consensus record included.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` and
``reports/e2e-canopy-2026-09-02/f058-census-v2/README.md`` as frozen for round 1 (``1b7cf44b``). Round 1's
reports are archived verbatim in ``reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md``.
Every substitution is anchored to occur exactly once, so a pass applied to anything but that freeze stops.

Usage:
    python3 util/ad-hoc/2026-10-05_phase11_ledger_round1_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
README = ROOT / "reports" / "e2e-canopy-2026-09-02" / "f058-census-v2" / "README.md"

ROUND1_RECORD = """- **Round 1**: five lanes on the frozen `1b7cf44b`, briefed separately with different entry points. Briefs are in
  `reports/e2e-canopy-2026-09-02/drafts/lane11{A1,A2,A3,B1,B2}_phase11_ledger_brief.md`, and the reports,
  verbatim, in `reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md`.
  - Lane 11-A1 re-derived every source claim at canopy `60ae1870` and `c7876f5a`, and in dash 4.2.0's renderer
    and dcc bundle.
  - Lane 11-A2 wrote its own reader of the raw transcripts, from the shim's JavaScript, before running the
    repo's readers.
  - Lane 11-A3 tested the instruments: the byte provenance of all 16 copied files, a re-run of the synthetic
    check (6 of 6), and mutations of both new readers.
  - Lane 11-B1 argued for folding F-CANOPY-068 into F-CANOPY-058 and for lower ratings.
  - Lane 11-B2 attacked every universal claim and argued for higher ratings.
  - The lanes' own probes are archived as `util/ad-hoc/2026-10-05_phase11_r1_{a1,a2,a3,b1,b2}_*.py` (41 files) by
    `util/ad-hoc/2026-10-05_archive_phase11_lane_probes.py`, without the lanes' copies of repo and canopy files
    or Lanes 11-B1's and 11-B2's shell helpers.
- **Verdicts.** Lane 11-A1 returned SOUND and the other four SOUND-WITH-FIXES. Lane 11-B2's MAJOR changes a
  rating, so §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires
  round 2.
- **What round 1 changed:**
  - one rating: F-CANOPY-068, from P2 to P1 if a shipped CHANGELOG promise counts as documented, else P2 (Lane
    11-B2), the owner's question F-CANOPY-065 already carries. The counts move to 7 open P1 and 16 open P2.
    Lane 11-B1, on the opposite brief, kept F-CANOPY-068 a finding of its own: the gate and the second Input
    stay inside F-CANOPY-058 because they do what they are specified to do, and the watchdog does not;
  - the lane timings, now read from each change's innermost record (Lanes 11-A2 and 11-A3, independently):
    11.0–14.9 s enabled before each fire (was 10.4–14.7), episodes 0.3–3.6 s old at a fire (was 0.3–3.8),
    about 2.7 s disabled per cycle (was 2.8), and the replay's medians: 9 and 7 in phase and 1 at random, with no
    fire in about one random replay in five (were 9 and 8, 2, and one in six);
  - F-CANOPY-058's horizon. A re-enable evicts when the in-flight response has not landed by the time the next
    request is made, not whenever it comes "more than one period" before the response lands: 13 of 21 such
    re-enables here did not evict (Lanes 11-B1 and 11-B2). Its header, trigger bullet and Status changed, and
    the minutes are now stated as synthetic;
  - the triggers that occurred in mid-request: four kinds, not two (Lanes 11-B1 and 11-B2);
  - F-CANOPY-068's header and Effect: 7 evicting fires, 6 of them cascades (Lane 11-B1);
  - item 25's method: triggers fired inside the page (Lanes 11-A3 and 11-B2), with the trigger lag attributed
    per action (Lanes 11-A2, 11-A3 and 11-B2);
  - the release trace, which now pairs each late release with the evicted request whose successor is in flight,
    and self-tests four mutations (Lane 11-A3);
  - wording: the longest request, 5.4 s (Lane 11-A3); the sampling drift, which has no fixed direction (Lane
    11-B2); the synthetic check's "each fire" (Lane 11-A3); what made the request after T-mode (Lanes 11-A2
    and 11-A3); the trio's processes (Lane 11-B2); Phase 9's node-test claim and item 0's correction list (Lane
    11-B1); and the shim's docstring (Lane 11-A1).
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-05_phase11_ledger_round1_corrections.py`,
    SUB_COUNT substitutions in the ledger and README_SUB_COUNT in the evidence README.
- **Re-derived by the orchestrator before applying:**
  - the innermost-record timeline, with no alternation break in either run, and every corrected figure;
  - canopy's CHANGELOG `[0.8.0]` promise, at `60ae1870`, and canopy#624 (`06d8607e`), which put it there;
  - the 32 mid-request re-enables, 8 of them evicting, and the next request 1.3–3.7 s after each;
  - canopy#614's three files, none of them a node-gated test;
  - the slow lane's place in the gated set, so the clamp stops it (`dashboard_manager.py:466`);
  - the release trace's successor pairing, which gives the same 29 late releases, and its four self-tests on
    both transcripts;
  - the fires' spacing, close to whole multiples of 5 s (Lane 11-B2's reading).
- **Refuted:** Lane 11-A1's reading that an all-`no_update` answer is an HTTP 204 in dash 4.2.0. `_callback.py:602`
  sets `has_update` from `has_output`, which is true for any callback with an Output (`:640-645`), so the answer
  is a 200 with empty data, as F-CANOPY-058's entry says. Lane 11-A1's other two points on the shim's docstring
  stand.
- **Unresolved, for the owner:** whether a shipped CHANGELOG promise counts as documented under plan §6.3, which
  now decides two ratings, F-CANOPY-065's and F-CANOPY-068's.
- **Slips.** Lanes 11-A2, 11-A3 and 11-B2 each printed a commit's author line, which carries the owner's e-mail
  address, into their own local tool output (`git show --stat`). None repeated or sent it.
- **What the evidence cannot support.** Two idle pages on one host, about 25 minutes each: no rate for a page
  during training, with a live stream or in a full view; nothing live on dash 4.4.1; no stall of minutes on
  canopy. The watchdog's other samples were not logged, so its aliasing is inferred, though the replay and the
  fires' spacing support it."""

SUBS = [
    # --- F-CANOPY-058's header: the horizon, and what was observed (Lanes 11-B1 and 11-B2) ---
    (
        "so a mid-request re-request, or a re-enable more than one period before the in-flight response lands, starts an eviction cascade, and the lane's responses can stop applying for minutes (P1, canopy repo; found 2026-09-23 by F-CANOPY-055's round-1 adversarial lane; observed live on canopy `main` 2026-10-05, Phase 11; OPEN).**",
        "so a mid-request re-request, or a re-enable that lets the next request be made before the in-flight response lands, can start an eviction cascade, and the lane's responses can stop applying for minutes (P1, canopy repo; found 2026-09-23 by F-CANOPY-055's round-1 adversarial lane; mechanism observed live on canopy `main` 2026-10-05, Phase 11, in runs of up to 11 evictions and 34.8 s, the minutes only in synthetic repros; OPEN).**",
    ),
    # --- F-CANOPY-058's Status bullet (Lanes 11-B1 and 11-B2) ---
    (
        "- **Status 2026-10-05: OBSERVED LIVE on canopy `main`, at `60ae1870` and `c7876f5a` (Phase 11).** Two census\n"
        "  runs found 29 of 611 responses evicted, in eight runs of up to 11. Read one request at a time, every evicted\n"
        "  request's late completion released the lane under its successor. The triggers were the strand watchdog's false\n"
        "  fires, now filed as F-CANOPY-068, and, once, the gate's write at page load; the other triggers below, and the\n"
        "  clamp defeat, were not tested. On #613's lane the census measured the lane enabled for about 2 s of each ~4.9 s\n"
        "  cycle, not \"about 1 s per cycle\" as the watchdog bullet below has it. This supersedes the \"NOT yet observed on\n"
        "  canopy itself\" bullet below.",
        "- **Status 2026-10-05: OBSERVED LIVE on canopy `main`, at `60ae1870` and `c7876f5a` (Phase 11).** Two census\n"
        "  runs found 29 of 611 responses evicted, in eight runs of up to 11 evictions; the longest left the lane 34.8 s\n"
        "  without an applied answer, and the minutes below were reached only in Lane B's synthetic runs. Read one\n"
        "  request at a time, every evicted request's late completion released the lane under its successor. Of 32\n"
        "  mid-request re-enables, 8 evicted: a re-enable evicts only if the in-flight response has not landed by the time\n"
        "  the renderer makes the next request, 1.3–3.7 s after the re-enable in those runs, so \"more than one period\n"
        "  before the in-flight response lands\" (the header until Phase 11's round 1) was too wide. The re-enables were\n"
        "  the strand watchdog's false fires (28, of which 7 evicted; filed as F-CANOPY-068), the gate's write at page\n"
        "  load (1, evicting), and, incidentally, a tab switch (2) and an Apply's end (1, the census's redundant\n"
        "  release), none of which evicted; none was a scored test. The second-Input change and the clamp defeat did not\n"
        "  occur in mid-request, and Phase 9's synthetic mount cascade did not reproduce. On #613's lane the census\n"
        "  measured the lane enabled for about 2 s of each ~4.9 s cycle, not \"about 1 s per cycle\" as the watchdog bullet\n"
        "  below has it. This supersedes the \"NOT yet observed on canopy itself\" bullet below.",
    ),
    # --- F-CANOPY-058's trigger bullet: the next request, not the tick, evicts (Lanes 11-B1 and 11-B2) ---
    (
        "A re-enable restarts the\n"
        "  Interval's timer, so it ticks one period later and evicts the in-flight request if its response has not\n"
        "  landed by then; a re-request evicts it directly.",
        "A re-enable restarts the\n"
        "  Interval's timer, so it ticks one period later and the renderer then makes the next request, which evicts the\n"
        "  in-flight request if its response has not landed by then: 1.3–3.7 s after the re-enable in Phase 11's runs.\n"
        "  (Until Phase 11's round 1 this bullet said the tick itself evicts.) A re-request evicts it directly.",
    ),
    # --- Phase 9's node-test claim (Lane 11-B1, Finding 4) ---
    (
        "        on `e9053227` is node-gated. GitHub's ubuntu image ships node, although `ci.yml` has no setup-node step.\n",
        "        on `e9053227` is node-gated. GitHub's ubuntu image ships node, although `ci.yml` has no setup-node step.\n"
        "        **Correction (Phase 11, round 1, Lane 11-B1; re-derived by the orchestrator):** canopy#614 (`5c87f983`)\n"
        "        added no node-gated test. It changed `canopy_constants.py`, `dashboard_manager.py` and\n"
        "        `test_poll_gating.py`, which runs no JavaScript. The node-gated tests on `main` are F-042's, F-054's,\n"
        "        the idle cuts', Y4's and the phase-B bridge's, and the CI observation holds for those.\n",
    ),
    # --- Phase 11, Summary ---
    (
        "  fire was false: a feeder request was in flight at each, and the lane had been enabled for 10.4–14.7 s of the\n"
        "  30 s before it. Seven fires started runs, which hold 28 of the 29 evictions. The remaining run, of 1, followed\n"
        "  the gate's write at page load in the first run.\n"
        "- **Filed: F-CANOPY-068 (P2, OPEN)**, the watchdog's false fires. New findings, below, also says why it is a\n"
        "  finding of its own rather than part of F-CANOPY-058.",
        "  fire was false: a feeder request was in flight at each, and the lane had been enabled for 11.0–14.9 s of the\n"
        "  30 s before it. Seven fires evicted a response, and six of those started cascades; together they hold 28 of\n"
        "  the 29 evictions. The remaining eviction, a run of 1, followed the gate's write at page load in the first run.\n"
        "- **Filed: F-CANOPY-068 (P1 if a shipped CHANGELOG promise counts as documented, else P2; OPEN)**, the\n"
        "  watchdog's false fires. canopy's CHANGELOG for 0.8.0 promises that it re-enables the lane only once the lane\n"
        "  \"has been continuously disabled\" for 30 s. New findings, below, also says why it is a finding of its own\n"
        "  rather than part of F-CANOPY-058.",
    ),
    (
        "- **Counts** (`e2e_finding_triage.py`): 79 findings, 53 fixed, 1 accepted, 2 withdrawn, **23 open**; no open P0,\n"
        "  6 open P1 and 17 open P2.\n\n### The runs",
        "- **Counts** (`e2e_finding_triage.py`): 79 findings, 53 fixed, 1 accepted, 2 withdrawn, **23 open**; no open P0,\n"
        "  7 open P1 and 16 open P2.\n\n### The runs",
    ),
    # --- The runs: the trio (Lane 11-B2) ---
    (
        "  documents. `:8051` was never touched, and the trio's three processes were the same before and after the second\n"
        "  run.",
        "  documents. `:8051` was never touched, and the trio's three processes, started 2026-09-22, were still the same\n"
        "  after the second run, by their pids and start times, read then.",
    ),
    # --- The tables: what made the request after T-mode (Lanes 11-A2 and 11-A3) ---
    (
        "| T-mode | NO-EFFECT | 38 | 4 | the targeted request was answered 0.6 s after the trigger, and the mode change's request entered at 2.1 s; the 4 evictions follow a watchdog fire at 1,452.6 s |",
        "| T-mode | NO-EFFECT | 38 | 4 | the targeted request was answered 0.6 s after the trigger, and the next request entered at 2.1 s (the transcript does not record what made it); the 4 evictions follow a watchdog fire at 1,452.6 s |",
    ),
    (
        "| T-mode | NO-EFFECT | 41 | 4 | the targeted request was answered 1.1 s after the trigger, and the mode change's request entered at 2.5 s; the 4 evictions follow a watchdog fire at 1,358.3 s |",
        "| T-mode | NO-EFFECT | 41 | 4 | the targeted request was answered 1.1 s after the trigger, and the next request entered at 2.5 s; the 4 evictions follow a watchdog fire at 1,358.3 s |",
    ),
    # --- What the events show: the timings, from innermost records (Lanes 11-A2 and 11-A3) ---
    (
        "  4,875 ms. The lane was disabled for about 2.8 s of it (median disabled episodes 2,746 and 2,803 ms) and enabled\n"
        "  for the rest: the 1 s until a re-enabled Interval ticks, plus the time the renderer took to start the next\n"
        "  request.",
        "  4,875 ms. The lane was disabled for about 2.7 s of it and enabled for the rest: the 1 s until a re-enabled\n"
        "  Interval ticks, plus the time the renderer took to start the next request. The median disabled episodes were\n"
        "  2,710 and 2,743 ms, read from each change's innermost record. `…_analyze.py` prints 2,746 and 2,803 ms: it\n"
        "  dates a nested change by its enclosing dispatch, which the shim stamps earlier (Instruments).",
    ),
    (
        "  was in flight, the lane's current disabled episode was 0.3–3.8 s old, and the lane had been enabled for\n"
        "  10.4–14.7 s of the 30 s before. The watchdog fires only when every one of its samples over 30 s has found the\n"
        "  lane disabled, so none of its samples fell in those enabled stretches (F-CANOPY-068).",
        "  was in flight, the lane's current disabled episode was 0.3–3.6 s old, and the lane had been enabled for\n"
        "  11.0–14.9 s of the 30 s before. The watchdog fires only when every one of its samples over 30 s has found the\n"
        "  lane disabled, so none of its samples fell in those enabled stretches (F-CANOPY-068).",
    ),
    (
        "  the fire, before any successor was made. So a successor was made anywhere from 1.4 s to more than 2.2 s after\n"
        "  a fire.",
        "  the fire, before any successor was made. So a successor was made anywhere from 1.4 s to more than 2.2 s after\n"
        "  a fire. Across all 32 mid-request re-enables, the 28 fires and 4 gate writes, 8 evicted, and the next request\n"
        "  entered `watched` 1.3–3.7 s after the re-enable.",
    ),
    # --- F-CANOPY-058 section (Lanes 11-B1 and 11-B2) ---
    (
        "- **What is now observed** is the class as filed. A re-enable while a request is in flight is followed by that\n"
        "  request's eviction; the evicted request's late completion re-enables the lane under its successor; and the\n"
        "  successor can be evicted in turn. Each of the eight runs ended by itself, after at most 11 evictions, when a\n"
        "  successor's answer landed before the next request was made.",
        "- **What is now observed** is the class as filed, with its horizon corrected. A re-enable while a request is in\n"
        "  flight evicts that request if its response has not landed by the time the next request is made, and 8 of the\n"
        "  32 mid-request re-enables did. The evicted request's late completion then re-enables the lane under its\n"
        "  successor, and the successor can be evicted in turn. Each of the eight runs ended by itself, after at most 11\n"
        "  evictions, when a successor's answer landed before the next request was made. The entry's header and trigger\n"
        "  bullet said that a re-enable \"more than one period before the in-flight response lands\" evicts; 13 of 21\n"
        "  such re-enables here did not, and both now name the next request.",
    ),
    (
        "- **What is not.** Of the entry's triggers, only two occurred: the watchdog's false fires and the gate's write at\n"
        "  page load. A tab switch, the end of an Apply and a second-Input change in mid-request were not tested,\n"
        "  because the scripted triggers landed late (Instruments), and neither was the clamp defeat. The entry's\n"
        "  \"can stop applying for minutes\" is not reached here: the longest run left the lane 34.8 s without an applied\n"
        "  answer. Lane B's synthetic runs, which reached minutes, stand as recorded.",
        "- **What is not.** Four kinds of trigger occurred in mid-request: the watchdog's false fires (28, of which 7\n"
        "  evicted), the gate's write at page load (1, evicting), a tab switch (2, T-tab's second clicks) and an Apply's\n"
        "  end (1, the census's redundant release after T-apply), and the last two kinds evicted nothing. None was a\n"
        "  scored test, because the targeted triggers landed late (Instruments). The second-Input change and the clamp\n"
        "  defeat did not occur in mid-request. The entry's \"can stop applying for minutes\" is not reached here: the\n"
        "  longest run left the lane 34.8 s without an applied answer. Lane B's synthetic runs, which reached minutes,\n"
        "  stand as recorded.",
    ),
    (
        "  answered 8 times, which ended the eight runs. This is F-CANOPY-058's mechanism read directly, not inferred from\n"
        "  the runs. The trace's self-test removes the late releases from a copy of each transcript, and then reads every\n"
        "  eviction as \"late release: none\".",
        "  answered 8 times, which ended the eight runs. This is F-CANOPY-058's mechanism read directly, not inferred from\n"
        "  the runs. One of the trace's four self-tests removes the late releases from a copy of each transcript, and\n"
        "  then reads every eviction as \"late release: none\" (Instruments).",
    ),
    (
        "- **The rating stays P1.** These runs confirm the mechanism on canopy; they change nothing the entry's rating\n"
        "  rests on.",
        "- **The rating stays P1.** These runs confirm the mechanism on canopy. The minutes stay synthetic, and the P1\n"
        "  rests, as before, on slow pages and on F-CANOPY-055's repair, neither of which an idle page with requests of\n"
        "  about 2.8 s could test.",
    ),
    # --- F-CANOPY-068's header: 6 cascades, and the conditional P1 (Lanes 11-B1 and 11-B2) ---
    (
        "and 7 of the 28 fires started F-CANOPY-058 cascades (P2, canopy repo; found 2026-10-05 by the F-CANOPY-058 census; OPEN).**",
        "and 7 of the 28 fires evicted a response, 6 of them starting F-CANOPY-058 cascades (P1 if a shipped CHANGELOG promise counts as documented, else P2, the owner's question; canopy repo; found 2026-10-05 by the F-CANOPY-058 census; re-rated P1 in round 1 of this phase's validation; OPEN).**",
    ),
    (
        "  case\" for that reason (`:2519-2522`; `canopy_constants.py:421-424` says the same). The threshold cannot keep\n"
        "  that promise. The predicate measures how long every 5 s sample has found the lane disabled, not how long the\n"
        "  lane has been disabled.",
        "  case\" for that reason (`:2519-2522`; `canopy_constants.py:421-424` says the same). canopy's CHANGELOG makes the\n"
        "  promise to its readers: its `[0.8.0]` entry says the watchdog \"re-enables the interval once it has been\n"
        "  continuously disabled for `METRICS_STORE_STRAND_TIMEOUT_MS`\", because \"fast recovery would reopen the\n"
        "  eviction window\" (`CHANGELOG.md:1222-1225` at `60ae1870`, added by canopy#624, `06d8607e`). The threshold\n"
        "  cannot keep that promise. The predicate measures how long every 5 s sample has found the lane disabled, not\n"
        "  how long the lane has been disabled.",
    ),
    (
        "  at `c7876f5a`, 30.9 and 35.7 an hour. At every fire a feeder request was in flight, the lane's current disabled\n"
        "  episode was 0.3–3.8 s old, and the lane had been enabled for 10.4–14.7 s of the 30 s before. The longest\n"
        "  request took 5.3 s, so none came near stranding.",
        "  at `c7876f5a`, 30.9 and 35.7 an hour. At every fire a feeder request was in flight, the lane's current disabled\n"
        "  episode was 0.3–3.6 s old, and the lane had been enabled for 11.0–14.9 s of the 30 s before. The longest\n"
        "  request took 5.4 s from entering `watched` to its response landing, so none came near stranding.",
    ),
    (
        "  not its other samples. The feeder's cycle was about 4.9 s and the watchdog samples every 5 s, so on average each\n"
        "  sample falls about 0.1 s later in the cycle than the one before. Once on the disabled part, about 2.8 s of each\n"
        "  cycle, it can stay there for many samples in a row. Replaying the watchdog's logic over each run's measured\n"
        "  lane, sampling every 5,000 ms in phase, gives 5–16 and 3–18 fires per run (medians 9 and 8) at every one of 500\n"
        "  starting phases, against 13 and 15 observed. Sampling at the same rate with each sample's phase randomized\n"
        "  gives a median of 2 in both runs, and no fire at all in about one replay in six. So the fires come from the\n"
        "  samples keeping phase with the cycle. Further from the cycle, at 6,000 and 7,500 ms, sampling in phase and\n"
        "  sampling at random give about the same, medians 2 to 4\n"
        "  (`util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py`). The replay does not exclude a lock between the\n"
        "  watchdog's samples and the feeder's cycle through the renderer's queue, which delays both.",
        "  not its other samples. The feeder's cycle was about 4.9 s and the watchdog samples every 5 s, so each sample\n"
        "  falls at nearly the same point in the cycle as the one before, drifting slowly one way or the other as the\n"
        "  cycle runs longer or shorter than 5 s. Once on the disabled part, about 2.7 s of each cycle, it can stay there\n"
        "  for many samples in a row. Replaying the watchdog's logic over each run's measured lane, sampling every\n"
        "  5,000 ms in phase, gives 5–16 and 3–18 fires per run (medians 9 and 7) at every one of 500 starting phases,\n"
        "  against 13 and 15 observed. Sampling at the same rate with each sample's phase randomized gives a median of 1\n"
        "  in both runs, and no fire at all in about one replay in five. So the fires come from the samples keeping phase\n"
        "  with the cycle. Further from the cycle, at 6,000 and 7,500 ms, sampling in phase and sampling at random give\n"
        "  about the same, medians 1 to 3.5 (`util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py`). The gaps between\n"
        "  fires sit close to whole multiples of 5 s, 20 of 26 within 0.3 s and all within 0.75 s except the one spanning\n"
        "  the first run's Apply clamp (1.3 s), so the watchdog's samples mostly kept to their own grid. Still, the replay\n"
        "  does not exclude some locking of its samples to the feeder's cycle through the renderer's queue, which delays\n"
        "  both, and its one phase per replay is a model: the Apply clamp stops the slow lane too\n"
        "  (`dashboard_manager.py:466`), which then restarts at a new phase.",
    ),
    (
        "  response is evicted. 7 of the 28 fires evicted, and through F-CANOPY-058 each became a run: 28 of the 29\n"
        "  evicted responses followed a false fire. Without F-CANOPY-058, an evicting false fire would cost one answer, a\n"
        "  cycle's delay; the longer stalls are F-CANOPY-058's.\n"
        "- **Rating: P2.** On its own it delays the chart by a cycle at a time, which plan §6.3 puts under drift; the harm\n"
        "  a user would see comes through F-CANOPY-058, which is P1 already.",
        "  response is evicted. 7 of the 28 fires evicted a response. Through F-CANOPY-058, 6 of those became cascades of\n"
        "  2 to 11 evictions; the seventh stopped at one, its late release falling under a request that was answered in\n"
        "  time. 28 of the 29 evicted responses followed a false fire. Without F-CANOPY-058, an evicting false fire would\n"
        "  cost one answer, a cycle's delay; the longer stalls are F-CANOPY-058's.\n"
        "- **Rating: P1 if a shipped CHANGELOG promise counts as documented, else P2**, the owner's question that\n"
        "  F-CANOPY-065 already carries (Phase 10's Consensus record). Plan §6.3's P1 is \"breaks a documented\n"
        "  behaviour\", and canopy's shipped CHANGELOG promises the behaviour these fires break (Its own contract,\n"
        "  above). If such a promise does not count, it is P2: on its own it delays the chart by a cycle at a time,\n"
        "  which §6.3 puts under drift, and the harm a user would see comes through F-CANOPY-058, which is P1 already.\n"
        "  This phase first rated it P2 on its code comment alone; round 1 found the CHANGELOG entry (Lane 11-B2).",
    ),
    (
        "  fire would still cost a response. A watchdog that counted progress would end the false fires, and the gate's",
        "  fire that evicts would still cost a response. A watchdog that counted progress would end the false fires, and the gate's",
    ),
    (
        "  the rate. The replay suggests the rate falls as the cycle moves away from the 5 s sampling period; Phase 9\n"
        "  modelled 37–44 an hour at a 7 s request time and judged that model probably too high there.",
        "  the rate. The replay varies only the sampling period over the measured lane, so it says nothing about a longer\n"
        "  request, which would also lengthen the lane's disabled part; Phase 9 modelled 37–44 an hour at a 7 s request\n"
        "  time and judged that model probably too high there.",
    ),
    # --- Instruments (Lanes 11-A1, 11-A2, 11-A3 and 11-B2) ---
    (
        "    eviction, a second-Input change evicting in both modes, the gate's mount write cascading, and a forced\n"
        "    strand caught at each fire. Its output is the evidence directory's `2026-10-05_synth_check.jsonl`.",
        "    eviction, a second-Input change evicting in both modes, the gate's mount write cascading, and a forced\n"
        "    strand caught at each of its five fires, though the check's rule asks only for one. Its output is the\n"
        "    evidence directory's `2026-10-05_synth_check.jsonl`. Round 1's Lane 11-A3 re-ran it: 6 of 6.",
    ),
    (
        "  - `2026-10-05_f058_census_v2_release_trace.py` reads F-CANOPY-058's mechanism one request at a time and checks\n"
        "    every fire against the lane's own timeline. Its `--self-test` builds, from the transcript itself, both\n"
        "    answers it must be able to give: with the late releases removed, every eviction reads \"none\"; with a fire\n"
        "    placed 31 s into the run's longest disabled episode (each run's Apply clamp, 62 s and 63 s), that fire reads\n"
        "    0 ms enabled. Both pass on both transcripts. Its first version took a release followed within 1 s by the\n"
        "    successor's answer for the successor's own, and so misread two late releases. It now uses 100 ms, and prints\n"
        "    the margin on both sides: own releases 13–89 ms before their answers, late releases 0.4–2.0 s before the\n"
        "    successor's.\n"
        "  - `2026-10-05_f058_watchdog_alias_replay.py` replays the watchdog's logic over the measured lane, in phase and\n"
        "    with each sample's phase randomized (F-CANOPY-068).",
        "  - `2026-10-05_f058_census_v2_release_trace.py` reads F-CANOPY-058's mechanism one request at a time and checks\n"
        "    every fire against the lane's own timeline. It pairs each late release with the evicted request whose\n"
        "    successor is the request in flight; until round 1 it took the oldest pending one, and a dropped or shifted\n"
        "    release then silently re-paired every later eviction (Lane 11-A3). Its `--self-test` builds four known\n"
        "    answers from the transcript itself: with the late releases removed, every eviction reads \"none\"; with a fire\n"
        "    placed 31 s into the run's longest disabled episode (each run's Apply clamp, 62 s and 63 s), that fire reads\n"
        "    0 ms enabled; with one late release dropped, only its eviction changes; and with every late release whose\n"
        "    successor was answered shifted into that successor's own window, exactly those evictions change. All four\n"
        "    pass on both transcripts. Its first version took a release followed within 1 s by the successor's answer\n"
        "    for the successor's own, and so misread two late releases. It now uses 100 ms, and prints the margin on\n"
        "    both sides: own releases 13–89 ms before their answers, late releases 0.4–2.0 s before the successor's.\n"
        "  - `2026-10-05_f058_watchdog_alias_replay.py` replays the watchdog's logic over the measured lane, in phase and\n"
        "    with each sample's phase randomized (F-CANOPY-068).\n"
        "  - **Both read the lane from each change's innermost record** since round 1. The shim stamps a record with its\n"
        "    dispatch's ENTRY time, and an enclosing dispatch logs a nested change again at its own, earlier time; read\n"
        "    from the enclosing records, a change is dated early, by a median of about 22 ms and up to 327 ms here (Lanes\n"
        "    11-A2 and 11-A3, independently). The innermost records alternate with no break in either run.\n"
        "    `…_analyze.py` is kept as it ran, and still dates changes by their enclosing records.\n"
        "  - **The shim's docstring is wrong in two places**, kept as it ran (Lane 11-A1): it logs the `running=` writes\n"
        "    as thunks with empty action types, not as `ON_PROP_CHANGE`; and actions dispatched inside a thunk, such as\n"
        "    `AddRequested`, bypass its wrapper, though the `AddWatched`, `RemoveWatched` and `AddExecuted` it scores do\n"
        "    not. Its third disputed claim holds: in dash 4.2.0 an all-`no_update` answer from a callback with an Output\n"
        "    is an HTTP 200 with empty data, not a 204 (`dash/_callback.py:602`, `:640-645`; re-derived by the\n"
        "    orchestrator).",
    ),
    (
        "  - **Its scripted triggers reached the page 1.3–4.2 s after they fired**, through the renderer's queue, and\n"
        "    each fired on a request already 1.6–2.9 s into a flight whose median was 2.8 s. So the gate, tab and mode\n"
        "    triggers each landed after the targeted request had been answered, and TOOK's horizons (1.0 s and 2.5 s)\n"
        "    were too short to see a later effect. To test the claim, a trigger has to fire as a request enters\n"
        "    `watched`, and be scored as \"a re-enable while a request is in flight, whose response lands after the next\n"
        "    request is made\", not within a fixed horizon.",
        "  - **Its scripted triggers took effect 1.3–4.2 s after they fired.** For T-gate and T-mode that was the\n"
        "    renderer's queue: 1.3–1.4 s to the gate's write, and 2.1–2.5 s to the next request. For T-tab most of it was\n"
        "    the driver's own: its clicks ran 0.7–1.0 s and 2.3–2.9 s after the trigger fired (its 1 s wait between them\n"
        "    took 1.6–1.9 s), and each gate write followed its click by 0.3–1.9 s (Lanes 11-A2, 11-A3 and 11-B2). Each\n"
        "    trigger fired on a request already 1.6–2.9 s into a flight whose median was 2.8 s, so the gate, tab and mode\n"
        "    triggers each landed after the targeted request had been answered, and TOOK's horizons (1.0 s and 2.5 s)\n"
        "    were too short to see a later effect. To test the claim, a trigger has to fire inside the page as a request\n"
        "    enters `watched` (a trigger sent from Python then would still land 1.0–2.9 s into the flight), and be scored\n"
        "    as \"a re-enable while a request is in flight, whose response lands after the next request is made\", not\n"
        "    within a fixed horizon.",
    ),
    # --- Still owed (Lanes 11-A3, 11-B1 and 11-B2) ---
    (
        "  samples of `disabled`. The canopy text to correct is now at `60ae1870`'s lines (F-CANOPY-058's section,\n"
        "  above), plus `test_poll_gating.py:194-197`'s \"continuously ``True``\" (F-CANOPY-068). The item's real-renderer\n"
        "  tests gain one: 10 idle minutes on a healthy lane whose cycle is near the watchdog's 5 s sampling period.",
        "  samples of `disabled`. The canopy text to correct is now at `60ae1870`'s lines (F-CANOPY-058's section,\n"
        "  above), plus, for F-CANOPY-068, `test_poll_gating.py:194-197`'s \"continuously ``True``\", the watchdog's own\n"
        "  comment (`dashboard_manager.py:2514-2522`) and `canopy_constants.py:412-424`; the shipped CHANGELOG's\n"
        "  `[0.8.0]` promise needs a correcting entry in the release that fixes it. The item's real-renderer tests gain\n"
        "  one: 10 idle minutes on a healthy lane whose cycle is near the watchdog's 5 s sampling period.",
    ),
    (
        "25. **The census's triggers.** Fire each as a request enters `watched`, and score it as described under\n"
        "    Instruments. Then run, on `main` or on item 0's fix, the four triggers these runs could not test: the gate, a\n"
        "    tab switch, the end of an Apply (with the clamp defeat) and a second-Input change in mid-request.",
        "25. **The census's triggers.** Fire each inside the page, from the shim's `AddWatched` hook, as a request enters\n"
        "    `watched`; timestamp every action in the page; and score each as described under Instruments. Then run, on\n"
        "    `main` or on item 0's fix, the four triggers these runs could not test as scored triggers: the gate, a tab\n"
        "    switch, the end of an Apply (with the clamp defeat) and a second-Input change in mid-request.",
    ),
    # --- Matrix effect and counts ---
    (
        "  - **6 open P1:** F-CANOPY-055, F-CANOPY-058, F-CANOPY-064, F-CANOPY-065, F-CASCOR-001 and F-CASCOR-002.\n"
        "  - **17 open P2**, F-CANOPY-068 the new one.",
        "  - **7 open P1:** F-CANOPY-055, F-CANOPY-058, F-CANOPY-064, F-CANOPY-065, F-CANOPY-068, F-CASCOR-001 and\n"
        "    F-CASCOR-002. F-CANOPY-065 and F-CANOPY-068 are P1 only if a shipped CHANGELOG promise counts as\n"
        "    documented; if not, the counts are 5 open P1 and 18 open P2.\n"
        "  - **16 open P2.**",
    ),
    # --- the Consensus record placeholder ---
    (
        "- Written after each round. Round 1 reviews this phase as frozen, without this record.",
        "ROUND1_RECORD",
    ),
]

README_SUBS = [
    (
        "   gives 5–16 fires at every one of 500 sampling phases (median 9), against 13 observed; at the same rate with\n"
        "   each sample's phase randomized it gives a median of 2 (`2026-10-05_f058_watchdog_alias_replay.py`; the second\n"
        "   run gives 3–18, median 8, against 15, and the same randomized median). That shows aliasing sufficient; it does\n"
        "   not exclude a phase lock through the renderer's queue.",
        "   gives 5–16 fires at every one of 500 sampling phases (median 9), against 13 observed; at the same rate with\n"
        "   each sample's phase randomized it gives a median of 1 (`2026-10-05_f058_watchdog_alias_replay.py`; the second\n"
        "   run gives 3–18, median 7, against 15, and the same randomized median). Those figures read the lane from each\n"
        "   change's innermost record, as the ledger's Phase 11 explains; before its round 1 the replay dated changes\n"
        "   early and gave medians of 9, 8 and 2. That shows aliasing sufficient; it does not exclude a phase lock\n"
        "   through the renderer's queue.",
    ),
    (
        "Its scripted triggers reach the page 1.3–4.2 s after they fire, so as written they cannot test a mid-request\n"
        "re-enable (the ledger's Phase 11, Instruments).",
        "Its scripted triggers take effect 1.3–4.2 s after they fire, partly through the renderer's queue and, for\n"
        "T-tab, mostly through the driver's own late clicks, so as written they cannot test a mid-request re-enable\n"
        "(the ledger's Phase 11, Instruments).",
    ),
]


def apply(text: str, subs: list) -> str:
    for old, new in subs:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"SUB anchor found {n} times: {old[:100]!r}")
        text = text.replace(old, new)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="apply in memory only; write nothing")
    args = ap.parse_args()
    before = LEDGER.read_text(encoding="utf-8")
    if "- Written after each round. Round 1 reviews this phase as frozen, without this record." not in before:
        raise SystemExit("the round-1 placeholder is absent: is this the round-1 freeze (1b7cf44b)?")
    after = apply(before, SUBS)
    # The record names the pass's own size, so it is filled in last.
    record = ROUND1_RECORD.replace("README_SUB_COUNT", str(len(README_SUBS))).replace("SUB_COUNT", str(len(SUBS)))
    if after.count("ROUND1_RECORD") != 1:
        raise SystemExit("round-1 record placeholder not found exactly once")
    after = after.replace("ROUND1_RECORD", record)
    readme_before = README.read_text(encoding="utf-8")
    readme_after = apply(readme_before, README_SUBS)
    print(f"ledger: {len(SUBS)} substitutions, {len(before)} -> {len(after)} chars; README: {len(README_SUBS)} substitutions")
    if not args.check:
        LEDGER.write_text(after, encoding="utf-8")
        README.write_text(readme_after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
