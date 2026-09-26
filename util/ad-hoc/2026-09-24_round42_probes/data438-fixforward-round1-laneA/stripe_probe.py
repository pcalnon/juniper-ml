#!/usr/bin/env python3
"""Lane A: the lock-stripe design, from behaviour, in the tree on PYTHONPATH (EXPECTED_TREE).

Sections:
  A  the stripes a new store creates: names, count, modes; the id -> stripe mapping, recomputed.
  B  the flags every lock open uses (recorded by wrapping local_fs.os.open), and FD_CLOEXEC on the held fd.
  C  recreated only on FileNotFoundError: a removed stripe, a stripe replaced by a directory, by a symlink.
  D  absent ids through every HTTP route that names one: nothing may be created anywhere.
  E  hostile ids at every storage entry point: InvalidDatasetIdError, nothing created, storage holds only locks/.
  F  hostile HTTP paths: never a 500.
  G  a symlinked metadata file: artifact 200 (no ETag), If-None-Match * 304, GET /{id} a generic 500;
     a symlinked .npz: artifact 500; batch-create's answer for such an id.
  H  the locks/ directory swapped for a symlink AFTER the store opened.
Runs on head and base; base-only differences are printed, not asserted.
"""

import errno
import fcntl
import hashlib
import json
import logging
import os
import stat
import sys
import tempfile
from pathlib import Path

import juniper_data
from juniper_data.storage import local_fs
from juniper_data.storage.base import InvalidDatasetIdError, StorageContainmentError
from juniper_data.storage.local_fs import LocalFSDatasetStore

EXPECTED = Path(os.environ["EXPECTED_TREE"]).resolve()
assert Path(juniper_data.__file__).resolve().is_relative_to(EXPECTED), juniper_data.__file__
print("juniper_data from:", juniper_data.__file__)

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402

HEAD = hasattr(LocalFSDatasetStore, "_open_lock_stripe")
print("tree has stripes:", HEAD)
WORK = Path(tempfile.mkdtemp(prefix="stripe-probe-"))


def tree(root: Path) -> list[str]:
    return sorted(str(p.relative_to(root)) + ("/" if p.is_dir() and not p.is_symlink() else "") for p in root.rglob("*"))


def client_for(store: LocalFSDatasetStore) -> TestClient:
    app = create_app(settings=Settings(storage_path=str(store.base_path), rate_limit_enabled=False))
    datasets.set_store(store)
    return TestClient(app, raise_server_exceptions=False)


def create(client: TestClient, seed: int, **extra) -> str:
    body = {"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": seed}, "persist": True, **extra}
    r = client.post("/v1/datasets", json=body)
    assert r.status_code == 201, r.text
    return r.json()["dataset_id"]


# ---------------------------------------------------------------- A
print("\n== A: stripes created with the store")
old_umask = os.umask(0o022)
s = LocalFSDatasetStore(WORK / "a" / "storage")
listing = tree(s.base_path)
print("storage listing:", listing)
if HEAD:
    lock_dir = s.base_path / "locks"
    files = sorted(p.name for p in lock_dir.iterdir())
    print("stripe files:", files, "count", len(files))
    print("expected    :", [f"{i:x}.lock" for i in range(16)] == files)
    print("locks/ mode:", oct(stat.S_IMODE(lock_dir.stat().st_mode)), " stripe modes:", sorted({oct(stat.S_IMODE((lock_dir / f).stat().st_mode)) for f in files}))
    ids = ["spiral-3.0.0-0123456789abcdef", "absent-0000", "a", "Z9._-x"]
    for dataset_id in ids:
        mine = f"{int(hashlib.sha256(dataset_id.encode()).hexdigest(), 16) % 16:x}.lock"
        print(f"  _lock_path({dataset_id!r}) -> {s._lock_path(dataset_id).relative_to(s.base_path)}  recomputed locks/{mine}  match={s._lock_path(dataset_id) == lock_dir / mine}")

# ---------------------------------------------------------------- B
print("\n== B: flags of every lock open; FD_CLOEXEC while held")
calls: list[tuple[str, int]] = []
real_os = local_fs.os


class RecordingOs:
    def __getattr__(self, name):
        return getattr(real_os, name)

    @staticmethod
    def open(path, flags, mode=0o777, *, dir_fd=None):
        calls.append((os.fspath(path), flags))
        return real_os.open(path, flags, mode, dir_fd=dir_fd)


