#!/usr/bin/env python3
"""
Write the ml-docs validator's text_fixes.json and prove every fix applies: each "old" occurs exactly once in the
file it names, and applying all of a file's fixes in order (to a scratch copy) leaves no "old" behind and, for a
JSON file, still parses.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (Cursor flood-4 session 8: the ml-docs carrier's claims-lens validation, check E)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/ml-docs-s8/findings.json (the findings each fix answers)

"DELIVERABLES/<name>" is a file under the carrier's tmp/flood4r2/ml-docs/ (its content/ included: that is what the
re-derive reads); "COPY/<path>" is the carrier tree's own copy. Nothing in the carrier is written: the applied
copies go under --scratch.

Usage:
  2026-11-14_flood4r2_val_ml-docs_text_fixes.py --carrier <carrier worktree> --out <text_fixes.json> --scratch <dir>
"""

import argparse
import json
from pathlib import Path

DELIV = "tmp/flood4r2/ml-docs/"

F1_REF_OLD = ("Under an inherited `GIT_DIR` the symbol screen looks for `refs/fleet/base` in the repository that variable names, exits 2, "
              "and is recorded as `status=skip`. A `skip` is not a pass: the verdict is then computed without that screen,")
F1_REF_NEW = ("Under an inherited `GIT_DIR` each screen that has a file to read (the symbol screen on a `.py` or `.bash` file, the docs "
              "screen on a `.md` file) looks for `refs/fleet/base` in the repository that variable names, exits 2, and is recorded as "
              "`status=skip`. A `skip` is not a pass: the verdict is then computed without that screen, so a section deletion the docs "
              "screen would fail no longer makes the PR `DAMAGED-FIX-FIRST`,")
F1_ROW_OLD = "| `ast_symbol_screen.status=skip` with `could not resolve ref: 'refs/fleet/base'` |"
F1_ROW_NEW = "| `ast_symbol_screen.status=skip` or `docs_additions_only.status=skip` with `could not resolve ref: 'refs/fleet/base'` |"
F1_CL_OLD = ("Under an inherited `GIT_DIR` the symbol screen reads the repository that variable names, exits 2\n"
             "    and is recorded as `skip`, so the verdict is computed without it.")
F1_CL_NEW = ("Under an inherited `GIT_DIR` each screen with a file to read (the symbol\n"
             "    screen or the docs screen) reads the repository that variable names, exits 2 and is recorded as `skip`, so the\n"
             "    verdict is computed without it.")
F1_PR_OLD = ("so under an inherited `GIT_DIR` the symbol screen reads the repository that variable names, exits 2 and is recorded as "
             "`skip`, and the verdict is computed without it.")
F1_PR_NEW = ("so under an inherited `GIT_DIR` each screen with a file to read (the symbol screen on a `.py` or `.bash` file, the docs "
             "screen on a `.md` file) reads the repository that variable names, exits 2 and is recorded as `skip`, and the verdict is "
             "computed without it: a section deletion the docs screen would fail no longer makes the PR `DAMAGED-FIX-FIRST`.")
F1_MAN_OLD = "so under an inherited GIT_DIR the symbol screen is recorded as `skip` (probe)."
F1_MAN_NEW = "so under an inherited GIT_DIR each screen with a file to read (the symbol screen, and the docs screen on a .md delta) is recorded as `skip` (probe)."

F2_RD_OLD = '    if last == head:\n        block = "\\n" + block\n'
F2_RD_NEW = '    block = "\\n" + block\n'
F2_CL_OLD = "the two tools.\n- **Operator documentation consolidated from the Cursor flood-4 round-2 docs drafts**"
F2_CL_NEW = "the two tools.\n\n- **Operator documentation consolidated from the Cursor flood-4 round-2 docs drafts**"

F3_CH_OLD = "Since juniper-ml#1004 the docs screen is `juniper-docs-additions-check`: a deleted heading"
F3_CH_NEW = "Since juniper-ml#1004 the docs screen applies `juniper-docs-additions-check`'s rule (the console script itself since #1024): a deleted heading"
F3_HR_OLD = "since juniper-ml#1004 the docs screen is `juniper-docs-additions-check`, not an inline any-removed-line counter"
F3_HR_NEW = "since juniper-ml#1004 the docs screen has `juniper-docs-additions-check`'s thresholds (the console script since #1024), not an inline any-removed-line counter"

