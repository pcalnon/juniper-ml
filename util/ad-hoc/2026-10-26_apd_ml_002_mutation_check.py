#!/usr/bin/env python3
"""
Show that the APD-ML-002 suites kill a mutant for each defect class the 2026-10-26 rulings close.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-26
Status: ad-hoc — investigation (suite strength evidence for the APD-ML-002 cascor-headline PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (§4.9, row APD-ML-002);
         util/experiments/run_suite.py; tests/test_run_suite.py; tests/test_run_suite_acceptance.py;
         util/ad-hoc/2026-10-25_turing_c9_guard_mutation_check.py (whose shape this follows)

The owner's four rulings of 2026-10-26 on APD-ML-002, and what each mutant re-breaks:

- ruling 1, the cascor columns: the reader back at the TOP of ``stats["cascor"]``, ``eval_scalars`` mapped,
  ``bool`` accepted, ``0.0`` dropped by truthiness, a non-finite accuracy dropped;
- ruling 2, the band names: ``final_accuracy`` re-admitted or refused without its reason, ``test_accuracy``
  dropped or fabricated from ``val_accuracy``, the pending warning missing or printed after the launches;
- ruling 3, ``--reaggregate``: the headline not re-read from stats.json, no fallback to the recorded
  metrics, the recorded value outranking the file, the registry appended to, the suite manifest
  rewritten, an incomplete cell re-run, the execution flags accepted, a suite id unresolved, a malformed
  manifest crashing, ``--compare-baseline`` ignored, ``--suite`` no longer required elsewhere;
- ruling 4, NaN / inf: compared like numbers, called absent, or ``isfinite`` applied to a huge int.

Each mutant edits a COPY of ``util/experiments/run_suite.py`` in a scratch tree that mirrors the repo
layout, and the three suites that pin it run against that copy. A mutant is KILLED when the suites fail,
and it must also be killed by its own pin test run alone. The unmutated control must pass, or the run is
void. Nothing in the repository is modified; the scratch tree lives under ``$TMPDIR``. This is evidence,
not a CI gate.

Exit codes:

- 0: every mutant killed, by the suites and by its pin;
- 1: a mutant survived, or the control failed;
- 2: an anchor was not found exactly once.

Usage:
    python3 util/ad-hoc/2026-10-26_apd_ml_002_mutation_check.py [--only ID ...]

``--only`` runs just the named mutants (after the control); a recorded result is always a full run.
"""

from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404 - runs the unittest suites on a scratch copy
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET = "util/experiments/run_suite.py"
SUITES = ("tests/test_run_suite.py", "tests/test_run_suite_acceptance.py", "tests/test_recurrence_degraded_phase_edges.py")
# `util/experiment_stack.bash` is read, never run: test_run_suite.py checks the launcher's accepted timeout form against it.
STAGED_FILES = SUITES + ("tests/redacted_env.py", "util/experiment_stack.bash")

HEADLINE = "tests.test_run_suite.CascorHeadlineMetricsTest"
ROWS = "tests.test_run_suite.RowMetricsTest"
REAGG = "tests.test_run_suite.ReaggregateTest"
BANDS = "tests.test_run_suite_acceptance.CascorBandMetricsTest"
NONFINITE = "tests.test_run_suite_acceptance.NonFiniteBandValueTest"
LOOP = "tests.test_run_suite_acceptance.CascorSuiteLoopAcceptanceTest"

