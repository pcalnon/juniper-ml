"""
Drive /ws/training resume frames over a real loopback WebSocket, write the shared answer table, and compare answers.

Subcommands:

  drive    --kind cascor|svc --src DIR --out FILE --log-dir DIR
           One source tree: juniper-cascor's ``src`` (kind ``cascor``) or a directory holding the
           ``juniper_service_core`` package (kind ``svc``). Its own app is served by uvicorn on an ephemeral
           127.0.0.1 port and the ``websockets`` sync client sends each of the 60 frames in each of the four
           server states, so every reply is read off the wire. Writes one JSON record per case.
  table    --probe FILE --out FILE
           The shared table (``ws_resume_answers.json``) from one probe: juniper-cascor's main is the reference.
  compare  --table FILE PROBE [PROBE ...]
           For each probe, the cases whose answer differs from the table, and the probe's own problems.

Each case: a fresh ``WebSocketManager`` with the state's replay capacity on ``app.state.ws_manager``; the
state's broadcasts made on the server's loop (and the state checked: last seq numbered, seqs buffered); a client
connects, sends the frame (nothing for ``no-frame``) and a ``subscribe_metrics`` sentinel, which the server answers
only from its receive loop, after the handshake and any snapshot; the frames before that answer are the handshake.
Then one live broadcast and a second sentinel: the frames before its answer are what the socket received live. No
timing decides a record: the handshake timeout is 30 s when a frame is sent (never reached) and 0.25 s for
``no-frame``, where the client sends nothing until the snapshot has arrived.

The six Sentry DSN variables are set to the empty string and every other JUNIPER_* / CASCOR_* / CANOPY_* variable
is removed from this process before any service module is imported. Nothing is printed from the environment.
Adapted from the 2026-11-12 design check's ``2026-11-12_flood4r2_val_d14-resume_wire_probe.py``.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table); juniper-cascor#754
"""

import argparse
import asyncio
import hashlib
import importlib
import importlib.metadata
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
FRAME_HANDSHAKE_TIMEOUT_S = 30.0
NO_FRAME_HANDSHAKE_TIMEOUT_S = 0.25
ORIGIN = "http://localhost:8050"
SENTINEL = '{"type":"subscribe_metrics","data":{"max_count":1}}'

#: name -> (replay buffer capacity, broadcasts made before the client connects)
STATES = {"fresh": (1024, 0), "buffered5": (1024, 5), "evicted": (3, 5), "disabled": (0, 5)}

#: Raw JSON text for ``last_seq`` in an otherwise well-formed resume frame (the design check's 31).
LAST_SEQ_RAW = ["0", "1", "2", "3", "5", "6", "1000", "-1", "-5", "-1000000000000000000000000000000", "-0", "3.0", "2.5", "-1.0", "-0.0", "1e2", "1e400", "true", "false", "null", "NaN", "Infinity", "-Infinity", '"3"', '"abc"', '""', '"-1"', "[3]", "[]", "{}", '{"seq":3}']

#: Whole frames as raw text (the design check's 29). ``@ID@`` is the server's own instance id; ``None`` sends nothing.
WHOLE_FRAMES = [
    ("no-frame", None),
    ("data-absent", '{"type":"resume"}'),
    ("data-null", '{"type":"resume","data":null}'),
    ("data-empty-object", '{"type":"resume","data":{}}'),
    ("data-empty-list", '{"type":"resume","data":[]}'),
    ("data-list-holding-a-cursor", '{"type":"resume","data":[{"last_seq":3,"server_instance_id":"@ID@"}]}'),
    ("data-string", '{"type":"resume","data":"last_seq"}'),
    ("data-empty-string", '{"type":"resume","data":""}'),
    ("data-int", '{"type":"resume","data":7}'),
    ("data-zero", '{"type":"resume","data":0}'),
    ("data-float", '{"type":"resume","data":1.5}'),
    ("data-true", '{"type":"resume","data":true}'),
    ("data-false", '{"type":"resume","data":false}'),
    ("last_seq-absent", '{"type":"resume","data":{"server_instance_id":"@ID@"}}'),
    ("id-absent", '{"type":"resume","data":{"last_seq":3}}'),
    ("id-null", '{"type":"resume","data":{"last_seq":3,"server_instance_id":null}}'),
    ("id-stale", '{"type":"resume","data":{"last_seq":3,"server_instance_id":"stale-id"}}'),
    ("id-stale+last_seq-negative", '{"type":"resume","data":{"last_seq":-1,"server_instance_id":"stale-id"}}'),
    ("id-stale+last_seq-string", '{"type":"resume","data":{"last_seq":"3","server_instance_id":"stale-id"}}'),
    ("id-stale+last_seq-fraction", '{"type":"resume","data":{"last_seq":2.5,"server_instance_id":"stale-id"}}'),
    ("id-number", '{"type":"resume","data":{"last_seq":3,"server_instance_id":5}}'),
    ("flat-cursor-no-data", '{"type":"resume","last_seq":3,"server_instance_id":"@ID@"}'),
    ("frame-list", "[1,2]"),
    ("frame-string", '"resume"'),
    ("frame-number", "5"),
    ("frame-null", "null"),
    ("frame-not-json", "resume"),
    ("frame-other-type", '{"type":"noop"}'),
    ("frame-type-absent", '{"data":{"last_seq":3,"server_instance_id":"@ID@"}}'),
]

