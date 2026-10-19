#!/usr/bin/env python3
"""Apply the W5.2 service half to a juniper-recurrence tree (exact-string edits + two new files).

Project: juniper-ml
Sub-Project: recurrence x equities (plan W5.2, service half; recurrence 0.8.0)
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc, single-use (kept for the record of exactly what the service PR changed)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (W5.2 row + Details);
         util/ad-hoc/2026-10-19_apply_w5_2_model.py (the model half, model 0.6.0, which the floor requires)

Usage:
    python3 util/ad-hoc/2026-10-19_apply_w5_2_service.py --root <juniper-recurrence checkout> [--check]

What changes:

* ``juniper_recurrence/_folds.py`` (new) -- ``build_folds``: the CV pool is the ``trainval`` view; folds
  come from model-core's ``walk_forward_folds`` with ``order=window_end_date`` and ``groups=ticker_code``
  when the artifact carries them; ``embargo`` defaults to the look-back (per entity); the
  label-availability rule (a train window whose ``window_end_date + target_dt`` reaches the cut is
  dropped) and an optional ``embargo_days`` gap are date-based post-filters. ``FoldingSpec`` records
  what was done and rides the response.
* ``schemas.py`` -- ``SplitName`` admits ``trainval``; ``CrossValRequest.embargo`` is optional,
  ``embargo_days`` added; ``CrossValFolding`` on ``CrossValResponse``.
* ``state.py`` / ``routers/crossval.py`` -- the folding block persisted and re-served.
* ``pyproject.toml`` / ``requirements.lock`` -- the model floor ``>=0.6.0,<0.7.0`` (the ``trainval`` view
  and the window keys live there).
* tests, README, CHANGELOG.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

EDITS: list[tuple[str, str, str]] = []
CREATE: dict[str, str] = {}


def edit(path: str, old: str, new: str) -> None:
    EDITS.append((path, old, new))


APP = "juniper-recurrence/"

# --- new module ----------------------------------------------------------------------------------

CREATE[APP + "juniper_recurrence/_folds.py"] = '''"""Fold construction for ``POST /v1/crossval`` (plan W5.2): chronological, entity-grouped, ``test``-free.

Before W5.2 the route cut row-index folds over the ``full`` view. On a panel artifact (several
tickers) that is wrong twice over: ``full`` is laid down entity-major (every window of ticker A, then
every window of ticker B), so a row-index cut puts ticker A's 2021 in train and ticker B's 2015 in
eval; and its last fold evaluates the ``test`` partition the plan reserves for one out-of-sample read
(W5.3). Here the pool is the composed ``trainval`` view, and when the artifact carries the per-window
keys ``juniper-recurrence-model`` 0.6.0 exposes -- ``window_end_date`` (a ``YYYYMMDD`` integer) and
``ticker_code`` -- the folds are cut on the **global date** through model-core's ``order=`` /
``groups=``: every entity's windows before the cut are train, after it eval, and the embargo purge is
applied **per entity** (its last ``embargo`` windows before the cut), which is what keeps one ticker's
look-back from straddling the boundary.

Three rules the plan sets, all encoded here:

* **``embargo`` is in windows and defaults to the look-back.** A window's input spans its last
  ``lookback`` steps, so a smaller gap lets an eval window's history overlap a train window's. An
  explicit smaller value is honoured (it is a methodological choice, and the E-G suite sweeps it) but
  logged at WARNING; the resolved value is on the response.
* **Label availability**: a train window whose label is not yet known at the cut -- its
  ``window_end_date + target_dt`` reaches the first eval day -- is dropped from train.
* **``embargo_days``** is a separately named *duration* gap: train windows ending within that many
  days before the cut are dropped as well.

A single-entity artifact (one ticker, or no keys at all) reduces to the row-index folds of before,
with the same per-window embargo. The dates are converted to day ordinals for the arithmetic;
``YYYYMMDD`` integers sort chronologically as they are, so the sort key needs no conversion.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from juniper_model_core.crossval import Fold, walk_forward_folds
from juniper_recurrence_model import SequenceData

__all__ = ["POOL_SPLIT", "FoldingSpec", "build_folds", "yyyymmdd_to_days"]

logger = logging.getLogger(__name__)

#: The split ``POST /v1/crossval`` selects over: train | val, never ``test`` (plan W5.2 / W5.3).
POOL_SPLIT = "trainval"


@dataclass(frozen=True)
class FoldingSpec:
    """How the folds were built -- the record the response carries (``CrossValFolding``)."""

    lookback: int
    embargo: int
    embargo_days: float | None
    grouped: bool
    ordered: bool
    n_entities: int | None
    n_folds: int
    dropped_label_availability: int
    dropped_embargo_days: int


def yyyymmdd_to_days(values: np.ndarray) -> np.ndarray:
    """``YYYYMMDD`` integers -> days since 1970-01-01 (``int64``), refusing anything that is not a calendar date."""
    v = np.asarray(values).astype(np.int64)
    year, month, day = v // 10000, (v // 100) % 100, v % 100
    if v.size and bool(np.any((year < 1900) | (year > 2200) | (month < 1) | (month > 12) | (day < 1) | (day > 31))):
        raise ValueError("window_end_date must hold YYYYMMDD calendar dates (e.g. 20150406)")
    months = (year - 1970).astype("datetime64[Y]").astype("datetime64[M]") + (month - 1).astype("timedelta64[M]")
    dates = months.astype("datetime64[D]") + (day - 1).astype("timedelta64[D]")
    if v.size and bool(np.any(dates.astype("datetime64[M]") != months)):
        raise ValueError("window_end_date holds a day that does not exist in its month (e.g. 20200230)")
    return dates.astype(np.int64)


