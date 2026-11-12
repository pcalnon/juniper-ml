"""
Seeded property sweep over /ws/training resume interleavings, re-run on the N-3 round-2 carrier.

Copied from round 1's sweep (the carrier worktree's tmp/flood4-fix/n3/seed_sweep.py) with only its paths and its
output changed, so its counts compare with round 1's: home-derived paths instead of a literal, and the summary JSON
written to --out. Each seed builds a random scenario on the real WebSocketManager and training_stream_handler (the
test file's FakeWS and helpers): replay-buffer size, chunking, history, last_seq (sometimes already evicted),
per-send yields, broadcasts concurrent with the resume, and for a quarter of seeds one injected send failure.

The property, whatever the outcome:
  * resume_ok and still open  -> it received exactly last_seq+1 .. current_seq;
  * resume_ok and closed      -> a gap-free prefix of that run, nothing after the gap, in neither connection set;
  * resume_failed             -> what it received live (after the fresh-connect promotion) is a gap-free run that
                                 ends at current_seq;
  * the observer always received exactly 1 .. current_seq.

Usage: python <this> --first 0 --n 20000 --out <json>   (SWEEP_SRC=<a src/ tree> to test other code; default: the
carrier's src/)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses
"""

import argparse
import asyncio
import importlib.util
import json
import logging
import os
import random
import sys
import time
from pathlib import Path

CARRIER = Path.home() / "Development" / "python" / "Juniper" / "worktrees" / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
SRC = Path(os.environ.get("SWEEP_SRC", str(CARRIER / "src")))
sys.path.insert(0, str(SRC))
_SPEC = importlib.util.spec_from_file_location("resume_tests", CARRIER / "src" / "tests" / "unit" / "api" / "test_websocket_resume_continuity.py")
t = importlib.util.module_from_spec(_SPEC)
sys.modules["resume_tests"] = t
_SPEC.loader.exec_module(t)

logging.disable(logging.CRITICAL)


def run_one(seed: int) -> dict:
    rng = random.Random(seed)

    async def scenario() -> dict:
        buf = rng.choice([3, 5, 8, 16, 1024])
        chunk_kwargs = {"max_message_size_bytes": 200, "chunk_payload_size_bytes": 64} if rng.random() < 0.3 else {}
        mgr = t._manager(max_replay_buffer_size=buf, **chunk_kwargs)
        observer = await t._observer(mgr)

        def message(tag: str) -> dict:
            if chunk_kwargs and rng.random() < 0.3:
                return {"type": "topology", "data": {"tag": tag, "blob": "z" * rng.randint(150, 600)}}
            return t._metrics(tag)

        for i in range(rng.randint(0, 12)):
            await mgr.broadcast(message(f"before-{i}"))
        last_seq = rng.randint(max(0, mgr.current_seq - buf - 2), mgr.current_seq)
        fail_on_seq = None
        if rng.random() < 0.25:
            fail_on_seq = rng.randint(last_seq + 1, last_seq + 1 + rng.randint(0, 20))
        ws, task = t._start_resume(mgr, last_seq, yields=lambda: rng.randint(0, 3), fail_on_seq=fail_on_seq)

        for i in range(rng.randint(0, 14)):
            for _ in range(rng.randint(0, 4)):
                await asyncio.sleep(0)
            await mgr.broadcast(message(f"during-{i}"))
        await t._settle(task, ws)
        await mgr.broadcast(message("live"))
        await t._finish(task, ws)

        seqs = ws.seqs()
        current = mgr.current_seq
        types = ws.types()
        got_ok = "resume_ok" in types
        closed = ws.closed is not None
        problems = []
        if observer.seqs() != list(range(1, current + 1)):
            problems.append("observer saw a hole")
        if got_ok:
            full = list(range(last_seq + 1, current + 1))
            if not closed:
                if seqs != full:
                    problems.append("resume_ok, open, but not exactly last_seq+1..current")
            else:
                if seqs != full[: len(seqs)]:
                    problems.append("resume_ok, closed, but not a gap-free prefix")
                if ws in mgr._active_connections or ws in mgr._pending_connections:
                    problems.append("closed but still registered")
        else:
            if "resume_failed" not in types:
                problems.append("neither resume_ok nor resume_failed")
            if seqs and seqs != list(range(seqs[0], seqs[0] + len(seqs))):
                problems.append("fresh-connect stream has a hole")
            if seqs and not closed and seqs[-1] != current:
                problems.append("fresh-connect stream stops short of current")
        outcome = ("ok-open" if not closed else ("ok-closed:" + ws.closed[1])) if got_ok else ("failed:" + ws.frame("resume_failed")["data"]["reason"])
        return {"seed": seed, "outcome": outcome, "problems": problems, "seqs": seqs if problems else None, "last_seq": last_seq, "current": current}

    return asyncio.run(scenario())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=0)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    start = time.monotonic()
    outcomes: dict = {}
    bad = []
    for seed in range(args.first, args.first + args.n):
        res = run_one(seed)
        outcomes[res["outcome"]] = outcomes.get(res["outcome"], 0) + 1
        if res["problems"]:
            bad.append(res)
    summary = {
        "code_under_test": sys.modules["api.websocket.manager"].__file__,
        "seeds": [args.first, args.first + args.n - 1],
        "n": args.n,
        "elapsed_s": round(time.monotonic() - start, 1),
        "outcomes": outcomes,
        "violations": len(bad),
        "first_violations": bad[:10],
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    print(json.dumps({k: summary[k] for k in ("code_under_test", "n", "elapsed_s", "outcomes", "violations")}))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
