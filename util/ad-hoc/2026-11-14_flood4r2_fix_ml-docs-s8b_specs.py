#!/usr/bin/env python3
"""
Build the edit specs that apply the session-8 ml-docs validator's text fixes to the round-2 "ml-docs" carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (Cursor flood-4 session 8: the ml-docs carrier's fix-up, I4)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/ml-docs-s8/text_fixes.json (the 31 fixes); util/ad-hoc/2026-11-08_flood4r2_fix_apply_edits.py
         (applies the specs written here, all or nothing)

The validator's rows name "COPY/<path>" (the carrier tree) and "DELIVERABLES/<name>" (the carrier's
tmp/flood4r2/ml-docs/, content/ included). Both become repo-relative paths of the carrier worktree.

Written to --out-dir:
  spec_dryrun_31.json  the 31 rows exactly as the validator wrote them (a dry run proves each old occurs once);
  spec_apply.json      the 28 rows that edit a file directly, then the extras: the open question in checks.json,
                       the provenance of #2484's paragraph in the commit body and the CHANGELOG entry (three
                       copies), and the source changes to the carrier's manifest helper, which carry the
                       validator's three manifest.json rows (and the same provenance in #2484's reason, and
                       claim 50) into the manifest the helper regenerates.

Usage:
  2026-11-14_flood4r2_fix_ml-docs-s8b_specs.py --carrier <carrier worktree> --fixes <text_fixes.json> --out-dir <dir>
"""

import argparse
import json
from pathlib import Path

DELIV = "tmp/flood4r2/ml-docs/"
MANIFEST_HELPER = "util/ad-hoc/2026-11-14_flood4r2_ml-docs_manifest.py"
ENTRY_COPIES = (DELIV + "changelog_entry.txt", DELIV + "content/changelog_entry.txt", "CHANGELOG.md")

OPEN_Q_OLD = (
    "so under an inherited GIT_DIR / GIT_WORK_TREE the symbol screen reads the repository GIT_DIR names, cannot resolve "
    "refs/fleet/base, exits 2 and degrades to skip: a branch that is DAMAGED-FIX-FIRST in a plain environment reads "
    "MERGE-CLEAN (ast_symbol_screen.status=skip)."
)
OPEN_Q_NEW = (
    "so under an inherited GIT_DIR / GIT_WORK_TREE each screen that has a file to read (juniper-symbol-loss-check on a .py "
    "or .bash delta, juniper-docs-additions-check on a .md delta) reads the repository GIT_DIR names, cannot resolve "
    "refs/fleet/base, exits 2 and degrades to skip: a branch that is DAMAGED-FIX-FIRST in a plain environment reads "
    "MERGE-CLEAN (ast_symbol_screen.status=skip for a lost symbol, docs_additions_only.status=skip for a deleted .md run; "
    "the second shown by the session-8 validator's probe and re-run by the fix-up on 7ce8d365, s8b/scratch_probe.json)."
)
COMMIT_OLD = "#2494, #2470 and one paragraph of #2484), each claim re-derived from the code on main, and corrects the\n"
COMMIT_NEW = (
    "#2494, #2470 and one paragraph of #2484's diff, written in draft #2480's commit, which its branch is\n"
    "stacked on), each claim re-derived from the code on main, and corrects the\n"
)
ENTRY_OLD = (
    "  #2490 and #2494, with #2470's index pointers and one paragraph of #2484), every claim re-derived from `main` with\n"
    "  the agent guard at 1.3.0: `docs/REFERENCE.md`, the developer cheatsheet, the documentation overview, the\n"
    "  quick start and `.claude/agents/fleet-supervisor.md`.\n"
)
ENTRY_NEW = (
    "  #2490 and #2494, with #2470's index pointers and one paragraph of #2484's diff, written in draft #2480's commit,\n"
    "  which its branch is stacked on), every claim re-derived from `main` with the agent guard at 1.3.0:\n"
    "  `docs/REFERENCE.md`, the developer cheatsheet, the documentation overview, the quick start and\n"
    "  `.claude/agents/fleet-supervisor.md`.\n"
)

