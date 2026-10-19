#!/usr/bin/env python3
"""
Apply W5.7 (F-P5 / F-P6 / F-P8 producer guards) to a juniper-data tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling (cross-repo: juniper-data)
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc -- one-off (the provenance of record for the juniper-data W5.7 PR)
Retire when: the juniper-data W5.7 PR is merged and the plan row W5.7 reads Done.

Plan: juniper-ml ``notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md``
row W5.7 (F-P5, F-P6, F-P8). Motivating case: ``notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md``
§1.1 (two mints under one ``dataset_id``, the second lacking the action columns).

What it changes (all under ``--root``):

* ``juniper_data/core/limits.py`` -- ``build_data_quality_meta`` gains ``dropped`` and
  ``actions_present``; ``IncompleteDataError`` words the zero-rows case for a lost symbol.
* ``juniper_data/generators/equities/generator.py`` -- ``_condition_universe`` (the shared
  conditioning loop, recording every lost ticker with its reason), ``_apply_incomplete_policy``
  gains ``lost=`` (a lost REQUESTED symbol is refused under the shut gate, annotated under the
  open one; the default universe is annotated only), the F-P8 guard in ``_condition_one``
  (``actions_present`` column + WARNING on the zero-fill), ``_check_return_target_inputs``
  (``close`` / ``next_close`` finite and positive before ``return`` / ``log_return``).
* ``juniper_data/generators/equities_seq/generator.py`` -- uses the shared loop; a ticker with
  too few rows for one window is classified lost BEFORE the policy; the guard call; the
  ``dataset_id`` is request-addressed paragraph in the module docstring.
* ``juniper_data/generators/equities/params.py`` -- the ``symbols`` description states the rule.
* Tests: the OHLCV fixtures carry the two action columns (yfinance's real shape under
  ``actions=True``); three tests that lost a requested symbol opt in; one asserts the F-P8
  annotation; new ``juniper_data/tests/unit/test_equities_producer_guards.py``.
* ``docs/REFERENCE.md`` -- new § Equities Data Quality Annotation; ``CHANGELOG.md`` Unreleased.

Each edit asserts its anchor exactly once (``--check`` reports applied / pending; the applied
test is "new text present once", so a re-run is a no-op).

Usage::

    python3 util/ad-hoc/2026-10-19_apply_w5_7_producer_guards.py --root <juniper-data tree> [--check]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# limits.py                                                                    #
# --------------------------------------------------------------------------- #

LIMITS_EDITS = [
    (
        """    Attributes:
        unrescued: identifiers that could not be recovered by any rescue path.
        rows_affected: dataset rows those identifiers account for.
    \"\"\"

    def __init__(self, *, detail: str, unrescued: list[str], rows_affected: int, opt_in_env: str) -> None:
        self.unrescued = list(unrescued)
        self.rows_affected = int(rows_affected)
        shown = ", ".join(self.unrescued[:8]) + ("…" if len(self.unrescued) > 8 else "")
        super().__init__(
            f"{detail} Affected ({len(self.unrescued)}): {shown}. {rows_affected:,} row(s) would carry fabricated values. Re-submit with allow_truncation=true (or set {opt_in_env}=true) to accept them, or with incomplete_rows='drop' to exclude them. Either choice is recorded permanently in the dataset's metadata."
        )
""",
        """    Attributes:
        unrescued: identifiers that could not be recovered by any rescue path -- or, for a
            lost REQUESTED symbol (W5.7, F-P5), the symbols that yielded no usable data.
        rows_affected: dataset rows those identifiers account for; ``0`` for lost symbols,
            which are not in the dataset to be affected.
    \"\"\"

    def __init__(self, *, detail: str, unrescued: list[str], rows_affected: int, opt_in_env: str) -> None:
        self.unrescued = list(unrescued)
        self.rows_affected = int(rows_affected)
        shown = ", ".join(self.unrescued[:8]) + ("…" if len(self.unrescued) > 8 else "")
        if self.rows_affected > 0:
            consequence = f"{rows_affected:,} row(s) would carry fabricated values. Re-submit with allow_truncation=true (or set {opt_in_env}=true) to accept them, or with incomplete_rows='drop' to exclude them. Either choice is recorded permanently in the dataset's metadata."
        else:
            # W5.7 (F-P5): the affected symbols are not IN the dataset -- they yielded no usable
            # data -- so there are no rows to accept or drop, only a partial universe to accept
            # knowingly. `incomplete_rows` is not offered: it chooses between rows that exist.
            consequence = f"The dataset would silently cover fewer symbols than were requested. Re-submit with allow_truncation=true (or set {opt_in_env}=true) to accept the partial universe; the lost symbols and their reasons are recorded permanently in the dataset's metadata (data_quality.dropped_symbols)."
        super().__init__(f"{detail} Affected ({len(self.unrescued)}): {shown}. {consequence}")
""",
    ),
    (
        """def build_data_quality_meta(
    *,
    unrescued: dict[str, str],
    degraded: dict[str, str],
    rows_affected: int,
    policy: str,
) -> dict[str, Any] | None:
""",
        """def build_data_quality_meta(
    *,
    unrescued: dict[str, str],
    degraded: dict[str, str],
    rows_affected: int,
    policy: str,
    dropped: dict[str, str] | None = None,
    actions_present: dict[str, bool] | None = None,
) -> dict[str, Any] | None:
""",
    ),
    (
        """    Returns ``None`` when both are empty, so the field's presence alone answers
    "is anything wrong with this dataset" -- the same contract
    ``DatasetMeta.truncation`` keeps.
    \"\"\"
    if not unrescued and not degraded:
        return None
    return {
        "complete": False,
        "unrescued": dict(sorted(unrescued.items())),
        "degraded": dict(sorted(degraded.items())),
        "rows_affected": int(rows_affected),
        "policy": policy,
    }
""",
        """    Two more, added by W5.7 (juniper-ml plan rows F-P5 / F-P8) and kept apart for the
    same reason:

    * ``dropped`` -- symbol -> reason, for a ticker that is ABSENT from the arrays although
      it was in the resolved universe: its download raised, returned nothing usable, or (the
      sequence generator) conditioned to too few rows for one window. Distinct from
      ``unrescued`` under the ``drop`` policy, which names symbols removed for a fabricated
      fundamental; these were never there to remove. Recorded as ``dropped_symbols``.
    * ``actions_present`` -- symbol -> bool, for every symbol in the arrays, saying whether
      the price response carried the ``dividend`` / ``split_ratio`` columns. yfinance adds
      both (zero-filled) under ``actions=True``, so ``false`` is an ANOMALOUS response -- or
      a cache file written from one -- that the generator zero-filled; it cannot tell that
      apart from "no actions in range" (F-P8), which is why this is recorded, not refused.
      An artifact whose ``data_quality`` has no ``actions_present`` key was minted before
      this field existed; compare the meta ``checksum`` across mints instead.

    Returns ``None`` when every category is clean (no symbol lost, every response carried
    its action columns), so the field's presence alone answers "is anything wrong with this
    dataset" -- the same contract ``DatasetMeta.truncation`` keeps.
    \"\"\"
    dropped = dict(dropped or {})
    actions_present = {symbol: bool(flag) for symbol, flag in (actions_present or {}).items()}
    actions_missing = not all(actions_present.values())
    if not unrescued and not degraded and not dropped and not actions_missing:
        return None
    return {
        "complete": False,
        "unrescued": dict(sorted(unrescued.items())),
        "degraded": dict(sorted(degraded.items())),
        "dropped_symbols": dict(sorted(dropped.items())),
        "actions_present": dict(sorted(actions_present.items())),
        "rows_affected": int(rows_affected),
        "policy": policy,
    }
""",
    ),
]

# --------------------------------------------------------------------------- #
# equities/generator.py                                                        #
# --------------------------------------------------------------------------- #

FLAT_EDITS = [
    # 1. generate(): the conditioning loop becomes the shared helper and carries `lost`.
    (
        """        constituents = EquitiesGenerator._load_constituents()
        symbols, meta_map, truncation = EquitiesGenerator._resolve_symbols(params, constituents)
        end_date = params.end_date or datetime.now(UTC).strftime("%Y-%m-%d")

        conditioned: dict[str, Any] = {}
        total = len(symbols)
        for index, ticker in enumerate(symbols, start=1):
            try:
                frame = EquitiesGenerator._condition_one(ticker, meta_map.get(ticker, {}), params, end_date)
            except Exception as exc:  # noqa: BLE001 - one bad ticker must not abort the whole batch
                _logger.warning("equities: skipping %s (%s)", ticker, exc)
                continue
            if frame is not None and not frame.empty:
                conditioned[ticker] = frame
                _logger.info("equities: [%d/%d] %s -> %d rows", index, total, ticker, len(frame))
            else:
                _logger.info("equities: [%d/%d] %s -> no data", index, total, ticker)

        if not conditioned:
            raise ValueError("No data could be retrieved for the requested symbols.")

        # Classify, refuse or prune, and build the annotation -- BEFORE assembling
        # anything. Shared with ``equities_seq``, which reuses this whole pipeline
        # and went a release without the policy at all (found by the round-38
        # handoff validation in juniper-ml, 2026-09-08).
        conditioned, quality_meta = EquitiesGenerator._apply_incomplete_policy(params, conditioned)
