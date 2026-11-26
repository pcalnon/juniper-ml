"""
Build the r23w code lens's fixes.json: exact old/new replacements against the carrier's files, each old checked unique.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

CARRIER is the builder's carrier directory (its final/ and texts/). BLOCK is the proposed test block for C1.
Paths starting with "texts/" are the carrier's texts/ files; every other path is repo-relative under final/.

Usage:
  python -I <this file> --carrier CARRIER --block BLOCK_TXT --out fixes.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

TEST = "juniper-service-core/tests/test_websocket_unsendable_late_frame_and_slot.py"
MANAGER = "juniper-service-core/juniper_service_core/websocket/manager.py"

C1_ANCHOR = '    assert executor.executed == ["start"]\n    assert peer.sent_after_the_close() == []\n'

C2_TEST_ANCHOR = "    assert peer_a.closes() == [DROP_CLOSE]  # not closed a second time\n    peer_a.hang_up(1011)\n    await asyncio.wait({task_a}, timeout=30)\n    assert _ended_cleanly(task_a)\n"
C2_TEST = '''

@pytest.mark.asyncio
async def test_close_all_leaves_no_address_charged() -> None:
    """close_all() forgets every socket, so their handlers' disconnect() finds no record to release: no address may stay charged."""
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT, max_connections_per_ip=1)
    peer_a, task_a = await _drop_first(mgr, "10.0.0.1")
    peer_b = AsgiPeer()
    task_b = await _serve(mgr, peer_b, "10.0.0.2")

    await mgr.close_all()
    peer_a.hang_up(1011)
    peer_b.hang_up(1001)
    await asyncio.wait({task_a, task_b}, timeout=30)

    assert mgr._per_ip_counts == {}
    for ip in ("10.0.0.1", "10.0.0.2"):
        peer = AsgiPeer()
        task = await _serve(mgr, peer, ip)
        assert not task.done() and peer.closes() == []
        peer.hang_up()
        await asyncio.wait({task}, timeout=30)
