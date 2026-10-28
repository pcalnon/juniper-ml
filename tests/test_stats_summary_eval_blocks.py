#!/usr/bin/env python3
"""juniper-ml#2064: a cascor run's eval scalars are cascor's FINAL evaluation, labelled, in stats.json / summary.md / eval_metrics.png.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests (util/experiments/stats_summary.py, util/experiments/plots_cascor.py)
Author:      Paul Calnon
License:     MIT License

Before juniper-ml#2064, ``stats_summary.build_stats`` copied the ``/v1/metrics`` body's top-level ``f1`` /
``precision`` / ``recall`` / ``roc_auc`` into ``cascor.eval_scalars``, ``summary.md`` printed them as "Eval
scalars", and ``plots_cascor.render_eval_metrics`` drew them. Those are the IN-LOOP values, the last mid-training
evaluation on the split early stopping reads, and nothing said so. The held-out scores sat one level down, in
``eval_metrics.final`` (juniper-cascor#614), and were never surfaced. On run ``20260916T002848Z-3959`` the summary
reported f1 0.9187 and roc_auc 0.9808 on 160 validation rows; the final evaluation of 120 test rows says 0.8997
and 0.9605.

What these pin, on real ``/v1/metrics`` bodies (``tests/cascor_eval_fixtures.py``):

- ``cascor_eval_blocks``: ``eval_scalars`` is the final block with its ``split`` and ``n_samples``, and
  ``held_out`` true only on ``test``; ``eval_scalars_in_loop`` keeps the in-loop values under their own split
  and n. Every way of having no final evaluation (disabled, a null final, a service before the switch, no
  body, no ``eval_metrics`` block) says why in ``absent`` and leaves every value ``None``: it never borrows
  the in-loop numbers. Both blocks always carry the same keys.
- ``build_stats`` writes both blocks under ``juniper-experiment-stats/2``; the values ``/1`` called
  ``eval_scalars`` are exactly the new in-loop block's.
- ``summary.md``: the eval-scalars heading names the split, n and whether it is held out, or says
  "none" and gives the reason, with no number under it; the in-loop values follow under their own
  heading; an undefined metric prints cascor's reason; a ``/1`` block is called unlabelled.
- ``eval_metrics.png``: one labelled series per block (the in-loop one never relabelled), a subtitle
  naming the eval scalars or the reason there are none, the same caption ``summary.md`` prints, and a
  ``ValueError`` (a recorded plot skip) when neither block has a number, or for a raw body.

``util/`` draws "(no files to check) Skipped" from every pre-commit Python hook, so this unittest is a
gate for the renderer, beside ``tests/test_run_experiment.py`` (the driver end to end) and
``tests/test_run_suite.py`` (the ``test_*`` headline columns).
"""

from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import stats_summary as ss  # noqa: E402  (path-invoked util import)

from tests.cascor_eval_fixtures import METRICS_FINAL_NULL_FINAL, METRICS_FINAL_PRE_SWITCH, METRICS_FINAL_TEST_SPLIT, METRICS_FINAL_VALIDATION_SPLIT, V1_STATS_CASCOR, with_final_accuracy  # noqa: E402

try:
    from experiments import plots_cascor as plots  # noqa: E402  (matplotlib + numpy at import time)

    HAVE_PLOTS = True
except ImportError:  # pragma: no cover - CI installs matplotlib and numpy; local envs all carry them
    HAVE_PLOTS = False

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MANIFEST: dict[str, Any] = {"run_id": "r-2064", "experiment": {"name": "e"}, "timings": {"total": 1.0}, "outcome": "succeeded", "acceptance": {"ok": True, "reasons": []}, "dataset": {"meta": {}}}
FINAL_KEYS = ["basis", "split", "n_samples", "held_out", "absent", "accuracy", "f1", "precision", "recall", "roc_auc", "n_classes", "average", "undefined"]
IN_LOOP_KEYS = ["basis", "split", "n_samples", "held_out", "absent", "f1", "precision", "recall", "roc_auc", "n_classes", "average", "undefined"]
PRE_SWITCH_REASON = "the service predates the final evaluation (juniper-cascor#614): eval_metrics has no final block"
DISABLED_REASON = "eval metrics disabled (JUNIPER_CASCOR_EVAL_METRICS_ENABLED)"


