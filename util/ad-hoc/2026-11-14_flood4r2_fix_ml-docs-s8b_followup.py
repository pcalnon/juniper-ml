#!/usr/bin/env python3
"""
Build the follow-up edit spec of the ml-docs carrier's session-8 fix-up: the bookkeeping that the text fixes moved.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (Cursor flood-4 session 8: the ml-docs carrier's fix-up, I4)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_flood4r2_fix_ml-docs-s8b_specs.py (the text fixes); util/ad-hoc/2026-11-08_flood4r2_fix_apply_edits.py
         (applies the spec written here, all or nothing)

Three edits, each an exact old -> new on a file of the carrier's tmp/flood4r2/ml-docs/:
  stamps.json      the CHANGELOG position site moves (the entry now follows a blank line and spans more lines), and
                   the re-derive the fix-up ran on main 0578d2ec is recorded with its values;
  probe_message.txt  the title, a blank line and the fixed commit body (it held the body before the fix);
  checks.json      the fix-up's checks are appended to "checks", so the manifest helper carries them.

Usage:
  2026-11-14_flood4r2_fix_ml-docs-s8b_followup.py --carrier <carrier worktree> --landing-tree <dir> --out <spec.json>
"""

import argparse
import json
from pathlib import Path

DELIV = "tmp/flood4r2/ml-docs/"
POS_OLD = "\"line\": 60, \"text\": \"- **Operator documentation consolidated from the Cursor flood-4 round-2 docs drafts** ...\", \"where\": \"top [Unreleased] (:8), group '### Added' (:10), after #2567's entry (:12) and #2548's (:25), before '### Fixed' (:94)\"}"
POS_NEW = "\"line\": 61, \"text\": \"- **Operator documentation consolidated from the Cursor flood-4 round-2 docs drafts** ...\", \"where\": \"top [Unreleased] (:8), group '### Added' (:10), after #2567's entry (:12) and #2548's (:25), one blank line (:60) before it, before '### Fixed' (:97)\"}"
CHECKS_TAIL = "\"log\": \"gpath.log, gtmp.log, codeql_prescreen.log, unused_globals.log, trap_shapes.log\"}\n ],\n \"open_questions\": ["