""",
        """        constituents = EquitiesGenerator._load_constituents()
        symbols, meta_map, truncation = EquitiesGenerator._resolve_symbols(params, constituents)
        end_date = params.end_date or datetime.now(UTC).strftime("%Y-%m-%d")

        conditioned, lost = EquitiesGenerator._condition_universe(symbols, meta_map, params, end_date, log_prefix="equities")

        if not conditioned:
            raise ValueError("No data could be retrieved for the requested symbols.")

        # Classify, refuse or prune, and build the annotation -- BEFORE assembling
        # anything. Shared with ``equities_seq``, which reuses this whole pipeline
        # and went a release without the policy at all (found by the round-38
        # handoff validation in juniper-ml, 2026-09-08). `lost` carries the tickers the
        # loop above could not condition (W5.7, F-P5).
        conditioned, quality_meta = EquitiesGenerator._apply_incomplete_policy(params, conditioned, lost=lost)
""",
    ),
    # 2. generate(): the F-P6 guard, per ticker, before the partition cut.
    (
        """        train_frames, val_frames, test_frames, full_frames = [], [], [], []
        for ticker in vocab:
            frame = conditioned[ticker].sort_index()
            frame["ticker_code"] = code_of[ticker]
""",
        """        train_frames, val_frames, test_frames, full_frames = [], [], [], []
        for ticker in vocab:
            frame = conditioned[ticker].sort_index()
            EquitiesGenerator._check_return_target_inputs(ticker, frame, params.regression_target)
            frame["ticker_code"] = code_of[ticker]
""",
    ),
    # 3. the two new helpers + _apply_incomplete_policy's signature.
    (
        """    @staticmethod
    def _apply_incomplete_policy(params: EquitiesParams, conditioned: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
        \"\"\"Classify the conditioned frames, apply fail / accept / drop, and build the annotation.
""",
        """    @staticmethod
    def _condition_universe(symbols: list[str], meta_map: dict[str, dict[str, Any]], params: EquitiesParams, end_date: str, *, log_prefix: str) -> tuple[dict[str, Any], dict[str, str]]:
        \"\"\"Condition every resolved ticker, recording each one that is lost and why (W5.7, F-P5).

        One loop for both generators. Each had its own copy, and both let the universe shrink
        in silence: a ticker whose download raised was logged at WARNING and skipped, one that
        returned nothing was logged at INFO and skipped, and neither left a trace in the
        dataset -- the artifact was indistinguishable from a complete one (F-P5). The reasons
        are returned so ``_apply_incomplete_policy`` can refuse or annotate.

        Args:
            symbols: the resolved universe, in order.
            meta_map: ticker -> constituent metadata (``name`` / ``cik`` / ``sector``).
            params: the request's params.
            end_date: the effective end date (``params.end_date`` or today).
            log_prefix: ``"equities"`` or ``"equities_seq"``, so the log says which pipeline.

        Returns:
            ``(conditioned, lost)``: ticker -> conditioned frame (sorted by date) for the tickers
            that yielded data, and ticker -> reason for the ones that did not.
        \"\"\"
        conditioned: dict[str, Any] = {}
        lost: dict[str, str] = {}
        total = len(symbols)
        for index, ticker in enumerate(symbols, start=1):
            try:
                frame = EquitiesGenerator._condition_one(ticker, meta_map.get(ticker, {}), params, end_date)
            except Exception as exc:  # noqa: BLE001 - one bad ticker must not abort the whole batch
                _logger.warning("%s: skipping %s (%s)", log_prefix, ticker, exc)
                lost[ticker] = f"conditioning failed: {exc}"
                continue
            if frame is not None and not frame.empty:
                conditioned[ticker] = frame.sort_index()
                _logger.info("%s: [%d/%d] %s -> %d rows", log_prefix, index, total, ticker, len(frame))
            else:
                _logger.info("%s: [%d/%d] %s -> no data", log_prefix, index, total, ticker)
                lost[ticker] = "no usable price data in range"
        return conditioned, lost

    @staticmethod
    def _check_return_target_inputs(ticker: str, frame: Any, mode: str) -> None:
        \"\"\"Refuse a return-type target over a non-positive or non-finite price (W5.7, F-P6).

        ``return`` divides by ``close`` and ``log_return`` takes the log of the ratio, so a zero
        or negative ``close`` (or ``next_close``) yields ±Inf / NaN in ``y_reg``. The reader on
        the recurrence side refuses a non-finite target -- but only after the artifact has been
        minted and cached under its ``dataset_id``, where it answers every later identical
        request. Checked here, per ticker, so the refusal names the symbol, the row count and
        the first offending session. ``next_close`` (the raw price) is not guarded: a zero price
        is then a value, not a divisor.

        Raises:
            ValueError: naming the ticker; the route maps it to 400.
        \"\"\"
        if mode == "next_close" or frame.empty:
            return
        close = frame["close"].to_numpy(dtype=np.float64)
        next_close = frame["next_close"].to_numpy(dtype=np.float64)
        bad = ~(np.isfinite(close) & np.isfinite(next_close) & (close > 0.0) & (next_close > 0.0))
        if bad.any():
            first = pd.Timestamp(frame.index[int(np.argmax(bad))]).date()
            raise ValueError(f"equities: {ticker} has {int(bad.sum())} row(s) with a non-positive or non-finite close (first {first}); regression_target={mode!r} would be non-finite there. Re-submit with regression_target='next_close', or a date range that excludes those sessions.")

    @staticmethod
    def _apply_incomplete_policy(params: EquitiesParams, conditioned: dict[str, Any], lost: dict[str, str] | None = None) -> tuple[dict[str, Any], dict[str, Any] | None]:
        \"\"\"Classify the conditioned frames, apply fail / accept / drop, and build the annotation.
""",
    ),
    (
        """        Args:
            params: the request's params; supplies the ``allow_truncation`` gate and
                the ``incomplete_rows`` choice via ``_resolve_incomplete_policy``.
            conditioned: ticker -> conditioned frame, as the conditioning loop built it.
""",
        """        **Lost symbols (W5.7, F-P5).** ``lost`` names the tickers of the resolved universe
        that are absent from ``conditioned`` -- their download raised, returned nothing usable,
        or (``equities_seq``) left too few rows for one window. When the request named its
        symbols, a lost one is refused under the shut gate exactly as an unrescued fundamental
        is, and annotated under ``data_quality.dropped_symbols`` when the gate is open. When
        the request took the default universe nothing was asked for by name, so a lost ticker
        is annotated but never refused. Either way the record is permanent: a dataset that
        quietly covers fewer symbols than its request is the failure this area exists to
        prevent.

        **Action columns (F-P8).** Every frame's ``actions_present`` flag (set by
        ``_condition_one``) is carried into the annotation, so a mint from a response that
        lacked ``dividend`` / ``split_ratio`` says so.

        Args:
            params: the request's params; supplies the ``allow_truncation`` gate and
                the ``incomplete_rows`` choice via ``_resolve_incomplete_policy``.
            conditioned: ticker -> conditioned frame, as the conditioning loop built it.
            lost: ticker -> reason for every resolved ticker that is not in ``conditioned``.
""",
    ),
    (
        """        Raises:
            IncompleteDataError: under ``INCOMPLETE_FAIL`` (the default: the gate is
                shut), and under ``INCOMPLETE_DROP`` when dropping empties the dataset.
                Subclasses ValueError; the route maps it to 422.
        \"\"\"
        degraded: dict[str, str] = {}
        unrescued: dict[str, str] = {}
        for ticker, frame in conditioned.items():
""",
        """        Raises:
            IncompleteDataError: under ``INCOMPLETE_FAIL`` (the default: the gate is
                shut) -- for an unrescued fundamental or a lost requested symbol -- and
                under ``INCOMPLETE_DROP`` when dropping empties the dataset.
                Subclasses ValueError; the route maps it to 422.
        \"\"\"
        lost = dict(lost or {})
        degraded: dict[str, str] = {}
        unrescued: dict[str, str] = {}
        actions_present: dict[str, bool] = {}
        for ticker, frame in conditioned.items():
            actions_present[ticker] = bool(frame["actions_present"].iloc[0]) if "actions_present" in frame.columns and len(frame) else True
""",
    ),
    (
        """        rows_affected = sum(len(conditioned[ticker]) for ticker in unrescued)
        policy = EquitiesGenerator._resolve_incomplete_policy(params, bool(unrescued))

        # The messages say "equities:" for both callers deliberately -- this IS the
        # equities pipeline, and the sequence generator is a windowing layer on top of it.
        if unrescued:
            _logger.warning("equities: %d symbol(s) have no shares data after every rescue path: %s", len(unrescued), ", ".join(sorted(unrescued)))
        if policy == INCOMPLETE_FAIL:
            raise IncompleteDataError(
                detail="Shares outstanding could not be resolved for part of the requested universe, so total_shares and market_cap would be fabricated for those rows.",
                unrescued=sorted(unrescued),
                rows_affected=rows_affected,
                opt_in_env="JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION",
            )