def flagnames(flags: int) -> str:
    names = [n for n in ("O_RDWR", "O_CREAT", "O_NOFOLLOW", "O_CLOEXEC", "O_EXCL", "O_TRUNC") if flags & getattr(os, n)]
    return "|".join(names)


b = LocalFSDatasetStore(WORK / "b" / "storage")
b.save("present-1", __import__("juniper_data.core.models", fromlist=["DatasetMeta"]).DatasetMeta(dataset_id="present-1", generator="spiral", generator_version="3.0.0", params={}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=__import__("datetime").datetime(2026, 9, 1, tzinfo=__import__("datetime").UTC), checksum="ab" * 32), {"X_train": __import__("numpy").zeros((2, 2), dtype="float32")})
local_fs.os = RecordingOs()
try:
    b.record_access("present-1")
    b.update_tags("present-1", ["t"], [])
    b.update_tags("absent-1", ["t"], [])
    b.delete_under_lock("absent-2")
    b.save_versioned("present-1", b.get_meta("present-1"), {"X_train": __import__("numpy").zeros((2, 2), dtype="float32")})
    b.delete_under_lock("present-1")
finally:
    local_fs.os = real_os
for path, flags in calls:
    rel = os.path.relpath(path, b.base_path)
    print(f"  os.open({rel}, {flagnames(flags)})")
print("  any O_CREAT:", any(f & os.O_CREAT for _, f in calls), " every open has O_NOFOLLOW|O_CLOEXEC:", all((f & os.O_NOFOLLOW) and (f & os.O_CLOEXEC) for _, f in calls))
print("  storage after:", tree(b.base_path))
if HEAD:
    with b._meta_write_lock("guarded"):
        target = os.fspath(b._lock_path("guarded"))
        held = [int(fd) for fd in os.listdir("/proc/self/fd") if os.path.realpath(f"/proc/self/fd/{fd}") == os.path.realpath(target)]
        print(f"  fds open on {os.path.relpath(target, b.base_path)} while held: {held}; FD_CLOEXEC set: {[bool(fcntl.fcntl(fd, fcntl.F_GETFD) & fcntl.FD_CLOEXEC) for fd in held]}")

# ---------------------------------------------------------------- C
if HEAD:
    print("\n== C: recreated only on FileNotFoundError")
    c = LocalFSDatasetStore(WORK / "c" / "storage")
    stripe = c._lock_path("x1")
    stripe.unlink()
    c.update_tags("x1", ["t"], [])  # absent id, but the lock is still taken
    print("  removed stripe recreated by the next lock:", stripe.is_file(), oct(stat.S_IMODE(stripe.stat().st_mode)))
    stripe.unlink()
    stripe.mkdir()
    try:
        c.update_tags("x1", ["t"], [])
        print("  stripe replaced by a DIRECTORY: no error (unexpected)")
    except OSError as exc:
        print(f"  stripe replaced by a DIRECTORY: {type(exc).__name__} errno={errno.errorcode.get(exc.errno)} -- not recreated; still a dir: {stripe.is_dir()}")
    stripe.rmdir()
    outside = WORK / "c" / "outside-target.lock"
    stripe.symlink_to(outside)
    try:
        c.delete_under_lock("x1")
        print("  stripe replaced by a dangling SYMLINK: no error (unexpected)")
    except OSError as exc:
        print(f"  stripe replaced by a dangling SYMLINK: {type(exc).__name__} errno={errno.errorcode.get(exc.errno)}; outside file created: {outside.exists()}")
    stripe.unlink()
    outside.write_text("")
    stripe.symlink_to(outside)
    try:
        c.delete_under_lock("x1")
        print("  stripe replaced by a SYMLINK to an existing file: no error (unexpected)")
    except OSError as exc:
        print(f"  stripe replaced by a SYMLINK to an existing file: {type(exc).__name__} errno={errno.errorcode.get(exc.errno)}")

