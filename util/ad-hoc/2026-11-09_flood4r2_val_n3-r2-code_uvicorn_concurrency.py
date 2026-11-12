"""
Concurrency probe of juniper-cascor's /ws/training resume path over a REAL transport: an in-process uvicorn server
(ephemeral 127.0.0.1 port, ws="auto" as production runs it, torn down when the scenario ends), real `websockets`
clients, and a real training thread calling broadcast_from_thread. No fakes.

K clients run concurrently; each repeatedly connects, reads for a while, disconnects, waits, and reconnects with a
resume from the last seq it held. Odd-numbered clients connect through a socket with a small receive buffer and do
not read for a pause after sending the resume, so the server's replay meets TCP back-pressure while the thread keeps
broadcasting. For every resumed session it checks the stream after ``resume_ok``: it must be exactly
last_seq+1, last_seq+2, ... with no gap, duplicate or reordering until the session ends. ``resume_failed`` and a 1011
close are counted (the carrier's contract allows both). A final ``--n3-06`` pass sends each non-integer / out-of-range
``last_seq`` over the real socket and records the reply.

Run once per tree:  python 2026-11-09_flood4r2_val_n3-r2-code_uvicorn_concurrency.py --src <tree>/src --label L --out F

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses;
         util/ad-hoc/2026-11-09_flood4r2_val_n3-code_e2e_uvicorn.py (round 1's probe, whose server setup this follows)
"""

import argparse
import asyncio
import json
import logging
import random
import socket
import sys
import threading
import time
import types
from collections import Counter


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