def build_folds(sequence: SequenceData, *, n_folds: int, scheme: str, embargo: int | None, min_train: int | None, embargo_days: float | None) -> tuple[list[Fold], FoldingSpec]:
    """Cut the walk-forward folds for ``sequence`` (the ``trainval`` pool) per the W5.2 rules.

    Raises ``ValueError`` (the route answers 422) when model-core refuses the configuration, when
    ``embargo_days`` is asked of an artifact with no ``window_end_date``, or when the date filters
    leave no fold with a training set.
    """
    n, lookback = int(sequence.X.shape[0]), int(sequence.X.shape[1])
    resolved_embargo = lookback if embargo is None else int(embargo)
    if embargo is not None and embargo < lookback:
        logger.warning("crossval embargo=%d is below the look-back of %d windows, so an eval window's history can overlap a train window's; omit embargo for the default of one look-back (plan W5.2)", embargo, lookback)
    order = sequence.window_end_date
    groups = sequence.ticker_code
    if embargo_days is not None and order is None:
        raise ValueError("embargo_days needs the artifact's window_end_date; this artifact has none (use embargo, in windows)")

    folds = walk_forward_folds(n, n_folds=n_folds, scheme=scheme, embargo=resolved_embargo, min_train=min_train, order=order, groups=groups)

    dropped_label = dropped_days = 0
    if order is not None:
        days = yyyymmdd_to_days(order)
        horizon = np.zeros(n, dtype=float) if sequence.target_dt is None else np.asarray(sequence.target_dt, dtype=float)
        kept: list[Fold] = []
        for fold in folds:
            train, ev = np.asarray(fold.train_idx), np.asarray(fold.eval_idx)
            cut = int(days[ev].min())  # the first eval day: the cut every entity shares
            keep = (days[train] + horizon[train]) < cut  # the label is known strictly before the cut
            dropped_label += int(np.sum(~keep))
            if embargo_days is not None:
                gap = days[train] < cut - float(embargo_days)
                dropped_days += int(np.sum(keep & ~gap))
                keep &= gap
            train = train[keep]
            if train.shape[0] < 1 or (scheme == "expanding" and min_train is not None and train.shape[0] < min_train):
                continue
            kept.append(Fold(train_idx=train, eval_idx=ev))
        if not kept:
            raise ValueError("no valid folds remain after the label-availability / embargo_days filters; reduce n_folds, embargo_days or min_train")
        folds = kept

    spec = FoldingSpec(
        lookback=lookback,
        embargo=resolved_embargo,
        embargo_days=None if embargo_days is None else float(embargo_days),
        grouped=groups is not None,
        ordered=order is not None,
        n_entities=None if groups is None else int(np.unique(groups).shape[0]),
        n_folds=len(folds),
        dropped_label_availability=dropped_label,
        dropped_embargo_days=dropped_days,
    )
    return folds, spec
'''

# --- new tests -----------------------------------------------------------------------------------

CREATE[APP + "tests/test_crossval_folds.py"] = '''"""W5.2: the fold builder behind ``POST /v1/crossval`` -- chronological, entity-grouped, label-aware.

The four tests the plan names (two tickers: no eval row precedes a train row in time; per-ticker
look-back non-overlap; label availability; ``test`` never in a fold -- the last one at the route,
``test_crossval_routes.py``) plus the date conversion, the embargo default and ``embargo_days``.
"""

from __future__ import annotations

import logging

import numpy as np
import pytest
from juniper_model_core.crossval import walk_forward_folds
from juniper_recurrence_model import SequenceData

from juniper_recurrence._folds import build_folds, yyyymmdd_to_days

LOOKBACK = 4


def _dates(start_days: int, n: int) -> np.ndarray:
    """``n`` consecutive calendar days from ``start_days`` (days since 1970), as YYYYMMDD int32."""
    days = (np.datetime64("1970-01-01") + np.arange(start_days, start_days + n).astype("timedelta64[D]")).astype("datetime64[D]")
    ymd = [(int(str(d)[0:4]) * 10000 + int(str(d)[5:7]) * 100 + int(str(d)[8:10])) for d in days]
    return np.asarray(ymd, dtype=np.int32)


def _panel(n_per_ticker: int = 30, tickers: int = 2, horizon: int = 1, keys: bool = True) -> SequenceData:
    """An entity-major two-ticker pool: ticker 0's windows (consecutive days), then ticker 1's (same days)."""
    rng = np.random.default_rng(0)
    n = n_per_ticker * tickers
    x = rng.standard_normal((n, LOOKBACK, 2)).astype("float32")
    y = rng.standard_normal((n, 1)).astype("float32")
    dt = np.zeros((n, LOOKBACK), dtype="float32")
    dt[:, 1:] = 1.0
    target_dt = np.full(n, float(horizon), dtype="float32")
    ticker = np.repeat(np.arange(tickers), n_per_ticker).astype(np.int32)
    dates = np.tile(_dates(18000, n_per_ticker), tickers)
    return SequenceData(X=x, y=y, dt=dt, target_dt=target_dt, ticker_code=ticker if keys else None, window_end_date=dates if keys else None)


