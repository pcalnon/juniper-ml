"""
Drive /ws/training over a real loopback WebSocket and record what a client receives for each malformed resume frame.

One run drives ONE source tree: juniper-cascor's ``src`` (kind ``cascor``) or a directory holding the
``juniper_service_core`` package (kind ``svc``: a ``git archive`` extraction of juniper-ml, or an unpacked wheel).
The service's own app is served by uvicorn on an ephemeral 127.0.0.1 port and a ``websockets`` client talks to it,
so every frame and every close code is read off the wire, not off an in-memory double.

For each case a fresh ``WebSocketManager`` is put on ``app.state`` (what a freshly started server holds), in one of
four buffer states: ``fresh`` (nothing broadcast), ``buffered5`` (seqs 1-5 buffered), ``evicted`` (a 3-slot buffer
holding seqs 3-5) and ``disabled`` (replay off, 5 broadcasts numbered). A witness client is connected and active
first, so a tree whose ``broadcast`` numbers nothing while no socket is active builds the same state.

No timing decides what is recorded. After the frame under test the client sends ``subscribe_metrics``; the server
answers that from its receive loop, which starts only when the handshake and any snapshot have been sent, so the
frames before that answer are exactly the handshake's. A broadcast is then made (awaited on the server's loop) and a
second ``subscribe_metrics`` bounds what the socket received live.

The six Sentry DSN variables are set to the empty string and every other JUNIPER_* / CASCOR_* / CANOPY_* variable is
removed from this process before any service module is imported. Nothing is printed from the environment.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor#754; the design check of whether juniper-service-core follows cascor's two new resume answers
"""

import argparse
import asyncio
import hashlib
import importlib
import importlib.metadata
import inspect
import json
import os
import socket
import sys
import threading
import time
import types
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
SCRUBBED_PREFIXES = ("JUNIPER_", "CASCOR_", "CANOPY_")

RECV_TIMEOUT_S = 15.0
HANDSHAKE_TIMEOUT_S = 0.3
ORIGIN = "http://localhost:8050"
SENTINEL = '{"type":"subscribe_metrics","data":{"max_count":1}}'
NOOP = '{"type":"noop"}'

#: name -> (replay buffer capacity, broadcasts made before the client under test connects)
STATES = {
    "fresh": (1024, 0),
    "buffered5": (1024, 5),
    "evicted": (3, 5),
    "disabled": (0, 5),
}

#: Raw JSON text for ``last_seq`` in an otherwise well-formed resume frame.
LAST_SEQ_RAW = [
    "0",
    "1",
    "2",
    "3",
    "5",
    "6",
    "1000",
    "-1",
    "-5",
    "-1000000000000000000000000000000",
    "-0",
    "3.0",
    "2.5",
    "-1.0",
    "-0.0",
    "1e2",
    "1e400",
    "true",
    "false",
    "null",
    "NaN",
    "Infinity",
    "-Infinity",
    '"3"',
    '"abc"',
    '""',
    '"-1"',
    "[3]",
    "[]",
    "{}",
    '{"seq":3}',
]

#: Whole frames, as raw text. ``@ID@`` is replaced by the server's own instance id. ``None`` sends nothing.
FRAMES = {
    "no-frame": None,
    "data-absent": '{"type":"resume"}',
    "data-null": '{"type":"resume","data":null}',
    "data-empty-object": '{"type":"resume","data":{}}',
    "data-empty-list": '{"type":"resume","data":[]}',
    "data-list-holding-a-cursor": '{"type":"resume","data":[{"last_seq":3,"server_instance_id":"@ID@"}]}',
    "data-string": '{"type":"resume","data":"last_seq"}',
    "data-empty-string": '{"type":"resume","data":""}',
    "data-int": '{"type":"resume","data":7}',
    "data-zero": '{"type":"resume","data":0}',
    "data-float": '{"type":"resume","data":1.5}',
    "data-true": '{"type":"resume","data":true}',
    "data-false": '{"type":"resume","data":false}',
    "last_seq-absent": '{"type":"resume","data":{"server_instance_id":"@ID@"}}',
    "id-absent": '{"type":"resume","data":{"last_seq":3}}',
    "id-null": '{"type":"resume","data":{"last_seq":3,"server_instance_id":null}}',
    "id-stale": '{"type":"resume","data":{"last_seq":3,"server_instance_id":"stale-id"}}',
    "id-stale+last_seq-negative": '{"type":"resume","data":{"last_seq":-1,"server_instance_id":"stale-id"}}',
    "id-stale+last_seq-string": '{"type":"resume","data":{"last_seq":"3","server_instance_id":"stale-id"}}',
    "id-stale+last_seq-fraction": '{"type":"resume","data":{"last_seq":2.5,"server_instance_id":"stale-id"}}',
    "id-number": '{"type":"resume","data":{"last_seq":3,"server_instance_id":5}}',
    "flat-cursor-no-data": '{"type":"resume","last_seq":3,"server_instance_id":"@ID@"}',
    "frame-list": "[1,2]",
    "frame-string": '"resume"',
    "frame-number": "5",
    "frame-null": "null",
    "frame-not-json": "resume",
    "frame-other-type": NOOP,
    "frame-type-absent": '{"data":{"last_seq":3,"server_instance_id":"@ID@"}}',
}