TABLE_ABOUT = [
    "One table of /ws/training resume frames and the answers a client reads off the wire, per server state.",
    "Two byte-identical copies: juniper-ml juniper-service-core/tests/fixtures/ws_resume_answers.json and juniper-cascor src/tests/fixtures/ws_resume_answers.json. A change to one is made to the other in the same pair of pull requests.",
    "Each repository drives its own handler against every row over a real WebSocket: juniper-ml juniper-service-core/tests/test_websocket_resume_answer_table.py, juniper-cascor src/tests/unit/api/test_websocket_resume_answer_table.py.",
    "juniper-ml tests/test_ws_resume_answer_table_drift.py fails when the two copies differ (in the weekly docs-full-check job, which clones the siblings, or locally with JUNIPER_DRIFT_TEST_FORCE_LOCAL=1).",
    "Seeded on 2026-11-15 from juniper-cascor's main (a1b0409d), served by uvicorn on 127.0.0.1 and driven with the websockets client.",
]

TABLE_FLOW = [
    "A fresh WebSocketManager with the state's replay_buffer_capacity is put on app.state.ws_manager, and the state's broadcasts are made, each {\"type\": \"metrics\"}.",
    "The client connects (connection_established, whose replay_buffer_capacity is the state's), sends the frame (nothing for no-frame), then {\"type\":\"subscribe_metrics\",\"data\":{\"max_count\":1}}.",
    "handshake: every frame received before the initial_metrics that answers that request. The server answers it only from its receive loop, which starts after the handshake and any snapshot.",
    "Then one live broadcast, {\"type\": \"metrics\"}, and a second subscribe_metrics: live is every frame received before its answer.",
    "The handshake timeout is 30 s when a frame is sent and 0.25 s for no-frame, where the client sends nothing until the snapshot has arrived.",
]

TABLE_LABELS = {
    "resume_ok(replayed_count=N)": "resume_ok and its data.replayed_count",
    "resume_failed(REASON)": "resume_failed and its data.reason",
    "initial_status": "the fresh-connect snapshot's first frame",
    "state": "the snapshot's second frame",
    "initial_metrics(current_seq=N)": "the snapshot's third frame and its data.current_seq",
    "TYPE#SEQ": "a numbered broadcast (replayed, caught up or live) by its type and seq",
    "close(CODE)": "the server closed the socket with CODE; no row expects one",
}

TABLE_NOT_COMPARED = [
    "timestamp, on every frame: the time it was sent",
    "connection_established.data.server_instance_id, server_start_time and connections: per process and per moment",
    "initial_status.data and state.data: the service's own lifecycle status and monitor state",
    "initial_metrics.data.count and data.metrics: the service's own metrics history",
    "a broadcast's payload beyond its type and seq (each service adds its own fields, such as emitted_at_monotonic)",
]


