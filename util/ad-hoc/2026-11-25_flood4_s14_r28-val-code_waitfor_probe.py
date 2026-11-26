"""
Probe: does asyncio.wait_for(task, timeout) raise TimeoutError when the awaited task swallows its cancellation and
returns normally (as juniper-canopy's metrics relay does), on the interpreter that runs this file?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r28-val-code (finding C5: the relay test's HOLD_SECONDS + 5 bound)

Usage:
    python <this file>

The task mirrors _relay_loop's shape: it awaits work that outlasts the timeout and, on CancelledError, sets a flag and
returns normally. Prints one JSON line: whether wait_for raised, what it returned, whether the task ended cancelled,
and the same for asyncio.wait as the alternative. Deterministic: no load, timeouts of 0.05 s against 0.5 s of work.
"""

from __future__ import annotations

import asyncio
import json
import sys


async def relay_like(state: dict) -> str:
    try:
        await asyncio.sleep(0.5)  # the work in flight when the deadline passes
        return "finished"
    except asyncio.CancelledError:
        state["swallowed"] = True  # _relay_loop: `except asyncio.CancelledError: relay_enabled = False`
        return "swallowed-cancel"


async def main() -> dict:
    out: dict = {"python": sys.version.split()[0]}
    state: dict = {}
    task = asyncio.create_task(relay_like(state))
    try:
        result = await asyncio.wait_for(task, timeout=0.05)
        out["wait_for"] = {"raised": None, "returned": result}
    except TimeoutError as exc:
        out["wait_for"] = {"raised": type(exc).__name__}
    out["wait_for"]["task_cancelled"] = task.cancelled()
    out["wait_for"]["task_swallowed_cancel"] = state.get("swallowed", False)
    state2: dict = {}
    task2 = asyncio.create_task(relay_like(state2))
    done, _pending = await asyncio.wait({task2}, timeout=0.05)
    out["asyncio_wait"] = {"task_in_done": task2 in done, "task_still_running": not task2.done()}
    task2.cancel()
    await asyncio.gather(task2, return_exceptions=True)
    return out


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main())))