# ---------------------------------------------------------------- D
print("\n== D: requests naming absent ids create nothing")
d = LocalFSDatasetStore(WORK / "d" / "storage")
dc = client_for(d)
before = tree(d.base_path)
absent = [f"absent-{i:04d}" for i in range(40)]
codes = {}
for i, a in enumerate(absent):
    kind = i % 8
    if kind == 0:
        codes.setdefault("GET /{id}", set()).add(dc.get(f"/v1/datasets/{a}").status_code)
    elif kind == 1:
        codes.setdefault("GET /{id}/artifact", set()).add(dc.get(f"/v1/datasets/{a}/artifact").status_code)
    elif kind == 2:
        codes.setdefault("GET /{id}/artifact If-None-Match:*", set()).add(dc.get(f"/v1/datasets/{a}/artifact", headers={"If-None-Match": "*"}).status_code)
    elif kind == 3:
        codes.setdefault("DELETE /{id}", set()).add(dc.delete(f"/v1/datasets/{a}").status_code)
    elif kind == 4:
        codes.setdefault("PATCH /{id}/tags", set()).add(dc.patch(f"/v1/datasets/{a}/tags", json={"add_tags": ["x"]}).status_code)
    elif kind == 5:
        codes.setdefault("PATCH /{id}/tags If-Match:*", set()).add(dc.patch(f"/v1/datasets/{a}/tags", json={"add_tags": ["x"]}, headers={"If-Match": "*"}).status_code)
    elif kind == 6:
        codes.setdefault("GET /{id}/access", set()).add(dc.get(f"/v1/datasets/{a}/access").status_code)
    else:
        codes.setdefault("GET /{id}/versions?", set()).add(dc.get(f"/v1/datasets/{a}", headers={"If-Match": '"x"'}).status_code)
codes["POST batch-delete"] = {dc.post("/v1/datasets/batch-delete", json={"dataset_ids": absent}).status_code}
codes["PATCH batch-tags"] = {dc.patch("/v1/datasets/batch-tags", json={"dataset_ids": absent, "add_tags": ["x"]}).status_code}
codes["POST cleanup-expired"] = {dc.post("/v1/datasets/cleanup-expired").status_code}
for k, v in codes.items():
    print(f"  {k}: {sorted(v)}")
after = tree(d.base_path)
print("  storage before:", len(before), "entries; after:", len(after), "entries; new:", sorted(set(after) - set(before))[:6], "..." if len(set(after) - set(before)) > 6 else "")

# ---------------------------------------------------------------- E
print("\n== E: hostile ids at every storage entry point")
from juniper_data.core.models import DatasetMeta  # noqa: E402
import datetime as _dt  # noqa: E402
import numpy as np  # noqa: E402

e_root = WORK / "e"
e = LocalFSDatasetStore(e_root / "storage")
e_before = tree(e_root)
hostile = ["../x", "..", "../../etc/passwd", "a/b", "/abs", "a/../b", ".hidden", ".", "", " ", "a b", "a\x00b", "a\nb", "x" * 129, "a\\b", "~root", "a..b", "..a", "a..", "%2e%2e", "a/", "/", "é", "a;b", "a:b", "*", "a?", "locks/0"]
meta = lambda i: DatasetMeta(dataset_id=i if isinstance(i, str) else "x", generator="spiral", generator_version="3.0.0", params={}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=_dt.datetime(2026, 9, 1, tzinfo=_dt.UTC), checksum="ab" * 32)  # noqa: E731
arrays = {"X_train": np.zeros((2, 2), dtype=np.float32)}
entry_points = {
    "save": lambda i: e.save(i, meta(i), arrays),
    "save_versioned": lambda i: e.save_versioned(i, meta(i), arrays),
    "get_meta": lambda i: e.get_meta(i),
    "get_artifact_bytes": lambda i: e.get_artifact_bytes(i),
    "open_artifact_stream": lambda i: e.open_artifact_stream(i),
    "exists": lambda i: e.exists(i),
    "delete": lambda i: e.delete(i),
    "delete_under_lock": lambda i: e.delete_under_lock(i),
    "update_meta": lambda i: e.update_meta(i, meta(i)),
    "update_tags": lambda i: e.update_tags(i, ["t"], []),
    "record_access": lambda i: e.record_access(i),
    "_meta_write_lock": lambda i: e._meta_write_lock(i).__enter__(),
}
table = {}
for name, fn in entry_points.items():
    outcomes = {}
    for h in hostile:
        try:
            fn(h)
            outcome = "NO ERROR"
        except InvalidDatasetIdError:
            outcome = "InvalidDatasetIdError"
        except Exception as exc:  # noqa: BLE001
            outcome = type(exc).__name__
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    table[name] = outcomes
for name, outcomes in table.items():
    print(f"  {name:22} {outcomes}")
