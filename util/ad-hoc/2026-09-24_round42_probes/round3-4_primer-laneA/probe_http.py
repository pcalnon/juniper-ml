#!/usr/bin/env python3
"""Lane A: re-derive Appendix E's HTTP claims by RUNNING juniper-data origin/main (git-archive extraction).

For each store mode (localfs = the service as deployed; memory = InMemoryDatasetStore via serve_jd.py):
  create a dataset through POST /v1/datasets, download the artifact, compare sha256(body) with the stored
  checksum, and exercise ETag / Cache-Control / If-None-Match / If-Match on the artifact, GET /{id},
  GET /latest, PATCH /{id}/tags and GET /{id}/access.

Starts each server on a port verified free, and always stops it. Strips every JUNIPER* env var from the
child environment (never printed). Writes probe_http.json + probe_http.log next to itself.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import socket
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import httpx
import numpy as np

HERE = Path(__file__).resolve().parent
JD = HERE / "jd-main"
PY = "/opt/miniforge3/envs/JuniperData/bin/python"
sys.path.insert(0, str(JD))
from juniper_data.core.artifacts import compute_checksum  # noqa: E402

RESULTS: list[dict] = []
LOG: list[str] = []


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.append(msg)


def check(name: str, ok: bool, observed: object, expected: object) -> None:
    RESULTS.append({"check": name, "ok": bool(ok), "observed": observed, "expected": expected})
    log(f"  [{'PASS' if ok else 'FAIL'}] {name}: observed={observed!r} expected={expected!r}")


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False


def start(mode: str, port: int) -> subprocess.Popen:
    assert port != 8100 and port_free(port), f"port {port} not free"
    storage = HERE / f"storage-{mode}"
    storage.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("JUNIPER")}
    env.update({"PYTHONPATH": str(JD), "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    errlog = open(HERE / f"server-{mode}.stderr.log", "w")
    proc = subprocess.Popen([PY, "-s", "-B", str(HERE / "serve_jd.py"), mode, str(port), str(storage)], cwd=str(HERE), env=env, stdout=errlog, stderr=subprocess.STDOUT)
    deadline = time.time() + 60
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"{mode} server exited early rc={proc.returncode}; see server-{mode}.stderr.log")
        try:
            if httpx.get(f"http://127.0.0.1:{port}/v1/health", timeout=2).status_code == 200:
                log(f"{mode}: server up on :{port} pid {proc.pid}")
                return proc
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError(f"{mode} server did not become healthy")


def stop(proc: subprocess.Popen, mode: str) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    log(f"{mode}: server pid {proc.pid} stopped rc={proc.returncode}")


def npz_facts(body: bytes) -> dict:
    zf = zipfile.ZipFile(io.BytesIO(body))
    infos = zf.infolist()
    with np.load(io.BytesIO(body)) as npz:
        arrays = {k: npz[k] for k in npz.files}
    names = [i.filename for i in infos]
    return {
        "entries": names,
        "entries_sorted": names == sorted(names),
        "compress_types": sorted({i.compress_type for i in infos}),  # 8 = DEFLATED, 0 = STORED
        "arrays": arrays,
    }


def run_mode(mode: str, port: int) -> None:
    log(f"\n===== mode={mode} =====")
    proc = start(mode, port)
    try:
        c = httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=60)
        name = f"lanea-{mode}-{int(time.time())}"
        req = {"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 60, "seed": 1234}, "name": name, "persist": True}
        r = c.post("/v1/datasets", json=req)
        check(f"{mode}: POST /v1/datasets", r.status_code == 201, r.status_code, 201)
        created = r.json()
        dsid = created["dataset_id"]
        checksum = created["meta"]["checksum"]
        log(f"  dataset_id={dsid} checksum={checksum}")

        # ---- claim 2: served bytes vs stored checksum ------------------------------------
        a = c.get(f"/v1/datasets/{dsid}/artifact")
        body = a.content
        facts = npz_facts(body)
        served_sha = hashlib.sha256(body).hexdigest()
        check(f"{mode}: artifact 200", a.status_code == 200, a.status_code, 200)
        check(f"{mode}: sha256(served bytes) != stored checksum", served_sha != checksum, served_sha, f"!= {checksum}")
        check(f"{mode}: served NPZ is DEFLATE-compressed (savez_compressed)", facts["compress_types"] == [zipfile.ZIP_DEFLATED], facts["compress_types"], [8])
        recomputed = compute_checksum(facts["arrays"])
        check(f"{mode}: compute_checksum(arrays loaded from served bytes) == stored checksum", recomputed == checksum, recomputed, checksum)
        buf = io.BytesIO()
        np.savez(buf, **{k: facts["arrays"][k] for k in sorted(facts["arrays"])})
        check(f"{mode}: sha256(uncompressed np.savez, keys sorted) == stored checksum", hashlib.sha256(buf.getvalue()).hexdigest() == checksum, hashlib.sha256(buf.getvalue()).hexdigest(), checksum)
        buf2 = io.BytesIO()
        np.savez(buf2, **facts["arrays"])  # served (unsorted?) order, uncompressed
        log(f"  served entry order: {facts['entries']} (sorted={facts['entries_sorted']}); uncompressed-in-served-order sha == checksum: {hashlib.sha256(buf2.getvalue()).hexdigest() == checksum}")
        RESULTS.append({"check": f"{mode}: served entry order", "ok": True, "observed": facts["entries"], "expected": "memory sorted / localfs generator order"})

        # ---- claim 4: artifact headers --------------------------------------------------
        etag = a.headers.get("etag")
        check(f"{mode}: artifact ETag == W/\"<checksum>\"", etag == f'W/"{checksum}"', etag, f'W/"{checksum}"')
        check(f"{mode}: artifact Cache-Control", a.headers.get("cache-control") == "private, no-cache", a.headers.get("cache-control"), "private, no-cache")
        log(f"  artifact content-type={a.headers.get('content-type')} content-disposition={a.headers.get('content-disposition')} accept-ranges={a.headers.get('accept-ranges')}")

        for label, inm, want in [
            ("If-None-Match W/<checksum>", f'W/"{checksum}"', 304),
            ("If-None-Match \"<checksum>\" (strong form, weak comparison)", f'"{checksum}"', 304),
            ("If-None-Match *", "*", 304),
            ("If-None-Match W/\"deadbeef\"", 'W/"deadbeef"', 200),
            ("If-None-Match \"<sha256(served bytes)>\"", f'"{served_sha}"', 200),
        ]:
            rr = c.get(f"/v1/datasets/{dsid}/artifact", headers={"If-None-Match": inm})
            extra = {"body_len": len(rr.content), "etag": rr.headers.get("etag"), "cache_control": rr.headers.get("cache-control")}
            ok = rr.status_code == want and (want != 304 or (len(rr.content) == 0 and rr.headers.get("etag") == f'W/"{checksum}"' and rr.headers.get("cache-control") == "private, no-cache"))
            check(f"{mode}: artifact {label}", ok, {"status": rr.status_code, **extra}, want)

        # ---- claim 5: If-Match on the artifact: only * ----------------------------------
        for label, im, want in [
            ("If-Match \"<checksum>\"", f'"{checksum}"', 412),
            ("If-Match W/\"<checksum>\"", f'W/"{checksum}"', 412),
            ("If-Match \"<sha256(served bytes)>\"", f'"{served_sha}"', 412),
            ("If-Match *", "*", 200),
        ]:
            rr = c.get(f"/v1/datasets/{dsid}/artifact", headers={"If-Match": im})
            check(f"{mode}: artifact {label}", rr.status_code == want, rr.status_code, want)

        # ---- claim 4: metadata strong ETag = sha256(exact body) ----------------------------
        m1 = c.get(f"/v1/datasets/{dsid}")
        m_etag = m1.headers.get("etag")
        check(f"{mode}: GET /{{id}} ETag == \"sha256(exact body)\" (strong)", m_etag == '"' + hashlib.sha256(m1.content).hexdigest() + '"', m_etag, "sha256(body)")
        check(f"{mode}: GET /{{id}} Cache-Control", m1.headers.get("cache-control") == "private, no-cache", m1.headers.get("cache-control"), "private, no-cache")
        body_keys = set(m1.json().keys())
        check(f"{mode}: GET /{{id}} body carries no access counters", not ({"access_count", "last_accessed_at"} & body_keys), sorted({"access_count", "last_accessed_at"} & body_keys), [])
        m304 = c.get(f"/v1/datasets/{dsid}", headers={"If-None-Match": m_etag})
        check(f"{mode}: GET /{{id}} If-None-Match -> bodiless 304 with validator", m304.status_code == 304 and len(m304.content) == 0 and m304.headers.get("etag") == m_etag, {"status": m304.status_code, "len": len(m304.content), "etag": m304.headers.get("etag"), "cc": m304.headers.get("cache-control")}, 304)
        time.sleep(0.5)
        acc1 = c.get(f"/v1/datasets/{dsid}/access")
        m2 = c.get(f"/v1/datasets/{dsid}")
        time.sleep(0.5)
        acc2 = c.get(f"/v1/datasets/{dsid}/access")
        check(f"{mode}: metadata ETag stable across reads while counters move", m2.headers.get("etag") == m_etag and acc2.json()["access_count"] > acc1.json()["access_count"], {"etag_same": m2.headers.get("etag") == m_etag, "count": [acc1.json()["access_count"], acc2.json()["access_count"]]}, "same etag, count increases")
        check(f"{mode}: GET /{{id}}/access 200 + Cache-Control no-store", acc1.status_code == 200 and acc1.headers.get("cache-control") == "no-store", {"status": acc1.status_code, "cc": acc1.headers.get("cache-control"), "keys": sorted(acc1.json().keys())}, "200 no-store")

        # ---- claim 4: /latest ------------------------------------------------------------
        lt = c.get("/v1/datasets/latest", params={"name": name})
        lt_etag = lt.headers.get("etag")
        check(f"{mode}: GET /latest ETag == \"sha256(exact body)\"", lt_etag == '"' + hashlib.sha256(lt.content).hexdigest() + '"', lt_etag, "sha256(body)")
        check(f"{mode}: GET /latest ETag == GET /{{id}} ETag", lt_etag == m_etag, lt_etag, m_etag)
        check(f"{mode}: GET /latest Cache-Control", lt.headers.get("cache-control") == "private, no-cache", lt.headers.get("cache-control"), "private, no-cache")
        log(f"  /latest content-location={lt.headers.get('content-location')}")
        lt304 = c.get("/v1/datasets/latest", params={"name": name}, headers={"If-None-Match": lt_etag})
        check(f"{mode}: GET /latest If-None-Match -> bodiless 304", lt304.status_code == 304 and len(lt304.content) == 0, {"status": lt304.status_code, "len": len(lt304.content)}, 304)

        # ---- claim 5: PATCH /tags conditional on the strong metadata ETag --------------------
        for label, im in [("If-Match W/\"<checksum>\" (artifact tag)", f'W/"{checksum}"'), ("If-Match \"<checksum>\"", f'"{checksum}"')]:
            p = c.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": ["never"]}, headers={"If-Match": im})
            check(f"{mode}: PATCH tags {label} -> 412", p.status_code == 412, p.status_code, 412)
        p1 = c.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": ["lanea"]}, headers={"If-Match": m_etag})
        new_etag = p1.headers.get("etag")
        check(f"{mode}: PATCH tags If-Match <current metadata ETag> -> 200, new strong ETag of body", p1.status_code == 200 and new_etag == '"' + hashlib.sha256(p1.content).hexdigest() + '"' and new_etag != m_etag, {"status": p1.status_code, "etag_is_body_sha": new_etag == '"' + hashlib.sha256(p1.content).hexdigest() + '"', "changed": new_etag != m_etag, "content_location": p1.headers.get("content-location")}, 200)
        p2 = c.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": ["stale"]}, headers={"If-Match": m_etag})
        tags_now = c.get(f"/v1/datasets/{dsid}").json().get("tags")
        check(f"{mode}: PATCH tags with the STALE ETag -> 412, nothing written", p2.status_code == 412 and "stale" not in (tags_now or []), {"status": p2.status_code, "tags": tags_now}, 412)
        p3 = c.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": ["unconditional"]})
        check(f"{mode}: PATCH tags with NO precondition (is one required?)", True, p3.status_code, "observe: 200 = optional, 428 = required")
        a2 = c.get(f"/v1/datasets/{dsid}/artifact")
        check(f"{mode}: artifact ETag unchanged by tag edits", a2.headers.get("etag") == etag, a2.headers.get("etag"), etag)
        check(f"{mode}: artifact bytes unchanged across reads", hashlib.sha256(a2.content).hexdigest() == served_sha, hashlib.sha256(a2.content).hexdigest(), served_sha)
        c.close()
    finally:
        stop(proc, mode)


def main() -> int:
    ports = {"localfs": 18761, "memory": 18762}
    for mode, port in ports.items():
        run_mode(mode, port)
    (HERE / "probe_http.json").write_text(json.dumps(RESULTS, indent=1, default=str))
    (HERE / "probe_http.log").write_text("\n".join(LOG) + "\n")
    fails = [r for r in RESULTS if not r["ok"]]
    log(f"\n{len(RESULTS)} checks, {len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
