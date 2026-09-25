#!/usr/bin/env python3
"""Child process for create_race.py: one LocalFS store on a shared directory, one save_versioned.

Usage: create_child.py <storage_dir> <dataset_id> <tag> <named:0|1> <sleep_in_save_seconds> <out_json>
Writes {"t_start", "t_enter_save", "t_end", "returned_tags", "saved", "juniper_data"} to out_json.
"""

import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

import juniper_data
from juniper_data.core.models import DatasetMeta
from juniper_data.storage.local_fs import LocalFSDatasetStore

storage, dataset_id, tag, named, sleep_s, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] == "1", float(sys.argv[5]), sys.argv[6]
assert Path(juniper_data.__file__).resolve().is_relative_to(Path(os.environ["EXPECTED_TREE"]).resolve())
store = LocalFSDatasetStore(Path(storage))
record = {"t_start": time.time(), "t_enter_save": None, "saved": False, "juniper_data": juniper_data.__file__}
real_save = store.save


def slow_save(*args, **kwargs):
    record["t_enter_save"] = time.time()
    record["saved"] = True
    if sleep_s:
        time.sleep(sleep_s)
    return real_save(*args, **kwargs)


store.save = slow_save
meta = DatasetMeta(dataset_id=dataset_id, generator="spiral", generator_version="3.0.0", params={}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=dt.datetime(2026, 9, 1, tzinfo=dt.UTC), checksum="cd" * 32, tags=[tag], dataset_name="probe-name" if named else None)
returned = store.save_versioned(dataset_id, meta, {"X_train": np.zeros((2, 2), dtype=np.float32)})
record["t_end"] = time.time()
record["returned_tags"] = sorted(returned.tags) if returned is not None else None
Path(out).write_text(json.dumps(record))
