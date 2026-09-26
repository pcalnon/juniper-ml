#!/usr/bin/env python3
"""
Re-measure the M-1 event-loop stall with requests sent THROUGHOUT a large create, not at one instant.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#438 fix-forward, round 2; reports/2026-09-24_defect-register-round-42/data438-fixforward-round1-laneB-refute.md (M-1)

Lane B's stall_probe2.py (util/ad-hoc/2026-09-24_round42_probes/data438-fixforward-round1-laneB/) sends ONE
read 0.5 s after the first ``*.tmp`` file appears in the storage directory. At d1c66a11 the save writes its
metadata temp file before it compresses, so that file marks the start of the compression, which runs under
the locks. The round-2 staged save compresses before it creates any temp file, so on the new tree the marker
appears only after the compression, and the read lands after the create has returned. There the probe
measures nothing. This variant needs no marker: from the moment the create is posted until it returns, it
sends a request for an unrelated small dataset every 100 ms and probes /v1/health every 20 ms.

Readers:
- ``metadata`` (GET /{id}) and ``artifact`` (GET /{id}/artifact) each record an access;
- ``tags`` (PATCH /{id}/tags) takes the same two locks as the create's commit, so its latency shows how
  long the locked section of a create lasts.

It imports the lane's ``common.py`` (start and stop a server on a free port, never 8100) from the adapted
copy whose trees are ``head`` (the new tree) and ``main`` (d1c66a11). The server's environment holds only
PATH, HOME and LANG, so no Sentry DSN reaches it. Each run's storage is deleted as soon as it ends.

Usage: python3 2026-09-24_data438_round2_stall_probe_throughout.py <lane-scripts-dir> [n_samples_per_class] [n_features]
"""

from __future__ import annotations

import json
import shutil
import sys
import threading
import time
from pathlib import Path

import httpx

SCRIPTS = Path(sys.argv[1]).resolve()
N_PER_CLASS = int(sys.argv[2]) if len(sys.argv) > 2 else 100_000
N_FEATURES = int(sys.argv[3]) if len(sys.argv) > 3 else 100
READ_EVERY_S = 0.1
HEALTH_EVERY_S = 0.02
SLOW_S = 0.5

sys.path.insert(0, str(SCRIPTS))
from common import S, fresh_dir, server  # noqa: E402


def one(tree: str, reader: str, seed: int) -> dict:
    storage = fresh_dir(S / "stall-throughout" / f"{tree}-{reader}")
    log = S / "out" / f"stall-throughout-server-{tree}-{reader}.log"
    try:
        with server(tree, 18740, storage, log) as (base, _proc):
            with httpx.Client(base_url=base, timeout=300) as c:
                d0 = c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 1}, "persist": True})
                assert d0.status_code == 201, d0.text
                d0_id = d0.json()["dataset_id"]
                body = {"generator": "gaussian", "params": {"n_classes": 2, "n_samples_per_class": N_PER_CLASS, "n_features": N_FEATURES, "seed": seed}, "persist": True}
                done = threading.Event()
                created: dict = {}
                reads: list[tuple[float, float, int]] = []
                health: list[tuple[float, float]] = []
                t0 = time.monotonic()

                def create() -> None:
                    with httpx.Client(base_url=base, timeout=600) as cc:
                        r = cc.post("/v1/datasets", json=body)
                    created["status"] = r.status_code
                    created["s"] = round(time.monotonic() - t0, 3)
                    done.set()

                def read() -> None:
                    with httpx.Client(base_url=base, timeout=600) as rc:
                        n = 0
                        while not done.is_set():
                            n += 1
                            ts = time.monotonic()
                            if reader == "metadata":
                                r = rc.get(f"/v1/datasets/{d0_id}")
                            elif reader == "artifact":
                                r = rc.get(f"/v1/datasets/{d0_id}/artifact")
                            else:
                                r = rc.patch(f"/v1/datasets/{d0_id}/tags", json={"add_tags": [f"t{n % 4}"]})
                            reads.append((round(ts - t0, 3), round(time.monotonic() - ts, 3), r.status_code))
                            time.sleep(READ_EVERY_S)

                def probe() -> None:
                    with httpx.Client(base_url=base, timeout=600) as hc:
                        while not done.is_set():
                            ts = time.monotonic()
                            status = hc.get("/v1/health").status_code
                            health.append((round(ts - t0, 3), round(time.monotonic() - ts, 3)))
                            assert status == 200, status
                            time.sleep(HEALTH_EVERY_S)

                threads = [threading.Thread(target=f) for f in (create, read, probe)]
                for th in threads:
                    th.start()
                for th in threads:
                    th.join()
                access = c.get(f"/v1/datasets/{d0_id}/access")
                during = [x for x in reads if x[0] < created["s"]]
                slow_health = [x for x in health if x[1] > SLOW_S]
                return {
                    "tree": tree,
                    "reader": reader,
                    "create_status": created["status"],
                    "create_s": created["s"],
                    "requests_sent": len(reads),
                    "requests_sent_during_create": len(during),
                    "request_statuses": sorted({x[2] for x in reads}),
                    "request_max_latency_s": max((x[1] for x in reads), default=None),
                    "health_probes": len(health),
                    "health_max_latency_s": max((x[1] for x in health), default=None),
                    f"health_probes_over_{SLOW_S}s": len(slow_health),
                    "first_slow_health_probe": ({"sent_at_s": slow_health[0][0], "latency_s": slow_health[0][1]} if slow_health else None),
                    "access_status": access.status_code,
                    "access_count": access.json().get("access_count") if access.status_code == 200 else None,
                }
    finally:
        shutil.rmtree(storage, ignore_errors=True)


def main() -> None:
    rows = []
    seed = 300
    for tree in ("main", "head"):
        for reader in ("metadata", "artifact", "tags"):
            seed += 1
            row = one(tree, reader, seed)
            print(json.dumps(row), flush=True)
            rows.append(row)
    (S / "out" / "stall_probe_throughout.json").write_text(json.dumps(rows, indent=2))
    shutil.rmtree(S / "stall-throughout", ignore_errors=True)


if __name__ == "__main__":
    main()
