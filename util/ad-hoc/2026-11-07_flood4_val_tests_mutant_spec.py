"""
Write the validator's own mutant spec for the flood-4 tests carrier, slice B (the 15 tests/ suites).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 tests carrier, slice B)
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 carrier validation (BRIEF_VALIDATE.txt); consumed by 2026-11-07_flood4_val_tests_mutants.py

Usage: python3 <this> <out spec.json>

Every mutant here differs from the builder's recorded one for the same suite (manifest.json "mutations"); boundary
suites get one mutant per direction where that is one line. "probe" entries record an outcome instead of requiring a kill.
"""

import json
import sys

WTC = "tests.test_wake_the_claude.WakeTheClaudeSecurityTests."
CIL = "tests.test_claude_interactive.ClaudeInteractiveLauncherRuntimeTests."
PLOT = "tests.test_run_experiment.PlotRendererUnitTest."


def m(mid, target, old, new, test_file, expect, run=None, kind="mutant"):
    entry = {"id": mid, "target": target, "old": old, "new": new, "test_file": test_file, "expect": expect, "kind": kind}
    if run:
        entry["run"] = run
    return entry


SPEC = [
    # tests/test_agents_md_touch_up.py -- builder: three-dot -> two-dot
    m("MA1", ".github/workflows/agents-md-touch-up.yml", "            | head -1 \\", "            | tail -1 \\", "tests/test_agents_md_touch_up.py", ["test_only_the_first_header_line_is_the_value"]),
    m("MA2", ".github/workflows/agents-md-touch-up.yml", "            | tr -d '[:space:]')", "            | cat)", "tests/test_agents_md_touch_up.py", ["test_surrounding_whitespace_still_parses"]),
    m("MA3", ".github/workflows/agents-md-touch-up.yml", "          set -euo pipefail", "          set -eo pipefail", "tests/test_agents_md_touch_up.py", ["test_unset_base_sha_on_the_diff_path_is_unbound"]),
    # tests/test_claude_agent_guard_brace_cap.py -- builder: numeric range slice cap - 1
    m("MB1", "util/claude_agent_guard.py", "    return _unique([text] + done + pending)[: limit + 1]", "    return _unique([text] + done + pending)[: limit]", "tests/test_claude_agent_guard_brace_cap.py", ["test_last_slot_of_a_full_list_assembles_ssh_and_is_denied"]),
    m("MB2", "util/claude_agent_guard.py", "    return _unique([text] + done + pending)[: limit + 1]", "    return _unique([text] + done + pending)[: limit + 2]", "tests/test_claude_agent_guard_brace_cap.py", ["test_one_past_the_cap_drops_the_assembled_ssh_name"]),
    m("MB3", "util/claude_agent_guard.py", "    return [str(v) for v in range(a, b + step, step)[:MAX_BRACE_ALTERNATIVES]]  # range slices lazily", "    return [str(v) for v in range(a, b + step, step)[:MAX_BRACE_ALTERNATIVES + 1]]  # range slices lazily", "tests/test_claude_agent_guard_brace_cap.py", ["test_numeric_range_one_past_the_cap_drops_the_far_end"]),
    # tests/test_claude_interactive.py -- builder: resume branch shift 2
    m("MC1", "scripts/claude_interactive.bash", 'export SCRIPT_VERSION="0.2.0"', 'export SCRIPT_VERSION="${SCRIPT_VERSION:-0.2.0}"', "tests/test_claude_interactive.py", ["test_script_version_ignores_an_inherited_script_version_and_does_not_launch"], run=[CIL + "test_script_version_ignores_an_inherited_script_version_and_does_not_launch"]),
    m("MC2", "scripts/claude_interactive.bash", '"--remote-control-session" | "--remote-control" | "-rc") CLAUDE_REMOTE_CONTROL="${TRUE}" && shift ;;', '"--remote-control-session" | "--remote-control" | "-rc") CLAUDE_REMOTE_CONTROL="${TRUE}" && shift 2 ;;', "tests/test_claude_interactive.py", ["test_boolean_flags_do_not_consume_the_following_prompt"], run=[CIL + "test_boolean_flags_do_not_consume_the_following_prompt"]),
    m("MC3", "scripts/claude_interactive.bash", '(( ${#CLAUDE_ARGS[@]} > 0 )) && CLAUDE_ARGS+=("${CLAUDE_SEPERATOR_FLAG}")', 'CLAUDE_ARGS+=("${CLAUDE_SEPERATOR_FLAG}")', "tests/test_claude_interactive.py", ["test_boolean_false_omits_the_option_instead_of_substituting_the_default"], run=[CIL + "test_boolean_false_omits_the_option_instead_of_substituting_the_default"]),
    m("MC4", "scripts/claude_interactive.bash", '        "--help" | "-h" | "-?") usage 0 ;;', '        "-h" | "-?") usage 0 ;;', "tests/test_claude_interactive.py", ["test_help_flags_print_usage_and_do_not_launch"], run=[CIL + "test_help_flags_print_usage_and_do_not_launch"]),
    # tests/test_duplicati_wrapper_contract.py -- builder: Restart=no -> on-failure
    m("MD1", "util/ad-hoc/2026-10-29_duplicati-trial-override.conf", "\nSystemCallErrorNumber=\n", "\n#SystemCallErrorNumber=\n", "tests/test_duplicati_wrapper_contract.py", ["test_the_trial_replaces_the_live_inputs_and_keeps_the_units_confinement", "test_the_dropin_assigns_only_the_documented_keys"], run=["tests.test_duplicati_wrapper_contract.TrialDropInMerge"]),
    m("MD2", "util/ad-hoc/2026-10-29_duplicati-trial-override.conf", "\nExecStart=\nExecStart=/usr/local/lib/duplicati-trial/", "\nExecStart=/usr/local/lib/duplicati-trial/", "tests/test_duplicati_wrapper_contract.py", ["test_the_trial_replaces_the_live_inputs_and_keeps_the_units_confinement"], run=["tests.test_duplicati_wrapper_contract.TrialDropInMerge"]),
    # tests/test_host_state_check.py -- builder: blocks_all = True
    m("MH1", "util/host_state_check.py", '        blockall = stdout_of(get_capture(sec, "blockall", "socketfilterfw --getblockall"), "socketfilterfw --getblockall")', '        blockall = stdout_of(get_capture(sec, "firewall", "socketfilterfw --getglobalstate"), "socketfilterfw --getblockall")', "tests/test_host_state_check.py", ["test_state_2_global_line_is_not_the_block_all_capture"]),
    m("MH2", "util/host_state_check.py", "    if int(state) >= 1:\n        if blocks_all:", "    if int(state) >= 0:\n        if blocks_all:", "tests/test_host_state_check.py", ["test_a_disabled_firewall_fails_even_when_block_all_reads_on"]),
    m("MH3", "util/host_state_check.py", '    raise DataError(f"socketfilterfw --getblockall: no block-all state in {first_line(text)!r}")', '    return "block all" in text', "tests/test_host_state_check.py", ["test_unknown_and_undefined_block_all_cannot_pass_an_enabled_firewall"]),
    # tests/test_host_state_gate_boundaries.py -- builder: <= -> < on the skew
    m("MG1", "util/host_state_check.py", "    if abs(gap) <= skew:", "    if abs(gap) <= skew + 1:", "tests/test_host_state_gate_boundaries.py", ["test_one_minor_past_the_allowance_fails_either_way", "test_a_zero_skew_admits_only_the_cluster_minor"]),
    m("MG2", "util/host_state_check.py", '    if rec["mbps"] < floor:', '    if rec["mbps"] <= floor:', "tests/test_host_state_gate_boundaries.py", ["test_a_measurement_equal_to_the_floor_passes_and_one_below_fails"]),
    m("MG3", "util/host_state_check.py", '    if rec["mbps"] < floor:', '    if rec["mbps"] < floor - 1:', "tests/test_host_state_gate_boundaries.py", ["test_a_measurement_equal_to_the_floor_passes_and_one_below_fails"]),
    # tests/test_per_run_timeout_boundary.py -- builder: > -> >=
    m("MP1", "util/experiments/run_suite.py", "if not timeout > sum(terms.values())}", "if not timeout > sum(terms.values()) + 1}", "tests/test_per_run_timeout_boundary.py", ["test_a_timeout_one_second_above_the_largest_budget_is_admitted"]),
    m("MP2", "util/experiments/run_suite.py", "    cell_id = max(short, key=lambda key: sum(short[key].values()))", "    cell_id = max(reversed(list(short)), key=lambda key: sum(short[key].values()))", "tests/test_per_run_timeout_boundary.py", ["test_cells_tied_for_the_largest_sum_are_all_counted_and_the_first_is_named"]),
    # tests/test_recurrence_operation_identity_and_dataset_budget.py -- builder: save_ok = True
    m("MR1", "util/experiments/run_experiment.py", '        if size != snapshot.get("size_bytes"):', '        if size != snapshot.get("size_bytes", size):', "tests/test_recurrence_operation_identity_and_dataset_budget.py", ["test_a_snapshot_without_size_bytes_is_not_vouched_for"]),
    m("MR2", "util/experiments/run_experiment.py", "            out_path.unlink(missing_ok=True)\n        return result\n    result.update(ok=True", "            out_path.exists()\n        return result\n    result.update(ok=True", "tests/test_recurrence_operation_identity_and_dataset_budget.py", ["test_a_failed_copy_removes_the_partial_model_and_does_not_refit", "test_a_snapshot_without_size_bytes_is_not_vouched_for"]),
    m("MR3", "util/experiments/run_experiment.py", '    except ServiceUnreachable as exc:\n        result["error"] = str(exc)\n        return result\n    if code != 201:', '    except RequestTimeout as exc:\n        result["error"] = str(exc)\n        return result\n    if code != 201:', "tests/test_recurrence_operation_identity_and_dataset_budget.py", ["test_a_dropped_snapshot_save_stays_a_failed_phase"]),
    # tests/test_release_train_exact_caps.py -- builder: ceremony encoded_len > cap -> >=
    m("MT1", "util/release_train/propose.py", "    return body if _body_size(body) <= PR_BODY_MAX else _pr_body(prop, date, inline_notes=False)", "    return body if _body_size(body) < PR_BODY_MAX else _pr_body(prop, date, inline_notes=False)", "tests/test_release_train_exact_caps.py", ["test_a_body_that_exactly_fills_the_limit_keeps_the_notes"]),
    m("MT2", "util/release_train/propose.py", "    if _body_size(prop.pr_body) > PR_BODY_MAX:  # refuse BEFORE", "    if _body_size(prop.pr_body) >= PR_BODY_MAX:  # refuse BEFORE", "tests/test_release_train_exact_caps.py", ["test_execute_opens_a_body_that_exactly_fills_the_limit"]),
    m("MT3", "util/release_train/ceremony.py", "        if encoded_len > cap:", "        if encoded_len > cap + 1:", "tests/test_release_train_exact_caps.py", ["test_an_archive_that_exactly_fills_the_cap_is_planned_and_one_byte_over_halts"]),
    # tests/test_run_experiment.py -- builder: numeric-type str admitted
    m("ME1", "util/experiments/plots_cascor.py", '        if not isinstance(block, Mapping) or "split" not in block or block.get("absent"):', '        if not isinstance(block, Mapping) or block.get("absent"):', "tests/test_run_experiment.py", ["test_a_schema_1_cascor_block_is_not_drawn_as_the_run_eval_scalars", "test_unlabelled_numbers_beside_a_real_in_loop_block_stay_off_the_bars"], run=[PLOT + "test_a_schema_1_cascor_block_is_not_drawn_as_the_run_eval_scalars", PLOT + "test_unlabelled_numbers_beside_a_real_in_loop_block_stay_off_the_bars", PLOT + "test_an_absent_block_keeps_stale_numbers_off_the_bars", PLOT + "test_a_numeric_string_is_not_a_bar"]),
    m("ME2", "util/experiments/plots_cascor.py", '        if not isinstance(block, Mapping) or "split" not in block or block.get("absent"):', '        if not isinstance(block, Mapping) or "split" not in block:', "tests/test_run_experiment.py", ["test_an_absent_block_keeps_stale_numbers_off_the_bars"], run=[PLOT + "test_a_schema_1_cascor_block_is_not_drawn_as_the_run_eval_scalars", PLOT + "test_unlabelled_numbers_beside_a_real_in_loop_block_stay_off_the_bars", PLOT + "test_an_absent_block_keeps_stale_numbers_off_the_bars", PLOT + "test_a_numeric_string_is_not_a_bar"]),
    # tests/test_run_suite.py -- builder: _read_stats returns any JSON value
    m("MS1", "util/experiments/run_suite.py", "    if stats is not None:\n        return _stats_headline(stats, Path(run_dir))", "    if stats:\n        return _stats_headline(stats, Path(run_dir))", "tests/test_run_suite.py", ["test_an_empty_object_is_a_readable_file_with_no_headline"]),
    # tests/test_stats_summary_eval_blocks.py -- builder: bool exclusion dropped
    m("MSE1", "util/experiments/stats_summary.py", '        if value is not None:\n            lines.append(f"- {name}: {_fmt(value)}")', '        if value:\n            lines.append(f"- {name}: {_fmt(value)}")', "tests/test_stats_summary_eval_blocks.py", ["test_a_zero_accuracy_is_reported_not_omitted"]),
    m("MSE2", "util/experiments/plots_cascor.py", "isinstance(block.get(name), (int, float)) and not isinstance(block.get(name), bool)}", "isinstance(block.get(name), (int, float)) and not isinstance(block.get(name), bool) and bool(block.get(name))}", "tests/test_stats_summary_eval_blocks.py", ["test_a_zero_score_is_a_bar_and_false_is_not"]),
    # tests/test_stats_summary_render.py -- builder: train theta truthiness
    m("MSR1", "util/experiments/stats_summary.py", '    if service.get("default_theta") is not None:', '    if service.get("default_theta"):', "tests/test_stats_summary_render.py", ["test_a_zero_theta_is_a_value"]),
    # tests/test_subpackage_py_typed.py -- builder: packages.find include renamed
    m("MPT1", "juniper-config-tools/pyproject.toml", 'include = ["juniper_config_tools*"]', 'include = ["juniper_config_tools*", "tests*"]', "tests/test_subpackage_py_typed.py", ["test_every_built_wheel_ships_py_typed"]),
    m("MPT2", "juniper-config-tools/pyproject.toml", 'juniper_config_tools = ["py.typed"]', "juniper_config_tools = []", "tests/test_subpackage_py_typed.py", [], kind="probe"),
    # tests/test_wake_the_claude.py -- builder: EFFORT_DEFAULT auto -> max
    m("MW1", "scripts/wake_the_claude.bash", "            shift  # shift to consume the worktree boolean true value", "            :  # shift to consume the worktree boolean true value", "tests/test_wake_the_claude.py", ["test_worktree_boolean_values_omit_or_let_claude_name"], run=[WTC + "test_worktree_boolean_values_omit_or_let_claude_name"]),
    m("MW2", "scripts/wake_the_claude.bash", 'REMOTE_CONTROL_FLAGS="-c | --remote | --control | ${CLAUDE_REMOTE_CONTROL_FLAGS}"', 'REMOTE_CONTROL_FLAGS="-c | --remote | --control | ${CLAUDE_REMOTE_CONTROL_FLAGS} | --remote-controls"', "tests/test_wake_the_claude.py", ["test_remote_control_aliases_forward_canonical_flag_without_consuming_the_next"], run=[WTC + "test_remote_control_aliases_forward_canonical_flag_without_consuming_the_next"]),
    m("MW3", "scripts/wake_the_claude.bash", '            CLAUDE_EFFORT_VALUE=("${CLAUDE_EFFORT_FLAGS}" "${EFFORT_DEFAULT}") && shift  # shift to consume the effort boolean true value', "            CLAUDE_EFFORT_VALUE=() && shift  # shift to consume the effort boolean true value", "tests/test_wake_the_claude.py", ["test_effort_boolean_values_omit_or_default_the_effort"], run=[WTC + "test_effort_boolean_values_omit_or_default_the_effort"]),
    m("MW4", "scripts/wake_the_claude.bash", 'debug_log "Error: Received Effort Flag but no valid Effort Value. Exiting..."\n            CLAUDE_EFFORT_VALUE=()\n            result_value="${FALSE}"', 'debug_log "Error: Received Effort Flag but no valid Effort Value. Exiting..."\n            CLAUDE_EFFORT_VALUE=()\n            result_value="${TRUE}"', "tests/test_wake_the_claude.py", ["test_missing_effort_value_fails_without_invoking_claude"], run=[WTC + "test_missing_effort_value_fails_without_invoking_claude"]),
    m("MW5", "scripts/wake_the_claude.bash", 'PERMISSIONS_FLAGS="-s | --skip | --skip-permissions | ${CLAUDE_PERMISSIONS_FLAGS}"', 'PERMISSIONS_FLAGS="-s | --skip | --skip-permissions | ${CLAUDE_PERMISSIONS_FLAGS} | --dangerously-skip-permission"', "tests/test_wake_the_claude.py", ["test_permission_aliases_forward_canonical_flag_without_consuming_the_next"], run=[WTC + "test_permission_aliases_forward_canonical_flag_without_consuming_the_next"]),
]


def main() -> int:
    with open(sys.argv[1], "w", encoding="utf-8") as fh:
        json.dump(SPEC, fh, indent=1)
    print(f"{len(SPEC)} entries -> {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
