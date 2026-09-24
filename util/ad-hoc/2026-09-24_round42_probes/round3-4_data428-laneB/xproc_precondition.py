"""Lane B: is the PATCH precondition atomic with the write ACROSS PROCESSES on LocalFS (per-host flock)?

Run against a tree given by PYTHONPATH (shipped 3a76a4c, or the N7 mutant whose check sits inside
_version_lock but outside the flock). Two OS processes share one LocalFS directory, as two uvicorn
workers on one host would:

  A: update_tags(ds, ["from-A"], [], precondition) where the precondition is the route's own
     If-Match check (ETag of the state A read at the start), and -- after it has PASSED -- waits
     for a release file, standing in for the gap between the check and the write.
  B: an unconditional update_tags(ds, ["from-B"], []) started while A sits in that gap.

Docs: "the atomicity is per host ... LocalFS orders processes with an advisory flock". If the check
is inside the flock, B cannot finish while A is in the gap. If it is not, B's write lands between
A's passed check and A's write -- A's If-Match named a state that no longer holds when it writes.
"""

from __future__ import annotations

import multiprocessing as mp
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np


def proc_a(d: str, etag0: str) -> None:
    from juniper_data.api.http_cache import body_etag, write_preconditions_hold
    from juniper_data.api.routes.datasets import _PUBLIC_META
    from juniper_data.storage.local_fs import LocalFSDatasetStore

    store = LocalFSDatasetStore(Path(d))

    def precondition(current) -> bool:
        ok = write_preconditions_hold(etag0, None, body_etag(_PUBLIC_META.dump_json(current, by_alias=True)))
        (Path(d) / "A_checked").write_text(f"{ok} tags={current.tags}")
        deadline = time.time() + 6
        while not (Path(d) / "release").exists() and time.time() < deadline:
            time.sleep(0.01)
        return ok

    try:
        meta = store.update_tags("ds", ["from-A"], [], precondition)
        (Path(d) / "A_result").write_text(f"OK wrote tags={meta.tags}")
    except Exception as exc:  # noqa: BLE001
        (Path(d) / "A_result").write_text(f"{type(exc).__name__}")


def proc_b(d: str) -> None:
    from juniper_data.storage.local_fs import LocalFSDatasetStore

    store = LocalFSDatasetStore(Path(d))
    meta = store.update_tags("ds", ["from-B"], [])
    (Path(d) / "B_done").write_text(f"wrote tags={meta.tags}")


def main() -> None:
    from juniper_data.api.http_cache import body_etag
    from juniper_data.api.routes.datasets import _PUBLIC_META
    from juniper_data.core.models import DatasetMeta
    from juniper_data.storage.local_fs import LocalFSDatasetStore

    d = Path(sys.argv[1])
    d.mkdir(parents=True, exist_ok=True)
    for f in ("A_checked", "A_result", "B_done", "release"):
        (d / f).unlink(missing_ok=True)
    store = LocalFSDatasetStore(d)
    meta = DatasetMeta(dataset_id="ds", generator="spiral", generator_version="3.0.0", params={"seed": 1}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=datetime(2026, 9, 22, tzinfo=UTC), checksum="ab" * 32)
    x = np.zeros((2, 2), dtype=np.float32)
    store.save("ds", meta, {"X_train": x, "y_train": x, "X_test": x, "y_test": x})
    etag0 = body_etag(_PUBLIC_META.dump_json(store.get_meta("ds"), by_alias=True))

    ctx = mp.get_context("spawn")
    a = ctx.Process(target=proc_a, args=(str(d), etag0))
    a.start()
    t0 = time.time()
    while not (d / "A_checked").exists() and time.time() - t0 < 20:
        time.sleep(0.01)
    print("A's precondition:", (d / "A_checked").read_text())
    b = ctx.Process(target=proc_b, args=(str(d),))
    b.start()
    t1 = time.time()
    while not (d / "B_done").exists() and time.time() - t1 < 3:
        time.sleep(0.01)
    b_in_gap = (d / "B_done").exists()
    print("B finished while A sat between its PASSED check and its write:", b_in_gap, "|", (d / "B_done").read_text() if b_in_gap else "(blocked)")
    (d / "release").write_text("go")
    a.join(20)
    b.join(20)
    print("A:", (d / "A_result").read_text())
    print("final tags:", store.get_meta("ds").tags)
    print("VERDICT:", "A's If-Match was STALE when it wrote, yet it succeeded (check not atomic with the write across processes)" if b_in_gap and (d / "A_result").read_text().startswith("OK") else "B was held off by the flock: check and write atomic across processes")


if __name__ == "__main__":
    main()
