"""
Write the claims lens's text_fixes.json for the ml-tests round-2 carrier (claims lens, session 8). Each fix is
{"id", "finding", "file", "old", "new"} with "old" copied from the file it names; the companion
2026-11-14_flood4r2_val_ml-tests-r2-claims_text_fixes.py checks that each "old" occurs exactly once.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_flood4r2_val_ml-tests-r2-claims_text_fixes.py
"""

import argparse
import json
import sys
from pathlib import Path

FIXES = [
    {
        "id": "T1",
        "finding": "F1",
        "file": "MANIFEST/carried/2484/dropped",
        "old": "its docs/REFERENCE.md paragraph on the scratch copying the checkout's shallow graft: documentation, left out of this tests carrier (round 1's open question 6; the docs carrier's builder has been told)",
        "new": "no docs/REFERENCE.md paragraph of its own: the paragraph on the scratch copying the checkout's shallow graft that its base branch shows is #2480's (commit 406e7d80), and #2480's row covers it (round 1's open question 6)",
    },
    {
        "id": "T2",
        "finding": "F1",
        "file": "TEMPLATE/pr_body.txt",
        "old": " Its `docs/REFERENCE.md` paragraph on the scratch copying the checkout's shallow graft is documentation and is not in this PR.",
        "new": " The `docs/REFERENCE.md` paragraph on the scratch copying the checkout's shallow graft, which its base branch shows, is #2480's (above), not #2484's.",
    },
    {
        "id": "T3",
        "finding": "F1",
        "file": "TEMPLATE/commit_body.txt",
        "old": "the second test of #2484 and its documentation paragraph.",
        "new": "its documentation paragraph, and the second test of #2484.",
    },
    {
        "id": "T4",
        "finding": "F1",
        "file": "TEMPLATE/changelog_entry.txt",
        "old": "#2484's second test, and #2484's",
        "new": "#2484's second test, and #2480's",
    },
    {
        "id": "T5",
        "finding": "F1",
        "file": "DELIVERABLES/dispositions.json",
        "old": "documentation; left out of this tests carrier by the round-2 brief (the docs carrier's builder has been told).",
        "new": "the paragraph is #2480's (commit 406e7d80, on #2484's base branch), not in #2484's own diff; documentation, left out of this tests carrier by the round-2 brief.",
    },
    {
        "id": "T6",
        "finding": "F2",
        "file": "MANIFEST/carried/2480/dropped",
        "old": "its CHANGELOG, docs/REFERENCE.md and fleet-supervisor.md hunks (they describe the superseded code)",
        "new": "its CHANGELOG and docs/REFERENCE.md hunks (they describe the superseded code); the .claude/agents/fleet-supervisor.md hunk its diff also shows is the Overtoad commit 21a9dabc97 beneath it (juniper-ml#2474, on main)",
    },
    {
        "id": "T7",
        "finding": "F2",
        "file": "TEMPLATE/pr_body.txt",
        "old": "Its near-duplicate missing-parent test, its docstring, CHANGELOG, `docs/REFERENCE.md` and `.claude/agents/fleet-supervisor.md` hunks go with it.",
        "new": "Its near-duplicate missing-parent test, its docstring, CHANGELOG and `docs/REFERENCE.md` hunks go with it; the `.claude/agents/fleet-supervisor.md` change its diff also shows is juniper-ml#2474's, on `main`.",
    },
    {
        "id": "T8",
        "finding": "F3",
        "file": "TEMPLATE/pr_body.txt",
        "old": "two builders were stopped before finishing",
        "new": "its first builder was stopped before finishing",
    },
    {
        "id": "T9",
        "finding": "F4",
        "file": "TEMPLATE/pr_body.txt",
        "old": "the four helpers the last session added",
        "new": "the five helpers the last session added",
    },
    {
        "id": "T10",
        "finding": "F5",
        "file": "MANIFEST/carried/2507/reason",
        "old": "Measured too on juniper-ml#2558's head d4dcefbc (the 0.11.5 release proposal, open on 2026-11-13): the eight tests pass on its Version cell and its reworded sentence.",
        "new": "Measured on juniper-ml#2558's head d4dcefbc while it was open, and again on main after it merged as the v0.11.5 cut (48b66130; 0.11.5 is released): the eight tests pass on its Version cell and its reworded sentence.",
    },
    {
        "id": "T11",
        "finding": "F6",
        "file": "TEMPLATE/pr_body.txt",
        "old": "its code is on `main` since juniper-ml#2474",
        "new": "what its code does is on `main` since juniper-ml#2474",
    },
    {
        "id": "T12",
        "finding": "F6",
        "file": "TEMPLATE/commit_body.txt",
        "old": "(main has it since",
        "new": "(main does the same since",
    },
    {
        "id": "T13",
        "finding": "F7",
        "file": "MANIFEST/carried/2472/fixes",
        "old": "black (the pinned hook joins the fake-claude and fake-wake scripts' implicit string concatenations onto one line; the draft's file fails the hook as submitted)",
        "new": "black (the pinned hook joins the fake-wake script's implicit string concatenation onto one line and re-quotes the fake-claude script's second string; the draft's file fails the hook as submitted)",
    },
    {
        "id": "T14",
        "finding": "F11",
        "file": "DELIVERABLES/dispositions.json",
        "old": "(0.6.70 on f9582a74; 0.6.71 after ml-propose)",
        "new": "(0.6.70 on f9582a74; 0.6.71 on a949d504; 0.6.72 on a949d504 after ml-propose)",
    },
    {
        "id": "T15",
        "finding": "F8",
        "optional": "apply only if the orchestrator reverses its juniper-data#539 precedent of keeping the phrase",
        "file": "TEMPLATE/pr_body.txt",
        "old": " (the record's next update adds it to its section 8)",
        "new": "",
    },
    {
        "id": "T16",
        "finding": "F8",
        "optional": "apply only if the orchestrator reverses its juniper-data#539 precedent of keeping the phrase",
        "file": "TEMPLATE/changelog_entry.txt",
        "old": "by the Overtoad's ruling of 2026-11-12 (the next\n    update of `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` adds it to its section 8).",
        "new": "by the Overtoad's ruling of 2026-11-12.",
    },
    {
        "id": "T17",
        "finding": "F13",
        "file": "MANIFEST/carried/2512/taken",
        "old": " (the session-7 spec typed tests/test_agent_suite_summary.py)",
        "new": "",
    },
    {
        "id": "T18",
        "finding": "F13",
        "file": "MANIFEST/carried/2515/taken",
        "old": " (the session-7 spec typed tests/test_configure_commit_signing.py)",
        "new": "",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Write text_fixes.json.")
    parser.add_argument("--scratch", required=True, type=Path)
    args = parser.parse_args()
    for fix in FIXES:
        if fix["file"].startswith("MANIFEST/"):
            # manifest.json is rebuilt from carried_input.json by the carrier's manifest tool.
            fix["also_apply_to"] = "DELIVERABLES/carried_input.json"
    with (args.scratch / "text_fixes.json").open("w", encoding="utf-8") as handle:
        json.dump(FIXES, handle, indent=1, ensure_ascii=False)
        handle.write("\n")
    print(f"{len(FIXES)} fixes written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