F5_CB_OLD = "fleet-triage text main itself had kept since juniper-ml#1004 and #1740: predict_merge's docs screen is"
F5_CB_NEW = "fleet-triage text main itself had kept stale since juniper-ml#1004, #1740 and #2474: predict_merge's docs screen is"
F5_CL_OLD = "stale since juniper-ml#1004 (2026-08-07) and #1740 (2026-09-05):"
F5_CL_NEW = "stale since juniper-ml#1004 (2026-08-07), #1740 (2026-09-05) and #2474 (2026-11-06):"
F5_CL2_OLD = "The sequence-safety gate paths name `juniper-ci-tools/tests/`."
F5_CL2_NEW = "The sequence-safety gate paths name `juniper-ci-tools/tests/`, where juniper-ml#1024 moved those suites."
F5_PR_OLD = "stale since juniper-ml#1004 (2026-08-07) and #1740 (2026-09-05), each sentence"
F5_PR_NEW = "stale since juniper-ml#1004 (2026-08-07), #1024 (2026-08-08), #1740 (2026-09-05) and #2474 (2026-11-06), each sentence"

F6_PR_OLD = ("- #2484's test file, its `tests/test_predict_merge.py` hunk, its `ci.yml` line and its \"Running every suite\" line: test "
             "registration, carried by the tests carrier; its `predict_merge.py`, agent-file and CHANGELOG changes, which come from the "
             "branch it is stacked on and which juniper-ml#2474 superseded.")
F6_PR_NEW = ("- #2484's test file, its `ci.yml` line and its \"Running every suite\" line: a test and its registration, left to the tests "
             "carrier, which takes the file's first test and not its second; its `tests/test_predict_merge.py`, `predict_merge.py`, "
             "agent-file and CHANGELOG changes, which come from the branches it is stacked on: draft #2480's, whose code juniper-ml#2474 "
             "superseded, and a pre-squash commit of #2474.")
F6_PR2_OLD = "- #2484 -- one paragraph, as a bullet of `#### Scratch repository`:"
F6_PR2_NEW = "- #2484 -- one paragraph of its diff (written in draft #2480's commit, which its branch is stacked on), as a bullet of `#### Scratch repository`:"
F6_MAN_OLD = "docs/REFERENCE.md only: its paragraph saying that predict_merge's scratch copies a shallow checkout's `shallow` file"
F6_MAN_NEW = ("docs/REFERENCE.md only: the paragraph its diff shows (written in draft #2480's commit 406e7d80, which its branch is stacked "
              "on) saying that predict_merge's scratch copies a shallow checkout's `shallow` file")
F6_MAN2_OLD = ("tests/test_predict_merge_shallow_worktree.py, its tests/test_predict_merge.py hunk, its .github/workflows/ci.yml line and its "
               "'Running every suite' line in docs/REFERENCE.md: test and registration content, the tests carrier's.")
F6_MAN2_NEW = ("tests/test_predict_merge_shallow_worktree.py, its .github/workflows/ci.yml line and its 'Running every suite' line in "
               "docs/REFERENCE.md: test and registration content, left to the tests carrier (it takes the file's first test only). Its "
               "tests/test_predict_merge.py hunk is not its own: it comes from draft #2480's commit 406e7d80 and #2474's pre-squash "
               "commit 21a9dabc.")

F7_PR_OLD = "per the Overtoad's \"Consolidate\" ruling."
F7_PR_NEW = "per the Overtoad's ruling of 2026-11-06, \"Consolidate, incl. post-grant\"."

F9_REF_OLD = "Tests: `tests/test_predict_merge.py`, `tests/test_predict_merge_inherited_git_env.py`."
F9_REF_NEW = "Tests: `tests/test_predict_merge.py` and every `tests/test_predict_merge_*.py` suite."

F10_ST_OLD = "--out . --report <scratch>/derive_report.json"
F10_ST_NEW = "--out . --report <scratch>/derive_report.json --work-dir <scratch>"


