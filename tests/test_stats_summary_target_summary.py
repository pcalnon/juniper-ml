#!/usr/bin/env python3
"""W5.5 (F-D8): the per-split regression target summary in ``stats.json`` / ``summary.md``.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests (util/experiments/stats_summary.py, util/experiments/run_experiment.py)
Author:      Paul Calnon
License:     MIT License

The equities end-to-end audit (plan §3.2, F-D8) found ``stats_summary.py`` reporting the
sequence dimensions and the class distribution but no regression-target summary, while the
experimentation plan's §8.3 asks for "class balance or target summary stats". Every equities
cell is a regression fit, so the audited ``stats.json`` said nothing about the thing the fit
predicts -- and nothing could tell a -18,081 r² solved on a target with a non-finite row from
one solved on a clean target.

What these pin:

- ``stats_summary.regression_target_summary`` (stdlib): mean / population std / min / max /
  finite fraction per split; NaN and ±Inf count toward ``n`` and against ``finite_fraction`` and
  are excluded from the moments; an all-non-finite split keeps ``n`` and reports ``None``
  moments; an empty split reports ``finite_fraction`` ``None`` (0/0 is not 0); splits come out
  train / val / test then sorted; a single value has std 0; no splits at all is ``None``; the
  result is JSON-serialisable.
- ``build_stats`` carries the block as ``dataset.target_summary`` (``None`` when absent) and turns
  a ``target_summary_error`` into a degraded-mode note rather than a missing key.
- ``render_summary_md`` prints one line per split plus the basis, says "moments unavailable" for
  a split with no finite values, and prints nothing when the block is absent.
- The driver's ``_regression_target_summary``, on the AUDITED artifact
  (``reports/2026-10-05_recurrence-equities-cv-consensus/laneA3-rerun/data/
  equities_seq-6.0.0-15505731cba5b86d.npz``, the mint the -18,081 was solved on): 1346 / 176 /
  176 windows, every one finite, and the log-return moments a numpy reference computes; no
  ``dataset_id`` and an artifact without ``y_reg_*`` keys are silent ``None``s; a failed fetch, an
  unreadable body and an absent numpy are ``None`` plus a reason -- and none of them raises,
  because the summary is evidence about the data and must never cost the run.

``util/`` is not pre-commit-lint-gated; this unittest is the gate. Hermetic: the driver's
``_http_bytes`` is replaced in-process; no service, no network. The numpy-backed class skips
without numpy (CI installs it).
"""

from __future__ import annotations

import io
import json
import math
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import run_experiment as rx  # noqa: E402  (path-invoked util import)
from experiments import stats_summary as ss  # noqa: E402

try:
    import numpy as np

    HAVE_NUMPY = True
except ImportError:  # pragma: no cover - CI installs numpy; local envs all carry it
    HAVE_NUMPY = False

AUDITED_ID = "equities_seq-6.0.0-15505731cba5b86d"
AUDITED_NPZ = REPO_ROOT / "reports" / "2026-10-05_recurrence-equities-cv-consensus" / "laneA3-rerun" / "data" / f"{AUDITED_ID}.npz"
NAN = float("nan")
INF = float("inf")


def _manifest() -> dict:
    return {
        "run_id": "r-w55",
        "experiment": {"name": "e-h", "description": "the audited equities cell"},
        "dataset": {
            "dataset_id": AUDITED_ID,
            "generator": "equities_seq",
            "version": "6.0.0",
            "split": "train",
            "params": {"symbols": ["AAPL"]},
            "meta": {"sequence": True, "task_type": "regression", "n_samples": 1698, "lookback": 64, "n_features": 15, "n_train": 1346, "n_test": 176, "class_distribution": None},
        },
        "timings": {"total": 1.0},
        "git": {},
        "packages": {},
    }


def _stats_with(target_summary) -> dict:
    return {
        "identity": {"run_id": "r-w55", "git": {}},
        "dataset": {"generator": "equities_seq", "generator_version": "6.0.0", "task_type": "regression", "shapes": {"kind": "sequence", "n_windows": 1698}, "class_distribution": None, "target_summary": target_summary},
        "outcome": {"outcome": "succeeded", "acceptance": {"ok": True}, "wall_seconds": 1.0, "timings": {}},
        "provenance": {"metrics_scraped": {}},
    }


