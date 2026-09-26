"""Auto-start through the REAL _auto_start_training + real start_training, over HTTP (scratch)."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

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


def run(fake, *, params='{"tickers": ["AAPL"]}', flag=True):
    TG.reset()
    settings = SimpleNamespace(juniper_data_url=fake.url, auto_dataset="equities", auto_dataset_params=params, allow_truncated_datasets=flag, auto_network="{}")
    m = M.TrainingLifecycleManager()
    try:
        app = SimpleNamespace(state=SimpleNamespace(lifecycle=m))
        with patch.object(m, "_run_training"):
            asyncio.run(_auto_start_training(app, settings))
            if m._training_future is not None:
                m._training_future.result(timeout=10)
        s = m.get_status()
        return (s["dataset_shortfall"] or {}).get("dataset_id"), (s["dataset_shortfall"] or {}).get("acceptance_source"), s["current_dataset"], m._auto_start_failure, fake.posts[-1]["params"] if fake.posts else None, fake.gen_calls
    finally:
        m.shutdown()


fake = FakeJD()
fake.create_mode = "ok"
print("A ok, partial, flag on      :", run(fake))
fake.artifact_mode = "train_only"
r = run(fake)
print("B refused artifact          :", r[:3], "| failure:", (r[3] or "")[:90])
fake.artifact_mode, fake.gen_mode, fake.create_mode = "three", "500", "422"
r = run(fake)
msg = r[3] or ""
print("C list 500 + producer 422   : wire:", r[4], "| WITHHELD:", "WITHHELD" in msg, "| names knob:", "--allow-truncated-datasets" in msg or "JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS" in msg)
print("   remedy:", msg.split("Producer detail:")[1].split("The resulting")[0].strip()[-420:])
fake.close()
