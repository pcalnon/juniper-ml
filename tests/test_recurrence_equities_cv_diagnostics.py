#!/usr/bin/env python3
"""Hermetic coverage for the W0.8/W0.9 equities cross-validation diagnostics.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py`` is the measurement
behind the P5 GO verdict. It ships with no tests, and ``util/ad-hoc/`` is
outside every pre-commit Python hook, so a silent change to the diagnostic is
indistinguishable from a new measurement.

These tests stay off the live stack. They pin the helpers whose wrong answer
changes the verdict:

* ``_z_against`` -- a constant memory column must not become ``inf`` (the
  zero-variance guard divides by 1), a real column is a population z-score,
  and a z of exactly 5 or exactly 10 does not count as an exceedance. One row
  counts once, however many of its columns exceed.
* ``_stats`` -- an empty vector raises. Summarising it as zeros would let an
  empty fold look measured.
* ``render_matrix`` -- an error cell is the word ERROR in the per-fold column
  and does not need aggregates, so a failed fit cannot be printed as a number.
  A resolved gamma of 0 is still printed. A string ridge stays a string.
* ``fold_table`` -- a fold missing its metrics raises, and a missing aggregate
  is ``nan``, not zero.
* ``http_json`` / ``create_dataset`` -- a non-JSON error stays text, an empty
  success body is None, and a create that did not return a dataset id exits
  instead of being replayed. The POST persists.

Nothing here opens a socket or imports juniper-recurrence.
"""

from __future__ import annotations

import importlib.util
import io
import json
import math
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-10-04_recurrence_equities_cv_matrix.py"

_spec = importlib.util.spec_from_file_location("recurrence_equities_cv_matrix", SCRIPT)
cv = importlib.util.module_from_spec(_spec)
assert _spec is not None and _spec.loader is not None
_spec.loader.exec_module(cv)


class _Body:
    """A urlopen response. ``read`` returns the body once, as the real one does."""

    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_Body":
        return self

    def __exit__(self, *exc: object) -> None:
        """Never suppresses: an exception inside the ``with`` propagates, as with a real response."""


def _http_error(status: int, body: bytes) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://127.0.0.1/unused", status, "err", hdrs=None, fp=io.BytesIO(body))


class ZAgainstTest(unittest.TestCase):
    """The memory-state z-score the matrix table prints per fold."""

    def test_a_constant_column_is_divided_by_one_and_the_boundary_is_strict(self) -> None:
        """Column 0 is constant, so its std is 0. Dividing by that std is inf, and inf is how a
        harmless constant column used to look like a blowup. Column 1 has population std sqrt(2).
        z == 5 and z == 10 must not count; the next row, which exceeds both, counts once.
        """
        ref = np.array(
            [
                [0.0, 10.0],
                [0.0, 10.0],
                [0.0, 12.0],
                [0.0, 8.0],
            ]
        )
        scale = math.sqrt(2.0)
        probe = np.array(
            [
                [3.0, 10.0],
                [0.0, 10.0 + scale * 5.0],
                [6.0, 10.0 + scale * 10.0],
                [11.0, 10.0 + scale * 11.0],
            ]
        )
        stats = cv._z_against(ref, probe)
        self.assertTrue(math.isfinite(stats["max_abs_z"]))
        self.assertEqual(stats["max_abs_z"], 11.0)
        self.assertEqual(stats["frac_rows_any_gt5"], 0.5)
        self.assertEqual(stats["frac_rows_any_gt10"], 0.25)
        # The constant column's offset of 3 survived as 3, which is |probe - mean| / 1.
        self.assertEqual(stats["p99_abs_z"], 11.0)

    def test_p99_is_not_the_max_and_a_single_outlier_row_counts_once(self) -> None:
        ref = np.zeros((100, 1))
        probe = np.zeros((100, 1))
        probe[-1, 0] = 100.0
        stats = cv._z_against(ref, probe)
        self.assertEqual(stats["max_abs_z"], 100.0)
        # Linear interpolation of one 100 among 99 zeros. Exact equality loses a ulp;
        # a max- or nearest-percentile rewrite lands on 100 or 0, not on 1.
        self.assertAlmostEqual(stats["p99_abs_z"], 1.0, places=6)
        self.assertEqual(stats["frac_rows_any_gt5"], 0.01)
        self.assertEqual(stats["frac_rows_any_gt10"], 0.01)
        self.assertTrue(all(math.isfinite(v) for v in stats.values()))


