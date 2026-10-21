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
#               util/ad-hoc/2026-10-21_phase15_ledger_round2_corrections.py (the pass before this one);
#               reports/e2e-canopy-2026-09-02/consensus/2026-10-21_validator_reports_phase15_round3.md (the report)
# ---------------------------------------------------------------------------
"""Round 3's correction pass on the ledger's Phase 15 and its handoff; the review ends here.

Applied after ``2026-10-21_phase15_ledger_round2_corrections.py``, to the files as frozen for round 3 (local commit
``71417d33``). Round 3 was one lane, Lane 15-R3, scoped to round 2's corrections and the handoff: SOUND-WITH-FIXES,
and it changes no number, disposition or action, so under §4 of the consensus procedure the review ends with it.
Its fourteen MINORs (D1–D14, three of them optional) are all applied here, each re-derived first: the fix tree's click
gaps from its logs (6.2–8.7 s early, 1.2–3.5 s settled), item 18's drives from Phase 10, the E2 validation script's
phases and extras, the driver's function names, the serving-commit file. The pass also fills every round-3
placeholder. D3 (the driver's forced-write comment) and D12 (the arc's auto-memory note) are edited directly, being
outside the shared files this pass replays.

Usage:
    python3 -I util/ad-hoc/2026-10-21_phase15_ledger_round3_corrections.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_canopy-phase15-items-31-32-done-f069-f028-fixed.md"

_PRI_RE = re.compile(r"\b(P0/P1|P0|P1|P2|CRITICAL|LEDGER)\b")
FREEZE_R3 = "`71417d33`"

ITEM33_ONE_RUN = """ Once the owner has pulled the canopy primary to `main`,
    `python3 -I util/ad-hoc/2026-10-19_turing_e2_validate_envs.py canopy --phase all` does the re-sync, that install
    (with the `[test,juniper-cascor,observability]` extras) and the lanes the E2 record cites in one run; on this
    route the conda env itself keeps dash 3.3.0, shadowed by the venv."""

CONSENSUS_ROUND3 = """- **Round 3** (2026-10-21): one lane, Lane 15-R3, on the round-3 freeze `71417d33`, scoped to round 2's corrections
  and the handoff (`reports/e2e-canopy-2026-09-02/drafts/lane15R3_phase15_ledger_brief.md`). Its report, verbatim, is
  in `reports/e2e-canopy-2026-09-02/consensus/2026-10-21_validator_reports_phase15_round3.md`: SOUND-WITH-FIXES, and
  **it changes no number, disposition or action**. The five MAJOR corrections are true against the evidence round 2
  cited; thirteen MINORs are true as applied, MINOR 8 in part (no "(at landing)" marks; what it left is landing-time
  by design) and MINOR 10 with a deviation the record had not disclosed; the verification block prints what its
  comments say; every remaining task is present; the replay prints MATCH for every shared file.
  - It raised fourteen MINORs: a verification comment naming item 7 for item 8; the Completed list's matrix cells;
    the driver's forced-write comment, which still stated the refuted premise; the click gaps' scope (the parent's
    arms; on the fix 6.2–8.7 s and 1.2–3.5 s); the provenance sentence's unrecorded check, now marked as the session's
    account; the round-2 record's "all … as proposed"; item 18's three drives; item 33's one-run route; item 27's
    interpreter and where the chrome channel and the CDN abort live; the eviction residual's precision; the
    serving-commit file's stale sha; the arc's memory note; item 23, done but never marked; and "the render it
    requests is held", not "the write".
  - **Corrections** (`util/ad-hoc/2026-10-21_phase15_ledger_round3_corrections.py`, each re-derived first: the fix
    tree's gaps from its logs, item 18's drives from Phase 10, the E2 validation script's phases and extras, the
    driver's functions, the serving-commit file): all fourteen; D3 in the driver and D12 in auto-memory directly.
  - Housekeeping: the brief's `pip show juniper-canopy` printed the package's author e-mail field in the lane's own
    output; the lane kept it out of its report and nothing was sent anywhere. Future briefs filter that output.
  - **The review ended at round 3** (§4 of the procedure)."""

LEDGER_SUBS = [
    (
        "D4a: the click gaps' scope",
        "and the click's writer went out 5.4–8.1 s after\n> that log line in the 2 s, 4 s and early forced arms (1.3–3.4 s at the settled timing, nothing pending).",
        "and on the parent the click's writer went out 5.4–8.1 s\n> after that log line in the 2 s, 4 s and early forced arms (1.3–3.4 s in the settled forced arms, nothing pending;\n> on the fix 6.2–8.7 s and 1.2–3.5 s).",
    ),
    (
        "D4b + D6: the round-2 record",
        "all five MAJORs and fifteen MINORs as proposed, the click gaps recomputed from the logs (5.4–8.1 s\n    early, 1.3–3.4 s settled);",
        "all five MAJORs and fifteen MINORs as proposed, except MINOR 8, whose \"(at landing)\" marks were not\n    added (its replay list was fixed, and MEMORY.md was updated before the landing), and MINOR 10, where the\n    provenance sentence kept the session's unrecorded same-day check (marked as the session's account in round 3);\n    the click gaps recomputed from the logs for the parent's arms (5.4–8.1 s early, 1.3–3.4 s settled; round 2's\n    settled 1.2–3.6 s spanned both trees);",
    ),
    (
        "D5: the provenance sentence",
        "with `test_poll_gating.py`, in a check the same day that kept no record: re-run against the same unchanged tree and\nrecorded on 2026-10-21 as `…_run3.json`, with three of the files the item 31 script touches).",
        "with `test_poll_gating.py`, in a check the same day that kept no record, by the session's account; the first record\nof either is `…_run3.json`, 2026-10-21, against the same unchanged tree, with three of the files the item 31 script\ntouches).",
    ),
    (
        "D10: the eviction residual",
        "> dash evicts the older executing call (`dash_renderer.dev.js:3379` in 4.4.1), so the click's write is discarded and\n",
        "> dash evicts the older in-flight call (in 4.4.1 it sits in `watched`; the duplicate removal is dispatched at\n> `dash_renderer.dev.js:3379` and its response is dropped at `:2884-2890`), so the click's write is discarded and\n",
    ),
    (
        "D13: item 23",
        "  re-stated them; no handoff carried them until this phase's.\n",
        "  re-stated them; no handoff carried them until this phase's.\n- **Item 23 is DONE**: the defect-register arc was told on 2026-10-08, under its item 11 (the INDEX's P2 ↔ P3 row); no\n  Still-owed list had marked it.\n",
    ),
    (
        "D14a: the render is held, not the write",
        "and a synthetic params-store write 150 ms after\nthe click is held behind the click's writer and cannot stage `early#2`'s order (0 of 6 at the early timing, 0 of 6",
        "and the table render a synthetic params-store\nwrite 150 ms after the click requests is held behind the click's writer, so it cannot stage `early#2`'s order (0 of\n6 at the early timing, 0 of 6",
    ),
    (
        "D8: item 33's one-run route (ledger)",
        "pip takes the newest dash 4.x (4.4.1 today) with `comm` and `janus`.\n    Or rebuild the conda env",
        "pip takes the newest dash 4.x (4.4.1 today) with `comm` and `janus`." + ITEM33_ONE_RUN + "\n    Or rebuild the conda env",
    ),
    ("round-3 record", "ROUND3_RECORD_PLACEHOLDER", CONSENSUS_ROUND3),
]

HANDOFF_SUBS = [
    (
        "D1: the release comment",
        "# v0.9.0 Latest (2026-10-17) means item 7 is still owed",
        "# v0.9.0 Latest (2026-10-17) means item 8, the canopy release, is still owed",
    ),
    (
        "D2: the matrix cells",
        "carries the ledger, the matrix (M-PARAMETERS-06's cell), this file,",
        "carries the ledger, the matrix (M-PARAMETERS-06's status cell and M-PARAMETERS-04's Expected cell), this file,",
    ),
    (
        "D7: item 18's drives",
        "18 F-CANOPY-064 (P1) and -067 (first decide -067's rating on unfixed `main` with the recurrence leg up and a canopy\n   restart on an idle cascor; never the trio)",
        "18 F-CANOPY-064 (P1) and -067 (first decide -067's rating on unfixed `main` in three drives: W8 step 13 after a\n   CasCor run with the recurrence leg up, a canopy restart on an idle cascor, and the same restart mid-run; never the\n   trio)",
    ),
    (
        "D8: item 33's one-run route (handoff)",
        "   `comm` and `janus`). Or rebuild the conda env",
        "   `comm` and `janus`). Once the owner has pulled the canopy primary to `main`,\n   `python3 -I util/ad-hoc/2026-10-19_turing_e2_validate_envs.py canopy --phase all` does the re-sync, that install\n   (with the `[test,juniper-cascor,observability]` extras) and the lanes the E2 record cites in one run; on this route\n   the conda env itself keeps dash 3.3.0, shadowed by the venv. Or rebuild the conda env",
    ),
    (
        "D9: item 27's interpreter and the chrome channel",
        "Then\n   `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py`, adapted to the chrome channel and the CDN route,\n   samples",
        "Then\n   `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py`, run with\n   `~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python -I` (the interpreter the item 31 drives gave\n   the driver) and adapted to the chrome channel and the CDN route (`launch`, `_route_cdn` and `new_page` in\n   `2026-10-20_item30_fixwave_redrive.py`), samples",
    ),
    (
        "D14b: Completed, the render is held",
        "150 ms after the click, which the renderer holds behind the click's writer, so it cannot stage early#2's order);",
        "150 ms after the click, whose table render the renderer holds behind the click's writer, so it cannot stage early#2's\n  order);",
    ),
    (
        "D14c: the trap, the render is held",
        "A params-store write after the click (the forced arms) is held behind the click's writer by the\n  renderer (the pin store is the render's Input), so it cannot stage",
        "The table render a params-store write after the click requests (the forced arms) is held\n  behind the click's writer by the renderer (the pin store is the writer's Output and the render's Input), so it\n  cannot stage",
    ),
    (
        "D11: the serving-commit trap",
        "  requested before the click's writer. Give every driver run its own `--out`.\n",
        "  requested before the click's writer. Give every driver run its own `--out`.\n- **`~/.local/state/juniper/turing-e2/legs/serving-commit` still reads `571743db`**, and\n  `2026-10-20_turing_canopy_leg.bash` stamps it on `/v1/health` whenever no sha is passed. After a re-sync of the E2\n  tree (items 27 and 33), launch through `2026-10-20_f069_fix_leg.bash` with its sixth argument, or rewrite that file\n  only after the blob check prints ALL MATCH for the new commit.\n",
    ),
    (
        "consensus line: round 3",
        "ROUND3_SUMMARY_PLACEHOLDER (ledger Phase 15, Consensus record).",
        "Round 3 on 2026-10-21, one lane on round 2's corrections and this handoff: SOUND-WITH-FIXES, fourteen MINORs, all\napplied; it changed no number, disposition or action, so the review ended there (ledger Phase 15, Consensus record).",
    ),
    (
        "item 1: the review's end",
        "   ROUND3_ITEM_PLACEHOLDER\n",
        "   The consensus review ended at round 3 (it changed no number, disposition or action); nothing of it is owed.\n",
    ),
]


def replace_once(text: str, old: str, new: str, what: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"anchor for {what} occurs {n} times, expected 1: {old[:90]!r}")
    return text.replace(old, new, 1)


def check_headers(ledger: str) -> None:
    for fid, want in (("F-CANOPY-069", "P0"), ("F-CANOPY-028", "P1")):
        m = re.search(r"^\*\*(" + fid + r") — (.*?)\*\*", ledger, re.M | re.S)
        assert m, f"{fid} header not found"
        body = " ".join(m.group(2).split())
        assert _PRI_RE.search(body).group(1) == want, (fid, body[:80])
        assert re.search(r"\bFIXED\b", body[-170:]), (fid, body[-170:])


def apply(root: Path, check_only: bool) -> None:
    ledger_p, handoff_p = root / LEDGER, root / HANDOFF
    ledger = ledger_p.read_text(encoding="utf-8")
    assert "ROUND3_RECORD_PLACEHOLDER" in ledger, "round 3 is already applied (or round 2 is missing)"
    for what, old, new in LEDGER_SUBS:
        ledger = replace_once(ledger, old, new, what)
    check_headers(ledger)
    handoff = handoff_p.read_text(encoding="utf-8")
    for what, old, new in HANDOFF_SUBS:
        handoff = replace_once(handoff, old, new, what)
    n = handoff.count("ROUND3_FREEZE_PLACEHOLDER")
    if n != 2:
        raise SystemExit(f"ROUND3_FREEZE_PLACEHOLDER occurs {n} times in the handoff, expected 2")
    handoff = handoff.replace("ROUND3_FREEZE_PLACEHOLDER", FREEZE_R3)
    for name, text in (("ledger", ledger), ("handoff", handoff)):
        left = re.findall(r"ROUND\d_[A-Z]+_PLACEHOLDER|CONSENSUS_[A-Z]+_PLACEHOLDER", text)
        assert not left, f"placeholders left in the {name}: {left}"
    if check_only:
        print("check OK: every anchor is unique; no placeholder is left; both headers still triage P0/P1 FIXED")
        return
    ledger_p.write_text(ledger, encoding="utf-8")
    handoff_p.write_text(handoff, encoding="utf-8")
    print("applied:", LEDGER, HANDOFF, sep="\n  ")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    apply(Path(args.root).resolve(), args.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())