""",
        """        rows_affected = sum(len(conditioned[ticker]) for ticker in unrescued)
        # A lost symbol opens the question only when the caller asked for it by name.
        requested_lost = lost if params.symbols else {}
        policy = EquitiesGenerator._resolve_incomplete_policy(params, bool(unrescued) or bool(requested_lost))

        # The messages say "equities:" for both callers deliberately -- this IS the
        # equities pipeline, and the sequence generator is a windowing layer on top of it.
        if unrescued:
            _logger.warning("equities: %d symbol(s) have no shares data after every rescue path: %s", len(unrescued), ", ".join(sorted(unrescued)))
        if lost:
            _logger.warning("equities: %d symbol(s) of the resolved universe are absent from the dataset: %s", len(lost), "; ".join(f"{ticker} ({reason})" for ticker, reason in sorted(lost.items())))
        if policy == INCOMPLETE_FAIL:
            if unrescued:
                raise IncompleteDataError(
                    detail="Shares outstanding could not be resolved for part of the requested universe, so total_shares and market_cap would be fabricated for those rows.",
                    unrescued=sorted(unrescued),
                    rows_affected=rows_affected,
                    opt_in_env="JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION",
                )
            reasons = "; ".join(f"{ticker}: {reason}" for ticker, reason in sorted(requested_lost.items())[:8])
            raise IncompleteDataError(
                detail=f"Requested symbol(s) yielded no usable data and would be missing from the dataset ({reasons}).",
                unrescued=sorted(requested_lost),
                rows_affected=0,
                opt_in_env="JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION",
            )
""",
    ),
    (
        """        quality_meta = build_data_quality_meta(
            unrescued=unrescued,
            degraded=degraded,
            rows_affected=0 if policy == INCOMPLETE_DROP else rows_affected,
            policy=policy,
        )
        return conditioned, quality_meta
""",
        """        quality_meta = build_data_quality_meta(
            unrescued=unrescued,
            degraded=degraded,
            rows_affected=0 if policy == INCOMPLETE_DROP else rows_affected,
            policy=policy,
            dropped=lost,
            actions_present={ticker: actions_present[ticker] for ticker in conditioned},
        )
        return conditioned, quality_meta
""",
    ),
    # 4. _condition_one: the F-P8 guard.
    (
        """        # yfinance omits the action columns entirely for a ticker with no
        # dividends or splits in range; absent means "none happened", which is
        # 0.0, not missing.
        for action_column in ("dividend", "split_ratio"):
            if action_column not in frame.columns:
                frame[action_column] = 0.0
        frame[["dividend", "split_ratio"]] = frame[["dividend", "split_ratio"]].fillna(0.0)
""",
        """        # THE F-P8 GUARD (W5.7). This used to read: "yfinance omits the action columns entirely
        # for a ticker with no dividends or splits in range; absent means none happened". The
        # 2026-10-05 consensus review refuted the second half by execution: two mints of
        # ``equities_seq-6.0.0-15505731cba5b86d`` 85 s apart differed, and the second carried an
        # all-zero ``dividend`` column and no 2020-08-31 AAPL split -- an incomplete upstream
        # response served as a complete artifact with no log line (juniper-ml
        # ``notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md`` §1.1).
        # yfinance's ``history`` adds BOTH columns, zero-filled, under ``actions=True``
        # (``scrapers/history.py``), so an absent column is an anomalous response -- or a cache
        # file written from one -- not the normal shape of an action-less ticker. The generator
        # still cannot tell the two apart, so this records and warns rather than refuses:
        # refusal is a request-level choice. The flag rides the frame as a column (as
        # ``shares_quality`` does) into ``data_quality.actions_present``; the zero-fill itself
        # is unchanged, so the arrays are what they were.
        missing_actions = [column for column in ("dividend", "split_ratio") if column not in frame.columns]
        if missing_actions:
            _logger.warning(
                "equities: %s: the price response carried no %s column(s); zero-filling them. Absent can mean no actions in range OR an incomplete upstream response, and the generator cannot tell which (F-P8). The dataset is annotated actions_present=false; compare the meta checksum across mints of the same dataset_id.",
                ticker,
                " / ".join(missing_actions),
            )
        for action_column in missing_actions:
            frame[action_column] = 0.0
        frame[["dividend", "split_ratio"]] = frame[["dividend", "split_ratio"]].fillna(0.0)
        frame["actions_present"] = not missing_actions
""",
    ),
]

# --------------------------------------------------------------------------- #
# equities_seq/generator.py                                                    #
# --------------------------------------------------------------------------- #

SEQ_EDITS = [
    # `Any` typed the conditioning loop's local, which moved into the shared helper.
    (
        """import logging
from datetime import UTC, datetime
from typing import Any

import numpy as np
""",
        """import logging
from datetime import UTC, datetime

import numpy as np
""",
    ),
    (
        """Sources, both in juniper-ml ``notes/``:
``JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md``
(W1.1, F-P1, the R4 note) and ``JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md``
(§2.3(b), §3.3). Pinned by ``tests/unit/test_equities_seq_generator.py::TestRecurrenceReadyBundle``.
\"\"\"
""",
        """Sources, both in juniper-ml ``notes/``:
``JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md``
(W1.1, F-P1, the R4 note) and ``JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md``
(§2.3(b), §3.3). Pinned by ``tests/unit/test_equities_seq_generator.py::TestRecurrenceReadyBundle``.

The ``dataset_id`` is request-addressed (W5.7, F-P8)
---------------------------------------------------
``dataset_id`` hashes the generator, its ``VERSION`` and the request params -- not the arrays.
Two mints of one id can therefore differ in content whenever the upstream response differs:
the 2026-10-05 review found a second mint of ``equities_seq-6.0.0-15505731cba5b86d`` whose
price response had no action columns, so its ``dividend`` column was all zero and the
2020-08-31 AAPL split was absent. The meta ``checksum`` IS the content fingerprint (sha256 over
the arrays), so a consumer that needs "the same data" compares checksums, not ids. The producer
guards here record what it can see -- ``data_quality.actions_present`` says whether each
symbol's response carried the action columns, ``data_quality.dropped_symbols`` names every
resolved symbol that is absent from the arrays and why -- and refuse a requested symbol that is
lost unless ``allow_truncation`` opens the gate. Refusing a mint whose actions MAY be missing is
a request-level choice: the generator cannot know whether a symbol had any actions in range.
\"\"\"
""",
    ),
    (
        """        constituents = EquitiesGenerator._load_constituents()
        symbols, meta_map, truncation = EquitiesGenerator._resolve_symbols(params, constituents)
        end_date = params.end_date or datetime.now(UTC).strftime("%Y-%m-%d")

        conditioned: dict[str, Any] = {}
        total = len(symbols)
        for index, ticker in enumerate(symbols, start=1):
            try:
                frame = EquitiesGenerator._condition_one(ticker, meta_map.get(ticker, {}), params, end_date)
            except Exception as exc:  # noqa: BLE001 - one bad ticker must not abort the whole batch
                _logger.warning("equities_seq: skipping %s (%s)", ticker, exc)
                continue
            if frame is not None and not frame.empty:
                conditioned[ticker] = frame.sort_index()
                _logger.info("equities_seq: [%d/%d] %s -> %d rows", index, total, ticker, len(frame))
            else:
                _logger.info("equities_seq: [%d/%d] %s -> no data", index, total, ticker)

        if not conditioned:
            raise ValueError("No data could be retrieved for the requested symbols.")

        # The incomplete-data policy, the flat generator's own helper (APD-DATA-018).
        # This generator had no copy of it, so an unrescued ticker shipped here with a
        # fabricated total_shares / market_cap, no refusal and no annotation -- while
        # the identical request to `equities` was refused. Called HERE, after
        # conditioning and before the normaliser fit and the windowing, so a dropped
        # ticker reaches neither: `vocab` below is derived from the returned mapping.
        conditioned, quality_meta = EquitiesGenerator._apply_incomplete_policy(params, conditioned)
