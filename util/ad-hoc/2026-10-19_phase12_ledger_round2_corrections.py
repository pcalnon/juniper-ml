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
"""Round 2's correction pass on the ledger's Phase 12: the final wording pass, which ends its review.

Applied to the ledger, the Phase 12 handoff and the two evidence READMEs as frozen for round 2 (local commit
``190c896c``, round 1's pass applied to ``c626e847``). Round 2's reports are archived verbatim in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase12_round2.md``. Neither lane found
anything that changes a number, a disposition or an action, so under §4 of
``notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`` the review ends at round 2.
The two README substitutions correct slips round 1 found in files outside the review (the orchestrator re-derived
each from the archived JSON before applying). Every substitution is anchored to occur exactly once in its file.

Usage:
    python3 util/ad-hoc/2026-10-19_phase12_ledger_round2_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
HANDOFF = ROOT / "prompts" / "thread-handoff_automated-prompts" / "HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md"
README_LIVE = ROOT / "reports" / "e2e-canopy-2026-09-02" / "pacer-live" / "README.md"
README_RENDERER = ROOT / "reports" / "e2e-canopy-2026-09-02" / "pacer-renderer-check" / "README.md"

ROUND2_RECORD = """
- **Round 2**: two lanes on the frozen `190c896c`, briefed on round 1's corrections only, from one brief,
  `reports/e2e-canopy-2026-09-02/drafts/lane12R2_phase12_ledger_brief.md`. The reports, verbatim, are in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase12_round2.md`.
  - Lane 12-R2A replayed round 1's pass on `c626e847`: `190c896c` byte for byte, with no hand edit, and re-derived
    every claim the pass introduced with its own readers of the transcripts, the renderer runs, the capture and
    canopy's source at `25c5c887`. Lane 12-R2B was adversarial on the pass, and replayed it too.
  - Both found every corrected number and credit to re-derive, the diff to hold nothing the record does not list,
    and the triage unchanged.
- **Verdicts.** Both returned SOUND-WITH-FIXES. Neither found anything that changes a number, a disposition or an
  action, so under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` **the
  review ends at round 2.**