'''
C2_CODE_OLD = "            self._dropped.clear()\n            self._connection_meta.clear()\n"
C2_CODE_NEW = "            self._dropped.clear()\n            self._connection_meta.clear()\n            # Their handlers' disconnect() will find no record to release, so no address may stay charged.\n            self._per_ip_counts.clear()\n"

INFLIGHT = " A command still executing when the heartbeat closed ended the handler the same way under all three implementations, at its acknowledgment (`Cannot call \"send\" once a close message has been sent.`, one `Exception in ASGI application`), measured on uvicorn 0.54.0 and, under `websockets` and `wsproto`, on 0.29.0."


def fixes() -> list[dict]:
    out = []
    # ---- C3: gap (b) reproduces under every implementation through a command running at the close ----
    out.append({
        "id": "C3a", "severity": "MINOR", "file": "texts/pr_body.txt",
        "old": "so only a frame already queued before the close reaches the app there.",
        "new": "so only a frame already queued before the close reaches the app there." + INFLIGHT,
        "why": "The gaps (b) says the handler returned under websockets-sansio and wsproto; a command still executing at the heartbeat's close crashed main's handler under all three (wire cells main/*/b_hb_inflight_*.json).",
    })
    out.append({
        "id": "C3b", "severity": "MINOR", "file": "juniper-service-core/CHANGELOG.md",
        "old": "    unless they had already queued the frame. 0.7.2's `control_stream.py` is the same file. The receive",
        "new": "    unless they had already queued the frame; a command still executing when the heartbeat closed\n    ended the handler the same way under all three, at its acknowledgment. 0.7.2's `control_stream.py`\n    is the same file. The receive",
        "why": "Same omission in the package CHANGELOG (b) bullet; measured under all three implementations on uvicorn 0.54.0.",
    })
    out.append({
        "id": "C3c", "severity": "MINOR", "file": "docs/REFERENCE.md",
        "old": "uvicorn 0.54.0's `websockets-sansio` (what `ws=\"auto\"` selects) and `wsproto` report the disconnect before such a frame, unless they had already queued it.",
        "new": "uvicorn 0.54.0's `websockets-sansio` (what `ws=\"auto\"` selects) and `wsproto` report the disconnect before such a frame, unless they had already queued it. A command still executing when the heartbeat closed failed the same way at its acknowledgment under all three implementations.",
        "why": "Same omission in the control-channel paragraph.",
    })
    out.append({
        "id": "C3d", "severity": "NIT", "file": "CHANGELOG.md",
        "old": "  ended with Starlette's `RuntimeError` on a late frame, and executed a late command it could not acknowledge; it now",
        "new": "  ended with Starlette's `RuntimeError` on a late frame (under uvicorn's `websockets` implementation) or on a command\n  still running at the close (under every implementation), and executed a late command it could not acknowledge; it now",
        "why": "The root entry states the late-frame crash unqualified (main returns cleanly on a late frame under websockets-sansio and wsproto) and omits the in-flight case that crashes under all three.",
    })
    # ---- C4: the slot-hold cost under websockets-sansio / wsproto is understated ----
    out.append({
        "id": "C4a", "severity": "MINOR", "file": "CHANGELOG.md",
        "old": "    implementation; more than 45 s under its `websockets-sansio` and `wsproto`).",
        "new": "    implementation; under its `websockets-sansio` and `wsproto`, still held 180 s after the drop, past uvicorn's own\n    keepalive timeout, until the client's connection goes).",
        "why": "Measured: fix/probe313/c_stall_{websockets-sansio,wsproto}_hold180.json -- A still draining and C refused at 180 s; uvicorn's keepalive (20 s + 20 s) calls transport.close(), which waits for a write buffer a non-reading peer never drains.",
    })
    out.append({
        "id": "C4b", "severity": "MINOR", "file": "docs/REFERENCE.md",
        "old": "the dropped socket's handler was still draining 45 s after the drop under `websockets-sansio` (what 0.54.0's `ws=\"auto\"` selects) and `wsproto`, its close never written, and a reconnect from its address was refused all that time.",
        "new": "the dropped socket's handler was still draining 180 s after the drop under `websockets-sansio` (what 0.54.0's `ws=\"auto\"` selects) and `wsproto`, its close never written, and a reconnect from its address was refused all that time. uvicorn's own keepalive timeout (20 s ping interval, 20 s ping timeout) does not end it: it calls `transport.close()`, which waits for a write buffer the peer never drains. It ends when the client's connection goes.",
        "why": "As C4a: the limit paragraph gives 45 s, the observation window, not the bound.",
    })
    out.append({
        "id": "C4c", "severity": "MINOR", "file": "docs/REFERENCE.md",
        "old": "and under `websockets-sansio` and `wsproto` it was still draining 45 s after the drop (the limit above).",
        "new": "and under `websockets-sansio` and `wsproto` it was still draining 180 s after the drop (the limit above).",
        "why": "As C4a.",
    })
    out.append({
        "id": "C4d", "severity": "MINOR", "file": "texts/pr_body.txt",
        "old": "Under `websockets-sansio` (the default) and `wsproto` it was still draining 45 s after the drop and a socket from its address was still refused.",
        "new": "Under `websockets-sansio` (the default) and `wsproto` it was still draining 180 s after the drop and a socket from its address was still refused, past uvicorn's own keepalive timeout (20 s + 20 s), whose `transport.close()` waits for a write buffer the client never drains: it lasts until the client's connection goes.",
        "why": "As C4a.",
    })
    # ---- C5: "a NumPy scalar" is too broad ----
    out.append({
        "id": "C5a", "severity": "NIT", "file": MANAGER,
        "old": "A value ``json`` cannot serialise (a ``datetime``, a NumPy scalar) fails",
        "new": "A value ``json`` cannot serialise (a ``datetime``, a NumPy integer or ``float32``) fails",
        "why": "np.float64 and np.str_ subclass float/str and serialise (logs/numpy_scalars.txt); the check rightly passes them.",
    })
    out.append({
        "id": "C6", "severity": "NIT", "file": "texts/pr_body.txt",
        "old": "- Not run: macOS, uvicorn older than 0.54.0, hypercorn, daphne, Python 3.15 (CI's informational leg).",
        "new": "- Not run: macOS, hypercorn, daphne. The code lens ran the two this list used to name: CI's informational Python 3.15 leg (3.15.2: 1262 passed, 99%, per-file gate PASS) and uvicorn 0.29.0, the `[test]` extra's floor, with websockets 12.0, FastAPI 0.110.0 and Starlette 0.36.3 (all three gaps reproduce without this change and are gone with it, under `websockets` and `wsproto`).",
        "why": "ci-service-core.yml's matrix is 3.12 + 3.13 blocking and 3.15 informational (not 3.14); measured: logs/ci_fix_py3.15/, wire/{main,fix}/old312/*.json.",
    })
    out.append({
        "id": "C5b", "severity": "NIT", "file": "docs/REFERENCE.md",
        "old": "(a `datetime` or a NumPy scalar, a lone surrogate, a circular reference)",
        "new": "(a `datetime` or a NumPy integer or `float32`, a lone surrogate, a circular reference)",
        "why": "As C5a.",
    })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--carrier", required=True, type=pathlib.Path)
    parser.add_argument("--block", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()
    block = args.block.read_text(encoding="utf-8")
    items = [
        {"id": "C1", "severity": "MINOR", "file": TEST, "old": C1_ANCHOR, "new": C1_ANCHOR + block,
         "why": "Mutants b8-b11 (each restores one post-execution acknowledgment in _handle_command_message to an unguarded send_json) survive the whole suite; b9-b11 bring back gap (b)'s RuntimeError (inproc/main_py3.13.json: main raises on all four endings). The new test kills all four and fails on main."},
        {"id": "C2-code", "severity": "MINOR", "file": MANAGER, "old": C2_CODE_OLD, "new": C2_CODE_NEW,
         "why": "close_all() clears _connection_meta and _dropped but not _per_ip_counts, so every address with a socket open at close_all stays charged for good (the handlers' disconnect() finds no record); this change adds dropped sockets to that set (inproc close_all_per_ip: main locks out 1 of 2 addresses, the fix 2 of 2)."},
        {"id": "C2-test", "severity": "MINOR", "file": TEST, "old": C2_TEST_ANCHOR, "new": C2_TEST_ANCHOR + C2_TEST,
         "why": "Pins C2-code: fails without it, passes with it."},
    ]
    items.extend(fixes())
    # every old must occur exactly once in the carrier's file
    for item in items:
        if item["file"].startswith("texts/"):
            path = args.carrier / item["file"]
        else:
            path = args.carrier / "final" / item["file"]
        count = path.read_text(encoding="utf-8").count(item["old"])
        item["old_occurrences_in_carrier"] = count
        if count != 1:
            print(f"BAD {item['id']}: old occurs {count} times in {path}")
    clean = [{k: v for k, v in item.items() if k != "old_occurrences_in_carrier"} for item in items]
    args.out.write_text(json.dumps(clean, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps([(i["id"], i["old_occurrences_in_carrier"]) for i in items]))
    return 0 if all(i["old_occurrences_in_carrier"] == 1 for i in items) else 1


if __name__ == "__main__":
    sys.exit(main())