class RegressionTargetSummaryTest(unittest.TestCase):
    """The stdlib summary function, value by value."""

    def test_known_values(self) -> None:
        out = ss.regression_target_summary({"train": [1.0, 2.0, 3.0, 4.0]})
        self.assertIsNotNone(out)
        self.assertEqual(out["basis"], ss.TARGET_SUMMARY_BASIS)
        block = out["splits"]["train"]
        self.assertEqual((block["n"], block["n_finite"], block["finite_fraction"]), (4, 4, 1.0))
        self.assertEqual((block["mean"], block["min"], block["max"]), (2.5, 1.0, 4.0))
        self.assertAlmostEqual(block["std"], math.sqrt(1.25), places=15, msg="population std (ddof=0), not the sample std")

    def test_non_finite_counts_toward_n_and_not_the_moments(self) -> None:
        block = ss.regression_target_summary({"train": [1.0, NAN, INF, 3.0, -INF]})["splits"]["train"]
        self.assertEqual((block["n"], block["n_finite"]), (5, 2))
        self.assertAlmostEqual(block["finite_fraction"], 0.4)
        self.assertEqual((block["mean"], block["std"], block["min"], block["max"]), (2.0, 1.0, 1.0, 3.0))

    def test_all_non_finite_keeps_n_and_reports_none_moments(self) -> None:
        block = ss.regression_target_summary({"val": [NAN, INF]})["splits"]["val"]
        self.assertEqual((block["n"], block["n_finite"], block["finite_fraction"]), (2, 0, 0.0))
        self.assertEqual([block[key] for key in ("mean", "std", "min", "max")], [None] * 4)

    def test_empty_split_is_not_zero_over_zero(self) -> None:
        block = ss.regression_target_summary({"test": []})["splits"]["test"]
        self.assertEqual((block["n"], block["n_finite"]), (0, 0))
        self.assertIsNone(block["finite_fraction"], "0/0 is unknown, not 0 -- a finite_fraction of 0 would read as 'every value non-finite'")
        self.assertIsNone(block["mean"])

    def test_split_order_is_train_val_test_then_sorted(self) -> None:
        out = ss.regression_target_summary({"test": [1.0], "zeta": [1.0], "alpha": [1.0], "val": [1.0], "train": [1.0]})
        self.assertEqual(list(out["splits"]), ["train", "val", "test", "alpha", "zeta"])

    def test_no_splits_is_none(self) -> None:
        self.assertIsNone(ss.regression_target_summary({}))

    def test_single_value_has_std_zero(self) -> None:
        block = ss.regression_target_summary({"train": [0.25]})["splits"]["train"]
        self.assertEqual((block["mean"], block["std"], block["min"], block["max"]), (0.25, 0.0, 0.25, 0.25))

    def test_unparseable_values_are_non_finite_not_fatal(self) -> None:
        block = ss.regression_target_summary({"train": ["1.5", None, "x", 2.5]})["splits"]["train"]
        self.assertEqual((block["n"], block["n_finite"]), (4, 2))
        self.assertEqual(block["mean"], 2.0)

    def test_result_is_json_serialisable(self) -> None:
        out = ss.regression_target_summary({"train": [1.0, NAN], "test": []})
        round_trip = json.loads(json.dumps(out))
        self.assertEqual(round_trip["splits"]["train"]["n"], 2)
        self.assertIsNone(round_trip["splits"]["test"]["finite_fraction"])


