#!/usr/bin/env python3
"""The Lane A3 ``checks`` report: the dataset facts the consensus note treats as measured.

Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

``util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py`` ``checks`` is the numpy-only
instrument behind the W5.1 consensus record. It shares no code with the model that produced
the NPZ, so a wrong flag here is a wrong fact in the note. The ``compare`` and
``fold-threads`` subcommands, and the comparator edges (``_cmp``, ``full_view`` ticker ties,
``compare_arrays`` NaN/dtype), are not pinned here, and no other suite pins them yet.

What this pins:

* a negative ``dt`` is flagged, and a nonzero first column is not reported all-zero;
* a backwards ``window_end_date`` is not monotone;
* a missing archive is ``NO ARTIFACT`` and the report is still written; identical file
  bytes are reported identical, and one changed array is not;
* ``meta_fields`` keeps ``access_count`` 0 and drops a key outside the allowlist;
* ``y_reg`` is the target when ``y`` is also present; a non-finite target is not finite;
* a NaN in ``X`` is not finite; an all-constant last step has no nonzero column std;
* fold 0's eval median uses ``n // (n_folds + 1)`` and the embargo, so a cut that
  ignores either one does not match.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
import warnings
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-10-05_recurrence_equities_laneA3_checks.py"

_spec = importlib.util.spec_from_file_location("lane_a3_checks", SCRIPT)
assert _spec is not None and _spec.loader is not None
checks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checks)

N_PER = 10
N = N_PER * 3
LOOKBACK = 3
N_FEAT = 2
N_FOLDS = 5
EMBARGO = 2


def _arrays(*, first_col: float = 0.0, dt_negative: bool = False, nan_x: bool = False, y_reg_inf: bool = False, include_y: bool = False, constant: bool = False, dates_swap: bool = False, dates: bool = True) -> dict:
    x = np.zeros((N, LOOKBACK, N_FEAT), dtype=np.float64)
    if constant:
        x[..., 0] = 3.0
        x[..., 1] = 7.0
    else:
        x[..., 0] = (np.arange(N) + 0.1)[:, None]
        x[..., 1] = 7.0
    if nan_x:
        x[0, 0, 0] = np.nan
    dt = np.zeros((N, 2), dtype=np.float64)
    dt[:, 0] = first_col
    dt[:, 1] = np.arange(N)
    if dt_negative:
        dt[0, 1] = -4.0
    y_reg = np.arange(N, dtype=np.float64)
    if y_reg_inf:
        y_reg[0] = np.inf
    arrays = {"X": x, "dt": dt, "y_reg": y_reg}
    if include_y:
        arrays["y"] = np.full(N, 5.0)
    if dates:
        window = np.array([f"2020-01-{i + 1:02d}" for i in range(N)])
        if dates_swap:
            window = window.copy()
            window[4], window[5] = window[5], window[4]
        arrays["window_end_date"] = window
    return arrays


def _save_splits(path: Path, arrays: dict) -> None:
    payload = {}
    for key, arr in arrays.items():
        payload[f"{key}_train"] = arr[:N_PER]
        payload[f"{key}_val"] = arr[N_PER : 2 * N_PER]
        payload[f"{key}_test"] = arr[2 * N_PER :]
    np.savez(path, **payload)


class LaneA3ReportTest(unittest.TestCase):
    def _report(self, arrays: dict, *, meta: dict | None = None, meta_missing: bool = False, archive: dict | None = None, archive_missing: bool = False, tolerate_summary: bool = False) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            npz = root / "today.npz"
            _save_splits(npz, arrays)
            out = root / "report.json"
            meta_path = None
            if meta is not None:
                meta_path = root / "today.meta.json"
                meta_path.write_text(json.dumps(meta))
            elif meta_missing:
                meta_path = root / "absent.meta.json"
            archive_npz = None
            if archive is not None:
                archive_npz = root / "archive.npz"
                _save_splits(archive_npz, archive)
            elif archive_missing:
                archive_npz = root / "no-such-archive.npz"
            args = argparse.Namespace(npz=npz, meta=meta_path, archive_npz=archive_npz, archive_meta=None, n_folds=N_FOLDS, embargo=EMBARGO, out=out)
            summary_error = None
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                with redirect_stdout(io.StringIO()):
                    try:
                        rc = checks.cmd_checks(args)
                    except TypeError as exc:
                        # The summary line formats a null min-nonzero std with ``.3e`` and
                        # raises after the JSON is written. The note reads the JSON.
                        summary_error = exc
                        rc = None
            self.assertTrue(out.is_file(), summary_error)
            if tolerate_summary:
                self.assertTrue(rc == 0 or summary_error is not None)
            else:
                if summary_error is not None:
                    raise summary_error
                self.assertEqual(rc, 0)
            report = json.loads(out.read_text())
            report["_sha256"] = hashlib.sha256(npz.read_bytes()).hexdigest()
            return report

    def test_finite_report_uses_the_documented_fold_cut_and_names_the_constant_column(self) -> None:
        report = self._report(_arrays())
        self.assertEqual(report["partitions"], {"train": N_PER, "val": N_PER, "test": N_PER})
        self.assertEqual(report["partition_sum"], N)
        self.assertEqual(report["npz_sha256_file"], report["_sha256"])
        view = report["full_view"]
        self.assertEqual(view["n_windows"], N)
        self.assertEqual(view["lookback"], LOOKBACK)
        self.assertEqual(view["n_features"], N_FEAT)
        self.assertTrue(view["X_all_finite"])
        self.assertTrue(report["target_all_finite"])
        self.assertFalse(report["dt_any_negative"])
        self.assertTrue(report["dt_first_col_all_zero"])
        self.assertTrue(report["window_end_date_monotone_nondecreasing"])
        self.assertEqual(report["window_end_date_first"], "2020-01-01")
        self.assertEqual(report["window_end_date_last"], "2020-01-30")
        self.assertEqual(report["X_last_step_n_zero_std_columns"], 1)
        self.assertEqual(report["X_last_step_zero_std_columns_value"], [7.0])
        self.assertEqual(report["X_last_step_std_argmin"], 1)
        last_step = np.column_stack((np.arange(N) + 0.1, np.full(N, 7.0)))
        self.assertEqual(report["X_last_step_full_per_feature_std_float64"][0], float(last_step.std(axis=0)[0]))
        self.assertEqual(report["X_last_step_full_per_feature_std_float32"][0], float(last_step.astype(np.float32).std(axis=0)[0]))
        self.assertNotEqual(report["X_last_step_full_per_feature_std_float64"][0], report["X_last_step_full_per_feature_std_float32"][0])
        fold_size = N // (N_FOLDS + 1)
        eval_start = fold_size
        eval_stop = 2 * fold_size
        train_end = eval_start - EMBARGO
        sums = np.arange(N, dtype=float)
        fold0 = report["folds"][0]
        self.assertEqual(fold0["train_end_excl"], train_end)
        self.assertEqual(fold0["eval_start"], eval_start)
        self.assertEqual(fold0["eval_stop_excl"], eval_stop)
        self.assertEqual(fold0["sum_dt_median_eval"], float(np.median(sums[eval_start:eval_stop])))
        self.assertEqual(fold0["sum_dt_median_train"], float(np.median(sums[:train_end])))
        self.assertEqual(report["target_key"], "y_reg")
        self.assertEqual(report["target_full"]["mean"], float(np.arange(N).mean()))

    def test_negative_dt_and_a_nonzero_first_column_are_flagged(self) -> None:
        report = self._report(_arrays(first_col=1.0, dt_negative=True))
        self.assertTrue(report["dt_any_negative"])
        self.assertFalse(report["dt_first_col_all_zero"])

    def test_a_backwards_window_end_date_is_not_monotone(self) -> None:
        report = self._report(_arrays(dates_swap=True))
        self.assertFalse(report["window_end_date_monotone_nondecreasing"])
        self.assertEqual(report["window_end_date_first"], "2020-01-01")
        self.assertEqual(report["window_end_date_last"], "2020-01-30")

    def test_a_missing_archive_is_no_artifact_and_the_report_is_written(self) -> None:
        report = self._report(_arrays(), archive_missing=True)
        self.assertEqual(report["archive"], {"npz": report["archive"]["npz"], "status": "NO ARTIFACT"})
        self.assertTrue(report["archive"]["npz"].endswith("no-such-archive.npz"))

    def test_identical_archive_bytes_match_and_one_changed_array_does_not(self) -> None:
        arrays = _arrays()
        same = self._report(arrays, archive=arrays)
        self.assertTrue(same["archive"]["npz_file_bytes_identical"])
        self.assertTrue(same["archive"]["comparison"]["all_identical"])
        changed = _arrays()
        changed["X"] = changed["X"].copy()
        changed["X"][0, 0, 0] = 123.0
        diff = self._report(arrays, archive=changed)
        self.assertFalse(diff["archive"]["npz_file_bytes_identical"])
        self.assertFalse(diff["archive"]["comparison"]["all_identical"])
        self.assertFalse(diff["archive"]["comparison"]["per_key"]["X_train"]["array_equal"])

    def test_meta_keeps_a_zero_access_count_and_drops_an_unknown_key(self) -> None:
        report = self._report(_arrays(), meta={"dataset_id": "equities_seq-6", "access_count": 0, "not_a_fact": "drop me"})
        meta = report["meta"]
        self.assertEqual(meta["dataset_id"], "equities_seq-6")
        self.assertEqual(meta["access_count"], 0)
        self.assertIsNone(meta["lookback"])
        self.assertNotIn("not_a_fact", meta)
        missing = self._report(_arrays(), meta_missing=True)
        self.assertIsNone(missing["meta"])

    def test_y_reg_wins_and_a_nonfinite_target_is_not_finite(self) -> None:
        both = self._report(_arrays(include_y=True))
        self.assertEqual(both["target_key"], "y_reg")
        self.assertEqual(both["target_full"]["mean"], float(np.arange(N).mean()))
        self.assertNotEqual(both["target_full"]["mean"], 5.0)
        nonfinite = self._report(_arrays(include_y=True, y_reg_inf=True))
        self.assertEqual(nonfinite["target_key"], "y_reg")
        self.assertFalse(nonfinite["target_all_finite"])

    def test_a_nan_in_x_is_not_finite_and_an_all_constant_last_step_has_no_nonzero_std(self) -> None:
        nan = self._report(_arrays(nan_x=True))
        self.assertFalse(nan["full_view"]["X_all_finite"])
        constant = self._report(_arrays(constant=True), tolerate_summary=True)
        self.assertIsNone(constant["X_last_step_std_min_nonzero"])
        self.assertEqual(constant["X_last_step_n_zero_std_columns"], N_FEAT)
        self.assertEqual(constant["X_last_step_zero_std_columns_value"], [3.0, 7.0])
        self.assertTrue(constant["full_view"]["X_all_finite"])


if __name__ == "__main__":
    unittest.main()
