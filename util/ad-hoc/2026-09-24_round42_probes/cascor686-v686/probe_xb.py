"""X-B (APD-CASCOR-013) lifecycle across every entry path, through the REAL _reload_dataset over HTTP (scratch)."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

import torch

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.CRITICAL)
for name in ("", "api", "cascor", "juniper_cascor"):
    logging.getLogger(name).setLevel(logging.CRITICAL)

from fakejd import FakeJD  # noqa: E402

import api.lifecycle.manager as M  # noqa: E402
from api.app import _auto_start_training  # noqa: E402

TG = M._TRUNCATABLE_GENERATORS
fake = FakeJD()
fake.create_mode = "ok"
os.environ["JUNIPER_DATA_URL"] = fake.url
os.environ["JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS"] = "true"
TG.reset()


def sf(m):
    s = m.get_status()
    d = s["dataset_shortfall"]
    return (d or {}).get("dataset_id"), s["current_dataset"], (None if m._train_x is None else tuple(m._train_x.shape))


def start(m, **kw):
    with patch.object(m, "_run_training"):
        try:
            m.start_training(**kw)
            if m._training_future is not None:
                m._training_future.result(timeout=10)
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {str(exc)[:70]}"


def swap(m, **cfg):
    m._experimental_functions_enabled = True
    with patch.object(m.state_machine, "is_started", return_value=True), patch.object(m, "save_snapshot", return_value=None), patch.object(m, "_run_training"):
        try:
            r = m.swap_dataset_live(**cfg)
            return r["status"]
        except Exception as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {str(exc)[:70]}"


m = M.TrainingLifecycleManager()
try:
    m.stage_dataset_config(dataset_type="equities", params={"tickers": ["AAPL"]})
    print("1 staged fetch             :", start(m), sf(m))
    print("2 Stop->Start retained     :", start(m), sf(m))
    m.reset()
    print("3 reset()                  :", sf(m))
    print("3b start after reset       :", start(m), sf(m))
    print("3c start_fresh on retained :", start(m, start_fresh=True), sf(m))
    print("4 inline X                 :", start(m, X=torch.zeros(8, 2), y=torch.zeros(8, 2)), sf(m))
    m.stage_dataset_config(dataset_type="equities", params={"tickers": ["MSFT"]})
    print("5 staged fetch #2          :", start(m), sf(m))
    fake.artifact_mode = "train_only"
    m.stage_dataset_config(dataset_type="equities", params={"tickers": ["IBM"]})
    print("6 refused artifact (staged):", start(m), sf(m), "pending kept:", m.get_pending_dataset_config() is not None)
    fake.artifact_mode, fake.create_mode = "three", "422"
    print("7 refused 422 (staged)     :", start(m), sf(m))
    m.clear_pending_dataset_config()
    fake.create_mode = "ok"
    before = sf(m)
    print("8 live swap ok             :", swap(m, dataset_type="equities", params={"tickers": ["NVDA"]}), sf(m), "(before:", before, ")")
    fake.create_mode = "422"
    print("9 live swap refused 422    :", swap(m, dataset_type="equities", params={"tickers": ["ORCL"]}), sf(m))
    fake.create_mode, fake.artifact_mode = "ok", "train_only"
    print("10 live swap refused art.  :", swap(m, dataset_type="equities", params={"tickers": ["AMD"]}), sf(m))
    fake.artifact_mode = "three"
    real = M.TrainingLifecycleManager._artifact_to_tensors
    polled = {}

    def convert_and_cancel(arrays):
        polled["mid"] = m.get_status()["dataset_shortfall"]["dataset_id"]
        m._swap_cancel_requested.set()
        return real(arrays)

    with patch.object(M.TrainingLifecycleManager, "_artifact_to_tensors", side_effect=convert_and_cancel):
        print("11 live swap cancelled     :", swap(m, dataset_type="equities", params={"tickers": ["INTC"]}), sf(m), "mid-conversion poll saw:", polled["mid"])
    # swap that fetches OK then is refused by the resize/pad step (dataset wider than capacity is grown, so force a ValueError)
    with patch.object(m, "_pad_dataset_for_network", side_effect=ValueError("forced post-fetch refusal")):
        print("12 swap refused post-fetch :", swap(m, dataset_type="equities", params={"tickers": ["QCOM"]}), sf(m))
    # a pending staged config beside inline X: the staged fetch wins
    m.stage_dataset_config(dataset_type="equities", params={"tickers": ["TSLA"]})
    print("13 inline X + staged cfg   :", start(m, X=torch.zeros(8, 2), y=torch.zeros(8, 2), dataset_shortfall={"dataset_id": "caller"}), sf(m))
    # inline X + staged cfg whose fetch FAILS: X is bound, the caller's annotation stays with it
    fake.create_mode = "422"
    m.stage_dataset_config(dataset_type="equities", params={"tickers": ["F"]})
    print("14 inline X + staged 422   :", start(m, X=torch.zeros(9, 2), y=torch.zeros(9, 2), dataset_shortfall={"dataset_id": "caller2"}), sf(m))
    m.clear_pending_dataset_config()
    print("15 inline train, val kept? :", "val rows:", None if m._val_x is None else m._val_x.shape[0], "test rows:", None if m._test_x is None else m._test_x.shape[0], "| shortfall:", sf(m)[0])
finally:
    m.shutdown()

print("\n== auto-start ==")
fake.create_mode, fake.artifact_mode = "ok", "three"
settings = SimpleNamespace(juniper_data_url=fake.url, auto_dataset="equities", auto_dataset_params='{"tickers": ["AAPL"]}', allow_truncated_datasets=True, auto_network="{}")
for mode in ("three", "train_only"):
    fake.artifact_mode = mode
    m = M.TrainingLifecycleManager()
    try:
        app = SimpleNamespace(state=SimpleNamespace(lifecycle=m))
        with patch.object(m, "_run_training"):
            asyncio.run(_auto_start_training(app, settings))
            if m._training_future is not None:
                m._training_future.result(timeout=10)
        print(f"auto-start [{mode:10s}]:", sf(m), "| failure:", (m._auto_start_failure or "")[:80])
    finally:
        m.shutdown()
fake.close()