def all_frames() -> list[tuple[str, str | None]]:
    """``(frame id, raw text template)`` for the 60 frames, the ``last_seq`` family first."""
    frames: list[tuple[str, str | None]] = [(f"last_seq={raw}", '{"type":"resume","data":{"last_seq":' + raw + ',"server_instance_id":"@ID@"}}') for raw in LAST_SEQ_RAW]
    frames.extend(WHOLE_FRAMES)
    return frames


def expected_buffer(capacity: int, broadcasts: int) -> list[int]:
    """The seqs a manager with ``capacity`` slots holds after ``broadcasts`` broadcasts."""
    if capacity <= 0:
        return []
    return list(range(max(1, broadcasts - capacity + 1), broadcasts + 1))


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
    """The module's file, after checking it was imported from ``root`` (the env holds editable installs of the primaries)."""
    found = Path(module.__file__).resolve()
    if root.resolve() not in found.parents:
        raise SystemExit(f"{module.__name__} was imported from {found}, not from {root}")
    return str(found)


class Target:
    """One source tree: its app, a fresh manager per case, and the handshake timeout per case."""

    def __init__(self, kind: str, src: Path, port: int):
        self.kind = kind
        sys.path.insert(0, str(src))
        if kind == "cascor":
            app_module = importlib.import_module("api.app")
            settings_module = importlib.import_module("api.settings")
            self._manager_module = importlib.import_module("api.websocket.manager")
            stream_module = importlib.import_module("api.websocket.training_stream")
            settings = settings_module.Settings(_env_file=None, host="127.0.0.1", port=port, auto_start=False, auto_start_data_service=False, auto_start_canopy=False)
            self.app = app_module.create_app(settings)
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
            self.app.state.settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=FRAME_HANDSHAKE_TIMEOUT_S)
            websocket_module.attach_websocket(self.app, manager=lifecycle, ws_manager=self._manager_module.WebSocketManager())
        self.files = {"training_stream": module_under(stream_module, src), "manager": module_under(self._manager_module, src)}

    def new_manager(self, capacity: int, loop: asyncio.AbstractEventLoop):
        """A manager with ``capacity`` replay slots, installed on ``app.state`` (cascor's lifespan made the one it replaces)."""
        manager = self._manager_module.WebSocketManager(max_replay_buffer_size=capacity)
        if self.kind == "cascor":
            manager.set_event_loop(loop)
        self.app.state.ws_manager = manager
        return manager

    def set_handshake_timeout(self, seconds: float) -> None:
        if self.kind == "cascor":
            self.app.state.settings.ws_resume_handshake_timeout_s = seconds
        else:
            self.app.state.settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=seconds)


class LoopbackServer:
    """uvicorn serving ``app`` on an ephemeral 127.0.0.1 port, on its own thread and event loop."""

    def __init__(self, listener: socket.socket):
        self._listener = listener
        self.port = listener.getsockname()[1]
        self.loop: asyncio.AbstractEventLoop | None = None
        self._server = None
        self._thread = threading.Thread(target=self._run, name="d14-wire-uvicorn", daemon=True)

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


def label(frame: dict) -> str:
    """One received frame as a table label."""
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
    """A ``websockets`` sync client that labels every frame and records the close it ends on."""

    def __init__(self, port: int):
        client_module = importlib.import_module("websockets.sync.client")
        self._closed_error = importlib.import_module("websockets.exceptions").ConnectionClosed
        self._socket = client_module.connect(f"ws://127.0.0.1:{port}/ws/training", origin=ORIGIN, open_timeout=RECV_TIMEOUT_S, close_timeout=2.0)
        self.close: str | None = None
        self.problem: str | None = None

    def send(self, text: str) -> bool:
        try:
            self._socket.send(text)
        except self._closed_error as closed:
            self._record_close(closed)
            return False
        return True

    def receive(self) -> dict | None:
        """The next frame, or ``None`` once the connection has closed or nothing came within the timeout."""
        try:
            raw = self._socket.recv(timeout=RECV_TIMEOUT_S)
        except TimeoutError:
            self.problem = f"nothing received within {RECV_TIMEOUT_S} s"
            return None
        except self._closed_error as closed:
            self._record_close(closed)
            return None
        return json.loads(raw)

    def _record_close(self, closed) -> None:
        received = closed.rcvd
        self.close = f"close({received.code if received is not None else 1006})"

    def until_sentinel_answer(self) -> list[str]:
        """Labels of the frames before the ``initial_metrics`` that answers the sentinel.

        A snapshot is ``initial_status``, ``state``, ``initial_metrics``: an ``initial_metrics`` after an
        ``initial_status`` belongs to the snapshot, and the next one is the answer.
        """
        labels: list[str] = []
        snapshot_open = False
        while True:
            frame = self.receive()
            if frame is None:
                if self.close is not None:
                    labels.append(self.close)
                return labels
            kind = frame.get("type")
            if kind == "initial_status":
                snapshot_open = True
            elif kind == "initial_metrics":
                if not snapshot_open:
                    return labels
                snapshot_open = False
            labels.append(label(frame))

    def shut(self) -> None:
        try:
            self._socket.close()
        except OSError:
            return