# batch_delete classifies instead of raising
deleted_ids, not_found_ids = e.batch_delete(hostile)
print(f"  batch_delete(hostile): deleted={len(deleted_ids)} not_found={len(not_found_ids)} of {len(hostile)}")
e_after = tree(e_root)
print("  created anywhere under the probe root:", sorted(set(e_after) - set(e_before)))
print("  storage now holds:", sorted({p.split('/')[1] if p.startswith('storage/') and '/' in p[8:] else p for p in e_after}))
print("  probe work dir entries outside storage/:", sorted(p for p in e_after if not p.startswith("storage")))

# ---------------------------------------------------------------- F
print("\n== F: hostile HTTP paths")
f = LocalFSDatasetStore(WORK / "f" / "storage")
fc = client_for(f)
paths = ["..%2f..%2fetc%2fpasswd", "%2e%2e", "..", ".hidden", "a%00b", "a%0ab", "x" * 129, "%2e%2e%2f%2e%2e%2fx", "a..b", "%5c..%5cx", "..%5c..%5cx", "a%20b", "%E9", "*"]
f_codes = {}
for p in paths:
    for method, suffix in (("GET", ""), ("GET", "/artifact"), ("DELETE", ""), ("PATCH", "/tags"), ("GET", "/access")):
        url = f"/v1/datasets/{p}{suffix}"
        r = fc.request(method, url, json={"add_tags": ["x"]} if method == "PATCH" else None)
        f_codes.setdefault(r.status_code, 0)
        f_codes[r.status_code] += 1
print("  status histogram over", sum(f_codes.values()), "requests:", dict(sorted(f_codes.items())))
r = fc.post("/v1/datasets/batch-delete", json={"dataset_ids": hostile[:10]})
print("  batch-delete with hostile ids:", r.status_code, {k: (len(v) if isinstance(v, list) else v) for k, v in r.json().items()} if r.status_code < 500 else r.text[:80])
r = fc.patch("/v1/datasets/batch-tags", json={"dataset_ids": hostile[:10], "add_tags": ["x"]})
print("  batch-tags with hostile ids:", r.status_code, r.text[:90])
print("  storage after hostile HTTP:", tree(f.base_path)[:3], "... total", len(tree(f.base_path)))

# ---------------------------------------------------------------- G
print("\n== G: stored files that lead out of the storage root")
logging.getLogger("asyncio").setLevel(logging.DEBUG)
records: list[logging.LogRecord] = []


class Keep(logging.Handler):
    def emit(self, record):
        records.append(record)


logging.getLogger().addHandler(Keep(level=logging.DEBUG))
logging.getLogger().setLevel(logging.DEBUG)
g = LocalFSDatasetStore(WORK / "g" / "storage")
gc = client_for(g)
gid = create(gc, seed=11)
outside = WORK / "g" / "outside"
outside.mkdir()


def lead_out(stored: Path) -> None:
    target = outside / stored.name
    target.write_bytes(stored.read_bytes())
    stored.unlink()
    stored.symlink_to(target)