CASCOR_PATHS = '    ("train_accuracy", ("final", "train_accuracy")),\n    ("val_accuracy", ("final", "val_accuracy")),\n)'
METRICS_LINE = "ACCEPTANCE_METRICS = frozenset(column for column, _ in RECURRENCE_HEADLINE_PATHS + CASCOR_HEADLINE_PATHS) | frozenset(PENDING_ACCEPTANCE_METRICS)\n"
EARLY_WARNING = '    # APD-ML-002 ruling 2: a band on a metric nothing produces yet is legal, and says so before any launch.\n    for warning in pending_band_warnings(cells):\n        print(f"[suite] warning: {warning}", file=sys.stderr)\n'
EARLY_WARNING_GONE = "    # APD-ML-002 ruling 2: a band on a metric nothing produces yet is legal, and says so before any launch.\n"
LATE_ANCHOR = '    comparison = _run_comparison(args.compare_baseline, suite_dir) if getattr(args, "compare_baseline", None) else None\n'
LATE_WARNING = '    for warning in pending_band_warnings(cells):\n        print(f"[suite] warning: {warning}", file=sys.stderr)\n' + LATE_ANCHOR
NONFINITE_BRANCH = '        elif isinstance(value, float) and not math.isfinite(value):\n            result = "fail"\n'
REAGG_TAIL = "    comparison = _run_comparison(compare_baseline, suite_dir) if compare_baseline else None\n    return aggregate(suite_dir, suite, cells, comparison=comparison)\n"
REAGG_COMPARISON = "    comparison = _run_comparison(compare_baseline, suite_dir) if compare_baseline else None\n"
RERUN = (
    "    registry = _read_registry(suite_dir)\n"
    "    for cell in cells:\n"
    '        if registry.get(cell["cell_id"], {}).get("outcome") not in COMPLETE_OUTCOMES:\n'
    '            execute_cell(cell, suite_dir / "cells" / cell["cell_id"] / "experiment.yaml", suite.get("app", "cascor"), 3600.0, DEFAULT_LAUNCHER, DEFAULT_DRIVER, sys.executable)\n'
)