REASON_OLD = "Docs-only take: one true sentence for its paragraph, with the consequence corrected to main's behaviour; its tests are the tests carrier's."
REASON_NEW = (
    "Docs-only take: one true sentence for the paragraph its diff shows (written in draft #2480's commit 406e7d80), with "
    "the consequence corrected to main's behaviour; its test file is left to the tests carrier, which takes the first test only."
)
CLAIM_OLD = "under an inherited GIT_DIR the symbol screen exits 2 on refs/fleet/base and is recorded as skip"
CLAIM_NEW = "under an inherited GIT_DIR each screen with a file to read (the symbol screen, the docs screen on a .md delta) exits 2 on refs/fleet/base and is recorded as skip"
EVIDENCE_OLD = "MERGE-CLEAN with ast_symbol_screen.status=skip under GIT_DIR, with and without GIT_WORK_TREE)"
EVIDENCE_NEW = (
    "MERGE-CLEAN with ast_symbol_screen.status=skip under GIT_DIR, with and without GIT_WORK_TREE); s8b/scratch_probe.json "
    "gitdir_md_inherited_GIT_DIR (the session-8 validator's probe, re-run on 7ce8d365: a .md deletion run, DAMAGED-FIX-FIRST in "
    "a plain environment, MERGE-CLEAN with docs_additions_only.status=skip)"
)
FIX_ALL = (
    "Session 8 fix-up (I4, 2026-11-15): the session-8 validator's 31 text fixes (findings F1-F8) applied to the carrier tree "
    "and to content/, which the re-derive reads, plus the provenance of #2484's paragraph in the commit body and the CHANGELOG "
    "entry; re-derived on 7ce8d365 and re-proved there (PROGRESS.txt, REPORT.txt)."
)
FIX_2494 = (
    "Session 8 fix-up (I4): the inherited-GIT_DIR sentences (the scratch bullet, the pitfall row, the CHANGELOG entry, the PR "
    "body, this row and claim 50) name both screens: the docs screen is recorded as skip too, so a .md deletion run that is "
    "DAMAGED-FIX-FIRST in a plain environment reads MERGE-CLEAN (the session-8 validator's finding F1; its probe re-run on "
    "7ce8d365, s8b/scratch_probe.json)."
)
FIX_2484 = (
    "Session 8 fix-up (I4): the provenance is stated in this row, the PR body, the commit body and the CHANGELOG entry: the "
    "paragraph and the tests/test_predict_merge.py hunk come from draft #2480's commit 406e7d80, which this branch is stacked "
    "on, and the tests carrier takes the test file's first test only (the session-8 validator's finding F2)."
)


def literal(text: str) -> str:
    """A Python string literal for ``text`` (JSON's escapes are valid Python ones)."""
    return json.dumps(text, ensure_ascii=False)