def run_case(target: Target, server: LoopbackServer, state: str, frame_id: str, template: str | None) -> dict:
    capacity, broadcasts = STATES[state]
    manager = target.new_manager(capacity, server.loop)
    target.set_handshake_timeout(NO_FRAME_HANDSHAKE_TIMEOUT_S if template is None else FRAME_HANDSHAKE_TIMEOUT_S)
    for index in range(broadcasts):
        server.call(manager.broadcast({"type": "metrics", "timestamp": time.time(), "data": {"before": index + 1}}))
    record: dict = {"state": state, "frame": frame_id, "sent": template, "problems": []}
    built = (manager.current_seq, [message.get("seq") for message in list(manager._replay_buffer)])
    if built != (broadcasts, expected_buffer(capacity, broadcasts)):
        record["problems"].append(f"state not built: current_seq and buffer {built}")

    client = Client(server.port)
    established = client.receive()
    if established is None or established.get("type") != "connection_established":
        record["problems"].append(f"first frame {established!r}")
        client.shut()
        return record
    if established["data"].get("replay_buffer_capacity") != capacity:
        record["problems"].append(f"replay_buffer_capacity {established['data'].get('replay_buffer_capacity')}")
    if template is None:
        handshake = []
        for _ in range(3):
            frame = client.receive()
            if frame is not None:
                handshake.append(label(frame))
        client.send(SENTINEL)
        handshake.extend(client.until_sentinel_answer())
    else:
        client.send(template.replace("@ID@", established["data"]["server_instance_id"]))
        client.send(SENTINEL)
        handshake = client.until_sentinel_answer()
    live: list[str] = []
    if client.close is None:
        server.call(manager.broadcast({"type": "metrics", "timestamp": time.time(), "data": {"live": True}}))
        if client.send(SENTINEL):
            live = client.until_sentinel_answer()
    if client.problem is not None:
        record["problems"].append(client.problem)
    record["handshake"] = handshake
    record["live"] = live
    client.shut()
    return record


def drive(args: argparse.Namespace) -> None:
    args.log_dir.mkdir(parents=True, exist_ok=True)
    prepare_environment(args.log_dir)
    os.chdir(args.log_dir)
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    server = LoopbackServer(listener)
    target = Target(args.kind, args.src.resolve(), server.port)
    server.start(target.app)
    records = [run_case(target, server, state, frame_id, template) for state in STATES for frame_id, template in all_frames()]
    stopped = server.stop()
    result = {
        "kind": args.kind,
        "src": str(args.src.resolve()),
        "files": {name: {"path": path, "sha256": sha256_of(path)} for name, path in target.files.items()},
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "versions": {name: importlib.metadata.version(name) for name in ("fastapi", "starlette", "uvicorn", "websockets")},
        "server_stopped_cleanly": stopped,
        "cases": records,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1)
        handle.write("\n")
    problems = sum(len(record["problems"]) for record in records)
    print(f"{args.kind} {args.src}: {len(records)} cases written to {args.out}; probe problems {problems}; server stopped cleanly: {stopped}")
    sys.stdout.flush()
    # cascor's lifespan can leave threads that outlive the serving thread; the result is on disk.
    os._exit(0)


