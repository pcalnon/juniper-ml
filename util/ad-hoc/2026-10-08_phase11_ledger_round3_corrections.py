#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-08
# Status      : ad-hoc — one-off correction pass; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Round 3's correction pass on the ledger's Phase 11, the evidence README and the two readers' docstrings.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md``,
``reports/e2e-canopy-2026-09-02/f058-census-v2/README.md``,
``util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py`` and ``util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py``
as frozen for round 3 (``7af6a381``, round 2's pass applied to ``b3c54692``). Round 3's reports are archived
verbatim in ``reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md``. The
numbers it introduces were re-derived first by ``util/ad-hoc/2026-10-08_phase11_round3_rederive.py``. The
readers' changes are to docstrings and comments only. Every substitution is anchored to occur exactly once.

Usage:
    python3 util/ad-hoc/2026-10-08_phase11_ledger_round3_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
README = ROOT / "reports" / "e2e-canopy-2026-09-02" / "f058-census-v2" / "README.md"
TRACE = ROOT / "util" / "ad-hoc" / "2026-10-05_f058_census_v2_release_trace.py"
REPLAY = ROOT / "util" / "ad-hoc" / "2026-10-05_f058_watchdog_alias_replay.py"

ROUND3_RECORD = """

- **Round 3**: two lanes on the frozen `7af6a381`, briefed on round 2's corrections only, from one brief,
  `reports/e2e-canopy-2026-09-02/drafts/lane11R3_phase11_ledger_brief.md`. The reports, verbatim, are in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md`.
  - Lane 11-R3A re-created the measurements from the artifacts, with its own reader, and replayed round 2's pass
    on `b3c54692`: `7af6a381` byte for byte, with no hand edit.
  - Lane 11-R3B was adversarial on the pass, and replayed it too.
  - Both lanes started on 2026-10-05 and stopped part-way when the API's weekly usage limit was reached. Each was
    resumed on 2026-10-08 with its context, and each report is the lane's final message.
  - Their own probes are archived as `util/ad-hoc/2026-10-08_phase11_r3_{a,b}_*.py` (19 files) by
    `util/ad-hoc/2026-10-05_archive_phase11_lane_probes.py --round 3`.
- **Verdicts.** Both returned SOUND-WITH-FIXES. Their findings change a disposition (the condition F-CANOPY-068's
  rating is stated to rest on), numbers (the counts each ruling gives, and F-CANOPY-058's horizon as worded) and
  actions (the owner's question's reach, and items 24 and 26), so §4 of
  `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires round 4.
- **What round 3 changed:**
  - the two limbs, carried everywhere. F-CANOPY-068's header, the Summary and the Rating's lead gave the first
    limb's condition, so under a ruling for the first limb alone the header read P1 where the counts read P2.
    They now give the second limb. The first limb is now put as a promise of something a user sees, and
    F-CANOPY-065's header now names the design plan its Severity bullet already did (Lanes 11-R3A and 11-R3B);
  - the counts each ruling gives now say that they move F-CANOPY-065 and F-CANOPY-068 alone. The first limb
    also reaches F-CANOPY-057, through the CAN-015g/h design note (Lane 11-R3A), and F-CANOPY-018, through
    canopy's 0.6.0 toast entry (named by Lane 11-R3B among what it could not check), and no other open finding
    has been checked. New item 26 is the sweep;
  - F-CANOPY-058's trigger bullet. The 8 evictions a fire or gate write started came 1.2–2.4 s after it, and the
    21 that followed a late release 1.4–2.6 s after that release; the bullet had given the first range for all
    29 (Lane 11-R3B);
  - the trigger lag, attributed nowhere now. T-mode's next request is not shown to be its effect, and T-tab's
    click times are stamped after each click's own handling, so a trigger sent from Python adds at most
    0.7–1.0 s (Lane 11-R3B). The README's sentence now says the same (Lanes 11-R3A and 11-R3B);
  - the readers. Only the trace's report exits 2 on an alternation break, and a disable and enable both logged
    only by non-thunk records leave no break; item 24 now asks for a push-order comparison first (Lanes 11-R3A
    and 11-R3B). The trace's self-test docstring now says five, and the trace's docstring and the replay's
    comment state the limit;
  - wording: F-CANOPY-068's Effect gives 1.4–2.4 s for the 7 evicting fires only (Lanes 11-R3A and 11-R3B); the
    shim wraps the store's `dispatch`, not every dispatch (Lane 11-R3B); round 2's record now says the three
    longest waits came at T-tab's activity, not after it (Lane 11-R3B); and round 1's record notes the split.
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-08_phase11_ledger_round3_corrections.py`,
    SUB_COUNT substitutions in the ledger, README_SUB_COUNT in the evidence README and READER_SUB_COUNT in the readers.
- **Re-derived by the orchestrator before applying:**
  - the CAN-015g/h note's status line, its promise and its record of g-3 and g-7 as merged;
  - canopy#533, merged on 2026-08-28;
  - plan §6.3's P1, which does not define "documented";
  - all 29 evictions, each from the last re-enable before it (`util/ad-hoc/2026-10-08_phase11_round3_rederive.py`):
    8 started by a fire or gate write, 1,214–2,391 ms after it, and 21 by a late release, 1,422–2,553 ms after it,
    four of them above 2.4 s;
  - `CLICK_TAB` in `…_live.py`, which stamps the page's time after `t.click()` returns;
  - round 2's report of Lane 11-R2A's push-order walk, identical to the type selection.
- **Slips.** Neither lane reported one.
- **Before round 4, the archived probes of all three rounds were edited for CodeQL**, whose unresolved review
  threads block a merge while every check reads green. `util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py`
  made 51 edits in 44 probes, each closing a file the probe opens or dropping an import or a binding nothing
  reads, and amended each touched probe's header to say so. `util/ad-hoc/2026-10-05_codeql_python_prescreen.py`
  predicted the alerts. It reproduces the 20 CodeQL threads on Phase 10's PR, juniper-ml#2157, and reports
  nothing on Phase 10's 33 merged scripts, nor now on any of this phase's."""

SUBS = [
    # --- the two limbs: Summary, F-CANOPY-068's header, F-CANOPY-065's header, the Rating's lead (R3A F1, R3B F1) ---
    (
        "- **Filed: F-CANOPY-068 (P1 if a shipped CHANGELOG promise counts as documented, else P2; OPEN)**, the\n"
        "  watchdog's false fires. canopy's CHANGELOG for 0.8.0 promises that it re-enables the lane only once the lane\n"
        '  "has been continuously disabled" for 30 s. New findings, below, also says why it is a finding of its own\n'
        "  rather than part of F-CANOPY-058.",
        "- **Filed: F-CANOPY-068 (P1 if a CHANGELOG's description of an internal mechanism counts as documented, else\n"
        "  P2; OPEN)**, the watchdog's false fires. canopy's CHANGELOG for 0.8.0 says that it re-enables the lane only\n"
        '  once the lane "has been continuously disabled" for 30 s. New findings, below, also says why it is a finding of\n'
        "  its own rather than part of F-CANOPY-058.",
    ),
    (
        "(P1 if a shipped CHANGELOG promise counts as documented, else P2, the owner's question; canopy repo; found 2026-10-05 by the F-CANOPY-058 census;",
        "(P1 if a CHANGELOG's description of an internal mechanism counts as documented, else P2, the second limb of the owner's question; canopy repo; found 2026-10-05 by the F-CANOPY-058 census;",
    ),
    (
        "(P1 if a shipped CHANGELOG promise counts as documented, else P2, the owner's question; canopy repo; observed 2026-09-23",
        "(P1 if a shipped CHANGELOG or design-plan promise counts as documented, else P2, the first limb of the owner's question; canopy repo; observed 2026-09-23",
    ),
    (
        "- **Rating: P1 if a shipped CHANGELOG promise counts as documented, else P2**, the owner's question that\n"
        "  F-CANOPY-065 already carries (Phase 10's Consensus record). Plan §6.3's P1 is \"breaks a documented\n"
        "  behaviour\", and canopy's shipped CHANGELOG promises the behaviour these fires break (Its own contract,\n"
        "  above). If such a promise does not count, it is P2: on its own it delays the chart by a cycle at a time,\n"
        "  which §6.3 puts under drift, and the harm a user would see comes through F-CANOPY-058, which is P1 already.\n"
        "  The question has a second limb here. F-CANOPY-065's promise is of something a user sees, the toast, and\n"
        "  rests on a CHANGELOG and a design plan; this one is a CHANGELOG's description of an internal mechanism, so a\n"
        "  ruling for F-CANOPY-065 does not by itself settle it (round 2, Lane 11-R2B).",
        "- **Rating: P1 if a CHANGELOG's description of an internal mechanism counts as documented, else P2**, the\n"
        "  second limb of the owner's question; its first limb, from Phase 10's Consensus record, decides F-CANOPY-065.\n"
        "  Plan §6.3's P1 is \"breaks a documented behaviour\", and canopy's shipped CHANGELOG describes the behaviour\n"
        "  these fires break (Its own contract, above). If such a description does not count, it is P2: on its own it\n"
        "  delays the chart by a cycle at a time, which §6.3 puts under drift, and the harm a user would see comes\n"
        "  through F-CANOPY-058, which is P1 already. The limbs differ: F-CANOPY-065's promise is of something a user\n"
        "  sees, the toast, and rests on a CHANGELOG and a design plan; this one is a CHANGELOG's description of an\n"
        "  internal mechanism, so a ruling for F-CANOPY-065 does not by itself settle it (round 2, Lane 11-R2B; carried\n"
        "  into this rating's lead, the header and the Summary in round 3, Lanes 11-R3A and 11-R3B).",
    ),
    # --- F-CANOPY-058's trigger bullet: the 8 trigger-started evictions vs the 21 within the runs (R3B F2) ---
    (
        "(in Phase 11's runs, the evictions came 1.2–2.4 s\n  after the re-enable).",
        "(in Phase 11's runs, the 8 evictions a fire or gate\n"
        "  write started came 1.2–2.4 s after it, and the 21 that followed a late release came 1.4–2.6 s after that\n"
        "  release).",
    ),
    (
        "The successors were evicted in turn 21 times and\n  answered 8 times, which ended the eight runs.",
        "The successors were evicted in turn 21 times, each\n  1.4–2.6 s after the late release, and answered 8 times, which ended the eight runs.",
    ),
    # --- F-CANOPY-068's Effect: 1.4–2.4 s holds for the 7 evicting fires only (R3A F4, R3B F5) ---
    (
        "  response in flight has not landed when the next request is made, 1.4–2.4 s after the fire in these runs, that\n"
        "  response is evicted. 7 of the 28 fires evicted a response. Through",
        "  response in flight has not landed when the next request is made, that response is evicted. 7 of the 28 fires\n"
        "  evicted a response, each 1.4–2.4 s after the fire. Through",
    ),
    # --- Instruments: the readers' alternation guard (R3A F5, R3B F8) ---
    (
        "An alternation break in the innermost records makes it exit 2,\n    and makes the replay refuse.",
        "An alternation break in the innermost records makes its report\n"
        "    exit 2, and makes the replay refuse; `--self-test` does not check for one. A disable and the enable after it,\n"
        "    both logged only by non-thunk records, would leave no break, and neither reader would see them. In these runs\n"
        "    a walk of the records in push order finds the same changes as the type selection (Lanes 11-R2A and 11-R3A),\n"
        "    and item 24 asks the readers to make that comparison themselves (round 3, Lanes 11-R3A and 11-R3B).",
    ),
    # --- Instruments: the trigger lag, attributed nowhere (R3B F4) ---
    (
        "  - **Its scripted triggers took effect 1.3–4.2 s after they fired.** For T-gate and T-mode the transcript does\n"
        "    not separate the driver's round trip from the renderer's queue: 1.3–1.4 s to the gate's write, and 2.1–2.5 s\n"
        "    to the next request (round 2, Lane 11-R2A). For T-tab, 0.7–1.0 s and 2.3–2.9 s passed before its clicks ran\n"
        "    in the page (its 1 s wait between them took 1.6–1.9 s), and each gate write followed its click by 0.3–1.9 s\n"
        "    (Lanes 11-A2, 11-A3 and 11-B2). Each\n"
        "    trigger fired on",
        "  - **Its scripted triggers took effect 1.3–4.2 s after they fired.** T-gate's write landed 1.3–1.4 s after it\n"
        "    fired, and the transcript does not separate the driver's round trip from the renderer's queue (round 2, Lane\n"
        "    11-R2A). After T-mode fired, the next request entered 2.1–2.5 s later, and the transcript does not record\n"
        "    what made it. T-tab's clicks had returned in the page 0.7–1.0 s and 2.3–2.9 s after it fired, each stamped\n"
        "    after the click's own handling (its 1 s wait between them took 1.6–1.9 s), and each gate write followed its\n"
        "    click's return by 0.3–1.9 s (Lanes 11-A2, 11-A3 and 11-B2; where the stamp is taken, round 3, Lane 11-R3B).\n"
        "    Each trigger fired on",
    ),
    (
        "could reorder what it measures (round 2, Lane 11-R2B); a trigger sent from Python then may land 1.0–2.9 s\n"
        "    into the flight, if T-tab's delays above are the driver's. It must be scored as",
        "could reorder what it measures (round 2, Lane 11-R2B). Sent from Python instead, it would land later by the\n"
        "    driver's round trip, at most the 0.7–1.0 s before T-tab's first click had returned (round 3, Lane 11-R3B).\n"
        "    It must be scored as",
    ),
    # --- the round-1 record notes the split (R3B F1) ---
    (
        "    11-B2), the owner's question F-CANOPY-065 already carries. The counts move to 7 open P1 and 16 open P2.",
        "    11-B2), the owner's question F-CANOPY-065 already carries; round 2 split that question, and this is now its\n"
        "    second limb. The counts move to 7 open P1 and 16 open P2.",
    ),
    # --- Unresolved: limb 1 is a promise of something a user sees, and reaches further (R3A F2, R3B F1) ---
    (
        "- **Unresolved, for the owner:** Phase 10's question, whether a shipped CHANGELOG or design-plan promise counts\n"
        "  as documented under plan §6.3, which decides F-CANOPY-065's rating; and, since round 2 (Lane 11-R2B), a second\n"
        "  limb, whether a CHANGELOG's description of an internal mechanism counts as documented behaviour, which decides\n"
        "  F-CANOPY-068's.",
        "- **Unresolved, for the owner:** Phase 10's question, whether a shipped CHANGELOG's or a design plan's promise\n"
        "  of something a user sees counts as documented under plan §6.3, which decides F-CANOPY-065's rating; and, since\n"
        "  round 2 (Lane 11-R2B), a second limb, whether a CHANGELOG's description of an internal mechanism counts as\n"
        "  documented behaviour, which decides F-CANOPY-068's. Since round 3 (Lanes 11-R3A and 11-R3B), the first limb\n"
        "  is known to reach further than F-CANOPY-065 (Matrix effect and counts; item 26).",
    ),
    # --- What the evidence cannot support: the shim wraps the store's dispatch (R3B F6) ---
    (
        "which wraps every\n  dispatch (165,942 in the first run)",
        "which wraps the\n  store's `dispatch` (165,942 calls in the first run)",
    ),
    # --- the round-2 record: the three longest waits came AT T-tab's activity (R3B F7) ---
    (
        "the three longest after the census's\n    own T-tab activity.",
        "the three longest at the census's\n    own T-tab activity.",
    ),
    # --- the round-3 record, after round 2's slips ---
    (
        "  generic bot no-reply address, not the owner's, into its own local output. Lane 11-R2A reported none.",
        "  generic bot no-reply address, not the owner's, into its own local output. Lane 11-R2A reported none.ROUND3_RECORD",
    ),
    # --- Matrix effect and counts: the counts move two findings only; the first limb reaches further (R3A F2) ---
    (
        "    F-CASCOR-002. F-CANOPY-065 is P1 only if a shipped CHANGELOG or design-plan promise counts as documented,\n"
        "    and F-CANOPY-068 only if a CHANGELOG's description of an internal mechanism does. By ruling: both P1, 7\n"
        "    open P1 and 16 open P2, as the triage counts them; F-CANOPY-065 alone, 6 and 17; neither, 5 and 18.",
        "    F-CASCOR-002. F-CANOPY-065 is P1 only if a shipped CHANGELOG's or a design plan's promise of something a user\n"
        "    sees counts as documented, and F-CANOPY-068 only if a CHANGELOG's description of an internal mechanism does.\n"
        "    Moving those two alone, by ruling: both P1, 7 open P1 and 16 open P2, as the triage counts them;\n"
        "    F-CANOPY-065 alone, 6 and 17; neither, 5 and 18.\n"
        "  - **A ruling may move more than those two** (round 3, Lanes 11-R3A and 11-R3B). No other open finding has been\n"
        "    checked against canopy's CHANGELOG or the design plans, and two open P2s are already known to be within\n"
        "    reach of the first limb:\n"
        "    - F-CANOPY-057, through the CAN-015g/h design note\n"
        "      (`JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`). Marked \"Implemented\", it\n"
        "      promises \"decision-boundary animation with per-unit weight evolution\" and records every CAN-015g item as\n"
        "      merged to `main`, g-3 included, which never reached it (F-CANOPY-057's History). canopy's manual and FAQ\n"
        "      have said since canopy#684 that no weight reaches the page;\n"
        "    - F-CANOPY-018, through the apply toast that canopy's 0.6.0 CHANGELOG promises, the entry F-CANOPY-065 rests\n"
        "      on. Its fix, canopy#533, merged on 2026-08-28 and awaits a live re-drive.\n"
        "    - Item 26 is the sweep, owed with the ruling.",
    ),
    # --- Still owed: item 24 gains the readers' push-order check (R3B F8); item 26, the ruling's reach (R3A F2) ---
    (
        "    watchdog, measure its rate during a run as well, with a live stream in the window view and in a full view.",
        "    watchdog, measure its rate during a run as well, with a live stream in the window view and in a full view.\n"
        "    Before those runs, make the release trace and the replay compare a walk of the lane records in push order\n"
        "    with their type selection, and exit 2 on any difference, and make `--self-test` refuse a transcript with an\n"
        "    alternation break (round 3, Lane 11-R3B).",
    ),
    (
        "    switch, the end of an Apply (with the clamp defeat) and a second-Input change in mid-request.\n",
        "    switch, the end of an Apply (with the clamp defeat) and a second-Input change in mid-request.\n"
        "26. **The reach of the owner's §6.3 ruling.** Once the owner rules, check each open finding not yet rated on a\n"
        "    CHANGELOG or a design plan for a promise, of a kind the ruling counts, of the behaviour it breaks. Start with\n"
        "    F-CANOPY-057 and F-CANOPY-018 (Matrix effect and counts), and re-rate what the ruling reaches. Whatever the\n"
        "    ruling, the CAN-015g/h design note's \"every CAN-015g item has merged to `main`\" needs a dated correction:\n"
        "    g-3 never reached cascor `main` (F-CANOPY-057's History).\n",
    ),
]

README_SUBS = [
    (
        "Its scripted triggers take effect 1.3–4.2 s after they fire, partly through the renderer's queue and, for\n"
        "T-tab, mostly through the driver's own late clicks, so as written they cannot test a mid-request re-enable\n"
        "(the ledger's Phase 11, Instruments).",
        "Its scripted triggers take effect 1.3–4.2 s after they fire, a delay the transcript does not split between the\n"
        "driver and the page, so as written they cannot test a mid-request re-enable (the ledger's Phase 11,\n"
        "Instruments).",
    ),
]

READER_SUBS = [
    (
        TRACE,
        "  2026-10-05 runs. A lane change logged only by a non-thunk record would be missing from the innermost timeline;\n"
        "  the report counts alternation breaks and exits 2 if there is any.",
        "  2026-10-05 runs. A lane change logged only by a non-thunk record would be missing from the innermost timeline;\n"
        "  the report counts alternation breaks and exits 2 if there is any. A disable and the enable after it, both\n"
        "  logged only so, leave no break and are not caught, and ``--self-test`` does not check for a break (round 3 of\n"
        "  Phase 11's review, Lanes 11-R3A and 11-R3B). In the 2026-10-05 runs a walk of the records in push order\n"
        "  finds the same changes as this selection (Lanes 11-R2A and 11-R3A).",
    ),
    (
        TRACE,
        '    """Two mutated copies of the transcript, each with a known answer, so this reader is shown able to fail."""',
        '    """Five mutated copies of the transcript, each with a known answer, so this reader is shown able to fail."""',
    ),
    (
        REPLAY,
        "        # A lane change logged only by a non-thunk record would be missing from the timeline (round 2 of Phase 11's\n"
        "        # review, Lane 11-R2B), and every replayed fire would rest on a timeline with holes in it.",
        "        # A lane change logged only by a non-thunk record would be missing from the timeline (round 2 of Phase 11's\n"
        "        # review, Lane 11-R2B), and every replayed fire would rest on a timeline with holes in it. A disable and the\n"
        "        # enable after it, both logged only so, leave no break and are not caught here (round 3, Lane 11-R3B).",
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
    if "- **Round 2**: two lanes on the frozen `b3c54692`" not in before or "- **Round 3**: two lanes on the frozen `7af6a381`" in before:
        raise SystemExit("this is not the round-3 freeze (7af6a381)")
    after = apply(before, SUBS)
    record = ROUND3_RECORD.replace("README_SUB_COUNT", str(len(README_SUBS))).replace("READER_SUB_COUNT", str(len(READER_SUBS))).replace("SUB_COUNT", str(len(SUBS)))
    if after.count("ROUND3_RECORD") != 1:
        raise SystemExit("round-3 record placeholder not found exactly once")
    after = after.replace("ROUND3_RECORD", record)
    readme_after = apply(README.read_text(encoding="utf-8"), README_SUBS)
    readers = {}
    for path, old, new in READER_SUBS:
        readers[path] = apply(readers.get(path, path.read_text(encoding="utf-8")), [(old, new)])
    for path, text in readers.items():
        compile(text, path.name, "exec")
    print(f"ledger: {len(SUBS)} substitutions, {len(before)} -> {len(after)} chars; README: {len(README_SUBS)}; readers: {len(READER_SUBS)}")
    if not args.check:
        LEDGER.write_text(after, encoding="utf-8")
        README.write_text(readme_after, encoding="utf-8")
        for path, text in readers.items():
            path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
