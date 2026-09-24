#!/usr/bin/env python3
"""Lane A: what does each uvicorn parser deliver to Starlette for a whitespace X-API-Key?
Starts/stops its own servers on free loopback ports; raw-socket requests so no client normalises."""
import socket
import subprocess
import sys
import time

SERVER = r'''
import sys, uvicorn
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
async def h(request):
    return PlainTextResponse(repr(request.headers.get("x-api-key")))
app = Starlette(routes=[Route("/h", h)])
uvicorn.run(app, host="127.0.0.1", port=int(sys.argv[1]), http=sys.argv[2], log_level="warning")
'''


def free(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def get(port, value: bytes):
    with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
        s.sendall(b"GET /h HTTP/1.1\r\nHost: x\r\nX-API-Key: " + value + b"\r\nConnection: close\r\n\r\n")
        data = b""
        while True:
            c = s.recv(65536)
            if not c:
                break
            data += c
    t = data.decode("latin-1")
    return t.split("\r\n", 1)[0].split(" ", 1)[1] + " | " + (t.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in t else "")


vals = {"3 spaces": b"   ", "2 tabs": b"\t\t", "space+tab": b" \t ", "NBSP (0xA0)": b"\xa0", "0x1C": b"\x1c"}
procs = []
try:
    for port, parser in ((47813, "h11"), (47814, "httptools")):
        assert free(port)
        p = subprocess.Popen([sys.executable, "-c", SERVER, str(port), parser], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(p)
        for _ in range(100):
            if not free(port):
                break
            time.sleep(0.1)
        print(f"== {parser}: " + "; ".join(f"{k} -> {get(port, v)}" for k, v in vals.items()))
finally:
    for p in procs:
        p.terminate()
        p.wait(timeout=10)
    print("stopped:", [p.returncode for p in procs])
