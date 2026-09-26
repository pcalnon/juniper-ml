"""Lane B (r42d): attack LocalFS's lock stripes at head (library level, one case per subprocess).

Cases:
  A  locks/ pre-planted as a symlink to an EMPTY dir outside the root         -> store init?
  B  locks/ pre-planted as a symlink to a dir INSIDE the root                  -> store init?
  C  locks/ pre-planted as a regular FILE                                      -> init, then each lock taker
  D  a FIFO pre-planted at the stripe of id X                                  -> init, then lock X (timeout)
  E  a dangling symlink pre-planted at the stripe of id X                      -> init, then X and a later stripe
  G  the storage dir read-only (chmod 0555) before the store opens             -> init, reads, lock takers
  H  ENOSPC on creating the locks/ DIRECTORY at init (first start, volume out of inodes), then delete
  I  ENOSPC on every new file, stripes created normally first, then delete (the PR's own scenario)
  L  locks/ swapped for a symlink to an outside dir AFTER init: (1) outside dir holds the stripes, (2) it does not
  M  the swap lands between _ensure_lock_dir's check and the O_CREAT open (deterministic stand-in for the race)
  P  PEP 446: is os.open's descriptor inheritable without O_CLOEXEC?
Run inside a tree: run_in_tree.bash <tree> stripe_probe.py <case> <workdir>
"""

from __future__ import annotations

import errno
import json
import os
import stat
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

import juniper_data
from juniper_data.core.models import DatasetMeta
from juniper_data.storage import local_fs
from juniper_data.storage.local_fs import LocalFSDatasetStore

TREE = Path(os.getcwd()).resolve()
assert Path(juniper_data.__file__).resolve().is_relative_to(TREE), juniper_data.__file__


def meta(dataset_id: str, **kw) -> DatasetMeta:
    fields = dict(dataset_id=dataset_id, generator="spiral", generator_version="3.0.0", params={"seed": 1}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=datetime(2026, 9, 22, 20, 0, tzinfo=UTC), checksum="ab" * 32)
    fields.update(kw)
    return DatasetMeta(**fields)


def arrays() -> dict[str, np.ndarray]:
    x = np.arange(8, dtype=np.float32).reshape(4, 2)
    y = np.eye(2, dtype=np.float32)[[0, 1, 0, 1]]
    return {"X_train": x[:2], "y_train": y[:2], "X_test": x[2:], "y_test": y[2:]}


def attempt(label: str, fn) -> dict:
    try:
        out = fn()
        return {"op": label, "ok": True, "result": repr(out)[:80]}
    except BaseException as exc:  # noqa: BLE001
        return {"op": label, "ok": False, "exc": type(exc).__name__, "errno": getattr(exc, "errno", None), "msg": str(exc)[:140]}


def stripe_of(store: LocalFSDatasetStore, dataset_id: str) -> str:
    return store._lock_path(dataset_id).name


def id_on_stripe(store: LocalFSDatasetStore, name: str, avoid: set[str] = frozenset()) -> str:
    for i in range(10_000):
        cand = f"probe-{i:05d}"
        if stripe_of(store, cand) == name and cand not in avoid:
            return cand
    raise RuntimeError("no id on stripe")


def takers(store: LocalFSDatasetStore, dataset_id: str) -> list[dict]:
    return [
        attempt("record_access", lambda: store.record_access(dataset_id)),
        attempt("update_tags", lambda: store.update_tags(dataset_id, ["t"], [])),
        attempt("save_versioned(new id)", lambda: store.save_versioned(dataset_id + "-new", meta(dataset_id + "-new"), arrays())),
        attempt("delete_under_lock", lambda: store.delete_under_lock(dataset_id)),
        attempt("still stored?", lambda: store.get_meta(dataset_id) is not None),
    ]