# (id, defect, pin test, [(anchor, replacement)]) -- every anchor must occur exactly once in TARGET.
MUTANTS = [
    ("M01", "the cascor reader back at the TOP of stats['cascor'] (the pre-fix shape)", f"{HEADLINE}.test_the_writer_shape_yields_exactly_train_and_val_accuracy", [(CASCOR_PATHS, '    ("train_accuracy", ("train_accuracy",)),\n    ("val_accuracy", ("val_accuracy",)),\n)')]),
    ("M02", "eval_scalars mapped as a headline (f1)", f"{HEADLINE}.test_the_writer_shape_yields_exactly_train_and_val_accuracy", [(CASCOR_PATHS, CASCOR_PATHS[:-1] + '    ("f1", ("eval_scalars", "f1")),\n)')]),
    ("M03", "bool accepted as a metric", f"{HEADLINE}.test_bool_none_and_strings_are_dropped", [("    return isinstance(value, (int, float)) and not isinstance(value, bool)\n", "    return isinstance(value, (int, float))\n")]),
    ("M04", "truthiness: a 0.0 accuracy dropped", f"{HEADLINE}.test_a_zero_accuracy_is_kept", [("            if _is_metric(value):\n", "            if _is_metric(value) and value:\n")]),
    ("M05", "a non-finite accuracy dropped by the reader (a band would read absent)", f"{HEADLINE}.test_a_non_finite_accuracy_is_kept_as_a_value", [("            if _is_metric(value):\n", "            if _is_metric(value) and math.isfinite(value):\n")]),
    ("M06", "final_accuracy re-admitted as a band metric", f"{BANDS}.test_final_accuracy_is_refused_with_its_reason_and_a_suite_naming_it_exits_two", [(METRICS_LINE, METRICS_LINE[:-1] + ' | frozenset({"final_accuracy"})\n')]),
    ("M07", "test_accuracy no longer accepted (the pending name dropped)", f"{BANDS}.test_test_accuracy_is_accepted_and_reads_absent_until_its_producer_lands", [(METRICS_LINE, "ACCEPTANCE_METRICS = frozenset(column for column, _ in RECURRENCE_HEADLINE_PATHS + CASCOR_HEADLINE_PATHS)\n")]),
    ("M08", "test_accuracy fabricated from val_accuracy (a producer that does not exist)", f"{BANDS}.test_test_accuracy_is_accepted_and_reads_absent_until_its_producer_lands", [(CASCOR_PATHS, CASCOR_PATHS[:-1] + '    ("test_accuracy", ("final", "val_accuracy")),\n)')]),
    ("M09", "the retired name's reason dropped from the refusal", f"{BANDS}.test_final_accuracy_is_refused_with_its_reason_and_a_suite_naming_it_exits_two", [('            why = f" ({RETIRED_ACCEPTANCE_METRICS[metric]})" if metric in RETIRED_ACCEPTANCE_METRICS else ""\n', '            why = ""\n')]),
    ("M10", "no pending-metric warning before the launch", f"{BANDS}.test_a_band_on_test_accuracy_warns_once_before_anything_launches", [(EARLY_WARNING, EARLY_WARNING_GONE)]),
    ("M11", "the pending-metric warning arrives only after every cell ran", f"{LOOP}.test_a_test_accuracy_band_warns_before_the_first_launch_and_flags_every_cell", [(EARLY_WARNING, EARLY_WARNING_GONE), (LATE_ANCHOR, LATE_WARNING)]),
    ("M12", "NaN / inf compared like a number (the pre-fix comparison)", f"{NONFINITE}.test_nan_and_both_infinities_fail_min_max_and_two_sided_bands", [(NONFINITE_BRANCH, "")]),
    ("M13", "a non-finite value called absent instead of failed", f"{NONFINITE}.test_nan_and_both_infinities_fail_min_max_and_two_sided_bands", [(NONFINITE_BRANCH, '        elif isinstance(value, float) and not math.isfinite(value):\n            result = "absent"\n            value = None\n')]),
    ("M14", "isfinite applied to every number (a huge int overflows)", f"{NONFINITE}.test_finite_values_still_compare_and_a_huge_int_does_not_overflow", [("        elif isinstance(value, float) and not math.isfinite(value):\n", "        elif not math.isfinite(value):\n")]),
    ("M15", "aggregate prints the recorded metrics, never re-reading stats.json (no backfill)", f"{REAGG}.test_a_pre_fix_cascor_suite_gains_the_columns_and_nothing_launches", [("    row_metrics = {cell_id: _row_metrics(row) for cell_id, row in registry.items()}\n", '    row_metrics = {cell_id: (row.get("metrics") or {}) for cell_id, row in registry.items()}\n')]),
    ("M16", "no fallback to the recorded metrics when the run dir is gone", f"{ROWS}.test_a_pruned_or_unreadable_run_falls_back_to_the_recorded_metrics", [('    recorded = row.get("metrics")\n    return recorded if isinstance(recorded, dict) else {}\n', "    return {}\n")]),
    ("M17", "a recorded value outranks the run's own stats.json", f"{ROWS}.test_a_readable_file_with_no_headline_is_empty_even_if_the_row_recorded_some", [("    if stats is not None:\n", '    if stats is not None and not row.get("metrics"):\n')]),
    ("M18", "--reaggregate appends re-derived rows to registry.jsonl", f"{REAGG}.test_a_pre_fix_cascor_suite_gains_the_columns_and_nothing_launches", [(REAGG_TAIL, REAGG_COMPARISON + '    for row in _read_registry(suite_dir).values():\n        _append_jsonl(suite_dir / "registry.jsonl", {**row, "metrics": _row_metrics(row)})\n    return aggregate(suite_dir, suite, cells, comparison=comparison)\n')]),
    ("M19", "--reaggregate rewrites suite_manifest.json", f"{REAGG}.test_a_pre_fix_cascor_suite_gains_the_columns_and_nothing_launches", [(REAGG_TAIL, REAGG_COMPARISON + '    (suite_dir / "suite_manifest.json").write_text(json.dumps({"suite": suite, "cells": cells}))\n    return aggregate(suite_dir, suite, cells, comparison=comparison)\n')]),
    ("M20", "--reaggregate re-runs the incomplete cells (what --resume does)", f"{REAGG}.test_an_incomplete_suite_keeps_its_exit_code_and_is_not_rerun", [(REAGG_TAIL, REAGG_COMPARISON + RERUN + "    return aggregate(suite_dir, suite, cells, comparison=comparison)\n")]),
    ("M21", "--reaggregate accepts the execution flags", f"{REAGG}.test_the_execution_flags_are_refused_before_anything_is_written", [("    if conflicting:\n", "    if False:\n")]),
    ("M22", "a suite id is not resolved under the run root", f"{REAGG}.test_a_suite_id_resolves_under_the_run_root", [("    suite_dir = given if given.is_dir() else by_id\n", "    suite_dir = given\n")]),
    ("M23", "a manifest cell without overrides is accepted (aggregate then crashes)", f"{REAGG}.test_a_dir_without_a_usable_manifest_is_refused", [('        if not isinstance(raw, dict) or not isinstance(raw.get("cell_id"), str) or not isinstance(overrides, dict):\n', '        if not isinstance(raw, dict) or not isinstance(raw.get("cell_id"), str):\n')]),
    ("M24", "--compare-baseline ignored by --reaggregate", f"{REAGG}.test_compare_baseline_is_honoured", [(REAGG_COMPARISON, "    comparison = None\n")]),
    ("M25", "--suite no longer required on the launch path", f"{REAGG}.test_without_suite_or_reaggregate_is_misuse", [("    if args.suite is None:\n", "    if False:\n")]),
]