- **What round 2 changed**, wording only:
  - where the enabled-lane gate writes fall: two at page load, one at T-gate, two or three at T-tab, one at the
    census's own release, none at T-mode (Lanes 12-R2A and 12-R2B);
  - item 27 says what a demo drive can and cannot establish: that the arm reaches the paced bar, not a difference
    from the old code, which Phase 9 found also got through on a demo page; Phase 9's item 0 asked for a leg "where
    the old code fails", which has no venue that trains, and that ask is recorded as unmet by design (Lane 12-R2B);
  - the cost's wording in item 18 and in the handoff now adds the tick and the round trip after the bound, as the
    Summary does, and the 49–52 s is "as much as", since the pacer's own round trip is a lower bound (Lane 12-R2B;
    Lane 12-R2A's note);
  - the squash's check runs: 53, of which 46 successful and 7 skipped (Lane 12-R2B);
  - the sentence on the pacer-live README now says where this phase departs from it, and two slips in the two
    READMEs, found in round 1, are corrected by this pass outside the reviewed files: the pacer-live README's table
    called census runs 1 to 4 the "F-055 census" and gave the commit-2 discriminator round 1 qualified, and the
    renderer-check README dated the first two runs 17:40–17:54 CDT (Lane 12-R2A; round 1, Lanes 12-A and 12-C);
  - round 1's record: the lanes' figures are ones a `json` reading of the archived files reproduces, not the
    archived readers; the renderer measurement is the final run's; Lane 12-B's count of 4 in flight for run 2 was
    not adopted, both readers giving 5; the times were Lane 12-A's second finding; the handoff's item-4 echo is
    listed; and Lane 12-C's finding 5 is checked once the commits land, before the PR is marked ready (Lanes
    12-R2A and 12-R2B).
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-19_phase12_ledger_round2_corrections.py`,
    SUB_COUNT_LEDGER substitutions in the ledger, SUB_COUNT_HANDOFF in the handoff and SUB_COUNT_README in the two READMEs.
- **Re-derived by the orchestrator before applying:** every gate write's place against the triggers in the four
  transcripts, none after T-mode (the last writes at 744,000, 789,703, 741,583 and 730,977 ms, T-mode at
  1,514,647 ms or later); the two READMEs' lines; the 53 check runs; the pacer's `maxRtt` as the age at the last
  pacer run that still saw the request unanswered (`dashboard_manager.py:578-587` at `25c5c887`).
- **Unresolved dissent.** None.
- **What the evidence cannot support** is unchanged from "What VERIFIED LIVE rests on": nothing live on the merged
  tree or the wheel, no injected failure, no training run, no mid-request Apply release, one host, dash 4.2.0
  only. The instrument of this phase is a reading of archived files and of the GitHub API; it could have produced
  a different answer only where those files disagree with the fix session's README and PR body, and the two
  places it found are recorded above.
- **Slips.** None reported."""

LEDGER_SUBS = [
    # --- the gate's writes, where they fall (R2A-2, R2B-4) ---
    (
        "  - **The gate wrote 8 or 9 times per run**: `false` onto an enabled lane 7, 6, 6 and 6 times (at page load, at\n"
        "    each trigger and at the census's own release after T-apply), once `true`",
        "  - **The gate wrote 8 or 9 times per run**: `false` onto an enabled lane 7, 6, 6 and 6 times (two at page load,\n"
        "    one at T-gate, two or three at T-tab, one at the census's own release after T-apply, and none at T-mode),\n"
        "    once `true`",
    ),
    # --- the pacer-live README sentence, and the READMEs' slips (R2A-3) ---
    (
        "run on dash 4.2.0 (`JuniperCanopy1`). The README in `reports/e2e-canopy-2026-09-02/pacer-live/` states what each\n"
        "leg served and how it is known; this phase's readings agree with it.",
        "run on dash 4.2.0 (`JuniperCanopy1`). The README in `reports/e2e-canopy-2026-09-02/pacer-live/` states what each\n"
        "leg served and how it is known; this phase's readings agree with it on what each leg served, and qualify its\n"
        "commit-2 discriminator below. Two slips in the two evidence READMEs, found by this phase's review, are corrected\n"
        "by its round-2 pass, outside the reviewed files: the pacer-live README's table called census runs 1 to 4 the\n"
        "\"F-055 census\", and the renderer-check README dated the first two runs 17:40–17:54 CDT, where their requests ran\n"
        "17:29–17:41 (round 2, Lane 12-R2A; round 1, Lanes 12-A and 12-C).",
    ),
    # --- the cost: as much as 49–52 s (R2B-6) ---
    (
        "the 16–17 s in-flight times of census runs 1 and 2 would\n"
        "  have set it to 49–52 s (round 1, Lane 12-B).",
        "the 16–17 s in-flight times of census runs 1 and 2 would\n"
        "  have set it to as much as 49–52 s, the pacer's own round trip being a lower bound (round 1, Lane 12-B; round\n"
        "  2, Lane 12-R2B).",
    ),
    # --- the squash's check runs (R2B-5) ---
    (
        "and CI on the squash passed (46 check runs, 7 skipped).",
        "and CI on the squash passed (53 check runs: 46 successful, 7 skipped).",
    ),
    # --- item 18's cost wording (R2B-2) ---
    (
        "poll waits out its stale bound, at least 30 s and at most 120 s, counted from the request. The drives that item",
        "poll's request is re-issued after its stale bound, at least 30 s and at most 120 s counted from the request,\n"
        "  and answered a tick and a round trip later. The drives that item",
    ),
    # --- item 27: what a demo drive can establish (R2B-1) ---
    (
        "    switch enabled while a run is active and disabled after the stop. Record the result in F-CANOPY-025's and\n"
        "    F-CANOPY-055's entries.",
        "    switch enabled while a run is active and disabled after the stop. A demo drive can show that the arm reaches\n"
        "    the paced bar; as Phase 9 found, it cannot discriminate from the old code, which also got responses through\n"
        "    on a demo page. Phase 9's item 0 asked for a leg \"where the old code fails\", which failed only at the trio's\n"
        "    latency on a page that does not train; that ask has no venue and is unmet by design (round 2, Lane 12-R2B).\n"
        "    Record the result in F-CANOPY-025's and F-CANOPY-055's entries.",
    ),
    # --- round 1's record: the probes' figures (R2A-1) ---
    (
        "and none produced a figure the ledger now rests on that the archived readers do\n"
        "    not reproduce.",
        "and none produced a figure the ledger now rests on that a `json` reading of the\n"
        "    archived files does not reproduce.",
    ),
    # --- round 1's record: which findings changed numbers (R2A-4c, R2B-7a) ---
    (
        "- **Verdicts.** All three returned SOUND-WITH-FIXES. Lane 12-A's and Lane 12-B's first findings change numbers in\n"
        "  the phase text (the gate's writes, and the first renderer runs' times),",
        "- **Verdicts.** All three returned SOUND-WITH-FIXES. Lane 12-A's first two findings and Lane 12-B's first change\n"
        "  numbers in the phase text (the gate's writes, and the first renderer runs' times),",
    ),
    # --- round 1's record: Lane 12-B's run-2 count (R2A-4b, R2B-7b) ---
    (
        "    and 6, with a request in flight at 5, 5, 5 and 2 of those; the draft had counted the clamp's two writes among\n"
        "    them and said \"most\" for run 4 (Lanes 12-A and 12-B);",
        "    and 6, with a request in flight at 5, 5, 5 and 2 of those; the draft had counted the clamp's two writes among\n"
        "    them and said \"most\" for run 4 (Lanes 12-A and 12-B; Lane 12-B's 4 in flight for run 2 was not adopted, both\n"
        "    the orchestrator's reader and the archived one giving 5);",
    ),
    # --- round 1's record: the final run (R2A-4a, R2B-7c) ---
    (
        "measured at 3.0–4.7 s\n"
        "    to issue in the renderer check, recorded under",
        "measured at 3.0–4.7 s\n"
        "    to issue in the renderer check's final run, recorded under",
    ),
    # --- round 1's record: the handoff's item-4 echo (R2A-4c) ---
    (
        "  - the handoff: where items 25, 27 and 28 run, and four references that lacked filenames (Lane 12-C).",
        "  - the handoff: where items 25, 27 and 28 run, four references that lacked filenames, and item 4's echo of\n"
        "    item 27's history (Lane 12-C).",
    ),
    # --- round 1's record: when Lane 12-C's finding 5 is checked (R2B-3) ---
    (
        "  Lane 12-C's finding 5, that the handoff describes a landing that has not happened, is checked after the PR\n"
        "  lands, as that finding asks.",
        "  Lane 12-C's finding 5, that the handoff describes a landing that has not happened, is checked once the commits\n"
        "  land, before the PR is marked ready, as that finding asks.",
    ),
    # --- the round-2 record, after round 1's ---
    (
        "- **Slips.** None reported.\n\n\n### Matrix effect and counts",
        "- **Slips.** None reported.ROUND2_RECORD\n\n### Matrix effect and counts",
    ),
]

HANDOFF_SUBS = [
    (
        "**Consensus**: Phase 12 went through CONSENSUS_ROUNDS_PENDING.",
        "**Consensus**: two rounds on 2026-10-19 (three lanes, then two on the corrections); round 2 changed no number,\n"
        "disposition or action, so the review ended there.",
    ),
    (
        "  - The cost (a failure outside a feeder's `try` waits out the stale bound, 30–120 s) is recorded.",
        "  - The cost (a failure outside a feeder's `try` is re-issued after the stale bound, 30–120 s, and answered a tick\n"
        "    and a round trip later) is recorded.",
    ),
    (
        "item 18's watchdog note is corrected\n"
        "    (a restart now waits out the stale bound); item 24's reader change is dropped with a reason.",
        "item 18's watchdog note is corrected\n"
        "    (a restart now waits for the stale bound, then a tick and a round trip); item 24's reader change is dropped\n"
        "    with a reason.",
    ),
    (
        "   experimental-functions toggle on. Record in F-CANOPY-025's and F-CANOPY-055's entries.",
        "   experimental-functions toggle on. It can show the arm reaches the paced bar; it cannot discriminate from the old\n"
        "   code (Phase 9). Record in F-CANOPY-025's and F-CANOPY-055's entries.",
    ),
    (
        "- **This session's PR** carries the ledger, this file, the parent's item 4, the INDEX's P2 row, the SUPERSEDED banner\n"
        "  on the 2026-10-08 handoff, and Phase 12's consensus records.",
        "- **This session's PR** carries the ledger, this file, the parent's item 4, the INDEX's P2 row, the SUPERSEDED banner\n"
        "  on the 2026-10-08 handoff, Phase 12's consensus records (two rounds: briefs, verbatim reports, replayable\n"
        "  passes), and two one-line corrections to the evidence READMEs.",
    ),
    (
        "  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-08_canopy-pacer-731-landed-phase12-owed.md`: the\n"
        "    SUPERSEDED banner.",
        "  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-08_canopy-pacer-731-landed-phase12-owed.md`: the\n"
        "    SUPERSEDED banner;\n"
        "  - `reports/e2e-canopy-2026-09-02/pacer-live/README.md` (its table's \"F-055 census\" label on the F-058 runs, and\n"
        "    the commit-2 discriminator) and `reports/e2e-canopy-2026-09-02/pacer-renderer-check/README.md` (the first\n"
        "    runs' times).",
    ),
]