def all_cases() -> list[tuple[str, str | None]]:
    """``(case id, raw frame template)`` for every case, the ``last_seq`` family first."""
    cases: list[tuple[str, str | None]] = [(f"last_seq={raw}", '{"type":"resume","data":{"last_seq":' + raw + ',"server_instance_id":"@ID@"}}') for raw in LAST_SEQ_RAW]
    cases.extend(FRAMES.items())
    return cases


def prepare_environment(log_dir: Path) -> None:
    """Empty the six Sentry variables, drop every other service variable, and point cascor's logs at ``log_dir``."""
    for name in list(os.environ):
        if name.startswith(SCRUBBED_PREFIXES):
            del os.environ[name]
    for name in SENTRY_DSN_NAMES:
        os.environ[name] = ""
    os.environ["JUNIPER_CASCOR_LOG_DIR"] = str(log_dir)


def sha256_of(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def module_under(module, root: Path) -> str:
    """The module's file, after checking it was imported from ``root``."""
    found = Path(module.__file__).resolve()
    if root.resolve() not in found.parents:
        raise SystemExit(f"{module.__name__} was imported from {found}, not from {root}")
    return str(found)


class Target:
    """One source tree: its app, and how to put a fresh manager on it."""

    def __init__(self, kind: str, src: Path, port: int):
        self.kind = kind
        sys.path.insert(0, str(src))
        if kind == "cascor":
            app_module = importlib.import_module("api.app")
            settings_module = importlib.import_module("api.settings")
            self._manager_module = importlib.import_module("api.websocket.manager")
            stream_module = importlib.import_module("api.websocket.training_stream")
            self._settings = settings_module.Settings(_env_file=None, host="127.0.0.1", port=port, ws_resume_handshake_timeout_s=HANDSHAKE_TIMEOUT_S, auto_start=False, auto_start_data_service=False, auto_start_canopy=False)
            self.app = app_module.create_app(self._settings)
        else:
            app_module = importlib.import_module("juniper_service_core.app")
            lifecycle_module = importlib.import_module("juniper_service_core.lifecycle")
            routes_module = importlib.import_module("juniper_service_core.routes")
            websocket_module = importlib.import_module("juniper_service_core.websocket")
            self._manager_module = importlib.import_module("juniper_service_core.websocket.manager")
            stream_module = importlib.import_module("juniper_service_core.websocket.training_stream")
            reference_module = importlib.import_module("juniper_model_core.conformance.reference")
            lifecycle = lifecycle_module.ServiceLifecycleManager(reference_module.ReferenceGrowableModel())
            self.app = app_module.create_app(routers=[*routes_module.build_routers(), websocket_module.build_websocket_router()])
            self.app.state.settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=HANDSHAKE_TIMEOUT_S)
            websocket_module.attach_websocket(self.app, manager=lifecycle, ws_manager=self._manager_module.WebSocketManager())
        self.files = {
            "training_stream": module_under(stream_module, src),
            "manager": module_under(self._manager_module, src),
        }

    def new_manager(self, capacity: int, loop: asyncio.AbstractEventLoop):
        """A manager as the service builds it, with ``capacity`` replay slots, installed on ``app.state``."""
        manager_class = self._manager_module.WebSocketManager
        if self.kind == "cascor":
            wanted = {
                "max_connections": self._settings.ws_max_connections,
                "send_timeout_seconds": self._settings.ws_send_timeout_seconds,
                "max_connections_per_ip": self._settings.ws_max_connections_per_ip,
                "max_connections_global": getattr(self._settings, "ws_max_connections_global", None),
                "max_connections_per_identity": getattr(self._settings, "ws_max_connections_per_identity", None),
                "max_message_size_bytes": self._settings.ws_max_message_size_bytes,
                "chunk_payload_size_bytes": self._settings.ws_chunk_payload_size_bytes,
                "emission_summary_interval_sec": getattr(self._settings, "ws_emission_summary_interval_sec", None),
            }
            accepted = inspect.signature(manager_class.__init__).parameters
            kwargs = {name: value for name, value in wanted.items() if name in accepted and value is not None}
            manager = manager_class(max_replay_buffer_size=capacity, **kwargs)
            manager.set_event_loop(loop)
        else:
            manager = manager_class(max_replay_buffer_size=capacity)
        self.app.state.ws_manager = manager
        return manager