""",
        """        constituents = EquitiesGenerator._load_constituents()
        symbols, meta_map, truncation = EquitiesGenerator._resolve_symbols(params, constituents)
        end_date = params.end_date or datetime.now(UTC).strftime("%Y-%m-%d")

        # The flat generator's conditioning loop (W5.7 made it shared), which records every
        # ticker it loses and why. Both generators had their own copy, and both lost tickers
        # in silence.
        conditioned, lost = EquitiesGenerator._condition_universe(symbols, meta_map, params, end_date, log_prefix="equities_seq")

        if not conditioned:
            raise ValueError("No data could be retrieved for the requested symbols.")

        # W5.7 (F-P5): a ticker with too few rows for one window is lost from the arrays
        # exactly as a ticker with no data is, and was just as silent -- the `continue` in
        # the windowing loop below logs at INFO and records nothing. Classified HERE, before
        # the policy, so a requested symbol that cannot contribute a window is refused under
        # the shut gate like one that returned nothing, and annotated under the open one. It
        # stays in `ticker_vocab` with zero windows: the code allocation is unchanged, so an
        # existing dataset_id keeps the arrays it had.
        for ticker, frame in conditioned.items():
            if len(frame) <= params.lookback + 1:
                lost[ticker] = f"{len(frame)} row(s) after conditioning, need more than lookback+1={params.lookback + 1}: no window"

        # The incomplete-data policy, the flat generator's own helper (APD-DATA-018).
        # This generator had no copy of it, so an unrescued ticker shipped here with a
        # fabricated total_shares / market_cap, no refusal and no annotation -- while
        # the identical request to `equities` was refused. Called HERE, after
        # conditioning and before the normaliser fit and the windowing, so a dropped
        # ticker reaches neither: `vocab` below is derived from the returned mapping.
        conditioned, quality_meta = EquitiesGenerator._apply_incomplete_policy(params, conditioned, lost=lost)
""",
    ),
    (
        """            feats = EquitiesGenerator._features(frame, norm)
            dates = EquitiesGenerator._dates_yyyymmdd(frame)
            y_dir = EquitiesGenerator._direction_onehot(frame)
            y_reg = EquitiesGenerator._regression_target(frame, params.regression_target)
""",
        """            feats = EquitiesGenerator._features(frame, norm)
            dates = EquitiesGenerator._dates_yyyymmdd(frame)
            y_dir = EquitiesGenerator._direction_onehot(frame)
            EquitiesGenerator._check_return_target_inputs(ticker, frame, params.regression_target)
            y_reg = EquitiesGenerator._regression_target(frame, params.regression_target)
""",
    ),
]

PARAMS_EDITS = [
    (
        """    symbols: list[str] | None = Field(
        default=None,
        description="Tickers to include. None = the bundled S&P 500 constituents.",
    )
""",
        """    symbols: list[str] | None = Field(
        default=None,
        description="Tickers to include. None = the bundled S&P 500 constituents. A named ticker that yields no usable data (download failed, nothing in range, or -- for equities_seq -- too few rows for one window) is REFUSED with 422 unless allow_truncation opens the gate, in which case the dataset is minted without it and PERMANENTLY annotated under DatasetMeta.data_quality.dropped_symbols (W5.7). A lost ticker of the default universe is annotated but not refused.",
    )
""",
    ),
]

# --------------------------------------------------------------------------- #
# Tests: fixtures carry the action columns; three tests opt in; one asserts F-P8  #
# --------------------------------------------------------------------------- #

ACTIONS_NOTE = "# W5.7 (F-P8): yfinance adds both action columns, zero-filled, under ``actions=True``; a response without them is the anomaly the generator now annotates."

TEST_FLAT_EDITS = [
    (
        """    volume = rng.integers(1_000_000, 5_000_000, periods).astype(float)
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Adj Close": close, "Volume": volume}, index=index)


def _shares(start: str = "2009-06-30"):
""",
        """    volume = rng.integers(1_000_000, 5_000_000, periods).astype(float)
    """
        + ACTIONS_NOTE
        + """
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Adj Close": close, "Volume": volume, "Dividends": 0.0, "Stock Splits": 0.0}, index=index)


def _shares(start: str = "2009-06-30"):
""",
    ),
    (
        """    def test_unknown_symbol_skipped_not_fatal(self) -> None:
        # AAPL returns data; NVDA returns an empty frame and is skipped (not fatal).
        arrays = _generate(["AAPL", "NVDA"], {"AAPL": _ohlcv(seed=17)}, _shares())
        assert arrays["ticker_vocab"].tolist() == ["AAPL"]
""",
        """    def test_unknown_symbol_skipped_not_fatal(self) -> None:
        # AAPL returns data; NVDA returns an empty frame and is skipped (not fatal) -- once the
        # gate is open. Under the shut gate a lost REQUESTED symbol is refused (W5.7, F-P5;
        # `TestLostRequestedSymbols` in test_equities_producer_guards.py), and either way it
        # is recorded.
        arrays = _generate(["AAPL", "NVDA"], {"AAPL": _ohlcv(seed=17)}, _shares(), allow_truncation=True)
        assert arrays["ticker_vocab"].tolist() == ["AAPL"]
        assert arrays[DATA_QUALITY_META_KEY]["dropped_symbols"] == {"NVDA": "no usable price data in range"}
""",
    ),
    (
        """    def test_absent_action_columns_mean_zero_not_missing(self) -> None:
        \"\"\"A ticker with no dividends or splits gets 0.0, never NaN.

        yfinance omits the columns entirely in that case. Treating absent as
        missing would put NaN into a float32 feature column for the majority of
        rows of the majority of tickers.
        \"\"\"
        arrays = _generate(["AAPL"], {"AAPL": _ohlcv(seed=12)}, _shares())
        for column in ("dividend", "split_ratio"):
            values = whole(arrays, "X")[:, _FEATURES.index(column)]
            assert not np.isnan(values).any()
            assert np.all(values == 0.0)
""",
        """    def test_absent_action_columns_mean_zero_not_missing(self, caplog: pytest.LogCaptureFixture) -> None:
        \"\"\"A response without the action columns still gets 0.0, never NaN -- and now says so.

        The zero-fill is unchanged: NaN in a float32 feature column would poison every row.
        What W5.7 (F-P8) adds is the record. yfinance adds both columns, zero-filled, under
        ``actions=True``, so a response without them is anomalous (the 2026-10-05 review's
        second mint), and the generator cannot tell that from "no actions in range" -- hence
        ``actions_present: false`` and a WARNING rather than a refusal.
        \"\"\"
        with caplog.at_level("WARNING", logger="juniper_data.generators.equities.generator"):
            arrays = _generate(["AAPL"], {"AAPL": _ohlcv(seed=12).drop(columns=["Dividends", "Stock Splits"])}, _shares())
        for column in ("dividend", "split_ratio"):
            values = whole(arrays, "X")[:, _FEATURES.index(column)]
            assert not np.isnan(values).any()
            assert np.all(values == 0.0)
        assert arrays[DATA_QUALITY_META_KEY]["actions_present"] == {"AAPL": False}
        assert any("AAPL" in record.getMessage() and "zero-filling" in record.getMessage() for record in caplog.records)
""",
    ),
]

TEST_SEQ_EDITS = [
    (
        """    volume = rng.integers(1_000_000, 5_000_000, periods).astype(float)
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Adj Close": close, "Volume": volume}, index=index)


def _shares(start: str = "2007-12-31"):
""",
        """    volume = rng.integers(1_000_000, 5_000_000, periods).astype(float)
    """
        + ACTIONS_NOTE
        + """
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Adj Close": close, "Volume": volume, "Dividends": 0.0, "Stock Splits": 0.0}, index=index)


def _shares(start: str = "2007-12-31"):
""",
    ),
    (
        """        with patch.object(eq_gen.yf, "download", side_effect=fake_download), patch.object(eq_gen.EquitiesGenerator, "_fetch_shares", staticmethod(lambda *_a: _shares())):
            arrays = EquitiesSeqGenerator.generate(EquitiesSeqParams(symbols=["AAPL", "MSFT"], start_date="2008-01-01", end_date="2011-01-01", use_cache=False, lookback=5, fundamentals_fill="zero"))
        assert arrays["ticker_vocab"].tolist() == ["AAPL"]

    def test_generate_handles_ticker_with_no_data(self) -> None:
        # MSFT is absent from the ohlcv map -> empty frame -> the "no data" else branch.
        arrays = _generate(["AAPL", "MSFT"], {"AAPL": _ohlcv(seed=21)}, _shares(), lookback=5)
        assert arrays["ticker_vocab"].tolist() == ["AAPL"]
""",
        """        # W5.7 (F-P5): a lost REQUESTED symbol is refused under the shut gate, so these skip
        # branches are reached with the gate open -- and the loss is recorded.
        with patch.object(eq_gen.yf, "download", side_effect=fake_download), patch.object(eq_gen.EquitiesGenerator, "_fetch_shares", staticmethod(lambda *_a: _shares())):
            arrays = EquitiesSeqGenerator.generate(EquitiesSeqParams(symbols=["AAPL", "MSFT"], start_date="2008-01-01", end_date="2011-01-01", use_cache=False, lookback=5, fundamentals_fill="zero", allow_truncation=True))
        assert arrays["ticker_vocab"].tolist() == ["AAPL"]
        assert arrays[esq_gen.DATA_QUALITY_META_KEY]["dropped_symbols"] == {"MSFT": "conditioning failed: download exploded"}

    def test_generate_handles_ticker_with_no_data(self) -> None:
        # MSFT is absent from the ohlcv map -> empty frame -> the "no data" else branch.
        arrays = _generate(["AAPL", "MSFT"], {"AAPL": _ohlcv(seed=21)}, _shares(), lookback=5, allow_truncation=True)
        assert arrays["ticker_vocab"].tolist() == ["AAPL"]
        assert arrays[esq_gen.DATA_QUALITY_META_KEY]["dropped_symbols"] == {"MSFT": "no usable price data in range"}
