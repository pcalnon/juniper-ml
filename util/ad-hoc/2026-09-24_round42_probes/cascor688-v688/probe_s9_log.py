"""S9 in isolation: a clean staged fetch, then auto-start hands start_training a PARTIAL train+val fetch (scratch).

Prints what the log says and what /v1/training/status says, over real HTTP.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.CRITICAL)

from fakejd2 import PARTIAL_META, FakeJD  # noqa: E402

import api.lifecycle.manager as M  # noqa: E402
from api.app import _auto_start_training  # noqa: E402

fake = FakeJD()
os.environ["JUNIPER_DATA_URL"] = fake.url
m = M.TrainingLifecycleManager()
try:
    fake.meta = {}
    m.stage_dataset_config(dataset_type="equities", params={"tickers": ["AAPL"]})
    with patch.object(m, "_run_training"):
        m.start_training()
    clean_test = m._test_x
    fake.meta, fake.artifact_mode = dict(PARTIAL_META), "train_val"
    settings = SimpleNamespace(juniper_data_url=fake.url, auto_dataset="equities", auto_dataset_params='{"tickers": ["AUTO"]}', allow_truncated_datasets=False, auto_network="{}")
    spy = MagicMock()
    with patch.object(m, "_run_training"), patch.object(m, "logger", spy):
        asyncio.run(_auto_start_training(SimpleNamespace(state=SimpleNamespace(lifecycle=m)), settings))
    warned = [c.args[0] % c.args[1:] if len(c.args) > 1 else c.args[0] for c in spy.warning.call_args_list]
    s = m.get_status()
    print("auto_start_failure :", m._auto_start_failure)
    print("log (WARNING)      :", [w[:95] for w in warned if "DATASET" in w])
    print("status shortfall   :", s["dataset_shortfall"])
    print("status current     :", s["current_dataset"])
    print("train/val are auto-start's partial ds-2; test is the clean fetch's:", m._test_x is clean_test, "| described:", sorted(m._described_partitions))
finally:
    m.shutdown()
    fake.close()
