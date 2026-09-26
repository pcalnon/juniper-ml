"""Lane B (r42d): two WORKER PROCESSES create one dataset id; is create-if-absent atomic across them?

Worker B saves first and is held INSIDE its save (flock held, nothing written yet) for 3 s.
Worker A starts its save_versioned during that hold. Correct code: A waits for the flock, then
re-checks, finds B's dataset and writes nothing. If the re-check ran outside the flock (my MX10),
A would find nothing, wait, and then overwrite B's acknowledged create.
Run inside a tree (head, or a mutated copy): python xproc_create_race.py <workdir>
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import juniper_data

TREE = Path(os.getcwd()).resolve()
assert Path(juniper_data.__file__).resolve().is_relative_to(TREE), juniper_data.__file__

WORKER = r"""
import sys, time
from datetime import UTC, datetime
from pathlib import Path
import numpy as np
from juniper_data.core.models import DatasetMeta
from juniper_data.storage.local_fs import LocalFSDatasetStore
storage, who, hold = Path(sys.argv[1]), sys.argv[2], float(sys.argv[3])
store = LocalFSDatasetStore(storage)
meta = DatasetMeta(dataset_id="race-id", generator="spiral", generator_version="3.0.0", params={"seed": 1}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=datetime.now(UTC), checksum="ab" * 32, tags=["from-" + who], description=who)
x = np.arange(8, dtype=np.float32).reshape(4, 2)
arrays = {"X_train": x[:2], "y_train": x[:2], "X_test": x[2:], "y_test": x[2:]}
real_save = store.save
def held_save(*a):
    (storage.parent / ("in-save." + who)).write_text("1")
    time.sleep(hold)
    return real_save(*a)
store.save = held_save
got = store.save_versioned("race-id", meta, arrays)
print(who, "answered with", got.tags)
"""


def main() -> None:
    work = Path(sys.argv[1])
    storage = work / "storage"
    storage.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONPATH": str(TREE)}
    b = subprocess.Popen([sys.executable, "-c", WORKER, str(storage), "B", "3"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + 60
    while not (work / "in-save.B").exists():
        if time.monotonic() > deadline or b.poll() is not None:
            raise SystemExit(f"B never reached its save: {b.communicate()}")
        time.sleep(0.01)
    a = subprocess.Popen([sys.executable, "-c", WORKER, str(storage), "A", "0"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out_b, err_b = b.communicate(timeout=60)
    out_a, err_a = a.communicate(timeout=60)
    stored = json.loads((storage / "race-id.meta.json").read_text())
    print(json.dumps({"tree": str(TREE), "B": out_b.strip() or err_b[-300:], "A": out_a.strip() or err_a[-300:], "stored_tags": stored["tags"], "A_saved_over_B": stored["tags"] == ["from-A"]}))


if __name__ == "__main__":
    main()