class StatsTest(unittest.TestCase):
    def test_an_empty_vector_is_not_summarised_as_zeros(self) -> None:
        with self.assertRaises(ValueError):
            cv._stats(np.array([]))

    def test_a_constant_vector_reports_population_std_zero(self) -> None:
        self.assertEqual(cv._stats(np.array([2.0, 2.0, 2.0])), {"min": 2.0, "max": 2.0, "mean": 2.0, "std": 0.0})


class RenderMatrixTest(unittest.TestCase):
    def _cells(self, table: str) -> list[list[str]]:
        rows = []
        for line in table.splitlines():
            if not line.startswith("|") or line.startswith("| ---") or line.startswith("| readout"):
                continue
            rows.append([cell.strip() for cell in line.split("|")[1:-1]])
        return rows

    def test_an_error_cell_is_not_a_number_and_needs_no_aggregate(self) -> None:
        table = cv.render_matrix(
            [
                {
                    "readout": "linear",
                    "ridge": 0.0,
                    "normalize": True,
                    "theta": "configured",
                    "error": "LinAlgError: singular",
                }
            ]
        )
        (row,) = self._cells(table)
        self.assertEqual(row[0], "linear")
        self.assertEqual(row[2], "on")
        self.assertEqual(row[4], "ERROR")
        self.assertEqual(row[5:9], ["", "", "", ""])
        self.assertEqual(row[9], "LinAlgError: singular")
        self.assertNotIn("+", row[4])

    def test_a_zero_gamma_is_printed_and_a_string_ridge_stays_a_string(self) -> None:
        table = cv.render_matrix(
            [
                {
                    "readout": "rff",
                    "ridge": "gcv",
                    "normalize": False,
                    "theta": "fold-resolved",
                    "folds": [
                        {
                            "eval_metrics": {"r2": -1.5},
                            "train_metrics": {"r2": 0.125},
                            "theta_resolved": 12.34,
                            "ridge_resolved": "gcv",
                            "gamma_resolved": None,
                            "memory_z_eval_vs_train": {"max_abs_z": 20.4},
                        }
                    ],
                    "eval_aggregate": {"r2": -1.5, "rmse": 0.2},
                },
                {
                    "readout": "rff",
                    "ridge": 0.0,
                    "normalize": False,
                    "theta": "configured",
                    "folds": [
                        {
                            "eval_metrics": {"r2": 0.25},
                            "train_metrics": {"r2": 0.5},
                            "theta_resolved": 1.0,
                            "ridge_resolved": 0.0,
                            "gamma_resolved": 0.0,
                            "memory_z_eval_vs_train": {"max_abs_z": 3.2},
                        }
                    ],
                    "eval_aggregate": {"r2": 0.25, "rmse": 0.1},
                },
            ]
        )
        gcv, zero = self._cells(table)
        self.assertEqual(gcv[2], "off")
        self.assertIn("gcv", gcv[9])
        self.assertNotIn("γ", gcv[9])
        self.assertIn("-1.50", gcv[4])
        self.assertIn("/γ0", zero[9])
        self.assertEqual(gcv[10], "20")


class FoldTableTest(unittest.TestCase):
    def test_a_complete_payload_keeps_the_sign_and_a_missing_aggregate_is_nan(self) -> None:
        fold = {
            "fold": 0,
            "train_metrics": {"r2": 0.5, "rmse": 0.01},
            "eval_metrics": {"r2": -83452.44, "rmse": 1.2, "mae": 0.3},
        }
        rendered = cv.fold_table({"folds": [fold], "eval_aggregate": {"r2": -83452.44, "rmse": 1.2, "mae": 0.3}, "eval_std": {"r2": 12.0}})
        self.assertIn("| 0 | +0.5000 | 0.01000 | -83452.4 | 1.20000 | 0.30000 |", rendered)
        self.assertIn("**-83452.4**", rendered)

        missing = cv.fold_table({"folds": [fold]})
        # The r2 format forces a sign, so a missing aggregate is "+nan", not a zero and not an unsigned nan.
        self.assertIn("**+nan**", missing)
        self.assertIn("(std nan)", missing)
        self.assertNotIn("**+0.0", missing)
        self.assertNotIn("**-0.0", missing)

    def test_a_fold_missing_its_metrics_raises(self) -> None:
        with self.assertRaises(KeyError):
            cv.fold_table({"folds": [{"fold": 0, "train_metrics": {"r2": 1.0, "rmse": 1.0}}]})