def test_yyyymmdd_to_days_is_exact_and_ordered():
    days = yyyymmdd_to_days(np.array([20191231, 20200101, 20200229, 20200301], dtype=np.int32))
    assert np.array_equal(np.diff(days), [1, 59, 1])  # a leap year, counted
    assert days[0] == (np.datetime64("2019-12-31") - np.datetime64("1970-01-01")).astype(int)


@pytest.mark.parametrize("bad", [20200230, 20201301, 1234, 20200100])
def test_yyyymmdd_to_days_refuses_a_non_date(bad):
    with pytest.raises(ValueError, match="window_end_date"):
        yyyymmdd_to_days(np.array([20200101, bad], dtype=np.int32))


def test_two_tickers_no_eval_row_precedes_a_train_row_in_time():
    seq = _panel()
    folds, spec = build_folds(seq, n_folds=3, scheme="expanding", embargo=None, min_train=None, embargo_days=None)
    days = yyyymmdd_to_days(seq.window_end_date)
    assert spec.grouped and spec.ordered and spec.n_entities == 2 and spec.embargo == LOOKBACK
    for fold in folds:
        assert days[fold.train_idx].max() < days[fold.eval_idx].min()
        # Both tickers sit on both sides of every cut: the cut is a date, not a row position.
        assert set(seq.ticker_code[fold.train_idx].tolist()) == {0, 1} == set(seq.ticker_code[fold.eval_idx].tolist())


def test_per_ticker_lookback_windows_never_overlap_across_the_boundary():
    seq = _panel()
    folds, _ = build_folds(seq, n_folds=3, scheme="expanding", embargo=None, min_train=None, embargo_days=None)
    days = yyyymmdd_to_days(seq.window_end_date)
    for fold in folds:
        for ticker in (0, 1):
            train_end = days[fold.train_idx][seq.ticker_code[fold.train_idx] == ticker]
            eval_end = days[fold.eval_idx][seq.ticker_code[fold.eval_idx] == ticker]
            if train_end.size and eval_end.size:
                # An eval window's input spans [end - (LOOKBACK - 1), end]; no train window's span may touch it.
                assert train_end.max() < eval_end.min() - (LOOKBACK - 1)


def test_a_train_window_whose_label_crosses_the_cut_is_excluded():
    seq = _panel(horizon=3)
    folds, spec = build_folds(seq, n_folds=3, scheme="expanding", embargo=0, min_train=None, embargo_days=None)
    days = yyyymmdd_to_days(seq.window_end_date)
    assert spec.dropped_label_availability > 0  # with no window embargo, only this rule stands between the horizon and the cut
    for fold in folds:
        cut = days[fold.eval_idx].min()
        assert np.all(days[fold.train_idx] + seq.target_dt[fold.train_idx] < cut)


def test_embargo_days_drops_train_windows_inside_the_gap():
    seq = _panel()
    folds, spec = build_folds(seq, n_folds=3, scheme="expanding", embargo=0, min_train=None, embargo_days=5.0)
    days = yyyymmdd_to_days(seq.window_end_date)
    assert spec.embargo_days == 5.0 and spec.dropped_embargo_days > 0
    for fold in folds:
        assert days[fold.train_idx].max() < days[fold.eval_idx].min() - 5.0


def test_embargo_days_needs_dates():
    with pytest.raises(ValueError, match="embargo_days needs"):
        build_folds(_panel(keys=False), n_folds=3, scheme="expanding", embargo=None, min_train=None, embargo_days=2.0)


def test_an_explicit_embargo_below_the_lookback_is_honoured_and_logged(caplog):
    seq = _panel()
    with caplog.at_level(logging.WARNING, logger="juniper_recurrence._folds"):
        _, spec = build_folds(seq, n_folds=3, scheme="expanding", embargo=1, min_train=None, embargo_days=None)
    assert spec.embargo == 1
    assert "below the look-back" in caplog.text


def test_a_keyless_single_series_reduces_to_the_row_index_folds():
    seq = _panel(tickers=1, keys=False)
    folds, spec = build_folds(seq, n_folds=3, scheme="expanding", embargo=None, min_train=None, embargo_days=None)
    expected = walk_forward_folds(seq.X.shape[0], n_folds=3, scheme="expanding", embargo=LOOKBACK)
    assert not spec.grouped and not spec.ordered and spec.n_entities is None
    assert [f.train_idx.tolist() for f in folds] == [f.train_idx.tolist() for f in expected]
    assert [f.eval_idx.tolist() for f in folds] == [f.eval_idx.tolist() for f in expected]


def test_filters_that_empty_every_fold_are_refused():
    with pytest.raises(ValueError, match="no valid folds remain"):
        build_folds(_panel(n_per_ticker=12), n_folds=2, scheme="expanding", embargo=0, min_train=None, embargo_days=365.0)