README_LIVE_SUBS = [
    (
        "| F-055 census, run 1, run 2 | 17:43–18:47 |",
        "| F-058 census v2, run 1, run 2 (the table said \"F-055 census\" until 2026-10-19, ledger Phase 12) | 17:43–18:47 |",
    ),
    (
        "| F-055 census (v2), run 3 | 19:02–19:33 | commit 2's tree (`b344ff97`'s content) | the page carried `__junPollPacerLastUnacked`, which only commit 2 has |",
        "| F-058 census v2, run 3 | 19:02–19:33 | commit 2's tree (`b344ff97`'s content) | the leg's `build_date`, 2026-10-09T00:02:18Z (`2026-10-08_status_bar_apply_census_8052_pacer_v2.json`), sixteen seconds after commit 2 and before commit 3, on the assumption that the leg does not reload its source; and the page carried `__junPollPacerLastUnacked`, which commit 1 lacks (this cell said \"which only commit 2 has\" until 2026-10-19; commits 3 to 5 keep the name: ledger Phase 12) |",
    ),
    (
        "| F-055 census (final), run 4 | 19:33–20:04 |",
        "| F-058 census v2, run 4 | 19:33–20:04 |",
    ),
]

README_RENDERER_SUBS = [
    (
        "**The first two runs (17:40–17:54 CDT) predate commit 1 of canopy#731.**",
        "**The first two runs (17:29–17:41 CDT; this said 17:40–17:54 until 2026-10-19, their file names carrying their end times: ledger Phase 12) predate commit 1 of canopy#731.**",
    ),
    (
        "Both arms ran concurrently, 17:40–17:54 CDT, beside two canopy unit suites",
        "Both arms ran concurrently, 17:29–17:41 CDT, beside two canopy unit suites",
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
    if "- **Round 1**: three lanes on the frozen `c626e847`" not in ledger or "- **Round 2**: two lanes on the frozen `190c896c`" in ledger:
        raise SystemExit("this is not the round-2 freeze (190c896c)")
    files = {
        "ledger": (LEDGER, ledger, LEDGER_SUBS),
        "handoff": (HANDOFF, HANDOFF.read_text(encoding="utf-8"), HANDOFF_SUBS),
        "readme-live": (README_LIVE, README_LIVE.read_text(encoding="utf-8"), README_LIVE_SUBS),
        "readme-renderer": (README_RENDERER, README_RENDERER.read_text(encoding="utf-8"), README_RENDERER_SUBS),
    }
    n_readme = len(README_LIVE_SUBS) + len(README_RENDERER_SUBS)
    record = ROUND2_RECORD.replace("SUB_COUNT_LEDGER", str(len(LEDGER_SUBS))).replace("SUB_COUNT_HANDOFF", str(len(HANDOFF_SUBS))).replace("SUB_COUNT_README", str(n_readme))
    out = {}
    for label, (path, text, subs) in files.items():
        new = apply(text, subs, label)
        if label == "ledger":
            if new.count("ROUND2_RECORD") != 1:
                raise SystemExit("round-2 record placeholder not found exactly once")
            new = new.replace("ROUND2_RECORD", record)
        print(f"{label}: {len(subs)} substitutions, {len(text)} -> {len(new)} chars")
        out[path] = new
    if not args.check:
        for path, new in out.items():
            path.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
