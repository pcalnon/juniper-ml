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
"""Round 4's correction pass on the ledger's Phase 11, the evidence README and round 3's rederive script.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md``,
``reports/e2e-canopy-2026-09-02/f058-census-v2/README.md`` and the docstring of
``util/ad-hoc/2026-10-08_phase11_round3_rederive.py`` as frozen for round 4 (``adcba49f``, round 3's pass
applied to ``7af6a381``). Round 4's reports are archived verbatim in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md``. Every substitution is
anchored to occur exactly once.

Usage:
    python3 util/ad-hoc/2026-10-08_phase11_ledger_round4_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
README = ROOT / "reports" / "e2e-canopy-2026-09-02" / "f058-census-v2" / "README.md"
REDERIVE = ROOT / "util" / "ad-hoc" / "2026-10-08_phase11_round3_rederive.py"

ROUND4_RECORD = """

- **Round 4**: two lanes on the frozen `adcba49f`, briefed on round 3's corrections only, from one brief,
  `reports/e2e-canopy-2026-09-02/drafts/lane11R4_phase11_ledger_brief.md`. The reports, verbatim, are in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md`.
  - Lane 11-R4A re-created the measurements with its own reader, replayed round 3's pass on `7af6a381` (all four
    files byte for byte at `adcba49f`, no hand edit), and replayed the CodeQL pass.
  - Lane 11-R4B was adversarial on the pass, and replayed it too.
  - Both found the readers' outputs unchanged, and that the CodeQL edits change nothing a probe computes.
  - Their own probes are archived as `util/ad-hoc/2026-10-08_phase11_r4_{a,b}_*.py` (18 files) by
    `util/ad-hoc/2026-10-05_archive_phase11_lane_probes.py --round 4`. A second run of the CodeQL pass,
    `--round r4`, fixed the 7 alerts the prescreen predicted on them.
- **Verdicts.** Both returned SOUND-WITH-FIXES. Both found that the reach left out F-CANOPY-012, which changes an
  action (the reach put to the owner, and item 26), so §4 of
  `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires round 5.