""",
    ),
    (
        """        arrays = _generate(["AAPL", "MSFT"], {"AAPL": _ohlcv(seed=24, periods=400), "MSFT": _ohlcv(seed=25, periods=8)}, _shares(), lookback=20)
        assert "AAPL" in arrays["ticker_vocab"].tolist()
        assert whole(arrays, "X").shape[0] > 0
""",
        """        # The gate is open: a requested ticker that cannot contribute a window is lost (W5.7).
        arrays = _generate(["AAPL", "MSFT"], {"AAPL": _ohlcv(seed=24, periods=400), "MSFT": _ohlcv(seed=25, periods=8)}, _shares(), lookback=20, allow_truncation=True)
        assert "AAPL" in arrays["ticker_vocab"].tolist()
        assert whole(arrays, "X").shape[0] > 0
        assert list(arrays[esq_gen.DATA_QUALITY_META_KEY]["dropped_symbols"]) == ["MSFT"]
        assert "lookback+1=21" in arrays[esq_gen.DATA_QUALITY_META_KEY]["dropped_symbols"]["MSFT"]
""",
    ),
]

TEST_SYMBOL_CAP_EDITS = [
    (
        """            "Adj Close": close,
            "Volume": 1_000_000.0,
        },
        index=index,
    )
""",
        """            "Adj Close": close,
            "Volume": 1_000_000.0,
            # W5.7 (F-P8): the real shape of a yfinance response under ``actions=True``.
            "Dividends": 0.0,
            "Stock Splits": 0.0,
        },
        index=index,
    )
""",
    ),
]

TEST_ARTIFACTS_EDITS = [
    (
        """                "Adj Close": close,
                "Volume": rng.integers(1_000_000, 5_000_000, periods).astype(float),
            },
            index=index,
        )
""",
        """                "Adj Close": close,
                "Volume": rng.integers(1_000_000, 5_000_000, periods).astype(float),
                # W5.7 (F-P8): the real shape of a yfinance response under ``actions=True``.
                "Dividends": 0.0,
                "Stock Splits": 0.0,
            },
            index=index,
        )
""",
    ),
]

TEST_COST_BASIS_EDITS = [
    (
        """    return pd.DataFrame(
        {"Open": close, "High": high, "Low": low, "Close": close, "Adj Close": adj, "Volume": np.full(periods, 1_000_000.0)},
        index=index,
    )
""",
        """    # W5.7 (F-P8): the real shape of a yfinance response under ``actions=True``.
    return pd.DataFrame(
        {"Open": close, "High": high, "Low": low, "Close": close, "Adj Close": adj, "Volume": np.full(periods, 1_000_000.0), "Dividends": 0.0, "Stock Splits": 0.0},
        index=index,
    )
""",
    ),
]

NEW_TEST = '''"""W5.7 producer guards: lost symbols (F-P5), the close guard (F-P6), the action columns (F-P8).

Plan: juniper-ml ``notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md``
row W5.7. Motivating case: ``notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md``
§1.1 -- two mints of ``equities_seq-6.0.0-15505731cba5b86d`` 85 s apart, the second without the
action columns, served as a complete artifact under the same ``dataset_id``.

