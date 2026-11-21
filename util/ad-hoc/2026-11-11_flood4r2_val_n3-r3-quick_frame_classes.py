"""
Drive the real /ws/training handler with the two inputs N-3 round 3 newly answers (a negative ``last_seq``; a resume
frame whose ``data`` is not an object) and record what a client sees on four code bases.

Adapted from ``2026-11-09_flood4r2_val_n3-r2-code_last_seq_classes.py`` (the round-2 code lens's helper, left
untouched). The four targets:

  main   juniper-cascor origin/main 9f632eac, pristine
  r2     the same commit with round 2's three source files (sha256 = round 2's manifest)
  r3     the same commit with the round-3 carrier's 11 files
  svc    juniper-service-core as it stands on juniper-ml's origin/main (extracted from the commit with ``git archive``;
         its own ``WebSocketManager`` and ``training_stream_handler``), the shared copy of the same protocol

Each case is the RAW JSON text a client would send, so ``-0``, ``NaN`` and bare ``null`` reach the server's own
``json.loads``. Four buffer states: nothing broadcast yet; seqs 1-5 buffered; a 3-slot buffer holding 3-5; replay
disabled. An already-active observer exists in every state, so main's ``broadcast`` numbers the same seqs. For each
case the record holds the resume reply and its reason, the seqs and frame types received, whether a fresh snapshot
followed, whether the socket was live for a broadcast made after the handshake, the close, any exception out of the
handler and (cascor only) the outcomes counted.

Child mode (``--child``) imports from one tree with ``-I -B`` and asserts the modules came from that tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses (N-3 round 3, code findings F4 and F5)
"""

import argparse
import asyncio
import json
import subprocess
import sys
import tarfile
import types
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
WORKTREES = JUNIPER / "worktrees"
ML_WORKTREE = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert"
OUT = ML_WORKTREE / "tmp" / "flood4r2-val" / "n3-r3-quick-s5"
ML_MAIN_SHA = "348777f4641da5abe54cfe15e6c2a4596a4f3d64"
SVC_ROOT = OUT / "svc-core-main"
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"

TARGETS = {
    "main": ("cascor", WORKTREES / "juniper-cascor--val--n3-r3-quick-main--20261111-1958--9f632eac" / "src"),
    "r2": ("cascor", WORKTREES / "juniper-cascor--val--n3-r3-quick-r2src--20261111-1958--9f632eac" / "src"),
    "r3": ("cascor", WORKTREES / "juniper-cascor--val--n3-r3-quick--20261111-1958--9f632eac" / "src"),
    "svc": ("service-core", SVC_ROOT / "juniper-service-core"),
}

#: Raw JSON text for ``last_seq``; ``None`` means the key is absent.
CASES = [None, "null", "0", "1", "3", "5", "6", "-1", "-5", "-100000000000000000000000000000", "-0", "-0.0", "-1.0", "true", "2.5", "NaN", '"3"', "[3]"]

#: Whole frames. ``@ID@`` is replaced by the server's own instance id.
FRAMES = {
    "data-missing": '{"type": "resume"}',
    "data-null": '{"type": "resume", "data": null}',
    "data-list": '{"type": "resume", "data": [1]}',
    "data-empty-list": '{"type": "resume", "data": []}',
    "data-string": '{"type": "resume", "data": "3"}',
    "data-number": '{"type": "resume", "data": 3}',
    "data-true": '{"type": "resume", "data": true}',
    "data-empty-object": '{"type": "resume", "data": {}}',
    "data-list-holding-a-cursor": '{"type": "resume", "data": [{"last_seq": 3, "server_instance_id": @ID@}]}',
    "frame-is-a-list": '[{"type": "resume", "data": {"last_seq": 3, "server_instance_id": @ID@}}]',
    "server-id-missing": '{"type": "resume", "data": {"last_seq": 3}}',
    "valid-control": '{"type": "resume", "data": {"last_seq": 3, "server_instance_id": @ID@}}',
}

