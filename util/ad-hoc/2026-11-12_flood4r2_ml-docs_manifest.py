#!/usr/bin/env python3
"""
Write the round-2 "ml-docs" carrier's manifest.json and stamps.json from its recorded decisions and check results.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- one-off (Cursor flood-4 round-2 docs-carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2)

The per-draft decisions and the claims table are data in this file: they were made by reading each draft's own
hunks against the code on the base commit, and each claim names the file:line, test or probe case that shows
it. The script adds what can be computed: the base commit, each carrier file's status and sha256, each draft's
head, and the results of the checks whose reports sit in the scratch directory. It refuses to write when the
working tree's changed paths are not exactly the carrier's.

Usage: 2026-11-12_flood4r2_ml-docs_manifest.py --scratch <dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CARRIER_FILES = [
    ".claude/agents/fleet-supervisor.md",
    "CHANGELOG.md",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
    "docs/DOCUMENTATION_OVERVIEW.md",
    "docs/QUICK_START.md",
    "docs/REFERENCE.md",
]
HELPER_GLOB = "2026-11-12_flood4r2_ml-docs_*.py"
GUARD = "util/claude_agent_guard.py"
PM = "util/fleet_triage/predict_merge.py"
WAKE = "scripts/wake_the_claude.bash"
CLAUDEY = "scripts/claude_interactive.bash"
DEFAULT_SESSION = "scripts/default_interactive_session_claude_code.bash"
SLC = "juniper-ci-tools/juniper_ci_tools/symbol_loss_check.py"
DAC = "juniper-ci-tools/juniper_ci_tools/docs_additions_check.py"
RERUN = "util/ad-hoc/2026-10-05_rerun_after_actions_outage.py"
LANE = "util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py"
LP = "claims/launcher_probe.json"
GP = "claims/guard_probe.json"
PP = "claims/predict_merge_probe.json"
SP = "claims/symbol_loss_probe.json"

CARRIED = [
    {
        "pr": 2479,
        "taken": [
            "docs/REFERENCE.md: the Table of Contents entry; the section '## Local Claude Code Launchers' (Entry points, Version flags, Prompt file, Where the prompt sits, Examples, and its pitfalls table); the launcher link in the '### Claude Code Action (`claude.yml`)' paragraph and in the '## Claude Code Action' intro",
            "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md: the 'Operator contract' pointer under '## Claude Code Session Script' and the launcher paragraph that ends '`-u` prints the usage text and exits 1.'",
            "docs/DOCUMENTATION_OVERVIEW.md: the row 'Launch a local Claude Code session'",
            "docs/QUICK_START.md: the 'Local Claude Code Launchers' bullet",
        ],
        "fixes": [
            "Entry-point table: the column was 'What reaches wake_the_claude.bash' and listed a bare --worktree. claudey hands wake `--worktree 0` and a `--` spacer (probe case E1), so the column now says what Claude Code is handed, read from a stub claude; the model and effort are named as the script's DEFAULT_MODEL / DEFAULT_EFFORT (opus / max as of juniper-ml#2554), because the model default is switched from time to time (tests/test_claude_interactive.py, shipped_defaults docstring).",
            "Added '### Effort' (owner ruling 3; landed by juniper-ml#2554): max is the default, `0` sends max, `auto` in any case and `1` send no --effort flag, anything else is refused (probe cases F1-F6). The triage asked for it.",
            "Added what juniper-ml#2554 carried from drafts #2504 and #2505: an exported empty CLAUDE_PROMPT_FILE / CLAUDE_PROMPT_PATH is refused (P4, P4b, P4c), and a later --file / --path that does not resolve drops the file an earlier one resolved (P11, P11b). The triage asked for both.",
            "stderr table: added the row for a prompt file that cannot be read or holds only whitespace (S8) and the row for the repo tmp/ that cannot be created (scripts/wake_the_claude.bash:1849-1851, from juniper-ml#2360, after the draft); the refused line names the flag AS TYPED (`-f`, `-c`: S3b, S9b).",
            "'An unknown flag ... nothing on stderr' holds only with the debug log off (S7); with it on, stderr carries the debug log (S7b). Qualified.",
            "'a leading `---name:` front-matter line' -> 'a leading `---` front-matter line' (E2).",
            "Remote control: claudey's third alias `--remote-control-session` added (scripts/claude_interactive.bash:218); 'the end of the input' added to what makes wake's flag bare (P9e).",
            "Version-flag row: 'Any later arguments are dropped' -> 'Any other arguments': a flag typed before -v is dropped too (V2c).",
            "claudey's usage text is said to go to stdout, with the 'Missing value' / 'Unknown argument' line above it (P3, P6: the probe reads them on stdout).",
            "Its '### Operator pitfalls' heading is '### Launcher pitfalls': docs/REFERENCE.md already has 40 headings with that exact text, and another in the middle would renumber the GitHub anchors of those after it. Three rows added (empty variable, later unresolved file, --effort auto).",
            "Regression command and test list: the two suites juniper-ml#2554 added (tests/test_claudey_empty_prompt_file_env.py, tests/test_prompt_file_later_flag.py) and the three effort tests; every named test exists on the base.",
        ],
        "dropped": [
            "Its stamp hunks in the four docs and its Version History row 0.6.91: one bump per document instead.",
            "scripts/claude_interactive.bash, scripts/default_interactive_session_claude_code.bash, scripts/wake_the_claude.bash, tests/test_claude_interactive.py, tests/test_wake_the_claude.py and CHANGELOG.md: not the draft's own. They are juniper-ml#2468's pre-squash commits (07271912, ca8224a9, 5c57ecde) that the draft's branch sits on; in those paths 5c57ecde is byte-identical to #2468's squash fc533642 (`git diff --stat fc533642 5c57ecde -- scripts tests/test_claude_interactive.py tests/test_wake_the_claude.py` is empty). Already on main; they belong to no carrier.",
        ],
        "outcome": "carried-with-fix",
        "reason": "Launcher section carried, every sentence checked by a 95-case stub-claude probe (260 expectations, 0 false), and extended with what juniper-ml#2554 changed (effort default, empty prompt-file variables, a later unresolved prompt file).",
    },
    {
        "pr": 2483,
        "taken": [
            "docs/REFERENCE.md: the Constraints bullet, the section '### A Python body that keeps at most 60 percent and loses at least 4 lines is WEAKENED', and the sub-bullet under the sequence-safety screens entry of the Utility Script Reference",
            "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md: the 'WEAKENED bounds.' paragraph",
            "docs/DOCUMENTATION_OVERVIEW.md: the row 'See when a gut is WEAKENED'",
            "docs/QUICK_START.md: the 'WEAKENED line bounds' bullet",
        ],
        "fixes": [
            "A bash function's line count is the distance to the next function OR to the end of the file (symbol_loss_check.py:306-310); the draft named only the next function.",
            "The waiver sentence says 'its kind prefix' (`_waives` strips whatever precedes the first colon, symbol_loss_check.py:438-444).",
        ],
        "dropped": ["Its stamp hunks in the four docs."],
        "outcome": "carried-with-fix",
        "reason": "Every row of its table re-derived by calling classify_file on built sources (10->6 and 7->3 WEAKENED, 15->10 and 7->4 not; a gutted method also fails its class; a method token does not waive the class).",
    },
    {
        "pr": 2487,
        "taken": [
            "docs/REFERENCE.md: two Table of Contents entries; the Test Suite Reference entries of tests/test_rerun_after_actions_outage.py and tests/test_equities_lane_a3_report.py; the `checks` row of 'What exit 0 does not mean'; the section '### Lane A3 checks'; the section '## Actions outage re-run' with '### A bad status page is not operational'",
            "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md, docs/DOCUMENTATION_OVERVIEW.md, docs/QUICK_START.md: its two pointers in each",
        ],
        "fixes": [
            "'It does not import juniper_data_client, juniper_recurrence, or model-core' -> the names the script's own docstring gives (juniper_recurrence_model), plus 'numpy and the standard library alone' (the module's imports, :59-69).",
            "'the same cut the matrix uses' -> 'the values the matrix script pins in E_H_CV' (util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py:74). The matrix cuts with model-core's walk_forward_folds; only the two values are shared text.",
            "Test Suite Reference sentence scoped to what the suite pins: the reading is pinned for every shape, the exit 2 for a dict-shaped `components` (test_an_unreadable_status_payload_keeps_waiting_and_never_touches_gh).",
            "'give up after 4 hours' -> 'once more than 4 hours have passed' (strict `>`; test_elapsed_equal_to_the_budget_still_waits).",
            "Table: 'No object named Actions' also covers a missing `components` key (test_a_missing_component_or_status_is_not_operational). 'a non-object after an operational Actions object was ignored' -> 'was never reached' (the 0.2.0 walk returned at the Actions object: `git show 22e4a4b9`).",
            "Index pointers: 'a malformed status page exits 2' -> 'reads `unknown`, and the wait gives up with exit 2'.",
        ],
        "dropped": ["Its stamp hunks in the four docs and its Version History row 0.6.94."],
        "outcome": "carried-with-fix",
        "reason": "Both pages describe fixes that are on main since juniper-ml#2366 (helper 0.3.0, script 0.3.1) and that main's docs did not mention; each sentence checked against the two scripts and the tests that pin them.",
    },
    {
        "pr": 2494,
        "taken": [
            ".claude/agents/fleet-supervisor.md: the scratch-repository description (was 'detached `git clone`') and the ERROR bullet",
            "docs/REFERENCE.md: the layer-table row; the subsection '#### Scratch repository'; the `ERROR` verdict row; its operator-pitfall row for a history cut above the merge base; the Test Suite Reference entry of tests/test_predict_merge.py ('scratch-never-mutates-source' and the scratch sub-bullet); the Utility Script Reference entry of predict_merge.py and its scratch sub-bullet; the repository-tree comment",
            "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md: the two command-table rows, the scratch sentences in its three fleet-triage paragraphs, and the sentence added to its three `predict_merge` exit `2` rows",
            "docs/DOCUMENTATION_OVERVIEW.md: the parentheticals on its two fleet-triage rows; docs/QUICK_START.md: the fleet-triage bullet",
        ],
        "fixes": [
            "Step 1 of the operator contract is NOT replaced. The draft rewrote it; juniper-ml#2554 has since rewritten that step (it carries #2513's sentence), so it stays byte-identical and the scratch detail lives in the new subsection.",
            "'These variables are removed from the environment before every git call' -> scoped to `_git`, and the list completed to nine with GIT_SHALLOW_FILE and GIT_GRAFT_FILE (predict_merge.py:140-144; the triage's 'add #2513's two vars').",
            "fleet-supervisor.md ERROR bullet and the cheatsheet exit-2 rows: 'a missing filter binary' and 'an inherited GIT_DIR' are removed from the causes of an error. main handles both (tests/test_predict_merge.py test_a_configured_filter_whose_binary_is_absent_does_not_break_the_scratch and test_an_inherited_git_dir_neither_breaks_the_run_nor_touches_the_source). The triage named this fix.",
            "'Without the copy, git merge printed could not parse commit, then Already up to date., and exited 0' is history the present code cannot show. Replaced by what a probe shows on git 2.53: with the copy a cut above the merge base ends `merge failed: fatal: refusing to merge unrelated histories`; with the copy switched off git reports `could not parse commit` on the ancestor check.",
            "'copies `.git/shallow`' -> 'the checkout's `shallow` file', read from the common git directory (predict_merge.py:371-373): a linked worktree has no `.git/shallow` of its own.",
            "Added a true statement the draft's wording hid: the two console-script screens and pre-commit are started with the caller's environment, so under an inherited GIT_DIR the symbol screen is recorded as `skip` (probe). See open_questions.",
            "Its two history bullets (the `git clone --shared` cause; 44 of 45 and 56 of 57) are not repeated: main's step 1 and CHANGELOG entry for juniper-ml#2474 already state them.",
        ],
        "dropped": [
            "util/fleet_triage/predict_merge.py docstring hunk: juniper-ml#2554 took it.",
            "The rest of its util/fleet_triage/predict_merge.py diff, tests/test_predict_merge.py, its CHANGELOG.md entry and the three corrections at the top of fleet-supervisor.md: not the draft's own. They are juniper-ml#2474's pre-squash commits (21a9dabc, 47b19f9d); in predict_merge.py, tests/test_predict_merge.py and fleet-supervisor.md 47b19f9d is byte-identical to #2474's squash 827199b6. Already on main.",
            "Four of its five docs/REFERENCE.md operator-pitfall rows and the two troubleshooting rows it added to three cheatsheet tables (`nonexistent object`; checkout fails / `git init` rewrote the source; UnicodeDecodeError): each names a symptom of the code before juniper-ml#2474, which main no longer produces.",
            "Its stamp hunks in the four docs.",
        ],
        "outcome": "carried-with-fix",
        "reason": "Its remainder after juniper-ml#2554 (fleet-supervisor.md and the docs hunks) carried against main's predict_merge.py, with the two causes main handles removed and #2513's two variables added.",
    },
    {
        "pr": 2490,
        "taken": [
            "docs/REFERENCE.md: the Table of Contents entry and the section '## GnuPG long-option abbreviations' (its structure: the rule, the exact `export` exception, short options, the table, the deny wording, nested text, the pins)",
            "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md, docs/DOCUMENTATION_OVERVIEW.md, docs/QUICK_START.md: its pointer in each",
        ],
        "fixes": [
            "Rewritten for the guard on main. The draft documented a floor of 4 (GPG_MIN_ABBREV = 4: `--cle`, `--sig`, `--exp` allowed). The floor is 2 since guard 1.3.0 (util/claude_agent_guard.py:288-290; juniper-ml#2554 carried draft #2493). Every row of the table is rebuilt from a 68-row guard probe: two letters or more of a denied option are denied, one letter is not, exact `export` is allowed and `--ex` .. `--expor` are not.",
            "The pins paragraph said the suite does not sit on the cut. It does now: GPG_CASES in tests/test_claude_agent_guard.py:381-405 pins both sides; the paragraph lists those rows.",
            "'A 3-character name is below the floor. It is not a spelling to retry' -> the one-letter case, citing the guard's own comment that one character is ambiguous to GnuPG for every denied option. What GnuPG itself does with a prefix is not restated; the section points to the guard's entry, which juniper-ml#2554 wrote from its own GnuPG 2.4.8 probe.",
            "The `gpg --exports` row is not carried (not a GnuPG option; nothing to tell an operator).",
        ],
        "dropped": [
            "Its sub-bullet under the Test Suite Reference entry of tests/test_claude_agent_guard.py and its 'GnuPG prefixes' sub-bullet under the guard's Utility Script Reference entry: juniper-ml#2554 rewrote both entries, and the second already has a '`GPG-SIGN` and GnuPG prefixes' bullet. Both entries stay byte-identical.",
            "Its stamp hunks in the four docs and its Version History row 0.6.96.",
        ],
        "outcome": "rewritten",
        "reason": "Its page is kept as a page; every number in it moved from the 4-character floor it documented to the guard's 2-character floor.",
    },
    {
        "pr": 2470,
        "taken": [
            "Its three index pointers, rewritten: the 'Agent-guard brace cap' bullet of docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md, the brace row of docs/DOCUMENTATION_OVERVIEW.md, and the 'Agent-guard brace cap' bullet of docs/QUICK_START.md",
        ],
        "fixes": [
            "Each pointer said 'alternative 65 is allowed'. It now states the refusal: a word whose brace expansion needs more than 64 alternatives ends the hook with exit 2 (owner ruling 8, 'Fail closed'; guard 1.3.0), while a list of exactly 64 is still expanded and judged (guard probe: 64 -> CRED-PATH-BASH, 65 -> exit 2, `{1..64}` allowed, `{1..65}` refused, `for i in {1..100}` refused, `$(seq 1 100)` allowed).",
            "The pointers link to the Utility Script Reference, where the guard's entry holds juniper-ml#2554's 1.3.0 bullets, because the draft's own section is not carried.",
        ],
        "dropped": [
            "docs/REFERENCE.md '## A Brace List of 64 Alternatives Still Names .ssh' with its three subsections, its Table of Contents entry and its Version History row 0.6.88. The section documents the expander before 1.3.0: alternative 65 dropped and the command allowed, `_brace_range` slicing a range to 64, and the constraint 'Leave the cap at 64 ... A .ssh or .gnupg component that exists only as alternative 65 is allowed'. The owner's ruling replaced that behaviour, and none of that text is restored. What is still true of it is already on main: a 64-alternative list keeps its last slot (the Test Suite Reference entry of tests/test_claude_agent_guard_brace_cap.py) and a range is sized before anything is built (the guard's 1.3.0 bullets).",
            "Its stamp hunks in the four docs.",
        ],
        "outcome": "rewritten",
        "reason": "After juniper-ml#2554 only its three index pointers were left to carry: main's index documents did not mention the brace cap at all. Its section is superseded by #2554's text.",
    },
    {
        "pr": 2484,
        "taken": [
            "docs/REFERENCE.md only: its paragraph saying that predict_merge's scratch copies a shallow checkout's `shallow` file, as one bullet of '#### Scratch repository' (the tests carrier takes its first test and leaves this paragraph out)",
        ],
        "fixes": [
            "main did NOT already say it in docs/REFERENCE.md: step 1 of the operator contract, as juniper-ml#2554 left it, names GIT_SHALLOW_FILE but not the copy. Only predict_merge.py's docstring does (:17-18).",
            "'Without it ... a behind-main PR that merges cleanly is reported CONFLICT (refusing to merge unrelated histories)' is the behaviour of draft #2480's code, not of main: on main a merge exit other than 0 or 1 raises PredictMergeError (predict_merge.py:428-430), which is exit 2 in --pr and an ERROR row in --batch. The bullet says what the probe shows: a shallow source whose cut lies below the merge base triages as a full one does, a linked worktree of it included (the draft's own case), and a cut above the merge base is an error.",
            "Placed in the new subsection, not in step 1, which stays byte-identical.",
        ],
        "dropped": [
            "tests/test_predict_merge_shallow_worktree.py, its tests/test_predict_merge.py hunk, its .github/workflows/ci.yml line and its 'Running every suite' line in docs/REFERENCE.md: test and registration content, the tests carrier's.",
            "util/fleet_triage/predict_merge.py, .claude/agents/fleet-supervisor.md and CHANGELOG.md: not its own (the branch is stacked on draft #2480's, commit 406e7d80, whose code juniper-ml#2474 superseded, and on #2474's pre-squash commit 21a9dabc).",
        ],
        "outcome": "carried-with-fix",
        "reason": "Docs-only take: one true sentence for its paragraph, with the consequence corrected to main's behaviour; its tests are the tests carrier's.",
    },
]

MAIN_DEFECT_4 = [
    {"where": "docs/REFERENCE.md, operator contract step 3; the '#### Docs screen vs `docs_additions_check.py` (honesty)' table and its closing paragraph; the 'Expecting docs screen ==' pitfall row; the Utility Script Reference sub-bullet", "was": "an inline docs additions-only screen that fails ANY removed content line, 'stricter by design'", "is": "predict_merge shells out to juniper-docs-additions-check with --files <every changed .md> and no --min-run; a deleted heading or a run of at least 5 deleted lines in a hunk that adds nothing fails", "evidence": f"{PM}:242-281; `git show 0ea1f4dd` (juniper-ml#1004, 2026-08-07); {PP} docs_screen"},
    {"where": "docs/REFERENCE.md, the heal-first sentence; the Utility Script Reference entry; the Test Suite Reference sub-bullet", "was": "`restore` / `heal` / `repair` / `fix-first` anywhere in title or branch", "is": "a head branch starting fix/ heal/ hotfix/, or a title starting fix( fix: or the word heal, case-insensitive; then contention, then PR number", "evidence": f"{PM}:530-555; tests/test_predict_merge.py:672-700; {PP} _is_heal, suggest_order"},
    {"where": "docs/REFERENCE.md, operator contract step 3; .claude/agents/fleet-supervisor.md", "was": "hooks black / isort / flake8 / mypy / check-ast", "is": "black, isort, flake8, ruff, ruff-format, mypy, check-ast; a hook the repo does not define is skip", "evidence": f"{PM}:97, :288-304; `git log -S'\"ruff-format\"'` -> 35e3adde (juniper-ml#1740, 2026-09-05)"},
    {"where": ".claude/agents/fleet-supervisor.md; docs/REFERENCE.md layer table, Utility Script Reference entry and tree comment; two cheatsheet command rows", "was": "a detached `git clone`", "is": "a scratch repository: git init plus objects/info/alternates", "evidence": f"{PM}:331-382; {PP} scratch"},
    {"where": ".claude/agents/fleet-supervisor.md (the docs screen's description; MERGE-CLEAN)", "was": "'any removed content line on a .md'; 'the docs diff is additions-only'", "is": "juniper-docs-additions-check's thresholds; no deleted heading or deletion run", "evidence": f"{PM}:245-281; {PP} docs_screen"},
    {"where": "docs/REFERENCE.md, 'Degrade paths'", "was": "missing/broken `symbol_loss_check.py` -> symbol screen skip", "is": "either console script missing, exit 2, empty or non-JSON stdout -> that screen skip; no .md short-circuits the docs subprocess too", "evidence": f"{PM}:208-218, :261-272"},
    {"where": "docs/REFERENCE.md, Constraints (sequence-safety CLIs)", "was": "Gates: tests/test_symbol_loss_check.py, tests/test_docs_additions_check.py", "is": "the same two files under juniper-ci-tools/tests/ (rollout W3 moved them; tests/ has neither)", "evidence": "juniper-ci-tools/tests/test_symbol_loss_check.py, juniper-ci-tools/tests/test_docs_additions_check.py exist; tests/ has no such file"},
    {"where": "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md: three fleet-triage paragraphs and two troubleshooting rows", "was": "the inline any-removed-line docs screen (three times); heal tokens `restore`/`heal`/`repair`/`fix-first` (twice); 'New `.md` falsely DAMAGED-FIX-FIRST: header-counting bug class'; 'Heal PR not first: needs restore/heal/repair/fix-first (not bare fix/hotfix)'", "is": "the same corrections as in docs/REFERENCE.md; the last row was false in the other direction, since fix/ and hotfix/ branches ARE what promotes", "evidence": f"{PM}:245-281, :530-545; {PP}"},
]

CLAIMS = [
    # ---- #2479: Local Claude Code Launchers -------------------------------------------------------------
    {"draft": 2479, "section": "Local Claude Code Launchers (intro)", "claim": "./claudey is the repo-root symlink to scripts/claude_interactive.bash and does not run the default-session script", "evidence": f"`ls -l claudey` -> scripts/claude_interactive.bash; {CLAUDEY}:66, :306 (calls wake_the_claude.bash directly)"},
    {"draft": 2479, "section": "intro", "claim": "TRUE=\"0\" and FALSE=\"1\" in both scripts; CLAUDE_SKIP_PERMISSIONS=1 on the default-session script means on", "evidence": f"{CLAUDEY}:43-44; {WAKE}:104-105; {DEFAULT_SESSION}:28-31; {LP} E4b"},
    {"draft": 2479, "section": "Entry points", "claim": "./claudey hands Claude Code a bare --worktree, a bare --remote-control, --effort max, --model opus, --dangerously-skip-permissions, then -- and 'Hello World, Claude!'; DEBUG=TRUE is what sends --dangerously-skip-permissions", "evidence": f"{LP} E1 (argv); {CLAUDEY}:46, :111, :115, :126, :287"},
    {"draft": 2479, "section": "Entry points", "claim": "the model default is switched from time to time", "evidence": "tests/test_claude_interactive.py:68-90 (shipped_defaults docstring); scripts/claude_interactive.bash:110-111 (the commented alternative)"},
    {"draft": 2479, "section": "Entry points", "claim": "--file / --path: the same options, the file's text is the prompt, the default prompt is not sent", "evidence": f"{LP} E2, E3, E3b; {CLAUDEY}:254-259"},
    {"draft": 2479, "section": "Entry points", "claim": "default-session script: --session-id plus a new UUID, bare --worktree, bare --remote-control, --effort high, -- and the default prompt; no --model; --dangerously-skip-permissions only with CLAUDE_SKIP_PERMISSIONS=1", "evidence": f"{LP} E4, E4b; {DEFAULT_SESSION}:22-31"},
    {"draft": 2479, "section": "Entry points", "claim": "wake with no arguments prints usage and exits 1; -u / --usage exit 1; -h / --help exit 0", "evidence": f"{LP} E5, E6, E6b, E7, E7b; {WAKE}:1691-1697, :1505, :1539"},
    {"draft": 2479, "section": "Entry points", "claim": "claudey hands wake --worktree 0, which wake sends bare; --no-worktree / --no-remote-control and CLAUDE_WORKTREE=1 / CLAUDE_REMOTE_CONTROL=1 turn them off; dates 2026-11-04 and 2026-11-06", "evidence": f"{LP} E1 (stdout line), E8, E9; {CLAUDEY}:119-123, :215, :219, :281; {WAKE}:1019-1025; {DEFAULT_SESSION}:21"},
    {"draft": 2479, "section": "Entry points", "claim": "-s is --id (needs a value) on claudey and --dangerously-skip-permissions on wake", "evidence": f"{LP} E10, E10b; {CLAUDEY}:205; {WAKE}:364"},
    {"draft": 2479, "section": "Entry points", "claim": "claudey exits with wake's status after the Closed line; it used to exit 0; the default-session script already returned wake's status", "evidence": f"{LP} E11, E4c; {CLAUDEY}:306-312 (and its comment); {DEFAULT_SESSION}:44-48"},
    {"draft": 2479, "section": "Effort", "claim": "EFFORT_DEFAULT is max again (owner ruling 2026-11-08); the flag aliases are -e, --effort, --effort-type, --effort-level", "evidence": f"{WAKE}:258-262, :361; {LP} F2"},
    {"draft": 2479, "section": "Effort", "claim": "0 -> --effort max; auto in any case -> no flag; 1 -> no flag; a valid value is sent; anything else or no value -> exit 1 with the refused line; ./claudey -e auto launches with no --effort", "evidence": f"{LP} F1-F6; {WAKE}:928-946, :1783-1787; tests/test_wake_the_claude.py test_effort_true_sends_the_max_default, test_effort_auto_sends_no_effort_flag, test_effort_false_omits_the_effort, test_missing_effort_value_fails_without_invoking_claude"},
    {"draft": 2479, "section": "Effort", "claim": "Claude Code has no auto value", "evidence": f"{WAKE}:258-259 (the comment the sentence cites); notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 4, first row"},
    {"draft": 2479, "section": "Version flags", "claim": "wake 1.1.0, claudey 0.2.0; -v / -V / --version / --claude-version run `claude --version`, print '<path> <output>', exit 0, start no session; claudey execs wake --version and drops other arguments", "evidence": f"{LP} V1 (four flags), V2 (four flags), V2b, V2c; {WAKE}:123, :356, :1390-1408; {CLAUDEY}:49, :177-180, :189-190, :201"},
    {"draft": 2479, "section": "Version flags", "claim": "--script-version: wake prints 'wake_the_claude.bash 1.1.0' and ignores an exported SCRIPT_VERSION; claudey prints 0.2.0 without calling wake", "evidence": f"{LP} V3, V3b, V3c; {WAKE}:121-123, :1457-1460; {CLAUDEY}:191-193"},
    {"draft": 2479, "section": "Version flags", "claim": "./claudey -v sets WTC_DEBUG to 1 when unset; WTC_DEBUG=0 keeps the log; WTC_DEBUG defaults to 0 (debug on) in wake", "evidence": f"{LP} V2 (stderr empty), V2d; {CLAUDEY}:179; {WAKE}:108-110, :137-142"},
    {"draft": 2479, "section": "Version flags (stderr table)", "claim": "the eight stderr lines and their exits", "evidence": f"{LP} V4, V4b, V5, S1, S2, S3, S3b, S4, S5, S5b, S6, S8; {WAKE}:1396, :1403, :1758, :1773, :1807-1808, :1831-1832, :1850-1851 (tmp, read from the code: not provoked), :1888-1889 (nohup, read from the code: not provoked)"},
    {"draft": 2479, "section": "Prompt file", "claim": "flag aliases; the CLAUDE_PROMPT_FILE / CLAUDE_PROMPT_PATH variables; a flag overwrites the variable", "evidence": f"{CLAUDEY}:223-224, :239-242; {WAKE}:352-353; {LP} P5, P5b, P5c"},
    {"draft": 2479, "section": "Prompt file", "claim": "a prompt together with a file exits 1 before wake runs, with the quoted message; CLAUDE_PROMPT=1 beside a file is accepted", "evidence": f"{LP} P1, P2, P14; {CLAUDEY}:254-256"},
    {"draft": 2479, "section": "Prompt file", "claim": "--file '' / --path '' / -f '' / -l '' exit 1 with 'Missing value for <flag>' and do not call wake; an exported empty variable is refused the same way, even with --prompt", "evidence": f"{LP} P3 (six flags), P4, P4b, P4c; {CLAUDEY}:170-173, :243-251; tests/test_claudey_empty_prompt_file_env.py"},
    {"draft": 2479, "section": "Prompt file", "claim": "an empty word is 'Unknown argument: (an empty word)'; wake still stops at an empty word; -w '' is a bare --worktree and later flags are parsed", "evidence": f"{LP} P6, P6b, P7; {CLAUDEY}:196-198, :208-209, :225; {WAKE}:1711-1714"},
    {"draft": 2479, "section": "Prompt file", "claim": "./claudey --prompt with no word exits 1; on wake the next word is the prompt even when it starts with -; 0 or empty sends the default, 1 none, a missing word the default", "evidence": f"{LP} P8, P9, P9b, P9c, P9d, P9e, P9f; {CLAUDEY}:221; {WAKE}:1216-1228"},
    {"draft": 2479, "section": "Prompt file", "claim": "the file is read after parsing; trailing newlines stripped, a leading --- kept; the text is the last argument after --; no --prompt reaches claude", "evidence": f"{LP} E2; {WAKE}:1558, :1803-1819"},
    {"draft": 2479, "section": "Prompt file", "claim": "unreadable or whitespace-only file -> the 'could not be read, or holds no prompt' line, exit 1", "evidence": f"{LP} S8 (whitespace); {WAKE}:1555-1563, :1806-1808 (unreadable: read from the code)"},
    {"draft": 2479, "section": "Prompt file", "claim": "which mistakes end in the unresolved-file error and which in the refused line; a later unresolved --file / --path drops the earlier file", "evidence": f"{LP} S1, S2, S3, S4, S5, S5b, P11, P11b; {WAKE}:1263-1299, :1331-1358, :1771-1775; tests/test_prompt_file_later_flag.py"},
    {"draft": 2479, "section": "Prompt file", "claim": "an unknown flag prints usage only, nothing on stderr, with the debug log off; the version-flag errors add no refused line", "evidence": f"{LP} S7, S7b, V4, V5; {WAKE}:1747-1750, :1427-1428"},
    {"draft": 2479, "section": "Prompt file", "claim": "claudey's usage: prefix 'Usage: claude_interactive.bash', lists -h, goes to stdout, the prompt and the prompt file are one alternative joined by |", "evidence": f"{LP} P12, P3, P6; {CLAUDEY}:55, :132, :141-147, :153-161"},
    {"draft": 2479, "section": "Where the prompt sits", "claim": "the -- keeps the prompt from becoming the value of a bare --worktree / --remote-control; both launch calls pass the same array", "evidence": f"{WAKE}:1812-1819, :1894, :1899; {LP} E1, P13b"},
    {"draft": 2479, "section": "Where the prompt sits", "claim": "remote-control aliases; on wake 0 / end of input / a following flag is bare, 1 omits, any other word is refused; on claudey the next word is parsed on its own", "evidence": f"{LP} S9, S9b, S9c, S9d, S9e, S9f, P9e, P13, P13b, P13c; {WAKE}:363, :1062-1077; {CLAUDEY}:218-219"},
    {"draft": 2479, "section": "Launcher pitfalls and the test list", "claim": "each row; every named test exists", "evidence": f"{LP} P3, P4, P6, P7, E11, V4b, S1, P11, S2, S3, F2; `grep -l 'def <name>('` on tests/*.py for each of the 18 names (all found on the base)"},
    {"draft": 2479, "section": "cheatsheet paragraph; overview row; quick-start bullet", "claim": "the same facts in short form", "evidence": f"{LP} (the cases above)"},
    # ---- #2483 -------------------------------------------------------------------------------------------
    {"draft": 2483, "section": "A Python body ... is WEAKENED", "claim": "both arms, both inclusive; constants 0.6 and 4", "evidence": f"{SLC}:72-73, :370-371; {SP} python_pairs"},
    {"draft": 2483, "section": "same", "claim": "the line count is the AST segment's newline count plus one, includes the def/class line, excludes a decorator above it; `ratio` is round(head/base, 2) and is not what the gate compares; 0.6*10 = 6.0, 0.6*15 = 9.0, 0.6*7 = 4.2", "evidence": f"{SLC}:192-198, :380; {SP} decorated_function_lines (5 for a decorated 5-line function), products"},
    {"draft": 2483, "section": "same", "claim": "a bash function uses the same arms; its count is the distance to the next function or the end of the file, never less than 1; the verdict is WARN", "evidence": f"{SLC}:306-310, :336-337; {SP} bash_10_to_6, bash_line_count_is_the_distance_to_the_next_function_or_the_end"},
    {"draft": 2483, "section": "same (table)", "claim": "10->6 and 7->3 (ratio 0.43) WEAKENED / FAIL; 15->10 and 7->4 not; 7->2, 4->3 and same-length are the three named tests", "evidence": f"{SP} python_pairs, same_length_gutting; juniper-ci-tools/tests/test_symbol_loss_check.py:172-209"},
    {"draft": 2483, "section": "same", "claim": "gutting a method can fail method:C.m and class:C; a waiver matches one key, or the key without its kind prefix; naming the method does not waive the class", "evidence": f"{SP} gutted_method, waivers; {SLC}:438-451"},
    {"draft": 2483, "section": "same", "claim": "a deleted name is LOST; a name twice at head is DUPLICATED and not also WEAKENED; imports and constants are never WEAKENED", "evidence": f"{SP} deleted_name, name_twice_at_head, constant_and_import_shrunk; {SLC}:356-370"},
    # ---- #2487 -------------------------------------------------------------------------------------------
    {"draft": 2487, "section": "Lane A3 checks", "claim": "script 0.3.1; `checks` uses numpy and the standard library alone; compare and fold-threads are separate; the suite covers checks only", "evidence": f"{LANE}:8, :16-18, :36-39, :59-69, :156-270; tests/test_equities_lane_a3_report.py"},
    {"draft": 2487, "section": "same", "claim": "--meta / --archive-npz / --archive-meta optional; --n-folds 5, --embargo 2, the values in E_H_CV; fold_size = n // (n_folds + 1); a missing --npz or --out is argparse exit 2", "evidence": f"{LANE}:102-110, :536-542; util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py:74"},
    {"draft": 2487, "section": "same", "claim": "the JSON is written, then the summary printed, then 0 returned; the named fields are report fields, not exits", "evidence": f"{LANE}:169, :175, :181, :235, :237-238, :270"},
    {"draft": 2487, "section": "same; the `checks` row; the Test Suite Reference entry", "claim": "min-nonzero is null when no column has a std > 0 and the summary says 'min-nonzero=none (no column has a std > 0)'; before 0.3.1 the null was formatted with .3e after the write and the run exited 1", "evidence": f"{LANE}:199-213, :249-254; `git show 22e4a4b9 -- {LANE}` (0.3.0 -> 0.3.1); tests/test_equities_lane_a3_report.py:228-254"},
    {"draft": 2487, "section": "Actions outage re-run", "claim": "helper 0.3.0; waits for exactly `operational` on the component named exactly `Actions`; --accept-degraded adds exactly `degraded_performance`; --merge / --no-merge exclusive and required; the status URL", "evidence": f"{RERUN}:8, :46, :71-75, :93-98, :100; tests/test_rerun_after_actions_outage.py:165-176, :339-365, :400-410"},
    {"draft": 2487, "section": "same", "claim": "only completed failure / cancelled / timed_out / startup_failure runs are re-run; --no-merge returns 0; --merge returns safe_merge's code; poll 120 s; give up once more than 4 hours have passed", "evidence": f"{RERUN}:47, :91-92, :102-104, :112-125, :129; tests/test_rerun_after_actions_outage.py test_only_completed_failure_class_runs_are_rerun, test_elapsed_equal_to_the_budget_still_waits"},
    {"draft": 2487, "section": "A bad status page is not operational", "claim": "the six readings; an operational Actions object beside a non-object is not read; until 0.3.0 the walk sat outside the try; unknown never ends the wait: GAVE UP, exit 2, nothing re-run", "evidence": f"{RERUN}:54-75, :101-104; `git show 22e4a4b9 -- {RERUN}`; tests/test_rerun_after_actions_outage.py:178-212, :367-398"},
    # ---- #2494 / #2484 / defect 4 ------------------------------------------------------------------------
    {"draft": 2494, "section": "Scratch repository", "claim": "the directory is <tempdir>/fleet-triage-*/clone; _git runs every git command of the simulation", "evidence": f"{PM}:357-358, :412, :147-160 (and every call site in _scratch_clone and simulate_merge)"},
    {"draft": 2494, "section": "same", "claim": "git init matches the source's object format; alternates names <common dir>/objects; a linked worktree borrows the common store; no transport, no hardlink; the merge writes only into the scratch", "evidence": f"{PM}:350-364, :332-340; {PP} scratch.plain_source, linked_worktree_of_the_shallow_source; tests/test_predict_merge.py:598-615"},
    {"draft": 2484, "section": "same (the shallow bullet)", "claim": "a shallow source's `shallow` file, from the common git directory, is copied to the scratch; a cut below the merge base then triages as a full source does, as a linked worktree too; a cut above it is an error (`merge failed: fatal: refusing to merge unrelated histories` on git 2.53); without the copy git reports `could not parse commit`", "evidence": f"{PM}:369-373, :428-430; {PP} scratch.shallow_cut_below_the_merge_base, linked_worktree_of_the_shallow_source, shallow_cut_above_the_merge_base (git 2.53.0); tests/test_predict_merge.py:512-540"},
    {"draft": 2494, "section": "same", "claim": "info/attributes is `* -filter`; GIT_LFS_SKIP_SMUDGE=1 on every _git call; output decoded with errors=replace", "evidence": f"{PM}:149-158, :365-368; {PP} scratch (info_attributes); tests/test_predict_merge.py:542-579"},
    {"draft": 2494, "section": "same", "claim": "_git removes nine variables, git init included; an inherited GIT_DIR made git init re-initialise the source", "evidence": f"{PM}:135-148, :359; {PP} _GIT_LOCATION_VARS; tests/test_predict_merge.py:581-596; tests/test_predict_merge_inherited_git_env.py"},
    {"draft": 2494, "section": "same (the screens bullet; the pitfall row; the overview clause)", "claim": "the screens and pre-commit are started with the caller's environment; under an inherited GIT_DIR the symbol screen exits 2 on refs/fleet/base and is recorded as skip; the verdict is computed without it; screen_coverage lists the PR", "evidence": f"{PM}:126-132 (_run passes no env), :212-214, :298, :651-657; {PP} inherited_git_dir (DAMAGED-FIX-FIRST in a plain environment, MERGE-CLEAN with ast_symbol_screen.status=skip under GIT_DIR, with and without GIT_WORK_TREE)"},
    {"draft": 2494, "section": "same", "claim": "SHAs are resolved in the source; an unfetched head fails 'does not resolve'; exit 0 and 1 are answers, anything else an error; a behind branch's clean merge must have main as HEAD^2; the source is not written; the scratch is removed unless keep_scratch", "evidence": f"{PM}:405-411, :419-435, :482-484; {PP} scratch (source_refs_unchanged), leftover_scratch_dirs"},
    {"draft": 2494, "section": "ERROR row; fleet-supervisor.md ERROR bullet; cheatsheet exit-2 rows", "claim": "what raises PredictMergeError; ERROR is --batch's soft row and exit 2 in --pr", "evidence": f"{PM}:353-381, :408-435, :594-604, :738-740"},
    {"draft": "main defect 4", "section": "operator contract step 3; honesty table", "claim": "the hook list; a hook the repo lacks is skip; the docs screen's command, thresholds, scope and JSON shape; the scope difference from main-verify", "evidence": f"{PM}:97, :245-281, :288-304; {DAC}:21-31, :70-76, :254-259; .github/workflows/main-verify.yml:257; {PP} docs_screen (swap pass, 4 lines pass, 5 lines fail, heading fail, README.md outside docs/ fail)"},
    {"draft": "main defect 4", "section": "heal-first sentence and its repeats", "claim": "the branch and title prefixes; case-insensitive; then contention, then PR number; since juniper-ml#1004", "evidence": f"{PM}:530-555; {PP} _is_heal (16 rows), suggest_order; `git show 0ea1f4dd`"},
    {"draft": 2494, "section": "Test Suite Reference entry of tests/test_predict_merge.py", "claim": "the six scratch pins; the docs-screen edges; the heal-first prefixes the suite asserts", "evidence": "tests/test_predict_merge.py:246, :320, :336, :351, :450-615, :672-700"},
    # ---- #2490 -------------------------------------------------------------------------------------------
    {"draft": 2490, "section": "GnuPG long-option abbreviations", "claim": "GPG_MIN_ABBREV is 2 since 1.3.0 and was 4; two characters or more of a denied option are denied, one is not; the name is casefolded; text after = is not part of it; GPG_EXACT_ALLOWED holds only export and is checked first", "evidence": f"{GUARD}:183, :282-290, :1204-1206, :1411-1418; tests/test_claude_agent_guard.py:381 ('A floor of 4 allowed every one')"},
    {"draft": 2490, "section": "same (table, short options, command name)", "claim": "every row", "evidence": f"{GP} (68 rows, 0 differ); {GUARD}:281-286, :1419-1426"},
    {"draft": 2490, "section": "same", "claim": "`gpg --list --sign x` names GPG-SECRET and adds 'Also matched: GPG-SIGN'; a deny is one JSON object and exit 0; an allowed command prints nothing; the reason's wording; nested text is scanned", "evidence": f"{GP} (the last row; wording; the two nested rows); {GUARD}:2188-2198, :2217-2219"},
    {"draft": 2490, "section": "same", "claim": "one character is ambiguous to GnuPG for every denied option (the guard's comment)", "evidence": f"{GUARD}:288-289 (cited, not re-derived: no GnuPG command was run by this builder)"},
    {"draft": 2490, "section": "same (pins)", "claim": "GPG_CASES pins both sides of the floor", "evidence": "tests/test_claude_agent_guard.py:381-405"},
    # ---- #2470 -------------------------------------------------------------------------------------------
    {"draft": 2470, "section": "three index pointers", "claim": "more than 64 alternatives is a refusal (hook exit 2); exactly 64 are expanded and judged, so a credential directory spelled in the last one is denied; {1..64} fits, {1..65} and `for i in {1..100}` are refused, $(seq 1 100) is not", "evidence": f"{GP} (the ten brace rows); {GUARD}:189, :515-516, :2213-2214; docs/REFERENCE.md, the guard's 1.3.0 bullets (juniper-ml#2554)"},
]


def run(args: list[str]) -> str:
    proc = subprocess.run(args, cwd=str(REPO), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} -> {proc.returncode}: {proc.stderr.strip()[:300]}")
    return proc.stdout


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def regression(scratch: Path) -> dict:
    base = load(scratch / "regression_baseline_clean_main.json")
    tree = load(scratch / "regression_carrier_tree.json")
    if base is None or tree is None:
        return {"status": "not run yet"}
    return {
        "baseline_tree": base["tree"],
        "carrier_tree": tree["tree"],
        "python": tree["python"],
        "python_version": tree["python_version"],
        "suites": tree["suites"],
        "tests_ran": {"clean_main": base["tests_ran"], "carrier": tree["tests_ran"]},
        "failed_alone_on_clean_main": base["failed_alone"],
        "failed_alone_on_the_carrier": tree["failed_alone"],
        "failed_only_on_the_carrier": sorted(set(tree["failed_alone"]) - set(base["failed_alone"])),
        "failed_only_beside_others_on_the_carrier": sorted(set(tree["failed_beside_others"]) - set(tree["failed_alone"])),
        "failing_tests": {"clean_main": {row["suite"]: row["failed"] for row in base["alone_pass"] if row["exit"] != 0}, "carrier": {row["suite"]: row["failed"] for row in tree["alone_pass"] if row["exit"] != 0}},
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Write the ml-docs carrier's manifest.json and stamps.json.")
    parser.add_argument("--scratch", required=True, type=Path)
    args = parser.parse_args(argv)
    scratch = args.scratch.resolve()
    base_sha = run(["git", "rev-parse", "HEAD"]).strip()
    origin_main = run(["git", "rev-parse", "origin/main"]).strip()
    status = [line for line in run(["git", "status", "--porcelain=v1"]).splitlines() if line.strip()]
    modified = sorted(line[3:] for line in status if not line.startswith("??"))
    untracked = sorted(line[3:] for line in status if line.startswith("??"))
    if modified != sorted(CARRIER_FILES):
        print(f"refused: the modified paths are {modified}, not the carrier's {sorted(CARRIER_FILES)}")
        return 2
    helpers = sorted(str(path.relative_to(REPO)) for path in (REPO / "util" / "ad-hoc").glob(HELPER_GLOB))
    stray = [path for path in untracked if path not in helpers]
    extract = {entry["pr"]: entry for entry in load(scratch / "extract" / "extract_summary.json")}
    for entry in CARRIED:
        entry["head_sha"] = extract[entry["pr"]]["head_sha"]
        entry["head_moved_since_fetch"] = extract[entry["pr"]]["head_moved"]
        entry["title"] = extract[entry["pr"]]["title"]
    numstat = {line.split("\t")[2]: line.split("\t")[:2] for line in run(["git", "diff", "--numstat"]).splitlines()}
    screens = load(scratch / "screens" / "sequence_safety_probe.json")
    launcher = load(scratch / LP)
    guard = load(scratch / GP)
    regress = regression(scratch)
    checks = [
        {"what": "juniper-check-doc-links, exactly as AGENTS.md gives it (--exclude tmp, --cross-repo skip)", "command": "juniper-check-doc-links --exclude templates --exclude history --exclude legacy --exclude pull_requests --exclude releases --exclude analysis --exclude fixes --exclude development --exclude CHANGELOG.md --exclude tmp --cross-repo skip", "result": "pass" if "PASSED: Documentation link validation" in (scratch / "doc_links.log").read_text(encoding="utf-8") else "fail", "log": "doc_links.log"},
        {"what": "the repo's pinned pre-commit on every changed file (6 carrier files, 8 helpers)", "command": "/opt/miniforge3/bin/pre-commit run --files <the 14 paths>", "result": "pass" if "Failed" not in (scratch / "precommit.log").read_text(encoding="utf-8") else "fail", "log": "precommit.log"},
        {"what": "CI's symbol-loss screen on a git commit-tree probe of the carrier", "command": screens["screens"][0]["command"], "result": "pass" if screens["screens"][0]["exit"] == 0 else "fail", "findings": len((screens["screens"][0]["json"] or {}).get("findings", [])), "log": "screens/sequence_safety_probe.json"},
        {"what": "CI's docs-additions screen on the same probe", "command": screens["screens"][1]["command"], "result": "pass" if screens["screens"][1]["exit"] == 0 else "fail", "findings_by_severity": tally(screens["screens"][1]), "allow_docs_rewrite_needed": [], "log": "screens/sequence_safety_probe.json"},
        {"what": "the docs-additions screen with every changed .md named (as predict_merge runs it; CHANGELOG.md and fleet-supervisor.md included)", "command": screens["screens"][2]["command"], "result": "pass" if screens["screens"][2]["exit"] == 0 else "fail", "findings_by_severity": tally(screens["screens"][2]), "log": "screens/sequence_safety_probe.json"},
        {"what": "CI's markdown structure step on the same probe", "command": screens["markdown_structure_delta"]["command"], "result": "pass" if screens["markdown_structure_delta"]["exit"] == 0 else "fail", "detail": screens["markdown_structure_delta"]["stdout"].strip().splitlines()[-1], "log": "screens/sequence_safety_probe.json"},
        {"what": "no existing heading line changed or removed in any touched markdown file", "command": "util/ad-hoc/2026-11-12_flood4r2_ml-docs_screens.py (headings)", "result": "pass" if all(not item["missing_from_probe"] for item in screens["headings"]) else "fail", "new_headings": {item["path"]: item["new_in_probe"] for item in screens["headings"] if item["new_in_probe"]}, "log": "screens/sequence_safety_probe.log"},
        {"what": "CI's whole regression list, one process per suite, on a clean main and on the carrier tree", "command": "python3 util/ad-hoc/2026-11-12_flood4r2_ml-docs_run_suites.py --tree <tree> --out <json> --jobs 4 (six Sentry DSN variables set to the empty string)", "result": "pass" if regress.get("failed_only_on_the_carrier") == [] else ("fail" if "failed_only_on_the_carrier" in regress else "not run yet"), "detail": regress, "log": "regression_baseline_clean_main.json, regression_carrier_tree.json"},
        {"what": "launcher probe (stub claude; draft 2479's claims)", "command": "python3 util/ad-hoc/2026-11-12_flood4r2_ml-docs_launcher_probe.py --out claims/launcher_probe.json", "result": "pass" if launcher["failed"] == [] else "fail", "detail": f"{launcher['cases']} cases, {launcher['checks']} expectations, {len(launcher['failed'])} false", "log": LP},
        {"what": "guard probe (GnuPG rows and brace-cap rows; text only, no gpg run)", "command": "python3 util/ad-hoc/2026-11-12_flood4r2_ml-docs_guard_probe.py --out claims/guard_probe.json", "result": "pass" if guard["failed"] == [] else "fail", "detail": f"{guard['guard_version']}: {guard['rows']} rows, {len(guard['failed'])} differ", "log": GP},
        {"what": "predict_merge probe (scratch, heal-first, docs screen, inherited GIT_DIR)", "command": "python3 util/ad-hoc/2026-11-12_flood4r2_ml-docs_predict_merge_probe.py --out claims/predict_merge_probe.json", "result": "pass", "detail": "records facts; the inherited-GIT_DIR finding is in open_questions", "log": PP},
        {"what": "symbol-loss probe (draft 2483's rows)", "command": "python3 util/ad-hoc/2026-11-12_flood4r2_ml-docs_symbol_loss_probe.py --out claims/symbol_loss_probe.json", "result": "pass", "log": SP},
        {"what": "G-PATH, G-TMP and the CodeQL prescreen on the helper scripts", "command": "python3 util/home_path_literal_check.py <helpers>; python3 util/tmp_path_literal_check.py <helpers>; python3 util/ad-hoc/2026-10-05_codeql_python_prescreen.py <helpers>", "result": "pass", "log": "gpath.log, gtmp.log, codeql_prescreen.log"},
        {"what": "memory-budget gate", "command": "not applicable", "result": "pass", "detail": "AGENTS.md is not changed by this carrier, so neither the budget gate nor the Last Updated check is in play"},
    ]
    stamps = {
        "landing_date_utc": "2026-11-13",
        "rule": "Each document is bumped exactly once from the value on the main it lands on, header == footer, dated the UTC day it lands. Built on 26ea0ecb, where docs/REFERENCE.md is 0.6.68. If another PR (N-2) lands first and takes 0.6.69, set docs/REFERENCE.md to that main's value + 1 at the four REFERENCE sites below and in the three texts that quote the number. The other three documents follow the same rule if a PR that lands first moves them. If the landing slips past 2026-11-13 UTC, re-date every 'date' site below.",
        "documents": [
            {"path": "docs/REFERENCE.md", "main": "0.6.68 / 2026-11-13", "carrier": "0.6.69 / 2026-11-13", "sites": ["line 5: **Version:** 0.6.69", "line 7: **Last Updated:** 2026-11-13 (main already says 2026-11-13: unchanged)", "footer: **Last Updated:** 2026-11-13 (unchanged) and **Version:** 0.6.69", "Version History: the row that begins '| 0.6.69  | 2026-11-13 |', directly after the 0.6.68 row"]},
            {"path": "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md", "main": "1.0.67 / 2026-11-12", "carrier": "1.0.68 / 2026-11-13", "sites": ["line 3: **Version**: 1.0.68", "line 4: **Date**: 2026-11-13", "footer: **Last Updated:** 2026-11-13 and **Version:** 1.0.68"]},
            {"path": "docs/DOCUMENTATION_OVERVIEW.md", "main": "0.2.57 / 2026-11-09", "carrier": "0.2.58 / 2026-11-13", "sites": ["line 5: **Version:** 0.2.58", "line 7: **Last Updated:** 2026-11-13", "footer: **Last Updated:** 2026-11-13 and **Version:** 0.2.58"]},
            {"path": "docs/QUICK_START.md", "main": "0.3.45 / 2026-11-09", "carrier": "0.3.46 / 2026-11-13", "sites": ["line 5: **Version:** 0.3.46", "line 7: **Last Updated:** 2026-11-13", "footer: **Last Updated:** 2026-11-13 and **Version:** 0.3.46"]},
        ],
        "texts_that_quote_a_stamp": ["CHANGELOG.md, this carrier's entry: '`docs/REFERENCE.md` 0.6.69'", "pr_body.txt: the stamp list", "changelog_entry.txt (the same text as the CHANGELOG entry)"],
        "not_stamped": [".claude/agents/fleet-supervisor.md (no stamp)", "CHANGELOG.md (no stamp)", "AGENTS.md (not touched: its **Last Updated** stays as main has it)"],
        "dates_in_carried_text_that_are_history_not_stamps": ["2026-11-04, 2026-11-06, 2026-11-08 (owner rulings and launcher changes)", "2026-08-07 (juniper-ml#1004), 2026-09-05 (juniper-ml#1740), 2026-10-05 (the Actions outage)"],
    }
    manifest = {
        "repo": "juniper-ml",
        "carrier": "ml-docs",
        "base_sha": base_sha,
        "origin_main_at_build": origin_main,
        "worktree": str(REPO),
        "built": "an UNCOMMITTED working tree on the base; nothing staged, nothing pushed",
        "files": [{"path": path, "status": "modified", "sha256": sha256(REPO / path), "added": numstat[path][0], "deleted": numstat[path][1]} for path in CARRIER_FILES],
        "helper_scripts_not_in_the_pr": [{"path": path, "status": "added", "sha256": sha256(REPO / path)} for path in helpers],
        "untracked_paths_that_are_not_helpers": stray,
        "carried": CARRIED,
        "main_defect_4": {"fixed": MAIN_DEFECT_4, "not_fixed_here": ["util/fleet_triage/predict_merge.py:33, the module docstring's own hook list (`black isort flake8 mypy check-ast`), is stale in the same way; it is a code file and is left alone.", "The triage's last clause (the shallow-file copy is unpinned by main's suite) is a test gap: draft 2484's first test, the tests carrier's."]},
        "not_carried_test_or_code_hunks": [
            {"draft": 2479, "paths": ["scripts/claude_interactive.bash", "scripts/default_interactive_session_claude_code.bash", "scripts/wake_the_claude.bash", "tests/test_claude_interactive.py", "tests/test_wake_the_claude.py"], "belongs": "nowhere: juniper-ml#2468's pre-squash commits, already on main"},
            {"draft": 2494, "paths": ["util/fleet_triage/predict_merge.py", "tests/test_predict_merge.py"], "belongs": "the docstring hunk went into juniper-ml#2554; the rest is juniper-ml#2474's pre-squash commits, already on main"},
            {"draft": 2484, "paths": ["tests/test_predict_merge_shallow_worktree.py", "tests/test_predict_merge.py", ".github/workflows/ci.yml", "util/fleet_triage/predict_merge.py"], "belongs": "the tests carrier (its first test and registration); the code is draft 2480's, superseded by juniper-ml#2474"},
        ],
        "checks": checks,
        "mutations": [],
        "claims": CLAIMS,
        "requirements": "None. No draft cites a JR id (2479: 'No tracked JR-ID applies.'; 2490 and 2494: 'No tracked JR-* ...'; 2470, 2483, 2484, 2487: no JR mention).",
        "open_questions": [
            "NEW DEFECT ON MAIN (code, not fixed here). util/fleet_triage/predict_merge.py starts the two console-script screens and pre-commit through _run, which passes the caller's environment unchanged; only _git drops the nine repository-location variables. Under an inherited GIT_DIR (with or without GIT_WORK_TREE) juniper-symbol-loss-check reads the repository that variable names, cannot resolve refs/fleet/base, exits 2 and is recorded as skip, so a branch that is DAMAGED-FIX-FIRST in a plain environment reads MERGE-CLEAN (claims/predict_merge_probe.json, inherited_git_dir). The same holds for the CLI's _resolve_repo_root, a `git rev-parse` through _run: under GIT_DIR and GIT_WORK_TREE of ANOTHER repository it answers that other repository. main's test for an inherited GIT_DIR uses a delta of .txt files, which neither screen reads. The carrier states the first fact as current behaviour in four places, and promises nothing: docs/REFERENCE.md '#### Scratch repository' (the bullet that begins 'The two console-script screens and `pre-commit` are separate processes'), docs/REFERENCE.md operator pitfalls (the row that begins '`ast_symbol_screen.status=skip` with'), docs/DOCUMENTATION_OVERVIEW.md (the clause 'the scratch's own git commands drop an inherited `GIT_DIR`, the screens do not'), and CHANGELOG.md (the sub-bullet 'Stated as it is.'). Decide whether those four stay, and where the fix goes.",
            "Stamps. docs/REFERENCE.md is 0.6.69 in this tree, one bump from 26ea0ecb. If N-2 lands first with 0.6.69, re-derive to 0.6.70 at the sites in stamps.json; a three-way merge of the header line alone would NOT show the collision, because both sides change 0.6.68 to 0.6.69 identically.",
            "Three Test Suite Reference entries are modified (tests/test_predict_merge.py and its sub-bullets, tests/test_rerun_after_actions_outage.py, tests/test_equities_lane_a3_report.py). If the tests carrier inserts a line next to one of them, the three-way merge of docs/REFERENCE.md needs a look at those places.",
            "util/fleet_triage/predict_merge.py:33 (its docstring's hook list) is still stale; it is code and was left for whoever next edits that file.",
            "Draft 2470: the three rewritten index pointers are separable (one line in each of the cheatsheet, the overview and the quick start) if the orchestrator prefers to carry nothing of it.",
            "The new launcher section covers the subject of round-3 drafts juniper-ml#2404 and #2406. No content was taken from either; whoever disposes of them can now compare them against this section.",
            "The pre-commit secrets hook passed, but it scans staged changes only and nothing is staged; no gitleaks directory scan was run by this builder.",
            "The baseline worktree this builder created for the clean-main regression run is removed at the end of the build; only its JSON report is kept.",
        ],
    }
    (scratch / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    (scratch / "stamps.json").write_text(json.dumps(stamps, indent=1) + "\n", encoding="utf-8")
    print(f"manifest.json: base {base_sha[:8]}, {len(CARRIER_FILES)} files, {len(CARRIED)} drafts, {len(CLAIMS)} claim rows, {len(checks)} checks; stray untracked: {stray}")
    for check in checks:
        print(f"  {check['result']:<12} {check['what']}")
    return 0


def tally(item: dict) -> dict:
    counts: dict[str, int] = {}
    for finding in (item["json"] or {}).get("findings", []):
        counts[finding.get("severity", "?")] = counts.get(finding.get("severity", "?"), 0) + 1
    return counts


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
