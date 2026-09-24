#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-09-23_data_additive_overflow_repro.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-09-23
# Last Modified: 2026-09-23
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#    Reproduce, through juniper-data's real API (FastAPI TestClient, in-memory store), what a
#    caller receives when an ADDITIVE-sizing request passes the field check but its inflated
#    size knob exceeds the generator cap.
#
#    Found by the perf lane (PF-2 axis 2, 2026-09-23): `n_points_per_spiral` 10,000 at the
#    suite split (val_percent 40, test_percent 30, so x1.7) is 17,000 rows per spiral
#    internally. `rescale_generator_params` re-validates and raises a pydantic
#    `ValidationError`; its docstring says that "turns into a 422 at the API boundary".
#    This script records what the boundary actually answers, and where the cause is logged.
#
#    Run it in the JuniperData env, where `juniper_data` resolves to the checkout under test:
#        /opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/2026-09-23_data_additive_overflow_repro.py
#
#    Exit 0 = the answers match the defect as filed (400 generic at 5,883 and 10,000; 201 at
#    5,882). Exit 1 = the behaviour moved; read the table before trusting anything filed.
#####################################################################################################################################################################################################
from __future__ import annotations

import logging
import sys
import tempfile

from fastapi.testclient import TestClient

from juniper_data.api.app import create_app
from juniper_data.api.routes import datasets
from juniper_data.api.settings import Settings
from juniper_data.storage.memory import InMemoryDatasetStore

# The exact partition vocabulary the experiment driver sent (read from a 2026-09-23 run's
# `data/spiral-3.0.0-*.meta.json`): additive sizing, val 40 %, test 30 % -> x1.7.
SUITE_PARAMS = {
    "sizing_mode": "additive",
    "val_percent": 40.0,
    "test_percent": 30.0,
    "n_spirals": 2,
    "seed": 20260807,
    "train_ratio": 0.8,
    "test_ratio": 0.2,
}

# (request, expected status, expected detail prefix) -- 5,882 x 1.7 = 9,999.4 -> 10,000 per
# spiral after rounding up; 5,883 x 1.7 = 10,001.1 -> over the cap. 10,000 is the documented
# field maximum. 10,001 fails the SAME bound on the request itself, and is the control: it
# reaches the route's own `except ValueError` and keeps its diagnostic, which is what makes the
# generic answer at 5,883..10,000 a lost diagnostic rather than a policy. (A first draft of this
# script expected 422 at 10,001, as the PF-2 re-spec's §1 says; the route answers 400, because
# `params` is `dict[str, Any]` and is validated in the route, not at the boundary.)
PROBES = [
    (5882, 201, None),
    (5883, 400, "Invalid request parameters"),
    (10000, 400, "Invalid request parameters"),
    (10001, 400, "Invalid parameters: 1 validation error for SpiralParams"),
]


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def main() -> int:
    capture = _Capture()
    root = logging.getLogger("juniper_data")
    root.addHandler(capture)
    root.setLevel(logging.DEBUG)

    with tempfile.TemporaryDirectory() as storage:
        app = create_app(settings=Settings(storage_path=storage))
        datasets.set_store(InMemoryDatasetStore())
        client = TestClient(app, raise_server_exceptions=False)

        mismatches = 0
        print(f"{'request':>8}  {'status':>6}  {'expected':>8}  detail / where the cause went")
        for n_points, expected, expected_detail in PROBES:
            capture.records.clear()
            body = {"generator": "spiral", "params": {**SUITE_PARAMS, "n_points_per_spiral": n_points}}
            response = client.post("/v1/datasets", json=body)
            detail = response.json().get("detail") if response.headers.get("content-type", "").startswith("application/json") else response.text
            if isinstance(detail, list):
                detail = "; ".join(f"{'.'.join(str(p) for p in e.get('loc', []))}: {e.get('msg')}" for e in detail)
            cause = [f"{r.levelname}:{' '.join(r.getMessage().split())[:120]}" for r in capture.records if "rror" in r.getMessage()]
            detail_ok = expected_detail is None or str(detail).startswith(expected_detail)
            moved = response.status_code != expected or not detail_ok
            mismatches += moved
            print(f"{n_points:>8}  {response.status_code:>6}  {expected:>8}  {' '.join(str(detail).split())[:120]}{'   <-- MOVED' if moved else ''}")
            for line in cause:
                print(f"{'':>28}log {line}")

    print()
    print("defect as filed" if mismatches == 0 else f"{mismatches} probe(s) moved -- re-read before filing")
    return 0 if mismatches == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
