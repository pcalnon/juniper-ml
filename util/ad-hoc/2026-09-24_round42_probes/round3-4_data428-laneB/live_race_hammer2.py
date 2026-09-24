"""Lane B: isolate the conditional PATCH's own guarantee from pre-existing batch-vs-batch and
record_access races.

Only two kinds of writer touch the dataset:
  * K conditional threads that learn the ETag from GET /v1/datasets/latest?name=... -- a route that
    records NO access, so no record_access rewrite is in play -- and PATCH .../tags with If-Match,
    retrying on 412;
  * ONE other thread: PATCH /batch-tags (takes no lock), or, in the control, an UNCONDITIONAL
    single-dataset PATCH (takes the lock).
With one batch thread, batch cannot race itself. So a lost acknowledged BATCH tag can only have
been overwritten by a conditional PATCH whose If-Match check passed against a state that no longer
held when it wrote -- the race the docs say "cannot" be lost. A lost CONDITIONAL tag was erased by
the batch route's unlocked read-modify-write.
"""

from __future__ import annotations

import sys
import threading

import httpx

BASE = sys.argv[1]
H = {"X-API-Key": "lane-b-scratch-key"}
K = 4
N = 60


def create(seed: int, name: str) -> str:
    r = httpx.post(f"{BASE}/v1/datasets", json={"generator": "spiral", "name": name, "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": seed}, "persist": True}, headers=H, timeout=30)
    assert r.status_code == 201, r.text
    return r.json()["dataset_id"]


def run(label: str, other: str, seed: int) -> None:
    name = f"laneb-race-{seed}"
    did = create(seed, name)
    access_before = httpx.get(f"{BASE}/v1/datasets/{did}/access", headers=H).json()["access_count"]
    acked: dict[str, list[str]] = {"conditional": [], other: []}
    retries = {"n": 0}
    lock = threading.Lock()

    def conditional(w: int) -> None:
        with httpx.Client(timeout=60, headers=H) as c:
            for i in range(N):
                tag = f"c{w}-{i}"
                while True:
                    latest = c.get(f"{BASE}/v1/datasets/latest", params={"name": name})
                    assert latest.headers["content-location"] == f"/v1/datasets/{did}"
                    r = c.patch(f"{BASE}/v1/datasets/{did}/tags", json={"add_tags": [tag]}, headers={"If-Match": latest.headers["etag"]})
                    if r.status_code == 200:
                        with lock:
                            acked["conditional"].append(tag)
                        break
                    assert r.status_code == 412, r.status_code
                    with lock:
                        retries["n"] += 1

    def batch() -> None:
        with httpx.Client(timeout=60, headers=H) as c:
            for i in range(N * K):
                tag = f"b-{i}"
                r = c.patch(f"{BASE}/v1/datasets/batch-tags", json={"dataset_ids": [did], "add_tags": [tag]})
                if r.status_code == 200 and did in r.json().get("updated", []):
                    with lock:
                        acked[other].append(tag)

    def single() -> None:
        with httpx.Client(timeout=60, headers=H) as c:
            for i in range(N * K):
                tag = f"s-{i}"
                r = c.patch(f"{BASE}/v1/datasets/{did}/tags", json={"add_tags": [tag]})
                if r.status_code == 200:
                    with lock:
                        acked[other].append(tag)

    threads = [threading.Thread(target=conditional, args=(w,)) for w in range(K)] + [threading.Thread(target=batch if other == "batch" else single)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    final = set(httpx.get(f"{BASE}/v1/datasets/latest", params={"name": name}, headers=H).json()["tags"])
    access_after = httpx.get(f"{BASE}/v1/datasets/{did}/access", headers=H).json()["access_count"]
    lost_c = sorted(set(acked["conditional"]) - final)
    lost_o = sorted(set(acked[other]) - final)
    print(f"== {label}: conditional acked {len(acked['conditional'])} (412 retries {retries['n']}), {other} acked {len(acked[other])}; access_count {access_before} -> {access_after} (no record_access in play)")
    print(f"   LOST conditional writes: {len(lost_c)} {lost_c[:6]}")
    print(f"   LOST {other} writes: {len(lost_o)} {lost_o[:6]}")


run("control: 4 conditional + 1 unconditional single-dataset PATCH", "single", 201)
run("4 conditional + 1 PATCH /batch-tags", "batch", 202)