class LoopbackServer:
    """uvicorn serving ``app`` on an ephemeral 127.0.0.1 port, on its own thread and event loop."""

    def __init__(self, listener: socket.socket):
        self._listener = listener
        self.port = listener.getsockname()[1]
        self.loop: asyncio.AbstractEventLoop | None = None
        self._server = None
        self._thread = threading.Thread(target=self._run, name="d14-probe-uvicorn", daemon=True)

    def start(self, app) -> None:
        uvicorn = importlib.import_module("uvicorn")
        self._server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="warning", lifespan="on"))
        self._thread.start()
        deadline = time.monotonic() + 120.0
        while not self._server.started:
            if not self._thread.is_alive():
                raise SystemExit("the server thread ended during startup")
            if time.monotonic() > deadline:
                raise SystemExit("the server did not start within 120 s")
            time.sleep(0.02)

    def _run(self) -> None:
        asyncio.run(self._serve())

    async def _serve(self) -> None:
        self.loop = asyncio.get_running_loop()
        await self._server.serve(sockets=[self._listener])

    def call(self, coroutine):
        """Run ``coroutine`` on the server's loop and wait for it."""
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result(timeout=RECV_TIMEOUT_S)

    def stop(self) -> bool:
        self._server.should_exit = True
        self._thread.join(timeout=20.0)
        return not self._thread.is_alive()


def manager_state(manager) -> dict:
    """What the manager holds, read between operations."""
    buffered = [message.get("seq") for message in list(manager._replay_buffer)]
    return {
        "current_seq": manager.current_seq,
        "buffered_seqs": buffered,
        "capacity": manager._replay_buffer_max_size,
        "active": len(manager._active_connections),
        "pending": len(manager._pending_connections),
    }


def describe(frame: dict) -> str:
    """One frame as a short label: its type, its seq when it has one, and the field that decides a resume."""
    kind = frame.get("type")
    data = frame.get("data") if isinstance(frame.get("data"), dict) else {}
    if kind == "resume_ok":
        return f"resume_ok(replayed_count={data.get('replayed_count')})"
    if kind == "resume_failed":
        return f"resume_failed({data.get('reason')})"
    if kind == "initial_metrics":
        return f"initial_metrics(current_seq={data.get('current_seq')})"
    if "seq" in frame:
        return f"{kind}#{frame['seq']}"
    return str(kind)


class Client:
    """A ``websockets`` sync client that records every frame and the close it ends on."""

    def __init__(self, port: int):
        client_module = importlib.import_module("websockets.sync.client")
        self._exceptions = importlib.import_module("websockets.exceptions")
        self._socket = client_module.connect(f"ws://127.0.0.1:{port}/ws/training", origin=ORIGIN, open_timeout=RECV_TIMEOUT_S, close_timeout=2.0)
        self.close: dict | None = None

    def send(self, text: str) -> bool:
        try:
            self._socket.send(text)
        except self._exceptions.ConnectionClosed as closed:
            self._record_close(closed)
            return False
        return True

    def receive(self) -> dict | None:
        """The next frame, or ``None`` once the connection has closed or nothing came within the timeout."""
        try:
            raw = self._socket.recv(timeout=RECV_TIMEOUT_S)
        except TimeoutError:
            self.close = {"code": None, "reason": f"PROBE TIMEOUT: nothing received within {RECV_TIMEOUT_S} s"}
            return None
        except self._exceptions.ConnectionClosed as closed:
            self._record_close(closed)
            return None
        return json.loads(raw)

    def _record_close(self, closed) -> None:
        received = closed.rcvd
        self.close = {"code": received.code if received is not None else 1006, "reason": received.reason if received is not None else "no close frame received"}

    def until_sentinel_answer(self) -> list[dict]:
        """Frames up to, not including, the answer to ``subscribe_metrics``.

        A snapshot is ``initial_status``, ``state``, ``initial_metrics`` in that order, so an
        ``initial_metrics`` that follows an ``initial_status`` belongs to the snapshot and the next one is the answer.
        """
        frames: list[dict] = []
        snapshot_open = False
        while True:
            frame = self.receive()
            if frame is None:
                return frames
            kind = frame.get("type")
            if kind == "initial_status":
                snapshot_open = True
            elif kind == "initial_metrics":
                if not snapshot_open:
                    return frames
                snapshot_open = False
            frames.append(frame)

    def shut(self) -> None:
        try:
            self._socket.close()
        except self._exceptions.WebSocketException:
            return


