"""End-to-end: does a padded OUTBOUND secret (data / cascor / recurrence key) reach canopy's logs or API bodies at 8917fdac?

Each scenario runs canopy in a fresh interpreter (real ``import main``, real lifespan via TestClient) in its own temp
working directory with the repo's logging config copied in, exactly like the PR's own fresh-boot tests. A parent-side
raw-socket server answers every HTTP request with 200 JSON, and records what arrives. The child records every log record
(``Logger.callHandlers`` hook) and every API response body; the parent greps those, stdout, stderr and logs/*.log.

usage: python e2e_other_secrets.py <python-exe> <src-dir> <scenario> [<scenario> ...]
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

MARK = "LEAKME"
RECEIVED: list[bytes] = []

CHILD = r'''
import json, logging, os, time
records = []
_real = logging.Logger.callHandlers
def _every(self, record):
    records.append(record)
    return _real(self, record)
logging.Logger.callHandlers = _every
import main
from fastapi.testclient import TestClient
MARK = "LEAKME"
bodies = []
with TestClient(main.app) as c:
    for method, path, body in json.loads(os.environ["PROBE_STEPS"]):
        if method == "SLEEP":
            time.sleep(body)
            continue
        r = c.request(method, path, json=body)
        bodies.append((f"{method} {path}", r.status_code, r.text))
def render(r):
    s = r.getMessage()
    if r.exc_info:
        s += "\n" + logging.Formatter().formatException(r.exc_info)
    return s
hits = [{"logger": r.name, "level": r.levelname, "msg": render(r)[:260]} for r in records if MARK in render(r)]
body_hits = [(k, s, t[:260]) for k, s, t in bodies if MARK in t]
print("__REPORT__" + json.dumps({"main_file": main.__file__, "hits": hits, "body_hits": body_hits, "n_records": len(records), "statuses": [(k, s) for k, s, _ in bodies]}))
'''


def serve(sock):
    while True:
        try:
            conn, _ = sock.accept()
        except OSError:
            return
        conn.settimeout(2)
        data = b""
        try:
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
        except OSError:
            pass
        RECEIVED.append(data)
        body = b'{"status":"ok"}'
        try:
            conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
        except OSError:
            pass
        conn.close()


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    py, src = sys.argv[1], Path(sys.argv[2]).resolve()
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(64)
    fake = f"http://127.0.0.1:{srv.getsockname()[1]}"
    threading.Thread(target=serve, args=(srv,), daemon=True).start()

    status_steps = [["GET", "/api/status", None], ["GET", "/api/metrics", None], ["GET", "/api/network/topology", None]]
    scenarios = {
        "data-lead-space": ({"JUNIPER_CANOPY_DEMO_MODE": "1", "JUNIPER_DATA_API_KEY": " LEAKME-data-key-1"}, status_steps),
        "data-trail-LF": ({"JUNIPER_CANOPY_DEMO_MODE": "1", "JUNIPER_DATA_API_KEY": "LEAKME-data-key-1b\n"}, status_steps),
        "cascor-lead-space": (
            {"JUNIPER_CANOPY_DEMO_MODE": "0", "JUNIPER_CANOPY_CASCOR_SERVICE_URL": fake, "JUNIPER_CASCOR_API_KEY": " LEAKME-cascor-key-2"},
            status_steps + [["POST", "/api/train/start", None], ["SLEEP", "", 6], ["GET", "/api/status", None]],
        ),
        "cascor-trail-LF": (
            {"JUNIPER_CANOPY_DEMO_MODE": "0", "JUNIPER_CANOPY_CASCOR_SERVICE_URL": fake, "JUNIPER_CASCOR_API_KEY": "LEAKME-cascor-key-3\n"},
            status_steps + [["POST", "/api/train/start", None], ["SLEEP", "", 6], ["GET", "/api/status", None]],
        ),
        "recurrence-lead-space": (
            {"JUNIPER_CANOPY_DEMO_MODE": "1", "JUNIPER_CANOPY_RECURRENCE_SERVICE_URL": fake, "JUNIPER_RECURRENCE_API_KEY": " LEAKME-rec-key-4"},
            [["POST", "/api/train/stop", None], ["SLEEP", "", 2], ["POST", "/api/model/select", {"nn_model": "recurrence"}], ["POST", "/api/train/start", {"dataset": {"generator": "spiral"}}], ["SLEEP", "", 3], ["GET", "/api/status", None]],
        ),
        "recurrence-trail-space": (
            {"JUNIPER_CANOPY_DEMO_MODE": "1", "JUNIPER_CANOPY_RECURRENCE_SERVICE_URL": fake, "JUNIPER_RECURRENCE_API_KEY": "LEAKME-rec-key-5 "},
            [["POST", "/api/train/stop", None], ["SLEEP", "", 2], ["POST", "/api/model/select", {"nn_model": "recurrence"}], ["POST", "/api/train/start", {"dataset": {"generator": "spiral"}}], ["SLEEP", "", 3], ["GET", "/api/status", None]],
        ),
    }
    scrub = ("CANOPY_API_KEY", "JUNIPER_CANOPY_REQUIRE_AUTH", "JUNIPER_SKIP_AUTH_POSTURE_CHECK", "JUNIPER_CANOPY_SERVER__", "JUNIPER_DATA_API_KEY", "JUNIPER_CASCOR_API_KEY", "JUNIPER_RECURRENCE_API_KEY", "JUNIPER_CANOPY_JUNIPER_DATA_API_KEY", "JUNIPER_CANOPY_RECURRENCE", "JUNIPER_CANOPY_CASCOR", "CASCOR_SERVICE_URL", "RECURRENCE_SERVICE_URL")
    for name in sys.argv[3:]:
        extra, steps = scenarios[name]
        work = Path(tempfile.mkdtemp(prefix=f"e2e-{name}-", dir=str(Path(__file__).parent / "work")))
        (work / "conf").mkdir()
        shutil.copy(src.parent / "conf" / "logging_config.yaml", work / "conf" / "logging_config.yaml")
        env = {k: v for k, v in os.environ.items() if not k.startswith(scrub) and "SENTRY" not in k.upper()}
        env.update({"PYTHONPATH": str(src), "PYTHONDONTWRITEBYTECODE": "1", "JUNIPER_CANOPY_LOG_LEVEL": "DEBUG", "JUNIPER_DATA_URL": fake, "JUNIPER_CANOPY_SERVER__PORT": str(free_port()), "LIBTORCH": "", "LD_LIBRARY_PATH": "", "PROBE_STEPS": json.dumps(steps)})
        env.update(extra)
        before = len(RECEIVED)
        res = subprocess.run([py, "-c", CHILD], cwd=str(work), env=env, capture_output=True, text=True, timeout=300)
        lines = [ln for ln in res.stdout.splitlines() if ln.startswith("__REPORT__")]
        print(f"===== {name}  (exit {res.returncode})")
        if not lines:
            print(res.stderr[-3000:])
            continue
        rep = json.loads(lines[0][len("__REPORT__"):])
        assert Path(rep["main_file"]).resolve() == (src / "main.py").resolve(), rep["main_file"]
        print(f"  records={rep['n_records']}  statuses={rep['statuses']}")
        print(f"  log records carrying the key: {len(rep['hits'])}")
        seen = set()
        for h in rep["hits"]:
            key = (h["logger"], h["level"], h["msg"][:70])
            if key in seen:
                continue
            seen.add(key)
            print(f"    [{h['level']}] {h['logger']}: {h['msg'][:230]!r}")
        print(f"  API bodies carrying the key: {len(rep['body_hits'])}")
        for k, s, t in rep["body_hits"]:
            print(f"    {k} -> {s}: {t[:230]!r}")
        for lf in sorted((work / "logs").glob("*.log")):
            n = sum(1 for ln in lf.read_text(errors="replace").splitlines() if MARK in ln)
            if n:
                print(f"  logs/{lf.name}: {n} lines carry the key")
        out_n = sum(1 for ln in (res.stdout + res.stderr).splitlines() if MARK in ln and not ln.startswith("__REPORT__"))
        print(f"  console lines carrying the key: {out_n}")
        wire = b"".join(RECEIVED[before:])
        print(f"  key bytes reached the fake upstream: {MARK.encode() in wire}  ({len(RECEIVED) - before} requests)")


if __name__ == "__main__":
    main()