def _disabled(body: dict) -> dict:
    """``body`` as a service with eval metrics switched off sends it: ``enabled`` false and, as cascor always does then, a null final."""
    out = copy.deepcopy(body)
    out["eval_metrics"].update(enabled=False, final=None)
    return out


class CascorEvalBlocksTest(unittest.TestCase):
    """``stats_summary.cascor_eval_blocks``: the one derivation behind stats.json, summary.md and the plot."""

    def test_a_test_split_final_evaluation_is_the_eval_scalars_and_the_in_loop_values_keep_their_own_label(self) -> None:
        blocks = ss.cascor_eval_blocks(METRICS_FINAL_TEST_SPLIT)
        self.assertEqual(
            blocks["eval_scalars"],
            {"basis": ss.CASCOR_FINAL_EVAL_BASIS, "split": "test", "n_samples": 120, "held_out": True, "absent": None, "accuracy": None, "f1": 0.899749373433584, "precision": 0.9020979020979021, "recall": 0.8994165045846069, "roc_auc": 0.9605445957210336, "n_classes": 2, "average": "macro", "undefined": {}},
        )
        self.assertEqual(
            blocks["eval_scalars_in_loop"],
            {"basis": ss.CASCOR_IN_LOOP_BASIS, "split": "validation", "n_samples": 160, "held_out": False, "absent": None, "f1": 0.9187214255011527, "precision": 0.9193396964481302, "recall": 0.91875, "roc_auc": 0.98078125, "n_classes": 2, "average": "macro", "undefined": {}},
        )

    def test_the_accuracy_from_juniper_cascor_731_is_carried_and_an_undefined_one_keeps_its_reason(self) -> None:
        cases = [(0.9, None, 0.9, {}), (0.0, None, 0.0, {}), (None, "empty_batch", None, {"accuracy": "empty_batch"})]
        for accuracy, reason, expected, undefined in cases:
            with self.subTest(accuracy=accuracy, reason=reason):
                held = ss.cascor_eval_blocks(with_final_accuracy(METRICS_FINAL_TEST_SPLIT, accuracy, reason))["eval_scalars"]
                self.assertEqual((held["accuracy"], held["undefined"], held["held_out"]), (expected, undefined, True))

    def test_a_validation_split_final_evaluation_is_not_held_out(self) -> None:
        # No test split was loaded, so cascor scored validation -- the in-loop split -- and the numbers equal the in-loop ones.
        blocks = ss.cascor_eval_blocks(METRICS_FINAL_VALIDATION_SPLIT)
        held = blocks["eval_scalars"]
        self.assertEqual((held["split"], held["n_samples"], held["held_out"], held["absent"], held["f1"]), ("validation", 80, False, None, 0.34959349593495936))
        self.assertEqual(blocks["eval_scalars_in_loop"]["f1"], held["f1"])

    def test_no_final_key_says_the_service_predates_it_and_borrows_no_in_loop_value(self) -> None:
        blocks = ss.cascor_eval_blocks(METRICS_FINAL_PRE_SWITCH)
        held = blocks["eval_scalars"]
        self.assertEqual(held["absent"], PRE_SWITCH_REASON)
        self.assertEqual({key: held[key] for key in FINAL_KEYS if key not in ("basis", "absent")}, {"split": None, "n_samples": None, "held_out": False, "accuracy": None, "f1": None, "precision": None, "recall": None, "roc_auc": None, "n_classes": None, "average": None, "undefined": {}})
        in_loop = blocks["eval_scalars_in_loop"]
        self.assertEqual((in_loop["split"], in_loop["n_samples"], in_loop["absent"], in_loop["f1"]), ("training", 200, None, 0.5049876246906173))

    def test_every_other_way_of_having_no_final_evaluation_says_why(self) -> None:
        cases: dict[str, tuple[Any, str, "str | None"]] = {
            "a null final (cascor's golden snapshot)": (METRICS_FINAL_NULL_FINAL, "eval_metrics.final is null: cascor scores the finished model only after a run that completes successfully with a test or validation split loaded", "the service reported no in-loop eval scalars"),
            # The flat fields still hold numbers in this body; a service that says it is disabled is believed in BOTH blocks.
            "eval metrics disabled": (_disabled(METRICS_FINAL_TEST_SPLIT), DISABLED_REASON, DISABLED_REASON),
            "no body collected": (None, "no /v1/metrics body was collected", "no /v1/metrics body was collected"),
            "a body that is not an object": (["f1", 0.9], "no /v1/metrics body was collected", "no /v1/metrics body was collected"),
            "no eval_metrics block": ({"f1": 0.9, "precision": 0.88, "recall": 0.91, "roc_auc": 0.97}, "the /v1/metrics body carries no eval_metrics block", None),
            "a final that is not an object": ({**METRICS_FINAL_TEST_SPLIT, "eval_metrics": {**METRICS_FINAL_TEST_SPLIT["eval_metrics"], "final": "test"}}, "eval_metrics.final is not an object (str)", None),
        }
        for label, (body, held_reason, in_loop_reason) in cases.items():
            with self.subTest(label):
                blocks = ss.cascor_eval_blocks(body)
                self.assertEqual(blocks["eval_scalars"]["absent"], held_reason)
                self.assertEqual([blocks["eval_scalars"][name] for name in ss.CASCOR_FINAL_EVAL_METRICS], [None] * 5, "never the in-loop values")
                self.assertEqual((blocks["eval_scalars"]["split"], blocks["eval_scalars"]["held_out"]), (None, False))
                self.assertEqual(blocks["eval_scalars_in_loop"]["absent"], in_loop_reason)

    def test_both_blocks_always_carry_the_same_keys_and_the_input_is_not_mutated(self) -> None:
        for body in (METRICS_FINAL_TEST_SPLIT, METRICS_FINAL_VALIDATION_SPLIT, METRICS_FINAL_PRE_SWITCH, METRICS_FINAL_NULL_FINAL, _disabled(METRICS_FINAL_TEST_SPLIT), None):
            with self.subTest(body=None if body is None else body.get("timestamp", "synthetic")):
                before = copy.deepcopy(body)
                blocks = ss.cascor_eval_blocks(body)
                self.assertEqual(list(blocks), ["eval_scalars", "eval_scalars_in_loop"])
                self.assertEqual(list(blocks["eval_scalars"]), FINAL_KEYS)
                self.assertEqual(list(blocks["eval_scalars_in_loop"]), IN_LOOP_KEYS)
                self.assertIs(blocks["eval_scalars_in_loop"]["held_out"], False, "an in-loop value is never held out")
                blocks["eval_scalars"]["undefined"]["mutated"] = "here"
                self.assertEqual(body, before)

    def test_is_labelled_eval_block_tells_a_v2_block_from_a_v1_one(self) -> None:
        blocks = ss.cascor_eval_blocks(METRICS_FINAL_TEST_SPLIT)
        self.assertTrue(ss.is_labelled_eval_block(blocks["eval_scalars"]))
        self.assertTrue(ss.is_labelled_eval_block(blocks["eval_scalars_in_loop"]))
        self.assertTrue(ss.is_labelled_eval_block(ss.cascor_eval_blocks(None)["eval_scalars"]), "an absent block is still labelled")
        not_labelled: "tuple[Any, ...]" = (V1_STATS_CASCOR["eval_scalars"], {}, None, [], {"split": "test"})
        for legacy in not_labelled:
            with self.subTest(legacy=legacy):
                self.assertFalse(ss.is_labelled_eval_block(legacy))


