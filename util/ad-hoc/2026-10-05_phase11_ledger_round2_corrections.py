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
"""Round 2's correction pass on the ledger's Phase 11 (and the evidence README), its Consensus record included.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` and
``reports/e2e-canopy-2026-09-02/f058-census-v2/README.md`` as frozen for round 2 (``b3c54692``, round 1's pass
applied to ``1b7cf44b``). Round 2's reports are archived verbatim in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md``. Every substitution
is anchored to occur exactly once.

Usage:
    python3 util/ad-hoc/2026-10-05_phase11_ledger_round2_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
README = ROOT / "reports" / "e2e-canopy-2026-09-02" / "f058-census-v2" / "README.md"

ROUND2_RECORD = """

- **Round 2**: two lanes on the frozen `b3c54692`, briefed on round 1's corrections only. Briefs are in
  `reports/e2e-canopy-2026-09-02/drafts/lane11R2A_phase11_ledger_brief.md` and
  `…/lane11R2B_phase11_ledger_corrections_brief.md`, and the reports, verbatim, in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md`.
  - Lane 11-R2A replayed round 1's pass on `1b7cf44b` and got `b3c54692` byte for byte, with no hand edit, and
    re-derived every claim the pass introduced, most of them from its own reader.
  - Lane 11-R2B was adversarial on the pass, and replayed it too.
  - Their own probes are archived as `util/ad-hoc/2026-10-05_phase11_r2_{a,b}_*.py` (16 files) by
    `util/ad-hoc/2026-10-05_archive_phase11_lane_probes.py --round 2`.
- **Verdicts.** Both returned SOUND-WITH-FIXES. Lane 11-R2A's two NITs change nothing; Lane 11-R2B's findings
  change numbers (the counts for each ruling, and the horizon) and actions (the owner's question, and item 25's
  method), so §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires
  round 3.
- **What round 2 changed:**
  - the owner's question. F-CANOPY-065's P1 rests on a shipped CHANGELOG or design-plan promise of something a
    user sees, the toast; F-CANOPY-068's on a CHANGELOG's description of an internal mechanism. So the question
    gains a second limb, and the counts are given for each ruling: 7 open P1 and 16 open P2 if both are P1, 6 and
    17 if F-CANOPY-065 alone, 5 and 18 if neither (Lane 11-R2B);
  - recorded as dissent: Lane 11-B1 rated F-CANOPY-068 P2, reading its contract, then cited from code comments
    only, as drift; its brief did not show it the CHANGELOG entry (Lane 11-R2B);
  - F-CANOPY-058's horizon. The 8 evicting re-enables evicted 1.2–2.4 s after the re-enable, when the next
    request was made; 1.3–3.7 s is when the next request entered `watched`, the three longest after the census's
    own T-tab activity. Round 1's pass had labelled the second range as the first (Lane 11-R2B);
  - item 25's method: a trigger scheduled as its own task, not run inside the renderer's dispatch, timed in the
    page and validated on the synthetic check first; and the T-gate and T-mode lag no longer attributed to the
    renderer's queue (Lanes 11-R2A and 11-R2B);
  - the release trace: an AMBIGUOUS flag for a release that more than one evicted request of a run could own, a
    fifth self-test that makes one, and an exit status of 2 on any alternation break; the replay now refuses such
    a timeline (Lane 11-R2B). Neither run has an ambiguous pairing or a break;
  - wording: the minutes' source (Lane 11-R2B); the README's self-test count and its sentence on the trio, and the
    replay's docstring (Lanes 11-R2A and 11-R2B); round 1's record, which left out the medians at 6,000 and
    7,500 ms (Lane 11-R2B); and "What the evidence cannot support", which now names the instrument's presence
    (Lane 11-R2B).
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-05_phase11_ledger_round2_corrections.py`,
    SUB_COUNT substitutions in the ledger and README_SUB_COUNT in the evidence README.
- **Re-derived by the orchestrator before applying:** F-CANOPY-065's Severity bullet and Phase 10's question,
  both naming CHANGELOG or design-plan promises; the 8 evictions, 1.2–2.4 s after their re-enables, and the three
  longest waits for the next request, each at the census's T-tab activity; Lane 11-R2B's pairing mutation, now the
  trace's fifth self-test, and the new flag's count, 0, in both runs.
- **Slips.** Lane 11-R2B's `git log --format=%B` of canopy `06d8607e` printed a co-author trailer holding a
  generic bot no-reply address, not the owner's, into its own local output. Lane 11-R2A reported none."""