STATES = {"fresh": (64, 0), "buffered5": (64, 5), "evicted": (3, 5), "disabled": (0, 5)}


class FakeWS:
    def __init__(self, app, first_frame: str, client: tuple = ("1.2.3.4", 5000)) -> None:
        self.client = client
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


class _Lifecycle:
    """Just enough for either fresh-connect path to send initial_status / state / initial_metrics."""

    def __init__(self) -> None:
        self.training_state = types.SimpleNamespace(get_state=lambda: {"status": "running"})
        self.monitor = types.SimpleNamespace(get_state=lambda: {"status": "running"})

    def get_status(self) -> dict:
        return {"status": "running"}

    def get_metrics_history(self, count: int = 100) -> list:
        return []


async def _one(manager_cls, handler, flavour: str, outcomes: list, buffer_size: int, broadcasts: int, frame_text) -> dict:
    mgr = manager_cls(send_timeout_seconds=60.0, max_replay_buffer_size=buffer_size)
    observer = FakeWS(None, "", client=("9.9.9.9", 1))
    assert await mgr.connect(observer)
    for i in range(broadcasts):
        await mgr.broadcast({"type": "metrics", "data": {"i": i}})
    # cascor reads an interval of 0 as "no heartbeat"; service-core always runs one, so give it an hour.
    heartbeat = 0 if flavour == "cascor" else 3600
    settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=60.0, ws_initial_metrics_count=1, ws_heartbeat_interval_sec=heartbeat, ws_heartbeat_pong_timeout_sec=60.0)
    app = types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, settings=settings, lifecycle=_Lifecycle()))
    ws = FakeWS(app, frame_text(mgr))
    del outcomes[:]
    task = asyncio.create_task(handler(ws))
    for _ in range(20_000):
        if task.done() or ws.listening.is_set():
            break
        await asyncio.sleep(0)
    live_before = ws in mgr._active_connections
    await mgr.broadcast({"type": "metrics", "data": {"i": "live"}})
    if not task.done():
        ws.hang_up()
    exc = None
    try:
        await asyncio.wait_for(task, timeout=30)
    except Exception as e:  # recorded, not raised: it is the case's outcome
        exc = f"{type(e).__name__}: {e}"[:200]
    reply = next((m for m in ws.sent if m.get("type") in ("resume_ok", "resume_failed")), None)
    return {
        "reply": None if reply is None else reply["type"] + ("" if reply["type"] == "resume_ok" else ":" + str(reply["data"].get("reason"))),
        "replayed_count": None if reply is None or reply["type"] != "resume_ok" else reply["data"].get("replayed_count"),
        "seqs": [m["seq"] for m in ws.sent if "seq" in m],
        "types": [m.get("type") for m in ws.sent],
        "fresh_snapshot": any(m.get("type") == "initial_status" for m in ws.sent),
        "live": live_before,
        "closed": ws.closed,
        "exception": exc,
        "outcomes": list(outcomes),
        "current_seq_after": mgr.current_seq,
    }


async def child_main(flavour: str, root: Path) -> dict:
    sys.path.insert(0, str(root))
    outcomes: list = []
    if flavour == "cascor":
        import api.observability as observability_mod
        import api.websocket.manager as manager_mod
        import api.websocket.training_stream as stream_mod

        observability_mod.ws_inc_resume_requests = outcomes.append
    else:
        import juniper_service_core.websocket.manager as manager_mod
        import juniper_service_core.websocket.training_stream as stream_mod
    for mod in (manager_mod, stream_mod):
        if not str(Path(mod.__file__).resolve()).startswith(str(root.resolve())):
            raise SystemExit(f"{mod.__name__} imported from {mod.__file__}, not from {root}")
    results = {"root": str(root), "flavour": flavour, "module_files": [manager_mod.__file__, stream_mod.__file__], "cases": {}}
    for state, (size, n) in STATES.items():
        for raw in CASES:
            if raw is None:
                def make(mgr):
                    return json.dumps({"type": "resume", "data": {"server_instance_id": mgr.server_instance_id}})
                key = "<missing>"
            else:
                def make(mgr, raw=raw):
                    return '{"type": "resume", "data": {"last_seq": ' + raw + ', "server_instance_id": ' + json.dumps(mgr.server_instance_id) + "}}"
                key = raw
            results["cases"][f"{state}|{key}"] = await _one(manager_mod.WebSocketManager, stream_mod.training_stream_handler, flavour, outcomes, size, n, make)
        for name, text in FRAMES.items():
            def make_frame(mgr, text=text):
                return text.replace("@ID@", json.dumps(mgr.server_instance_id))
            results["cases"][f"{state}|frame:{name}"] = await _one(manager_mod.WebSocketManager, stream_mod.training_stream_handler, flavour, outcomes, size, n, make_frame)
    return results