class BuildStatsTargetSummaryTest(unittest.TestCase):
    """``build_stats`` carries the block under ``dataset`` and the error into the degraded notes."""

    def test_block_is_carried_under_dataset(self) -> None:
        summary = ss.regression_target_summary({"train": [1.0, 2.0], "test": [3.0]})
        stats = ss.build_stats(_manifest(), kind="recurrence", target_summary=summary)
        self.assertEqual(stats["dataset"]["target_summary"], summary)
        self.assertEqual(stats["dataset"]["shapes"]["kind"], "sequence", "the rest of the dataset block is untouched")
        self.assertNotIn("regression target summary", " ".join(stats["provenance"]["degraded_notes"]))

    def test_absent_summary_is_none_with_no_note(self) -> None:
        stats = ss.build_stats(_manifest(), kind="recurrence")
        self.assertIn("target_summary", stats["dataset"], "the key is always present, so a reader can tell absent from unwritten")
        self.assertIsNone(stats["dataset"]["target_summary"])
        self.assertEqual(stats["provenance"]["degraded_notes"], [])

    def test_error_is_a_degraded_note_and_the_block_stays_none(self) -> None:
        stats = ss.build_stats(_manifest(), kind="cascor", target_summary_error="numpy unavailable: No module named 'numpy'")
        self.assertIsNone(stats["dataset"]["target_summary"])
        self.assertIn("regression target summary unavailable: numpy unavailable: No module named 'numpy'", stats["provenance"]["degraded_notes"])


class RenderTargetSummaryTest(unittest.TestCase):
    """``summary.md`` lines for the block."""

    def test_one_line_per_split_plus_the_basis(self) -> None:
        summary = ss.regression_target_summary({"train": [1.0, 2.0, 3.0, 4.0], "val": [0.5]})
        rendered = ss.render_summary_md(_stats_with(summary))
        self.assertIn("- regression target (y_reg) per split:", rendered)
        self.assertIn("  - train: n=4, finite=4 (fraction 1), mean=2.5, std=1.11803, min=1, max=4", rendered)
        self.assertIn("  - val: n=1, finite=1 (fraction 1), mean=0.5, std=0, min=0.5, max=0.5", rendered)
        self.assertIn(f"  - basis: {ss.TARGET_SUMMARY_BASIS}", rendered)

    def test_no_finite_values_says_so(self) -> None:
        summary = ss.regression_target_summary({"test": [NAN, NAN]})
        rendered = ss.render_summary_md(_stats_with(summary))
        self.assertIn("  - test: n=2, finite=0 (fraction 0), moments unavailable (no finite values)", rendered)
        self.assertNotIn("mean=None", rendered)

    def test_absent_block_renders_no_line(self) -> None:
        rendered = ss.render_summary_md(_stats_with(None))
        self.assertNotIn("regression target", rendered)
        stale = dict(_stats_with(None))
        del stale["dataset"]["target_summary"]
        self.assertNotIn("regression target", ss.render_summary_md(stale), "a pre-W5.5 stats.json still renders")


