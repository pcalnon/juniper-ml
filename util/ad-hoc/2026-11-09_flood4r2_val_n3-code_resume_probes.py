"""
Adversarial probes for juniper-cascor's /ws/training resume-loss fix (flood-4 round 2, validator n3, code lens).

Imports the real ``api.websocket.manager`` / ``api.websocket.training_stream`` from the ``--src``
tree given (origin/main's, the fix's, or a mutant's) and drives the real handler with an
independent fake socket. Each scenario prints one JSON line; ``--out`` also writes them all.

Scenarios:
  repro_defect1      a broadcast made while nobody is connected, then a resume from the last seq held
  repro_defect2      a TRAINING-THREAD broadcast (broadcast_from_thread) landing during a replay send
  final_check_waiter promote_to_active(replayed_through=...) with a second task queued on the manager lock
  fuzz               N seeds: several concurrent resumes through the handler, a sequential broadcaster,
                     and connect_pending/disconnect churn contending for the manager lock
  evict_boundary     the catch-up when the oldest buffered seq is exactly cursor+1 / cursor+2
  evict_later_pass   eviction during a LATER catch-up pass (not during the replay)
  close_all_mid      close_all() while a catch-up send is in flight
  peer_dies_mid      the transport dies on a catch-up send
  keeps_pace         one new broadcast per catch-up send: does the catch-up ever end?
  cursors            last_seq NaN / Infinity / above current_seq / negative / bool / float
  unserializable     a buffered message made unserializable after it was buffered

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
import random
import sys
import threading
import types
from typing import Any, Callable, Dict, List, Optional


def _load(src: str):
    sys.path.insert(0, src)
    import api.websocket.manager as manager_mod  # noqa: E402
    import api.websocket.training_stream as ts  # noqa: E402
    from fastapi import WebSocketDisconnect  # noqa: E402

    return manager_mod, ts, WebSocketDisconnect


class Sock:
    """An independent fake /ws/training socket (not the builder's FakeWS)."""

    _n = 0

    def __init__(self, disconnect_exc, *, app=None, frames=(), yields: Callable[[], int] = lambda: 0, hook=None, host: Optional[str] = None, accept_yields: Callable[[], int] = lambda: 0):
        self._accept_yields = accept_yields
        Sock._n += 1
        self.name = f"s{Sock._n}"
        self.client = (host or f"10.{Sock._n // 250}.{Sock._n % 250}.1", 4000 + Sock._n)
        self.headers: Dict[str, str] = {}
        self.app = app
        self.out: List[dict] = []
        self.closes: List[tuple] = []
        self.dead = False
        self._exc = disconnect_exc
        self._q: "asyncio.Queue[Optional[str]]" = asyncio.Queue()
        for f in frames:
            self._q.put_nowait(f)
        self._yields = yields
        self._hook = hook
        self.serving = asyncio.Event()

    async def accept(self) -> None:
        # A server whose accept awaits the handshake write (the model in the builder's own lock
        # test: "a concurrent connect that is slow to accept() holds it"). connect()/connect_pending()
        # hold the manager lock across this await.
        for _ in range(self._accept_yields()):
            await asyncio.sleep(0)

    async def send_json(self, message: dict) -> None:
        if self._hook is not None:
            await self._hook(self, message)
        for _ in range(self._yields()):
            await asyncio.sleep(0)
        if self.dead:
            raise RuntimeError("transport gone")
        self.out.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closes.append((code, reason))

    async def receive_text(self) -> str:
        if self._q.empty():
            self.serving.set()
        item = await self._q.get()
        if item is None:
            raise self._exc(code=1000)
        return item

    def hang_up(self) -> None:
        self._q.put_nowait(None)

    def seqs(self) -> List[int]:
        return [m["seq"] for m in self.out if "seq" in m]

    def types(self) -> List[str]:
        return [m.get("type") for m in self.out]

    def tags(self) -> List[Any]:
        return [m.get("data", {}).get("tag") for m in self.out if "seq" in m]


def _app(mgr, resume_timeout: float = 60.0):
    settings = types.SimpleNamespace(
        ws_resume_handshake_timeout_s=resume_timeout,
        ws_initial_metrics_count=0,
        ws_heartbeat_interval_sec=0,
        ws_heartbeat_pong_timeout_sec=60,
    )
    return types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, settings=settings, lifecycle=None))