Both generators are exercised through the mocked sources of ``test_equities_generator`` and
``test_equities_seq_generator`` (yfinance and SEC patched; no network).
"""

# Project:       Juniper
# Sub-Project:   JuniperData
# Application:   juniper_data
# File Name:     test_equities_producer_guards.py
# Author:        Paul Calnon
# Version:       0.17.1
# License:       MIT License

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from juniper_data.core import limits as eq_limits
from juniper_data.core.limits import DATA_QUALITY_META_KEY, IncompleteDataError, build_data_quality_meta

pd = pytest.importorskip("pandas")
pytest.importorskip("yfinance")

from juniper_data.generators.equities import EquitiesGenerator, EquitiesParams  # noqa: E402
from juniper_data.generators.equities import generator as eq_gen  # noqa: E402
from juniper_data.generators.equities_seq import EquitiesSeqGenerator, EquitiesSeqParams  # noqa: E402
from juniper_data.tests.partitions import whole  # noqa: E402
from juniper_data.tests.unit.test_equities_generator import _generate as _flat_generate  # noqa: E402
from juniper_data.tests.unit.test_equities_generator import _ohlcv as _flat_ohlcv  # noqa: E402
from juniper_data.tests.unit.test_equities_generator import _shares as _flat_shares  # noqa: E402
from juniper_data.tests.unit.test_equities_seq_generator import _generate as _seq_generate  # noqa: E402
from juniper_data.tests.unit.test_equities_seq_generator import _ohlcv as _seq_ohlcv  # noqa: E402
from juniper_data.tests.unit.test_equities_seq_generator import _shares as _seq_shares  # noqa: E402

pytestmark = [pytest.mark.unit, pytest.mark.generators]

_LOGGER = "juniper_data.generators.equities.generator"


def _without_actions(frame):
    """The anomalous response: no ``Dividends`` / ``Stock Splits`` column at all."""
    return frame.drop(columns=["Dividends", "Stock Splits"])


class TestActionColumns:
    """F-P8: record whether the price response carried the action columns; warn on the zero-fill."""

    def test_seq_mint_without_action_columns_is_annotated_and_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """The plan's acceptance line: ``actions_present: false`` and a WARNING."""
        with caplog.at_level("WARNING", logger=_LOGGER):
            arrays = _seq_generate(["AAPL"], {"AAPL": _without_actions(_seq_ohlcv(seed=70))}, _seq_shares())
        quality = arrays[DATA_QUALITY_META_KEY]
        assert quality["complete"] is False
        assert quality["actions_present"] == {"AAPL": False}
        assert quality["dropped_symbols"] == {}
        assert quality["unrescued"] == {}
        warnings = [record.getMessage() for record in caplog.records if record.levelname == "WARNING"]
        assert any("AAPL" in message and "dividend / split_ratio" in message and "zero-filling" in message for message in warnings), warnings

    def test_flat_mint_without_action_columns_is_annotated(self) -> None:
        arrays = _flat_generate(["AAPL"], {"AAPL": _without_actions(_flat_ohlcv(seed=71))}, _flat_shares())
        assert arrays[DATA_QUALITY_META_KEY]["actions_present"] == {"AAPL": False}

    def test_one_missing_column_is_enough(self) -> None:
        """Either column absent is an incomplete response; the WARNING names the one that is."""
        arrays = _flat_generate(["AAPL"], {"AAPL": _flat_ohlcv(seed=72).drop(columns=["Stock Splits"])}, _flat_shares())
        assert arrays[DATA_QUALITY_META_KEY]["actions_present"] == {"AAPL": False}

    def test_a_complete_response_carries_no_annotation_and_no_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Absence of the block stays the signal: the fixtures carry both columns, as yfinance does."""
        with caplog.at_level("WARNING", logger=_LOGGER):
            arrays = _seq_generate(["AAPL"], {"AAPL": _seq_ohlcv(seed=73)}, _seq_shares())
        assert DATA_QUALITY_META_KEY not in arrays
        assert not [record for record in caplog.records if "zero-filling" in record.getMessage()]

    def test_the_zero_fill_itself_is_unchanged(self) -> None:
        """The arrays are what they were: the guard adds a record, not a different artifact."""
        before = _flat_generate(["AAPL"], {"AAPL": _flat_ohlcv(seed=74)}, _flat_shares())
        after = _flat_generate(["AAPL"], {"AAPL": _without_actions(_flat_ohlcv(seed=74))}, _flat_shares())
        np.testing.assert_array_equal(whole(before, "X"), whole(after, "X"))

    def test_every_symbol_is_listed_when_one_is_incomplete(self) -> None:
        """The map covers the whole universe, so a consumer sees which mints to distrust."""
        arrays = _flat_generate(["AAPL", "MSFT"], {"AAPL": _flat_ohlcv(seed=75), "MSFT": _without_actions(_flat_ohlcv(seed=76))}, _flat_shares())
        assert arrays[DATA_QUALITY_META_KEY]["actions_present"] == {"AAPL": True, "MSFT": False}

    def test_the_flag_does_not_trip_the_gate(self) -> None:
        """Refusal is a request-level choice: the generator cannot know whether actions exist in range."""
        arrays = _flat_generate(["AAPL"], {"AAPL": _without_actions(_flat_ohlcv(seed=77))}, _flat_shares())
        assert arrays[DATA_QUALITY_META_KEY]["policy"] == "accept"


class TestLostRequestedSymbols:
    """F-P5: a requested symbol that yields nothing is refused under the shut gate, recorded under the open one."""

    def test_flat_lost_requested_symbol_is_refused_by_default(self) -> None:
        with pytest.raises(IncompleteDataError) as excinfo:
            _flat_generate(["AAPL", "NVDA"], {"AAPL": _flat_ohlcv(seed=80)}, _flat_shares())
        message = str(excinfo.value)
        assert excinfo.value.unrescued == ["NVDA"]
        assert excinfo.value.rows_affected == 0
        assert "NVDA: no usable price data in range" in message
        assert "allow_truncation" in message and "JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION" in message
        assert "fabricated" not in message, "no rows exist to carry a fabricated value"
        assert "incomplete_rows" not in message, "accept / drop chooses between rows that exist"

    def test_seq_lost_requested_symbol_is_refused_by_default(self) -> None:
        with pytest.raises(IncompleteDataError, match="MSFT"):
            _seq_generate(["AAPL", "MSFT"], {"AAPL": _seq_ohlcv(seed=81)}, _seq_shares())

    def test_refusal_is_a_value_error(self) -> None:
        """So a missed catch lands on 400, never a 500; the route maps the subclass to 422."""
        with pytest.raises(ValueError):
            _flat_generate(["AAPL", "NVDA"], {"AAPL": _flat_ohlcv(seed=82)}, _flat_shares())

    def test_open_gate_mints_without_the_symbol_and_records_it(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level("WARNING", logger=_LOGGER):
            arrays = _flat_generate(["AAPL", "NVDA"], {"AAPL": _flat_ohlcv(seed=83)}, _flat_shares(), allow_truncation=True)
        assert arrays["ticker_vocab"].tolist() == ["AAPL"]
        quality = arrays[DATA_QUALITY_META_KEY]
        assert quality["complete"] is False
        assert quality["dropped_symbols"] == {"NVDA": "no usable price data in range"}
        assert quality["unrescued"] == {} and quality["rows_affected"] == 0
        assert quality["actions_present"] == {"AAPL": True}, "only symbols IN the arrays carry the flag"
        assert any("NVDA" in record.getMessage() and "absent from the dataset" in record.getMessage() for record in caplog.records)

    def test_a_conditioning_failure_records_its_exception(self) -> None:
        good = _seq_ohlcv(seed=84)

        def fake_download(symbol, **_kwargs):
            if symbol == "MSFT":
                raise RuntimeError("download exploded")
            return good.copy()

        params = EquitiesSeqParams(symbols=["AAPL", "MSFT"], start_date="2008-01-01", end_date="2011-01-01", use_cache=False, lookback=5, allow_truncation=True)
        with patch.object(eq_gen.yf, "download", side_effect=fake_download), patch.object(eq_gen.EquitiesGenerator, "_fetch_shares", staticmethod(lambda *_a: _seq_shares())):
            arrays = EquitiesSeqGenerator.generate(params)
        assert arrays[DATA_QUALITY_META_KEY]["dropped_symbols"] == {"MSFT": "conditioning failed: download exploded"}

    def test_seq_too_few_rows_for_a_window_is_a_loss(self) -> None:
        """The windowing skip was the third silent shrink; it is classified before the policy."""
        with pytest.raises(IncompleteDataError, match="lookback") as excinfo:
            _seq_generate(["AAPL", "MSFT"], {"AAPL": _seq_ohlcv(seed=85, periods=400), "MSFT": _seq_ohlcv(seed=86, periods=8)}, _seq_shares(), lookback=20)
        assert excinfo.value.unrescued == ["MSFT"]

    def test_seq_short_ticker_stays_in_the_vocab_with_zero_windows(self) -> None:
        """Deliberate: the code allocation is unchanged, so an existing dataset_id keeps its arrays."""
        arrays = _seq_generate(["AAPL", "MSFT"], {"AAPL": _seq_ohlcv(seed=87, periods=400), "MSFT": _seq_ohlcv(seed=88, periods=8)}, _seq_shares(), lookback=20, allow_truncation=True)
        assert arrays["ticker_vocab"].tolist() == ["AAPL", "MSFT"]
        assert not (whole(arrays, "ticker_code") == 1).any()
        assert "no window" in arrays[DATA_QUALITY_META_KEY]["dropped_symbols"]["MSFT"]

    def test_default_universe_losses_are_recorded_but_never_refused(self) -> None:
        """Nothing was asked for by name, so there is nothing to refuse -- only to record."""
        constituents = {"AAPL": {"name": "Apple", "cik": 320193, "sector": ""}, "MSFT": {"name": "Microsoft", "cik": 789019, "sector": ""}}
        params = EquitiesParams(symbols=None, start_date="2008-01-01", end_date="2011-01-01", use_cache=False)
        frames = {"AAPL": _flat_ohlcv(seed=89)}
        with (
            patch.object(eq_gen.EquitiesGenerator, "_load_constituents", staticmethod(lambda: constituents)),
            patch.object(eq_gen.yf, "download", side_effect=lambda symbol, **_k: frames[symbol].copy() if symbol in frames else pd.DataFrame()),
            patch.object(eq_gen.EquitiesGenerator, "_fetch_shares", staticmethod(lambda *_a: _flat_shares())),
        ):
            arrays = EquitiesGenerator.generate(params)
        assert arrays["ticker_vocab"].tolist() == ["AAPL"]
        assert arrays[DATA_QUALITY_META_KEY]["dropped_symbols"] == {"MSFT": "no usable price data in range"}

    def test_deployment_gate_opens_it_for_a_cli_caller(self) -> None:
        settings = MagicMock()
        settings.equities_max_symbols = 14
        settings.equities_allow_truncation = True
        settings.equities_incomplete_rows = "accept"
        with patch("juniper_data.api.settings.get_settings", return_value=settings):
            arrays = _flat_generate(["AAPL", "NVDA"], {"AAPL": _flat_ohlcv(seed=90)}, _flat_shares())
        assert list(arrays[DATA_QUALITY_META_KEY]["dropped_symbols"]) == ["NVDA"]

    def test_an_unrescued_fundamental_still_takes_precedence_in_the_message(self) -> None:
        """Both defects under the shut gate: the fundamentals refusal is the one raised (its remedy differs)."""
        with pytest.raises(IncompleteDataError, match="fabricated") as excinfo:
            _flat_generate(["AAPL", "NVDA"], {"AAPL": _flat_ohlcv(seed=91)}, shares=None)
        assert excinfo.value.unrescued == ["AAPL"]

    def test_every_symbol_lost_is_still_the_old_no_data_error(self) -> None:
        """Nothing conditioned: the existing refusal fires before the policy, unchanged."""
        with pytest.raises(ValueError, match="No data"):
            _flat_generate(["NVDA"], {}, _flat_shares(), allow_truncation=True)


class TestCloseGuard:
    """F-P6: ``close`` / ``next_close`` finite and positive before a return-type target."""

    @staticmethod
    def _with_bad_close(frame, value: float, at: int = 100):
        frame = frame.copy()
        frame.iloc[at, frame.columns.get_loc("Close")] = value
        return frame

    @pytest.mark.parametrize("mode", ["return", "log_return"])
    @pytest.mark.parametrize("value", [0.0, -3.0, np.inf])
    def test_flat_refuses_a_return_target_over_a_bad_close(self, mode: str, value: float) -> None:
        with pytest.raises(ValueError, match=r"AAPL has 2 row\\(s\\) with a non-positive or non-finite close") as excinfo:
            _flat_generate(["AAPL"], {"AAPL": self._with_bad_close(_flat_ohlcv(seed=92), value)}, _flat_shares(), regression_target=mode)
        # Two rows: the session itself (its `close`) and the one before it (its `next_close`).
        assert f"regression_target={mode!r}" in str(excinfo.value)
        assert "next_close" in str(excinfo.value), "the message offers the raw-price target as the remedy"

    @pytest.mark.parametrize("mode", ["return", "log_return"])
    def test_seq_refuses_a_return_target_over_a_zero_close(self, mode: str) -> None:
        with pytest.raises(ValueError, match="MSFT has 2 row"):
            _seq_generate(["AAPL", "MSFT"], {"AAPL": _seq_ohlcv(seed=93), "MSFT": self._with_bad_close(_seq_ohlcv(seed=94), 0.0)}, _seq_shares(), regression_target=mode)

    def test_the_message_names_the_first_offending_session(self) -> None:
        frame = self._with_bad_close(_flat_ohlcv(seed=95), 0.0, at=100)
        first = frame.index[99].date()  # the row BEFORE the zero: its next_close is the zero
        with pytest.raises(ValueError, match=str(first)):
            _flat_generate(["AAPL"], {"AAPL": frame}, _flat_shares(), regression_target="log_return")

    def test_next_close_is_not_guarded(self) -> None:
        """A zero price is then a value, not a divisor -- the raw target mints as before."""
        arrays = _flat_generate(["AAPL"], {"AAPL": self._with_bad_close(_flat_ohlcv(seed=96), 0.0)}, _flat_shares(), regression_target="next_close")
        assert np.isfinite(whole(arrays, "y_reg")).all()

    def test_a_clean_frame_mints_a_finite_target(self) -> None:
        arrays = _flat_generate(["AAPL"], {"AAPL": _flat_ohlcv(seed=97)}, _flat_shares(), regression_target="log_return")
        assert np.isfinite(whole(arrays, "y_reg")).all()

    def test_the_guard_is_a_plain_value_error_not_a_422(self) -> None:
        """A bad price is not caller-fixable by opting in; it is a 400, not the incomplete-data 422."""
        with pytest.raises(ValueError) as excinfo:
            _flat_generate(["AAPL"], {"AAPL": self._with_bad_close(_flat_ohlcv(seed=98), 0.0)}, _flat_shares(), regression_target="return")
        assert not isinstance(excinfo.value, IncompleteDataError)


class TestDescriptorAndError:
    """The two shared pieces in ``core/limits.py``."""

    def test_builder_is_none_when_every_category_is_clean(self) -> None:
        assert build_data_quality_meta(unrescued={}, degraded={}, rows_affected=0, policy="accept", dropped={}, actions_present={"AAPL": True}) is None
        assert build_data_quality_meta(unrescued={}, degraded={}, rows_affected=0, policy="accept") is None

    def test_builder_flags_a_dropped_symbol_alone(self) -> None:
        meta = build_data_quality_meta(unrescued={}, degraded={}, rows_affected=0, policy="accept", dropped={"NVDA": "no usable price data in range"})
        assert meta == {"complete": False, "unrescued": {}, "degraded": {}, "dropped_symbols": {"NVDA": "no usable price data in range"}, "actions_present": {}, "rows_affected": 0, "policy": "accept"}

    def test_builder_flags_a_missing_action_column_alone(self) -> None:
        meta = build_data_quality_meta(unrescued={}, degraded={}, rows_affected=0, policy="accept", actions_present={"MSFT": False, "AAPL": True})
        assert meta is not None and meta["complete"] is False
        assert list(meta["actions_present"]) == ["AAPL", "MSFT"], "sorted, like the other maps"

    def test_builder_keeps_the_old_shape_for_the_old_callers(self) -> None:
        meta = build_data_quality_meta(unrescued={"KO": "x"}, degraded={}, rows_affected=3, policy="accept")
        assert meta is not None
        assert meta["dropped_symbols"] == {} and meta["actions_present"] == {}
        assert meta["unrescued"] == {"KO": "x"} and meta["rows_affected"] == 3

    def test_error_wording_follows_rows_affected(self) -> None:
        with_rows = str(IncompleteDataError(detail="d.", unrescued=["A"], rows_affected=5, opt_in_env="E"))
        assert "5 row(s) would carry fabricated values" in with_rows and "incomplete_rows='drop'" in with_rows
        without = str(IncompleteDataError(detail="d.", unrescued=["A"], rows_affected=0, opt_in_env="E"))
        assert "fewer symbols than were requested" in without and "data_quality.dropped_symbols" in without
        assert "fabricated" not in without and "incomplete_rows" not in without
        assert "E=true" in without and "allow_truncation=true" in without

    def test_the_default_policy_constant_is_unchanged(self) -> None:
        assert eq_limits.EQUITIES_DEFAULT_INCOMPLETE_ROWS == "accept"
'''

# --------------------------------------------------------------------------- #
# Docs                                                                         #
# --------------------------------------------------------------------------- #

REFERENCE_SECTION = """## Equities Data Quality Annotation