SUBS = [
    # --- the owner's question, with both sources and a second limb (Lane 11-R2B, Finding 1) ---
    (
        "  F-CANOPY-065 already carries (Phase 10's Consensus record). Plan §6.3's P1 is \"breaks a documented\n"
        "  behaviour\", and canopy's shipped CHANGELOG promises the behaviour these fires break (Its own contract,\n"
        "  above). If such a promise does not count, it is P2: on its own it delays the chart by a cycle at a time,\n"
        "  which §6.3 puts under drift, and the harm a user would see comes through F-CANOPY-058, which is P1 already.\n"
        "  This phase first rated it P2 on its code comment alone; round 1 found the CHANGELOG entry (Lane 11-B2).",
        "  F-CANOPY-065 already carries (Phase 10's Consensus record). Plan §6.3's P1 is \"breaks a documented\n"
        "  behaviour\", and canopy's shipped CHANGELOG promises the behaviour these fires break (Its own contract,\n"
        "  above). If such a promise does not count, it is P2: on its own it delays the chart by a cycle at a time,\n"
        "  which §6.3 puts under drift, and the harm a user would see comes through F-CANOPY-058, which is P1 already.\n"
        "  The question has a second limb here. F-CANOPY-065's promise is of something a user sees, the toast, and\n"
        "  rests on a CHANGELOG and a design plan; this one is a CHANGELOG's description of an internal mechanism, so a\n"
        "  ruling for F-CANOPY-065 does not by itself settle it (round 2, Lane 11-R2B). This phase first rated it P2 on\n"
        "  its code comment alone; round 1 found the CHANGELOG entry (Lane 11-B2), and Lane 11-B1, which had not been\n"
        "  shown it, rated it P2 as drift.",
    ),
    (
        "  - **7 open P1:** F-CANOPY-055, F-CANOPY-058, F-CANOPY-064, F-CANOPY-065, F-CANOPY-068, F-CASCOR-001 and\n"
        "    F-CASCOR-002. F-CANOPY-065 and F-CANOPY-068 are P1 only if a shipped CHANGELOG promise counts as\n"
        "    documented; if not, the counts are 5 open P1 and 18 open P2.",
        "  - **7 open P1:** F-CANOPY-055, F-CANOPY-058, F-CANOPY-064, F-CANOPY-065, F-CANOPY-068, F-CASCOR-001 and\n"
        "    F-CASCOR-002. F-CANOPY-065 is P1 only if a shipped CHANGELOG or design-plan promise counts as documented,\n"
        "    and F-CANOPY-068 only if a CHANGELOG's description of an internal mechanism does. By ruling: both P1, 7\n"
        "    open P1 and 16 open P2, as the triage counts them; F-CANOPY-065 alone, 6 and 17; neither, 5 and 18.",
    ),
    (
        "- **Unresolved, for the owner:** whether a shipped CHANGELOG promise counts as documented under plan §6.3, which\n"
        "  now decides two ratings, F-CANOPY-065's and F-CANOPY-068's.",
        "- **Unresolved, for the owner:** Phase 10's question, whether a shipped CHANGELOG or design-plan promise counts\n"
        "  as documented under plan §6.3, which decides F-CANOPY-065's rating; and, since round 2 (Lane 11-R2B), a second\n"
        "  limb, whether a CHANGELOG's description of an internal mechanism counts as documented behaviour, which decides\n"
        "  F-CANOPY-068's.",
    ),
    # --- F-CANOPY-058's horizon: when the next request was MADE (Lane 11-R2B, Finding 2) ---
    (
        "  mid-request re-enables, 8 evicted: a re-enable evicts only if the in-flight response has not landed by the time\n"
        "  the renderer makes the next request, 1.3–3.7 s after the re-enable in those runs, so \"more than one period\n"
        "  before the in-flight response lands\" (the header until Phase 11's round 1) was too wide. The re-enables were\n"
        "  the strand watchdog's false fires (28, of which 7 evicted; filed as F-CANOPY-068), the gate's write at page\n",
        "  mid-request re-enables, 8 evicted: a re-enable evicts only if the in-flight response has not landed by the time\n"
        "  the renderer makes the next request. The 8 evicted 1.2–2.4 s after the re-enable; after the other 24 the\n"
        "  answer had landed first, 0.1–2.2 s after it. So \"more than one period before the in-flight response lands\"\n"
        "  (the header until Phase 11's round 1) was too wide. The re-enables were the strand watchdog's false fires\n"
        "  (28, of which 7 evicted; filed as F-CANOPY-068), the gate's write at page\n",
    ),
    (
        "  in-flight request if its response has not landed by then: 1.3–3.7 s after the re-enable in Phase 11's runs.\n",
        "  in-flight request if its response has not landed by then (in Phase 11's runs, the evictions came 1.2–2.4 s\n"
        "  after the re-enable).\n",
    ),
    (
        "  a fire. Across all 32 mid-request re-enables, the 28 fires and 4 gate writes, 8 evicted, and the next request\n"
        "  entered `watched` 1.3–3.7 s after the re-enable.",
        "  a fire. Across all 32 mid-request re-enables, the 28 fires and 4 gate writes, 8 evicted, 1.2–2.4 s after the\n"
        "  re-enable, when the next request was made. The next request entered `watched` 1.3–3.7 s after a re-enable;\n"
        "  the three longest waits came at the census's own T-tab activity, and without them the range is 1.3–2.6 s.",
    ),
    # --- the minutes' source (Lane 11-R2B, Finding 5) ---
    (
        "  without an applied answer, and the minutes below were reached only in Lane B's synthetic runs. Read one",
        "  without an applied answer, and the minutes below were reached only in synthetic repros (Lanes B and B1). Read one",
    ),
    # --- item 25's method and the lag attribution (Lanes 11-R2A and 11-R2B) ---
    (
        "  - **Its scripted triggers took effect 1.3–4.2 s after they fired.** For T-gate and T-mode that was the\n"
        "    renderer's queue: 1.3–1.4 s to the gate's write, and 2.1–2.5 s to the next request. For T-tab most of it was\n"
        "    the driver's own: its clicks ran 0.7–1.0 s and 2.3–2.9 s after the trigger fired (its 1 s wait between them\n"
        "    took 1.6–1.9 s), and each gate write followed its click by 0.3–1.9 s (Lanes 11-A2, 11-A3 and 11-B2). Each",
        "  - **Its scripted triggers took effect 1.3–4.2 s after they fired.** For T-gate and T-mode the transcript does\n"
        "    not separate the driver's round trip from the renderer's queue: 1.3–1.4 s to the gate's write, and 2.1–2.5 s\n"
        "    to the next request (round 2, Lane 11-R2A). For T-tab, 0.7–1.0 s and 2.3–2.9 s passed before its clicks ran\n"
        "    in the page (its 1 s wait between them took 1.6–1.9 s), and each gate write followed its click by 0.3–1.9 s\n"
        "    (Lanes 11-A2, 11-A3 and 11-B2). Each",
    ),
    (
        "    were too short to see a later effect. To test the claim, a trigger has to fire inside the page as a request\n"
        "    enters `watched` (a trigger sent from Python then would still land 1.0–2.9 s into the flight), and be scored\n"
        "    as \"a re-enable while a request is in flight, whose response lands after the next request is made\", not\n"
        "    within a fixed horizon.",
        "    were too short to see a later effect. To test the claim, a trigger has to be fired from the page itself as a\n"
        "    request enters `watched`, scheduled as its own task rather than run inside the renderer's dispatch, which\n"
        "    could reorder what it measures (round 2, Lane 11-R2B); a trigger sent from Python then may land 1.0–2.9 s\n"
        "    into the flight, if T-tab's delays above are the driver's. It must be scored as \"a re-enable while a request\n"
        "    is in flight, whose response lands after the next request is made\", not within a fixed horizon.",
    ),
    (
        "25. **The census's triggers.** Fire each inside the page, from the shim's `AddWatched` hook, as a request enters\n"
        "    `watched`; timestamp every action in the page; and score each as described under Instruments. Then run, on",
        "25. **The census's triggers.** Fire each from the page itself when the shim sees a request enter `watched`,\n"
        "    scheduled as its own task (for example `setTimeout(…, 0)`), never synchronously inside the renderer's\n"
        "    dispatch, which could reorder what it measures; timestamp every action's execution in the page; validate the\n"
        "    method on the synthetic check before a live run; and score each as described under Instruments. Then run, on",
    ),
    # --- the release trace's new flag and fifth self-test (Lane 11-R2B, Finding 4) ---
    (
        "    release then silently re-paired every later eviction (Lane 11-A3). Its `--self-test` builds four known\n"
        "    answers from the transcript itself: with the late releases removed, every eviction reads \"none\"; with a fire\n"
        "    placed 31 s into the run's longest disabled episode (each run's Apply clamp, 62 s and 63 s), that fire reads\n"
        "    0 ms enabled; with one late release dropped, only its eviction changes; and with every late release whose\n"
        "    successor was answered shifted into that successor's own window, exactly those evictions change. All four\n"
        "    pass on both transcripts.",
        "    release then silently re-paired every later eviction (Lane 11-A3). The successor rule can still guess: an\n"
        "    evicted request whose response lands after its successor was itself evicted would read \"none\" while its\n"
        "    release went to the successor. So since round 2 a release is flagged AMBIGUOUS when another evicted request\n"
        "    of the same run was still awaiting a release (Lane 11-R2B); there are none in either run. Its `--self-test`\n"
        "    builds five known answers from the transcript itself: with the late releases removed, every eviction reads\n"
        "    \"none\"; with a fire placed 31 s into the run's longest disabled episode (each run's Apply clamp, 62 s and\n"
        "    63 s), that fire reads 0 ms enabled; with one late release dropped, only its eviction changes; with every\n"
        "    late release whose successor was answered shifted into that successor's own window, exactly those\n"
        "    evictions change; and with one release moved into the flight after the next eviction, it is flagged\n"
        "    AMBIGUOUS. All five pass on both transcripts. An alternation break in the innermost records makes it exit 2,\n"
        "    and makes the replay refuse.",
    ),
    (
        "  the runs. One of the trace's four self-tests removes the late releases from a copy of each transcript, and\n"
        "  then reads every eviction as \"late release: none\" (Instruments).",
        "  the runs. One of the trace's five self-tests removes the late releases from a copy of each transcript, and\n"
        "  then reads every eviction as \"late release: none\" (Instruments).",
    ),
    # --- round 1's record: the medians it left out (Lane 11-R2B, Finding 5) ---
    (
        "    about 2.7 s disabled per cycle (was 2.8), and the replay's medians: 9 and 7 in phase and 1 at random, with no\n"
        "    fire in about one random replay in five (were 9 and 8, 2, and one in six);",
        "    about 2.7 s disabled per cycle (was 2.8), and the replay's medians: 9 and 7 in phase and 1 at random, with no\n"
        "    fire in about one random replay in five (were 9 and 8, 2, and one in six), and 1 to 3.5 at 6,000 and\n"
        "    7,500 ms (were 2 to 4; added in round 2, Lane 11-R2B);",
    ),
    # --- What the evidence cannot support: the instrument's presence (Lane 11-R2B, Finding 2) ---
    (
        "  canopy. The watchdog's other samples were not logged, so its aliasing is inferred, though the replay and the\n"
        "  fires' spacing support it.",
        "  canopy. The watchdog's other samples were not logged, so its aliasing is inferred, though the replay and the\n"
        "  fires' spacing support it. And every timing here comes from a page running the shim, which wraps every\n"
        "  dispatch (165,942 in the first run), with no uninstrumented control (round 2, Lane 11-R2B).ROUND2_RECORD",
    ),
]

