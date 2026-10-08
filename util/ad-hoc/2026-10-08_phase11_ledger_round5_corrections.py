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
"""Round 5's correction pass on the ledger's Phase 11, its Consensus record included.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` as frozen for round 5
(``684d70bc``, round 4's pass applied to ``adcba49f``). Round 5's reports are archived verbatim in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md``. Round 5's
docstring fix to ``util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py`` (Lane 11-R5B's NIT) was made by hand
with that pass's third run, ``--round r5``, and is not part of this pass. Every substitution is anchored to occur
exactly once.

Usage:
    python3 util/ad-hoc/2026-10-08_phase11_ledger_round5_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

ROUND5_RECORD = """

- **Round 5**: two lanes on the frozen `684d70bc`, briefed on round 4's corrections only, from one brief,
  `reports/e2e-canopy-2026-09-02/drafts/lane11R5_phase11_ledger_brief.md`. It also told them that another open
  finding within reach is a finding only where the ledger says something false about it. The reports, verbatim,
  are in `reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md`.
  - Lane 11-R5A re-derived the pass's claims with its own reader, and replayed the pass on `adcba49f`: `684d70bc`
    byte for byte, with no hand edit. Lane 11-R5B was adversarial on the pass, and replayed it too.
  - Both found that every statement gives one rating for F-CANOPY-065 and one for F-CANOPY-068 under each ruling,
    that every trigger-lag figure re-derives, and that the CodeQL pass's second run changes nothing a probe
    computes.
  - Their own probes are archived as `util/ad-hoc/2026-10-08_phase11_r5_{a,b}_*.py` (7 files) by
    `util/ad-hoc/2026-10-05_archive_phase11_lane_probes.py --round 5`. A third run of the CodeQL pass,
    `--round r5`, fixed the 5 alerts the prescreen predicted on them.
- **Verdicts.** Both returned SOUND-WITH-FIXES, with the same MINOR. The manual check covered F-CANOPY-012 alone,
  though the manual section it cites also documents what F-CANOPY-013 breaks, and the Matrix called item 26 a sweep
  of the manual that it did not owe. That changes an action, item 26's first step, so §4 of
  `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires round 6.
- **What round 5 changed:**
  - item 26's first step now checks every open finding against canopy's manual, F-CANOPY-012 and F-CANOPY-013
    first, and the Matrix's F-CANOPY-013 bullet names the manual's step 6 and canopy#532 (Lanes 11-R5A and
    11-R5B);
  - item 26's ruling step names a description of an internal mechanism beside a promise (Lane 11-R5B);
  - wording: the Unresolved bullet quotes Phase 10's question as Phase 10 words it, without "shipped" (Lanes
    11-R5A and 11-R5B); "cannot keep to what that entry describes" (Lane 11-R5B); round 1's re-derived list notes
    that the `[0.8.0]` text is a description (Lane 11-R5B);
  - round 4's record: its first-limb bullet no longer calls the shipped wording Phase 10's, and calls the second
    limb a condition, not an exception (Lanes 11-R5A and 11-R5B); its Verdicts give Lane 11-R4B's first-limb claim;
    its credits for T-mode's unrecorded effect and for F-CANOPY-013's reason now name the lanes that raised them;
    and its Slips record Lane 11-R4B's two bytecode files (Lane 11-R5A);
  - by hand, with the CodeQL pass's third run: its docstring now states the `fh` guard as the code applies it
    (Lane 11-R5B).
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-08_phase11_ledger_round5_corrections.py`,
    SUB_COUNT substitutions in the ledger.
- **Re-derived by the orchestrator before applying:**
  - step 6 of the manual's Network Editor workflow, "Use the API response shown in the status alert to confirm
    the edit", at `3411673c` (`:387`), `28da69f8^` (`:424`) and `60ae1870` (`:465`);
  - F-CANOPY-013's entry, which calls the alert "the one surface an operator has for confirming a blind mutation"
    and rates it P2 as cosmetic;
  - canopy#532, merged on 2026-08-28 as `359e1bf7`.
