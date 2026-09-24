#!/usr/bin/env python3
"""Lane A: reproduce APD-DATA-056 (lone-surrogate tag -> 500) against juniper-data origin/main,
in-process via TestClient (no port bound), LocalFS store rooted in the scratch dir.

Also records: the PATCH that adds the tag, a later GET / PATCH / filter, whether the ERROR log
carries the surrogate, and whether removing the tag heals the dataset. A control run with an
ordinary tag shows the same sequence returns 200s (so the 500s are caused by the surrogate)."""
from __future__ import annotations

import io
import logging
import os
import shutil
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
sys.path.insert(0, f"{S}/src/juniper-data-pre428")
for k in [k for k in os.environ if k.startswith("JUNIPER_DATA_")]:
    del os.environ[k]
store_dir = f"{S}/data056_store_pre428"
shutil.rmtree(store_dir, ignore_errors=True)
os.makedirs(store_dir)
os.environ["JUNIPER_DATA_STORAGE_PATH"] = store_dir
os.environ["JUNIPER_DATA_REQUIRE_AUTH"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

import juniper_data  # noqa: E402
from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.settings import get_settings  # noqa: E402

print("juniper_data imported from:", juniper_data.__file__)
get_settings.cache_clear() if hasattr(get_settings, "cache_clear") else None
app = create_app()

log_buf = io.StringIO()
handler = logging.StreamHandler(log_buf)
handler.setLevel(logging.ERROR)


def run(tag_json: str, label: str) -> None:
    print(f"\n===== {label}")
    with TestClient(app, raise_server_exceptions=False) as client:
        logging.getLogger("juniper_data").addHandler(handler)
        r = client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_points_per_spiral": 20, "seed": 7}})
        print("create:", r.status_code)
        ds = r.json()["dataset_id"]
        body = '{"add_tags": [' + tag_json + "]}"
        r = client.patch(f"/v1/datasets/{ds}/tags", content=body.encode("utf-8"), headers={"Content-Type": "application/json"})
        print("PATCH add tag:", r.status_code, r.text[:120])
        r = client.get(f"/v1/datasets/{ds}")
        print("GET metadata:", r.status_code, r.text[:80])
        r = client.patch(f"/v1/datasets/{ds}/tags", json={"add_tags": ["ordinary"]})
        print("PATCH ordinary tag:", r.status_code)
        r = client.get("/v1/datasets/filter")
        print("GET /v1/datasets/filter:", r.status_code)
        r = client.get(f"/v1/datasets/{ds}/artifact")
        print("GET artifact:", r.status_code)
        r = client.patch(f"/v1/datasets/{ds}/tags", content=('{"remove_tags": [' + tag_json + "]}").encode("utf-8"), headers={"Content-Type": "application/json"})
        print("PATCH remove tag:", r.status_code)
        r = client.get(f"/v1/datasets/{ds}")
        print("GET metadata after removal:", r.status_code, "tags=", r.json().get("tags") if r.status_code == 200 else None)
        client.delete(f"/v1/datasets/{ds}")
        logging.getLogger("juniper_data").removeHandler(handler)


run('"ok-tag"', "CONTROL: ordinary tag")
log_buf.truncate(0)
log_buf.seek(0)
run('"\\ud800"', "TEST: lone surrogate \\ud800")
logs = log_buf.getvalue()
print("\nERROR-level log records captured:", logs.count("Response serialization failed"), "x 'Response serialization failed'")
print("log text carries the surrogate (as \\ud800 escape or raw)?", ("\\ud800" in logs) or ("\ud800" in logs), "| mentions 'surrogate':", "surrogate" in logs)
tail = [ln for ln in logs.splitlines() if "surrogate" in ln or "ud800" in ln][:3]
print("sample log lines:", tail)
shutil.rmtree(store_dir, ignore_errors=True)
