"""Lane B (r42d): a second process that holds LocalFS's cross-process lock for one (absent) id.

Run inside a tree: run_in_tree.bash <tree> stripe_holder.py <storage> <holder_id> <seconds> <ready_file>
"""

import os
import sys
import time
from pathlib import Path

import juniper_data
from juniper_data.storage.local_fs import LocalFSDatasetStore

TREE = Path(os.getcwd()).resolve()
assert Path(juniper_data.__file__).resolve().is_relative_to(TREE), juniper_data.__file__

storage, holder_id, seconds, ready = Path(sys.argv[1]), sys.argv[2], float(sys.argv[3]), Path(sys.argv[4])
store = LocalFSDatasetStore(storage)
with store._meta_write_lock(holder_id):
    ready.write_text(str(store._lock_path(holder_id)))
    time.sleep(seconds)
