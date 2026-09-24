"""End-to-end: real canopy under real uvicorn (h11 and httptools), a blank-ish CANOPY_API_KEY,
raw-byte X-API-Key requests to a key-gated route. Run once per tree.

Usage: python canopy_e2e.py <tree-dir>
"""

import os
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.join(HERE, sys.argv[1])
PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"

KEYS = [
    ("space-tab-space", " \t "),
    ("NBSP", "\xa0"),
    ("NEL", "\x85"),
    ("FS..US", "\x1c\x1d\x1e\x1f"),
    ("VT", "\x0b"),
]
ROUTE = b"/api/status"


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def raw_get(port, header):
    req = b"GET " + ROUTE + b" HTTP/1.1\r\nHost: 127.0.0.1\r\n" + header + b"Connection: close\r\n\r\n"
    s = socket.create_connection(("127.0.0.1", port), timeout=20)
    s.sendall(req)
    data = b""
    try:
        while True:
            c = s.recv(65536)
            if not c:
                break
            data += c
    except socket.timeout:
        pass
    s.close()
    head, _, body = data.partition(b"\r\n\r\n")
    status = head.split(b"\r\n", 1)[0].decode("latin-1") if head else "<none>"
    return status.replace("HTTP/1.1 ", ""), body[:70].decode("latin-1", "replace")


for label, key in KEYS:
    for impl in ("h11", "httptools"):
        port = free_port()
        env = {k: v for k, v in os.environ.items() if k not in ("SENTRY_SDK_DSN", "JUNIPER_ML_PYPI", "JUNIPER_ML_TEST_PYPI", "CANOPY_API_KEY_FILE")}
        env.update(CANOPY_API_KEY=key, JUNIPER_CANOPY_DEMO_MODE="1", JUNIPER_SKIP_DEP_FLOOR_CHECK="1", PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=f"{TREE}/src:{TREE}", LIBTORCH="", LD_LIBRARY_PATH="")
        log = open(os.path.join(HERE, f"e2e-{sys.argv[1]}-{impl}-{label}.log"), "wb")
        proc = subprocess.Popen([PY, "-m", "uvicorn", "main:app", "--http", impl, "--host", "127.0.0.1", "--port", str(port)], cwd=f"{TREE}/src", env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            up = False
            for _ in range(300):
                try:
                    socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                    up = True
                    break
                except OSError:
                    time.sleep(0.1)
            if not up:
                print(f"{sys.argv[1]} {impl:9s} {label:16s} SERVER DID NOT START")
                continue
            r_none = raw_get(port, b"")
            r_key = raw_get(port, b"X-API-Key: " + key.encode("latin-1") + b"\r\n")
            r_wrong = raw_get(port, b"X-API-Key: wrong-ascii-key\r\n")
            print(f"{sys.argv[1]} {impl:9s} {label:16s} keyless={r_none[0]:18s} key-bytes={r_key[0]:18s} wrong-key={r_wrong[0]:18s} | key-body={r_key[1]!r}")
        finally:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
            log.close()
