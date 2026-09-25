"""8f28272: #685's start-fresh param carry-over x #686's partition provenance, over real HTTP (scratch)."""

from __future__ import annotations

import logging
import os
import sys
from unittest.mock import patch

import torch

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.CRITICAL)

from fakejd2 import FakeJD  # noqa: E402

import api.lifecycle.manager as M  # noqa: E402

fake = FakeJD()
os.environ["JUNIPER_DATA_URL"] = fake.url
os.environ.pop("JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS", None)
m = M.TrainingLifecycleManager()
calls = {"reset": 0, "reapply": []}
real_reset = m._start_fresh_reset_locked
real_reapply = getattr(m, "_reapply_carried_params_locked", None)


def spy_reset():
    calls["reset"] += 1
    return real_reset()


def spy_reapply(carried):
    calls["reapply"].append(dict(carried))
    return real_reapply(carried)


def start(**kw):
    with patch.object(m, "_run_training"):
        m.start_training(**kw)
        if m._training_future is not None:
            m._training_future.result(timeout=10)


def rec():
    s = m.get_status()
    return (s["dataset_shortfall"] or {}).get("dataset_id"), s["current_dataset"], sorted(m._described_partitions)


try:
    m.stage_dataset_config(dataset_type="equities", params={"tickers": ["AAPL"]})
    start()
    fetched_val, fetched_test = m._val_x, m._test_x
    print("partial fetch            :", rec())
    start(X=torch.randn(8, 2), y=torch.randn(8, 2))
    print("train-only inline        :", rec())
    m.update_params({"max_hidden_units": 32, "output_epochs": 60})
    net_before = m.network
    with patch.object(m, "_start_fresh_reset_locked", side_effect=spy_reset), (patch.object(m, "_reapply_carried_params_locked", side_effect=spy_reapply) if real_reapply else patch.object(m, "logger")):
        start(start_fresh=True)
    print("start_fresh (retained)   :", rec(), "| network rebuilt:", m.network is not net_before, "| reset calls:", calls["reset"], "| reapplied max_hidden_units/output_epochs:", [(c.get("max_hidden_units"), c.get("output_epochs")) for c in calls["reapply"]], "| live:", m.network.max_hidden_units, m.network.output_epochs)
    print("   fetch's val/test still loaded:", m._val_x is fetched_val, m._test_x is fetched_test)
    with patch.object(m, "_start_fresh_reset_locked", side_effect=spy_reset), (patch.object(m, "_reapply_carried_params_locked", side_effect=spy_reapply) if real_reapply else patch.object(m, "logger")):
        start(start_fresh=True, X=torch.randn(8, 2), y=torch.randn(8, 2))
    print("start_fresh + inline X   :", rec(), "| reset calls:", calls["reset"], "| live:", m.network.max_hidden_units, m.network.output_epochs)
    # A start-fresh whose re-application RAISES after the data was bound: is the record still the data's?
    if real_reapply:
        with patch.object(m, "_reapply_carried_params_locked", side_effect=ValueError("forced")):
            try:
                start(start_fresh=True, X=torch.randn(8, 2), y=torch.randn(8, 2), X_val=torch.randn(4, 2), y_val=torch.randn(4, 2))
                print("forced reapply failure   : started?!")
            except ValueError as exc:
                print("forced reapply failure   :", exc, "->", rec(), "| test still the fetch's:", m._test_x is fetched_test)
finally:
    m.shutdown()
    fake.close()