class HttpAndCreateTest(unittest.TestCase):
    def test_success_empty_and_error_bodies(self) -> None:
        seen: dict = {}

        def urlopen(req, timeout=None):
            seen["method"] = req.get_method()
            seen["url"] = req.full_url
            seen["data"] = req.data
            seen["timeout"] = timeout
            seen["content_type"] = req.get_header("Content-type")
            kind = seen["kind"]
            if kind == "json":
                return _Body(200, b'{"ok": true}')
            if kind == "empty":
                return _Body(200, b"")
            if kind == "http-json":
                raise _http_error(422, b'{"detail": "no"}')
            if kind == "http-text":
                raise _http_error(500, b"<html>down</html>")
            raise AssertionError(kind)

        with mock.patch.object(cv.urllib.request, "urlopen", urlopen):
            seen["kind"] = "json"
            self.assertEqual(cv.http_json("PUT", "http://127.0.0.1:9/v1/x", {"a": 1}, timeout=3.5), (200, {"ok": True}))
            self.assertEqual(seen["method"], "PUT")
            self.assertEqual(seen["timeout"], 3.5)
            self.assertEqual(json.loads(seen["data"]), {"a": 1})
            self.assertEqual(seen["content_type"], "application/json")

            seen["kind"] = "empty"
            self.assertEqual(cv.http_json("GET", "http://127.0.0.1:9/v1/health"), (200, None))
            self.assertIsNone(seen["data"])

            seen["kind"] = "http-json"
            self.assertEqual(cv.http_json("GET", "http://127.0.0.1:9/v1/x"), (422, {"detail": "no"}))

            seen["kind"] = "http-text"
            self.assertEqual(cv.http_json("GET", "http://127.0.0.1:9/v1/x"), (500, "<html>down</html>"))

    def test_create_dataset_persists_and_refuses_a_body_with_no_id(self) -> None:
        params = {"symbols": ["AAPL"]}
        scripted = [
            (201, b'{"dataset_id": "equities_seq-ok", "meta": {}}'),
            (200, b'{"meta": {}}'),
            (200, b'{"dataset_id": ""}'),
            (200, b'["not-a-dataset"]'),
            (503, b'{"detail": "busy"}'),
        ]
        calls: list[dict] = []

        def urlopen(req, timeout=None):
            calls.append(
                {
                    "url": req.full_url,
                    "data": json.loads(req.data),
                    "timeout": timeout,
                    "method": req.get_method(),
                }
            )
            status, body = scripted[len(calls) - 1]
            if status >= 400:
                raise _http_error(status, body)
            return _Body(status, body)

        with mock.patch.object(cv.urllib.request, "urlopen", urlopen):
            created = cv.create_dataset("http://127.0.0.1:8110", params)
            self.assertEqual(created["dataset_id"], "equities_seq-ok")
            messages = []
            for _ in scripted[1:]:
                with self.assertRaises(SystemExit) as ctx:
                    cv.create_dataset("http://127.0.0.1:8110", params)
                messages.append(str(ctx.exception))

        self.assertEqual([m for m in messages if "POST /v1/datasets -> HTTP" not in m], [])
        self.assertIn("HTTP 200", messages[0])
        self.assertIn("HTTP 200", messages[1])
        self.assertIn("HTTP 200", messages[2])
        self.assertIn("HTTP 503", messages[3])
        self.assertNotIn("equities_seq-ok", "".join(messages))
        self.assertEqual(len(calls), 5)
        for call in calls:
            self.assertEqual(call["method"], "POST")
            self.assertEqual(call["url"], "http://127.0.0.1:8110/v1/datasets")
            self.assertEqual(call["timeout"], 900.0)
            self.assertEqual(
                call["data"],
                {"generator": "equities_seq", "params": params, "persist": True},
            )


if __name__ == "__main__":
    unittest.main()