`DatasetMeta.data_quality` is the permanent record of *what is wrong with what is present* for `equities` / `equities_seq` (APD-DATA-018 follow-up; W5.7 of juniper-ml `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` added the last two categories). It is **absent when nothing is wrong** — the same contract as `truncation` — so its presence alone answers "is anything degraded here". Built by `EquitiesGenerator._apply_incomplete_policy` through `build_data_quality_meta` (`juniper_data/core/limits.py`), popped from the arrays by the create route before checksum and persist.

| Key | Meaning |
|-----|---------|
| `complete` | Always `false` when the block exists. |
| `unrescued` | symbol → reason: no share count from any rescue path; `total_shares` / `market_cap` would be fabricated. Governs the fail / accept / drop gate. |
| `degraded` | symbol → source quality: a value WAS recovered, from a weaker source (`period_average`, `issued_includes_treasury`) or one that went `stale`. |
| `dropped_symbols` | symbol → reason (**W5.7, F-P5**): a resolved symbol that is **absent from the arrays** — its download raised (`conditioning failed: …`), returned nothing usable (`no usable price data in range`), or, for `equities_seq`, conditioned to too few rows for one window (`… need more than lookback+1=N: no window`; it stays in `ticker_vocab` with zero windows, so the code allocation and every existing `dataset_id`'s arrays are unchanged). |
| `actions_present` | symbol → bool (**W5.7, F-P8**), for every symbol in the arrays: whether the price response carried the `dividend` / `split_ratio` columns. yfinance adds both, zero-filled, under `actions=True`, so `false` is an **anomalous response** — or a cache file written from one — that the generator zero-filled with a WARNING. It cannot tell that from "no actions in range", so this is recorded, never refused. An artifact whose block has no `actions_present` key was minted before the field existed. |
| `rows_affected` | rows the `unrescued` symbols account for (`0` under `drop`, and for lost symbols, which are not in the dataset to be affected). |
| `policy` | `fail` / `accept` / `drop`, as resolved for this request. |

### A lost requested symbol is refused by default (W5.7, F-P5)

Both generators used to let the universe shrink in silence: a ticker whose download raised was logged at WARNING and skipped, one that returned nothing was logged at INFO and skipped, and the artifact was indistinguishable from a complete one. Now `EquitiesGenerator._condition_universe` (the one conditioning loop both generators share) records every lost ticker with its reason, and the gate treats it like an unrescued fundamental:

| Request | Gate shut (default) | Gate open (`allow_truncation=true` or `JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION`) |
|---------|---------------------|-----------------------------------------------------------------------------------|
| `symbols` named | **422** `IncompleteDataError` naming the symbols and reasons; `rows_affected` is 0 and the message offers only `allow_truncation` (there are no rows for `incomplete_rows` to accept or drop) | minted without them; `dropped_symbols` records each with its reason; WARNING |
| default universe | annotated, never refused — nothing was asked for by name | same |

A request every one of whose symbols is lost still fails with the older `No data could be retrieved` (400) before the policy runs. An unrescued fundamental and a lost symbol under the shut gate raise the fundamentals refusal (its remedy differs); the lost symbol is still in the log.

### The close guard (W5.7, F-P6)

`regression_target` `return` divides by `close` and `log_return` takes the log of the ratio, so a zero, negative or non-finite `close` / `next_close` yields ±Inf / NaN in `y_reg` — which the recurrence reader refuses as non-finite, but only after the artifact is minted and cached under its `dataset_id`. `EquitiesGenerator._check_return_target_inputs` runs per ticker before the target is computed and refuses with a **400** `ValueError` naming the symbol, the row count and the first offending session (`equities: AAPL has 2 row(s) with a non-positive or non-finite close (first 2008-05-21); regression_target='log_return' would be non-finite there`). `next_close` is not guarded: a zero price is then a value, not a divisor. This is a plain `ValueError`, not the 422 `IncompleteDataError` — a bad price is not caller-fixable by opting in.

### `dataset_id` is request-addressed (W5.7, F-P8)

`dataset_id` hashes the generator, its `VERSION` and the request params — never the arrays — so two mints of one id differ whenever the upstream response does. The 2026-10-05 consensus review (juniper-ml `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` §1.1) found a second mint of `equities_seq-6.0.0-15505731cba5b86d` 85 s after a complete one whose response had no action columns: all-zero `dividend`, no 2020-08-31 AAPL split, served as complete. The meta `checksum` **is** the content fingerprint (sha256 over an uncompressed `np.savez` of the arrays, sorted keys); a consumer that needs "the same data" compares checksums, not ids (see also § Conditional Requests above: the artifact is not content-addressed). Refusing a mint whose actions *may* be missing is a request-level choice the generator cannot make for the caller.

**`generator_version` is not bumped** (`equities` 5.0.0, `equities_seq` 6.0.0), as for W1.8: a refused request mints nothing, and every request that still mints emits the arrays it emitted before — the annotation and the WARNING are the only additions.

### Pins

| Test | File | Guards |
|------|------|--------|
| `TestActionColumns` (7) | `juniper_data/tests/unit/test_equities_producer_guards.py` | a mint without the action columns carries `actions_present: false` and a WARNING (both generators); a complete response carries no block and no WARNING; the zero-fill is byte-identical; every symbol is listed; the flag never trips the gate |
| `TestLostRequestedSymbols` (11) | same | refused by default (both generators; a `ValueError` subclass; `rows_affected` 0; no `fabricated` / `incomplete_rows` in the message); open gate mints, records the reason and warns; a conditioning exception records its text; the seq no-window loss is refused under the shut gate and the ticker keeps its vocab slot; the default universe is recorded, never refused; the deployment gate opens it; the fundamentals refusal takes precedence; all-lost is still `No data` |
| `TestCloseGuard` (11) | same | zero / negative / inf close under `return` and `log_return` refused naming ticker, count and first session (both generators); `next_close` unguarded; a plain `ValueError`, not the 422 |
| `TestDescriptorAndError` (6) | same | `build_data_quality_meta` is `None` only when every category is clean; the old callers' shape; `IncompleteDataError` wording follows `rows_affected` |
| `test_absent_action_columns_mean_zero_not_missing` | `juniper_data/tests/unit/test_equities_generator.py` | the zero-fill stays, now annotated |
| `test_unknown_symbol_skipped_not_fatal`, `test_generate_skips_ticker_whose_download_raises`, `test_generate_handles_ticker_with_no_data`, `test_generate_skips_ticker_shorter_than_lookback` | `test_equities_generator.py`, `test_equities_seq_generator.py` | the skip branches, reached with the gate open, record the loss |

The OHLCV fixtures in the equities test modules carry `Dividends` / `Stock Splits` (zero) columns — the real shape of a yfinance response under `actions=True` — so a fixture *without* them is the anomaly under test, not the baseline.

---

"""

REFERENCE_EDITS = [
    (
        """---

## Equities Sequence: Recurrence-Ready Parameters
""",
        """---

"""
        + REFERENCE_SECTION
        + """## Equities Sequence: Recurrence-Ready Parameters
""",
    ),
]

REFERENCE_DATE_OLD = "**Last Updated:** October 8, 2026"
REFERENCE_DATE_NEW = "**Last Updated:** October 19, 2026"

CHANGELOG_ENTRY = """## [Unreleased]

### Added

- **The equities generators record every symbol they lose, refuse a lost requested one by
  default, guard the return targets, and say whether the price response carried the action
  columns** (W5.7 of juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`:
  F-P5, F-P6, F-P8; the motivating case is
  `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` §1.1, two mints
  of one `dataset_id` 85 s apart, the second lacking the action columns and served as complete).
  - **Lost symbols (F-P5).** Both generators let the universe shrink in silence: a ticker whose
    download raised was logged and skipped, one that returned nothing was logged at INFO and
    skipped, and the artifact was indistinguishable from a complete one. The conditioning loop is
    now one shared `EquitiesGenerator._condition_universe`, which records each lost ticker with its
    reason, and `_apply_incomplete_policy` treats a lost **requested** symbol like an unrescued
    fundamental: **422** `IncompleteDataError` under the shut gate (`rows_affected` 0; the message
    offers `allow_truncation` only, since no rows exist for `incomplete_rows` to accept or drop),
    minted without it and recorded under **`data_quality.dropped_symbols`** (symbol → reason) with a
    WARNING under the open gate. A lost ticker of the default universe is recorded, never refused.
    For `equities_seq` a ticker that conditions to too few rows for one window is a loss too,
    classified before the policy; it keeps its `ticker_vocab` slot with zero windows, so the code
    allocation — and every existing `dataset_id`'s arrays — are unchanged.
  - **The close guard (F-P6).** `return` / `log_return` over a zero, negative or non-finite
    `close` / `next_close` produced ±Inf / NaN in `y_reg`, caught only by the recurrence reader
    after the artifact was minted and cached. `_check_return_target_inputs` refuses per ticker,
    before the target is computed, with a **400** `ValueError` naming the symbol, the row count
    and the first offending session. `next_close` is not guarded (a zero price is a value there).
  - **The action columns (F-P8).** `_condition_one` zero-filled `dividend` / `split_ratio` when the
    response lacked them, with no log line, under the comment "absent means none happened".
    yfinance adds both columns, zero-filled, under `actions=True`, so an absent column is an
    anomalous response (or a cache file written from one). The zero-fill is unchanged; the
    generator now logs it at WARNING and records **`data_quality.actions_present`** (symbol → bool,
    every symbol in the arrays). It cannot tell an incomplete response from "no actions in range",
    so this is recorded, never refused: refusal is a request-level choice. The `equities_seq`
    module docstring and `docs/REFERENCE.md` § Equities Data Quality Annotation document that
    **`dataset_id` is request-addressed** and the meta `checksum` is the content fingerprint.
  - `build_data_quality_meta` gains `dropped` / `actions_present` and returns `None` only when every
    category is clean; the block gains `dropped_symbols` and `actions_present` (both always present
    when the block exists). The `symbols` field description states the rule.
  - **`generator_version` is not bumped** (`equities` 5.0.0, `equities_seq` 6.0.0), as for W1.8: a
    refused request mints nothing, and every request that still mints emits the arrays it emitted
    before. An artifact whose `data_quality` has no `actions_present` key predates this change.
  - Pins: `juniper_data/tests/unit/test_equities_producer_guards.py` (new, 35 tests). The OHLCV
    fixtures of the equities test modules now carry `Dividends` / `Stock Splits` columns — the
    real shape of a yfinance response — so a fixture without them is the anomaly under test;
    `test_absent_action_columns_mean_zero_not_missing` asserts the annotation, and the four
    skip-branch tests (`test_unknown_symbol_skipped_not_fatal`,
    `test_generate_skips_ticker_whose_download_raises`, `test_generate_handles_ticker_with_no_data`,
    `test_generate_skips_ticker_shorter_than_lookback`) open the gate and assert the record.
  - Applied by juniper-ml `util/ad-hoc/2026-10-19_apply_w5_7_producer_guards.py`.
"""

CHANGELOG_EDITS = [
    (
        """## [Unreleased]

## [0.17.1] - 2026-10-10
""",
        CHANGELOG_ENTRY
        + """
## [0.17.1] - 2026-10-10
""",
    ),
]


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

PLAN = [
    ("juniper_data/core/limits.py", LIMITS_EDITS),
    ("juniper_data/generators/equities/generator.py", FLAT_EDITS),
    ("juniper_data/generators/equities_seq/generator.py", SEQ_EDITS),
    ("juniper_data/generators/equities/params.py", PARAMS_EDITS),
    ("juniper_data/tests/unit/test_equities_generator.py", TEST_FLAT_EDITS),
    ("juniper_data/tests/unit/test_equities_seq_generator.py", TEST_SEQ_EDITS),
    ("juniper_data/tests/unit/test_equities_seq_symbol_cap.py", TEST_SYMBOL_CAP_EDITS),
    ("juniper_data/tests/unit/test_artifacts_load_without_pickle.py", TEST_ARTIFACTS_EDITS),
    ("juniper_data/tests/unit/test_equities_cost_basis_drop_edges.py", TEST_COST_BASIS_EDITS),
    ("docs/REFERENCE.md", REFERENCE_EDITS),
    ("CHANGELOG.md", CHANGELOG_EDITS),
]
NEW_TEST_PATH = "juniper_data/tests/unit/test_equities_producer_guards.py"


def _apply(path: Path, edits: list[tuple[str, str]], *, check: bool) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    applied = pending = 0
    for old, new in edits:
        if text.count(new) == 1:
            applied += 1
            continue
        if text.count(old) != 1:
            raise SystemExit(f"{path}: anchor not found exactly once (count={text.count(old)}):\n{old[:300]}")
        pending += 1
        if not check:
            text = text.replace(old, new, 1)
    if not check and pending:
        path.write_text(text, encoding="utf-8")
    return applied, pending


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply W5.7 (F-P5 / F-P6 / F-P8 producer guards) to a juniper-data tree.")
    parser.add_argument("--root", required=True, type=Path, help="the juniper-data tree to edit (a scratch copy at origin/main)")
    parser.add_argument("--check", action="store_true", help="report applied / pending without writing")
    args = parser.parse_args(argv)
    root: Path = args.root.resolve()
    if not (root / "juniper_data" / "generators" / "equities" / "generator.py").exists():
        raise SystemExit(f"{root} is not a juniper-data tree")

    total_applied = total_pending = 0
    for rel, edits in PLAN:
        applied, pending = _apply(root / rel, edits, check=args.check)
        total_applied += applied
        total_pending += pending
        state = "applied" if not pending else ("pending" if args.check else "written")
        print(f"{state}: {rel} ({applied} already, {pending} {'pending' if args.check else 'written'})")

    # REFERENCE.md's two "Last Updated" lines.
    ref = root / "docs" / "REFERENCE.md"
    text = ref.read_text(encoding="utf-8")
    if REFERENCE_DATE_OLD in text:
        if not args.check:
            ref.write_text(text.replace(REFERENCE_DATE_OLD, REFERENCE_DATE_NEW), encoding="utf-8")
        print(f"{'pending' if args.check else 'written'}: docs/REFERENCE.md Last Updated x{text.count(REFERENCE_DATE_OLD)}")
        total_pending += 1
    elif REFERENCE_DATE_NEW in text:
        total_applied += 1
    else:
        raise SystemExit("docs/REFERENCE.md: neither Last Updated line found")

    new_test = root / NEW_TEST_PATH
    if new_test.exists() and new_test.read_text(encoding="utf-8") == NEW_TEST:
        total_applied += 1
        print(f"applied: {NEW_TEST_PATH} (already present)")
    else:
        total_pending += 1
        if not args.check:
            new_test.write_text(NEW_TEST, encoding="utf-8")
        print(f"{'pending' if args.check else 'written'}: {NEW_TEST_PATH}")

    print(f"summary: {total_applied} applied, {total_pending} {'pending' if args.check else 'written'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
