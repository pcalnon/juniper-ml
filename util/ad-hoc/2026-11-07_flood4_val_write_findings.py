"""
Flood-4 validation (fidelity, fixes and gates lens): write the validator's findings.json to the scratch dir.

Usage: python3 <this> <scratch_dir>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CHECKED = [
    "Carrier identity: the builder worktree's on-disk files hashed as git blobs (plain reads) against every one of the 5672 paths of staged tree ddfae11e; the only 99 mismatches are git-lfs-smudged images (.gitattributes filter=lfs); extra on-disk files are .coverage x2, the .git file and logs/subprocess_tiny_http.log. The carrier IS ddfae11e on 303ccc0b (setup.json).",
    "All 30 draft refs refs/flood4/pr/<N> equal GitHub's headRefOid (gh pr view, read-only) (trace.json gh_heads).",
    "Re-applied the 26 non-rebuilt test drafts' OWN merge-base..head diffs onto 303ccc0b (git apply --cached --3way into a throwaway GIT_INDEX_FILE): all 26 rc 0. The residual against ddfae11e is exactly the recorded fixes/drops (#2410 ci.yml comments, docstring and dropped negative control; #2455 _record helper and patch import; the three builder-authored Test Suite Reference entries; #2466's util-bullet prose moved), the #2403/#2407 rebuilds, the two docs-draft sentences, the CHANGELOG entry and the 11 helpers (reapply_vs_carrier.patch).",
    "Every deleted/altered MAIN line (28) traced: ci.yml 3 (#2410 x2, #2421 x1); docs/REFERENCE.md 3 (#2432, #2424, #2466's 'Tests:' list); CHANGELOG.md 0; juniper-ci-tools test_docs_additions_check.py 1 (#2425); juniper-service-core test_workers_coverage.py 1 (#2430); test_agents_md_touch_up.py 4 (#2414); test_host_state_check.py 5 (#2416); test_recurrence_operation_identity_and_dataset_budget.py 4 (#2431, default 201+size_bytes stub path preserved); test_subpackage_py_typed.py 7 (the manifest's main_text_fixes, justified by the setuptools re-derivation below). test_claude_interactive.py, test_wake_the_claude.py and every other file: 0 deletions. No deleted line is one main added after any draft's merge-base (trace.json deleted_or_altered_main_lines).",
    "Whole-file-copy screen: the carrier's blob equals a draft head's blob only for the 13 NEW files (status A, absent on main); every modified file differs from every draft head (trace.json whole_file_screen).",
    "Test-name sets (AST): the 28 drafts add 123 tests; 121 are carried by name; the 2 differences are the recorded #2410 drop and #2407 rename (test_name_sets.log).",
    "#2424/#2432: each carrier line == the draft's '+' line with only its cross-link removed, and the draft's '-' line == main's line; both claims re-read in util/host_state_check.py:718-724 and util/experiments/run_suite.py:893-904, 995-1001 (docs_hunks.log).",
    "Registrations: ci.yml's regression-step sequence == REFERENCE.md '### Running every suite', 231 == 231 in identical order (main 227 == 227); each new suite follows the same predecessor in both and has a Test Suite Reference entry; tests/test_ci_test_wiring_drift.py 14 OK; util/ad-hoc/2026-09-10_agents_md_test_list_drift.py 0/0/0 with 231 on disk (registration_order.log).",
    "The three builder-authored Test Suite Reference entries checked claim by claim against their test files (PR_BODY_MAX = 65_536 at util/release_train/propose.py:1281; MAX_BRACE_ALTERNATIVES = 64 at util/claude_agent_guard.py:182; the six per-run-timeout cases).",
    "REFERENCE.md stamp untouched (Last Updated 2026-10-08); docs/REFERENCE.md is not memory-budget governed (conf/memory_budget.json). CHANGELOG entry is under the top '## [Unreleased]' (line 8) as '### Added' ahead of main's '### Changed'/'### Fixed', [0.11.4] at line 89; it names all 28 drafts plus #2424/#2432 and its claims match the diff.",
    "Sub-package collection: every test the carrier adds (64 in 14 juniper-service-core files; 2 in juniper-ci-tools/tests/test_docs_additions_check.py) is PASSED in junit XML when run the way ci-service-core.yml (pytest juniper-service-core/tests/... from the root; its pyproject config, python_classes Test*, asyncio_mode strict) and ci-ci-tools.yml (from juniper-ci-tools/) run them; none skipped, no unmarked async test (subpkg_collection.json).",
    "ci.yml: with every run: block removed, the parsed workflow equals main's (job names, step names, matrix, triggers, needs), so no required check name moves; only two run blocks change, both in job `tests` (Install test dependencies; Run Python regression tests). actionlint 1.7.12 -shellcheck= -pyflakes= rc 0 (its shellcheck pass hung here); shellcheck -S warning on both changed blocks: 0 on main, 0 on the carrier (shellcheck_run_blocks.log).",
    "ci.yml effects: #2410 adds `pip install \"setuptools>=68\"` to all three Regression Tests legs (plus comments); #2455/#2448/#2466/#2459 each add one `python3 -m unittest -v` line to the regression step (after release_train_ceremony / run_suite / claude_agent_guard / host_state_check); #2421 is comment-only (its new tests run through the existing invocation). Because ci.yml changes, host-tooling-macos runs all 12 HOST_TOOLING_SUITES; the only carrier-modified one, tests/test_host_state_check.py, adds stdlib-only synthetic-capture tests.",
    "#2459's suite is meaningful on Linux CI: it drives _kubectl/_throughput of util/host_state_check.py with synthetic probes and no shell-out, so leaving it out of HOST_TOOLING_SUITES loses no BSD-userland coverage.",
    "#2410 re-derived: setuptools' build_py.find_data_files always adds _IMPLICIT_DATA_FILES = ('*.pyi', 'py.typed') (81.0.0 build_py.py:25,123-130; same line 25 in 84.2.1, what `setuptools>=68` resolves on PyPI today). Own probe: all 6 sub-packages built with the WHOLE [tool.setuptools.package-data] table deleted still ship <import>/py.typed (py_typed_probe.log). The juniper-config-tools-v0.1.0 tag tree has no py.typed. tests/test_subpackage_py_typed.py is 6/6 OK under Python 3.12.11 + setuptools 84.2.1 (CI parity; py_typed_test_setuptools84_py312.log). No other suite depends on setuptools being absent.",
    "#2455/#2407/#2403 mypy: the pinned hook on the DRAFT heads reports 7 errors (6 func-returns-value at test_release_train_exact_caps.py:167-187, 1 var-annotated at test_claude_interactive.py:435); on the carrier it passes (mypy_drafts_vs_carrier.log).",
    "#2403/#2407 against main's scripts: wake_the_claude.bash TRUE=0/FALSE=1 (104-105), EFFORT_DEFAULT=auto (259), effort parsing (907-952), alias patterns (361-362), '--' before the prompt (1798-1800); claude_interactive.bash parse loop (196-225), '--' appended after the valued options (274), remote control default TRUE (123, 235, 276), --script-version (192, 202), SCRIPT_NAME (55). Every carried expectation is what the scripts do; the 5 + 5 tests pass; full test_claude_interactive.py 33 OK.",
    "Environmental failures: the 5 suites and juniper-ci-tools run in the carrier copy and in a clean origin/main worktree with the same interpreter (3.14.7) and TMPDIR: identical failing test ids in all six (a0_restore_scripts 10, configure_commit_signing 54, e2e_f037_render_census 1, replay_redrive_stack_refusal 13, workflow_script_paths 1, ci-tools 9 of 305 vs 9 of 303), messages identical up to random mkdtemp suffixes (env_failures.json). Main's CI run 42239110639 on 303ccc0b: Regression Tests 3.12/3.13/3.14 and Host Tooling (macOS) success. The carrier introduces none.",
    "67 suites (every tests/ suite that reads ci.yml, REFERENCE.md or CHANGELOG.md, plus the 15 carrier-touched top-level suites), one unittest process each on the carrier copy under 3.14.7: 67 passed (reader_and_touched_suites.json).",
    "Older CI interpreters: py_compile of all 41 changed .py and the 15 touched top-level suites + 15 touched sub-package files under 3.13.13: 0 failures; under 3.12.11: 0 failures once juniper-model-core is on the path as ci-service-core.yml installs it (two new lifecycle files first failed with ModuleNotFoundError: juniper_model_core, this interpreter's gap) (older_pythons.json).",
    "CodeQL prescreen on all 41 changed .py (including the 11 helpers): 9 predictions, 0 on changed lines; the same 9 appear on main's copies of the three files (codeql_prescreen.json).",
    "Pinned pre-commit on the 33 non-helper paths and on the 11 helpers: rc 0, no file rewritten; G5 home-path check on the helpers: 0 literal lines; util/markdown_structure_delta.py 303ccc0b..af80cd27 (the builder's probe commit of ddfae11e): 0 regressions; sequence-safety screens from in-repo juniper-ci-tools 0.9.1 (the PyPI version CI installs): symbol-loss 0 findings, docs-additions 3 WARN small-deletion, fail 0 (precommit_all.log, precommit_helpers.log, symbol_loss.log, docs_additions.log).",
]

NOT_CHECKED = [
    "The macOS host-tooling leg itself (no macOS runner here); reasoned only: the one carrier-modified host-tooling suite is stdlib-only synthetic captures.",
    "The full 231-suite regression list end to end; 67 suites were re-run (all ci.yml/REFERENCE.md/CHANGELOG.md readers and every carrier-touched suite).",
    "Mutation re-runs (another lens): the builder's 30 records were read, not re-executed.",
    "The ruleset's required-context list was not fetched; required names were judged by the workflow being identical outside run: blocks.",
    "actionlint's own shellcheck/pyflakes pass (hung on this host); replaced by shellcheck run directly on the two changed run blocks.",
]

FINDINGS = [
    {
        "id": "F1",
        "severity": "MINOR",
        "where": "AGENTS.md:65",
        "claim": "The carrier adds 4 suites (ci.yml and REFERENCE.md now list 231) but AGENTS.md still says 'the full ordered list of 227 `python3 -m unittest` commands lives in docs/REFERENCE.md'. Every one of the last 8 commits on main that added a top-level suite also bumped this number (e.g. 2e2a65cc: 226 -> 227), and no gate catches it (2026-09-10_agents_md_test_list_drift.py compares REFERENCE.md, ci.yml and disk only). Severity uncertain: it is resident memory every agent loads, so the stale count misleads; nothing fails.",
        "evidence": "grep -n 227 AGENTS.md -> '65:# Run all tests -- the full ordered list of 227 `python3 -m unittest`'; util/ad-hoc/2026-11-07_flood4_val_registration_order.py -> 'carrier: ci 231 ... run-list 231'; git log -G'full ordered list of [0-9]+' 303ccc0b -- AGENTS.md lists the same 8 commits as git log --diff-filter=A -- 'tests/test_*.py'.",
        "fix": "Change 227 to 231 in AGENTS.md:65 and bump its **Last Updated** to the PR's UTC date (.github/workflows/agents-md-touch-up.yml:121-128 fails a PR that changes AGENTS.md without the bump), or record it as a follow-up.",
    },
    {
        "id": "F2",
        "severity": "MINOR",
        "where": "tests/test_claude_interactive.py:621-622",
        "claim": "Carried verbatim from the #2407 draft: 'No valued option was added, so the `--` separator, which is inserted only in front of those, is absent.' claudey appends `--` AFTER the valued options, not in front of them, and the carrier's own sibling test asserts exactly that order.",
        "evidence": "scripts/claude_interactive.bash:269-274 appends --model/--effort/--id/--worktree, then '(( ${#CLAUDE_ARGS[@]} > 0 )) && CLAUDE_ARGS+=(\"${CLAUDE_SEPERATOR_FLAG}\")'; tests/test_claude_interactive.py:599 'self.assertLess(args.index(\"--effort\"), args.index(\"--\"))'.",
        "fix": "'...so the `--` separator, which claudey appends only after a valued option, is absent.'",
    },
    {
        "id": "F3",
        "severity": "MINOR",
        "where": "pr_body.txt line 53 (builder scratch tmp/flood4/ml-tests/tests/pr_body.txt); manifest.json carried[#2403].reason",
        "claim": "'#2403. Five of six tests expected the argv from before juniper-ml#2438' (manifest: '5 of 6 tests failed on the merged tree (10 with subtests)'). The draft adds exactly five tests; four assert the pre-#2438 argv (no `--`), the fifth (missing effort) asserts no launch. The '10 with subtests' matches those four (1 + 1 + 4 + 4).",
        "evidence": "git diff b22126a4 refs/flood4/pr/2403 --stat -> 'tests/test_wake_the_claude.py | 71 +++', five '+    def test_' lines; its assertEqual(args, ...) lines carry no '--'.",
        "fix": "'Four of its five tests expected the argv from before juniper-ml#2438 ...'.",
    },
    {
        "id": "F4",
        "severity": "MINOR",
        "where": "tests/test_subpackage_py_typed.py:19-26 and 35-39",
        "claim": "The rewritten module docstring states the implicit-pattern fact twice (lines 21-22 and 35-37) and pins it to 'setuptools 81.0.0', the local version; CI's `setuptools>=68` resolves to 84.2.1, which carries the same _IMPLICIT_DATA_FILES, so the text is true but narrower than what CI runs.",
        "evidence": "sed -n 19,39p tests/test_subpackage_py_typed.py; grep -n '^_IMPLICIT_DATA_FILES' <venv setuptools 84.2.1>/setuptools/command/build_py.py -> '25:_IMPLICIT_DATA_FILES = (\\'*.pyi\\', \\'py.typed\\')'; PyPI setuptools latest 84.2.1.",
        "fix": "Keep one statement, e.g. 'observed in setuptools 81.0.0 and 84.2.1', and drop the repeat in the second paragraph.",
    },
]


def main() -> int:
    scratch = Path(sys.argv[1])
    doc = {
        "carrier": "juniper-ml flood-4 TESTS carrier: builder worktree .claude/worktrees/agent-a7674bdaf3240b78b, base origin/main 303ccc0b4613dadcbe5ef16985a862beccec7a1a, staged tree ddfae11e73e0663bf798fef2834dfc559493e7fe (44 paths)",
        "lens": "fidelity, fixes and gates",
        "validator_worktrees": {
            "carrier_copy": "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/agent-adfe0777292754a5c (HEAD 303ccc0b + all 44 carrier paths, uncommitted, plus the validator's util/ad-hoc/2026-11-07_flood4_val_*.py helpers)",  # home-path-literal: allow
            "clean_main": "/home/pcalnon/Development/python/Juniper/worktrees/juniper-ml--val-fidelity-clean-main--20261107-1800--303ccc0b (detached 303ccc0b, no carrier files; left in place)",  # home-path-literal: allow
        },
        "checked": CHECKED,
        "not_checked": NOT_CHECKED,
        "findings": FINDINGS,
    }
    out = scratch / "findings.json"
    out.write_text(json.dumps(doc, indent=2) + "\n")
    counts: dict[str, int] = {}
    for f in FINDINGS:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    print(out, counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
