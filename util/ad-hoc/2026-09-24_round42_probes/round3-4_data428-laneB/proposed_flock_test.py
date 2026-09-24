"""Lane B: a proposed in-process test that pins the precondition under the CROSS-PROCESS flock.

flock(2) locks belong to open file descriptions, so a second open() of the lock file conflicts with
the store's lock even inside one process. Run against the shipped tree (expect HELD) and the N7
mutant (expect NOT HELD).
"""

import fcntl
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from juniper_data.core.models import DatasetMeta
from juniper_data.storage.local_fs import LocalFSDatasetStore

d = Path(sys.argv[1])
d.mkdir(parents=True, exist_ok=True)
store = LocalFSDatasetStore(d)
x = np.zeros((2, 2), dtype=np.float32)
store.save("ds", DatasetMeta(dataset_id="ds", generator="spiral", generator_version="3.0.0", params={}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=datetime(2026, 9, 22, tzinfo=UTC), checksum="ab" * 32), {"X_train": x, "y_train": x, "X_test": x, "y_test": x})
seen: list[bool] = []


def check(_current) -> bool:
    fd = os.open(store._lock_path("ds"), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(fd, fcntl.LOCK_UN)
        seen.append(False)  # we could take it: the store was NOT holding the flock
    except BlockingIOError:
        seen.append(True)
    finally:
        os.close(fd)
    return True


store.update_tags("ds", ["t"], [], check)
print("flock held while the precondition ran:", seen)
