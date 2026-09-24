"""Lane B: un-instrumented concurrency against the live server (3a76a4c, LocalFS, 1 worker).

Writers on ONE dataset, all adding distinct tags (so every acknowledged tag must survive):
  * K "conditional" threads: GET the ETag, PATCH .../tags with If-Match; retry on 412 until it lands.
  * K "batch" threads: PATCH /batch-tags (no lock taken by that route).
  * control run: K "single" threads doing UNCONDITIONAL single-dataset PATCHes instead of batch.
Afterwards every tag whose write was acknowledged (200 / listed in "updated") is looked for.
A missing acknowledged tag is a lost update. Nothing is instrumented server-side.
"""

from __future__ import annotations

import sys
import threading

import httpx

BASE = sys.argv[1]
H = {"X-API-Key": "lane-b-scratch-key"}
K = 4
N = 40


def create(seed: int) -> str:
    r = httpx.post(f"{BASE}/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": seed}, "persist": True}, headers=H, timeout=30)
    assert r.status_code == 201, r.text
    return r.json()["dataset_id"]


def run(label: str, other: str, seed: int) -> None:
    did = create(seed)
    acked: dict[str, list[str]] = {"conditional": [], other: []}
    retries = {"n": 0}
    lock = threading.Lock()

    def conditional(w: int) -> None:
        with httpx.Client(timeout=60, headers=H) as c:
            for i in range(N):
                tag = f"c{w}-{i}"
                while True:
                    etag = c.get(f"{BASE}/v1/datasets/{did}").headers["etag"]
                    r = c.patch(f"{BASE}/v1/datasets/{did}/tags", json={"add_tags": [tag]}, headers={"If-Match": etag})
                    if r.status_code == 200:
                        with lock:
                            acked["conditional"].append(tag)
                        break
                    assert r.status_code == 412, r.status_code
                    with lock:
                        retries["n"] += 1

    def batch(w: int) -> None:
        with httpx.Client(timeout=60, headers=H) as c:
            for i in range(N):
                tag = f"b{w}-{i}"
                r = c.patch(f"{BASE}/v1/datasets/batch-tags", json={"dataset_ids": [did], "add_tags": [tag]})
                if r.status_code == 200 and did in r.json().get("updated", []):
                    with lock:
                        acked[other].append(tag)

    def single(w: int) -> None:
        with httpx.Client(timeout=60, headers=H) as c:
            for i in range(N):
                tag = f"s{w}-{i}"
                r = c.patch(f"{BASE}/v1/datasets/{did}/tags", json={"add_tags": [tag]})
                if r.status_code == 200:
                    with lock:
                        acked[other].append(tag)

    target = batch if other == "batch" else single
    threads = [threading.Thread(target=conditional, args=(w,)) for w in range(K)] + [threading.Thread(target=target, args=(w,)) for w in range(K)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    final = set(httpx.get(f"{BASE}/v1/datasets/{did}", headers=H).json()["tags"])
    lost_c = sorted(set(acked["conditional"]) - final)
    lost_o = sorted(set(acked[other]) - final)
    print(f"== {label}: conditional acked {len(acked['conditional'])} (412 retries {retries['n']}), {other} acked {len(acked[other])}")
    print(f"   LOST conditional writes: {len(lost_c)} {lost_c[:6]}")
    print(f"   LOST {other} writes: {len(lost_o)} {lost_o[:6]}")


run("control: conditional vs unconditional single-dataset PATCH", "single", 101)
run("conditional PATCH vs PATCH /batch-tags", "batch", 102)