def brief(r: dict) -> str:
    return f"{r['reply']} n={r['replayed_count']} seqs={r['seqs']} fresh={int(r['fresh_snapshot'])} live={int(r['live'])} close={r['closed']} exc={r['exception']} counted={r['outcomes']}"


def wire(r: dict) -> tuple:
    """What the client can observe (the outcome counter is server-side, so it is left out)."""
    return (r["reply"], r["replayed_count"], tuple(r["seqs"]), tuple(r["types"]), r["closed"], r["exception"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--flavour")
    ap.add_argument("--root")
    args = ap.parse_args()
    if args.child:
        print(json.dumps(asyncio.run(child_main(args.flavour, Path(args.root)))))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    if not SVC_ROOT.exists():
        tar_path = OUT / "svc-core-main.tar"
        subprocess.run(["git", "-C", str(ML_WORKTREE), "archive", "--format=tar", "-o", str(tar_path), ML_MAIN_SHA, "juniper-service-core/juniper_service_core"], check=True)
        with tarfile.open(tar_path) as tar:
            tar.extractall(path=SVC_ROOT, filter="data")
    runs = {}
    for label, (flavour, root) in TARGETS.items():
        proc = subprocess.run([PYTHON, "-I", "-B", __file__, "--child", "--flavour", flavour, "--root", str(root)], capture_output=True, text=True, cwd=str(OUT))
        if proc.returncode != 0:
            print(proc.stderr[-4000:])
            raise SystemExit(f"child for {label} failed: {proc.returncode}")
        runs[label] = json.loads(proc.stdout.strip().splitlines()[-1])
    (OUT / "frame_classes.json").write_text(json.dumps(runs, indent=1) + "\n", encoding="utf-8")
    lines = []
    for key in runs["main"]["cases"]:
        recs = {label: runs[label]["cases"][key] for label in TARGETS}
        marks = "".join(
            [
                "M" if wire(recs["r3"]) != wire(recs["main"]) else ".",
                "2" if wire(recs["r3"]) != wire(recs["r2"]) else ".",
                "S" if wire(recs["r3"]) != wire(recs["svc"]) else ".",
            ]
        )
        lines.append(f"[{marks}] {key}")
        for label in TARGETS:
            lines.append(f"        {label:4} {brief(recs[label])}")
    lines.append("")
    lines.append("Marks: M = r3 differs from main on the wire; 2 = r3 differs from r2; S = r3 differs from service-core's main.")
    lines.append("")
    lines.append("Is a negative cursor answered exactly as 0 is (same reply, count, seqs, frame types, close)?")
    for label in TARGETS:
        for state in STATES:
            zero = runs[label]["cases"][f"{state}|0"]
            verdicts = []
            for raw in ("-1", "-5", "-100000000000000000000000000000", "-0"):
                verdicts.append(f"{raw[:6]}:{'same' if wire(runs[label]['cases'][f'{state}|{raw}']) == wire(zero) else 'DIFFERS'}")
            lines.append(f"  {label:4} {state:10} {'  '.join(verdicts)}")
    text = "\n".join(lines) + "\n"
    (OUT / "frame_classes.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
