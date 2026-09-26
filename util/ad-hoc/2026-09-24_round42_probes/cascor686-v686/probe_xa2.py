"""X-A staged path end to end: real manager, real client, real HTTP, env-driven Settings (scratch)."""

from __future__ import annotations

import logging
import os
import sys
from unittest.mock import patch

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.CRITICAL)

from fakejd import FakeJD  # noqa: E402

import api.lifecycle.manager as M  # noqa: E402

TG = M._TRUNCATABLE_GENERATORS
EQ_NOT_TRUNC = [{"name": "equities", "version": "5", "description": "e", "available": True, "install_hint": None, "schema": {"type": "object", "properties": {"tickers": {"type": "array"}}}}]


def start(m):
    with patch.object(m, "_run_training"):
        try:
            m.start_training()
            if m._training_future is not None:
                m._training_future.result(timeout=10)
            return "started"
        except Exception as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {exc}"


def names_knob(msg):
    return "--allow-truncated-datasets" in msg or "JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS" in msg


os.environ["JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS"] = "true"

print("== A. flag ON, list 500s, producer 422s: withheld on the wire, staged config kept, retry forwards ==")
fake = FakeJD()
os.environ["JUNIPER_DATA_URL"] = fake.url
TG.reset()
m = M.TrainingLifecycleManager()
try:
    fake.gen_mode = "500"
    m.stage_dataset_config(dataset_type="equities", params={"tickers": ["AAPL"]})
    out = start(m)
    print(" wire params:", fake.posts[-1]["params"], "| pending kept:", m.get_pending_dataset_config() is not None)
    print(" WITHHELD in msg:", "WITHHELD" in out, "| names knob:", names_knob(out))
    fake.gen_mode = "ok"
    out2 = start(m)
    print(" retry wire params:", fake.posts[-1]["params"], "| gen_calls:", fake.gen_calls)
    fake.create_mode = "ok"
    out3 = start(m)
    print(" third start:", out3, "| wire:", fake.posts[-1]["params"], "| gen_calls (memo hit => unchanged):", fake.gen_calls)
    print(" shortfall after success:", (m.get_status()["dataset_shortfall"] or {}).get("dataset_id"), "| acceptance_source:", (m.get_status()["dataset_shortfall"] or {}).get("acceptance_source"))
finally:
    m.shutdown()
    fake.close()

print("\n== B. runtime URL change: memo follows JUNIPER_DATA_URL ==")
f1, f2 = FakeJD(), FakeJD()
f1.listing = EQ_NOT_TRUNC
TG.reset()
m = M.TrainingLifecycleManager()
try:
    os.environ["JUNIPER_DATA_URL"] = f1.url
    m.stage_dataset_config(dataset_type="equities", params={"tickers": ["AAPL"]})
    start(m)
    os.environ["JUNIPER_DATA_URL"] = f2.url
    start(m)
    print(" f1 wire:", f1.posts[-1]["params"], "f1 gen_calls:", f1.gen_calls)
    print(" f2 wire:", f2.posts[-1]["params"], "f2 gen_calls:", f2.gen_calls)
    print(" memo keys:", sorted(TG._by_source))
finally:
    m.shutdown()
    f1.close()
    f2.close()

print("\n== C. caller sent allow_truncation: null -- remedy with the flag OFF vs ON ==")
for flag in ("false", "true"):
    fake = FakeJD()
    os.environ["JUNIPER_DATA_URL"] = fake.url
    os.environ["JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS"] = flag
    TG.reset()
    m = M.TrainingLifecycleManager()
    try:
        m.stage_dataset_config(dataset_type="equities", params={"tickers": ["AAPL"], "allow_truncation": None})
        out = start(m)
        remedy = out.split("Producer detail:")[1] if "Producer detail:" in out else out
        print(f" flag={flag}: wire={fake.posts[-1]['params']} gen_calls={fake.gen_calls}\n   remedy: {remedy.split('The resulting dataset')[0].strip()[-330:]}")
    finally:
        m.shutdown()
        fake.close()
os.environ["JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS"] = "true"

print("\n== D. flag ON, list read, generator NOT declared, producer 422s ==")
fake = FakeJD()
fake.listing = EQ_NOT_TRUNC
os.environ["JUNIPER_DATA_URL"] = fake.url
TG.reset()
m = M.TrainingLifecycleManager()
try:
    m.stage_dataset_config(dataset_type="equities", params={"tickers": ["AAPL"]})
    out = start(m)
    print(" names knob:", names_knob(out), "| 'does not declare':", "does not declare" in out)
finally:
    m.shutdown()
    fake.close()
