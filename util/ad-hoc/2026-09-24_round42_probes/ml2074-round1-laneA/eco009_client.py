#!/usr/bin/env python3
"""Lane A: raw-socket probes of the eco009 server (cap 32 bytes). Starts and stops its own servers
on two free loopback ports, one per uvicorn parser."""
import socket
import subprocess
import sys
import time

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
PY = sys.executable


def free(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def send(port: int, raw: bytes) -> str:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
        s.sendall(raw)
        pass  # no half-close: uvicorn treats it as a disconnect
        data = b""
        try:
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
    text = data.decode("latin-1")
    status = text.split("\r\n", 1)[0]
    body = text.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in text else ""
    return f"{status} | {body[:80]}"


def chunked(payload: bytes) -> bytes:
    return f"{len(payload):x}\r\n".encode() + payload + b"\r\n0\r\n\r\n"


P100 = b"A" * 100
P64 = b"B" * 64
cases = {
    "control: Content-Length 100 (over the 32-byte cap)": b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 100\r\nConnection: close\r\n\r\n" + P100,
    "control: Content-Length 10 (under)": b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 10\r\nConnection: close\r\n\r\n" + b"C" * 10,
    "chunked, no Content-Length, 100 bytes": b"POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n" + chunked(P100),
    "Content-Length 10 AND Transfer-Encoding chunked, 64-byte chunk": b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 10\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n" + chunked(P64),
}

procs = []
try:
    for port, parser in ((47811, "h11"), (47812, "httptools")):
        assert free(port), f"port {port} busy"
        p = subprocess.Popen([PY, f"{S}/eco009_server.py", str(port), parser], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        procs.append(p)
        for _ in range(100):
            if not free(port):
                break
            time.sleep(0.1)
        print(f"===== uvicorn --http {parser} on :{port} (pid {p.pid})")
        for label, raw in cases.items():
            print(f"  {label:66s} -> {send(port, raw)}")
finally:
    for p in procs:
        p.terminate()
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
    print("servers stopped:", [p.returncode for p in procs])