class BuildStatsEvalBlocksTest(unittest.TestCase):
    """``build_stats`` carries both blocks, and the schema marks the boundary."""

    def _stats(self, body: Any) -> dict:
        return json.loads(json.dumps(ss.build_stats(MANIFEST, kind="cascor", metrics_final=body)))

    def test_the_cascor_block_carries_both_labelled_blocks_under_schema_2(self) -> None:
        stats = self._stats(METRICS_FINAL_TEST_SPLIT)
        self.assertEqual(stats["schema"], "juniper-experiment-stats/2")
        self.assertEqual(list(stats["cascor"]), ["final", "eval_scalars", "eval_scalars_in_loop", "completion_reason", "candidate_correlation", "training_step_duration"])
        self.assertEqual({key: stats["cascor"][key] for key in ("eval_scalars", "eval_scalars_in_loop")}, json.loads(json.dumps(ss.cascor_eval_blocks(METRICS_FINAL_TEST_SPLIT))))

    def test_the_values_schema_1_called_eval_scalars_are_kept_as_the_in_loop_block(self) -> None:
        # V1_STATS_CASCOR is what the /1 writer made of this very body: its `final` is unchanged, and its
        # `eval_scalars` are exactly the new in-loop block's values -- kept, now labelled.
        stats = self._stats(METRICS_FINAL_TEST_SPLIT)
        self.assertEqual(stats["cascor"]["final"], V1_STATS_CASCOR["final"])
        self.assertEqual({name: stats["cascor"]["eval_scalars_in_loop"][name] for name in ss.CASCOR_IN_LOOP_METRICS}, V1_STATS_CASCOR["eval_scalars"])
        self.assertNotEqual({name: stats["cascor"]["eval_scalars"][name] for name in ss.CASCOR_IN_LOOP_METRICS}, V1_STATS_CASCOR["eval_scalars"], "the eval scalars changed meaning")

    def test_a_recurrence_stats_block_is_untouched(self) -> None:
        stats = json.loads(json.dumps(ss.build_stats(MANIFEST, kind="recurrence", train_summary={"final_metrics": {"r2": 0.5}})))
        self.assertNotIn("cascor", stats)
        self.assertEqual(list(stats["recurrence"]), ["final_metrics", "n_epochs", "stopped_reason", "dataset_descriptor", "theta", "readout", "crossval"])