'''

# --- schemas -------------------------------------------------------------------------------------

S = APP + "juniper_recurrence/schemas.py"

edit(
    S,
    """SplitName = Literal["train", "val", "test", "full"]
""",
    """SplitName = Literal["train", "val", "test", "full", "trainval"]
""",
)

edit(
    S,
    """    dataset: DatasetRef
    n_folds: int = Field(ge=2)
    scheme: Literal["expanding", "rolling"] = "expanding"
    embargo: int = Field(default=0, ge=0)
    min_train: int | None = Field(default=None, ge=1)
    d: int | None = Field(default=None, ge=1)
""",
    """    dataset: DatasetRef
    n_folds: int = Field(ge=2)
    scheme: Literal["expanding", "rolling"] = "expanding"
    # W5.2: ``embargo`` is in windows, applied per entity, and ``None`` means one look-back -- the
    # default that keeps an eval window's history clear of every train window. ``embargo_days`` is a
    # separately named duration gap on top (needs the artifact's ``window_end_date``).
    embargo: int | None = Field(default=None, ge=0)
    embargo_days: float | None = Field(default=None, ge=0)
    min_train: int | None = Field(default=None, ge=1)
    d: int | None = Field(default=None, ge=1)
""",
)

edit(
    S,
    """class CrossValResponse(BaseModel):
    \"\"\"``POST /v1/crossval`` result: per-fold detail + per-metric mean / std aggregates.\"\"\"

    task_type: str
    n_folds: int
    folds: list[CrossValFoldModel]
    eval_aggregate: dict[str, float]
    eval_std: dict[str, float]
    dataset: DatasetDescriptor
""",
    """class CrossValFolding(BaseModel):
    \"\"\"How the folds were cut (W5.2): the pool is the ``trainval`` view (``dataset.split``), and this says the rest.

    ``embargo`` is the resolved per-entity window gap (the look-back when the request omitted it);
    ``grouped`` / ``ordered`` say whether the artifact's ``ticker_code`` / ``window_end_date`` cut the
    folds (a keyless single series is row-indexed); the two ``dropped_*`` counts are the train windows
    the label-availability rule and ``embargo_days`` removed across all folds.
    \"\"\"

    lookback: int
    embargo: int
    embargo_days: float | None = None
    grouped: bool
    ordered: bool
    n_entities: int | None = None
    n_folds: int
    dropped_label_availability: int
    dropped_embargo_days: int


class CrossValResponse(BaseModel):
    \"\"\"``POST /v1/crossval`` result: per-fold detail + per-metric mean / std aggregates.\"\"\"

    task_type: str
    n_folds: int
    folds: list[CrossValFoldModel]
    eval_aggregate: dict[str, float]
    eval_std: dict[str, float]
    dataset: DatasetDescriptor
    folding: CrossValFolding
""",
)

# --- state ---------------------------------------------------------------------------------------

ST = APP + "juniper_recurrence/state.py"

edit(
    ST,
    """    from juniper_recurrence.schemas import DatasetDescriptor, ReadoutDiagnostics
""",
    """    from juniper_recurrence.schemas import CrossValFolding, DatasetDescriptor, ReadoutDiagnostics
""",
)

edit(
    ST,
    """        self._crossval_diagnostics: list[ReadoutDiagnostics] = []
""",
    """        self._crossval_diagnostics: list[ReadoutDiagnostics] = []
        self._crossval_folding: CrossValFolding | None = None
""",
)

edit(
    ST,
    """    def set_crossval(self, result: CrossValResult, dataset: DatasetDescriptor, diagnostics: list[ReadoutDiagnostics]) -> None:
        \"\"\"Publish a completed cross-validation run. Sets ``_crossval_result`` last (publish-the-pointer-last).

        ``diagnostics`` is one :class:`~juniper_recurrence.schemas.ReadoutDiagnostics` per fold, in
        ``result.folds`` order (W5.10); the status route re-serves it with the result.
        \"\"\"
        self._crossval_dataset = dataset
        self._crossval_diagnostics = list(diagnostics)
        self._crossval_result = result  # published last

    def crossval_status(self) -> tuple[str, CrossValResult | None, DatasetDescriptor | None, list[ReadoutDiagnostics]]:
        \"\"\"``("idle"|"done", last_result, dataset, per_fold_diagnostics)`` for ``GET /v1/crossval/status``.\"\"\"
        if self._crossval_result is None:
            return ("idle", None, None, [])
        return ("done", self._crossval_result, self._crossval_dataset, self._crossval_diagnostics)
""",
    """    def set_crossval(self, result: CrossValResult, dataset: DatasetDescriptor, diagnostics: list[ReadoutDiagnostics], folding: CrossValFolding) -> None:
        \"\"\"Publish a completed cross-validation run. Sets ``_crossval_result`` last (publish-the-pointer-last).

        ``diagnostics`` is one :class:`~juniper_recurrence.schemas.ReadoutDiagnostics` per fold, in
        ``result.folds`` order (W5.10); ``folding`` is how the folds were cut (W5.2); the status route
        re-serves both with the result.
        \"\"\"
        self._crossval_dataset = dataset
        self._crossval_diagnostics = list(diagnostics)
        self._crossval_folding = folding
        self._crossval_result = result  # published last

    def crossval_status(self) -> tuple[str, CrossValResult | None, DatasetDescriptor | None, list[ReadoutDiagnostics], CrossValFolding | None]:
        \"\"\"``("idle"|"done", last_result, dataset, per_fold_diagnostics, folding)`` for ``GET /v1/crossval/status``.\"\"\"
        if self._crossval_result is None:
            return ("idle", None, None, [], None)
        return ("done", self._crossval_result, self._crossval_dataset, self._crossval_diagnostics, self._crossval_folding)
""",
)

# --- route ---------------------------------------------------------------------------------------

R = APP + "juniper_recurrence/routers/crossval.py"

edit(
    R,
    """is the one seam that sees the model, so the route captures it there.
\"\"\"
""",
    """is the one seam that sees the model, so the route captures it there.

W5.2 (entity-grouped chronological CV): the pool is the ``trainval`` view (never ``test``), and
``juniper_recurrence._folds.build_folds`` cuts the folds on the global ``window_end_date`` with a
per-entity embargo that defaults to the look-back, dropping train windows whose label crosses the
cut; the ``folding`` block on the response says what was done.
\"\"\"
""",
)

edit(
    R,
    """from juniper_model_core.crossval import CrossValResult, cross_validate, walk_forward_folds
from juniper_recurrence_model import LMURegressor

from juniper_recurrence import metrics
from juniper_recurrence._readout import build_lmu_regressor, readout_diagnostics
from juniper_recurrence.data import load_sequence_data
from juniper_recurrence.routers._common import get_settings, get_state, map_data_error
from juniper_recurrence.schemas import CrossValFoldModel, CrossValRequest, CrossValResponse, CrossValStatusResponse, DatasetDescriptor, ReadoutDiagnostics
""",
    """from juniper_model_core.crossval import CrossValResult, cross_validate
from juniper_recurrence_model import LMURegressor

from juniper_recurrence import metrics
from juniper_recurrence._folds import POOL_SPLIT, build_folds
from juniper_recurrence._readout import build_lmu_regressor, readout_diagnostics
from juniper_recurrence.data import load_sequence_data
from juniper_recurrence.routers._common import get_settings, get_state, map_data_error
from juniper_recurrence.schemas import CrossValFolding, CrossValFoldModel, CrossValRequest, CrossValResponse, CrossValStatusResponse, DatasetDescriptor, ReadoutDiagnostics
""",
)

edit(
    R,
    """def _to_response(result: CrossValResult, dataset: DatasetDescriptor, diagnostics: list[ReadoutDiagnostics]) -> CrossValResponse:
    \"\"\"Render a :class:`~juniper_model_core.crossval.CrossValResult` as the API response model.

    ``diagnostics`` is one block per fold in ``result.folds`` order (W5.10); the two are zipped by
    position and must agree in length.
    \"\"\"
""",
    """def _to_response(result: CrossValResult, dataset: DatasetDescriptor, diagnostics: list[ReadoutDiagnostics], folding: CrossValFolding) -> CrossValResponse:
    \"\"\"Render a :class:`~juniper_model_core.crossval.CrossValResult` as the API response model.

    ``diagnostics`` is one block per fold in ``result.folds`` order (W5.10); the two are zipped by
    position and must agree in length. ``folding`` is how the folds were cut (W5.2).
    \"\"\"
""",
)

edit(
    R,
    """        eval_std=result.eval_std,
        dataset=dataset,
    )
""",
    """        eval_std=result.eval_std,
        dataset=dataset,
        folding=folding,
    )
""",
)

edit(
    R,
    """    \"\"\"Synchronously cross-validate the LMU over walk-forward folds of the dataset's ``_full`` split.\"\"\"
""",
    """    \"\"\"Synchronously cross-validate the LMU over walk-forward folds of the dataset's ``trainval`` pool (W5.2).\"\"\"
""",
)

edit(
    R,
    """                split="full",  # CV always derives folds from the full chronological set (D-CV-4)
""",
    """                split=POOL_SPLIT,  # W5.2: train | val, entity-major; ``test`` is reserved for one out-of-sample read
""",
)

edit(
    R,
    """        try:
            folds = walk_forward_folds(
                sequence.X.shape[0],
                n_folds=req.n_folds,
                scheme=req.scheme,
                embargo=req.embargo,
                min_train=req.min_train,
            )
        except ValueError as exc:
            raise HTTPException(422, f"invalid cross-validation configuration: {exc}") from exc
""",
    """        try:
            folds, spec = build_folds(sequence, n_folds=req.n_folds, scheme=req.scheme, embargo=req.embargo, min_train=req.min_train, embargo_days=req.embargo_days)
        except ValueError as exc:
            raise HTTPException(422, f"invalid cross-validation configuration: {exc}") from exc
        folding = CrossValFolding(**spec.__dict__)
""",
)

edit(
    R,
    """        logger.info("cross-validation start: dataset=%s folds=%s scheme=%s d=%s theta=%s readout=%s", descriptor["dataset_id"], len(folds), req.scheme, d, theta, req.readout or "linear")
""",
    """        logger.info("cross-validation start: dataset=%s folds=%s scheme=%s d=%s theta=%s readout=%s", descriptor["dataset_id"], len(folds), req.scheme, d, theta, req.readout or "linear")
        logger.info("cross-validation folding: pool=%s lookback=%d embargo=%d embargo_days=%s grouped=%s ordered=%s n_entities=%s dropped_label_availability=%d dropped_embargo_days=%d", POOL_SPLIT, spec.lookback, spec.embargo, spec.embargo_days, spec.grouped, spec.ordered, spec.n_entities, spec.dropped_label_availability, spec.dropped_embargo_days)
""",
)

edit(
    R,
    """        state.set_crossval(result, dataset, diagnostics)
""",
    """        state.set_crossval(result, dataset, diagnostics, folding)
""",
)

edit(
    R,
    """        return _to_response(result, dataset, diagnostics)
    finally:
        state.crossval_lock.release()
""",
    """        return _to_response(result, dataset, diagnostics, folding)
    finally:
        state.crossval_lock.release()
""",
)

edit(
    R,
    """    state_name, result, dataset, diagnostics = state.crossval_status()
    return CrossValStatusResponse(
        state=state_name,
        result=_to_response(result, dataset, diagnostics) if result is not None and dataset is not None else None,
    )
""",
    """    state_name, result, dataset, diagnostics, folding = state.crossval_status()
    return CrossValStatusResponse(
        state=state_name,
        result=_to_response(result, dataset, diagnostics, folding) if result is not None and dataset is not None and folding is not None else None,
    )
""",
)

# --- existing tests --------------------------------------------------------------------------------

TR = APP + "tests/test_crossval_routes.py"

edit(
    TR,
    """def full_npz_arrays() -> dict[str, np.ndarray]:
    \"\"\"A contract-valid 3-D sequence NPZ mapping for the ``full`` split (20 windows).\"\"\"
    rng = np.random.default_rng(0)
    n_windows, lookback, n_features = 20, 5, 2
""",
    """def full_npz_arrays() -> dict[str, np.ndarray]:
    \"\"\"A contract-valid 3-D sequence NPZ mapping: a ``train`` partition of 40 windows (the ``trainval`` pool is train | val; with no ``val`` it is the train set).

    40 windows against a look-back of 5 leaves every one of three folds a training set under the
    W5.2 default embargo (one look-back): fold 0 trains on 10 − 5 rows.
    \"\"\"
    rng = np.random.default_rng(0)
    n_windows, lookback, n_features = 40, 5, 2
""",
)

edit(
    TR,
    """    return {
        "X_full": X,
        "y_reg_full": y,
        "dt_full": dt,
        "target_dt_full": target_dt,
        "seq_lengths_full": seq_lengths,
    }
""",
    """    return {
        "X_train": X,
        "y_reg_train": y,
        "dt_train": dt,
        "target_dt_train": target_dt,
        "seq_lengths_train": seq_lengths,
    }


@pytest.fixture
def three_partition_npz_arrays() -> dict[str, np.ndarray]:
    \"\"\"A two-ticker artifact with train / val / test partitions and the W5.2 keys, laid down split-major as juniper-data does.\"\"\"
    rng = np.random.default_rng(1)
    lookback, n_features = 5, 2
    counts = {"train": 24, "val": 8, "test": 8}
    out: dict[str, np.ndarray] = {}
    for split, per_ticker in counts.items():
        n = 2 * per_ticker
        out[f"X_{split}"] = rng.standard_normal((n, lookback, n_features)).astype("float32")
        dt = np.zeros((n, lookback), dtype="float32")
        dt[:, 1:] = 1.0
        out[f"dt_{split}"] = dt
        out[f"y_reg_{split}"] = rng.standard_normal((n,)).astype("float32")
        out[f"target_dt_{split}"] = np.ones((n,), dtype="float32")
        out[f"seq_lengths_{split}"] = np.full((n,), lookback, dtype="int64")
        out[f"ticker_code_{split}"] = np.repeat(np.array([0, 1], dtype=np.int32), per_ticker)
    # Consecutive YYYYMMDD days per ticker, train before val before test, the same calendar for both tickers.
    base = np.datetime64("2020-01-01")
    offset = 0
    for split, per_ticker in counts.items():
        days = (base + np.arange(offset, offset + per_ticker).astype("timedelta64[D]")).astype("datetime64[D]")
        ymd = np.asarray([int(str(d)[0:4]) * 10000 + int(str(d)[5:7]) * 100 + int(str(d)[8:10]) for d in days], dtype=np.int32)
        out[f"window_end_date_{split}"] = np.tile(ymd, 2)
        offset += per_ticker
    return out


@pytest.fixture
def fake_three_partition_data(monkeypatch, three_partition_npz_arrays) -> dict[str, np.ndarray]:
    class _FakeDataClient:
        def __init__(self, **kwargs) -> None:
            pass

        def get_latest(self, name):
            return {"dataset_id": f"latest-of-{name}"}

        def create_dataset(self, **kwargs):
            return {"dataset_id": "created-1"}

        def download_artifact_npz(self, dataset_id):
            return three_partition_npz_arrays

        def close(self) -> None:
            pass

    monkeypatch.setattr("juniper_recurrence.data.JuniperDataClient", _FakeDataClient)
    monkeypatch.setattr("juniper_recurrence.data.validate_npz_contract", lambda arrays, **kw: "sequence")
    return three_partition_npz_arrays
""",
)

edit(
    TR,
    """    # CV always operates on the full chronological split.
    assert body["dataset"]["split"] == "full"
    assert body["dataset"]["n_windows"] == 20
""",
    """    # CV selects over the trainval pool (W5.2); with no val partition that is the train set.
    assert body["dataset"]["split"] == "trainval"
    assert body["dataset"]["n_windows"] == 40
    assert body["folding"] == {"lookback": 5, "embargo": 5, "embargo_days": None, "grouped": False, "ordered": False, "n_entities": None, "n_folds": 3, "dropped_label_availability": 0, "dropped_embargo_days": 0}


def test_crossval_pool_excludes_test_and_cuts_a_panel_on_the_date(fake_three_partition_data):
    # W5.2 at the route: the pool is train | val (never test), both tickers' keys cut the folds, and the
    # response's folding block says so.
    arrays = fake_three_partition_data
    body = _client(api_keys=None).post("/v1/crossval", json={"dataset": {"dataset_id": "ds-1"}, "n_folds": 3, "d": 4}).json()
    assert body["dataset"]["split"] == "trainval"
    assert body["dataset"]["n_windows"] == arrays["X_train"].shape[0] + arrays["X_val"].shape[0]
    folding = body["folding"]
    assert folding["grouped"] is True and folding["ordered"] is True and folding["n_entities"] == 2
    assert folding["embargo"] == 5 and folding["n_folds"] == len(body["folds"]) >= 1
    assert folding["dropped_label_availability"] >= 0


def test_crossval_embargo_days_is_accepted_and_reported(fake_three_partition_data):
    body = _client(api_keys=None).post("/v1/crossval", json={"dataset": {"dataset_id": "ds-1"}, "n_folds": 2, "d": 4, "embargo": 0, "embargo_days": 2.5}).json()
    assert body["folding"]["embargo_days"] == 2.5 and body["folding"]["embargo"] == 0


def test_crossval_embargo_days_without_dates_422(fake_full_data):
    resp = _client(api_keys=None).post("/v1/crossval", json={"dataset": {"dataset_id": "ds-1"}, "n_folds": 2, "d": 4, "embargo_days": 2.0})
    assert resp.status_code == 422
    assert "embargo_days needs" in resp.text
""",
)

edit(
    TR,
    """    assert done["result"]["eval_aggregate"] == posted["eval_aggregate"]
    assert done["result"]["dataset"]["split"] == "full"
""",
    """    assert done["result"]["eval_aggregate"] == posted["eval_aggregate"]
    assert done["result"]["dataset"]["split"] == "trainval"
    assert done["result"]["folding"] == posted["folding"]
""",
)

TD = APP + "tests/test_readout_diagnostics.py"

edit(
    TD,
    """    rng = np.random.default_rng(0)
    n_windows, lookback, n_features = 20, 5, 2
    X = rng.standard_normal((n_windows, lookback, n_features)).astype("float32")
    dt = np.zeros((n_windows, lookback), dtype="float32")
    dt[:, 1:] = rng.uniform(0.5, 2.0, size=(n_windows, lookback - 1)).astype("float32")
    y = rng.standard_normal((n_windows,)).astype("float32")
    target_dt = rng.uniform(0.5, 2.0, size=(n_windows,)).astype("float32")
    seq_lengths = np.full((n_windows,), lookback, dtype="int64")
    return {"X_full": X, "y_reg_full": y, "dt_full": dt, "target_dt_full": target_dt, "seq_lengths_full": seq_lengths}
""",
    """    rng = np.random.default_rng(0)
    n_windows, lookback, n_features = 40, 5, 2  # 40 against a look-back of 5: three folds survive the W5.2 default embargo
    X = rng.standard_normal((n_windows, lookback, n_features)).astype("float32")
    dt = np.zeros((n_windows, lookback), dtype="float32")
    dt[:, 1:] = rng.uniform(0.5, 2.0, size=(n_windows, lookback - 1)).astype("float32")
    y = rng.standard_normal((n_windows,)).astype("float32")
    target_dt = rng.uniform(0.5, 2.0, size=(n_windows,)).astype("float32")
    seq_lengths = np.full((n_windows,), lookback, dtype="int64")
    return {"X_train": X, "y_reg_train": y, "dt_train": dt, "target_dt_train": target_dt, "seq_lengths_train": seq_lengths}
""",
)

edit(
    TD,
    """    body = _client(api_keys=None).post("/v1/crossval", json={"dataset": {"dataset_id": "ds-1"}, "n_folds": 3, "d": 4}).json()
    elapsed = np.sum(fake_full_data["dt_full"], axis=1)
    folds = walk_forward_folds(elapsed.shape[0], n_folds=3, scheme="expanding", embargo=0, min_train=None)
""",
    """    body = _client(api_keys=None).post("/v1/crossval", json={"dataset": {"dataset_id": "ds-1"}, "n_folds": 3, "d": 4, "embargo": 0}).json()
    elapsed = np.sum(fake_full_data["dt_train"], axis=1)
    folds = walk_forward_folds(elapsed.shape[0], n_folds=3, scheme="expanding", embargo=0, min_train=None)
""",
)

TS = APP + "tests/test_schemas_split.py"

edit(
    TS,
    """@pytest.mark.parametrize("split", ["train", "val", "test", "full"])
def test_the_four_contract_splits_validate(split):
""",
    """@pytest.mark.parametrize("split", ["train", "val", "test", "full", "trainval"])
def test_the_four_contract_splits_validate(split):
""",
)

edit(
    TS,
    """    assert schema["components"]["schemas"]["DatasetRef"]["properties"]["split"]["enum"] == ["train", "val", "test", "full"]
""",
    """    assert schema["components"]["schemas"]["DatasetRef"]["properties"]["split"]["enum"] == ["train", "val", "test", "full", "trainval"]  # trainval: the W5.2 CV pool
""",
)

# --- README / CHANGELOG / floors ------------------------------------------------------------------

edit(
    APP + "README.md",
    """| `/v1/crossval` | POST | Walk-forward cross-validation over the whole dataset (the `full` split — the artifact's own `*_full` when present, otherwise rebuilt from `train \\| val \\| test`) (synchronous); returns aggregated per-fold metrics. |
""",
    """| `/v1/crossval` | POST | Walk-forward cross-validation over the `trainval` pool (train \\| val, rebuilt entity-major; `test` is never in a fold). On an artifact with `ticker_code` / `window_end_date` the folds are cut on the global date with a per-entity embargo (default: one look-back) and a label-availability rule; `embargo_days` adds a duration gap. The response's `folding` block says what was done. Synchronous; returns aggregated per-fold metrics. |
""",
)

edit(
    APP + "CHANGELOG.md",
    """## [Unreleased]

## [0.7.0] - 2026-10-19
""",
    """## [Unreleased]

### Changed

- **`POST /v1/crossval` selects over the `trainval` pool and cuts a panel's folds on the global
  date, per entity** (W5.2 of juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`;
  findings F-P7 / F-SCI2). The pool is juniper-recurrence-model 0.6.0's composed `trainval` view
  (train | val, entity-major), so the final `test` partition is never in a fold -- on the W5.1
  equities row the old `full`-view fold 4 evaluated the entire `test` partition, and the row's CV
  population becomes 1,522 windows. When the artifact carries `ticker_code` and `window_end_date`,
  model-core's `walk_forward_folds` is called with `groups` / `order`: every ticker's windows before
  the cut are train and after it eval, and the embargo purge is applied per entity. **`embargo`
  (windows) now defaults to the look-back** rather than 0 -- the gap that keeps an eval window's
  history clear of every train window; an explicit smaller value is honoured (the E-G suite sweeps
  it) and logged at WARNING. Two date-based rules follow: a train window whose
  `window_end_date + target_dt` reaches the cut is dropped (its label is not known at the cut), and
  the new optional **`embargo_days`** drops train windows ending within that many days of the cut
  (422 on an artifact without dates). `window_end_date` is a `YYYYMMDD` integer and is converted to
  day ordinals for the arithmetic. A keyless single series keeps its row-index folds. The response
  and `GET /v1/crossval/status` carry a **`folding`** block (`lookback`, the resolved `embargo`,
  `embargo_days`, `grouped`, `ordered`, `n_entities`, `n_folds`, `dropped_label_availability`,
  `dropped_embargo_days`); `dataset.split` reads `trainval`. `SplitName` admits `trainval` on the
  train route too. The floor is `juniper-recurrence-model>=0.6.0,<0.7.0` (also `[torch]`,
  `[bench-torch]` and the image lock), where the view and the keys live.

## [0.7.0] - 2026-10-19
""",
)

P = APP + "pyproject.toml"

edit(
    P,
    """    "juniper-recurrence-model>=0.5.0,<0.6.0",
    "juniper-data-client>=0.6.0,<0.7.0",
""",
    """    "juniper-recurrence-model>=0.6.0,<0.7.0",
    "juniper-data-client>=0.6.0,<0.7.0",
""",
)

edit(
    P,
    """torch = [
    "juniper-recurrence-model[torch]>=0.5.0,<0.6.0",
]
""",
    """torch = [
    "juniper-recurrence-model[torch]>=0.6.0,<0.7.0",
]
""",
)

edit(
    P,
    """bench-torch = [
    "juniper-recurrence-model[torch]>=0.5.0,<0.6.0",
]
""",
    """bench-torch = [
    "juniper-recurrence-model[torch]>=0.6.0,<0.7.0",
]
""",
)

edit(
    P,
    """# 0.5.0 does, and sets the gcv_at_edge_ / null_model_ fit diagnostics the W5.10 response block reads.
dependencies = [
""",
    """# 0.5.0 does, and sets the gcv_at_edge_ / null_model_ fit diagnostics the W5.10 response block reads.
# Raised to >=0.6.0 (W5.2, 2026-10-19): the crossval route's pool is the model reader's composed
# `trainval` view, and the folds are cut on the `ticker_code` / `window_end_date` keys 0.6.0 reads.
dependencies = [
""",
)

L = APP + "requirements.lock"

edit(
    L,
    """# ``default_ridge: "gcv"`` is safe only on a model that standardises the linear rung's memory block.
annotated-doc==0.0.5
""",
    """# ``default_ridge: "gcv"`` is safe only on a model that standardises the linear rung's memory block.
#
# MOVED 2026-10-19 (later), TARGETED, for the 0.8.0 image (W5.2 of the same plan):
# ``juniper-recurrence-model`` 0.5.0 -> **0.6.0** (the composed ``trainval`` view and the
# ``ticker_code`` / ``window_end_date`` keys the crossval route cuts its folds on). The ONLY pin
# change; the count is unchanged at 31; 0.6.0 changed none of its own requirements (verify its
# PyPI ``requires_dist`` against 0.5.0's when it publishes), so no other pin can move; a
# pure-Python wheel, so the arm64 pre-flight is unaffected. The ``pyproject.toml`` floor moves with it.
annotated-doc==0.0.5
""",
)

edit(
    L,
    """juniper-recurrence-model==0.5.0
""",
    """juniper-recurrence-model==0.6.0
""",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", required=True, help="juniper-recurrence checkout root")
    parser.add_argument("--check", action="store_true", help="report each edit's state; write nothing")
    args = parser.parse_args()
    root = pathlib.Path(args.root)
    pending = applied = 0
    failed = []
    for rel, content in CREATE.items():
        path = root / rel
        if path.exists() and path.read_text(encoding="utf-8") == content:
            applied += 1
            print(f"  = {rel}: already created")
            continue
        pending += 1
        if args.check:
            print(f"  ~ {rel}: WOULD create ({len(content)} bytes)")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"  + {rel}: created ({len(content)} bytes)")
    for rel, old, new in EDITS:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        if text.count(new) == 1:  # an insertion edit keeps its anchor inside ``new``, so ``new`` present is the test
            applied += 1
            print(f"  = {rel}: already applied")
            continue
        count = text.count(old)
        if count != 1:
            failed.append((rel, count, old.splitlines()[0]))
            print(f"  ! {rel}: anchor matched {count} times: {old.splitlines()[0][:80]!r}")
            continue
        pending += 1
        if args.check:
            print(f"  ~ {rel}: WOULD apply: {old.splitlines()[0][:80]!r}")
        else:
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            print(f"  + {rel}: applied: {old.splitlines()[0][:80]!r}")
    print(f"applied {applied}, pending {pending}, failed {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
