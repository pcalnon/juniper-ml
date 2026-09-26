"""With canopy auth ENABLED, can a KEYLESS caller read a padded JUNIPER_CASCOR_API_KEY out of an API response?

Fresh interpreter, real import main + lifespan (TestClient), service mode against a parent-side fake cascor.
The caller holds no X-API-Key: it mints a CSRF token (GET /api/csrf, no Origin, as a same-origin browser does) and
POSTs /api/train/start with an allowlisted Origin -- the key-exempt browser control surface.

usage: python e2e_anon_extract.py <python-exe> <src-dir>
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

CHILD = r'''
import json
import main
from fastapi.testclient import TestClient
out = {"auth_enabled": main.api_key_auth.enabled}
with TestClient(main.app) as c:
    out["status_keyless"] = c.get("/api/status").status_code
    tok = c.get("/api/csrf")
    out["csrf_status"] = tok.status_code
    token = tok.json().get("csrf_token") or tok.json().get("token")
    r = c.post("/api/train/start", headers={"Origin": "http://localhost:8050", "X-CSRF-Token": token or ""})
    out["start_status"] = r.status_code
    out["start_body"] = r.text[:400]
    out["key_in_start_body"] = "LEAKME" in r.text
print("__REPORT__" + json.dumps(out))
'''


def serve(sock):
    while True:
        try:
            conn, _ = sock.accept()
        except OSError:
            return
        try:
            conn.settimeout(2)
            conn.recv(65536)
            body = b'{"status":"ok"}'
            conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
        except OSError:
            pass
        conn.close()


def main():
    py, src = sys.argv[1], Path(sys.argv[2]).resolve()
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(16)
    fake = f"http://127.0.0.1:{srv.getsockname()[1]}"
    threading.Thread(target=serve, args=(srv,), daemon=True).start()
    work = Path(tempfile.mkdtemp(prefix="e2e-anon-", dir=str(Path(__file__).parent / "work")))
    (work / "conf").mkdir()
    shutil.copy(src.parent / "conf" / "logging_config.yaml", work / "conf" / "logging_config.yaml")
    scrub = ("CANOPY_API_KEY", "JUNIPER_CANOPY_REQUIRE_AUTH", "JUNIPER_SKIP_AUTH_POSTURE_CHECK", "JUNIPER_CANOPY_SERVER__", "JUNIPER_DATA_API_KEY", "JUNIPER_CASCOR_API_KEY", "JUNIPER_CANOPY_CASCOR", "CASCOR_SERVICE_URL")
    env = {k: v for k, v in os.environ.items() if not k.startswith(scrub) and "SENTRY" not in k.upper()}
    s2 = socket.socket()
    s2.bind(("127.0.0.1", 0))
    port = s2.getsockname()[1]
    s2.close()
    env.update({"PYTHONPATH": str(src), "PYTHONDONTWRITEBYTECODE": "1", "JUNIPER_DATA_URL": fake, "JUNIPER_CANOPY_SERVER__PORT": str(port), "LIBTORCH": "", "LD_LIBRARY_PATH": "",
                "JUNIPER_CANOPY_DEMO_MODE": "0", "JUNIPER_CANOPY_CASCOR_SERVICE_URL": fake,
                "CANOPY_API_KEY": "real-canopy-key-no-padding", "JUNIPER_CASCOR_API_KEY": "LEAKME-cascor-key-6\n"})
    res = subprocess.run([py, "-c", CHILD], cwd=str(work), env=env, capture_output=True, text=True, timeout=300)
    lines = [ln for ln in res.stdout.splitlines() if ln.startswith("__REPORT__")]
    print(json.dumps(json.loads(lines[0][10:]), indent=1) if lines else res.stderr[-3000:])


if __name__ == "__main__":
    main()