def run_case(target: Target, server: LoopbackServer, state: str, case_id: str, template: str | None) -> dict:
    capacity, broadcasts = STATES[state]
    manager = target.new_manager(capacity, server.loop)

    witness = Client(server.port)
    witness_frames = [witness.receive()]
    witness.send(NOOP)
    witness_frames.extend(witness.receive() for _ in range(3))
    for index in range(broadcasts):
        server.call(manager.broadcast({"type": "metrics", "timestamp": time.time(), "data": {"probe": "before", "index": index + 1}}))
        witness_frames.append(witness.receive())
    before = manager_state(manager)

    client = Client(server.port)
    established = client.receive()
    server_id = established["data"]["server_instance_id"]
    record: dict = {"state": state, "case": case_id, "sent": template, "state_before": before, "established": describe(established)}
    if template is None:
        handshake = [client.receive() for _ in range(3)]
        client.send(SENTINEL)
        handshake.extend(client.until_sentinel_answer())
    else:
        client.send(template.replace("@ID@", server_id))
        client.send(SENTINEL)
        handshake = client.until_sentinel_answer()
    record["handshake_frames"] = [frame for frame in handshake if frame is not None]
    record["handshake"] = [describe(frame) for frame in record["handshake_frames"]]
    record["close_after_handshake"] = client.close
    record["state_after_handshake"] = manager_state(manager)

    server.call(manager.broadcast({"type": "state", "timestamp": time.time(), "data": {"probe": "live"}}))
    witness_live = witness.receive()
    record["witness_live"] = describe(witness_live) if witness_live is not None else None
    live: list[dict] = []
    if client.close is None and client.send(SENTINEL):
        live = client.until_sentinel_answer()
    record["live"] = [describe(frame) for frame in live]
    record["close"] = client.close
    record["witness"] = [describe(frame) for frame in witness_frames if frame is not None]
    client.shut()
    witness.shut()
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--kind", choices=("cascor", "svc"), required=True)
    parser.add_argument("--name", required=True, help="label of this target in the output")
    parser.add_argument("--src", type=Path, required=True, help="cascor's src directory, or the directory holding juniper_service_core")
    parser.add_argument("--out", type=Path, required=True, help="JSON file to write")
    parser.add_argument("--log-dir", type=Path, required=True, help="directory for the service's own log files")
    parser.add_argument("--only-state", choices=tuple(STATES), default=None)
    args = parser.parse_args()

    args.log_dir.mkdir(parents=True, exist_ok=True)
    prepare_environment(args.log_dir)
    os.chdir(args.log_dir)

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    server = LoopbackServer(listener)
    target = Target(args.kind, args.src.resolve(), server.port)
    server.start(target.app)

    states = [args.only_state] if args.only_state else list(STATES)
    records = []
    for state in states:
        for case_id, template in all_cases():
            records.append(run_case(target, server, state, case_id, template))
    stopped = server.stop()

    versions = {name: importlib.metadata.version(name) for name in ("fastapi", "starlette", "uvicorn", "websockets")}
    result = {
        "target": args.name,
        "kind": args.kind,
        "src": str(args.src.resolve()),
        "files": {label: {"path": path, "sha256": sha256_of(path)} for label, path in target.files.items()},
        "python": sys.version.split()[0],
        "versions": versions,
        "transport": "uvicorn on 127.0.0.1 (ephemeral port) + websockets.sync.client",
        "server_stopped_cleanly": stopped,
        "cases": records,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(f"{args.name}: {len(records)} cases written to {args.out}; server stopped cleanly: {stopped}")
    sys.stdout.flush()
    # cascor's lifespan can outlive the serving thread (worker monitor, executor); the result is on disk, so leave now.
    os._exit(0)


if __name__ == "__main__":
    main()
