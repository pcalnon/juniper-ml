"""
The tests-lens validator's own mutants of what the ml-tests carrier's test files pin, run in a COPY of the landing.

Every mutant is an exact-text edit (the old text must occur once) of product code, a workflow, a document or, for the
harness class, of the test file's own fixture. It is applied in --tree (a landed copy the validator made, never the
carrier), the named suite is run, and the file is restored in a ``finally:`` block; the sha256 of every touched file
is compared with its value before the run after EVERY mutant. The hashes of every file the run may touch are written
to --progress before the first mutant.

A product mutant is KILLED when the suite fails; a harness mutant is expected to make the test FAIL too (a test that
still passes after its fixture is broken is vacuous). --baseline runs every suite unmutated first and counts
``def test_`` (by ast) against unittest's ``Ran N tests``.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent, flood-4 session 7)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --tree <landed copy> --out <dir> --progress <PROGRESS.txt> [--baseline] [--only ID ...]
        [--own-repo <the validator's own worktree, for draft blobs>]
"""

import argparse
import ast
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
DEAD_BUS = "unix:path=/nonexistent/no-session-bus"
RAN_RE = re.compile(r"^Ran (\d+) tests? in", re.M)
ID_RE = re.compile(r"^(?P<kind>FAIL|ERROR): (?P<name>\S+) \((?P<where>[^)]*)\)", re.M)
PYTEST_FAIL_RE = re.compile(r"^(?:FAILED|ERROR) (\S+)", re.M)

GUARD = "util/claude_agent_guard.py"
WAKE = "scripts/wake_the_claude.bash"
CLAUDEY = "scripts/claude_interactive.bash"
PM = "util/fleet_triage/predict_merge.py"
STATS = "util/experiments/stats_summary.py"
SLC = "juniper-ci-tools/juniper_ci_tools/symbol_loss_check.py"
REF = "docs/REFERENCE.md"
CI = ".github/workflows/ci.yml"
PYPROJECT = "pyproject.toml"
T = "tests/"
CI_TOOLS_TEST = "juniper-ci-tools/tests/test_symbol_loss_weaken_boundary.py"

BASELINE_SUITES = (
    T + "test_claude_agent_guard_nest_depth.py",
    T + "test_claude_agent_guard_push_signed.py",
    T + "test_claude_agent_guard_ansi_escapes.py",
    T + "test_claude_agent_guard_gpgsign_off.py",
    T + "test_claude_agent_guard_sign_edges.py",
    T + "test_launcher_empty_version_output.py",
    T + "test_launcher_prompt_and_version_edges.py",
    T + "test_prompt_file_boolean_tokens.py",
    T + "test_prompt_file_kind.py",
    T + "test_wake_spacer_flags.py",
    T + "test_predict_merge_error_screen.py",
    T + "test_predict_merge_guard_edges.py",
    T + "test_predict_merge_scratch_edges.py",
    T + "test_predict_merge_shallow_worktree.py",
    T + "test_cascor_eval_zero_and_enabled.py",
    CI_TOOLS_TEST,
    T + "test_ci_host_tooling_macos.py",
    T + "test_predict_merge.py",
    T + "test_pyproject_extras.py",
)


def edit(path, old, new):
    return {"path": path, "old": old, "new": new}


def create(path, text=None, blob=None):
    return {"path": path, "create": True, "text": text, "blob": blob}


