#!/usr/bin/env python3
"""Validate LMURegressor (juniper-recurrence-model) on the irregular_sine dataset.

End-to-end check (recurrence "Item 2"): generate the irregular-Δt sine synthetic
(juniper-data #188), feed it to ``LMURegressor`` through the §9.1c loader
(``sequence_data_from_arrays``), and confirm two things on a *purpose-built* irregular-Δt
dataset (signal known, timing essential):

  1. the model trains + generalises on the real generator's 3-D output, and
  2. the Δt-native behaviour does real work — shuffling the per-step gaps degrades predictions.

A persistence baseline (predict = last observed value) is reported for context.

Run in an env with BOTH juniper-data and juniper-recurrence-model importable, e.g.::

    /opt/miniforge3/envs/JuniperData/bin/pip install juniper-recurrence-model
    /opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/verify_recurrence_on_irregular_sine.py

Project:     Juniper / juniper-ml (cross-package validation)
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
"""

from __future__ import annotations

import numpy as np

from juniper_data.generators.irregular_sine.generator import IrregularSineGenerator
from juniper_data.generators.irregular_sine.params import IrregularSineParams
from juniper_recurrence_model import LMURegressor, sequence_data_from_arrays


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean(axis=0)) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def main() -> int:
    params = IrregularSineParams(n_steps=4000, lookback=32, horizon=1, jitter=0.6, n_components=3, seed=0)
    arrays = IrregularSineGenerator.generate(params)
    train = sequence_data_from_arrays(arrays, "train")
    test = sequence_data_from_arrays(arrays, "test")
    pos = train.dt[train.dt > 0]
    print(f"irregular_sine: train X={train.X.shape}  test X={test.X.shape}  "
          f"dt in [{pos.min():.3f}, {train.dt.max():.3f}] (jitter={params.jitter})")

    model = LMURegressor(d=24)  # theta data-driven from the windows' dt
    model.fit(train.X, train.y, **train.fit_kwargs())
    print(f"resolved theta = {model.theta:.3f}  (d={model.d})")

    # (1) fit + generalise
    r2_train = _r2(train.y, model.predict(train.X, **train.fit_kwargs()))
    test_pred = model.predict(test.X, **test.fit_kwargs())
    r2_test = _r2(test.y, test_pred)

    # persistence baseline: predict the last observed value of the window
    persistence = test.X[:, -1, :]
    r2_persist = _r2(test.y, persistence)

    print(f"[fit]   train R^2 = {r2_train:.4f}   test R^2 = {r2_test:.4f}   (persistence baseline R^2 = {r2_persist:.4f})")

    # (2) Δt-native win: shuffle each window's per-step gaps (same multiset, dt[:,0] kept 0)
    rng = np.random.default_rng(0)
    dt_shuf = test.dt.copy()
    for i in range(dt_shuf.shape[0]):
        dt_shuf[i, 1:] = test.dt[i, rng.permutation(test.dt.shape[1] - 1) + 1]
    r2_shuf = _r2(test.y, model.predict(test.X, dt=dt_shuf, target_dt=test.target_dt))
    print(f"[Δt]    test R^2 TRUE dt = {r2_test:.4f}   SHUFFLED dt = {r2_shuf:.4f}   (degradation = {r2_test - r2_shuf:.4f})")

    fits = r2_test > 0.5
    uses_dt = r2_shuf < r2_test
    beats_persistence = r2_test >= r2_persist
    print(f"\nfits (test R^2>0.5): {fits}   uses Δt (true>shuffled): {uses_dt}   >= persistence: {beats_persistence}")
    ok = fits and uses_dt
    print("RESULT:", "PASS — LMURegressor consumes irregular_sine end-to-end and the Δt channel matters"
          if ok else "REVIEW — metrics not as expected; inspect above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