FIRST_FAILURE = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+)\)", re.MULTILINE)


def stage(tmp: Path) -> None:
    shutil.copytree(REPO / "util" / "experiments", tmp / "util" / "experiments", ignore=shutil.ignore_patterns("__pycache__"))
    for rel in STAGED_FILES:
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest)


def run_tests(tmp: Path, targets: "list[str]") -> "tuple[bool, str]":
    proc = subprocess.run([sys.executable, "-m", "unittest", *targets], cwd=tmp, capture_output=True, text=True, timeout=1800, check=False)  # nosec B603
    match = FIRST_FAILURE.search(proc.stderr)
    first = f"{match.group(3).rsplit('.', 2)[-2]}.{match.group(2)}" if match else "-"
    return proc.returncode == 0, first


def main(argv: "list[str]") -> int:
    only = set(argv[argv.index("--only") + 1 :]) if "--only" in argv else None
    mutants = [m for m in MUTANTS if only is None or m[0] in only]
    if not mutants:
        print(f"no mutant matches --only {sorted(only or [])}")
        return 2
    original = (REPO / TARGET).read_text(encoding="utf-8")
    for mid, _, _, edits in mutants:
        for anchor, _ in edits:
            if original.count(anchor) != 1:
                print(f"ANCHOR {mid}: {anchor!r} occurs {original.count(anchor)} times in {TARGET} (need exactly 1)")
                return 2
    with tempfile.TemporaryDirectory(prefix="apd-ml-002-mutation-") as raw:
        tmp = Path(raw)
        stage(tmp)
        passed, first = run_tests(tmp, list(SUITES))
        if not passed:
            print(f"VOID     control: {', '.join(SUITES)} fail on the unmutated source (first failure: {first})")
            return 1
        print(f"OK       control: {', '.join(SUITES)} pass on the unmutated source", flush=True)
        survivors = pins_missed = 0
        for mid, defect, pin, edits in mutants:
            mutated = original
            for anchor, replacement in edits:
                mutated = mutated.replace(anchor, replacement)
            (tmp / TARGET).write_text(mutated, encoding="utf-8")
            try:
                suites_passed, first = run_tests(tmp, list(SUITES))
                pin_passed, _ = run_tests(tmp, [pin])
            finally:
                (tmp / TARGET).write_text(original, encoding="utf-8")
            survivors += 1 if suites_passed else 0
            pins_missed += 1 if pin_passed else 0
            print(f"{'SURVIVED' if suites_passed else 'KILLED':8} {mid} {defect}\n                  first failure: {first}; {'PIN MISSED' if pin_passed else 'pin kills it'}: {pin.rsplit('.', 2)[-2]}.{pin.rsplit('.', 1)[-1]}", flush=True)
    total = len(mutants)
    print(f"\n{total - survivors} of {total} mutants killed by the suites; {total - pins_missed} of {total} by their own pin test alone")
    return 0 if survivors == 0 and pins_missed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
