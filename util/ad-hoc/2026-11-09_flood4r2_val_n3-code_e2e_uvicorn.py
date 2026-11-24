"""
End-to-end probe of the /ws/training resume path over a REAL transport: an in-process uvicorn server (ephemeral
127.0.0.1 port, torn down at exit), real `websockets` clients, and a real training thread calling
broadcast_from_thread. No fakes. Run against origin/main's src and the fix's src.

  e2e1  defect 1: broadcasts while nobody is connected, then a resume from the last seq held
  e2e2  defect 2: an observer keeps broadcasts numbered; the resuming client delays reading so the replay
        meets real TCP back-pressure while the training thread keeps broadcasting

Every broadcast carries the thread's counter `n`, so a loss is visible even when it took no seq.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-cascor fix/ws-resume-losses
"""

import argparse
import asyncio
import json
import logging
import sys
import threading
import time
import types


def build(src: str):
    sys.path.insert(0, src)
    from fastapi import FastAPI  # noqa: E402

    from api.websocket.manager import WebSocketManager  # noqa: E402
    from api.websocket.training_stream import training_stream_handler  # noqa: E402

    return FastAPI, WebSocketManager, training_stream_handler


class Trainer(threading.Thread):
    def __init__(self, mgr, period_s: float, pad: int):
        super().__init__(daemon=True)
        self.mgr, self.period_s, self.pad = mgr, period_s, pad
        self.n = 0
        self.stop_evt = threading.Event()

    def run(self) -> None:
        while not self.stop_evt.is_set():
            self.n += 1
            self.mgr.broadcast_from_thread({"type": "metrics", "data": {"n": self.n, "pad": "x" * self.pad}})
            time.sleep(self.period_s)


async def _read_for(ws, seconds: float, sink: list) -> None:
    end = time.monotonic() + seconds
    while True:
        left = end - time.monotonic()
        if left <= 0:
            return
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=left)
        except asyncio.TimeoutError:
            return
        sink.append(json.loads(raw))


def _ns(frames: list) -> list:
    return [f["data"]["n"] for f in frames if f.get("type") == "metrics"]


def _seqs(frames: list) -> list:
    return [f["seq"] for f in frames if "seq" in f]


def _cap_server_sndbuf(nbytes: int) -> None:
    """Instrumentation only: give every server-side websocket a small kernel send buffer.

    On loopback the kernel autotunes the send buffer to MBs (and a 12 MB replay to a non-reading client was
    measured never to block: zero pause_writing calls), so a replay never meets back-pressure locally. A slow
    WAN consumer fills normal buffers; this compresses that. The code under test is not touched.
    """
    import socket

    import websockets.legacy.protocol as wlp

    orig = wlp.WebSocketCommonProtocol.connection_made

    def connection_made(self, transport):  # type: ignore[no-untyped-def]
        sock = transport.get_extra_info("socket")
        if sock is not None:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, nbytes)
        return orig(self, transport)

    wlp.WebSocketCommonProtocol.connection_made = connection_made


async def _small_rcvbuf_socket(port: int, rcvbuf: int):
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
    sock.setblocking(False)
    await asyncio.get_running_loop().sock_connect(sock, ("127.0.0.1", port))
    return sock


