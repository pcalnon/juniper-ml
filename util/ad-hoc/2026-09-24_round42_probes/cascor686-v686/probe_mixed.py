"""Inline train-only start after a PARTIAL staged fetch: which partitions does the run use, and what does it report? (scratch)"""

import logging
import os
import sys
from unittest.mock import patch

import torch

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.CRITICAL)

from fakejd import FakeJD  # noqa: E402

import api.lifecycle.manager as M  # noqa: E402

fake = FakeJD()
fake.create_mode = "ok"
os.environ["JUNIPER_DATA_URL"] = fake.url
os.environ["JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS"] = "true"
m = M.TrainingLifecycleManager()
try:
    m.stage_dataset_config(dataset_type="equities", params={"tickers": ["AAPL"]})
    with patch.object(m, "_run_training"):
        m.start_training()
    fetched_val, fetched_test = m._val_x, m._test_x
    print("after partial fetch : shortfall", m.get_status()["dataset_shortfall"]["dataset_id"], "| val/test rows", fetched_val.shape[0], fetched_test.shape[0])
    with patch.object(m, "_run_training") as run:
        m.start_training(X=torch.zeros(8, 2), y=torch.zeros(8, 2))  # what POST /v1/training/start sends for inline_data {train_x, train_y}
        m._training_future.result(timeout=10)
    _, _, xv, _ = run.call_args.args[:4]
    print("inline train-only   : shortfall", m.get_status()["dataset_shortfall"], "| current_dataset", m.get_status()["current_dataset"])
    print("                      run's in-loop val IS the partial fetch's:", xv is fetched_val, "| reported test IS the partial fetch's:", m._test_x is fetched_test)
    print("                      GET /v1/metrics dataset_shortfall:", m.get_metrics().get("dataset_shortfall"))
finally:
    m.shutdown()
    fake.close()