def render_table(table: dict) -> str:
    """The table as JSON text: two-space indent, and each state's answer on one line, so a row edit is a one-line diff."""
    head = json.dumps({key: value for key, value in table.items() if key != "frames"}, indent=2, ensure_ascii=False)
    lines: list[str] = []
    for index, row in enumerate(table["frames"]):
        lines.append("    {")
        lines.append(f'      "id": {json.dumps(row["id"], ensure_ascii=False)},')
        lines.append(f'      "sent": {json.dumps(row["sent"], ensure_ascii=False)},')
        lines.append('      "answers": {')
        answers = list(row["answers"].items())
        for position, (state, answer) in enumerate(answers):
            lines.append(f"        {json.dumps(state)}: {json.dumps(answer, ensure_ascii=False)}" + ("," if position < len(answers) - 1 else ""))
        lines.append("      }")
        lines.append("    }" + ("," if index < len(table["frames"]) - 1 else ""))
    return head[: -len("\n}")] + ',\n  "frames": [\n' + "\n".join(lines) + "\n  ]\n}\n"


def build_table(args: argparse.Namespace) -> None:
    with open(args.probe, encoding="utf-8") as handle:
        probe = json.load(handle)
    if any(record["problems"] for record in probe["cases"]):
        raise SystemExit("the probe recorded problems; no table is written from it")
    by_case = {(record["frame"], record["state"]): record for record in probe["cases"]}
    frames = []
    for frame_id, template in all_frames():
        answers = {state: {"handshake": by_case[(frame_id, state)]["handshake"], "live": by_case[(frame_id, state)]["live"]} for state in STATES}
        frames.append({"id": frame_id, "sent": template, "answers": answers})
    table = {
        "about": TABLE_ABOUT,
        "flow": TABLE_FLOW,
        "labels": TABLE_LABELS,
        "not_compared": TABLE_NOT_COMPARED,
        "states": {state: {"replay_buffer_capacity": capacity, "broadcasts_before": broadcasts, "buffered_seqs": expected_buffer(capacity, broadcasts)} for state, (capacity, broadcasts) in STATES.items()},
        "frames": frames,
    }
    text = render_table(table)
    if json.loads(text) != table:
        raise SystemExit("the rendered table does not parse back to the table built")
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"table: {len(frames)} frames x {len(STATES)} states written to {args.out}; sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()}")


def compare(args: argparse.Namespace) -> None:
    with open(args.table, encoding="utf-8") as handle:
        table = json.load(handle)
    expected = {(row["id"], state): answer for row in table["frames"] for state, answer in row["answers"].items()}
    summary = []
    for path in args.probe:
        with open(path, encoding="utf-8") as handle:
            probe = json.load(handle)
        differing = []
        problems = []
        for record in probe["cases"]:
            key = (record["frame"], record["state"])
            problems.extend(f"{key}: {problem}" for problem in record["problems"])
            got = {"handshake": record.get("handshake"), "live": record.get("live")}
            if got != expected[key]:
                differing.append((key, expected[key], got))
        families = sorted({frame for (frame, _state), _want, _got in differing})
        summary.append({"probe": str(path), "src": probe["src"], "files": probe["files"], "differing_cases": len(differing), "of": len(probe["cases"]), "differing_frames": len(families), "problems": problems, "cases": [{"frame": key[0], "state": key[1], "table": want, "probe": got} for key, want, got in differing]})
        print(f"{path}: {len(differing)} of {len(probe['cases'])} cases differ from the table ({len(families)} frames); probe problems {len(problems)}")
    if args.out is not None:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=1)
            handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    drive_parser = sub.add_parser("drive")
    drive_parser.add_argument("--kind", choices=("cascor", "svc"), required=True)
    drive_parser.add_argument("--src", type=Path, required=True)
    drive_parser.add_argument("--out", type=Path, required=True)
    drive_parser.add_argument("--log-dir", type=Path, required=True)
    table_parser = sub.add_parser("table")
    table_parser.add_argument("--probe", type=Path, required=True)
    table_parser.add_argument("--out", type=Path, required=True)
    compare_parser = sub.add_parser("compare")
    compare_parser.add_argument("--table", type=Path, required=True)
    compare_parser.add_argument("--out", type=Path, default=None)
    compare_parser.add_argument("probe", type=Path, nargs="+")
    args = parser.parse_args()
    {"drive": drive, "table": build_table, "compare": compare}[args.command](args)


if __name__ == "__main__":
    main()