def helper_edits(manifest_rows: list) -> list:
    """The source changes to the manifest helper, so the manifest it regenerates carries the fixes."""
    consts = []
    pairs = []
    for number, row in enumerate(manifest_rows, start=1):
        consts.append(f"S8B_MANIFEST_OLD_{number} = {literal(row['old'])}\nS8B_MANIFEST_NEW_{number} = {literal(row['new'])}\n")
        pairs.append(f"    S8B_MANIFEST_OLD_{number}: S8B_MANIFEST_NEW_{number},\n")
    consts.append(f"S8B_REASON_OLD = {literal(REASON_OLD)}\nS8B_REASON_NEW = {literal(REASON_NEW)}\n")
    pairs.append("    S8B_REASON_OLD: S8B_REASON_NEW,\n")
    consts.append(
        f"S8B_CLAIM_OLD = {literal(CLAIM_OLD)}\nS8B_CLAIM_NEW = {literal(CLAIM_NEW)}\n"
        f"S8B_EVIDENCE_OLD = {literal(EVIDENCE_OLD)}\nS8B_EVIDENCE_NEW = {literal(EVIDENCE_NEW)}\n"
    )
    old_corr = (
        "TEXT_CORRECTIONS = {\n"
        "    # Counted on main a949d504 (and on 26ea0ecb): `grep -c -x -F '### Operator pitfalls' docs/REFERENCE.md` is 32.\n"
        '    "docs/REFERENCE.md already has 40 headings with that exact text": "docs/REFERENCE.md already has 32 headings with that exact text",\n'
        "}\n"
    )
    new_corr = (
        "# Session 8 fix-up (I4): the session-8 validator's rows for manifest.json (tmp/flood4r2-val/ml-docs-s8/text_fixes.json,\n"
        "# findings F1 and F2), the same provenance in #2484's reason, and claim 50, which named only the symbol screen (F1).\n"
        + "".join(consts)
        + "TEXT_CORRECTIONS = {\n"
        "    # Counted on main a949d504 (and on 26ea0ecb): `grep -c -x -F '### Operator pitfalls' docs/REFERENCE.md` is 32.\n"
        '    "docs/REFERENCE.md already has 40 headings with that exact text": "docs/REFERENCE.md already has 32 headings with that exact text",\n'
        + "".join(pairs)
        + "}\n"
        "CLAIM_CORRECTIONS = {\n"
        "    S8B_CLAIM_OLD: S8B_CLAIM_NEW,\n"
        "    S8B_EVIDENCE_OLD: S8B_EVIDENCE_NEW,\n"
        "}\n"
    )
    old_all = "after the entries already there.\",\n    ],\n"
    new_all = f"after the entries already there.\",\n        {literal(FIX_ALL)},\n    ],\n"
    old_2479 = "scripts/wake_the_claude.bash:255-262.\",\n    ],\n}\n"
    new_2479 = (
        "scripts/wake_the_claude.bash:255-262.\",\n    ],\n"
        f"    2494: [\n        {literal(FIX_2494)},\n    ],\n"
        f"    2484: [\n        {literal(FIX_2484)},\n    ],\n}}\n"
    )
    old_fn = "def load_session6():\n"
    new_fn = (
        "def corrected_claim(claim: dict) -> dict:\n"
        '    """Apply CLAIM_CORRECTIONS to a claim\'s text and evidence."""\n'
        "    fixed = dict(claim)\n"
        '    for key in ("claim", "evidence"):\n'
        "        for old, new in CLAIM_CORRECTIONS.items():\n"
        "            fixed[key] = fixed[key].replace(old, new)\n"
        "    return fixed\n"
        "\n\n"
        "def load_session6():\n"
    )
    old_claims = "    claims = [claim_status(claim, facts) for claim in session6.CLAIMS]\n"
    new_claims = (
        "    claims = [claim_status(corrected_claim(claim), facts) for claim in session6.CLAIMS]\n"
        "    for new in CLAIM_CORRECTIONS.values():\n"
        "        if new not in json.dumps(claims):\n"
        '            raise SystemExit(f"a claim correction did not apply: {new!r}")\n'
    )
    return [
        {"id": "H1-fixes-all", "file": MANIFEST_HELPER, "old": old_all, "new": new_all},
        {"id": "H2-fixes-2494-2484", "file": MANIFEST_HELPER, "old": old_2479, "new": new_2479},
        {"id": "H3-corrections", "file": MANIFEST_HELPER, "old": old_corr, "new": new_corr},
        {"id": "H4-claim-fn", "file": MANIFEST_HELPER, "old": old_fn, "new": new_fn},
        {"id": "H5-claim-apply", "file": MANIFEST_HELPER, "old": old_claims, "new": new_claims},
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--carrier", required=True)
    ap.add_argument("--fixes", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    rows = json.loads(Path(args.fixes).read_text(encoding="utf-8"))
    mapped = []
    for number, row in enumerate(rows, start=1):
        name = row["file"]
        rel = DELIV + name[len("DELIVERABLES/"):] if name.startswith("DELIVERABLES/") else name[len("COPY/"):]
        mapped.append({"id": f"{row['finding']}#{number}", "file": rel, "old": row["old"], "new": row["new"]})
    direct = [row for row in mapped if row["file"] != DELIV + "manifest.json"]
    via_helper = [row for row in mapped if row["file"] == DELIV + "manifest.json"]
    extras = [{"id": "X1-open-question", "file": DELIV + "checks.json", "old": OPEN_Q_OLD, "new": OPEN_Q_NEW}]
    extras.append({"id": "X2-commit-2484", "file": DELIV + "commit_body.txt", "old": COMMIT_OLD, "new": COMMIT_NEW})
    for path in ENTRY_COPIES:
        extras.append({"id": "X3-entry-2484", "file": path, "old": ENTRY_OLD, "new": ENTRY_NEW})
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    worktree = str(Path(args.carrier).resolve())
    (out / "spec_dryrun_31.json").write_text(json.dumps({"worktree": worktree, "edits": mapped}, indent=1) + "\n", encoding="utf-8")
    apply_edits = direct + extras + helper_edits(via_helper)
    (out / "spec_apply.json").write_text(json.dumps({"worktree": worktree, "edits": apply_edits}, indent=1) + "\n", encoding="utf-8")
    print(f"{len(mapped)} validator rows ({len(direct)} direct, {len(via_helper)} through the manifest helper); {len(extras)} extras; {len(apply_edits)} edits to apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