def fixup_checks() -> list:
    s8b = "s8b/"
    return [
        {"what": "S8b: the session-8 validator's 31 text fixes, each old exactly once (dry run first), applied all or nothing to the carrier tree and content/, with extras X1-X3 and the manifest helper's source", "command": "python3.14 util/ad-hoc/2026-11-08_flood4r2_fix_apply_edits.py s8b/spec_dryrun_31.json ... --dry-run; ... s8b/spec_apply.json s8b/apply.log.json", "result": "pass", "detail": "31/31 old strings once; 38 edits applied; sha256 before/after per file in the log", "log": s8b + "apply.log.json"},
        {"what": "S8b: finding F1 reproduced (the validator's probe, inherited GIT_DIR on a .py and on a .md delta) on main 7ce8d365", "command": "bash runenv.bash python3 util/ad-hoc/2026-11-14_flood4r2_val_ml-docs_scratch_probe.py --repo <7ce8d365 tree> --work s8b/scratch_probe_work --out s8b/scratch_probe.json", "result": "pass", "detail": "md: DAMAGED-FIX-FIRST plain, MERGE-CLEAN with docs_additions_only.status=skip inherited; py: ast_symbol_screen.status=skip inherited", "log": s8b + "scratch_probe.json"},
        {"what": "S8b: re-derive self-check: derive(fixed content/, base a949d504, main a949d504) == the fixed carrier tree", "command": "python3.14 util/ad-hoc/2026-11-14_flood4r2_ml-docs_rederive.py derive --content-dir content --base a949d504 --main a949d504 --landing-date 2026-11-15 --out s8b/selfcheck_out --work-dir s8b/work", "result": "pass", "detail": "6/6 files byte-identical", "log": s8b + "selfcheck_report.json"},
        {"what": "S8b: re-derive on a fresh detached worktree of main 0578d2ec, then the landing read", "command": "stamps.json rederive_command with --main 0578d2ec --landing-date 2026-11-15 --work-dir s8b/work; util/ad-hoc/2026-11-14_flood4r2_fix_ml-docs-s8b_verify_landing.py", "result": "pass", "detail": "exit 0, no conflict; REFERENCE 0.6.72, cheatsheet 1.0.69, overview 0.2.58, quick start 0.3.46, all 2026-11-15; header == footer; row after 0.6.71; entry in [Unreleased] '### Added'; 28 fix texts present; 6 modified + 15 added", "log": s8b + "landing_check_0578d2ec_final.json"},
        {"what": "S8b: re-derive onto the ml-tests fix-up's pull-request tree (eeb5c694 + ml-tests) as --main-dir", "command": "rederive.py derive --content-dir content --base a949d504 --main-dir <ml-tests pull-request tree> --landing-date 2026-11-15 --out s8b/demo_on_mltests_pr_tree", "result": "pass", "detail": "exit 0; the one recorded ERROR-row resolution applied; REFERENCE one step past ml-tests' value", "log": s8b + "demo_on_mltests_pr_tree/report.json"},
        {"what": "S8b: juniper-check-doc-links exactly as AGENTS.md gives it (--exclude tmp, --cross-repo skip) on the 0578d2ec landing tree", "command": "bash runenv.bash python3 -m juniper_doc_tools.cli --exclude templates ... --exclude tmp --cross-repo skip", "result": "pass", "detail": "PASSED, 1662 files", "log": s8b + "doc_links_0578d2ec.log"},
        {"what": "S8b: pinned pre-commit on the 21 files of the 0578d2ec landing tree", "command": "bash runenv.bash xargs -a s8b/files21.txt /opt/miniforge3/bin/pre-commit run --files", "result": "pass", "detail": "exit 0; 13 hooks Passed, the rest out of scope; 21/21 sha256 unchanged", "log": s8b + "precommit_0578d2ec.log"},
        {"what": "S8b: the 25 suites that read these documents (the validator's list) on the 0578d2ec landing tree", "command": "bash runenv.bash python3 util/ad-hoc/2026-11-14_flood4r2_val_ml-docs_suites.py --tree landing=<tree> --suites s8b/doc_suites.txt", "result": "pass", "detail": "25/25 exit 0, 1000 tests, 3.14.7, 4 workers", "log": s8b + "doc_suites_0578d2ec.json"},
        {"what": "S8b: CI's sequence-safety screens and markdown_structure_delta on probe commit 0df5c1f1 (main 0578d2ec + the 21 files; final title and fixed commit body)", "command": "bash runenv.bash python3 util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py --freeze s8b/freeze --title pr_title.txt --body commit_body.txt --scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash' --main-ref 0578d2ec; python3 util/markdown_structure_delta.py --base 0578d2ec --head 0df5c1f1", "result": "pass", "detail": "symbol-loss 0 findings (15 files); docs 0 FAIL, 45 WARN small-deletion; structure 0 regressions (6 files)", "log": s8b + "screens/"},
        {"what": "S8b: G-PATH, G-TMP, CodeQL prescreen, unused globals and the seven shapes on rederive.py, manifest.py and the fix-up's two new helpers", "command": "python3.14 util/home_path_literal_check.py ...; util/tmp_path_literal_check.py ...; util/ad-hoc/2026-10-05_codeql_python_prescreen.py ...; util/ad-hoc/2026-11-09_flood4r2_land_unused_globals.py ...; 2026-11-11_flood4r2_n4-r2_trap_shapes.py --known-answer and the files", "result": "pass", "detail": "0 literal lines; 0 predicted alerts; 0 unused globals; known answer PASS, 0 hits", "log": "PROGRESS.txt"},
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--carrier", required=True)
    ap.add_argument("--landing-tree", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    carrier = Path(args.carrier).resolve()
    deliv = carrier / DELIV
    landed = {
        "main": "0578d2ec (juniper-ml#2571; re-fetched 2026-11-15 02:32Z)",
        "tree": args.landing_tree,
        "command": "rederive_command above, with --main 0578d2ec --landing-date 2026-11-15 --work-dir <scratch>",
        "result": "exit 0, no conflict (s8b/derive_report_0578d2ec.json; read by s8b/landing_check_0578d2ec_final.json, ok)",
        "values": {
            "docs/REFERENCE.md": "0.6.71 -> 0.6.72: header :5 == footer :10258, dates :7 and :10257, Version History row :9703 directly after main's 0.6.71 row :9702",
            "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md": "1.0.68 -> 1.0.69: :3 / :1293, dates :4 / :1292",
            "docs/DOCUMENTATION_OVERVIEW.md": "0.2.57 -> 0.2.58: :5 / :281, dates :7 / :280",
            "docs/QUICK_START.md": "0.3.45 -> 0.3.46: :5 / :233, dates :7 / :232",
            "CHANGELOG.md": "entry :78 in the top [Unreleased] (:8), its only '### Added' (:10), after #2548's entry with one blank line (:77), before '### Changed' (:114)",
        },
    }
    history_anchor = "  \"if_main_moves\": [\n"
    stamps_text = (deliv / "stamps.json").read_text(encoding="utf-8")
    if stamps_text.count(history_anchor) != 1:
        raise SystemExit("stamps.json: the if_main_moves anchor is not there exactly once")
    landed_line = "  \"session8_fixup_rederived_on_0578d2ec\": " + json.dumps(landed, ensure_ascii=False) + ",\n"
    title = (deliv / "pr_title.txt").read_text(encoding="utf-8").rstrip("\n")
    old_body = (deliv / "pre-s8b" / DELIV / "commit_body.txt").read_text(encoding="utf-8")
    new_body = (deliv / "commit_body.txt").read_text(encoding="utf-8")
    probe_now = (deliv / "probe_message.txt").read_text(encoding="utf-8")
    if probe_now != f"{title}\n\n{old_body}":
        raise SystemExit("probe_message.txt is not the title, a blank line and the pre-fix commit body")
    checks_new = CHECKS_TAIL.replace("\"}\n ],", "\"},\n" + ",\n".join("  " + json.dumps(row, ensure_ascii=False) for row in fixup_checks()) + "\n ],", 1)
    edits = [
        {"id": "S1-position", "file": DELIV + "stamps.json", "old": POS_OLD, "new": POS_NEW},
        {"id": "S2-landed", "file": DELIV + "stamps.json", "old": history_anchor, "new": landed_line + history_anchor},
        {"id": "S3-probe-message", "file": DELIV + "probe_message.txt", "old": probe_now, "new": f"{title}\n\n{new_body}"},
        {"id": "S4-checks", "file": DELIV + "checks.json", "old": CHECKS_TAIL, "new": checks_new},
    ]
    Path(args.out).write_text(json.dumps({"worktree": str(carrier), "edits": edits}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(edits)} edits -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