- **What round 4 changed:**
  - the reach. F-CANOPY-012 is within reach of the first limb through the CAN-015g/h note, which records h-5, the
    Network Editor, as merged and specifies its output-layer "Patch weights" card, and canopy's own manual may make
    it P1 without any ruling; item 26 now checks that first. F-CANOPY-013 is recorded as unsettled. Round 3's
    record now notes the pointer it left out (Lanes 11-R4A and 11-R4B, from Lane 11-R3A's report);
  - the first limb is Phase 10's question again, worded as Phase 10, F-CANOPY-065's header and its Severity bullet
    word it, and the second limb is stated as its exception: whether it extends to a CHANGELOG's description of an
    internal mechanism. F-CANOPY-068's contract bullet and item 0 now call the `[0.8.0]` text a description (Lane
    11-R4B; Lane 11-R4A as a NIT);
  - the trigger lag. The gate and tab triggers took effect 1.3–4.2 s after they fired, and T-mode's effect is not
    recorded, now in the Summary, the Instruments and the README (Lanes 11-R4A and 11-R4B);
  - attributions. Where T-tab's stamp is taken was Lane 11-R2A's finding first (Lane 11-R4B). Of the trace's two
    modes only the report exits 2, while the replay refuses too (Lanes 11-R4A and 11-R4B). Round 3's record also
    now says that its "weekly" comes from the lanes' transcripts (Lane 11-R4B's "could not check"; Lane 11-R4A
    read it there);
  - the rederive script's docstring: the round-3 reports' file, and "was made" (Lanes 11-R4A and 11-R4B).
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-08_phase11_ledger_round4_corrections.py`,
    SUB_COUNT substitutions in the ledger, README_SUB_COUNT in the evidence README and REDERIVE_SUB_COUNT in the rederive script.
- **Re-derived by the orchestrator before applying:**
  - the CAN-015g/h note's h-5 row and its output-layer "Patch weights" card (`:627`);
  - canopy's manual at canopy#535's parent (`docs/USER_MANUAL.md:407-415` at `28da69f8^`), which lists
    `output_weights` under Patch Weights, with values entered as separated floats, and says canopy "lets CasCor
    validate the exact target shape";
  - F-CANOPY-012's entry, which rates it P2 because the failure is "loud, precise, and non-mutating" and does not
    weigh the manual;
  - canopy#535's merge, `28da69f8`, on 2026-08-28.
- **Slips.** Lane 11-R4A ran the repo's rederive script once without `-B`, which wrote one git-ignored bytecode
  file into the worktree; no tracked file changed. Lane 11-R4B ran one canopy `git log` whose format printed author
  dates, with no name or e-mail. Neither printed a secret or an address."""

SUBS = [
    # --- Summary: T-mode's effect is not recorded (R4A F5, R4B F3) ---
    (
        "- **The census's scripted triggers did not test F-CANOPY-058.** In both runs each took effect 1.3–4.2 s after it\n"
        "  fired, and each time the request it was aimed at had been answered by then (Instruments).",
        "- **The census's scripted triggers did not test F-CANOPY-058.** In both runs the gate and tab triggers took effect\n"
        "  1.3–4.2 s after they fired, after the request each was aimed at had been answered; T-mode's effect is not\n"
        "  recorded, and its targeted request was answered 0.6 s and 1.1 s after it fired (Instruments).",
    ),
    # --- F-CANOPY-068's contract: the [0.8.0] text is a description (R4B F1, R4A F2) ---
    (
        "canopy's CHANGELOG makes the\n  promise to its readers:",
        "canopy's CHANGELOG describes it\n  to its readers:",
    ),
    (
        "The threshold\n  cannot keep that promise.",
        "The watchdog\n  cannot do what that entry describes.",
    ),
    # --- the Rating's lead: the second limb as the first's exception (R4B F1, R4A F2) ---
    (
        "  second limb of the owner's question; its first limb, from Phase 10's Consensus record, decides F-CANOPY-065.\n",
        "  second limb of the owner's question: whether its first, Phase 10's question, which decides F-CANOPY-065, extends\n"
        "  to such a description.\n",
    ),
    # --- Instruments: the lead, the stamp's attribution, T-mode (R4B F3, F4a; R4A F5) ---
    (
        "  - **Its scripted triggers took effect 1.3–4.2 s after they fired.** T-gate's write landed 1.3–1.4 s after it\n"
        "    fired,",
        "  - **The gate and tab triggers took effect 1.3–4.2 s after they fired; T-mode's effect is not recorded.** T-gate's\n"
        "    write landed 1.3–1.4 s after it fired,",
    ),
    (
        "(Lanes 11-A2, 11-A3 and 11-B2; where the stamp is taken, round 3, Lane 11-R3B).",
        "(Lanes 11-A2, 11-A3 and 11-B2; where the stamp is taken, round 2, Lane 11-R2A, and round 3, Lane 11-R3B).",
    ),
    (
        "so the gate, tab and mode\n"
        "    triggers each landed after the targeted request had been answered, and TOOK's horizons (1.0 s and 2.5 s)\n"
        "    were too short to see a later effect.",
        "so the gate and tab\n"
        "    triggers each landed after the targeted request had been answered, T-mode's targeted requests were answered\n"
        "    0.6 s and 1.1 s after it fired, and TOOK's horizons (1.0 s and 2.5 s) were too short to see a later effect.",
    ),
    # --- the round-1 record: the rating now rests on the second limb (R4B F1) ---
    (
        "round 2 split that question, and this is now its\n    second limb.",
        "round 2 split that question, and F-CANOPY-068's\n    rating now rests on its second limb.",
    ),
    # --- Unresolved: Phase 10's wording, and the second limb as its exception (R4B F1, R4A F2) ---
    (
        "- **Unresolved, for the owner:** Phase 10's question, whether a shipped CHANGELOG's or a design plan's promise\n"
        "  of something a user sees counts as documented under plan §6.3, which decides F-CANOPY-065's rating; and, since\n"
        "  round 2 (Lane 11-R2B), a second limb, whether a CHANGELOG's description of an internal mechanism counts as\n"
        "  documented behaviour, which decides F-CANOPY-068's. Since round 3 (Lanes 11-R3A and 11-R3B), the first limb\n"
        "  is known to reach further than F-CANOPY-065 (Matrix effect and counts; item 26).",
        "- **Unresolved, for the owner:** Phase 10's question, whether a shipped CHANGELOG or design-plan promise counts as\n"
        "  documented under plan §6.3, which decides F-CANOPY-065's rating; and, since round 2 (Lane 11-R2B), a second\n"
        "  limb: if it does, whether that extends to a CHANGELOG's description of an internal mechanism, which decides\n"
        "  F-CANOPY-068's. Since rounds 3 and 4, the first limb is known to reach further than F-CANOPY-065 (Matrix effect\n"
        "  and counts; item 26).",
    ),
    # --- the round-3 record: what round 3 did, stated as it was; the pointer it left out; "weekly"; attributions ---
    (
        "  - Both lanes started on 2026-10-05 and stopped part-way when the API's weekly usage limit was reached. Each was\n"
        "    resumed on 2026-10-08 with its context, and each report is the lane's final message.",
        "  - Both lanes started on 2026-10-05 and stopped part-way when the API's weekly usage limit was reached, as their\n"
        "    transcripts record. Each was resumed on 2026-10-08 with its context, and each report is the lane's final\n"
        "    message.",
    ),
    (
        "  - the two limbs, carried everywhere. F-CANOPY-068's header",
        "  - the two limbs, carried further. F-CANOPY-068's header",
    ),
    (
        "The first limb is now put as a promise of something a user sees, and",
        "The first limb was put as a promise of something a user sees (round 4 restored Phase 10's wording), and",
    ),
    (
        "    has been checked. New item 26 is the sweep;",
        "    has been checked. New item 26 is the sweep. This record left out Lane 11-R3A's own pointer, F-CANOPY-012 and\n"
        "    F-CANOPY-013 against the note's CAN-015h half, until round 4;",
    ),
    (
        "so a trigger sent from Python adds at most\n    0.7–1.0 s (Lane 11-R3B).",
        "so a trigger sent from Python adds at most\n    0.7–1.0 s (Lane 11-R3B; Lane 11-R2A had found where the stamp is taken, in round 2).",
    ),
    (
        "  - the readers. Only the trace's report exits 2 on an alternation break,",
        "  - the readers. Of the trace's two modes, only the report exits 2 on an alternation break,",
    ),
    # --- the round-4 record, after the round-3 record's last bullet ---
    (
        "  nothing on Phase 10's 33 merged scripts, nor now on any of this phase's.",
        "  nothing on Phase 10's 33 merged scripts, nor now on any of this phase's.ROUND4_RECORD",
    ),
    # --- Matrix effect and counts: Phase 10's wording, and the reach with F-CANOPY-012 (R4A F1, R4B F2) ---
    (
        "    F-CASCOR-002. F-CANOPY-065 is P1 only if a shipped CHANGELOG's or a design plan's promise of something a user\n"
        "    sees counts as documented, and F-CANOPY-068 only if a CHANGELOG's description of an internal mechanism does.\n"
        "    Moving those two alone, by ruling: both P1, 7 open P1 and 16 open P2, as the triage counts them;\n"
        "    F-CANOPY-065 alone, 6 and 17; neither, 5 and 18.\n"
        "  - **A ruling may move more than those two** (round 3, Lanes 11-R3A and 11-R3B). No other open finding has been\n"
        "    checked against canopy's CHANGELOG or the design plans, and two open P2s are already known to be within\n"
        "    reach of the first limb:\n",
        "    F-CASCOR-002. F-CANOPY-065 is P1 only if a shipped CHANGELOG or design-plan promise counts as documented, and\n"
        "    F-CANOPY-068 only if that extends to a CHANGELOG's description of an internal mechanism. Moving those two\n"
        "    alone, by ruling: both P1, 7 open P1 and 16 open P2, as the triage counts them; F-CANOPY-065 alone, 6 and 17;\n"
        "    neither, 5 and 18.\n"
        "  - **A ruling may move more than those two** (rounds 3 and 4, Lanes 11-R3A, 11-R3B, 11-R4A and 11-R4B). No open\n"
        "    finding has been swept against canopy's CHANGELOG, the design plans or canopy's manual, and three open P2s\n"
        "    are already known to be within reach of the first limb:\n",
    ),
    (
        "      on. Its fix, canopy#533, merged on 2026-08-28 and awaits a live re-drive.\n"
        "    - Item 26 is the sweep, owed with the ruling.",
        "      on. Its fix, canopy#533, merged on 2026-08-28 and awaits a live re-drive;\n"
        "    - F-CANOPY-012, through the same design note, which records h-5, the Network Editor, as merged and specifies\n"
        "      an output-layer \"Patch weights\" card (`:627`). F-CANOPY-012 found `output_weights`, the editor's default\n"
        "      patch target, impossible to patch from the UI. canopy's own manual may reach it without any ruling: before\n"
        "      canopy#535 it listed `output_weights` under Patch Weights, with values \"entered as comma-, semicolon-, or\n"
        "      newline-separated floats\", though it also said that canopy \"lets CasCor validate the exact target shape\"\n"
        "      (`docs/USER_MANUAL.md:407-415` at `28da69f8^`, canopy#535's parent). Its fix, canopy#535, merged on\n"
        "      2026-08-28 and awaits a live re-drive.\n"
        "    - F-CANOPY-013, the editor's success messages, is unsettled: the note promises no message text (Lane 11-R3A).\n"
        "    - Item 26 is the sweep, owed with the ruling; it checks F-CANOPY-012 against the manual first.",
    ),
    # --- item 0: the [0.8.0] text is a description (R4B F1) ---
    (
        "  `[0.8.0]` promise needs a correcting entry in the release that fixes it.",
        "  `[0.8.0]` description needs a correcting entry in the release that fixes it.",
    ),
    # --- item 26: the manual first, and F-CANOPY-012 and -013 in the start list (R4A F1, R4B F2) ---
    (
        "26. **The reach of the owner's §6.3 ruling.** Once the owner rules, check each open finding not yet rated on a\n"
        "    CHANGELOG or a design plan for a promise, of a kind the ruling counts, of the behaviour it breaks. Start with\n"
        "    F-CANOPY-057 and F-CANOPY-018 (Matrix effect and counts), and re-rate what the ruling reaches. Whatever the\n"
        "    ruling, the CAN-015g/h design note's \"every CAN-015g item has merged to `main`\" needs a dated correction:\n"
        "    g-3 never reached cascor `main` (F-CANOPY-057's History).\n",
        "26. **The reach of the owner's §6.3 ruling, and canopy's manual.** First, without waiting for the ruling, check\n"
        "    F-CANOPY-012 against canopy's manual (Matrix effect and counts). Once the owner rules, check each open finding\n"
        "    not yet rated on a CHANGELOG or a design plan for a promise, of a kind the ruling counts, of the behaviour it\n"
        "    breaks. Start with F-CANOPY-057, F-CANOPY-018, F-CANOPY-012 and F-CANOPY-013, and re-rate what the ruling\n"
        "    reaches. Whatever the ruling, the CAN-015g/h design note's \"every CAN-015g item has merged to `main`\" needs a\n"
        "    dated correction: g-3 never reached cascor `main` (F-CANOPY-057's History).\n",
    ),
]

README_SUBS = [
    (
        "Its scripted triggers take effect 1.3–4.2 s after they fire, a delay the transcript does not split between the\n"
        "driver and the page, so as written they cannot test a mid-request re-enable (the ledger's Phase 11,\n"
        "Instruments).",
        "Its gate and tab triggers take effect 1.3–4.2 s after they fire, a delay the transcript splits only for T-tab,\n"
        "and only in part, and T-mode's effect is not recorded, so as written they cannot test a mid-request re-enable\n"
        "(the ledger's Phase 11, Instruments).",
    ),
]

REDERIVE_SUBS = [
    (
        "``reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round3.md``",
        "``reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md``",
    ),
    (
        "which is when the next request entered.",
        "which is when the next request was made.",
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
    if "- **Round 3**: two lanes on the frozen `7af6a381`" not in before or "- **Round 4**: two lanes on the frozen `adcba49f`" in before:
        raise SystemExit("this is not the round-4 freeze (adcba49f)")
    after = apply(before, SUBS)
    record = ROUND4_RECORD.replace("README_SUB_COUNT", str(len(README_SUBS))).replace("REDERIVE_SUB_COUNT", str(len(REDERIVE_SUBS))).replace("SUB_COUNT", str(len(SUBS)))
    if after.count("ROUND4_RECORD") != 1:
        raise SystemExit("round-4 record placeholder not found exactly once")
    after = after.replace("ROUND4_RECORD", record)
    readme_after = apply(README.read_text(encoding="utf-8"), README_SUBS)
    rederive_after = apply(REDERIVE.read_text(encoding="utf-8"), REDERIVE_SUBS)
    compile(rederive_after, REDERIVE.name, "exec")
    print(f"ledger: {len(SUBS)} substitutions, {len(before)} -> {len(after)} chars; README: {len(README_SUBS)}; rederive: {len(REDERIVE_SUBS)}")
    if not args.check:
        LEDGER.write_text(after, encoding="utf-8")
        README.write_text(readme_after, encoding="utf-8")
        REDERIVE.write_text(rederive_after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
