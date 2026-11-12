"""
Drive juniper-cascor's /ws/training handler with a resume frame for every class of ``last_seq`` input and record what a
client sees, on origin/main's code and on the N-3 round-2 carrier's code, then diff the two.

Each case is the RAW JSON text of ``last_seq`` (so NaN, Infinity, 1e400, huge integers and bare ``true`` reach the
server's own ``json.loads`` exactly as a client would send them), run against three buffer states:

  fresh      no broadcast made yet (current_seq 0, empty replay buffer)
  buffered5  five broadcasts, all buffered (seqs 1-5)
  evicted    five broadcasts into a 3-slot buffer (seqs 3-5 held)

An already-active observer socket exists in every state, so main's ``broadcast`` (which returned early with no active
socket) numbers the same seqs as the carrier's. For each case it records the reply (``resume_ok`` / ``resume_failed``
and its reason), the seqs and frame types the socket received, whether it was promoted (a live broadcast after the
handshake reaches it), the close, and any exception out of the handler.

Child mode (``--child --tree T``) imports ``api.websocket`` from ``T/src`` and asserts the module file is under T.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses (N3-06)
"""

import argparse
import asyncio
import json
import subprocess
import sys
import types
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
WORKTREES = JUNIPER / "worktrees"
TREES = {
    "main": WORKTREES / "juniper-cascor--val--flood4r2-n3-r2-code-main--20261109-0916--7640d420",
    "carrier": WORKTREES / "juniper-cascor--val--flood4r2-n3-r2-code--20261109-0916--7640d420",
}
OUT = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert" / "tmp" / "flood4r2-val" / "n3-r2-code-lens"
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"

#: Raw JSON text for ``last_seq``; ``None`` means the key is absent.
CASES = [
    None,
    "null",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "-1",
    "-5",
    "100000000000000000000000000000",
    "9223372036854775808",
    "-100000000000000000000000000000",
    "1" + "0" * 4300,
    "true",
    "false",
    "3.0",
    "5.0",
    "2.5",
    "-0.0",
    "1e400",
    "-1e400",
    "NaN",
    "Infinity",
    "-Infinity",
    '"3"',
    '""',
    "[3]",
    "{}",
]

#: Whole-frame variants (the ``data`` object or the server id malformed).
FRAMES = {
    "data-null": '{"type": "resume", "data": null}',
    "data-list": '{"type": "resume", "data": [1]}',
    "data-missing": '{"type": "resume"}',
    "server-id-missing": '{"type": "resume", "data": {"last_seq": 3}}',
    "server-id-wrong": '{"type": "resume", "data": {"last_seq": 3, "server_instance_id": "not-this-server"}}',
    "server-id-int": '{"type": "resume", "data": {"last_seq": 3, "server_instance_id": 7}}',
}

STATES = {"fresh": (64, 0), "buffered5": (64, 5), "evicted": (3, 5)}


class FakeWS:
    def __init__(self, app, first_frame: str) -> None:
        self.client = ("1.2.3.4", 5000)
        self.headers: dict = {}
        self.app = app
        self.sent: list = []
        self.closed = None
        self.listening = asyncio.Event()
        self._incoming = [first_frame]
        self._hung_up = asyncio.Event()

    async def accept(self) -> None:
        return None

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)

    async def receive_text(self) -> str:
        if self._incoming:
            return self._incoming.pop(0)
        self.listening.set()
        await self._hung_up.wait()
        from fastapi import WebSocketDisconnect

        raise WebSocketDisconnect(code=1000)

    def hang_up(self) -> None:
        self._hung_up.set()


class _Observer(FakeWS):
    def __init__(self) -> None:
        super().__init__(None, "")
        self.client = ("9.9.9.9", 1)


class _Lifecycle:
    """Just enough for the fresh-connect path to send initial_status / state / initial_metrics."""

    def __init__(self) -> None:
        self.training_state = types.SimpleNamespace(get_state=lambda: {"status": "running"})

    def get_status(self) -> dict:
        return {"status": "running"}

    def get_metrics_history(self, count: int = 100) -> list:
        return []


