#!/usr/bin/env python3
"""
Real-uvicorn probe of the N-4 fix, its known limits and its two adjacent gaps: what a raw-socket client sees.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (measures the figures the N-4 round-2 texts state)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (section 8, ruling 11);
         juniper-service-core/juniper_service_core/websocket/manager.py,
         juniper-service-core/juniper_service_core/websocket/training_stream.py

Adapted from the round-1 code validator's probe (its scenarios and raw client, unchanged in substance), with the
matrix runner folded in. Two modes::

    python3 <this> matrix --out <dir> --model-core <dir> --cell <scenario>:<ws-impl>:<tree-tag>:<py-tag> [...]
                          --tree <tree-tag>=<dir holding juniper_service_core> [...] --python <py-tag>=<python> [...]
                          [--workers N]
    <python> <this> run <scenario> <ws-impl> <out-json>      (PYTHONPATH = the tree's directory and juniper-model-core)

``matrix`` runs each cell as ``<python> <this> run ...`` in its own process, at most four at a time, and writes
``<out>/matrix.json``. ``run`` binds 127.0.0.1 port 0 (a free port: no live service's port is touched), serves the
real ``training_stream_handler`` / ``control_stream_handler`` and ``WebSocketManager`` under uvicorn in this process,
and drives them with a raw-socket RFC 6455 client that can stop reading, or send a frame after the server's close.

Scenarios (ws-impl is uvicorn's ``ws=``: websockets | websockets-sansio | wsproto):

- stall: ``max_connections_per_ip=1``, send timeout 0.5 s. Client A completes the handshake and never reads again
  (small SO_RCVBUF). 55 kB broadcasts until A is dropped. Then client B, same address, connects. Records whether B is
  admitted while A's handler still runs, how long A's handler outlives the drop (waited for up to 45 s), and the
  manager's close record: at the drop, after that wait, when both handlers have ended (the clients then close their
  sockets), and 3 s later.
- poison: two clients; one good broadcast, then one Starlette's ``send_json`` cannot serialise (a datetime). Records
  what each client sees, the accounting, what two resumes from the last good seq get, and that a fresh connect works.
- late_training / late_control: heartbeat 0.3 s / 0.3 s, the client never answers a ping; after it has read the
  server's 1011 close frame it sends one more text frame, as a frame already in flight would arrive: a pong, or for
  ``late_control_command`` a ``stop`` command with an executor installed. Records how the handler ended, what the
  executor ran, and whether uvicorn logged "Exception in ASGI application".
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime
import inspect
import json
import logging
import os
import socket
import struct
import subprocess
import sys
import time
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCENARIOS = ("stall", "poison", "late_training", "late_control", "late_control_command")


class RawClient:
    """A minimal RFC 6455 client over a blocking socket driven from a thread."""

    def __init__(self, port: int, rcvbuf: int | None = None, timeout: float = 6.0) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if rcvbuf is not None:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
        self.sock.settimeout(timeout)
        self.sock.connect(("127.0.0.1", port))
        self.buf = b""
        self.timed_out = False

    def handshake(self, path: str = "/ws/training") -> int:
        key = base64.b64encode(os.urandom(16)).decode()
        req = f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        self.sock.sendall(req.encode())
        while b"\r\n\r\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                return -1
            self.buf += chunk
        head, self.buf = self.buf.split(b"\r\n\r\n", 1)
        return int(head.split(b" ", 2)[1])

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        mask = os.urandom(4)
        header = bytes([0x80 | opcode])
        size = len(payload)
        if size < 126:
            header += bytes([0x80 | size])
        elif size < 65536:
            header += bytes([0x80 | 126]) + struct.pack("!H", size)
        else:
            header += bytes([0x80 | 127]) + struct.pack("!Q", size)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(header + mask + masked)

    def send_text(self, obj: dict) -> str:
        try:
            self._send_frame(0x1, json.dumps(obj).encode())
        except OSError as exc:
            return f"send failed: {type(exc).__name__}"
        return "sent"

    def send_close(self, code: int = 1000) -> str:
        try:
            self._send_frame(0x8, struct.pack("!H", code))
        except OSError as exc:
            return f"send failed: {type(exc).__name__}"
        return "sent"

    def _need(self, size: int) -> bool:
        while len(self.buf) < size:
            try:
                chunk = self.sock.recv(65536)
            except TimeoutError:
                self.timed_out = True
                return False
            except OSError:
                return False
            if not chunk:
                return False
            self.buf += chunk
        return True

    def read_frame(self) -> tuple[int, bytes] | None:
        if not self._need(2):
            return None
        first, second = self.buf[0], self.buf[1]
        size, offset = second & 0x7F, 2
        if size == 126:
            if not self._need(4):
                return None
            size, offset = struct.unpack("!H", self.buf[2:4])[0], 4
        elif size == 127:
            if not self._need(10):
                return None
            size, offset = struct.unpack("!Q", self.buf[2:10])[0], 10
        if not self._need(offset + size):
            return None
        payload, self.buf = self.buf[offset : offset + size], self.buf[offset + size :]
        return first & 0x0F, payload

    def read_until_close(self, limit: int = 1000) -> dict:
        texts = []
        for _ in range(limit):
            frame = self.read_frame()
            if frame is None:
                return {"texts": texts, "close": None, "eof": not self.timed_out, "timed_out": self.timed_out}
            opcode, payload = frame
            if opcode == 0x1:
                texts.append(json.loads(payload))
            elif opcode == 0x8:
                code = struct.unpack("!H", payload[:2])[0] if len(payload) >= 2 else None
                return {"texts": texts, "close": [code, payload[2:].decode(errors="replace")], "eof": False, "timed_out": False}
        return {"texts": texts, "close": None, "eof": False, "timed_out": False}

    def read_text(self) -> dict | None:
        frame = self.read_frame()
        if frame is None or frame[0] != 0x1:
            return None
        return json.loads(frame[1])

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            # Already closed by the peer or the server: nothing left to release.
            return


class Capture(logging.Handler):
    """Collects every record of the loggers it is attached to."""

    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(f"{record.name} {record.levelname} {record.getMessage()}")


class RecordingExecutor:
    """A ``/ws/control`` command executor that records what it is asked to run (the handler calls it in a thread)."""

    def __init__(self) -> None:
        self.ran: list[str] = []

    def execute(self, command: str, params: dict | None) -> dict:
        self.ran.append(command)
        return {"status": "ok", "command": command, "params": params}


def kinds(texts: list) -> list:
    return [t["seq"] if "seq" in t else t.get("type") for t in texts]


def build_app(mods: types.SimpleNamespace, mgr, live: dict, executor: RecordingExecutor | None, **settings):
    app = mods.FastAPI()
    app.state.ws_manager = mgr
    app.state.lifecycle = None
    app.state.command_executor = executor
    values = {"ws_resume_handshake_timeout_s": 2.0, "ws_initial_metrics_count": 0, "ws_heartbeat_interval_sec": 3600, "ws_heartbeat_pong_timeout_sec": 3600, "ws_control_idle_timeout_sec": 0}
    values.update(settings)
    app.state.settings = types.SimpleNamespace(**values)

    async def tracked(handler, websocket) -> None:
        key = id(websocket)
        live[key] = {"start": time.monotonic(), "end": None, "raised": None}
        try:
            await handler(websocket)
        except Exception as exc:
            live[key]["raised"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            live[key]["end"] = time.monotonic()

    async def training(websocket) -> None:
        await tracked(mods.training_stream_handler, websocket)

    async def control(websocket) -> None:
        await tracked(mods.control_stream_handler, websocket)

    # Starlette routes, not ``@app.websocket``: FastAPI resolves a route's annotations in the module's globals, and
    # the WebSocket class is imported only inside ``run`` (``matrix`` needs neither fastapi nor the package).
    app.router.routes.append(mods.WebSocketRoute("/ws/training", training))
    app.router.routes.append(mods.WebSocketRoute("/ws/control", control))
    return app


async def until(predicate, limit: float = 20.0) -> bool:
    deadline = time.monotonic() + limit
    while not predicate():
        if time.monotonic() > deadline:
            return False
        await asyncio.sleep(0.01)
    return True


def closing_count(mgr):
    record = getattr(mgr, "_closing", None)
    return None if record is None else len(record)


async def scenario_stall(port: int, mgr, live: dict) -> dict:
    out: dict = {}
    a = RawClient(port, rcvbuf=4096)
    out["a_handshake"] = await asyncio.to_thread(a.handshake)
    await asyncio.to_thread(a.read_text)
    a.send_text({"type": "hello"})
    await until(lambda: mgr.connection_count == 1)
    big = "x" * 55_000
    started = time.monotonic()
    sent = 0
    slowest = 0.0
    while mgr.connection_count == 1 and time.monotonic() - started < 60:
        before = time.monotonic()
        await mgr.broadcast({"type": "metrics", "data": {"blob": big}})
        slowest = max(slowest, time.monotonic() - before)
        sent += 1
    dropped_at = time.monotonic()
    out["broadcasts_until_drop"] = sent
    out["slowest_broadcast_seconds"] = round(slowest, 3)
    out["dropped"] = mgr.connection_count == 0
    out["per_ip_after_drop"] = dict(mgr._per_ip_counts)
    out["endpoint_counts_after_drop"] = mgr.endpoint_counts()
    out["closing_record_at_drop"] = closing_count(mgr)
    a_key = next(iter(live))
    out["a_handler_alive_at_drop"] = live[a_key]["end"] is None
    before = time.monotonic()
    await mgr.broadcast({"type": "metrics", "data": {"blob": "after the drop"}})
    out["next_broadcast_seconds"] = round(time.monotonic() - before, 3)
    b = RawClient(port)
    out["b_handshake"] = await asyncio.to_thread(b.handshake)
    b_first = await asyncio.to_thread(b.read_text)
    out["b_first_frame"] = b_first.get("type") if b_first else None
    b.send_text({"type": "hello"})
    await asyncio.sleep(0.3)
    out["b_active"] = mgr.connection_count == 1
    out["a_handler_alive_when_b_active"] = live[a_key]["end"] is None
    out["handlers_running_from_one_ip_with_cap_1"] = sum(1 for entry in live.values() if entry["end"] is None)
    out["connection_count_with_b"] = mgr.connection_count
    out["endpoint_counts_with_b"] = mgr.endpoint_counts()
    await until(lambda: live[a_key]["end"] is not None, limit=45)
    end = live[a_key]["end"]
    out["a_handler_outlived_drop_seconds"] = None if end is None else round(end - dropped_at, 2)
    out["a_handler_still_running_after_45s"] = end is None
    out["a_handler_raised"] = live[a_key]["raised"]
    out["closing_record_after_the_wait"] = closing_count(mgr)
    out["per_ip_after_the_wait"] = dict(mgr._per_ip_counts)
    b.close()
    client_left_at = time.monotonic()
    a.close()
    await until(lambda: all(entry["end"] is not None for entry in live.values()), limit=10)
    end = live[a_key]["end"]
    out["a_handler_ended_after_the_client_closed_its_socket"] = end is not None
    out["seconds_from_the_client_closing_to_a_handler_end"] = None if end is None or end < client_left_at else round(end - client_left_at, 2)
    out["per_ip_final"] = dict(mgr._per_ip_counts)
    out["closing_record_when_all_handlers_ended"] = closing_count(mgr)
    await asyncio.sleep(3.0)
    out["closing_record_3s_after_all_handlers_ended"] = closing_count(mgr)
    record = getattr(mgr, "_closing", None)
    out["pending_close_tasks_3s_after_all_handlers_ended"] = None if record is None else sum(1 for task in record.values() if not task.done())
    return out


async def scenario_poison(port: int, mgr, live: dict) -> dict:
    out: dict = {}
    clients = [RawClient(port), RawClient(port)]
    established: dict = {}
    for client in clients:
        await asyncio.to_thread(client.handshake)
        established = await asyncio.to_thread(client.read_text) or {}
        client.send_text({"type": "hello"})
    await until(lambda: mgr.connection_count == 2)
    await mgr.broadcast({"type": "metrics", "data": {"tag": "good"}})
    await mgr.broadcast({"type": "metrics", "data": {"when": datetime.datetime(2026, 11, 11, tzinfo=datetime.timezone.utc)}})
    seen = [await asyncio.to_thread(client.read_until_close) for client in clients]
    out["clients_frames"] = [kinds(s["texts"]) for s in seen]
    out["clients_close"] = [s["close"] for s in seen]
    out["clients_read_timed_out"] = [s["timed_out"] for s in seen]
    out["after_poison"] = {"connection_count": mgr.connection_count, "per_ip": dict(mgr._per_ip_counts), "handlers_alive": sum(1 for entry in live.values() if entry["end"] is None), "send_failures": mgr.transport_stats()["send_failures"]}
    for client in clients:
        client.send_close(1011)
        client.close()
    await until(lambda: all(entry["end"] is not None for entry in live.values()))
    out["handlers_raised"] = [entry["raised"] for entry in live.values()]
    resumes = []
    for _ in range(2):
        resumer = RawClient(port)
        await asyncio.to_thread(resumer.handshake)
        await asyncio.to_thread(resumer.read_text)
        resumer.send_text({"type": "resume", "data": {"last_seq": 1, "server_instance_id": established.get("data", {}).get("server_instance_id")}})
        got = await asyncio.to_thread(resumer.read_until_close)
        resumes.append({"frames": kinds(got["texts"]), "close": got["close"]})
        resumer.close()
    out["resumes_from_seq_1"] = resumes
    fresh = RawClient(port)
    await asyncio.to_thread(fresh.handshake)
    await asyncio.to_thread(fresh.read_text)
    fresh.send_text({"type": "hello"})
    await until(lambda: mgr.connection_count == 1)
    await mgr.broadcast({"type": "metrics", "data": {"tag": "after"}})
    got_fresh = await asyncio.to_thread(fresh.read_text)
    out["fresh_connect_gets_seq"] = None if got_fresh is None else got_fresh.get("seq")
    fresh.close()
    return out


async def scenario_late(port: int, mgr, live: dict, path: str, late_frame: dict, executor: RecordingExecutor | None) -> dict:
    out: dict = {}
    client = RawClient(port)
    out["handshake"] = await asyncio.to_thread(client.handshake, path)
    await asyncio.to_thread(client.read_text)
    if path == "/ws/training":
        client.send_text({"type": "hello"})
    seen = await asyncio.to_thread(client.read_until_close)
    out["frames_before_close"] = kinds(seen["texts"])
    out["close_seen_by_client"] = seen["close"]
    out["late_frame"] = late_frame
    out["late_frame_send"] = client.send_text(late_frame)
    await asyncio.sleep(0.5)
    entry = next(iter(live.values()))
    out["handler_ended_before_client_left"] = entry["end"] is not None
    client.send_close(1011)
    client.close()
    await until(lambda: entry["end"] is not None, limit=30)
    out["handler_ended"] = entry["end"] is not None
    out["handler_raised"] = entry["raised"]
    out["executor_ran"] = None if executor is None else list(executor.ran)
    out["accounting"] = {"connection_count": mgr.connection_count, "per_ip": dict(mgr._per_ip_counts), "endpoint_counts": mgr.endpoint_counts()}
    return out


async def run_async(mods: types.SimpleNamespace, scenario: str, ws_impl: str) -> dict:
    mgr = mods.WebSocketManager(send_timeout_seconds=0.5, max_connections_per_ip=1 if scenario == "stall" else 5)
    live: dict = {}
    late = scenario.startswith("late_")
    executor = RecordingExecutor() if scenario == "late_control_command" else None
    app = build_app(mods, mgr, live, executor, **({"ws_heartbeat_interval_sec": 0.3, "ws_heartbeat_pong_timeout_sec": 0.3} if late else {}))
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    server = mods.uvicorn.Server(mods.uvicorn.Config(app, ws=ws_impl, log_level="warning", lifespan="off"))
    # Attached only now: uvicorn.Config's dictConfig replaces the handlers of the uvicorn loggers, so a handler
    # attached before it never sees "Exception in ASGI application".
    capture = Capture()
    for name in ("uvicorn.error", "juniper_service_core"):
        logging.getLogger(name).addHandler(capture)
        logging.getLogger(name).setLevel(logging.DEBUG)
    serving = asyncio.create_task(server.serve(sockets=[listener]))
    await until(lambda: server.started)
    try:
        if scenario == "stall":
            body = await scenario_stall(port, mgr, live)
        elif scenario == "poison":
            body = await scenario_poison(port, mgr, live)
        elif scenario == "late_training":
            body = await scenario_late(port, mgr, live, "/ws/training", {"type": "pong"}, executor)
        elif scenario == "late_control":
            body = await scenario_late(port, mgr, live, "/ws/control", {"type": "pong"}, executor)
        else:
            body = await scenario_late(port, mgr, live, "/ws/control", {"command": "stop"}, executor)
    finally:
        server.should_exit = True
        await asyncio.wait({serving}, timeout=30)
    body["asgi_exceptions_logged"] = sum(1 for record in capture.records if "Exception in ASGI application" in record)
    body["drop_logs"] = [record for record in capture.records if "Broadcast of seq" in record or "dropped WebSocket" in record][:4]
    body["resume_abort_logs"] = sum(1 for record in capture.records if "Resume aborted" in record)
    return body


def run(scenario: str, ws_impl: str, out_path: str) -> int:
    import uvicorn
    from fastapi import FastAPI
    from starlette.routing import WebSocketRoute

    from juniper_service_core.websocket.control_stream import control_stream_handler
    from juniper_service_core.websocket.manager import WebSocketManager
    from juniper_service_core.websocket.training_stream import training_stream_handler

    mods = types.SimpleNamespace(uvicorn=uvicorn, FastAPI=FastAPI, WebSocketRoute=WebSocketRoute, control_stream_handler=control_stream_handler, WebSocketManager=WebSocketManager, training_stream_handler=training_stream_handler)
    result = {"scenario": scenario, "ws": ws_impl, "python": sys.version.split()[0], "uvicorn": uvicorn.__version__, "manager_has_drop": hasattr(WebSocketManager, "_drop"), "manager_file": inspect.getfile(WebSocketManager)}
    result.update(asyncio.run(run_async(mods, scenario, ws_impl)))
    Path(out_path).write_text(json.dumps(result, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1, default=str))
    return 0


def _run_cell(cell: str, trees: dict[str, str], pythons: dict[str, str], model_core: str, out: Path) -> dict:
    scenario, impl, tree_tag, py_tag = cell.split(":")
    stem = f"{scenario}-{tree_tag}-{py_tag}-{impl}"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([trees[tree_tag], model_core])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    out_json = out / f"{stem}.json"
    if out_json.exists():
        out_json.unlink()
    log = out / f"{stem}.log"
    with log.open("w", encoding="utf-8") as handle:
        try:
            rc: int | str = subprocess.run([pythons[py_tag], str(Path(__file__).resolve()), "run", scenario, impl, str(out_json)], env=env, stdout=handle, stderr=subprocess.STDOUT, timeout=240, check=False).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
    row: dict = {"cell": stem, "rc": rc}
    if out_json.exists():
        row["result"] = json.loads(out_json.read_text(encoding="utf-8"))
    else:
        row["log_tail"] = log.read_text(encoding="utf-8")[-1500:]
    return row


def matrix(args: argparse.Namespace) -> int:
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    trees = dict(item.split("=", 1) for item in args.tree)
    pythons = dict(item.split("=", 1) for item in args.python)
    with ThreadPoolExecutor(max_workers=min(4, max(1, args.workers))) as pool:
        rows = list(pool.map(lambda cell: _run_cell(cell, trees, pythons, str(args.model_core.resolve()), out), args.cell))
    (out / "matrix.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        print(row["cell"], "rc=", row["rc"])
    return 0 if all(row["rc"] == 0 for row in rows) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="mode", required=True)
    one = sub.add_parser("run")
    one.add_argument("scenario", choices=SCENARIOS)
    one.add_argument("ws_impl")
    one.add_argument("out_json")
    many = sub.add_parser("matrix")
    many.add_argument("--out", required=True, type=Path)
    many.add_argument("--model-core", required=True, type=Path)
    many.add_argument("--cell", action="append", required=True)
    many.add_argument("--tree", action="append", required=True)
    many.add_argument("--python", action="append", required=True)
    many.add_argument("--workers", type=int, default=4, help="cells run at once (at most four)")
    args = parser.parse_args()
    if args.mode == "run":
        return run(args.scenario, args.ws_impl, args.out_json)
    return matrix(args)


if __name__ == "__main__":
    sys.exit(main())