class SummaryMdEvalBlocksTest(unittest.TestCase):
    """``render_summary_md``: the eval-scalars section names what it reports, or why there is nothing."""

    def _sections(self, body: Any) -> "tuple[str, str]":
        rendered = ss.render_summary_md(ss.build_stats(MANIFEST, kind="cascor", metrics_final=body))
        section = rendered[rendered.index("### Eval scalars") : rendered.index("### Candidate correlation")]
        held, in_loop = section.split("### In-loop eval scalars")
        return held, in_loop

    def test_a_held_out_run_reports_the_final_evaluation_then_the_in_loop_values(self) -> None:
        held, in_loop = self._sections(with_final_accuracy(METRICS_FINAL_TEST_SPLIT, 0.9))
        self.assertEqual(held, f"### Eval scalars (final evaluation: test split, n=120, held out)\n\n- accuracy: 0.9\n- f1: 0.899749\n- precision: 0.902098\n- recall: 0.899417\n- roc_auc: 0.960545\n- basis: {ss.CASCOR_FINAL_EVAL_BASIS}\n\n")
        self.assertEqual(in_loop, f" (validation split, n=160, NOT held out: the in-loop split)\n\n- f1: 0.918721\n- precision: 0.91934\n- recall: 0.91875\n- roc_auc: 0.980781\n- basis: {ss.CASCOR_IN_LOOP_BASIS}\n\n")

    def test_a_validation_split_final_evaluation_is_headed_not_held_out(self) -> None:
        held, _ = self._sections(METRICS_FINAL_VALIDATION_SPLIT)
        self.assertTrue(held.startswith("### Eval scalars (final evaluation: validation split, n=80, NOT held out: the in-loop split)\n\n- accuracy: not reported\n- f1: 0.349593\n"), held)

    def test_no_final_evaluation_prints_the_reason_and_no_number(self) -> None:
        held, in_loop = self._sections(METRICS_FINAL_PRE_SWITCH)
        self.assertEqual(held, f"### Eval scalars (final evaluation: none)\n\n(none: {PRE_SWITCH_REASON}; the in-loop values below are not the run's eval scalars)\n\n")
        self.assertTrue(in_loop.startswith(" (training split, n=200, NOT held out: the training split)\n\n- f1: 0.504988\n"), in_loop)

    def test_disabled_eval_metrics_say_so_in_both_sections(self) -> None:
        held, in_loop = self._sections(_disabled(METRICS_FINAL_NULL_FINAL))
        self.assertIn(f"(none: {DISABLED_REASON}; the in-loop values below are not the run's eval scalars)", held)
        self.assertEqual(in_loop, f" (none)\n\n(none: {DISABLED_REASON})\n\n")

    def test_an_undefined_metric_prints_cascors_reason_and_a_missing_one_says_not_reported(self) -> None:
        held, _ = self._sections(with_final_accuracy(METRICS_FINAL_TEST_SPLIT, None, "empty_batch"))
        self.assertIn("- accuracy: undefined (empty_batch)\n", held)
        held, _ = self._sections(METRICS_FINAL_TEST_SPLIT)
        self.assertIn("- accuracy: not reported\n", held)

    def test_a_schema_1_block_renders_as_unlabelled_in_loop_values(self) -> None:
        rendered = ss.render_summary_md({"cascor": copy.deepcopy(V1_STATS_CASCOR)})
        self.assertIn("### Eval scalars (unlabelled: a juniper-experiment-stats/1 block, the in-loop values)\n\n- f1: 0.918721\n", rendered)
        self.assertNotIn("final evaluation", rendered)
        self.assertNotIn("### In-loop eval scalars", rendered)


