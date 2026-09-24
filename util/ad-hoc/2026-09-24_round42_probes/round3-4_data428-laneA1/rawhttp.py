"""Lane A1: a minimal raw HTTP/1.1 client, so header lines, their count, their order and their
bytes are exactly what the test says -- no client library joins, folds, dedups or refuses them."""

from __future__ import annotations

import json
import socket
import time

HOST = "127.0.0.1"
KEY = "laneA1-scratch-key"  # the self-chosen dummy key the scratch server was started with


def build(method: str, path: str, headers: list[tuple[str, str]] | None = None, body: bytes | None = None, *, key: bool = True, close: bool = True) -> bytes:
    lines = [f"{method} {path} HTTP/1.1", f"Host: {HOST}"]
    if key:
        lines.append(f"X-API-Key: {KEY}")
    for name, value in headers or []:
        lines.append(f"{name}: {value}")
    if body is not None:
        lines.append("Content-Type: application/json")
        lines.append(f"Content-Length: {len(body)}")
    if close:
        lines.append("Connection: close")
    head = ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1")
    return head + (body or b"")


def read_response(sock: socket.socket, method: str = "GET") -> tuple[int, dict[str, list[str]], bytes]:
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(65536)
        if not chunk:
            break
        buf += chunk
    if b"\r\n\r\n" not in buf:
        return -1, {}, buf
    head, rest = buf.split(b"\r\n\r\n", 1)
    lines = head.decode("latin-1").split("\r\n")
    status = int(lines[0].split()[1])
    headers: dict[str, list[str]] = {}
    for line in lines[1:]:
        k, _, v = line.partition(":")
        headers.setdefault(k.strip().lower(), []).append(v.strip())
    if method == "HEAD" or status in (204, 304) or 100 <= status < 200:
        return status, headers, b""
    if "content-length" in headers:
        n = int(headers["content-length"][0])
        while len(rest) < n:
            chunk = sock.recv(65536)
            if not chunk:
                break
            rest += chunk
        return status, headers, rest[:n]
    if headers.get("transfer-encoding", [""])[0].lower() == "chunked":
        body = b""
        while True:
            while b"\r\n" not in rest:
                rest += sock.recv(65536)
            size_line, rest = rest.split(b"\r\n", 1)
            size = int(size_line.split(b";")[0], 16)
            while len(rest) < size + 2:
                rest += sock.recv(65536)
            body += rest[:size]
            rest = rest[size + 2 :]
            if size == 0:
                return status, headers, body
    # read to close
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        rest += chunk
    return status, headers, rest


def request(port: int, method: str, path: str, headers: list[tuple[str, str]] | None = None, body: bytes | None = None, *, key: bool = True, timeout: float = 60.0, raw: bytes | None = None):
    """One request on a fresh connection. Returns (status, headers, body, seconds)."""
    data = raw if raw is not None else build(method, path, headers, body, key=key)
    t0 = time.perf_counter()
    with socket.create_connection((HOST, port), timeout=timeout) as sock:
        sock.sendall(data)
        status, hdrs, payload = read_response(sock, method)
    return status, hdrs, payload, time.perf_counter() - t0


def jbody(obj) -> bytes:
    return json.dumps(obj).encode()
