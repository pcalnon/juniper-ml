#!/usr/bin/env python3
"""
Show that the juniper-ml#2064 tests kill a mutant for each defect class the change closes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-27
Status: ad-hoc — investigation (suite strength evidence for the juniper-ml#2064 held-out eval-scalars PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/experiments/stats_summary.py; util/experiments/plots_cascor.py; util/experiments/run_experiment.py;
         util/experiments/run_suite.py; tests/test_stats_summary_eval_blocks.py; tests/test_run_suite.py;
         tests/test_run_suite_acceptance.py; tests/test_run_experiment.py;
         util/ad-hoc/2026-10-26_apd_ml_002_mutation_check.py (whose shape this follows)

juniper-ml#2064 makes a cascor run's eval scalars cascor's FINAL evaluation (``eval_metrics.final``), labelled,
in stats.json / summary.md / eval_metrics.png, keeps the in-loop values beside them under their own label, and
gives ``run_suite`` the held-out ``test_*`` columns only from a final evaluation of the TEST split. Each mutant
re-breaks one of those, in one of the four changed modules:

- ``stats_summary.py`` (the derivation and summary.md): the final block filled from the in-loop fields, or
  falling back to them when there is no final block; the split, n or held-out label lost or wrong; the
  disabled / pre-switch reasons wrong; accuracy or cascor's undefined reasons dropped; the in-loop block
  unlabelled or called held out; summary.md's heading, reason or no-number rule broken; build_stats back on
  the unlabelled shape; the schema not bumped; a ``/1`` block taken for a labelled one;
- ``plots_cascor.py``: the two series swapped or unlabelled, the no-final subtitle silent, the legend caption
  drifting from summary.md's, nothing-to-draw not refused, a bool drawn as a score;
- ``run_experiment.py``: the plot handed the raw ``/v1/metrics`` body again;
- ``run_suite.py``: a validation block filling ``test_*``, the columns read from the in-loop block, no
  re-derivation for a ``/1`` stats.json (or none through ``_row_metrics``, which ``--reaggregate`` uses),
  ``metrics_final.json`` overruling a labelled stats.json, ``--reaggregate`` writing the derived block back
  into stats.json, the columns not bandable, ``test_accuracy`` pending again, a bool or null becoming a
  column, and the pending-metric warning (still pinned, now on a stand-in name) gone.

Each mutant edits a COPY of its module in a scratch tree that mirrors the repo layout, and the suites that pin
that module run against the copy. A mutant is KILLED when those suites fail, and it must also be killed by
its own pin test run alone. The unmutated control must pass, or the run is void. Nothing in the repository is
modified -- the four modules are hashed before and after to show it -- and the scratch tree lives under
``$TMPDIR``. This is evidence, not a CI gate.

Exit codes:

- 0: every mutant killed, by the suites and by its pin, and the repository modules unchanged;
- 1: a mutant survived, a pin missed, the control failed, or a module changed;
- 2: an anchor was not found exactly once, or ``--only`` matched nothing.

Usage:
    python3 util/ad-hoc/2026-10-27_issue_2064_eval_blocks_mutation_check.py [--only ID ...]

``--only`` runs just the named mutants (after the control); a recorded result is always a full run.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess  # nosec B404 - runs the unittest suites on a scratch copy
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STATS = "util/experiments/stats_summary.py"
PLOTS = "util/experiments/plots_cascor.py"
DRIVER = "util/experiments/run_experiment.py"
SUITE = "util/experiments/run_suite.py"
# `util/experiment_stack.bash` is read, never run: test_run_suite.py checks the launcher's accepted timeout form against it.
STAGED_FILES = ("tests/test_stats_summary_eval_blocks.py", "tests/test_run_suite.py", "tests/test_run_suite_acceptance.py", "tests/test_run_experiment.py", "tests/cascor_eval_fixtures.py", "tests/redacted_env.py", "util/experiment_stack.bash")

BLOCKS = "tests.test_stats_summary_eval_blocks.CascorEvalBlocksTest"
BUILD = "tests.test_stats_summary_eval_blocks.BuildStatsEvalBlocksTest"
SUMMARY = "tests.test_stats_summary_eval_blocks.SummaryMdEvalBlocksTest"
PLOT = "tests.test_stats_summary_eval_blocks.EvalMetricsPlotTest"
E2E = "tests.test_run_experiment.EvalScalarsEndToEndTest"
COLUMNS = "tests.test_run_suite.CascorHeldOutColumnsTest"
BANDS = "tests.test_run_suite_acceptance.CascorBandMetricsTest"

# The driver classes that load stats_summary / plots_cascor, rather than all ~3 minutes of test_run_experiment.py.
DRIVER_CLASSES = ("tests.test_run_experiment.EvalScalarsEndToEndTest", "tests.test_run_experiment.HappyPathTest", "tests.test_run_experiment.CascorPlotsTest", "tests.test_run_experiment.PlotRendererUnitTest", "tests.test_run_experiment.StatsSummaryUnitTest")
SUITES_FOR = {
    STATS: ("tests/test_stats_summary_eval_blocks.py", "tests/test_run_suite.py", "tests/test_run_suite_acceptance.py", *DRIVER_CLASSES),
    PLOTS: ("tests/test_stats_summary_eval_blocks.py", *DRIVER_CLASSES),
    DRIVER: DRIVER_CLASSES,
    SUITE: ("tests/test_run_suite.py", "tests/test_run_suite_acceptance.py"),
}

HELD_LINE = '    held = _labelled_eval_block(CASCOR_FINAL_EVAL_BASIS, CASCOR_FINAL_EVAL_METRICS, final, final, isinstance(final, Mapping) and final.get("split") == "test", absent)\n'
IN_LOOP_TAIL = "live if in_loop_absent is None else None, False, in_loop_absent)\n"
DERIVE_LINE = '    return ss.cascor_eval_blocks(body)["eval_scalars"] if body is not None else None\n'
WRITE_BACK = (
    '    derived = ss.cascor_eval_blocks(body)["eval_scalars"] if body is not None else None\n'
    "    if derived is not None and run_dir is not None:\n"
    '        (run_dir / "artifacts" / "results" / "stats.json").write_text(json.dumps({**stats, "cascor": {**cascor, "eval_scalars": derived}}))\n'
    "    return derived\n"
)
EARLY_WARNING = '    # APD-ML-002 ruling 2: a band on a metric nothing produces yet is legal, and says so before any launch.\n    for warning in pending_band_warnings(cells):\n        print(f"[suite] warning: {warning}", file=sys.stderr)\n'

# (id, module, defect, pin test, [(anchor, replacement)]) -- every anchor must occur exactly once in its module.
MUTANTS = [
    ("S01", STATS, "the final block's values taken from the top-level in-loop fields", f"{BLOCKS}.test_a_test_split_final_evaluation_is_the_eval_scalars_and_the_in_loop_values_keep_their_own_label", [(HELD_LINE, HELD_LINE.replace("METRICS, final, final,", "METRICS, body, final,"))]),
    ("S02", STATS, "no final block falls back, silently, to the in-loop values", f"{BLOCKS}.test_no_final_key_says_the_service_predates_it_and_borrows_no_in_loop_value", [(HELD_LINE, HELD_LINE.replace("METRICS, final, final,", "METRICS, final if absent is None else body, final,"))]),
    ("S03", STATS, "the split label dropped", f"{BLOCKS}.test_a_test_split_final_evaluation_is_the_eval_scalars_and_the_in_loop_values_keep_their_own_label", [('"split": meta.get("split")', '"split": None')]),
    ("S04", STATS, "the final block labelled with the in-loop split and n", f"{BLOCKS}.test_a_test_split_final_evaluation_is_the_eval_scalars_and_the_in_loop_values_keep_their_own_label", [(HELD_LINE, HELD_LINE.replace("METRICS, final, final,", "METRICS, final, live,"))]),
    ("S05", STATS, "a validation final block called held out", f"{BLOCKS}.test_a_validation_split_final_evaluation_is_not_held_out", [(HELD_LINE, HELD_LINE.replace(' and final.get("split") == "test", absent)', ", absent)"))]),
    ("S06", STATS, "disabled eval metrics reported as a null final", f"{BLOCKS}.test_every_other_way_of_having_no_final_evaluation_says_why", [('    if live.get("enabled") is False:\n        return "eval metrics disabled (JUNIPER_CASCOR_EVAL_METRICS_ENABLED)"\n', "")]),
    ("S07", STATS, "a service before the switch reported as a null final", f"{BLOCKS}.test_no_final_key_says_the_service_predates_it_and_borrows_no_in_loop_value", [('    if "final" not in live:\n', "    if False:\n")]),
    ("S08", STATS, "the in-loop block loses its split and n", f"{BLOCKS}.test_a_test_split_final_evaluation_is_the_eval_scalars_and_the_in_loop_values_keep_their_own_label", [(IN_LOOP_TAIL, "None, False, in_loop_absent)\n")]),
    ("S09", STATS, "the in-loop block called held out", f"{BLOCKS}.test_both_blocks_always_carry_the_same_keys_and_the_input_is_not_mutated", [(IN_LOOP_TAIL, "live if in_loop_absent is None else None, True, in_loop_absent)\n")]),
    ("S10", STATS, "accuracy (juniper-cascor#731) dropped from the final block", f"{BLOCKS}.test_the_accuracy_from_juniper_cascor_731_is_carried_and_an_undefined_one_keeps_its_reason", [('CASCOR_FINAL_EVAL_METRICS = ("accuracy", "f1", "precision", "recall", "roc_auc")', 'CASCOR_FINAL_EVAL_METRICS = ("f1", "precision", "recall", "roc_auc")')]),
    ("S11", STATS, "cascor's undefined reasons dropped", f"{BLOCKS}.test_the_accuracy_from_juniper_cascor_731_is_carried_and_an_undefined_one_keeps_its_reason", [('"undefined": dict(undefined) if isinstance(undefined, Mapping) else {}', '"undefined": {}')]),
    ("S12", STATS, "a disabled service's in-loop block not marked disabled", f"{BLOCKS}.test_every_other_way_of_having_no_final_evaluation_says_why", [('    elif live is not None and live.get("enabled") is False:\n', "    elif False:\n")]),
    ("S13", STATS, "summary.md's eval-scalars heading names no split, n or held-out status", f"{SUMMARY}.test_a_held_out_run_reports_the_final_evaluation_then_the_in_loop_values", [("f\"### Eval scalars ({'final evaluation: ' if is_labelled_eval_block(held) else ''}{eval_caption(held)})\"", '"### Eval scalars"')]),
    ("S14", STATS, "summary.md drops the reason there is no final evaluation", f"{SUMMARY}.test_no_final_evaluation_prints_the_reason_and_no_number", [("        return [f\"(none: {block['absent']}{absent_rider})\"]\n", '        return ["(none)"]\n')]),
    ("S15", STATS, "summary.md prints metric lines under an absent final block", f"{SUMMARY}.test_no_final_evaluation_prints_the_reason_and_no_number", [('    if block.get("absent"):\n        return [f"(none: ', '    if False:\n        return [f"(none: ')]),
    ("S16", STATS, "the caption calls any labelled split held out", f"{SUMMARY}.test_a_validation_split_final_evaluation_is_headed_not_held_out", [('    if block.get("held_out"):\n        status = "held out"\n', '    if block.get("split"):\n        status = "held out"\n')]),
    ("S17", STATS, "build_stats back on the unlabelled /1 eval_scalars", f"{BUILD}.test_the_cascor_block_carries_both_labelled_blocks_under_schema_2", [("            **cascor_eval_blocks(metrics_final),\n", '            "eval_scalars": {name: final.get(name) for name in ("f1", "precision", "recall", "roc_auc")},\n')]),
    ("S18", STATS, "the schema not bumped at the boundary", f"{BUILD}.test_the_cascor_block_carries_both_labelled_blocks_under_schema_2", [('STATS_SCHEMA = "juniper-experiment-stats/2"', 'STATS_SCHEMA = "juniper-experiment-stats/1"')]),
    ("S19", STATS, "a /1 eval_scalars block taken for a labelled one", f"{BLOCKS}.test_is_labelled_eval_block_tells_a_v2_block_from_a_v1_one", [('    return isinstance(block, Mapping) and "split" in block and "absent" in block\n', "    return isinstance(block, Mapping)\n")]),
    ("P01", PLOTS, "the in-loop series drawn as the final evaluation (series swapped)", f"{PLOT}.test_the_series_are_the_two_labelled_blocks", [("    for role, block in ((FINAL_EVAL_ROLE, final), (IN_LOOP_ROLE, in_loop)):\n", "    for role, block in ((FINAL_EVAL_ROLE, in_loop), (IN_LOOP_ROLE, final)):\n")]),
    ("P02", PLOTS, "a series labelled with its role alone (no split, n or held-out status)", f"{PLOT}.test_the_series_are_the_two_labelled_blocks", [('            series.append((role, f"{role}: {_eval_caption(block)}", values))\n', "            series.append((role, role, values))\n")]),
    ("P03", PLOTS, "the subtitle silent about a missing final evaluation", f"{PLOT}.test_with_no_final_evaluation_only_the_in_loop_bars_are_drawn_under_their_own_label", [('        subtitle = f"no final evaluation ({reason}): the in-loop bars are NOT the run\'s eval scalars"\n', '        subtitle = "eval scalars"\n')]),
    ("P04", PLOTS, "the legend caption drifting from summary.md's (any split held out)", f"{PLOT}.test_the_legend_caption_is_the_summary_md_caption", [('    if block.get("held_out"):\n', '    if block.get("split"):\n')]),
    ("P05", PLOTS, "nothing to draw not refused (a raw body reaches the renderer)", f"{PLOT}.test_nothing_to_draw_is_a_value_error_and_a_raw_body_is_never_drawn", [("    if not series:\n", "    if False:\n")]),
    ("P06", PLOTS, "a bool drawn as a score", f"{PLOT}.test_a_bool_or_a_null_is_no_bar", [(" and not isinstance(block.get(name), bool)}", "}")]),
    ("R01", DRIVER, "the eval_metrics plot handed the raw /v1/metrics body again", f"{E2E}.test_a_test_split_final_evaluation_is_the_runs_eval_scalars_in_all_three_outputs", [('plots.render_eval_metrics(eval_blocks, title, plots_dir / "eval_metrics.png")', 'plots.render_eval_metrics(metrics_final, title, plots_dir / "eval_metrics.png")')]),
    ("U01", SUITE, "a validation final block fills the test_* columns", f"{COLUMNS}.test_a_validation_split_final_evaluation_fills_no_test_column", [('    if not isinstance(block, dict) or block.get("split") != CASCOR_HELD_OUT_SPLIT:\n', "    if not isinstance(block, dict):\n")]),
    ("U02", SUITE, "the test_* columns read from the in-loop block", f"{COLUMNS}.test_a_test_split_final_evaluation_yields_every_test_column", [('    block = cascor.get("eval_scalars")\n', '    block = cascor.get("eval_scalars_in_loop")\n')]),
    ("U03", SUITE, "no re-derivation from metrics_final.json for a /1 stats.json", f"{COLUMNS}.test_a_schema_1_stats_json_re_derives_the_block_from_metrics_final_json", [(DERIVE_LINE, "    return None\n")]),
    ("U04", SUITE, "metrics_final.json overrules a labelled stats.json", f"{COLUMNS}.test_a_labelled_stats_json_is_never_overruled_by_metrics_final_json", [("    if ss.is_labelled_eval_block(block):\n        return block\n", "")]),
    ("U05", SUITE, "_row_metrics (what --reaggregate reads) skips the re-derivation", f"{COLUMNS}.test_row_metrics_re_derives_for_a_schema_1_row", [("        return _stats_headline(stats, Path(run_dir))\n", "        return _stats_headline(stats)\n")]),
    ("U06", SUITE, "--reaggregate writes the derived block back into stats.json", f"{COLUMNS}.test_reaggregate_backfills_a_schema_1_suite_and_rewrites_no_run_file", [(DERIVE_LINE, WRITE_BACK)]),
    ("U07", SUITE, "the test_* columns not accepted as band metrics", f"{BANDS}.test_acceptance_metrics_is_the_union_of_the_column_tables_plus_the_pending_names", [("RECURRENCE_HEADLINE_PATHS + CASCOR_HEADLINE_PATHS + CASCOR_TEST_COLUMNS)", "RECURRENCE_HEADLINE_PATHS + CASCOR_HEADLINE_PATHS)")]),
    ("U08", SUITE, "test_accuracy pending again (its warning back)", f"{BANDS}.test_a_band_on_test_accuracy_no_longer_warns", [('PENDING_ACCEPTANCE_METRICS: "dict[str, str]" = {}', 'PENDING_ACCEPTANCE_METRICS: "dict[str, str]" = {"test_accuracy": "pending"}')]),
    ("U09", SUITE, "a null or bool test value becomes a column", f"{COLUMNS}.test_undefined_bool_and_non_finite_test_values", [("CASCOR_TEST_COLUMNS if _is_metric(block.get(key))}", "CASCOR_TEST_COLUMNS if key in block}")]),
    ("U10", SUITE, "the pending-metric warning gone (the facility is still pinned)", f"{BANDS}.test_a_pending_name_warns_once_before_anything_launches", [(EARLY_WARNING, "")]),
]

FIRST_FAILURE = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+)\)", re.MULTILINE)
MODULES = (STATS, PLOTS, DRIVER, SUITE)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage(tmp: Path) -> None:
    shutil.copytree(REPO / "util" / "experiments", tmp / "util" / "experiments", ignore=shutil.ignore_patterns("__pycache__"))
    for rel in STAGED_FILES:
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest)


def run_tests(tmp: Path, targets: "list[str]") -> "tuple[bool, str]":
    proc = subprocess.run([sys.executable, "-m", "unittest", *targets], cwd=tmp, capture_output=True, text=True, timeout=1800, check=False)  # nosec B603
    match = FIRST_FAILURE.search(proc.stderr)
    first = f"{match.group(3).rsplit('.', 2)[-2]}.{match.group(2)}" if match else ("-" if proc.returncode == 0 else proc.stderr.strip().splitlines()[-1][:160])
    return proc.returncode == 0, first


def main(argv: "list[str]") -> int:
    only = set(argv[argv.index("--only") + 1 :]) if "--only" in argv else None
    mutants = [m for m in MUTANTS if only is None or m[0] in only]
    if not mutants:
        print(f"no mutant matches --only {sorted(only or [])}")
        return 2
    originals = {module: (REPO / module).read_text(encoding="utf-8") for module in MODULES}
    before = {module: _digest(REPO / module) for module in MODULES}
    for mid, module, _, _, edits in mutants:
        for anchor, _ in edits:
            if originals[module].count(anchor) != 1:
                print(f"ANCHOR {mid}: {anchor!r} occurs {originals[module].count(anchor)} times in {module} (need exactly 1)")
                return 2
    with tempfile.TemporaryDirectory(prefix="issue-2064-mutation-") as raw:
        tmp = Path(raw)
        stage(tmp)
        control = sorted({target for module in MODULES for target in SUITES_FOR[module]})
        passed, first = run_tests(tmp, control)
        if not passed:
            print(f"VOID     control: the suites fail on the unmutated source (first failure: {first})")
            return 1
        print(f"OK       control: {len(control)} suites / classes pass on the unmutated source", flush=True)
        survivors = pins_missed = 0
        for mid, module, defect, pin, edits in mutants:
            mutated = originals[module]
            for anchor, replacement in edits:
                mutated = mutated.replace(anchor, replacement)
            (tmp / module).write_text(mutated, encoding="utf-8")
            try:
                suites_passed, first = run_tests(tmp, list(SUITES_FOR[module]))
                pin_passed, _ = run_tests(tmp, [pin])
            finally:
                (tmp / module).write_text(originals[module], encoding="utf-8")
            survivors += 1 if suites_passed else 0
            pins_missed += 1 if pin_passed else 0
            print(f"{'SURVIVED' if suites_passed else 'KILLED':8} {mid} {Path(module).name}: {defect}\n                  first failure: {first}; {'PIN MISSED' if pin_passed else 'pin kills it'}: {pin.rsplit('.', 2)[-2]}.{pin.rsplit('.', 1)[-1]}", flush=True)
    after = {module: _digest(REPO / module) for module in MODULES}
    changed = [module for module in MODULES if after[module] != before[module]]
    for module in MODULES:
        print(f"sha256 {module}: {before[module][:16]} before, {after[module][:16]} after{' -- CHANGED' if module in changed else ''}")
    total = len(mutants)
    print(f"\n{total - survivors} of {total} mutants killed by the suites; {total - pins_missed} of {total} by their own pin test alone; repository modules {'CHANGED' if changed else 'byte-identical'}")
    return 0 if survivors == 0 and pins_missed == 0 and not changed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