lead_out(g._meta_path(gid))
records.clear()
r1 = gc.get(f"/v1/datasets/{gid}/artifact")
r2 = gc.get(f"/v1/datasets/{gid}/artifact", headers={"If-None-Match": "*"})
r3 = gc.get(f"/v1/datasets/{gid}")
r4 = gc.get("/v1/datasets/filter")
r5 = gc.patch(f"/v1/datasets/{gid}/tags", json={"add_tags": ["x"]})
r6 = gc.delete(f"/v1/datasets/{gid}")
r7 = gc.post("/v1/datasets/batch-delete", json={"dataset_ids": [gid]})
r8 = gc.get("/v1/datasets/stats")
r9 = gc.post("/v1/datasets/cleanup-expired")
r10 = gc.post("/v1/datasets/batch-create", json={"datasets": [{"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 11}, "persist": True}]})
r11 = gc.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 11}, "persist": True})
r12 = gc.get("/v1/datasets")
r13 = gc.get(f"/v1/datasets/{gid}/preview")
r14 = gc.get(f"/v1/datasets/{gid}/access")
r15 = gc.post("/v1/datasets/batch-export", json={"dataset_ids": [gid]})
r16 = gc.patch("/v1/datasets/batch-tags", json={"dataset_ids": [gid], "add_tags": ["x"]})
for label, r in (("artifact", r1), ("artifact INM *", r2), ("GET /{id}", r3), ("/filter", r4), ("PATCH tags", r5), ("DELETE", r6), ("batch-delete", r7), ("/stats", r8), ("cleanup-expired", r9), ("batch-create (same id)", r10), ("POST create (same id)", r11), ("GET /v1/datasets (list)", r12), ("GET /{id}/preview", r13), ("GET /{id}/access", r14), ("batch-export", r15), ("batch-tags", r16)):
    body = r.text if len(r.text) < 140 else r.text[:140] + "..."
    print(f"  {label:26} {r.status_code} etag={r.headers.get('etag')!s:8} body={body if r.status_code != 200 or label != 'artifact' else '<npz bytes>'}")
leaks = [rec for rec in records if rec.levelno >= logging.WARNING and gid in logging.Formatter("%(message)s").format(rec)]
print("  WARNING+ records naming the id:", len(leaks), [f"{rec.name}:{rec.levelname}" for rec in leaks][:6])
print("  asyncio 'Exception in callback' records:", sum(1 for rec in records if rec.name == "asyncio" and "Exception in callback" in rec.getMessage()))
gid2 = create(gc, seed=12)
lead_out(g._npz_path(gid2))
r = gc.get(f"/v1/datasets/{gid2}/artifact")
print(f"  symlinked .npz: artifact {r.status_code} {r.text[:60]}; with INM *: {gc.get(f'/v1/datasets/{gid2}/artifact', headers={'If-None-Match': '*'}).status_code}")

# ---------------------------------------------------------------- H
if HEAD:
    print("\n== H: locks/ swapped for a symlink after the store opened")
    h = LocalFSDatasetStore(WORK / "h" / "storage")
    h_out_empty = WORK / "h" / "outside-empty"
    h_out_empty.mkdir()
    (h.base_path / "locks").rename(WORK / "h" / "locks-orig")
    (h.base_path / "locks").symlink_to(h_out_empty)
    try:
        h.delete_under_lock("x1")
        print("  -> empty outside dir: no error")
    except Exception as exc:  # noqa: BLE001
        print(f"  -> empty outside dir: {type(exc).__name__}: {exc}")
    print("  files created in the outside dir:", sorted(p.name for p in h_out_empty.iterdir()))
    h_out_full = WORK / "h" / "outside-full"
    h_out_full.mkdir()
    for i in range(16):
        (h_out_full / f"{i:x}.lock").write_text("")
    (h.base_path / "locks").unlink()
    (h.base_path / "locks").symlink_to(h_out_full)
    try:
        h.update_tags("x1", ["t"], [])
        print("  -> outside dir that HOLDS stripe files: opened and locked without error (containment is checked only when a stripe is missing)")
    except Exception as exc:  # noqa: BLE001
        print(f"  -> outside dir that holds stripe files: {type(exc).__name__}")
    try:
        LocalFSDatasetStore(WORK / "h" / "storage")
        print("  a NEW store over that directory: opened (unexpected)")
    except StorageContainmentError as exc:
        print(f"  a NEW store over that directory: refused, {type(exc).__name__}")

# ---------------------------------------------------------------- I
if HEAD:
    print("\n== I: an unwritable storage directory still opens")
    ro = WORK / "i" / "storage"
    ro.mkdir(parents=True)
    ro.chmod(0o555)
    try:
        rs = LocalFSDatasetStore(ro)
        print("  read-only dir: store opened; locks/ exists:", (ro / "locks").exists())
        try:
            rs.delete_under_lock("x1")
        except Exception as exc:  # noqa: BLE001
            print(f"  ... a lock on it then fails: {type(exc).__name__}")
    finally:
        ro.chmod(0o755)
os.umask(old_umask)
import shutil  # noqa: E402

shutil.rmtree(WORK, ignore_errors=True)
print("\ndone")
