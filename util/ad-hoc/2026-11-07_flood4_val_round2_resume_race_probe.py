#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 docs carrier, round-2 validation (read-only probe)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# -----------------------------------------------------------------------------
"""Does a broadcast that lands while a resume replay is being SENT reach the resuming client?

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 2 (findings: tmp/flood4/ml-docs/val-round2/)

Drives the real ``WebSocketManager`` and ``training_stream._handle_resume`` from the
juniper-service-core tree named on the command line. Two fake sockets: one already active
(so broadcasts are sequenced and buffered), one resuming. The resuming socket's send yields
once (``asyncio.sleep(0)``), the shape of a send that waits on transport back-pressure; a
broadcast is scheduled to run during that yield. Prints which seqs each socket received.

Usage: python3 <this> <path-to-juniper-service-core>
Writes nothing.
"""

import asyncio
import sys


class FakeWS:
    def __init__(self, name: str, suspend: bool) -> None:
        self.name = name
        self.suspend = suspend
        self.sent: list = []
        self.client = ("127.0.0.1", 1)
        self.headers = {}

    async def accept(self) -> None:
        return None

    async def close(self, code: int = 1000, reason: str = "") -> None:
        return None

    async def send_json(self, message: dict) -> None:
        if self.suspend:
            await asyncio.sleep(0)
        self.sent.append(message)


async def main(core: str) -> int:
    sys.path.insert(0, core)
    from juniper_service_core.websocket.manager import WebSocketManager
    from juniper_service_core.websocket import training_stream as ts

    mgr = WebSocketManager()
    other = FakeWS("other", suspend=False)
    await mgr.connect(other)
    for i in range(5):
        await mgr.broadcast({"type": "metrics", "data": {"i": i}})
    last_seq_client_had = 2
    resuming = FakeWS("resuming", suspend=True)
    await mgr.connect_pending(resuming)

    async def late_broadcast() -> None:
        await mgr.broadcast({"type": "metrics", "data": {"i": "during-replay"}})

    msg = {"type": "resume", "data": {"last_seq": last_seq_client_had, "server_instance_id": mgr.server_instance_id}}
    task = asyncio.ensure_future(late_broadcast())
    ok = await ts._handle_resume(resuming, mgr, msg)
    await task
    await mgr.promote_to_active(resuming)
    await mgr.broadcast({"type": "metrics", "data": {"i": "after-promote"}})

    buffered = [m.get("seq") for m in mgr.replay_since(0)]
    got = [m.get("seq") for m in resuming.sent if "seq" in m]
    kinds = [m.get("type") for m in resuming.sent]
    print("resume ok:", ok)
    print("buffered seqs:", buffered)
    print("resuming client got seqs:", got, "frame types:", kinds)
    missing = [s for s in buffered if s > last_seq_client_had and s not in got]
    print("buffered after last_seq but never delivered to the resuming client:", missing)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1])))