async def _small_rcvbuf_socket(port: int, rcvbuf: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
    sock.setblocking(False)
    await asyncio.get_running_loop().sock_connect(sock, ("127.0.0.1", port))
    return sock


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
        except Exception:  # the server closed the connection; the close code is read by the caller
            return
        sink.append(json.loads(raw))


def _check_session(last_seq, frames: list) -> dict:
    """Classify one resumed session and, after resume_ok, measure gaps / dups / reordering."""
    reply = next((f for f in frames if f.get("type") in ("resume_ok", "resume_failed")), None)
    out = {"reply": None if reply is None else (reply["type"] if reply["type"] == "resume_ok" else "resume_failed:" + str(reply["data"].get("reason")))}
    if reply is not None and reply["type"] == "resume_ok":
        idx = frames.index(reply)
        seqs = [f["seq"] for f in frames[idx + 1:] if "seq" in f]
        expected = list(range(last_seq + 1, last_seq + 1 + len(seqs)))
        out["seqs"] = len(seqs)
        out["missing"] = len(sorted(set(range(last_seq + 1, (max(seqs) if seqs else last_seq) + 1)) - set(seqs)))
        out["dups"] = len(seqs) - len(set(seqs))
        out["out_of_order"] = sum(1 for x, y in zip(seqs, seqs[1:]) if y <= x)
        out["exact"] = seqs == expected
        out["replayed_count"] = reply["data"].get("replayed_count")
        out["frames_before_reply"] = [(f.get("type"), f.get("seq")) for f in frames[:idx]][:6]
        prev = last_seq
        gaps = []
        for pos, s in enumerate(seqs):
            if s != prev + 1:
                gaps.append({"index": pos, "expected": prev + 1, "got": s})
            prev = s
        out["gaps"] = gaps[:5]
    return out


async def scenario(src: str, clients: int, cycles: int, period: float, pad: int, buffer: int, seed: int, n306: bool, log_path: str = "", tracing: bool = False, grace: float = 0.0) -> dict:
    sys.path.insert(0, src)
    import uvicorn
    from fastapi import FastAPI
    from websockets.asyncio.client import connect

    import api.websocket.manager as manager_mod
    import api.websocket.training_stream as stream_mod

    if not manager_mod.__file__.startswith(src) or not stream_mod.__file__.startswith(src):
        raise SystemExit(f"api.websocket imported from {manager_mod.__file__}, not {src}")
    if log_path:
        handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
        root = logging.getLogger()
        root.addHandler(handler)
        root.setLevel(logging.INFO)
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("websockets").setLevel(logging.WARNING)
    else:
        logging.disable(logging.CRITICAL)
    rng = random.Random(seed)
    app = FastAPI()
    mgr = manager_mod.WebSocketManager(
        send_timeout_seconds=5.0,
        max_replay_buffer_size=buffer,
        max_connections=200,
        max_connections_per_ip=200,
        max_connections_global=400,
        max_connections_per_identity=200,
    )
    mgr.set_event_loop(asyncio.get_running_loop())
    trace: dict = {}
    numbered_while_inactive: dict = {}
    wire_sends: dict = {}
    session_end: dict = {}
    if tracing:
        # Instance-level wrappers only (the code under test is not edited): per server-side socket, keyed by the
        # client's port, record each personal send, each catch-up and each activation, with the newest seq at the time.
        orig_send = mgr.send_personal_message
        orig_activate = getattr(mgr, "_activate", None)  # absent on origin/main
        orig_catch_up = getattr(mgr, "_catch_up_and_activate", None)  # absent on origin/main
        orig_assign = mgr._assign_seq_and_buffer

        def port_of(websocket) -> int:
            return getattr(websocket, "client", (None, -1))[1]

        async def send_traced(websocket, message):
            ok = await orig_send(websocket, message)
            trace.setdefault(port_of(websocket), []).append(("send", message.get("type"), message.get("seq"), ok, mgr.current_seq))
            return ok

        def activate_traced(websocket):
            trace.setdefault(port_of(websocket), []).append(("activate", None, None, True, mgr.current_seq))
            return orig_activate(websocket)

        async def catch_up_traced(websocket, replayed_through):
            trace.setdefault(port_of(websocket), []).append(("catch_up_start", None, replayed_through, None, mgr.current_seq))
            res = await orig_catch_up(websocket, replayed_through)
            trace.setdefault(port_of(websocket), []).append(("catch_up_end", None, replayed_through, res, mgr.current_seq))
            return res

        def assign_traced(message):
            enriched = orig_assign(message)
            pending = {port_of(w) for w in mgr._pending_connections}
            for p in pending:
                numbered_while_inactive.setdefault(p, []).append(enriched["seq"])
            return enriched

        orig_send_json = mgr._send_json

        async def send_json_traced(websocket, message):
            ok = await orig_send_json(websocket, message)
            if message.get("seq") is not None:
                wire_sends.setdefault(port_of(websocket), {})[message["seq"]] = (ok, time.monotonic())
            return ok

        mgr._send_json = send_json_traced
        mgr.send_personal_message = send_traced
        if orig_catch_up is not None:
            mgr._activate = activate_traced
            mgr._catch_up_and_activate = catch_up_traced
        mgr._assign_seq_and_buffer = assign_traced
    app.state.ws_manager = mgr
    app.state.lifecycle = None
    app.state.settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=0.5, ws_initial_metrics_count=0, ws_heartbeat_interval_sec=0, ws_heartbeat_pong_timeout_sec=10)
    app.add_api_websocket_route("/ws/training", stream_mod.training_stream_handler)
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32768)
    lsock.bind(("127.0.0.1", 0))
    port = lsock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, ws="auto", lifespan="off", log_level="critical"))
    serve = asyncio.create_task(server.serve(sockets=[lsock]))
    while not server.started:
        await asyncio.sleep(0.01)
    uri = f"ws://127.0.0.1:{port}/ws/training"
    trainer = Trainer(mgr, period_s=period, pad=pad)
    trainer.start()
    sessions: list = []
    pending_peak = {"n": 0}

    async def sample_pending() -> None:
        while True:
            pending_peak["n"] = max(pending_peak["n"], len(mgr._pending_connections))
            await asyncio.sleep(0.002)

    async def client(i: int) -> None:
        last_seq = None
        for c in range(cycles):
            frames: list = []
            late_frames: list = []
            slow = i % 2 == 1
            kwargs = {"max_size": None}
            if slow:
                kwargs.update(sock=await _small_rcvbuf_socket(port, 16384), max_queue=2)
            close_code = None
            local_port = None
            try:
                async with connect(uri, **kwargs) as ws:
                    local_port = ws.local_address[1]
                    await ws.recv()  # connection_established
                    if last_seq is not None:
                        await ws.send(json.dumps({"type": "resume", "data": {"last_seq": last_seq, "server_instance_id": mgr.server_instance_id}}))
                        if slow:
                            await asyncio.sleep(rng.uniform(0.1, 0.4))  # not reading: the replay meets back-pressure
                    await _read_for(ws, rng.uniform(0.3, 0.8), frames)
                    if grace > 0:
                        # Keep reading past the server's 5 s send timeout: a frame a concurrent broadcast task
                        # delivers late is then seen (as reordering), and only a frame never sent stays missing.
                        await _read_for(ws, grace, late_frames)
                    close_code = ws.close_code
                    session_end[local_port] = time.monotonic()
            except Exception as exc:  # recorded: a connection the server refused or reset
                close_code = f"{type(exc).__name__}"
            if last_seq is not None:
                rec = _check_session(last_seq, frames)
                if grace > 0 and rec.get("gaps"):
                    window_seqs = [f["seq"] for f in frames if "seq" in f]
                    late_seqs = {f["seq"] for f in late_frames if "seq" in f}
                    hole = set(range(last_seq + 1, max(window_seqs) + 1)) - set(window_seqs)
                    rec["missing_after_grace"] = len(hole - late_seqs)
                    rec["delivered_late"] = len(hole & late_seqs)
                rec.update({"client": i, "cycle": c, "slow": slow, "close": close_code, "last_seq": last_seq, "port": local_port})
                if tracing and rec.get("gaps"):
                    window_seqs = {f["seq"] for f in frames if "seq" in f}
                    hole = sorted(set(range(last_seq + 1, max(window_seqs) + 1)) - window_seqs)
                    sent = wire_sends.get(local_port, {})
                    end = session_end.get(local_port, 0.0)
                    rec["_hole"] = hole
                    rec["hole_server_view"] = {
                        "hole": len(hole),
                        "never_sent_to_this_socket": sum(1 for s in hole if s not in sent),
                        "sent_ok_before_client_stopped_reading": sum(1 for s in hole if s in sent and sent[s][0] and sent[s][1] <= end),
                        "sent_ok_after_client_stopped_reading": sum(1 for s in hole if s in sent and sent[s][0] and sent[s][1] > end),
                        "send_failed": sum(1 for s in hole if s in sent and not sent[s][0]),
                    }
                    events = trace.get(local_port, [])
                    sends = [e for e in events if e[0] == "send"]
                    rec["server_trace"] = {
                        "non_send_events": [e for e in events if e[0] != "send"],
                        "personal_sends": len(sends),
                        "personal_send_seq_range": [min((e[2] for e in sends if e[2] is not None), default=None), max((e[2] for e in sends if e[2] is not None), default=None)],
                        "failed_sends": [e for e in sends if not e[3]][:5],
                        "first_sends": sends[:3],
                        "last_sends": sends[-3:],
                        "numbered_while_pending_range": [min(numbered_while_inactive.get(local_port, [0])), max(numbered_while_inactive.get(local_port, [0]))],
                        "numbered_while_pending_count": len(numbered_while_inactive.get(local_port, [])),
                    }
                sessions.append(rec)
            seqs = [f["seq"] for f in frames + late_frames if "seq" in f]
            if seqs:
                last_seq = seqs[-1]  # the last seq received, as canopy's client tracks it
            await asyncio.sleep(rng.uniform(0.02, 0.3))

    sampler = asyncio.create_task(sample_pending())
    out: dict = {}
    try:
        await asyncio.gather(*(client(i) for i in range(clients)))
        if tracing:
            # Post-hoc server view of each hole: stop the producer, let every in-flight broadcast task finish (each
            # send is bounded by the 5 s send timeout), then ask whether each missing seq was ever sent to that socket.
            trainer.stop_evt.set()
            await asyncio.sleep(12.0)
            for rec in sessions:
                if rec.get("gaps") and rec.get("reply") == "resume_ok":
                    sent = wire_sends.get(rec["port"], {})
                    end = session_end.get(rec["port"], 0.0)
                    hole = rec.pop("_hole", [])
                    rec["hole_server_view_final"] = {
                        "hole": len(hole),
                        "never_sent_to_this_socket": sum(1 for s in hole if s not in sent),
                        "sent_ok_after_client_stopped_reading": sum(1 for s in hole if s in sent and sent[s][0] and sent[s][1] > end),
                        "sent_ok_before_client_stopped_reading": sum(1 for s in hole if s in sent and sent[s][0] and sent[s][1] <= end),
                        "send_failed": sum(1 for s in hole if s in sent and not sent[s][0]),
                        "max_delay_after_stop_s": round(max((sent[s][1] - end for s in hole if s in sent), default=0.0), 3),
                    }
        if n306:
            replies = {}
            for raw in ["NaN", "Infinity", "-Infinity", "2.0", "true", '"5"', "-1", "0", str(mgr.current_seq), str(mgr.current_seq + 1), "1" + "0" * 30]:
                frames = []
                async with connect(uri, max_size=None) as ws:
                    await ws.recv()
                    await ws.send('{"type": "resume", "data": {"last_seq": ' + raw + ', "server_instance_id": ' + json.dumps(mgr.server_instance_id) + "}}")
                    await _read_for(ws, 0.3, frames)
                rep = next((f for f in frames if f.get("type") in ("resume_ok", "resume_failed")), None)
                key = raw if len(raw) < 20 else f"<{len(raw)}-digit int>"
                replies[key] = None if rep is None else (rep["type"] + ":" + str(rep["data"].get("reason", rep["data"].get("replayed_count"))))
            out["n3_06_replies"] = replies
    finally:
        sampler.cancel()
        trainer.stop_evt.set()
        await mgr.close_all()
        server.should_exit = True
        await asyncio.wait_for(serve, timeout=10)
    ok = [s for s in sessions if s["reply"] == "resume_ok"]
    out.update(
        {
            "sessions_resumed": len(sessions),
            "replies": dict(sorted(Counter(str(s["reply"]) for s in sessions).items())),
            "close_codes": sorted({str(s["close"]) for s in sessions}),
            "closes_1011": sum(1 for s in sessions if s["close"] == 1011),
            "resume_ok_sessions": len(ok),
            "resume_ok_with_loss": sum(1 for s in ok if s["missing"]),
            "missing_total": sum(s["missing"] for s in ok),
            "dups_total": sum(s["dups"] for s in ok),
            "out_of_order_total": sum(s["out_of_order"] for s in ok),
            "inexact_sessions": sum(1 for s in ok if not s["exact"]),
            "slow_resume_ok": sum(1 for s in ok if s["slow"]),
            "seqs_after_resume_ok": sum(s["seqs"] for s in ok),
            "pending_peak": pending_peak["n"],
            "broadcasts_total": mgr.current_seq,
            "worst": sorted(ok, key=lambda s: -s["missing"])[:3],
            "lossy": [s for s in ok if not s["exact"]],
        }
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--clients", type=int, default=8)
    ap.add_argument("--cycles", type=int, default=6)
    ap.add_argument("--period", type=float, default=0.0008)
    ap.add_argument("--pad", type=int, default=4000)
    ap.add_argument("--buffer", type=int, default=1024)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--n3-06", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--log", default="")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--grace", type=float, default=0.0)
    a = ap.parse_args()
    params = {"clients": a.clients, "cycles": a.cycles, "period": a.period, "pad": a.pad, "buffer": a.buffer, "seed": a.seed, "trace": a.trace, "grace": a.grace}
    res = asyncio.run(scenario(a.src, a.clients, a.cycles, a.period, a.pad, a.buffer, a.seed, a.n3_06, a.log, a.trace, a.grace))
    result = {"label": a.label, "params": params, **res}
    print(json.dumps({k: v for k, v in result.items() if k != "worst"}), flush=True)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
