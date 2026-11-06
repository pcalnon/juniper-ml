#!/usr/bin/env python3
"""juniper-ml#2064: a measured zero is a score, and only ``enabled is False`` turns eval metrics off.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests (util/experiments/stats_summary.py)
Author:      Paul Calnon
License:     MIT License

``tests/test_stats_summary_eval_blocks.py`` pins the shapes a real cascor body takes: a test
split, a validation split, a null final, a disabled service whose final is also null, and
in-loop fields that are either real scores or all null. It does not pin the comparisons
those shapes happen to satisfy.

- An in-loop ``f1`` / ``precision`` / ``recall`` / ``roc_auc`` of ``0.0`` is a measurement.
  ``cascor_eval_blocks`` treats a scalar as missing only when it ``is None``. A truthiness
  check would call an all-zero block "the service reported no in-loop eval scalars" and
  drop the zeros from ``summary.md``.
- ``enabled is False`` is the off switch, and it wins over a populated ``eval_metrics.final``.
  The existing disabled fixture also nulls ``final``, so a check that trusted a present
  final object would still pass. A missing ``enabled`` key, and ``enabled`` of ``0``, are
  not that switch: ``not live.get("enabled")`` would throw away the held-out scores.
- ``held_out`` is true only when the final split is exactly ``test``. ``Test`` and
  ``test `` stay a final evaluation and are not held out. ``eval_caption`` prints ``n=0``
  and does not call a test split held out unless the block says so.
"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import stats_summary as ss  # noqa: E402  (path-invoked util import)

from tests.cascor_eval_fixtures import METRICS_FINAL_TEST_SPLIT  # noqa: E402

DISABLED = "eval metrics disabled (JUNIPER_CASCOR_EVAL_METRICS_ENABLED)"
NO_IN_LOOP = "the service reported no in-loop eval scalars"
MANIFEST: dict[str, Any] = {"run_id": "r-zero", "experiment": {"name": "e"}, "timings": {"total": 1.0}, "outcome": "succeeded", "acceptance": {"ok": True, "reasons": []}, "dataset": {"meta": {}}}


def _body() -> dict[str, Any]:
    return copy.deepcopy(METRICS_FINAL_TEST_SPLIT)


class CascorEvalZeroAndEnabledTest(unittest.TestCase):
    """The comparisons around a present final block, not the shapes the corpus fixtures already take."""

    def test_in_loop_zeros_are_scores(self) -> None:
        """``0.0`` is not ``None``: an all-zero in-loop block, and a block whose only scalar is ``f1`` 0.0, are published."""
        all_zero = _body()
        for name in ss.CASCOR_IN_LOOP_METRICS:
            all_zero[name] = 0.0
        all_zero["eval_metrics"]["n_samples"] = 0
        blocks = ss.cascor_eval_blocks(all_zero)
        in_loop = blocks["eval_scalars_in_loop"]
        self.assertIsNone(in_loop["absent"])
        self.assertEqual({name: in_loop[name] for name in ss.CASCOR_IN_LOOP_METRICS}, {name: 0.0 for name in ss.CASCOR_IN_LOOP_METRICS})
        self.assertEqual((in_loop["split"], in_loop["n_samples"], in_loop["held_out"]), ("validation", 0, False))
        self.assertTrue(blocks["eval_scalars"]["held_out"], "zeroing the in-loop values must not drop the held-out final")

        only_f1 = _body()
        only_f1["f1"] = 0.0
        for name in ss.CASCOR_IN_LOOP_METRICS:
            if name != "f1":
                only_f1[name] = None
        in_loop = ss.cascor_eval_blocks(only_f1)["eval_scalars_in_loop"]
        self.assertIsNone(in_loop["absent"])
        self.assertEqual(in_loop["f1"], 0.0)
        self.assertEqual([in_loop[name] for name in ss.CASCOR_IN_LOOP_METRICS if name != "f1"], [None, None, None])

        rendered = ss.render_summary_md(ss.build_stats(MANIFEST, kind="cascor", metrics_final=all_zero))
        self.assertIn("### In-loop eval scalars (validation split, n=0, NOT held out: the in-loop split)", rendered)
        self.assertIn("- f1: 0\n", rendered)
        self.assertNotIn(NO_IN_LOOP, rendered)

    def test_enabled_false_discards_a_populated_final(self) -> None:
        """``enabled is False`` wins even when ``final`` and the in-loop fields still hold numbers.

        The corpus disabled fixture also sets ``final`` to null, so looking at the final object first would still pass it.
        """
        body = _body()
        body["eval_metrics"]["enabled"] = False
        self.assertIsInstance(body["eval_metrics"]["final"], dict)
        self.assertIsNotNone(body["f1"])
        blocks = ss.cascor_eval_blocks(body)
        self.assertEqual(blocks["eval_scalars"]["absent"], DISABLED)
        self.assertEqual(blocks["eval_scalars_in_loop"]["absent"], DISABLED)
        self.assertEqual([blocks["eval_scalars"][name] for name in ss.CASCOR_FINAL_EVAL_METRICS], [None] * 5)
        self.assertEqual([blocks["eval_scalars_in_loop"][name] for name in ss.CASCOR_IN_LOOP_METRICS], [None] * 4)
        self.assertFalse(blocks["eval_scalars"]["held_out"])

        rendered = ss.render_summary_md(ss.build_stats(MANIFEST, kind="cascor", metrics_final=body))
        self.assertIn(DISABLED, rendered)
        self.assertNotIn("0.899749", rendered)
        self.assertNotIn("0.918721", rendered)

    def test_a_missing_enabled_or_a_zero_still_reports_the_final(self) -> None:
        """``not live.get("enabled")`` is the wrong check: a missing key and ``0`` are not ``False``."""
        cases: dict[str, dict[str, Any]] = {}
        missing = _body()
        del missing["eval_metrics"]["enabled"]
        cases["missing enabled"] = missing
        numeric = _body()
        numeric["eval_metrics"]["enabled"] = 0
        cases["enabled 0"] = numeric
        for label, body in cases.items():
            with self.subTest(label):
                held = ss.cascor_eval_blocks(body)["eval_scalars"]
                self.assertIsNone(held["absent"])
                self.assertTrue(held["held_out"])
                self.assertEqual(held["split"], "test")
                self.assertEqual(held["f1"], METRICS_FINAL_TEST_SPLIT["eval_metrics"]["final"]["f1"])

    def test_held_out_is_the_exact_split_test_and_a_zero_final_still_counts(self) -> None:
        """``"Test"`` and ``"test "`` are a final evaluation and are not held out. An all-zero ``test`` final is held out."""
        for split, held_out in (("test", True), ("Test", False), ("test ", False)):
            with self.subTest(split=split):
                body = _body()
                body["eval_metrics"]["final"]["split"] = split
                held = ss.cascor_eval_blocks(body)["eval_scalars"]
                self.assertIsNone(held["absent"])
                self.assertIs(held["held_out"], held_out)
                self.assertEqual(held["split"], split)
                self.assertEqual(held["f1"], METRICS_FINAL_TEST_SPLIT["eval_metrics"]["final"]["f1"])

        zeros = _body()
        final = zeros["eval_metrics"]["final"]
        for name in ("accuracy", "f1", "precision", "recall", "roc_auc"):
            final[name] = 0.0
        final["n_samples"] = 0
        held = ss.cascor_eval_blocks(zeros)["eval_scalars"]
        self.assertIsNone(held["absent"])
        self.assertTrue(held["held_out"])
        self.assertEqual({name: held[name] for name in ss.CASCOR_FINAL_EVAL_METRICS}, {name: 0.0 for name in ss.CASCOR_FINAL_EVAL_METRICS})
        self.assertEqual(held["n_samples"], 0)

    def test_caption_keeps_a_zero_count_and_trusts_the_held_out_flag(self) -> None:
        """``n=0`` is a count. A test split is held out only when the block says so, not because its name is ``test``."""
        self.assertEqual(ss.eval_caption({"split": "test", "absent": None, "held_out": False, "n_samples": 0}), "test split, n=0, NOT held out")
        self.assertEqual(ss.eval_caption({"split": "test", "absent": None, "held_out": True, "n_samples": 0}), "test split, n=0, held out")
        self.assertEqual(ss.eval_caption({"split": None, "absent": None, "held_out": False, "n_samples": None}), "unknown split, n=unknown, NOT held out")
        self.assertEqual(ss.eval_caption({"split": "Test", "absent": None, "held_out": False, "n_samples": 120}), "Test split, n=120, NOT held out")


if __name__ == "__main__":
    unittest.main()