README_SUBS = [
    (
        "  set, 2026-10-05 21:11–21:36Z. The trio's three processes were the same before and after it.",
        "  set, 2026-10-05 21:11–21:36Z. The trio's three processes, started 2026-09-22, were still the same after it,\n"
        "  by their pids and start times, read then; no file here records that reading.",
    ),
    (
        "\"$T\" --self-test   # both known-answer mutations",
        "\"$T\" --self-test   # five known-answer mutations",
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
    if "- **Round 1**: five lanes on the frozen `1b7cf44b`" not in before or "- **Round 2**: two lanes on the frozen `b3c54692`" in before:
        raise SystemExit("this is not the round-2 freeze (b3c54692)")
    after = apply(before, SUBS)
    record = ROUND2_RECORD.replace("README_SUB_COUNT", str(len(README_SUBS))).replace("SUB_COUNT", str(len(SUBS)))
    if after.count("ROUND2_RECORD") != 1:
        raise SystemExit("round-2 record placeholder not found exactly once")
    after = after.replace("ROUND2_RECORD", record)
    readme_after = apply(README.read_text(encoding="utf-8"), README_SUBS)
    print(f"ledger: {len(SUBS)} substitutions, {len(before)} -> {len(after)} chars; README: {len(README_SUBS)} substitutions")
    if not args.check:
        LEDGER.write_text(after, encoding="utf-8")
        README.write_text(readme_after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
