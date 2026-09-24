"""Measure what h11 and httptools (via real uvicorn) deliver for raw X-API-Key header bytes.

Starts echo_app under ``uvicorn --http <impl>`` on a free loopback port for each parser, then
sends hand-built HTTP/1.1 requests over a raw socket (so no client library normalizes the
bytes), and prints the status line plus the echoed body.
"""

import json
import os
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

CASES = [
    ("spaces", b"   "),
    ("tabs", b"\t\t"),
    ("space-tab-space", b" \t "),
    ("VT", b"\x0b"),
    ("FF", b"\x0c"),
    ("NBSP U+00A0 (latin-1 byte)", b"\xa0"),
    ("NEL U+0085 (latin-1 byte)", b"\x85"),
    ("NBSP as UTF-8 bytes", b"\xc2\xa0"),
    ("FS U+001C", b"\x1c"),
    ("GS U+001D", b"\x1d"),
    ("RS U+001E", b"\x1e"),
    ("US U+001F", b"\x1f"),
    ("FS..US", b"\x1c\x1d\x1e\x1f"),
    ("padded real", b"  real-key  "),
    ("empty", b""),
]


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def send_raw(port, header_value):
    req = b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\nX-API-Key: " + header_value + b"\r\nConnection: close\r\n\r\n"
    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    s.sendall(req)
    data = b""
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass
    s.close()
    head, _, body = data.partition(b"\r\n\r\n")
    status = head.split(b"\r\n", 1)[0].decode("latin-1") if head else "<no response>"
    return status, body


def main(app_spec, app_dir):
    out = {}
    for impl in ("h11", "httptools"):
        port = free_port()
        proc = subprocess.Popen([PY, "-m", "uvicorn", app_spec, "--app-dir", app_dir, "--http", impl, "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            for _ in range(100):
                try:
                    socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                    break
                except OSError:
                    time.sleep(0.1)
            for name, value in CASES:
                status, body = send_raw(port, value)
                try:
                    parsed = json.loads(body)
                except Exception:  # noqa: BLE001
                    parsed = body[:80].decode("latin-1")
                out[(impl, name)] = (status, parsed)
                print(f"{impl:9s} | {name:28s} | {status:28s} | {parsed}")
        finally:
            proc.terminate()
            proc.wait(5)
    return out


if __name__ == "__main__":
    import uvicorn, h11, httptools  # noqa: E401

    print("uvicorn", uvicorn.__version__, "h11", h11.__version__, "httptools", httptools.__version__)
    main("echo_app:app", HERE)