async def scenario(src: str, which: str, pad: int = 12000, period: float = 0.0015, accum: float = 1.0, pause: float = 0.5) -> dict:
    import uvicorn
    from websockets.asyncio.client import connect

    FastAPI, WebSocketManager, handler = build(src)
    logging.disable(logging.CRITICAL)
    app = FastAPI()
    mgr = WebSocketManager(send_timeout_seconds=5.0)
    mgr.set_event_loop(asyncio.get_running_loop())
    app.state.ws_manager = mgr
    app.state.lifecycle = None
    app.state.settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=0.3, ws_initial_metrics_count=0, ws_heartbeat_interval_sec=0, ws_heartbeat_pong_timeout_sec=10)
    app.add_api_websocket_route("/ws/training", handler)
    import socket

    # Accepted sockets inherit SO_SNDBUF from the listener: a small kernel send buffer, so a multi-MB replay
    # to a client that is not reading really blocks the server's send (the kernel's 4 MB autotuned buffer
    # otherwise absorbs it and the replay never yields).
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32768)
    lsock.bind(("127.0.0.1", 0))
    port = lsock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, ws="websockets", lifespan="off", log_level="critical"))
    serve = asyncio.create_task(server.serve(sockets=[lsock]))
    while not server.started:
        await asyncio.sleep(0.01)
    uri = f"ws://127.0.0.1:{port}/ws/training"
    out: dict = {"which": which}
    trainer = None
    try:
        if which == "e2e1":
            trainer = Trainer(mgr, period_s=0.002, pad=100)
            trainer.start()
            a_frames: list = []
            async with connect(uri) as a:
                await _read_for(a, 0.8, a_frames)  # fresh connect (no resume frame), then live
            a_seq, a_n = _seqs(a_frames)[-1], _ns(a_frames)[-1]
            await asyncio.sleep(0.5)  # nobody connected; the thread keeps broadcasting
            b_frames: list = []
            async with connect(uri) as b:
                await b.recv()  # connection_established
                await b.send(json.dumps({"type": "resume", "data": {"last_seq": a_seq, "server_instance_id": mgr.server_instance_id}}))
                await _read_for(b, 0.8, b_frames)
            trainer.stop_evt.set()
            ns = _ns(b_frames)
            expected = list(range(a_n + 1, ns[-1] + 1)) if ns else []
            out.update(
                {
                    "a_last_seq": a_seq,
                    "a_last_n": a_n,
                    "b_first_frame": {k: b_frames[0].get(k) for k in ("type", "data")} if b_frames else None,
                    "b_n_count": len(ns),
                    "b_missing_n": len(sorted(set(expected) - set(ns))),
                    "b_missing_n_first": sorted(set(expected) - set(ns))[:5],
                    "b_seq_gaps": sum(1 for x, y in zip(_seqs(b_frames), _seqs(b_frames)[1:]) if y != x + 1),
                    "b_dups": len(_seqs(b_frames)) - len(set(_seqs(b_frames))),
                }
            )
        else:
            o_frames: list = []
            async with connect(uri, max_size=None) as o:
                obs_task = asyncio.create_task(_read_for(o, accum + pause + 5.0, o_frames))
                await asyncio.sleep(0.5)  # O promoted (fresh) and reading
                trainer = Trainer(mgr, period_s=period, pad=pad)
                trainer.start()
                a_frames = []
                async with connect(uri) as a:
                    await _read_for(a, 0.6, a_frames)
                a_seq = _seqs(a_frames)[-1]
                await asyncio.sleep(accum)  # a multi-MB replay backlog, inside the 1024-slot buffer
                out["backlog_at_resume"] = mgr.current_seq - a_seq
                b_frames = []
                pending_samples = []
                sock = await _small_rcvbuf_socket(port, 32768)
                async with connect(uri, sock=sock, max_queue=2, max_size=None) as b:
                    await b.recv()
                    await b.send(json.dumps({"type": "resume", "data": {"last_seq": a_seq, "server_instance_id": mgr.server_instance_id}}))
                    steps = max(1, int(pause / 0.01))
                    for _ in range(steps):  # do not read: the replay meets TCP back-pressure
                        await asyncio.sleep(0.01)
                        pending_samples.append(len(mgr._pending_connections))
                    await _read_for(b, 3.0, b_frames)
                    close_code = b.close_code
                trainer.stop_evt.set()
                await obs_task
            seqs = _seqs(b_frames)
            resume_ok = next((f for f in b_frames if f.get("type") == "resume_ok"), None)
            expected = list(range(a_seq + 1, seqs[-1] + 1)) if seqs else []
            missing = sorted(set(expected) - set(seqs))
            out.update(
                {
                    "a_last_seq": a_seq,
                    "resume_ok": resume_ok is not None,
                    "replayed_count": (resume_ok or {}).get("data", {}).get("replayed_count"),
                    "b_seq_count": len(seqs),
                    "b_missing_seq_count": len(missing),
                    "b_missing_seq_first": missing[:8],
                    "b_dups": len(seqs) - len(set(seqs)),
                    "b_out_of_order": any(y <= x for x, y in zip(seqs, seqs[1:])),
                    "b_close_code_while_reading": close_code,
                    "pending_while_not_reading": max(pending_samples) if pending_samples else None,
                    "observer_seq_gaps": sum(1 for x, y in zip(_seqs(o_frames), _seqs(o_frames)[1:]) if y != x + 1),
                    "broadcasts_total": mgr.current_seq,
                }
            )
    finally:
        if trainer is not None:
            trainer.stop_evt.set()
        await mgr.close_all()
        server.should_exit = True
        await asyncio.wait_for(serve, timeout=10)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--which", nargs="+", default=["e2e1", "e2e2"])
    ap.add_argument("--pad", type=int, default=12000)
    ap.add_argument("--period", type=float, default=0.0015)
    ap.add_argument("--accum", type=float, default=1.0)
    ap.add_argument("--pause", type=float, default=0.5)
    ap.add_argument("--out")
    a = ap.parse_args()
    _cap_server_sndbuf(32768)
    results = {"label": a.label, "params": {"pad": a.pad, "period": a.period, "accum": a.accum, "pause": a.pause, "server_sndbuf": 32768}}
    for w in a.which:
        results[w] = asyncio.run(scenario(a.src, w, pad=a.pad, period=a.period, accum=a.accum, pause=a.pause))
        print(a.label, json.dumps(results[w]), flush=True)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
