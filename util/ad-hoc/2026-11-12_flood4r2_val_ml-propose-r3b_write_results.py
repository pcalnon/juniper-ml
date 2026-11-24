#!/usr/bin/env python3
"""
Write the quick check's findings.json and text_fixes.json, and prove each text fix's old string occurs exactly once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14; juniper-ml#2558

WHY THIS EXISTS
The findings are long, quote backticks and quotation marks, and must stay valid JSON after every rewrite. They are
kept here as Python data and serialized, so a quoting slip cannot leave a broken file, and every text fix is
checked against the files it names before it is written: its old string must occur exactly once in the
carrier's deliverable and in the copy the landing helper wrote (DELIVERABLES/<name>), or in the landed file
(COPY/<repo path>).

Usage:
    python3 <this> --status in-progress|final
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
ML = JUNIPER / "juniper-ml"
ORCHESTRATOR = ML / ".claude" / "worktrees" / "humming-stargazing-papert"
CARRIER = ML / ".claude" / "worktrees" / "agent-a211deee35ec85ad3"
DELIVERABLES = CARRIER / "tmp" / "flood4r2" / "ml-propose" / "r3b"
SCRATCH = ORCHESTRATOR / "tmp" / "flood4r2-val" / "ml-propose-r3b-quick-s7"
WORKTREES = JUNIPER / "worktrees"
LANDED = WORKTREES / "juniper-ml--val--flood4r2-ml-propose-r3b--20261112-2019--f9582a74"
AFTER_2558 = WORKTREES / "juniper-ml--val--flood4r2-ml-propose-r3b-after2558--20261112-2044--d4dcefbc"
TWIN = ML / ".claude" / "worktrees" / "agent-a61564fc0ee03e2a2"
HELPERS = ORCHESTRATOR / "util" / "ad-hoc"
LAND = f"python3 {CARRIER}/util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_land.py --carrier {CARRIER}"
PREFIX = f"python3 {HELPERS}/2026-11-12_flood4r2_val_ml-propose-r3b_"

TEXT_FIXES = [
    {
        "finding": "F3",
        "when": "always",
        "file": "DELIVERABLES/pr_body.txt",
        "old": "The pristine, patch and minor rows were then run again on a tree that holds #2555's own changes (its head `067f5547`) on top of juniper-ml#2554's, with the same counts.",
        "new": "The pristine, patch and minor rows were then run again on a tree that holds #2555's own changes (its head then, `067f5547`) on top of juniper-ml#2554's, with the same counts. Both have merged since, #2554 as `b6b843b6` and #2555 as `26ea0ecb`; in that commit `pyproject.toml`, `tests/test_pyproject_extras.py`, `README.md` and `docs/QUICK_START.md` are byte for byte what `067f5547` held. The three rows were run a third time on `main` `f9582a74`, which holds both, with the tests carrier's gate file as it stood then (sha256 `1ee53200`): its 20 tests pass before a proposal; the unextended script's patch proposal fails 3 of the 8 and its minor proposal 4; with this PR the 8, the 20 and the propose suite's 188 pass after both.",
    },
    {
        "finding": "F4",
        "when": "always",
        "file": "DELIVERABLES/pr_body.txt",
        "old": "and every check below except the full mutation run was made again there.",
        "new": "and every check below except the full mutation run was made again there. `main` has gained nine commits since (to `ae801a70`); three of them, juniper-ml#2554, #2555 and #2557, change `CHANGELOG.md` and `docs/REFERENCE.md`. The 22 files were landed on `f9582a74` with the landing command (both documents rebuilt three-way, no conflict; the other 20 files byte for byte) and these were measured there: the propose suite, 188 against 156; `main`'s propose.py under these tests, 11 failures and 29 errors; the 59 mutants, 56 killed; the patch and minor rows of the table; pre-commit, the CodeQL prescreen, the shape scan and both gates; and CI's two sequence-safety screens, which pass with no waiver. CI's regression list has 239 suites there, not 234, and it was not run whole: of the 79 suites that name a file this PR changes or walk `util/`, `notes/` or `docs/`, 77 pass, and the two that fail (`tests/test_a0_restore_scripts.py`, `tests/test_workflow_script_paths.py`) fail the same tests on a clean `f9582a74`.",
    },
    {
        "finding": "F5",
        "when": "always",
        "file": "DELIVERABLES/pr_body.txt",
        "old": "That carrier's copy of the file (sha256 `a4d2dc83`) was only run here",
        "new": "That carrier's round-1 copy of the file (sha256 `a4d2dc83`) was only run here",
    },
    {
        "finding": "F6",
        "when": "always (juniper-ml#2558, 'release: juniper-ml v0.11.5 (proposal)', is open, so 'the 0.11.5 proposal' now names a real pull request that did not do this)",
        "file": "DELIVERABLES/pr_body.txt",
        "old": "On that tree the 0.11.5 proposal changes two tokens of the paragraph",
        "new": "On that tree a 0.11.5 proposal built by this PR's propose.py changes two tokens of the paragraph",
    },
    {
        "finding": "F6",
        "when": "only while juniper-ml#2558's head is d4dcefbc (re-run the compare helper if it moved)",
        "file": "DELIVERABLES/pr_body.txt",
        "old": "and the REVIEW line does not name them: it asks about the history in general and names the renamed clause.",
        "new": "and the REVIEW line does not name them: it asks about the history in general and names the renamed clause. juniper-ml#2558, the 0.11.5 proposal opened on 2026-11-13, was built by the unextended script. Its generated commit (`8764f5cf`) changes no line of `docs/REFERENCE.md`. Its second commit (`d4dcefbc`) sets by hand the Version cell that this PR's propose.py writes, byte for byte, and makes the same two renames in the paragraph; it also rewords the raise's words and the words after the clause's pins, which the script never writes.",
    },
    {
        "finding": "F7",
        "when": "optional, and only once juniper-ml#2558 has merged (the sentence is true as written, one cut behind)",
        "file": "DELIVERABLES/pr_body.txt",
        "old": "Each cut from 0.11.0 to 0.11.4 rewrote whichever of them moved with a one-off `util/ad-hoc/*_cut_cochanges.py` script.",
        "new": "Each cut from 0.11.0 to 0.11.5 rewrote whichever of them moved with a one-off `util/ad-hoc/*_cut_cochanges.py` script (the 0.11.5 cut is juniper-ml#2558).",
    },
]


def check_text_fixes() -> list:
    problems = []
    for index, fix in enumerate(TEXT_FIXES, start=1):
        kind, _, rest = fix["file"].partition("/")
        targets = [DELIVERABLES / rest, SCRATCH / "land" / "texts" / rest] if kind == "DELIVERABLES" else [LANDED / rest]
        counts = {str(target): target.read_text(encoding="utf-8").count(fix["old"]) for target in targets}
        fix["old_occurrences"] = counts
        if set(counts.values()) != {1}:
            problems.append(f"text fix {index} ({fix['finding']}): old occurs {counts}")
        if not fix["new"] or fix["new"] == fix["old"]:
            problems.append(f"text fix {index}: new is empty or equal to old")
    return problems


def findings(status: str) -> dict:
    after_cut = [
        "git -C <your own juniper-ml worktree> fetch origin",
        "git -C <your own juniper-ml worktree> worktree add --detach <D> origin/main",
        f"{LAND} --dest <D> --landing-date <UTC date> --out <OUT>/dry --dry-run      # EXPECT exit 1 and exactly ONE line that starts with PROBLEM: \"CHANGELOG.md: the entry is not under the top [Unreleased] (headings above it: ['## [Unreleased]', '## [0.11.5] - ...'])\"; every file line starts with ok; docs/REFERENCE.md shows main's Version + 0.0.1. Any other PROBLEM, or a conflict: stop. Exit 0 instead means main's [Unreleased] is not empty: then the one command of 'landing' is the whole procedure.",
        f"{LAND} --dest <D> --landing-date <UTC date> --out <OUT>/land               # exit 1 AGAIN, and this time the 22 files ARE written into <D>, the CHANGELOG entry inside ## [0.11.5]. <D> is not a landing tree until the next two commands pass.",
        f"{PREFIX}changelog_after_cut.py --tree <D> --entry <OUT>/land/texts/changelog_entry.txt      # exit 0, prints: written: {{'occurrences': 1, 'first_line': 12, 'release_headings_above': ['## [Unreleased]'], 'subsection': '### Fixed'}}. It writes main's CHANGELOG.md plus one block under the empty [Unreleased] and refuses anything else.",
        f"{PREFIX}landing_check.py --landed <D> --out <OUT>/check --since <the merge commit of #2558> --since f9582a74      # exit 0 and no PROBLEM line; changelog: release_headings_above == ['## [Unreleased]'], subsection '### Fixed'; reference: expected_landed_stamp == the new row; the only removed lines are the two **Version:** stamp lines.",
        f"{PREFIX}run_suites.py --tree <D> --python /opt/miniforge3/bin/python3.12 --out <OUT>/suites --label landed-py312 --suite tests/test_release_train_propose.py --workers 1      # ran 188, OK (repeat with /opt/miniforge3/envs/JuniperCascor1/bin/python)",
        f"{PREFIX}simulate.py --make --landed <D> --gate <the tests carrier's tests/test_pyproject_extras.py> --sims <a NEW directory under {WORKTREES}, outside every juniper-ml checkout> --out <OUT>/sim --patch-version 0.11.6 --minor-version 0.12.0      # landed--patch and landed--minor: 'after gate OK (20), class OK (8) ... propose suite OK (188)'; the main--* rows report 'CHANGELOG move refused' (main's [Unreleased] is empty)",
        f"{PREFIX}make_freeze.py --landed <D> --out <OUT>/freeze",
        f"python3 {HELPERS}/2026-11-12_flood4r2_s6_seqsafety_probe.py --freeze <OUT>/freeze --title <OUT>/land/texts/pr_title.txt --body <OUT>/land/texts/commit_body.txt --out <OUT>/seqsafety --scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash' --repo-dir <D> --main-ref HEAD      # symbol screen exit=0 ; docs screen exit=0",
        "env -C <D> <the six Sentry DSN variables set empty> /opt/miniforge3/bin/pre-commit run --files <the 22 paths>      # 17 Passed, 9 Skipped, 0 Failed, no file modified",
        "PR texts: <OUT>/land/texts/{pr_title,commit_body}.txt as they are; <OUT>/land/texts/pr_body.txt (its Stamps line is re-derived) with text_fixes.json applied; the CHANGELOG entry is <OUT>/land/texts/changelog_entry.txt, byte for byte.",
        "gh pr view 2558 --repo pcalnon/juniper-ml --json state,headRefOid,mergeCommit      # if the merged head is not d4dcefbc90288cc09b3cb3d0b74911c54ff168d0, re-run compare_2558.py (its usage line) before using the fifth text fix, and read `git -C <D> log -1 --stat <merge commit>`: anything beyond its seven files is new.",
    ]
    return {
        "carrier": f"ml-propose (juniper-ml; uncommitted at {CARRIER}, base 15b5d9bb, 22 files, round 3b; ruling 14, 'Carry + extend propose.py')",
        "lens": "QUICK CHECK K2 (flood-4 session 7): the landing on today's main, the round-3 code and tests, the ruling's point, the texts, the screens; plus check F, the real 0.11.5 proposal (juniper-ml#2558), added by the coordinator during the run",
        "status": status,
        "verdict": "SHIP-WITH-FIXES. The code, the tests and the three documents are sound on today's main (f9582a74 landed; ae801a70 dry run, same bytes). Do NOT use the one landing command once juniper-ml#2558 has merged (F1), and settle the order against #2558 first (F2).",
        "severity_counts": {"BLOCKER": 1, "MAJOR": 1, "MINOR": 5, "note": "the BLOCKER is conditional: it exists only on a main that holds juniper-ml#2558; on today's main there is none"},
        "scratch": f"{SCRATCH} (every evidence path below without a root is under it)",
        "main_sha_used": "f9582a749d190a3242aae9cb16c521199bd53013 for every check (landing written there). origin/main moved to ae801a70fa815a3e312777a0fe3a08e1d6c7bc80 at 02:49Z (juniper-ml#2559: ONE file, tests/test_duplicati_scheduled_backup.py, +66), verified by fetch; the landing helper's dry run on a worktree at ae801a70 exits 0 and assembles CHANGELOG.md (sha256 c45e9bc2...) and docs/REFERENCE.md (d290cd6c...) byte-identical to the f9582a74 landing, with the same pr_body.txt (land-on-ae801a70-dry/). Nothing of the carrier needs re-deriving for #2559.",
        "landing": {
            "command": f"{LAND} --dest <a detached worktree of origin/main> --landing-date 2026-11-13 --out <scratch dir>",
            "on_main": {
                "result": "CORRECT on f9582a74 (written into my worktree) and on ae801a70 (dry run): exit 0, no PROBLEM line, nothing to do by hand",
                "worktree": str(LANDED),
                "next_number_without_help": "yes: docs/REFERENCE.md 0.6.69 -> 0.6.70, header :5 == footer :9982; both Last Updated lines already 2026-11-13 on main and stay",
                "history_row": "| 0.6.70  | 2026-11-13 | ... at :9427, directly after main's highest row (0.6.69, :9424 on main, :9426 landed); no version twice in the table, on main or landed",
                "runbook": "1.2.4 / 2026-10-26 -> 1.2.5 / 2026-11-13 (main unchanged since the carrier's base: landed bytes == the carrier's)",
                "changelog": "+47/-0, one block at :282 under the top ## [Unreleased] -> ### Fixed, fourth of twelve entries, between the same two entries as in the carrier",
                "reverts": "none. Lines that b6b843b6 (#2554), 26ea0ecb (#2555) or f9582a74 (#2557) added to CHANGELOG.md or docs/REFERENCE.md and that the landing removes: only the two '**Version:** 0.6.69' stamp lines (#2557's), replaced by 0.6.70",
                "other_files": "util/release_train/propose.py (sha256 0f4038d0...) and tests/test_release_train_propose.py (4f3a945c...) are the carrier's bytes (main's blobs of both are unchanged from 15b5d9bb to f9582a74); the 17 added helpers are the carrier's bytes",
                "sha256": {"CHANGELOG.md": "c45e9bc2fafe05c9aaec52a1480b18e0e121b40513c52360ca2e2bc019797eb3", "docs/REFERENCE.md": "d290cd6c78a68a5625ce6843e79c8d6f57f92c9d75932ac74449a335cb571f87"},
                "texts": "land/texts/: pr_title.txt and commit_body.txt identical to the carrier's; pr_body.txt differs in the '- Stamps:' line only (0.6.69 -> 0.6.70). Use that copy.",
                "evidence": "land/landing_report.json (the helper's); landing-check/landing_check.json and *.diff (mine, independent: zero-context change blocks with their neighbours; exit 0)",
            },
            "on_main_after_pr_2558": "see real_proposal_2558: the same command exits 1 AFTER writing a tree whose CHANGELOG entry is inside ## [0.11.5]",
        },
        "checked": [
            "CARRIER INTACT (session-6 addendum, section 1): 22 of 22 files equal manifest.json's sha256 at the start and at the end; status re-derived from blob hashes without running a version-control command in the carrier: 5 modified, 17 added, 0 deleted; the nine deliverable texts unchanged since the dead session-6 agent's 01:22Z record (verify_carrier_start.json, verify_carrier_end.json).",
            "A. THE LANDING, once, on f9582a74, in my own detached worktree, then re-derived from the landed bytes with my own helper (not the landing helper's multiset): see 'landing'.",
            "B. PROPOSE SUITE on the landed tree: 188 OK on Python 3.12.11 (/opt/miniforge3/bin/python3.12) and 3.14.7 (JuniperCascor1); clean f9582a74: 156. AST count: 156 -> 188 test methods, ReferenceCompatHelperTest 21 + BuildProposalReferenceCompatTest 11 = 32 new, none added to an existing class, none removed (claims.json).",
            "B. THE NEW TESTS FAIL ON THE CODE THEY ARE FOR: main's propose.py (sha256 e5dd0e02...) under the carrier's test file, in my twin: FAILED (failures=11, errors=29), 32 distinct tests = 31 of the 32 new ones + test_meta_self_bump_moves_the_readme_compat_lead_in; the one new test that passes is test_escaping_subpackage_bump_without_a_column_leaves_the_release_sites_alone (mut/MAIN.suite.log, claims.json).",
            "B. F2 IS NOT VACUOUS AND NO LONGER BREAKS ON A PARAGRAPH BREAK. Vacuity: run ALONE, the live-file control fails on four code mutants (K1 the sentence writer rewrites other lines; K2 the new row twice; K3 a wrong series label; K5 the clause found only on the sentence's line) and on four changes to the live docs/REFERENCE.md (R2 the sentence without its period; R3 a second Version cell; R4 the heading renamed; R5 the clause's verb plural). K5 is killed by the control's parted run and by no other test of the 188. Paragraph break: with the clause parted from the sentence in the LIVE file (R1) the control and the whole suite pass (188); round 2's control (its test file, sha256 1bb1266c) FAILS on that same file (R2TEST) -- the defect F2 named, reproduced.",
            "B. F3's FIVE CHECKLIST MUTANTS EACH DIE (the final check's definitions, re-applied to the landed propose.py): S3 by test_escaping_subpackage_bump_moves_its_matrix_cell_in_the_one_reference_edit; S5 and S13 by test_escaping_subpackage_bump_that_cannot_reach_its_row_is_required_and_a_patch_owes_nothing; S6 and S7 by test_meta_patch_bump_names_the_release_and_keeps_the_series_row.",
            "B. MY OWN 14 MUTANTS of what round 3 changed (K1-K14, none from the carrier's lists): 14 killed by the suite; K8 (a row the pin did reach, marked REQUIRED) and K10 (the F8 wording) each die on exactly one round-3 assertion, and K5 on the live control's parted run alone. K4 (row position) and K6 (cell width) pass the live control alone and die in fixture tests, as designed. Every file restored in a finally block, sha256 compared after each of the 26 runs; the twin's hashes at the end equal those written to PROGRESS.txt before the run (mut/mutants.json).",
            "B. THE CARRIER'S OWN 59 MUTANTS, re-run with its script on a scratch tree built from my twin at f9582a74: 56 killed (round 2's 38 of 38; the final check's 10 of 13, S8 S11 S12 surviving as recorded; live 8 of 8), target restored (mut-carrier59/mutation_results.json).",
            "B. DISPOSITIONS F1-F8: each read in the landed files. F1: the old wordings ('carried in the round-2 tests carrier', 'merges before this PR') occur 0 times in the five landed files; the three texts state the order. F2 and F3: above. F4: the landing. F5: see findings F3-F5 (the figures are honest about their base, and that base is no longer the landing's). F6: not this carrier's; the round-2 gate file has both tests on non-live literals. F7: the history row names the Version cell under Package Overview. F8: 'restore the pins that series' last release published' once in each of propose.py, its test, CHANGELOG.md, docs/REFERENCE.md and the runbook; the old string 0 times. No fix broke another: 188 OK and every mutant accounted for.",
            "C. THE RULING'S POINT on f9582a74 with the tests carrier's ROUND-2 gate file (agent-abd21f5554a19c89f/tests/test_pyproject_extras.py, sha256 1ee532009b13..., equal to the value in that carrier's copy_tree_final_bytes.json and manifest.json; frozen copy gate/test_pyproject_extras.round2.py; main's own copy of the file is one blob at 26ea0ecb and f9582a74, so its three-way rebuild holds on today's main). Six fresh `git archive` sandboxes outside juniper-ml, the proposal built by each sandbox's own propose.build_proposal and written edit by edit: main + gate, no proposal: 20 OK (ReferenceCompatibilityMatrixTest 8 OK). main's propose.py: PATCH 0.11.5 -> 3 of 8 fail (the sentence, the Version cell, the clause); MINOR 0.12.0 -> 4 of 8 fail (+ the series row). With the carrier: PATCH and MINOR -> 8 of 8, the gate file's 20 and the propose suite's 188 pass after the proposal (sim/summary.json). My simulator's pyproject.toml, AGENTS.md, README.md and CHANGELOG.md for 0.11.5 are byte-identical to the generated commit of the real proposal, juniper-ml#2558 (compare_2558.json).",
            "C. THE SENTENCE #2555 ADDED (docs/REFERENCE.md:184): the 0.11.5 proposal changes exactly two tokens of the paragraph (0.11.4 -> 0.11.5 in the 'declares' sentence and in the clause). 'The `0.11.x` row is 0.11.4's, and its floors are 0.11.2's, except the `juniper-observability` cell: it holds `main`'s floor, `>=0.4.2` (unreleased; first in juniper-ml 0.11.5), where the published 0.11.4 declares `>=0.4.1`.' is kept verbatim, and so is '`main` raises it to `>=0.7.2,<0.8.0` (unreleased; first in juniper-ml 0.11.5).' The REVIEW line names neither: it names the renamed clause and the history in general (sim/landed--patch.proposal.json).",
            "D. THE TEXTS: gh on 2026-11-13: #2507 OPEN, draft, head 3263db9e; #2554 MERGED b6b843b6 (head f0993179); #2555 MERGED 26ea0ecb from head a6efd625 (not the 067f5547 the PR body names: F3); #2557 MERGED f9582a74; #2548 OPEN, head 5099d14c; the tests carrier is not merged; ReferenceCompatibilityMatrixTest occurs 0 times in main's tests/test_pyproject_extras.py. Counts and history re-derived (claims.json): 156 -> 188, 21 + 11; 11 failures and 29 errors, 32 of 34; 56 of 59; 3 and 4 of 8; at tag v0.11.4 the 0.11.x row equals pyproject at v0.11.2, v0.11.3 and v0.11.4 and not at v0.11.0 or v0.11.1, and the 0.6.x row equals v0.7.0 and v0.7.1 and not v0.6.0; #1991 (594bb5dd) added the 0.9.x row, rewrote none, and its message says 'ADDED TO rather than rewritten'; #2306 added 0.11.x; #2319 and #2339 rewrote 0.11.x in place; of the in-repo packages only juniper-doc-tools has both a ceiling and a matrix column; five *_cut_cochanges.py scripts are on main; every script the PR body cites exists on main or ships in the PR. No text promises a later pull request beyond the stated order (this change, then the tests carrier), names another session, plan or register id, or says 0.11.5 is released.",
            "E. THE SCREENS on the landed tree: CodeQL prescreen 0 predicted alerts in the 19 Python files; the seven-shape scan 0 hits (its known-answer control passes, 9 of 9); G-PATH PASS (18 in scope) and G-TMP PASS (19); the pinned pre-commit on the 22 files in my worktree: 17 Passed, 9 Skipped, 0 Failed, no file modified (sha256 before == after).",
            "E. SEQUENCE SAFETY: CI's two commands (same scopes as ci.yml:1826 and :1835) on probe commit 42e0476425a1 (tree 0941adfd41c0, parent f9582a74, message = the carrier's title + blank line + commit body, 22 adds): symbol-loss exit 0 (19 files screened, 0 findings); docs screen exit 0 (2 files, 3 WARN small-deletion on stamp lines, fail=0). No Allow-Symbol-Loss or Allow-Docs-Rewrite value is needed.",
            "E. CI REGRESSION SUITES THAT READ WHAT THE CARRIER CHANGES, one process per suite, 3 at a time, Python 3.14.7, on the landed tree: 79 of ci.yml's 239 (38 name docs/REFERENCE.md, CHANGELOG.md, the runbook, the release train or propose.py; 41 more walk a tree and name util, ad-hoc, notes or docs; the list with each reason: reader_suites_selection.json). 77 pass, 3,153 tests. tests/test_workflow_script_paths.py (1 failure) and tests/test_a0_restore_scripts.py (10) fail with the same test ids on a clean f9582a74 worktree (suites/).",
            "F. THE REAL PROPOSAL: see real_proposal_2558.",
        ],
        "not_checked": [
            "GitHub's own CodeQL analysis, the macOS job, a CI-parity secret scan of the new files.",
            "CI's whole regression list (239 suites): 79 were run. The PR body's '37 suites x 2 trees x 2 interpreters' and '48 suites that walk util/' figures were not re-measured.",
            "Rows 3 to 9 of the PR body's table (the hand-raise scenarios and the paragraph-break scenario through build_proposal) on today's main: only pristine, patch and minor were run. The paragraph break was run on the live file through the suite (R1).",
            "The detector end to end (detect.py --json feeding propose.py) and --execute. A proposal was built by build_proposal with live file reads and an empty open-PR list.",
            "The carrier's 17 helper scripts beyond the three I ran (land, r3_assemble through it, r3_mutation_check): screened only.",
            "juniper-ml#2558 itself (whether its hand edits are right), how the Release ceremony renders the [0.11.5] section, and the tests carrier beyond its gate file.",
            "A landing on a main that holds BOTH #2558 and #2559: #2559 is one test file neither touches, so the tree at #2558's head was used for check F.",
        ],
        "findings": [
            {
                "id": "F1",
                "severity": "BLOCKER (conditional: only on a main that holds juniper-ml#2558, the open 0.11.5 release proposal; none on today's main)",
                "where": "util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_land.py:191-199 and :261-262 (it runs the assemble helper, which writes, BEFORE its own checks), util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3_assemble.py:215-219; DELIVERABLES/REPORT.txt:53 ('Otherwise exit 1, nothing written into --dest')",
                "claim": "On main after #2558 the one landing command files the carrier's CHANGELOG entry INSIDE the released section, '## [0.11.5] - 2026-11-13' -> '### Fixed' (CHANGELOG.md:285), with 0 conflicts: #2558 moves the entries the carrier's entry was written between under the new heading, and the three-way rebuild follows them. The helper's own check then reports it and exits 1, but all 22 files are already written into --dest: 'exit 1, nothing written' is false for a check that fails after a clean rebuild. The helper can never exit 0 on such a main: it wants the entry below another [Unreleased] entry, and #2558 leaves '## [Unreleased]' with no entry and no ### heading. This repository has filed a bullet under a released heading this way twice (juniper-ml#2002 after v0.9.0; juniper-ml#2360 after v0.11.4, which #2558's own cut script repairs).",
                "evidence": "Worktree detached at #2558's head d4dcefbc (two commits directly on f9582a74, so its tree is main after the PR). land-after-2558.stdout: 'PROBLEM CHANGELOG.md: the entry is not under the top [Unreleased] (headings above it: ['## [Unreleased]', '## [0.11.5] - 2026-11-13'])' and 'main d4dcefbc <- carrier base 15b5d9bb; written into <the worktree>; ... NOT OK', exit 1; `git status --porcelain` there: 5 modified + 17 untracked. landing-check-after-2558/landing_check.json: changelog.landed_first_line_of_entry 285, release_headings_above ['## [Unreleased]', '## [0.11.5] - 2026-11-13']. The same with --dry-run: exit 1, nothing written (land-after-2558-dry.stdout). First seen on a simulated cut (probe commit 20db12ec, land-after-cut/).",
                "fix": "No change to the carrier. At the freeze, if #2558 has merged: run the landing command with --dry-run first and treat its exit status as the only signal; then the procedure in real_proposal_2558.at_the_freeze_if_2558_has_merged (the landing command, then util/ad-hoc/2026-11-12_flood4r2_val_ml-propose-r3b_changelog_after_cut.py, then my landing check, which must exit 0). Measured in my after-2558 worktree: the entry at CHANGELOG.md:12 under '## [Unreleased]' -> '### Fixed', the file = main's + that one block (+49/-0), landing check exit 0, propose suite 188, the sequence-safety screens and pre-commit pass. A code fix, if one is wanted later: have land.py call the assemble helper with --dry-run, check, and only then write.",
            },
            {
                "id": "F2",
                "severity": "MAJOR",
                "where": "the landing order against juniper-ml#2558 (CHANGELOG.md; no file of the carrier is wrong)",
                "claim": "A correct landing on today's main does not stay as landed. If the carrier merges first and #2558 merges after it, #2558's merge moves the carrier's entry under '## [0.11.5] - 2026-11-13' as well, with no conflict and with no one deciding it. So in either order the entry ends under the 0.11.5 heading unless someone acts, and the only order that leaves it under [Unreleased] untouched is: #2558 first, then this carrier by the after-2558 procedure. Which heading is right depends on a fact this arc does not own: whether the v0.11.5 tag will carry this change (it will, if the carrier is on main when the Release is cut; #2558's cut script moved #2360's bullet to [0.11.5] on exactly that ground), and whether the Release body, rendered from that section, may gain an entry after the proposal was reviewed.",
                "evidence": "`git merge-tree --write-tree 42e0476425a1 refs/flood4r2v/pr/2558` (main + the landed carrier, merged with #2558's head) -> tree bf884f94e7b8bfbeb6f1e5e34b7d2fc65283163c, no conflict; `git grep -n` in that tree's CHANGELOG.md: '## [Unreleased]' :8, '## [0.11.5] - 2026-11-13' :10, the carrier's entry :285, '## [0.11.4] - 2026-11-06' :531. util/ad-hoc/2026-11-13_juniper_ml_0_11_5_cut_cochanges.py (in #2558), docstring: 'A bullet under the wrong release. juniper-ml#2360 merged on 2026-11-12, six days after v0.11.4 was tagged ... The v0.11.4 tag does not carry that change and the v0.11.5 tag does, so the bullet moves'.",
                "fix": "A decision, not an edit; it is the orchestrator's to take to the Overtoad with the arc that owns #2558. (a) Land now, before #2558 merges, and tell that arc its merge will carry this entry into [0.11.5]: consistent if v0.11.5 is tagged after both. (b) Land after #2558 merges and before the Release: the entry goes under [Unreleased] by the after-2558 procedure, and the v0.11.5 tag then carries a change its section does not list. (c) Land after the v0.11.5 Release is cut: [Unreleased], with no question left. Whichever is chosen, read CHANGELOG.md's headings above the entry on main after BOTH have merged.",
            },
            {
                "id": "F3",
                "severity": "MINOR",
                "where": "DELIVERABLES/pr_body.txt:26",
                "claim": "The PR body says the three rows were re-run on 'a tree that holds #2555's own changes (its head `067f5547`)'. #2555 merged at 2026-11-13T00:49:00Z as 26ea0ecb from head a6efd625, so the head it names is not the one that merged, and the paragraph still speaks of #2555 as an open pull request. Only the text is stale: pyproject.toml, tests/test_pyproject_extras.py, README.md and docs/QUICK_START.md are identical at 067f5547 and 26ea0ecb, the quoted sentence occurs once at 067f5547, 26ea0ecb and f9582a74, and the counts hold on f9582a74.",
                "evidence": "gh pr view 2555: state MERGED, headRefOid a6efd6259416cf190944b2cb873cfea76cddcdb1, mergeCommit 26ea0ecb, mergedAt 2026-11-13T00:49:00Z. `git diff --stat 067f5547 26ea0ecb -- pyproject.toml tests/test_pyproject_extras.py README.md docs/QUICK_START.md`: empty. `git grep -c -F <the quoted sentence>` at the three commits: 1, 1, 1. sim/summary.json.",
                "fix": "text_fixes.json entry 1.",
            },
            {
                "id": "F4",
                "severity": "MINOR",
                "where": "DELIVERABLES/pr_body.txt:38 and :65",
                "claim": "The final check's F5 again, one step milder: 'Every figure was measured on this tree: origin/main 15b5d9bb plus this PR's 22 files' is true and labelled, but the tree that lands is nine commits later (#2549, #2551, #2550, #2553, #2554, #2555, #2556, #2557, #2559), and three of them rewrote the two documents the landing rebuilds. One figure is no longer the landing tree's: CI's regression list has 239 suites on f9582a74, not 234. The others I re-measured come out the same (188 and 156; 11 and 29; 56 of 59; 3 and 4 of 8; 17 and 9; 0 alerts).",
                "evidence": "`git log 15b5d9bb..origin/main`: nine commits. reader_suites_selection.json: suites_in_ci_list 239. suites/*/summary.json, mut/mutants.json, mut-carrier59/mutation_results.json, sim/summary.json, screens/.",
                "fix": "text_fixes.json entry 2 (it adds what was measured on the landing tree and keeps the build-time figures, labelled).",
            },
            {
                "id": "F5",
                "severity": "MINOR",
                "where": "DELIVERABLES/pr_body.txt:34",
                "claim": "'That carrier's copy of the file (sha256 `a4d2dc83`)' names the tests carrier's round-1 file. That carrier's tree now holds its round-2 file (sha256 1ee53200..., built on 26ea0ecb, two tests on non-live literals) and is still being finished, so a reader who checks the hash finds another.",
                "evidence": "sha256sum agent-abd21f5554a19c89f/tests/test_pyproject_extras.py -> 1ee532009b132004d11e2e2b0b8f4a5359b129ddfae461b3fcaff57bd814ddf6; its tmp/flood4r2/ml-tests/r2/copy_tree_final_bytes.json and manifest.json record the same value.",
                "fix": "text_fixes.json entry 3 ('round-1 copy'). Entry 1 states what the round-2 file gave.",
            },
            {
                "id": "F6",
                "severity": "MINOR",
                "where": "DELIVERABLES/pr_body.txt:26 (second half)",
                "claim": "'On that tree the 0.11.5 proposal changes two tokens of the paragraph ... and leaves the raise's own words (...) byte for byte' describes a proposal the builder simulated. Since 02:32Z a real 'release: juniper-ml v0.11.5 (proposal)' exists (juniper-ml#2558), built by the unextended script, and it did the opposite: it reworded those words by hand. Once it merges, main no longer holds the sentence the PR body quotes. Read today, 'the 0.11.5 proposal' names the wrong thing.",
                "evidence": "gh pr view 2558 (OPEN, head d4dcefbc, created 2026-11-13T02:32:19Z). compare_2558.json: words_main_to_pr replaces 'the `juniper-observability` cell: it holds `main`'s floor, `>=0.4.2` (unreleased; first in juniper-ml 0.11.5), where the published 0.11.4 declares `>=0.4.1`.' with '`juniper-observability`, which 0.11.5 raises from `>=0.4.1` to `>=0.4.2`.'",
                "fix": "text_fixes.json entries 4 and 5.",
            },
            {
                "id": "F7",
                "severity": "MINOR",
                "where": "COPY/CHANGELOG.md (the entry, lines 5-6 of it), DELIVERABLES/pr_body.txt:10, COPY/util/release_train/propose.py:38-39, :838-839 and :1993, COPY/docs/REFERENCE.md:4091",
                "claim": "Only once #2558 has merged, and true as written: 'every cut from 0.11.0 to 0.11.4 rewrote whichever of them moved with a one-off script' (and '...0_11_0_cut_cochanges.py and its four successors') is then one cut behind. The 0.11.5 cut did the same, with util/ad-hoc/2026-11-13_juniper_ml_0_11_5_cut_cochanges.py.",
                "evidence": "#2558's file list (gh): util/ad-hoc/2026-11-13_juniper_ml_0_11_5_cut_cochanges.py +448; its docstring: 'The juniper-ml 0.11.5 cut's co-changes: REFERENCE.md's Version cell and compatibility sentence, and the CHANGELOG repairs.'",
                "fix": "Optional. text_fixes.json entry 6 for the PR body. I do not recommend touching the four main-bound files for it: each sentence stays true, and an edit to a carrier file means a new manifest and a new run of every check that cites these bytes.",
            },
        ],
        "real_proposal_2558": {
            "the_pull_request": "juniper-ml#2558 'release: juniper-ml v0.11.5 (proposal)', read with gh: OPEN, not a draft, base main, branch release/juniper-ml-v0.11.5, created 2026-11-13T02:32:19Z, head d4dcefbc90288cc09b3cb3d0b74911c54ff168d0, mergeStateStatus BLOCKED, no auto-merge. Two commits directly on f9582a74: 8764f5cf 'chore(release): juniper-ml v0.11.5 -- version bump + CHANGELOG move' (generated) and d4dcefbc 'docs(release): the 0.11.5 cut's co-changes -- REFERENCE.md and the CHANGELOG section the Release renders' (by hand). Seven files: AGENTS.md +1-1, CHANGELOG.md +70-66, README.md +1-1, docs/REFERENCE.md +2-2, pyproject.toml +1-1, and two new util/ad-hoc scripts.",
            "tree_used": f"{AFTER_2558}: a detached worktree at d4dcefbc, which is main after the pull request, tree for tree. main has since gained #2559 (one test file that neither touches).",
            "1_the_landing_there": {
                "changelog": "INSIDE '## [0.11.5] - 2026-11-13' -> '### Fixed', at CHANGELOG.md:285, fourth of thirteen entries; 0 conflicts. #2558 leaves '## [Unreleased]' (:8) empty, with no ### heading, directly above '## [0.11.5] - 2026-11-13' (:10). By the coordinator's rule this is a BLOCKER (finding F1).",
                "helper": "exit 1 with --dry-run (nothing written) AND exit 1 without it, after writing all 22 files. It cannot exit 0 on that main.",
                "reference": "main's stamp is still 0.6.69 (#2558 does not move it): the landing takes 0.6.70, header == footer, the history row at :9427 directly after the 0.6.69 row, no version twice. Its two entry lines and the row are the carrier's; #2558's lines :108 and :184 are untouched.",
                "reverted": "nothing: no line that 8764f5cf or d4dcefbc added to CHANGELOG.md or docs/REFERENCE.md is removed by the landing (landing-check-after-2558/landing_check.json).",
                "repaired_in_my_worktree": "util/ad-hoc/2026-11-12_flood4r2_val_ml-propose-r3b_changelog_after_cut.py: the entry at CHANGELOG.md:12 under '## [Unreleased]' -> '### Fixed'; the file is main's plus that block (+49/-0), sha256 790b2f18c77b78aef86d27586bfdb8da576ebe762cceadd38d4170d5122afc55; docs/REFERENCE.md 17d92d8ae808...; my landing check exits 0 (landing-check-after-2558-fixed/). The helper's own output is kept as land-after-2558/CHANGELOG.md.as-the-helper-wrote-it.",
            },
            "2_the_propose_suite_there": "188 OK on Python 3.12.11 and 3.14.7 (suites/after2558-landed-py312, -py314); main's own tests/test_pyproject_extras.py 12 OK. The live-file control (F2) passes against the reworded paragraph. No test and no matcher of propose.py depends on a word #2558 changed: the sentence still opens '`juniper-ml` 0.11.5 declares the following pins.' and holds exactly one 'X.Y.Z sets them to `pin`, `pin` and `pin`' clause, on the same physical line (the cut script says it keeps both for #2507's tests).",
            "3_the_next_proposals_from_there": {
                "gate_file": "the tests carrier's round-2 file (sha256 1ee53200...), as in check C. On main + #2558 with no proposal: 20 OK, ReferenceCompatibilityMatrixTest 8 OK, so #2558's hand edits satisfy #2507's tests.",
                "unextended": "main's propose.py refuses any next proposal there: 'CHANGELOG move refused: [Unreleased] section has no content to move' (expected; nothing is unreleased).",
                "patch_0_11_6": "with the carrier landed (its entry under [Unreleased]): edits pyproject.toml, CHANGELOG.md, README.md, docs/REFERENCE.md, AGENTS.md, one edit per path. REFERENCE: the Version cell `0.11.5` -> `0.11.6` (width kept) and two tokens of the paragraph, 0.11.5 -> 0.11.6 in the sentence and in the clause; the 0.11.x row is current and untouched. After it: the gate file 20 OK, the class 8 OK, the propose suite 188 OK.",
                "minor_0_12_0": "the Version cell, the same two tokens (-> 0.12.0), and one new row '| 0.12.x     | >=0.17.1 ... | >=0.4.2 |' directly below the 0.11.x row, which is untouched. After it: 20 OK, 8 OK, 188 OK.",
                "review_line_on_the_sentence": "It does not quote or name #2558's sentence 'The `0.11.x` row is 0.11.5's: its floors are 0.11.2's, except `juniper-observability`, which 0.11.5 raises from `>=0.4.1` to `>=0.4.2`.' After the 0.11.6 proposal that sentence stands unchanged under '`juniper-ml` 0.11.6 declares the following pins'. The REVIEW line says, verbatim: 'docs/REFERENCE.md \"Ecosystem Compatibility\" prose (REVIEW by hand in this PR): the train renders the release, the pins and the current series' row, and never the paragraph's history (which release raised which floor, and \"The `0.N.x` row is X's\"); the [recurrence] clause now names 0.11.6, so words after its pins that say what a release changed (': it raises ...') now describe 0.11.6: reword them, or move them into the history -- util/ad-hoc/2026-11-06_juniper_ml_0_11_4_cut_cochanges.py is the 0.11.4 cut's wording.' On the minor it adds the previous-series note ('restore the pins that series' last release published'). Its example ': it raises ...' no longer matches main's words after #2558 ('..., as 0.11.4 did: 0.11.4 raised ...'): the carrier's open question on quoting the row sentence is unchanged by this.",
                "evidence": "sim-after-2558/summary.json and landed--patch.proposal.json, landed--minor.proposal.json, main--patch.proposal.json",
            },
            "4_hand_edits_against_the_tool": {
                "same_lines": "yes. #2558's generated commit changes NO line of docs/REFERENCE.md; its hand commit changes exactly :108 and :184, the two lines the extended propose.py changes for 0.11.5 from f9582a74.",
                "version_cell": "identical, byte for byte: '| **Version**            | `0.11.5`     |'.",
                "matrix": "neither touches a row (the 0.11.x row was already current).",
                "paragraph": "NOT the same text. Both rename the release twice (the sentence and the clause). #2558 also rewords five runs of words by hand, which the tool never writes: \"0.11.4's, and\" -> \"0.11.5's:\"; \"the `juniper-observability` cell: it holds `main`'s floor, `>=0.4.2` (unreleased; first in juniper-ml 0.11.5), where the published 0.11.4 declares `>=0.4.1`.\" -> \"`juniper-observability`, which 0.11.5 raises from `>=0.4.1` to `>=0.4.2`.\"; \"`>=0.7.1,<0.8.0`; `main`\" -> \"`>=0.7.1,<0.8.0`, and 0.11.5\"; \"`>=0.7.2,<0.8.0` (unreleased; first in juniper-ml 0.11.5).\" -> \"`>=0.7.2,<0.8.0`.\"; \"above): it raises\" -> \"above), as 0.11.4 did: 0.11.4 raised\".",
                "what_it_says": "The tool would have produced the two changed lines, the cell exactly and the paragraph with its two renames, and that proposal passes #2507's tests (check C). It would not have produced this proposal: four of the five rewordings are the words the floor raise wrote, which the REVIEW line does not name, and the fifth is the words after the clause's pins, which it does name. The tool's paragraph would have read '0.11.5 declares' above '(unreleased; first in juniper-ml 0.11.5)' until a reviewer acted on the REVIEW line.",
                "other_files": "pyproject.toml, AGENTS.md, README.md and CHANGELOG.md written by main's propose.py in my sandbox are byte-identical to #2558's generated commit 8764f5cf (the extended script uses the same code for them); #2558's head then changes CHANGELOG.md by hand in 10 blocks.",
                "evidence": "compare_2558.json",
            },
            "at_the_freeze_if_2558_has_merged": after_cut,
            "texts_2558_makes_stale": {
                "says_0_11_5_is_released": "no text of the carrier does. '0.11.5' occurs in pr_body.txt only (lines 26 and 47): inside the quote of main's then-current words ('unreleased; first in juniper-ml 0.11.5'), as 'the 0.11.5 proposal', and in the table row 'patch, 0.11.4 -> 0.11.5'. commit_body.txt, the CHANGELOG entry and the lines the carrier adds to docs/REFERENCE.md, the runbook, propose.py and its tests do not contain it. 'the next release' occurs nowhere.",
                "stale": "pr_body.txt:26 (finding F6; text fixes 4 and 5), and, once it has merged and only as 'one cut behind', the 'from 0.11.0 to 0.11.4' sentences (finding F7).",
                "not_stale": "the table's 'patch, 0.11.4 -> 0.11.5' and 'minor, 0.11.4 -> 0.12.0' rows are records of runs on the mains they name; 'the 0.11.4 cut left \"0.11.4 sets them to ...: it raises ...\"' (pr_body.txt:23, the CHANGELOG entry) is history that the v0.11.4 tag still shows.",
            },
            "order_matters": "see finding F2: landed BEFORE #2558 merges, the entry is carried under [0.11.5] by #2558's own merge (merge-tree bf884f94, no conflict).",
        },
        "if_main_moves_again_before_the_freeze": [
            f"ALWAYS: a fresh detached worktree of the new origin/main, then {LAND} --dest <it> --landing-date <UTC date> --out <dir> --dry-run. Exit 0 and no PROBLEM line, or stop. If the mover touched none of the carrier's five modified paths, the assembled CHANGELOG.md and REFERENCE.md keep sha256 c45e9bc2... and d290cd6c... (so for #2559).",
            "juniper-ml#2558 (the 0.11.5 proposal): finding F1 and real_proposal_2558.at_the_freeze_if_2558_has_merged.",
            "A mover that bumps docs/REFERENCE.md's stamp: the helper takes the next number by itself; use <out>/texts/pr_body.txt for the Stamps line and check 'no version twice' with my landing check.",
            "A mover that changes pyproject.toml, tests/test_pyproject_extras.py or one of REFERENCE's four sites: the propose suite (its live-file control reads them) and the simulator.",
            "A mover that changes util/release_train/propose.py or tests/test_release_train_propose.py: the helper switches from copy to three-way for them; then the suite, both mutant runs and the screens again.",
            "juniper-ml#2548 (OPEN, auto-merge armed, head 5099d14c of 02:16:52Z): its diff is now 11 NEW files only (3 tests, 6 under util/ad-hoc, 2 under util/systemd). Its head commit bf53a1d6 says 'step aside for the 0.11.5 cut (shared files back to main's copy)': it no longer changes ci.yml, AGENTS.md, CHANGELOG.md or docs/REFERENCE.md. If it regains them: the first three items.",
            "A landing after 2026-11-14T00:00Z: --landing-date 2026-11-14 (the helper prints a NOTE when the date is not today's UTC date).",
            "The order: the texts say this change lands before the tests carrier, in one sitting. Today #2507 is an open draft and the tests carrier is not merged and has no number.",
        ],
        "observations": [
            "tests/test_duplicati_scheduled_backup.py was run ZERO times in this session (the coordinator's rule of 02:51Z): it is not among my 79 suites. The two suites of my run that name notify-send (tests/test_juniper_backup_tier2_lane.py, _tier3_lane.py) stub it, by their own docstrings. DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent/no-session-bus is now in the child environment of my three test-running helpers.",
            "The landing helper's last line tells the truth even when it exits 1 ('written into <dest>' / 'NOTHING WRITTEN' / 'DRY RUN, nothing written'): read it, not the exit status alone.",
            "docs/REFERENCE.md's own stamp is not gated by any test (no suite but the propose suite's fixtures mentions its Version History): a generated proposal that now edits the file moves no document stamp. Not a defect of this carrier; step 5b-ii already edited the file without one.",
            "The carrier's CHANGELOG entry and commit body say what a later change will do ('the tests land after it, in the flood-4 round-2 tests carrier'). It is the order the final check asked the texts to state, and it holds only if the tests carrier lands the same day.",
        ],
        "validator_artifacts": {
            "isolation_worktree_and_mutation_twin": f"{TWIN} (branch worktree-agent-a61564fc0ee03e2a2 at f9582a74 + the landed carrier, uncommitted; every mutant ran here; tmp/k2/ holds the sources of my helpers)",
            "git_worktrees_created_under_Juniper_worktrees": [
                f"{LANDED} (the landing: f9582a74 + the 22 files, uncommitted, never mutated)",
                f"{AFTER_2558} (check F: #2558's head + the 22 files, CHANGELOG.md repaired by my helper)",
                f"{WORKTREES}/juniper-ml--val--flood4r2-ml-propose-r3b-aftercut--20261112-2042--20db12ec (clean, at my probe commit of a SIMULATED 0.11.5 cut)",
                f"{WORKTREES}/juniper-ml--val--flood4r2-ml-propose-r3b-cleanmain--20261112-2051--f9582a74 (clean; created at f9582a74 for the two failing suites, then moved to ae801a70 for the dry run: its name says f9582a74, its HEAD is ae801a70)",
            ],
            "plain_directories_created_under_Juniper_worktrees": [
                f"{WORKTREES}/juniper-ml--val--flood4r2-ml-propose-r3b-sims--20261112-2031--f9582a74 (6 sandboxes of check C and mut-carrier59, the scratch tree of the carrier's mutation script)",
                f"{WORKTREES}/juniper-ml--val--flood4r2-ml-propose-r3b-sims-after2558--20261112-2050--d4dcefbc (6 sandboxes of check F)",
            ],
            "local_refs_created": ["refs/flood4r2v/pr/2548", "refs/flood4r2v/pr/2555", "refs/flood4r2v/pr/2558"],
            "dangling_objects": "probe commits 42e0476425a1 (main + carrier, sequence safety), 98a66143b982 (the same after #2558), 20db12ec (the simulated cut) and the merge-tree bf884f94: local, unsigned, on no branch, never pushed",
            "helpers": f"{HELPERS}/2026-11-12_flood4r2_val_ml-propose-r3b_{{landing_check,show,run_suites,mutants,simulate,make_freeze,reader_suites,claims,cut_probe,changelog_after_cut,compare_2558,write_results}}.py (mine), and ..._verify_carrier.py (the dead session-6 agent's, read in full and run unchanged)",
            "left_alone": "the dead agent's scratch (ml-propose-r3b-quick-s6/) and its worktree at 26ea0ecb; the carrier; the tests carrier's tree; every primary checkout",
            "note": "Nothing was pushed, no pull request was touched, no signed commit was made, nothing was written under the system temp directory, TMPDIR was not changed, no process other than my own was stopped, and I left no pyproject.toml under any juniper-ml tmp/ (my scratch, my twin's tmp/ and my worktrees hold none). At most 4 workers of mine ran at once (3 suite workers + the 59-mutant run).",
            "environment": "Every unittest run and every pre-commit run had the six Sentry DSN variables set to the empty string. The processes that run no test and import no Juniper service inherited the session's environment unchanged: the landing helper, my plumbing helpers, the static screens, the two sequence-safety console scripts, and the simulator's build child (it imports util/release_train's detect and propose only). The simulator now passes the empty variables to that child as well; that edit and the no-session-bus variable were made after the runs and change no result.",
            "not_mine_seen_under_the_primary_tmp": "tmp/tmpw216lw5r/pyproject.toml in juniper-ml's primary checkout (a [project] fixture named 'synthetic-repo', created 2026-11-13T02:39:25Z): tests/test_env_drift_check.py writes it, and that suite is not among the 79 I ran, so it is another session's. Created in the same half second: tmp/rekey-real-jv6z5znd and tmp/rekey-gate-3qmi8e6m, which tests/test_backup_rekey_real_path.py makes; my run of that suite and another session's ran at that moment (mine exited 0 after 313.9 s), and I cannot tell whose they are. I removed none of the three. tests/test_release_train_registry.py walks tmp/; it passed in my run (27 tests, 2 skipped).",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--status", required=True, choices=("in-progress", "final"))
    args = parser.parse_args()
    problems = check_text_fixes()
    (SCRATCH / "text_fixes.json").write_text(json.dumps(TEXT_FIXES, indent=1) + "\n", encoding="utf-8")
    (SCRATCH / "findings.json").write_text(json.dumps(findings(args.status), indent=1) + "\n", encoding="utf-8")
    for line in problems:
        print("PROBLEM", line)
    print(f"findings.json ({args.status}) and text_fixes.json ({len(TEXT_FIXES)} entries) written to {SCRATCH}; text-fix problems: {len(problems)}")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