def _resume(mgr, last_seq: Any, raw: Optional[str] = None) -> str:
    if raw is not None:
        return '{"type":"resume","data":{"last_seq":%s,"server_instance_id":"%s"}}' % (raw, mgr.server_instance_id)
    return json.dumps({"type": "resume", "data": {"last_seq": last_seq, "server_instance_id": mgr.server_instance_id}})


def _m(tag: Any) -> dict:
    return {"type": "metrics", "data": {"tag": tag}}


async def _serving_or_done(sock: Sock, task: "asyncio.Task", timeout: float = 20.0) -> None:
    waiter = asyncio.ensure_future(sock.serving.wait())
    try:
        await asyncio.wait({task, waiter}, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
    finally:
        waiter.cancel()


async def _end(sock: Sock, task: "asyncio.Task") -> None:
    sock.hang_up()
    await asyncio.wait_for(task, timeout=20.0)


def _check_stream(seqs: List[int], expected: List[int]) -> Dict[str, Any]:
    dups = sorted({s for s in seqs if seqs.count(s) > 1})
    ooo = any(b <= a for a, b in zip(seqs, seqs[1:]))
    missing = sorted(set(expected) - set(seqs))
    return {"dups": dups, "out_of_order": ooo, "missing": missing}


# ------------------------------------------------------------------------------------------------
# Reproductions
# ------------------------------------------------------------------------------------------------


async def repro_defect1(M, ts, WSD) -> dict:
    mgr = M.WebSocketManager(send_timeout_seconds=30)
    a = Sock(WSD)
    assert await mgr.connect(a)
    await mgr.broadcast(_m("t0"))
    held = a.seqs()[-1]
    await mgr.disconnect(a)
    await mgr.broadcast(_m("t1-nobody-connected"))
    await mgr.broadcast(_m("t2-nobody-connected"))
    s = Sock(WSD, app=_app(mgr), frames=[_resume(mgr, held)])
    task = asyncio.create_task(ts.training_stream_handler(s))
    await _serving_or_done(s, task)
    await mgr.broadcast(_m("t3-live"))
    await _end(s, task)
    got = s.tags()
    lost = [t for t in ("t1-nobody-connected", "t2-nobody-connected", "t3-live") if t not in got]
    resume_ok = next((m for m in s.out if m.get("type") == "resume_ok"), None)
    return {"held_seq": held, "resume_ok": resume_ok is not None, "replayed_count": (resume_ok or {}).get("data", {}).get("replayed_count"), "received_seqs": s.seqs(), "received_tags": got, "lost_tags": lost, "LOSS": bool(lost) and resume_ok is not None}


async def repro_defect2(M, ts, WSD) -> dict:
    """The mid-replay broadcast comes from a real thread through broadcast_from_thread."""
    loop = asyncio.get_running_loop()
    mgr = M.WebSocketManager(send_timeout_seconds=30)
    mgr.set_event_loop(loop)
    obs = Sock(WSD)
    assert await mgr.connect(obs)
    for i in range(1, 6):
        await mgr.broadcast(_m(f"pre{i}"))  # seqs 1-5

    async def hook(_sock: Sock, msg: dict) -> None:
        if msg.get("seq") == 3:  # the first replayed frame is being written (a send under back-pressure)
            t = threading.Thread(target=mgr.broadcast_from_thread, args=(_m("training-thread"),))
            t.start()
            await asyncio.to_thread(t.join)
            for _ in range(5):
                await asyncio.sleep(0)

    s = Sock(WSD, app=_app(mgr), frames=[_resume(mgr, 2)], hook=hook)
    task = asyncio.create_task(ts.training_stream_handler(s))
    await _serving_or_done(s, task)
    await mgr.broadcast(_m("live"))
    await _end(s, task)
    expected = list(range(3, mgr.current_seq + 1))
    chk = _check_stream(s.seqs(), expected)
    return {"received_seqs": s.seqs(), "expected": expected, "observer_seqs": obs.seqs(), **chk, "LOSS": bool(chk["missing"])}


# ------------------------------------------------------------------------------------------------
# Boundary probes (need promote_to_active(..., replayed_through=...), i.e. the fix or a mutant of it)
# ------------------------------------------------------------------------------------------------


def _has_cursor_api(M) -> bool:
    import inspect

    return "replayed_through" in inspect.signature(M.WebSocketManager.promote_to_active).parameters


async def final_check_waiter(M, ts, WSD) -> dict:
    """A second task waits on the manager lock while the resuming socket makes its final check."""
    if not _has_cursor_api(M):
        return {"skipped": "no replayed_through API"}
    mgr = M.WebSocketManager(send_timeout_seconds=30)
    obs = Sock(WSD)
    assert await mgr.connect(obs)
    s = Sock(WSD)
    assert await mgr.connect_pending(s)
    for i in range(3):
        await mgr.broadcast(_m(i))  # seqs 1-3 while s is pending
    for ev in mgr.replay_since(0):
        assert await mgr.send_personal_message(s, ev)
    await mgr._lock.acquire()  # held elsewhere, e.g. connect() awaiting a slow accept()
    promote = asyncio.create_task(mgr.promote_to_active(s, replayed_through=3))
    await asyncio.sleep(0)  # promote queues on the lock
    contender = asyncio.create_task(mgr.connect_pending(Sock(WSD)))  # queued behind it
    await asyncio.sleep(0)
    mgr._lock.release()
    late = asyncio.create_task(mgr.broadcast(_m("late")))  # ready to run whenever promote yields
    ok = await promote
    await late
    await contender
    chk = _check_stream(s.seqs(), [1, 2, 3, 4])
    return {"promote_returned": ok, "received_seqs": s.seqs(), "observer_seqs": obs.seqs(), **chk, "LOSS": bool(chk["missing"])}


async def fuzz_one(M, ts, WSD, seed: int, n_resumers: int = 3, accept_yields: int = 0) -> dict:
    rng = random.Random(seed)
    ay = (lambda: rng.randint(0, accept_yields)) if accept_yields else (lambda: 0)
    buf = rng.choice([6, 12, 1024])
    mgr = M.WebSocketManager(send_timeout_seconds=30, max_replay_buffer_size=buf, max_connections=500, max_connections_per_ip=500, max_connections_global=500)
    obs = Sock(WSD)
    assert await mgr.connect(obs)
    for i in range(rng.randint(0, 8)):
        await mgr.broadcast(_m(f"pre{i}"))
    resumers = []
    for k in range(n_resumers):
        lo = max(0, mgr.current_seq - buf + 1)
        last = rng.randint(lo, mgr.current_seq) if mgr.current_seq else 0
        s = Sock(WSD, app=_app(mgr), frames=[_resume(mgr, last)], yields=lambda: rng.randint(0, 3), accept_yields=ay)
        resumers.append((s, last, asyncio.create_task(ts.training_stream_handler(s))))

    async def broadcaster() -> None:
        for i in range(rng.randint(5, 30)):
            for _ in range(rng.randint(0, 3)):
                await asyncio.sleep(0)
            await mgr.broadcast(_m(f"b{i}"))

    async def churn() -> None:
        for _ in range(rng.randint(0, 12)):
            x = Sock(WSD, accept_yields=ay)
            for _ in range(rng.randint(0, 2)):
                await asyncio.sleep(0)
            await mgr.connect_pending(x)
            for _ in range(rng.randint(0, 2)):
                await asyncio.sleep(0)
            await mgr.disconnect(x)

    await asyncio.gather(broadcaster(), churn())
    for s, _, task in resumers:
        await _serving_or_done(s, task)
    await mgr.broadcast(_m("final"))
    for s, _, task in resumers:
        if not task.done():
            await _end(s, task)
        else:
            await task
    violations = []
    for s, last, _ in resumers:
        types_ = s.types()
        seqs = s.seqs()
        if "resume_ok" in types_:
            expected = list(range(last + 1, mgr.current_seq + 1))
            if s.closes:  # aborted: must be a gap-free prefix
                if s.closes[-1][0] != 1011 or seqs != expected[: len(seqs)]:
                    violations.append({"sock": s.name, "kind": "abort-not-prefix", "last": last, "seqs": seqs, "closes": s.closes})
            elif seqs != expected:
                violations.append({"sock": s.name, "kind": "resume_ok-stream-wrong", "last": last, "seqs": seqs, "expected": expected, **_check_stream(seqs, expected)})
        else:  # resume_failed -> fresh path: what it does get must be contiguous to the end
            if seqs and seqs != list(range(seqs[0], mgr.current_seq + 1)):
                violations.append({"sock": s.name, "kind": "fresh-stream-wrong", "seqs": seqs})
    if obs.seqs() != list(range(1, mgr.current_seq + 1)):
        violations.append({"sock": "observer", "kind": "observer-stream-wrong", "seqs": obs.seqs()})
    return {"seed": seed, "violations": violations, "aborts": sum(1 for s, _, _ in resumers if s.closes), "resume_ok": sum(1 for s, _, _ in resumers if "resume_ok" in s.types())}


async def evict_boundary(M, ts, WSD) -> dict:
    if not _has_cursor_api(M):
        return {"skipped": "no replayed_through API"}
    out = {}
    for label, n_extra in (("oldest==cursor+1", 4), ("oldest==cursor+2", 5)):
        mgr = M.WebSocketManager(send_timeout_seconds=30, max_replay_buffer_size=4)
        s = Sock(WSD)
        assert await mgr.connect_pending(s)
        for i in range(2):
            await mgr.broadcast(_m(i))  # seqs 1-2: the socket "holds" them
        for i in range(n_extra):
            await mgr.broadcast(_m(f"x{i}"))  # 4 extra -> buffer 3..6 (oldest = 3 = cursor+1); 5 extra -> 4..7
        ok = await mgr.promote_to_active(s, replayed_through=2)
        out[label] = {"promote_returned": ok, "received_seqs": s.seqs(), "active": s in mgr._active_connections}
    return out


async def evict_later_pass(M, ts, WSD) -> dict:
    """Eviction while a LATER catch-up pass is sending, through the real handler."""
    if not _has_cursor_api(M):
        return {"skipped": "no replayed_through API"}
    mgr = M.WebSocketManager(send_timeout_seconds=30, max_replay_buffer_size=4)
    obs = Sock(WSD)
    assert await mgr.connect(obs)
    for i in range(2):
        await mgr.broadcast(_m(i))  # seqs 1-2

    state = {"phase": 0}

    async def hook(_sock: Sock, msg: dict) -> None:
        seq = msg.get("seq")
        if seq == 2 and state["phase"] == 0:  # the replay: one broadcast, so a catch-up pass is needed
            state["phase"] = 1
            await mgr.broadcast(_m("c1"))  # seq 3
        elif seq == 3 and state["phase"] == 1:  # first catch-up pass sending seq 3: burst past the buffer
            state["phase"] = 2
            for i in range(6):
                await mgr.broadcast(_m(f"burst{i}"))  # seqs 4-9; buffer keeps 6-9, seqs 4-5 evicted

    s = Sock(WSD, app=_app(mgr), frames=[_resume(mgr, 1)], hook=hook)
    task = asyncio.create_task(ts.training_stream_handler(s))
    await _serving_or_done(s, task)
    if not task.done():
        await mgr.broadcast(_m("live"))
        await _end(s, task)
    else:
        await task
    expected = list(range(2, mgr.current_seq + 1))
    seqs = s.seqs()
    prefix_ok = seqs == expected[: len(seqs)]
    return {"received_seqs": seqs, "closes": s.closes, "prefix_ok": prefix_ok, "HOLE": not prefix_ok, "expected": expected}


async def close_all_mid(M, ts, WSD) -> dict:
    if not _has_cursor_api(M):
        return {"skipped": "no replayed_through API"}
    mgr = M.WebSocketManager(send_timeout_seconds=30)
    obs = Sock(WSD)
    assert await mgr.connect(obs)
    for i in range(3):
        await mgr.broadcast(_m(i))

    async def hook(_sock: Sock, msg: dict) -> None:
        if msg.get("seq") == 2:
            await mgr.broadcast(_m("during"))  # seq 4: needs the catch-up
        if msg.get("seq") == 4:  # a catch-up send: shutdown now
            await mgr.close_all()

    s = Sock(WSD, app=_app(mgr), frames=[_resume(mgr, 1)], hook=hook)
    task = asyncio.create_task(ts.training_stream_handler(s))
    await _serving_or_done(s, task)
    served = not task.done()
    if served:
        await _end(s, task)
    else:
        await task
    return {"served_after_close_all": served, "active": s in mgr._active_connections, "pending": s in mgr._pending_connections, "closes": s.closes, "received_seqs": s.seqs(), "RESURRECTED": served or s in mgr._active_connections}


async def peer_dies_mid(M, ts, WSD) -> dict:
    if not _has_cursor_api(M):
        return {"skipped": "no replayed_through API"}
    mgr = M.WebSocketManager(send_timeout_seconds=30)
    obs = Sock(WSD)
    assert await mgr.connect(obs)
    for i in range(3):
        await mgr.broadcast(_m(i))
    g0, ip0 = mgr._global_ws_count, dict(mgr._per_ip_counts)

    async def hook(sock: Sock, msg: dict) -> None:
        if msg.get("seq") == 2:
            await mgr.broadcast(_m("during"))  # seq 4
        if msg.get("seq") == 4:
            sock.dead = True

    s = Sock(WSD, app=_app(mgr), frames=[_resume(mgr, 1)], hook=hook)
    task = asyncio.create_task(ts.training_stream_handler(s))
    await _serving_or_done(s, task)
    served = not task.done()
    if served:
        await _end(s, task)
    else:
        await task
    return {"served": served, "closes": s.closes, "received_seqs": s.seqs(), "slots_released": (mgr._global_ws_count, mgr._per_ip_counts) == (g0, ip0), "active": s in mgr._active_connections}


async def keeps_pace(M, ts, WSD, limit: int = 20000) -> dict:
    """Each catch-up send yields once, and one broadcast lands per send: the backlog never drains."""
    if not _has_cursor_api(M):
        return {"skipped": "no replayed_through API"}
    mgr = M.WebSocketManager(send_timeout_seconds=30)
    obs = Sock(WSD)
    assert await mgr.connect(obs)
    for i in range(3):
        await mgr.broadcast(_m(i))
    state = {"n": 0, "stop": False, "sent_while_pending": 0, "first_active_send_at": None}

    async def hook(sock: Sock, msg: dict) -> None:
        if "seq" not in msg:
            return
        if sock in mgr._pending_connections:
            state["sent_while_pending"] += 1
        elif state["first_active_send_at"] is None:
            state["first_active_send_at"] = msg["seq"]
        if msg["seq"] >= 2 and not state["stop"]:
            state["n"] += 1
            if state["n"] >= limit:
                state["stop"] = True
            await mgr.broadcast(_m(f"pace{state['n']}"))

    s = Sock(WSD, app=_app(mgr), frames=[_resume(mgr, 1)], hook=hook)
    task = asyncio.create_task(ts.training_stream_handler(s))
    await _serving_or_done(s, task, timeout=600.0)
    if not task.done():
        await mgr.broadcast(_m("live"))
        await _end(s, task)
    expected = list(range(2, mgr.current_seq + 1))
    chk = _check_stream(s.seqs(), expected)
    return {
        "broadcasts_injected": state["n"],
        "limit": limit,
        "frames_sent_while_still_pending": state["sent_while_pending"],
        "first_seq_sent_after_activation": state["first_active_send_at"],
        "activated_only_after_injection_stopped": state["sent_while_pending"] >= limit,
        **chk,
    }


async def cursors(M, ts, WSD) -> dict:
    out = {}
    cases = [
        ("nan", None, "NaN"),
        ("inf", None, "Infinity"),
        ("neg_inf", None, "-Infinity"),
        ("above_current", "ABOVE", None),
        ("float_2_5", 2.5, None),
        ("bool_true", True, None),
        ("negative_-3", -3, None),
        ("string_'2'", "2", None),
    ]
    for label, value, raw in cases:
        mgr = M.WebSocketManager(send_timeout_seconds=30)
        a = Sock(WSD)
        assert await mgr.connect(a)
        for i in range(5):
            await mgr.broadcast(_m(i))  # seqs 1-5
        await mgr.disconnect(a)
        v = mgr.current_seq + 100 if value == "ABOVE" else value
        s = Sock(WSD, app=_app(mgr), frames=[_resume(mgr, v, raw=raw)])
        task = asyncio.create_task(ts.training_stream_handler(s))
        await _serving_or_done(s, task)
        await mgr.broadcast(_m("live"))
        if not task.done():
            await _end(s, task)
        else:
            await task
        first = next((m for m in s.out if m.get("type") in ("resume_ok", "resume_failed")), None)
        out[label] = {
            "answer": (first or {}).get("type") or "fresh-connect (no resume answer)",
            "reason": (first or {}).get("data", {}).get("reason"),
            "replayed_count": (first or {}).get("data", {}).get("replayed_count"),
            "received_seqs": s.seqs(),
        }
    return out


async def unserializable(M, ts, WSD) -> dict:
    """A buffered message mutated after buffering (nested dict shared with the producer)."""
    import numpy as np

    mgr = M.WebSocketManager(send_timeout_seconds=30)
    obs = Sock(WSD)
    assert await mgr.connect(obs)
    msg = {"type": "state", "data": {"status": "running"}}
    await mgr.broadcast(_m(0))  # seq 1
    await mgr.broadcast(msg)  # seq 2
    await mgr.broadcast(_m(2))  # seq 3
    msg["data"]["patience"] = np.int64(3)  # the producer mutates a dict the buffer still references
    runs = []
    for _ in range(3):
        s = Sock(WSD, app=_app(mgr), frames=[_resume(mgr, 1)])
        task = asyncio.create_task(ts.training_stream_handler(s))
        await _serving_or_done(s, task)
        if not task.done():
            await _end(s, task)
        else:
            await task
        runs.append({"types": s.types(), "received_seqs": s.seqs(), "closes": s.closes})
    # Is the precondition reachable from cascor's producers? model_dump builds fresh containers.
    from api.websocket.messages import create_state_message

    state = {"status": "running", "nested": {"a": 1}}
    built = create_state_message(state)
    shares = built["data"] is state or built["data"].get("nested") is state["nested"]
    return {"runs": runs, "producer_message_shares_caller_dicts": shares}


SCENARIOS = {
    "repro_defect1": repro_defect1,
    "repro_defect2": repro_defect2,
    "final_check_waiter": final_check_waiter,
    "evict_boundary": evict_boundary,
    "evict_later_pass": evict_later_pass,
    "close_all_mid": close_all_mid,
    "peer_dies_mid": peer_dies_mid,
    "keeps_pace": keeps_pace,
    "cursors": cursors,
    "unserializable": unserializable,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--fuzz-seeds", type=int, default=0)
    ap.add_argument("--fuzz-start", type=int, default=0)
    ap.add_argument("--accept-yields", type=int, default=0, help="max yields inside accept() (connect* hold the manager lock across it)")
    ap.add_argument("--out")
    args = ap.parse_args()
    M, ts, WSD = _load(args.src)
    import logging

    logging.disable(logging.CRITICAL)
    results = {"label": args.label, "src": args.src}

    async def run() -> None:
        for name, fn in SCENARIOS.items():
            if args.only and name not in args.only:
                continue
            res = await fn(M, ts, WSD)
            results[name] = res
            print(json.dumps({name: res}, default=str))
        if args.fuzz_seeds:
            bad = []
            aborts = 0
            oks = 0
            for seed in range(args.fuzz_start, args.fuzz_start + args.fuzz_seeds):
                r = await fuzz_one(M, ts, WSD, seed, accept_yields=args.accept_yields)
                aborts += r["aborts"]
                oks += r["resume_ok"]
                if r["violations"]:
                    bad.append(r)
            results["fuzz"] = {"accept_yields": args.accept_yields, "seeds": args.fuzz_seeds, "start": args.fuzz_start, "violating_seeds": len(bad), "aborted_resumes": aborts, "resume_ok": oks, "first_violations": bad[:3]}
            print(json.dumps({"fuzz": results["fuzz"]}, default=str))

    asyncio.run(run())
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