@unittest.skipUnless(HAVE_NUMPY, "numpy decodes the artifact (CI installs it)")
class DriverTargetSummaryOnAuditedArtifactTest(unittest.TestCase):
    """``run_experiment._regression_target_summary`` against the committed audited artifact."""

    def setUp(self) -> None:
        self.calls: list = []
        self.addCleanup(setattr, rx, "_http_bytes", rx._http_bytes)

    def _serve(self, body) -> None:
        def fake(url: str, timeout: float = 60.0) -> bytes:
            self.calls.append(url)
            if isinstance(body, Exception):
                raise body
            return body

        rx._http_bytes = fake  # type: ignore[assignment]

    def test_audited_artifact_summary_matches_the_numpy_reference(self) -> None:
        self._serve(AUDITED_NPZ.read_bytes())
        out = rx._regression_target_summary("http://127.0.0.1:1", {"dataset_id": AUDITED_ID, "meta": {"task_type": "regression"}})
        self.assertEqual(self.calls, [f"http://127.0.0.1:1/v1/datasets/{AUDITED_ID}/artifact"], "one fetch, of the artifact the plot set reads")
        self.assertIsNone(out["target_summary_error"])
        splits = out["target_summary"]["splits"]
        self.assertEqual(list(splits), ["train", "val", "test"])
        self.assertEqual({split: block["n"] for split, block in splits.items()}, {"train": 1346, "val": 176, "test": 176}, "the audited window counts (plan §3.4)")
        with np.load(AUDITED_NPZ, allow_pickle=False) as bundle:
            for split, block in splits.items():
                with self.subTest(split=split):
                    y = bundle[f"y_reg_{split}"].astype(float).ravel()
                    self.assertEqual(block["n_finite"], int(np.isfinite(y).sum()))
                    self.assertEqual(block["finite_fraction"], 1.0, "the audit found every numeric key 100 % finite")
                    self.assertAlmostEqual(block["mean"], float(y.mean()), places=12)
                    self.assertAlmostEqual(block["std"], float(y.std()), places=12, msg="numpy's default ddof=0, the same basis")
                    self.assertEqual((block["min"], block["max"]), (float(y.min()), float(y.max())))
        # The numbers themselves, so a regression in either the artifact or the reader is legible here.
        train = splits["train"]
        self.assertAlmostEqual(train["mean"], 0.000928602, places=8)
        self.assertAlmostEqual(train["std"], 0.0182354, places=6)
        self.assertAlmostEqual(train["min"], -0.137708, places=5)
        self.assertAlmostEqual(train["max"], 0.113157, places=5)
        self.assertEqual(out["target_summary"]["basis"], ss.TARGET_SUMMARY_BASIS)

    def test_no_dataset_id_is_silent_and_fetches_nothing(self) -> None:
        self._serve(AUDITED_NPZ.read_bytes())
        for response in ({}, {"dataset_id": None}, {"dataset_id": ""}):
            with self.subTest(response=response):
                self.assertEqual(rx._regression_target_summary("http://127.0.0.1:1", response), {"target_summary": None, "target_summary_error": None})
        self.assertEqual(self.calls, [])

    def test_artifact_without_targets_is_silent(self) -> None:
        buf = io.BytesIO()
        np.savez(buf, X_train=np.zeros((4, 2), dtype="float32"), y_train=np.zeros((4, 2), dtype="float32"))
        self._serve(buf.getvalue())
        self.assertEqual(rx._regression_target_summary("http://127.0.0.1:1", {"dataset_id": "spirals-1.0.0-abc"}), {"target_summary": None, "target_summary_error": None})
        self.assertEqual(len(self.calls), 1)

    def test_fetch_failure_is_a_reason_not_an_exception(self) -> None:
        self._serve(rx.ServiceUnreachable("GET http://127.0.0.1:1/v1/datasets/x/artifact: connection refused"))
        out = rx._regression_target_summary("http://127.0.0.1:1", {"dataset_id": "x"})
        self.assertIsNone(out["target_summary"])
        self.assertIn("ServiceUnreachable", out["target_summary_error"])
        self.assertIn("connection refused", out["target_summary_error"])

    def test_unreadable_body_is_a_reason(self) -> None:
        self._serve(b"not an npz artifact")
        out = rx._regression_target_summary("http://127.0.0.1:1", {"dataset_id": "x"})
        self.assertIsNone(out["target_summary"])
        self.assertTrue(out["target_summary_error"], "the decode failure is named")

    def test_numpy_unavailable_is_a_reason_and_nothing_is_fetched(self) -> None:
        self._serve(AUDITED_NPZ.read_bytes())
        saved = sys.modules.get("numpy")
        # A None entry makes `import numpy` raise ImportError, which is the branch under test.
        sys.modules["numpy"] = None  # type: ignore[assignment]
        try:
            out = rx._regression_target_summary("http://127.0.0.1:1", {"dataset_id": AUDITED_ID})
        finally:
            if saved is None:
                sys.modules.pop("numpy", None)
            else:
                sys.modules["numpy"] = saved
        self.assertIsNone(out["target_summary"])
        self.assertTrue(out["target_summary_error"].startswith("numpy unavailable"), out["target_summary_error"])
        self.assertEqual(self.calls, [], "no decode possible, so no fetch")

    def test_the_summary_survives_build_stats_and_the_renderer(self) -> None:
        self._serve(AUDITED_NPZ.read_bytes())
        inputs = rx._regression_target_summary("http://127.0.0.1:1", {"dataset_id": AUDITED_ID})
        stats = ss.build_stats(_manifest(), kind="recurrence", **inputs)
        self.assertEqual(stats["dataset"]["target_summary"]["splits"]["val"]["n"], 176)
        rendered = ss.render_summary_md(stats)
        self.assertIn("  - train: n=1346, finite=1346 (fraction 1), mean=0.0009286", rendered)
        json.dumps(stats)


if __name__ == "__main__":
    unittest.main()