def fixes() -> list[dict]:
    rows = []

    def add(finding: str, files: list[str], old: str, new: str) -> None:
        for name in files:
            rows.append({"finding": finding, "file": name, "old": old, "new": new})

    ref = ["COPY/docs/REFERENCE.md", "DELIVERABLES/content/docs/REFERENCE.md"]
    chs = ["COPY/docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md", "DELIVERABLES/content/docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"]
    entry = ["DELIVERABLES/changelog_entry.txt", "DELIVERABLES/content/changelog_entry.txt", "COPY/CHANGELOG.md"]
    add("F1", ref, F1_REF_OLD, F1_REF_NEW)
    add("F1", ref, F1_ROW_OLD, F1_ROW_NEW)
    add("F1", entry, F1_CL_OLD, F1_CL_NEW)
    add("F1", ["DELIVERABLES/pr_body.txt"], F1_PR_OLD, F1_PR_NEW)
    add("F1", ["DELIVERABLES/manifest.json"], F1_MAN_OLD, F1_MAN_NEW)
    add("F8", ["COPY/util/ad-hoc/2026-11-14_flood4r2_ml-docs_rederive.py"], F2_RD_OLD, F2_RD_NEW)
    add("F8", ["COPY/CHANGELOG.md"], F2_CL_OLD, F2_CL_NEW)
    add("F3", chs, F3_CH_OLD, F3_CH_NEW)
    add("F3", ["DELIVERABLES/content/history_row.txt", "COPY/docs/REFERENCE.md"], F3_HR_OLD, F3_HR_NEW)
    add("F4", ["DELIVERABLES/commit_body.txt"], F5_CB_OLD, F5_CB_NEW)
    add("F4", entry, F5_CL_OLD, F5_CL_NEW)
    add("F4", entry, F5_CL2_OLD, F5_CL2_NEW)
    add("F4", ["DELIVERABLES/pr_body.txt"], F5_PR_OLD, F5_PR_NEW)
    add("F2", ["DELIVERABLES/pr_body.txt"], F6_PR_OLD, F6_PR_NEW)
    add("F2", ["DELIVERABLES/pr_body.txt"], F6_PR2_OLD, F6_PR2_NEW)
    add("F2", ["DELIVERABLES/manifest.json"], F6_MAN_OLD, F6_MAN_NEW)
    add("F2", ["DELIVERABLES/manifest.json"], F6_MAN2_OLD, F6_MAN2_NEW)
    add("F6", ["DELIVERABLES/pr_body.txt"], F7_PR_OLD, F7_PR_NEW)
    add("F5", ref, F9_REF_OLD, F9_REF_NEW)
    add("F7", ["DELIVERABLES/stamps.json"], F10_ST_OLD, F10_ST_NEW)
    return rows


def resolve(carrier: Path, name: str) -> Path:
    if name.startswith("DELIVERABLES/"):
        return carrier / DELIV / name[len("DELIVERABLES/"):]
    return carrier / name[len("COPY/"):]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--carrier", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scratch", required=True)
    args = ap.parse_args()
    carrier = Path(args.carrier)
    rows = fixes()
    texts: dict[str, str] = {}
    ok = True
    for row in rows:
        path = resolve(carrier, row["file"])
        text = texts.setdefault(row["file"], path.read_text(encoding="utf-8"))
        count = text.count(row["old"])
        row_ok = count == 1
        ok &= row_ok
        print(("ok  " if row_ok else "BAD ") + f"{row['finding']} {row['file']}: old occurs {count}x")
        if row_ok:
            texts[row["file"]] = text.replace(row["old"], row["new"], 1)
    scratch = Path(args.scratch)
    for name, text in texts.items():
        target = scratch / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        if name.endswith(".json"):
            json.loads(text)
        left = [r["finding"] for r in rows if r["file"] == name and r["old"] in text and r["old"] not in r["new"]]
        if left:
            ok = False
            print(f"BAD {name}: an old string survives the fixes: {left}")
    Path(args.out).write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(rows)} fixes; all apply once: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