def case(name: str, work: Path) -> dict:
    storage = work / "storage"
    outside = work / "outside"
    outside.mkdir(parents=True, exist_ok=True)
    storage.mkdir(parents=True, exist_ok=True)
    rec: dict = {"case": name}
    if name == "A":
        (storage / "locks").symlink_to(outside)
        rec["init"] = attempt("init", lambda: LocalFSDatasetStore(storage))
        rec["outside_listing"] = sorted(p.name for p in outside.iterdir())
    elif name == "B":
        (storage / "realocks").mkdir()
        (storage / "locks").symlink_to(storage / "realocks")
        rec["init"] = attempt("init", lambda: LocalFSDatasetStore(storage))
    elif name == "C":
        (storage / "locks").write_text("not a directory")
        box: dict = {}
        rec["init"] = attempt("init", lambda: box.setdefault("s", LocalFSDatasetStore(storage)))
        store = box["s"]
        store.save("victim", meta("victim"), arrays())
        rec["takers"] = takers(store, "victim")
    elif name == "D":
        probe = LocalFSDatasetStore(work / "scratch-store")
        target = "victim"
        stripe = stripe_of(probe, target)
        (storage / "locks").mkdir()
        os.mkfifo(storage / "locks" / stripe)
        box = {}
        rec["init"] = attempt("init", lambda: box.setdefault("s", LocalFSDatasetStore(storage)))
        store = box["s"]
        store.save(target, meta(target), arrays())
        results: list = []
        th = threading.Thread(target=lambda: results.append(takers(store, target)), daemon=True)
        th.start()
        th.join(10)
        rec["fifo_is_fifo"] = stat.S_ISFIFO(os.lstat(storage / "locks" / stripe).st_mode)
        rec["takers"] = results[0] if results else "HUNG (10 s)"
    elif name == "E":
        probe = LocalFSDatasetStore(work / "scratch-store")
        target = "victim"
        stripe = stripe_of(probe, target)
        (storage / "locks").mkdir()
        (storage / "locks" / stripe).symlink_to(outside / "planted.lock")
        box = {}
        rec["init"] = attempt("init", lambda: box.setdefault("s", LocalFSDatasetStore(storage)))
        store = box["s"]
        rec["stripes_after_init"] = sorted(p.name for p in (storage / "locks").iterdir())
        store.save(target, meta(target), arrays())
        rec["takers_on_planted_stripe"] = takers(store, target)
        other = id_on_stripe(store, "f.lock")
        store.save(other, meta(other), arrays())
        rec["takers_on_stripe_f"] = takers(store, other)
        rec["outside_created"] = (outside / "planted.lock").exists()
        # how many of 1,000 ids hash to the planted stripe
        rec["share_of_ids_on_planted_stripe"] = sum(stripe_of(store, f"x-{i}") == stripe for i in range(1000)) / 1000
    elif name == "G":
        os.chmod(storage, 0o555)
        try:
            box = {}
            rec["init"] = attempt("init", lambda: box.setdefault("s", LocalFSDatasetStore(storage)))
            store = box.get("s")
            rec["locks_exists"] = (storage / "locks").exists()
            if store is not None:
                rec["takers"] = takers(store, "victim")
        finally:
            os.chmod(storage, 0o755)
    elif name == "H":
        real_mkdir = Path.mkdir

        def no_inode_mkdir(self, *a, **k):
            if self.name == "locks":
                raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC), str(self))
            return real_mkdir(self, *a, **k)

        # the dataset is on disk first (written while the volume still had room, by an OLDER version)
        pre = LocalFSDatasetStore(work / "pre")  # noqa: F841 -- only to compute nothing; keep storage clean
        seed = LocalFSDatasetStore.__new__(LocalFSDatasetStore)
        # write the dataset files directly with a store over a different root, then move them
        tmp_store = LocalFSDatasetStore(work / "writer")
        tmp_store.save("victim", meta("victim", expires_at=datetime(2026, 9, 22, 21, 0, tzinfo=UTC)), arrays())
        for p in (work / "writer").glob("victim.*"):
            p.rename(storage / p.name)
        del seed
        Path.mkdir = no_inode_mkdir
        real_open = os.open

        class NoInodes:
            def __getattr__(self, n):
                return getattr(os, n)

            @staticmethod
            def open(path, flags, mode=0o777, *, dir_fd=None):
                if flags & os.O_CREAT and not os.path.lexists(path):
                    raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC), os.fspath(path))
                return real_open(path, flags, mode, dir_fd=dir_fd)

        local_fs.os = NoInodes()
        try:
            box = {}
            rec["init"] = attempt("init", lambda: box.setdefault("s", LocalFSDatasetStore(storage)))
            store = box["s"]
            rec["locks_exists"] = (storage / "locks").exists()
            rec["delete_under_lock"] = attempt("delete_under_lock", lambda: store.delete_under_lock("victim"))
            rec["batch_delete"] = attempt("batch_delete", lambda: store.batch_delete(["victim"]))
            rec["delete_expired"] = attempt("delete_expired", lambda: store.delete_expired())
            rec["still_stored"] = store.get_meta("victim") is not None
        finally:
            Path.mkdir = real_mkdir
            local_fs.os = os
    elif name == "I":
        store = LocalFSDatasetStore(storage)
        store.save("victim", meta("victim"), arrays())
        real_open = os.open

        class NoInodes:
            def __getattr__(self, n):
                return getattr(os, n)

            @staticmethod
            def open(path, flags, mode=0o777, *, dir_fd=None):
                if flags & os.O_CREAT and not os.path.lexists(path):
                    raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC), os.fspath(path))
                return real_open(path, flags, mode, dir_fd=dir_fd)

        local_fs.os = NoInodes()
        try:
            rec["delete_under_lock"] = attempt("delete_under_lock", lambda: store.delete_under_lock("victim"))
            rec["still_stored"] = store.get_meta("victim") is not None
        finally:
            local_fs.os = os
    elif name == "L":
        store = LocalFSDatasetStore(storage)
        store.save("victim", meta("victim"), arrays())
        stripe = stripe_of(store, "victim")
        # (1) the outside dir holds a file at the stripe's name: is it opened?
        (outside / "withstripes").mkdir()
        (outside / "withstripes" / stripe).write_text("")
        real_locks = storage / "locks-real"
        (storage / "locks").rename(real_locks)
        (storage / "locks").symlink_to(outside / "withstripes")
        opened: list = []
        real_flock = local_fs.fcntl.flock

        def spy_flock(fd, op):
            if op == local_fs.fcntl.LOCK_EX:
                opened.append(os.readlink(f"/proc/self/fd/{fd}"))
            return real_flock(fd, op)

        local_fs.fcntl.flock = spy_flock
        try:
            rec["L1_update_tags"] = attempt("update_tags", lambda: store.update_tags("victim", ["t"], []))
            rec["L1_flocked_file"] = opened[:]
            # (2) the outside dir has no stripe file
            (storage / "locks").unlink()
            (outside / "empty").mkdir()
            (storage / "locks").symlink_to(outside / "empty")
            opened.clear()
            rec["L2_update_tags"] = attempt("update_tags", lambda: store.update_tags("victim", ["u"], []))
            rec["L2_outside_created"] = sorted(p.name for p in (outside / "empty").iterdir())
        finally:
            local_fs.fcntl.flock = real_flock
    elif name == "M":
        store = LocalFSDatasetStore(storage)
        store.save("victim", meta("victim"), arrays())
        stripe_path = store._lock_path("victim")
        stripe_path.unlink()  # a missing stripe: the lazy-create path runs
        real_ensure = LocalFSDatasetStore._ensure_lock_dir
        (outside / "swapped").mkdir()

        def ensure_then_swap(self):
            real_ensure(self)  # the check passes on the real directory ...
            # ... and an attacker with write access to the storage dir swaps it before the open
            (storage / "locks").rename(storage / "locks-moved")
            (storage / "locks").symlink_to(outside / "swapped")

        LocalFSDatasetStore._ensure_lock_dir = ensure_then_swap
        try:
            rec["update_tags"] = attempt("update_tags", lambda: store.update_tags("victim", ["t"], []))
        finally:
            LocalFSDatasetStore._ensure_lock_dir = real_ensure
        rec["outside_created"] = sorted(p.name for p in (outside / "swapped").iterdir())
    elif name == "P":
        fd = os.open(work / "f", os.O_CREAT | os.O_RDWR, 0o600)
        rec["inheritable_without_O_CLOEXEC"] = os.get_inheritable(fd)
        os.close(fd)
    else:
        raise ValueError(name)
    return rec


if __name__ == "__main__":
    print(json.dumps(case(sys.argv[1], Path(sys.argv[2])), indent=1, default=str))