@unittest.skipUnless(HAVE_PLOTS, "matplotlib + numpy required for the SS8.1 plot set")
class EvalMetricsPlotTest(unittest.TestCase):
    """``plots_cascor``: eval_metrics.png draws the labelled blocks, never the raw body's in-loop fields as eval scalars."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="eval-blocks-plot-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def test_the_series_are_the_two_labelled_blocks(self) -> None:
        names, series, subtitle = plots.eval_metrics_series(ss.cascor_eval_blocks(with_final_accuracy(METRICS_FINAL_TEST_SPLIT, 0.9)))
        self.assertEqual(names, ["accuracy", "f1", "precision", "recall", "roc_auc"])
        self.assertEqual([(role, label) for role, label, _ in series], [("final evaluation", "final evaluation: test split, n=120, held out"), ("in-loop", "in-loop: validation split, n=160, NOT held out: the in-loop split")])
        self.assertEqual(series[0][2], {"accuracy": 0.9, "f1": 0.899749373433584, "precision": 0.9020979020979021, "recall": 0.8994165045846069, "roc_auc": 0.9605445957210336})
        self.assertEqual(series[1][2], {"f1": 0.9187214255011527, "precision": 0.9193396964481302, "recall": 0.91875, "roc_auc": 0.98078125})
        self.assertEqual(subtitle, "eval scalars = the final evaluation (test split, n=120, held out)")

    def test_a_bool_or_a_null_is_no_bar(self) -> None:
        blocks = ss.cascor_eval_blocks(with_final_accuracy(METRICS_FINAL_TEST_SPLIT, None, "empty_batch"))
        blocks["eval_scalars"]["f1"] = True
        _, series, _ = plots.eval_metrics_series(blocks)
        self.assertEqual(sorted(series[0][2]), ["precision", "recall", "roc_auc"], "neither True nor the undefined accuracy is a score")

    def test_with_no_final_evaluation_only_the_in_loop_bars_are_drawn_under_their_own_label(self) -> None:
        names, series, subtitle = plots.eval_metrics_series(ss.cascor_eval_blocks(METRICS_FINAL_PRE_SWITCH))
        self.assertEqual([(role, label) for role, label, _ in series], [("in-loop", "in-loop: training split, n=200, NOT held out: the training split")])
        self.assertEqual(names, ["f1", "precision", "recall", "roc_auc"])
        self.assertEqual(subtitle, f"no final evaluation ({PRE_SWITCH_REASON}): the in-loop bars are NOT the run's eval scalars")

    def test_a_final_evaluation_with_every_metric_undefined_says_so(self) -> None:
        body = with_final_accuracy(METRICS_FINAL_TEST_SPLIT, None, "empty_batch")
        body["eval_metrics"]["final"].update(f1=None, precision=None, recall=None, roc_auc=None, n_samples=0)
        _, series, subtitle = plots.eval_metrics_series(ss.cascor_eval_blocks(body))
        self.assertEqual([role for role, _, _ in series], ["in-loop"])
        self.assertEqual(subtitle, "eval scalars = the final evaluation (test split, n=0, held out); it defined no metric")

    def test_the_legend_caption_is_the_summary_md_caption(self) -> None:
        bodies = [METRICS_FINAL_TEST_SPLIT, METRICS_FINAL_VALIDATION_SPLIT, METRICS_FINAL_PRE_SWITCH, {"f1": 0.9}]
        blocks = [block for body in bodies for block in ss.cascor_eval_blocks(body).values() if not block["absent"]]
        blocks.append({**blocks[0], "split": None, "n_samples": None, "held_out": False})
        self.assertGreaterEqual(len(blocks), 7)
        for block in blocks:
            with self.subTest(split=block["split"], n=block["n_samples"]):
                self.assertEqual(plots._eval_caption(block), ss.eval_caption(block))

    def test_the_png_renders_from_the_blocks_and_from_a_stats_json_cascor_block(self) -> None:
        stats_cascor = json.loads(json.dumps(ss.build_stats(MANIFEST, kind="cascor", metrics_final=METRICS_FINAL_TEST_SPLIT)))["cascor"]
        for label, blocks in (("derived", ss.cascor_eval_blocks(with_final_accuracy(METRICS_FINAL_TEST_SPLIT, 0.9))), ("stats.json", stats_cascor), ("in-loop only", ss.cascor_eval_blocks(METRICS_FINAL_PRE_SWITCH))):
            with self.subTest(label):
                raw = plots.render_eval_metrics(blocks, "run", self.tmp / f"{label}.png").read_bytes()
                self.assertTrue(raw.startswith(PNG_MAGIC))
                self.assertGreater(len(raw), 1500)

    def test_nothing_to_draw_is_a_value_error_and_a_raw_body_is_never_drawn(self) -> None:
        # A raw /v1/metrics body is what this renderer drew until juniper-ml#2064: its top-level in-loop fields, as the run's eval scalars.
        for label, blocks in (("disabled", ss.cascor_eval_blocks(_disabled(METRICS_FINAL_NULL_FINAL))), ("a raw body", METRICS_FINAL_TEST_SPLIT)):
            with self.subTest(label):
                with self.assertRaises(ValueError) as ctx:
                    plots.render_eval_metrics(blocks, "run", self.tmp / "eval.png")
                self.assertIn("no eval metrics to plot", str(ctx.exception))
                self.assertFalse((self.tmp / "eval.png").exists())


if __name__ == "__main__":
    unittest.main()