- **Slips.** Neither lane reported one."""

SUBS = [
    # --- Matrix: F-CANOPY-013 reaches the manual's step 6 (R5A F1, R5B F1); its reason's credit (R5A F4, R5B F1) ---
    (
        "    - F-CANOPY-013, the editor's success messages, is unsettled: the note promises no message text (Lane 11-R3A).\n"
        "    - Item 26 is the sweep, owed with the ruling; it checks F-CANOPY-012 against the manual first.",
        "    - F-CANOPY-013, the editor's success messages, is unsettled against the note, which promises no message text\n"
        "      (Lane 11-R4A; Lane 11-R3A had named it). canopy's manual may reach it without any ruling: its Network\n"
        "      Editor workflow says \"Use the API response shown in the status alert to confirm the edit\" (step 6,\n"
        "      `docs/USER_MANUAL.md:424` at `28da69f8^`), and F-CANOPY-013's alert misreports a successful append (Lanes\n"
        "      11-R5A and 11-R5B). Its fix, canopy#532, merged on 2026-08-28 and awaits a live re-drive.\n"
        "    - Item 26 is the sweep: every open finding against canopy's manual first, which needs no ruling, then, with\n"
        "      the ruling, against the CHANGELOG and the design plans.",
    ),
    # --- item 26: the manual for every open finding; descriptions beside promises (R5A F1, R5B F1, R5B F3) ---
    (
        "26. **The reach of the owner's §6.3 ruling, and canopy's manual.** First, without waiting for the ruling, check\n"
        "    F-CANOPY-012 against canopy's manual (Matrix effect and counts). Once the owner rules, check each open finding\n"
        "    not yet rated on a CHANGELOG or a design plan for a promise, of a kind the ruling counts, of the behaviour it\n"
        "    breaks.",
        "26. **The reach of the owner's §6.3 ruling, and canopy's manual.** First, without waiting for the ruling, check\n"
        "    every open finding against canopy's manual, which §6.3 already counts, starting with F-CANOPY-012 and\n"
        "    F-CANOPY-013 (Matrix effect and counts). Once the owner rules, check each open finding not yet rated on a\n"
        "    CHANGELOG or a design plan for a promise, or, if the ruling counts it, a description of an internal\n"
        "    mechanism, of the behaviour it breaks.",
    ),
    # --- Unresolved: Phase 10's question as Phase 10 words it (R5A F3, R5B F2) ---
    (
        "Phase 10's question, whether a shipped CHANGELOG or design-plan promise counts as\n",
        "Phase 10's question, whether a CHANGELOG or design-plan promise counts as\n",
    ),
    # --- F-CANOPY-068's contract: "keep to" (R5B F4) ---
    (
        "The watchdog\n  cannot do what that entry describes.",
        "The watchdog\n  cannot keep to what that entry describes.",
    ),
    # --- round 1's re-derived list: the [0.8.0] text is a description since round 4 (R5B F3) ---
    (
        "  - canopy's CHANGELOG `[0.8.0]` promise, at `60ae1870`, and canopy#624 (`06d8607e`), which put it there;",
        "  - canopy's CHANGELOG `[0.8.0]` promise (called a description since round 4), at `60ae1870`, and canopy#624\n"
        "    (`06d8607e`), which put it there;",
    ),
    # --- round 4's record: the first limb's wording, a condition not an exception (R5A F3, R5B F2) ---
    (
        "  - the first limb is Phase 10's question again, worded as Phase 10, F-CANOPY-065's header and its Severity bullet\n"
        "    word it, and the second limb is stated as its exception: whether it extends to a CHANGELOG's description of an\n"
        "    internal mechanism.",
        "  - the first limb is Phase 10's question again, worded as F-CANOPY-065's header and its Severity bullet word it,\n"
        "    \"shipped\" included (both entries in play shipped; round 5 quotes Phase 10's own wording in the Unresolved\n"
        "    bullet), and the second limb is stated as a condition on it: whether it extends to a CHANGELOG's description\n"
        "    of an internal mechanism.",
    ),
    # --- round 4's record: Verdicts, credits and Slips (R5A F2, F4) ---
    (
        "  action (the reach put to the owner, and item 26), so §4 of\n"
        "  `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires round 5.",
        "  action (the reach put to the owner, and item 26). Lane 11-R4B's MINOR on the first limb also changed an action,\n"
        "  the question put to the owner, and under one ruling F-CANOPY-068's rating and a count. So §4 of\n"
        "  `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires round 5.",
    ),
    (
        "    recorded, now in the Summary, the Instruments and the README (Lanes 11-R4A and 11-R4B);",
        "    recorded, now in the Summary, the Instruments and the README (T-mode's, Lane 11-R4B; the README's split, Lanes\n"
        "    11-R4A and 11-R4B);",
    ),
    (
        "  dates, with no name or e-mail. Neither printed a secret or an address.",
        "  dates, with no name or e-mail, and one probe without `-B`, which wrote two git-ignored bytecode files into the\n"
        "  worktree (Lane 11-R5A). Neither printed a secret or an address.ROUND5_RECORD",
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
    if "- **Round 4**: two lanes on the frozen `adcba49f`" not in before or "- **Round 5**: two lanes on the frozen `684d70bc`" in before:
        raise SystemExit("this is not the round-5 freeze (684d70bc)")
    after = apply(before, SUBS)
    record = ROUND5_RECORD.replace("SUB_COUNT", str(len(SUBS)))
    if after.count("ROUND5_RECORD") != 1:
        raise SystemExit("round-5 record placeholder not found exactly once")
    after = after.replace("ROUND5_RECORD", record)
    print(f"ledger: {len(SUBS)} substitutions, {len(before)} -> {len(after)} chars")
    if not args.check:
        LEDGER.write_text(after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