async def _one(manager_cls, handler, buffer_size: int, broadcasts: int, frame_text) -> dict:
    mgr = manager_cls(send_timeout_seconds=60.0, max_replay_buffer_size=buffer_size)
    observer = _Observer()
    assert await mgr.connect(observer)
    for i in range(broadcasts):
        await mgr.broadcast({"type": "metrics", "data": {"i": i}})
    settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=60.0, ws_initial_metrics_count=1, ws_heartbeat_interval_sec=0, ws_heartbeat_pong_timeout_sec=60.0)
    app = types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, settings=settings, lifecycle=_Lifecycle()))
    text = frame_text(mgr)
    ws = FakeWS(app, text)
    task = asyncio.create_task(handler(ws))
    for _ in range(20_000):
        if task.done() or ws.listening.is_set():
            break
        await asyncio.sleep(0)
    promoted_before_live = ws in mgr._active_connections
    await mgr.broadcast({"type": "metrics", "data": {"i": "live"}})
    if not task.done():
        ws.hang_up()
    exc = None
    try:
        await asyncio.wait_for(task, timeout=30)
    except Exception as e:  # recorded, not raised: the case's outcome
        exc = f"{type(e).__name__}: {e}"[:200]
    reply = next((m for m in ws.sent if m.get("type") in ("resume_ok", "resume_failed")), None)
    return {
        "reply": None if reply is None else reply["type"] + ("" if reply["type"] == "resume_ok" else ":" + str(reply["data"].get("reason"))),
        "replayed_count": None if reply is None or reply["type"] != "resume_ok" else reply["data"].get("replayed_count"),
        "seqs": [m["seq"] for m in ws.sent if "seq" in m],
        "types": [m.get("type") for m in ws.sent],
        "fresh_snapshot": any(m.get("type") == "initial_status" for m in ws.sent),
        "promoted": promoted_before_live,
        "closed": ws.closed,
        "exception": exc,
        "current_seq_after": mgr.current_seq,
    }


async def child_main(tree: Path) -> dict:
    sys.path.insert(0, str(tree / "src"))
    import api.websocket.manager as manager_mod
    import api.websocket.training_stream as stream_mod

    for mod in (manager_mod, stream_mod):
        if not str(Path(mod.__file__).resolve()).startswith(str(tree.resolve())):
            raise SystemExit(f"{mod.__name__} imported from {mod.__file__}, not from {tree}")
    results = {"tree": str(tree), "module_files": [manager_mod.__file__, stream_mod.__file__], "cases": {}}
    for state, (size, n) in STATES.items():
        for raw in CASES:
            if raw is None:
                def make(mgr):
                    return json.dumps({"type": "resume", "data": {"server_instance_id": mgr.server_instance_id}})
                key = "<missing>"
            else:
                def make(mgr, raw=raw):
                    return '{"type": "resume", "data": {"last_seq": ' + raw + ', "server_instance_id": ' + json.dumps(mgr.server_instance_id) + "}}"
                key = raw if len(raw) < 40 else f"<int of {len(raw)} digits>"
            results["cases"][f"{state}|{key}"] = await _one(manager_mod.WebSocketManager, stream_mod.training_stream_handler, size, n, make)
        for name, text in FRAMES.items():
            results["cases"][f"{state}|frame:{name}"] = await _one(manager_mod.WebSocketManager, stream_mod.training_stream_handler, size, n, lambda mgr, text=text: text)
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--tree")
    args = ap.parse_args()
    if args.child:
        print(json.dumps(asyncio.run(child_main(Path(args.tree)))))
        return 0
    runs = {}
    for label, tree in TREES.items():
        proc = subprocess.run([PYTHON, "-I", __file__, "--child", "--tree", str(tree)], capture_output=True, text=True, cwd=str(tree))
        if proc.returncode != 0:
            print(proc.stderr[-4000:])
            raise SystemExit(f"child for {label} failed: {proc.returncode}")
        runs[label] = json.loads(proc.stdout.strip().splitlines()[-1])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "last_seq_classes.json").write_text(json.dumps(runs, indent=1) + "\n", encoding="utf-8")
    keys = list(runs["main"]["cases"])
    print(f"{'case':44} | {'main':52} | carrier")
    for key in keys:
        m, c = runs["main"]["cases"][key], runs["carrier"]["cases"][key]

        def brief(r):
            return f"{r['reply']} n={r['replayed_count']} seqs={r['seqs']} fresh={int(r['fresh_snapshot'])} prom={int(r['promoted'])} close={r['closed']} exc={r['exception']}"

        mark = "  " if brief(m) == brief(c) else "**"
        print(f"{mark}{key:42} | {brief(m)[:52]:52} | {brief(c)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