MUTANTS = [
    # ---- the agent guard -------------------------------------------------------------------------------------
    {"id": "G1", "kind": "product", "suite": T + "test_claude_agent_guard_nest_depth.py", "claim": "a depth equal to the cap is still analysed", "edits": [edit(GUARD, "        if depth > MAX_DEPTH:\n", "        if depth >= MAX_DEPTH:\n")]},
    {"id": "G2", "kind": "product", "suite": T + "test_claude_agent_guard_push_signed.py", "claim": "a prefix check would let falsehood / 00 / 0.0 through", "edits": [edit(GUARD, '    return text.partition("=")[2].casefold() not in _PUSH_SIGNED_OFF\n', '    return not text.partition("=")[2].casefold().startswith(_PUSH_SIGNED_OFF)\n')]},
    {"id": "G3", "kind": "product", "suite": T + "test_claude_agent_guard_ansi_escapes.py", "claim": "U+10FFFF itself stays that character", "edits": [edit(GUARD, 'out.append(chr(value) if value <= 0x10FFFF else "?")', 'out.append(chr(value) if value < 0x10FFFF else "?")')]},
    {"id": "G3b", "kind": "product", "suite": T + "test_claude_agent_guard_ansi_escapes.py", "claim": "three octal digits are decoded", "edits": [edit(GUARD, 'spec = (r"[0-7]{1,3}", 8, 1)', 'spec = (r"[0-7]{1,2}", 8, 1)')]},
    {"id": "G4", "kind": "product", "suite": T + "test_claude_agent_guard_gpgsign_off.py", "claim": "a prefix check would allow falsehood and offside", "edits": [edit(GUARD, 'value.strip().casefold() not in ("false", "no", "off", "0")', 'not value.strip().casefold().startswith(("false", "no", "off", "0"))')]},
    {
        "id": "G5",
        "kind": "product",
        "suite": T + "test_claude_agent_guard_sign_edges.py",
        "claim": "a guard that stops at the first gpgsign key would allow a later on-switch",
        "edits": [
            edit(
                GUARD,
                '                        self.hit("GPG-SIGN", "git -c " + rest[i].text)\n                    if GIT_DASH_C_SIGNING_RE.match(key.strip()):\n',
                '                        self.hit("GPG-SIGN", "git -c " + rest[i].text)\n                    elif "gpgsign" in key.casefold():\n                        return\n                    if GIT_DASH_C_SIGNING_RE.match(key.strip()):\n',
            )
        ],
    },
    {"id": "G6", "kind": "product", "suite": T + "test_claude_agent_guard_sign_edges.py", "claim": "am -S is a signing form", "edits": [edit(GUARD, '"cherry-pick", "revert", "am", "pull", "commit-tree")', '"cherry-pick", "revert", "pull", "commit-tree")')]},
    # ---- the launchers ---------------------------------------------------------------------------------------
    {"id": "W1", "kind": "product", "suite": T + "test_launcher_empty_version_output.py", "claim": "a version of one character (0) still counts", "edits": [edit(WAKE, '            if [[ "${current_version}" == "" ]]; then\n', '            if [[ ( "${current_version}" == "" ) || ( "${current_version}" == "${TRUE}" ) ]]; then\n')]},
    {"id": "W1b", "kind": "product", "suite": T + "test_launcher_empty_version_output.py", "claim": "no version text exits 1", "edits": [edit(WAKE, '                echo "Error: \\"${version_bin} ${CLAUDE_VERSION_FLAGS}\\" printed no version" >&2\n                result_value="${FALSE}"\n', '                echo "Error: \\"${version_bin} ${CLAUDE_VERSION_FLAGS}\\" printed no version" >&2\n                result_value="${TRUE}"\n')]},
    {"id": "W2", "kind": "product", "suite": T + "test_launcher_prompt_and_version_edges.py", "claim": "a missing --file must not fail the launch when a prompt was given", "edits": [edit(WAKE, 'if [[ ( "${VALID_PROMPT_PARAM}" != "${TRUE}" ) && ( ( "${FILE_NAME}" != "" ) || ( "${PATH_NAME}" != "" ) ) && ( "${PROMPT_FILE}" == "" ) ]]; then', 'if [[ ( ( "${FILE_NAME}" != "" ) || ( "${PATH_NAME}" != "" ) ) && ( "${PROMPT_FILE}" == "" ) ]]; then')]},
    {"id": "W3", "kind": "product", "suite": T + "test_launcher_prompt_and_version_edges.py", "claim": "--prompt 1 (false) leaves the file as the prompt", "edits": [edit(WAKE, '        elif [[ "${current_prompt}" == "${FALSE}" ]]; then\n', '        elif [[ "${current_prompt}" == "never-false" ]]; then\n')]},
    {"id": "W4", "kind": "product", "suite": T + "test_launcher_prompt_and_version_edges.py", "claim": "CLAUDE_PROMPT_PATH alone suppresses the default prompt", "edits": [edit(CLAUDEY, 'if [[ ( "${CLAUDE_PROMPT_FILE_PARAM}" != "" ) || ( "${CLAUDE_PROMPT_PATH_PARAM}" != "" ) ]]; then', 'if [[ ( "${CLAUDE_PROMPT_FILE_PARAM}" != "" ) ]]; then')]},
    {"id": "W5", "kind": "product", "suite": T + "test_launcher_prompt_and_version_edges.py", "claim": "CLAUDE_PROMPT=0 with a file is refused", "edits": [edit(CLAUDEY, '( "${CLAUDE_PROMPT:-}" == "${FALSE}" ) ]] || usage 1 "A prompt and a prompt file are exclusive', '( "${CLAUDE_PROMPT:-}" == "${FALSE}" ) || ( "${CLAUDE_PROMPT:-}" == "${TRUE}" ) ]] || usage 1 "A prompt and a prompt file are exclusive')]},
    {"id": "W6", "kind": "product", "suite": T + "test_prompt_file_boolean_tokens.py", "claim": "a prompt file holding 1 is that prompt", "edits": [edit(WAKE, '    elif [[ ! "${prompt_text}" =~ [^[:space:]] ]]; then\n', '    elif [[ ( ! "${prompt_text}" =~ [^[:space:]] ) || ( "${prompt_text}" == "${FALSE}" ) ]]; then\n')]},
    {"id": "W7", "kind": "product", "suite": T + "test_prompt_file_kind.py", "claim": "treating the directory as a file (-e) would report could-not-be-read", "edits": [edit(WAKE, '    if [[ ! -f "${current_file}" ]]; then\n', '    if [[ ! -e "${current_file}" ]]; then\n')]},
    {"id": "W8", "kind": "product", "suite": T + "test_prompt_file_kind.py", "claim": "prompt loading follows a symlink to a regular file", "edits": [edit(WAKE, '    if [[ ( "${prompt_file}" == "" ) || ( ! -f "${prompt_file}" ) || ( ! -r "${prompt_file}" ) ]]; then\n', '    if [[ ( "${prompt_file}" == "" ) || ( ! -f "${prompt_file}" ) || ( -L "${prompt_file}" ) || ( ! -r "${prompt_file}" ) ]]; then\n')]},
    {"id": "W9", "kind": "product", "suite": T + "test_wake_spacer_flags.py", "claim": "end-of-options would append the following words to claude's argv", "edits": [edit(WAKE, '        "${SPACER_FLAGS_INDEX}")         parse_spacer_flags             "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;', '        "${SPACER_FLAGS_INDEX}")         CLAUDE_PERMISSIONS_VALUE+=("${UPDATED_PARAMS[@]}"); UPDATED_PARAMS=() ;;')]},
    # ---- predict_merge ---------------------------------------------------------------------------------------
    {"id": "P1", "kind": "product", "suite": T + "test_predict_merge_error_screen.py", "claim": "the ERROR row stays in the denominator", "edits": [edit(PM, '"screened_fraction": round(evaluated / len(verdicts), 3) if verdicts else 0.0,', '"screened_fraction": round(evaluated / max(evaluated, 1), 3) if verdicts else 0.0,')]},
    {"id": "P1b", "kind": "product", "suite": T + "test_predict_merge_error_screen.py", "claim": "an absent status stays out of evaluated", "edits": [edit(PM, '        evaluated = tally["pass"] + tally["fail"]\n', '        evaluated = tally["pass"] + tally["fail"] + tally["absent"]\n')]},
    {"id": "P2", "kind": "product", "suite": T + "test_predict_merge_guard_edges.py", "claim": "GIT_INDEX_FILE dropped from the denylist makes simulate_merge raise", "edits": [edit(PM, '    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",\n', '    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR",\n')]},
    {"id": "P3", "kind": "product", "suite": T + "test_predict_merge_guard_edges.py", "claim": "GIT_OBJECT_DIRECTORY dropped from the denylist makes simulate_merge raise", "edits": [edit(PM, '    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE",\n', '    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE",\n')]},
    {"id": "P4", "kind": "product", "suite": T + "test_predict_merge_guard_edges.py", "claim": "a prepare failure removes the scratch directory", "edits": [edit(PM, '    except OSError as exc:\n        shutil.rmtree(scratch, ignore_errors=True)\n        raise PredictMergeError(f"could not prepare', '    except OSError as exc:\n        raise PredictMergeError(f"could not prepare')]},
    {"id": "P5", "kind": "product", "suite": T + "test_predict_merge_guard_edges.py", "claim": "a failed merge must not leave the scratch behind", "edits": [edit(PM, "        if scratch is not None and not keep_scratch:\n", "        if scratch is not None and not keep_scratch and sys.exc_info()[0] is None:\n")]},
    {"id": "P6a", "kind": "product", "suite": T + "test_predict_merge_scratch_edges.py", "claim": "the alternate names the COMMON directory's objects, not --git-dir's", "edits": [edit(PM, '    common = _git(repo_root, "rev-parse", "--path-format=absolute", "--git-common-dir")\n', '    common = _git(repo_root, "rev-parse", "--path-format=absolute", "--git-dir")\n')]},
    {"id": "P6b", "kind": "product", "suite": T + "test_predict_merge_shallow_worktree.py", "claim": "a linked worktree's graft is the common directory's", "edits": [edit(PM, '    common = _git(repo_root, "rev-parse", "--path-format=absolute", "--git-common-dir")\n', '    common = _git(repo_root, "rev-parse", "--path-format=absolute", "--git-dir")\n')]},
    {"id": "P7", "kind": "product", "suite": T + "test_predict_merge_shallow_worktree.py", "claim": "the scratch copies the common directory's shallow file", "edits": [edit(PM, '            shutil.copyfile(shallow, clone / ".git" / "shallow")\n', '            (clone / ".git" / "shallow").write_text(shallow.read_text(encoding="utf-8").splitlines()[0] + "\\n", encoding="utf-8")\n')]},
    {"id": "P8", "kind": "product", "suite": T + "test_predict_merge.py", "claim": "a non-shallow source's scratch gets no shallow graft", "edits": [edit(PM, '            shutil.copyfile(shallow, clone / ".git" / "shallow")\n', '            shutil.copyfile(shallow, clone / ".git" / "shallow")\n        else:\n            (clone / ".git" / "shallow").write_text(base_sha + "\\n", encoding="utf-8")\n')]},
    # ---- stats_summary ---------------------------------------------------------------------------------------
    {"id": "S1", "kind": "product", "suite": T + "test_cascor_eval_zero_and_enabled.py", "claim": "enabled of 0 is not the off switch (the in-loop arm)", "edits": [edit(STATS, '    elif live is not None and live.get("enabled") is False:\n', '    elif live is not None and not live.get("enabled", True):\n')]},
    {"id": "S2", "kind": "product", "suite": T + "test_cascor_eval_zero_and_enabled.py", "claim": "held_out is true only when the split is exactly test", "edits": [edit(STATS, 'isinstance(final, Mapping) and final.get("split") == "test", absent)', 'isinstance(final, Mapping) and str(final.get("split")).strip().lower() == "test", absent)')]},
    {"id": "S3", "kind": "product", "suite": T + "test_cascor_eval_zero_and_enabled.py", "claim": "eval_caption prints n=0", "edits": [edit(STATS, "n={n_samples if n_samples is not None else 'unknown'}", "n={n_samples or 'unknown'}")]},
    {"id": "S4", "kind": "product", "suite": T + "test_cascor_eval_zero_and_enabled.py", "claim": "a test split is held out only when the block says so", "edits": [edit(STATS, '    if block.get("held_out"):\n        status = "held out"\n', '    if block.get("held_out") or split == "test":\n        status = "held out"\n')]},
    # ---- juniper-ci-tools ------------------------------------------------------------------------------------
    {"id": "C1", "kind": "product", "suite": CI_TOOLS_TEST, "claim": "both arms must hold", "edits": [edit(SLC, "            if hsym.lines <= WEAKEN_RATIO * bsym.lines and (bsym.lines - hsym.lines) >= WEAKEN_MIN_DELTA:\n", "            if hsym.lines <= WEAKEN_RATIO * bsym.lines or (bsym.lines - hsym.lines) >= WEAKEN_MIN_DELTA:\n")]},
    # ---- #2507: docs/REFERENCE.md against pyproject.toml, and finding F6 ----------------------------------------
    {"id": "R1", "kind": "product", "suite": T + "test_pyproject_extras.py", "claim": "the current series row's juniper-cascor cell", "edits": [edit(REF, "| 0.11.x     | >=0.17.1     | >=0.12.0       |", "| 0.11.x     | >=0.17.1     | >=0.11.0       |")]},
    {"id": "R2", "kind": "product", "suite": T + "test_pyproject_extras.py", "claim": "the sets-them-to clause holds all three recurrence pins", "edits": [edit(REF, "sets them to `juniper-recurrence-model>=0.6.0,<0.7.0`, `juniper-recurrence>=0.8.1,<0.9.0` and `juniper-recurrence-client>=0.3.0,<0.4.0` (see", "sets them to `juniper-recurrence-model>=0.6.0,<0.7.0` and `juniper-recurrence>=0.8.1,<0.9.0` (see")]},
    {"id": "R3", "kind": "product", "suite": T + "test_pyproject_extras.py", "claim": "one Version cell", "edits": [edit(REF, "| **Version**            | `0.11.4`     |\n", "| **Version**            | `0.11.4`     |\n| **Version**            | `0.11.4`     |\n")]},
    {"id": "R4", "kind": "product", "suite": T + "test_pyproject_extras.py", "claim": "a floor raised in pyproject.toml alone fails the row test; the two F6 tests stay green", "expect_pass": ["test_spec_drops_the_extras_marker", "test_parser_reads_the_current_series_row_not_an_older_one"], "edits": [edit(PYPROJECT, '    "juniper-data-client>=0.5.0",\n', '    "juniper-data-client>=0.5.1",\n')]},
    {"id": "R5", "kind": "harness-parser", "suite": T + "test_pyproject_extras.py", "claim": "F6: a parser that keeps the extras marker (in the spec) fails test_spec_drops_the_extras_marker", "edits": [edit(T + "test_pyproject_extras.py", '_REQ_SPEC_RE = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+)(?:\\[[^\\]]*\\])?(?P<spec>>=.+)$")', '_REQ_SPEC_RE = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+)(?P<spec>(?:\\[[^\\]]*\\])?>=.+)$")')]},
    {"id": "R6", "kind": "harness-parser", "suite": T + "test_pyproject_extras.py", "claim": "F6: a parser that gives every row the newest row's cells fails the series-row test", "edits": [edit(T + "test_pyproject_extras.py", "        if cells and cells[0]:\n            rows[cells[0]] = cells\n", "        if cells and cells[0]:\n            rows[cells[0]] = cells\n            for key in rows:\n                rows[key] = [key] + cells[1:]\n")]},
    {"id": "R7", "kind": "harness-parser", "suite": T + "test_pyproject_extras.py", "claim": "parsing stops at the first line that is not part of the table, so a later table is not a row", "edits": [edit(T + "test_pyproject_extras.py", '        if not line.startswith("|"):\n            break\n', '        if not line.startswith("|"):\n            continue\n')]},
    # ---- the macOS wiring (the Overtoad's ruling of 2026-11-12) ---------------------------------------------------
    {"id": "D1", "kind": "product", "suite": T + "test_ci_host_tooling_macos.py", "claim": "a suite removed from the list fails the pin", "edits": [edit(CI, "        claude_agent_guard_nest_depth claude_agent_guard_push_signed claude_agent_guard_ansi_escapes", "        claude_agent_guard_push_signed claude_agent_guard_ansi_escapes")]},
    {"id": "D2", "kind": "product", "suite": T + "test_ci_host_tooling_macos.py", "claim": "a suite added without the pin fails", "edits": [edit(CI, "        mcp_setup\n      HOST_TOOLING_PATHS: >-\n", "        mcp_setup wake_the_claude\n      HOST_TOOLING_PATHS: >-\n")]},
    {"id": "D3", "kind": "product", "suite": T + "test_ci_host_tooling_macos.py", "claim": "the trigger paths cover every guard suite", "edits": [edit(CI, '          for suite in $HOST_TOOLING_SUITES; do echo "tests/test_${suite}.py"; done > "$watched"\n', '          for suite in $HOST_TOOLING_SUITES; do case "$suite" in claude_agent_guard_*) continue ;; esac; echo "tests/test_${suite}.py"; done > "$watched"\n')]},
    {
        "id": "D4",
        "kind": "harness",
        "suite": T + "test_ci_host_tooling_macos.py",
        "claim": "a guard suite dropped from the list AND from the pin still fails (the on-disk comparison)",
        "edits": [
            edit(CI, "claude_agent_guard_push_signed claude_agent_guard_ansi_escapes claude_agent_guard_gpgsign_off", "claude_agent_guard_push_signed claude_agent_guard_gpgsign_off"),
            edit(T + "test_ci_host_tooling_macos.py", '    "claude_agent_guard_ansi_escapes",\n', ""),
        ],
    },
    {"id": "D5", "kind": "product", "suite": T + "test_ci_host_tooling_macos.py", "claim": "a new guard suite on disk that is not listed fails", "edits": [create(T + "test_claude_agent_guard_zz_probe.py", text='"""Validator probe: an agent-guard suite on disk that no list names."""\n')]},
    {"id": "D6a", "kind": "product", "suite": T + "test_ci_host_tooling_macos.py", "claim": "each listed suite also runs in the Linux regression step", "edits": [edit(CI, "          python3 -m unittest -v tests/test_claude_agent_guard_sign_edges.py\n", "")]},
    {"id": "D6b", "kind": "product", "suite": T + "test_ci_test_wiring_drift.py", "claim": "a suite on disk that ci.yml does not invoke fails the wiring-drift suite", "edits": [edit(CI, "          python3 -m unittest -v tests/test_claude_agent_guard_sign_edges.py\n", "")]},
    {"id": "D6c", "kind": "product", "suite": T + "test_ci_test_wiring_drift.py", "claim": "a carried launcher suite that ci.yml does not invoke fails the wiring-drift suite", "edits": [edit(CI, "          python3 -m unittest -v tests/test_wake_spacer_flags.py\n", "")]},
    # ---- harness mutants: the test must FAIL when its own fixture is broken ------------------------------------
    {"id": "H1", "kind": "harness", "suite": T + "test_claude_agent_guard_nest_depth.py", "claim": "one eval fewer than asked: the one-past-the-cap test must fail", "edits": [edit(T + "test_claude_agent_guard_nest_depth.py", '    return ("eval " * depth) + command\n', '    return ("eval " * (depth - 1)) + command\n')]},
    {"id": "H2", "kind": "harness", "suite": T + "test_launcher_empty_version_output.py", "claim": "a fake claude that always prints a version: the refusal test must fail", "edits": [edit(T + "test_launcher_empty_version_output.py", "'  printf %s \"$VERSION_STDOUT\"\\n'", "'  printf %s \"9.9.9\"\\n'")]},
    {"id": "H3", "kind": "harness", "suite": T + "test_predict_merge_scratch_edges.py", "claim": "a stand-in smudge that never refuses: the negative control must fail", "edits": [edit(T + "test_predict_merge_scratch_edges.py", "'if [ \"$GIT_LFS_SKIP_SMUDGE\" = \"1\" ]; then\\n'", "'if [ \"$GIT_LFS_SKIP_SMUDGE\" != \"never\" ]; then\\n'")]},
    {"id": "H5", "kind": "harness", "suite": T + "test_pyproject_extras.py", "claim": "F6 fixture with equal rows: the series-row test must fail", "edits": [edit(T + "test_pyproject_extras.py", "| 9.9.x      | >=9.9.1      |", "| 9.9.x      | >=9.9.0      |")]},
    {"id": "H6", "kind": "harness", "suite": T + "test_predict_merge_error_screen.py", "claim": "an ERROR row whose gates all pass: the absent test must fail", "edits": [edit(T + "test_predict_merge_error_screen.py", '        "gates": {},\n', '        "gates": {"ast_symbol_screen": {"status": "pass"}, "docs_additions_only": {"status": "pass"}},\n')]},
    {"id": "H7", "kind": "harness", "suite": T + "test_predict_merge_shallow_worktree.py", "claim": "no graft written: the shallow precondition must fail", "edits": [edit(T + "test_predict_merge_shallow_worktree.py", '        shallow.write_text(graft, encoding="utf-8")\n', "")]},
    # ---- the draft's own LFS test (#2481), as submitted, against each LFS protection removed -------------------
    {"id": "X1", "kind": "draft-claim", "suite": "tests.test_zz_draft2481_scratch_edges.ScratchBorrowEdgesTest.test_lfs_checkout_leaves_the_pointer_in_place", "claim": "the draft's LFS test passes with the smudge-skip variable removed", "edits": [create(T + "test_zz_draft2481_scratch_edges.py", blob="refs/flood4r2v/pr/2481:tests/test_predict_merge_scratch_edges.py"), edit(PM, '    env["GIT_LFS_SKIP_SMUDGE"] = "1"\n', "")]},
    {"id": "X2", "kind": "draft-claim", "suite": "tests.test_zz_draft2481_scratch_edges.ScratchBorrowEdgesTest.test_lfs_checkout_leaves_the_pointer_in_place", "claim": "the draft's LFS test passes with the scratch's filter attribute removed", "edits": [create(T + "test_zz_draft2481_scratch_edges.py", blob="refs/flood4r2v/pr/2481:tests/test_predict_merge_scratch_edges.py"), edit(PM, '        (clone / ".git" / "info" / "attributes").write_text("* -filter\\n", encoding="utf-8")\n', "")]},
    {"id": "X0", "kind": "draft-claim", "suite": "tests.test_zz_draft2481_scratch_edges.ScratchBorrowEdgesTest.test_lfs_checkout_leaves_the_pointer_in_place", "claim": "the draft's LFS test passes unmutated (control)", "edits": [create(T + "test_zz_draft2481_scratch_edges.py", blob="refs/flood4r2v/pr/2481:tests/test_predict_merge_scratch_edges.py")]},
]


def sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).is_file() else "absent"


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def child_env():
    env = dict(os.environ)
    for name in SENTRY_DSN_NAMES:
        env[name] = ""
    env["DBUS_SESSION_BUS_ADDRESS"] = DEAD_BUS
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_suite(tree, suite, timeout):
    if suite.startswith("juniper-ci-tools/"):
        argv = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", suite[len("juniper-ci-tools/") :]]
        cwd = Path(tree) / "juniper-ci-tools"
    else:
        argv = [sys.executable, "-B", "-m", "unittest", "-v", suite]
        cwd = Path(tree)
    try:
        proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, check=False, env=child_env())
        rc, out = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out = 124, "TIMEOUT after %ss\n%s%s" % (timeout, exc.stdout or "", exc.stderr or "")
    ran = RAN_RE.findall(out) or re.findall(r"(\d+) (?:passed|failed)", out)
    ids = sorted({"%s %s (%s)" % (m.group("kind"), m.group("name"), m.group("where")) for m in ID_RE.finditer(out)} | set(PYTEST_FAIL_RE.findall(out)))
    return rc, out, (int(ran[-1]) if ran and not suite.startswith("juniper-ci-tools/") else sum(int(n) for n in ran) if ran else None), ids


def count_tests(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    names = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            names += ["%s.%s" % (node.name, item.name) for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_")]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            names.append(node.name)
    after_main = []
    main_line = None
    for node in tree.body:
        if isinstance(node, ast.If) and "__name__" in ast.dump(node.test):
            main_line = node.lineno
        elif main_line is not None and isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            after_main.append(node.name)
    skips = sorted(set(re.findall(r"skip(?:Test|If|Unless)?\b", Path(path).read_text(encoding="utf-8"))))
    return names, after_main, skips


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--progress", required=True)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--own-repo")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args(argv)

    tree, out = Path(args.tree).resolve(), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if "flood4r2-ml-tests-r2-tests-mut" not in tree.name:
        raise SystemExit("--tree must be the validator's own mutation copy, got %s" % tree)
    chosen = [m for m in MUTANTS if not args.only or m["id"] in args.only]

    touched = sorted({e["path"] for m in chosen for e in m["edits"]})
    before = {path: sha256_of(tree / path) for path in touched}
    with open(args.progress, "a", encoding="utf-8") as fh:
        fh.write("%s MUTATION RUN START in %s (%d mutants: %s). sha256 BEFORE of every file it may touch: %s\n" % (stamp(), tree, len(chosen), " ".join(m["id"] for m in chosen), json.dumps(before, sort_keys=True)))

    results = {"tree": str(tree), "interpreter": sys.version.split()[0], "before": before, "baseline": [], "mutants": []}
    if args.baseline:
        for suite in BASELINE_SUITES:
            names, after_main, skips = count_tests(tree / suite)
            rc, text, ran, ids = run_suite(tree, suite, args.timeout)
            (out / ("baseline__" + suite.replace("/", "__") + ".log")).write_text(text, encoding="utf-8")
            row = {"suite": suite, "rc": rc, "ran": ran, "def_test": len(names), "counts_agree": ran == len(names), "defined_after_main_block": after_main, "skip_words": skips, "failing_ids": ids, "skipped_in_output": len(re.findall(r"\.\.\. skipped", text))}
            results["baseline"].append(row)
            print("BASELINE %-62s rc=%s ran=%s def_test=%s agree=%s after_main=%s skips=%s skipped=%d" % (suite, rc, ran, len(names), row["counts_agree"], after_main, skips, row["skipped_in_output"]), flush=True)

    for mutant in chosen:
        row = {"id": mutant["id"], "kind": mutant["kind"], "suite": mutant["suite"], "claim": mutant["claim"], "edits": [{k: v for k, v in e.items() if k != "text"} for e in mutant["edits"]]}
        originals = {}
        created = []
        try:
            problem = None
            for e in mutant["edits"]:
                target = tree / e["path"]
                if e.get("create"):
                    if target.exists():
                        problem = "%s already exists" % e["path"]
                        break
                    if e.get("blob"):
                        done = subprocess.run(["git", "show", e["blob"]], cwd=args.own_repo, capture_output=True, check=False)
                        if done.returncode != 0:
                            problem = "no blob %s" % e["blob"]
                            break
                        content = done.stdout
                    else:
                        content = e["text"].encode("utf-8")
                    created.append(target)
                    target.write_bytes(content)
                    continue
                data = target.read_bytes()
                originals.setdefault(target, data)
                current = target.read_bytes()
                old = e["old"].encode("utf-8")
                if current.count(old) != 1:
                    problem = "%s: old text occurs %d times" % (e["path"], current.count(old))
                    break
                target.write_bytes(current.replace(old, e["new"].encode("utf-8"), 1))
            if problem:
                row.update({"result": "SPEC-ERROR", "detail": problem})
            else:
                rc, text, ran, ids = run_suite(tree, mutant["suite"], args.timeout)
                (out / ("mut_%s.log" % mutant["id"])).write_text(text, encoding="utf-8")
                row.update({"rc": rc, "ran": ran, "failing_ids": ids, "tail": text.strip().splitlines()[-3:]})
                if mutant["kind"] == "draft-claim":
                    row["result"] = "PASSES" if rc == 0 else "FAILS"
                elif mutant["kind"] == "harness":
                    row["result"] = "test fails (sound)" if rc != 0 else "TEST STILL PASSES (vacuous?)"
                else:
                    row["result"] = "killed" if rc != 0 else "SURVIVED"
                if mutant.get("expect_pass"):
                    row["expect_pass"] = {name: (name + " (") in text and not any(name in failing for failing in ids) for name in mutant["expect_pass"]}
        finally:
            for target, data in originals.items():
                target.write_bytes(data)
            for target in created:
                if target.exists():
                    target.unlink()
        after = {path: sha256_of(tree / path) for path in touched}
        row["restored"] = after == before
        results["mutants"].append(row)
        print("%-4s %-13s %-28s restored=%s %s | %s" % (row["id"], row["kind"], row.get("result"), row["restored"], mutant["suite"].rsplit("/", 1)[-1][:60], "; ".join(row.get("failing_ids", [])[:3])[:230] or row.get("detail", "")), flush=True)
        with open(out / "results.json", "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=1)
            fh.write("\n")
        if not row["restored"]:
            with open(args.progress, "a", encoding="utf-8") as fh:
                fh.write("%s MUTATION RUN STOPPED: after %s a hash differs: %s\n" % (stamp(), row["id"], json.dumps(after, sort_keys=True)))
            return 3

    after = {path: sha256_of(tree / path) for path in touched}
    with open(out / "results.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
        fh.write("\n")
    with open(args.progress, "a", encoding="utf-8") as fh:
        fh.write("%s MUTATION RUN END: %d mutants; every touched file restored=%s (sha256 after == before); results %s\n" % (stamp(), len(chosen), after == before, out / "results.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
