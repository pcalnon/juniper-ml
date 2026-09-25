"""Library-level probe: does each outbound client raise an exception whose text holds a padded key?

Runs a raw-socket capture server (HTTP 200 JSON / 101 WS upgrade) and pushes a set of padded
key values through requests, JuniperCascorClient (REST + WS), JuniperDataClient and httpx.
Prints, per client and value: outcome, whether str(exc) contains the key body, and whether
the key bytes reached the wire.
"""

import asyncio
import base64
import hashlib
import importlib.metadata as md
import socket
import threading

import httpx
import requests

CAPTURED: list[bytes] = []


def _serve(sock: socket.socket) -> None:
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
        CAPTURED.append(data)
        try:
            if b"upgrade: websocket" in data.lower():
                key = b""
                for line in data.split(b"\r\n"):
                    if line.lower().startswith(b"sec-websocket-key:"):
                        key = line.split(b":", 1)[1].strip()
                acc = base64.b64encode(hashlib.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
                conn.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + acc + b"\r\n\r\n")
            else:
                body = b'{"status":"ok","dataset_id":"x"}'
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
        except OSError:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass


VALUES = {
    "lead-space": " LEAKME-lead-space",
    "trail-space": "LEAKME-trail-space ",
    "trail-LF": "LEAKME-trail-LF\n",
    "lead-tab": "\tLEAKME-lead-tab",
    "trail-CRLF": "LEAKME-trail-CRLF\r\n",
    "inner-LF": "LEAKME-in\nner-LF",
    "inner-VT": "LEAKME-in\x0bner-VT",
    "trail-NBSP": "LEAKME-trail-NBSP ",
    "latin1": "LEAKME-clé",
    "non-latin1": "LEAKME-euro€",
}


def check(label: str, fn, value: str) -> None:
    before = len(CAPTURED)
    body = value.strip()
    try:
        fn(value)
        outcome, text = "OK", ""
    except BaseException as exc:  # noqa: BLE001
        outcome = type(exc).__name__
        text = str(exc)
        # include chained causes' text as a logger with exc_info would render
        c = exc.__cause__ or exc.__context__
        while c is not None:
            text += " || " + type(c).__name__ + ": " + str(c)
            c = c.__cause__ or c.__context__
    wire = b"".join(CAPTURED[before:])
    on_wire = body.encode("utf-8", "replace") in wire or body.encode("latin-1", "replace") in wire
    leak = "LEAKME" in text
    print(f"  {label:<14} {outcome:<32} key-in-exc-text={str(leak):<5} key-on-wire={on_wire}" + (f"  | {text[:150]!r}" if leak else ""))


def main() -> None:
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(64)
    port = srv.getsockname()[1]
    threading.Thread(target=_serve, args=(srv,), daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    print("versions:", {d: md.version(d) for d in ["requests", "urllib3", "httpx", "h11", "websockets", "juniper-cascor-client", "juniper-data-client"]})

    from juniper_cascor_client import CascorTrainingStream, JuniperCascorClient
    from juniper_data_client import JuniperDataClient

    def f_requests(v):
        requests.get(base + "/x", headers={"X-API-Key": v}, timeout=3)

    def f_cascor_rest(v):
        JuniperCascorClient(base_url=base, api_key=v, retries=0).get_training_status()

    def f_data(v):
        JuniperDataClient(base_url=base, api_key=v).create_dataset(generator="spiral", params={}, persist=True)

    def f_httpx(v):
        with httpx.Client(base_url=base, headers={"Accept": "application/json", "X-API-Key": v}, timeout=3) as c:
            c.request("GET", "/v1/training/status")

    def f_ws(v):
        async def go():
            s = CascorTrainingStream(base_url=f"ws://127.0.0.1:{port}", api_key=v)
            await s.connect()
            await s.disconnect()

        asyncio.run(go())

    for name, fn in [("requests", f_requests), ("cascor REST", f_cascor_rest), ("data-client", f_data), ("httpx", f_httpx), ("cascor WS", f_ws)]:
        print(f"== {name}")
        for label, v in VALUES.items():
            check(label, fn, v)


if __name__ == "__main__":
    main()
