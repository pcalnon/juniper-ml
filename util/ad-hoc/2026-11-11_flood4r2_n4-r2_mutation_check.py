#!/usr/bin/env python3
"""
Mutation check, round 2: every round-1 arm and every validator mutant of the N-4 fix, each in its own scratch copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (test-efficacy evidence for the N-4 pins, round 2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (section 8, ruling 11);
         juniper-service-core/juniper_service_core/websocket/manager.py,
         juniper-service-core/juniper_service_core/websocket/training_stream.py,
         juniper-service-core/tests/test_websocket_broadcast_drop_close.py

Supersedes round 1's mutation helper (its 15 arms are kept here under ``r1_``; the three that replaced a condition
with ``True`` or ``False`` now use ``1`` or ``0``, the same mutant) and adds the round-1 code validator's 22 mutants
(``v_``) and four of this round's own (``r2_``). Usage::

    python3 <this file> --tree <tree root> --out <scratch dir> --python <interpreter>

The tree is never modified (the sha256 of the three files is recorded before and after). Each arm copies the tree's
``juniper-service-core/juniper_service_core`` and ``juniper-service-core/tests`` -- without ``pyproject.toml``, so no
``[project]`` table lands under a ``tmp/``, and without any ``__pycache__`` -- into ``<out>/arms/<arm>/``, applies
exact-text replacements (each ``old`` must occur exactly once) and runs the WebSocket suites there with
``-c <tree>/juniper-service-core/pyproject.toml``, PYTHONDONTWRITEBYTECODE=1 and PYTHONPATH = the tree's
``juniper-model-core`` only. ``tests/`` is a package, so pytest puts the copy's root first on ``sys.path``: the
``canary`` arm (the copy's manager.py raises on import) must fail every suite, which proves the copy is what runs,
and the ``control`` arm (no change) must pass. The ``main`` arm swaps in ``origin/main``'s two modules (``git show``,
run in the tree): the tests of the new file that fail there are the failing-first set.

An arm is KILLED when at least one of the tests it names fails; an arm marked ``survives`` is expected to pass every
suite, and its reason is recorded. The exit status is 0 only when every arm met its expectation. At most four arms
run at once. The arm copies are removed afterwards; the logs and ``mutants.json`` stay in ``<out>``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MANAGER = "juniper_service_core/websocket/manager.py"
STREAM = "juniper_service_core/websocket/training_stream.py"
NEW_TESTS = "tests/test_websocket_broadcast_drop_close.py"
T = NEW_TESTS + "::"

WS_SUITES = [
    NEW_TESTS,
    "tests/test_websocket_resume_continuity.py",
    "tests/test_websocket_training_stream.py",
    "tests/test_websocket_manager_extra.py",
    "tests/test_t2_websocket.py",
    "tests/test_websocket_bridge.py",
    "tests/test_websocket_replay_continuity.py",
    "tests/test_websocket_control_stream.py",
]

# Tests of the new file, by the short names the arms use.
RAISES = T + "test_a_socket_whose_broadcast_send_raises_is_closed_1011_and_the_others_are_untouched"
TIMES_OUT = T + "test_a_socket_whose_broadcast_send_times_out_is_closed_1011"
INFO = T + "test_a_dropped_socket_is_logged_at_info_not_warning"
GONE = T + "test_a_socket_whose_transport_is_gone_is_dropped_without_a_close_attempt"
SERVER_CLOSED = T + "test_a_socket_the_server_already_closed_is_not_closed_again"
PEER_LEFT = T + "test_a_socket_whose_peer_has_disconnected_is_not_closed"
OVERLAP = T + "test_overlapping_broadcasts_that_both_drop_a_socket_close_it_once"
FORGOTTEN_FIRST = T + "test_no_socket_is_closed_before_the_broadcast_has_forgotten_it"
SLOW_CLOSE = T + "test_a_slow_close_holds_the_broadcast_at_most_the_send_timeout_and_is_not_cancelled"
CONCURRENT = T + "test_the_closes_of_one_broadcast_run_concurrently"
ONE_WAIT = T + "test_the_broadcast_waits_once_for_all_its_closes_for_one_send_timeout"
SLOT_ONCE = T + "test_a_dropped_sockets_per_ip_slot_is_released_once"
CLOSE_FAILS = T + "test_a_close_that_fails_is_retrieved_and_logged_at_debug"
RESUME = T + "test_a_dropped_client_is_closed_and_a_resume_replays_the_frame_it_missed"
DRAINS = T + "test_after_the_managers_close_the_receive_loop_drains_until_the_disconnect"
BEFORE_LOOP = T + "test_a_socket_closed_before_the_receive_loop_starts_is_drained_not_read"
LATE_PONG = T + "test_a_late_pong_after_the_heartbeat_close_does_not_end_the_handler_with_an_error"
PEER_THERE = T + "test_a_disconnect_while_the_peer_is_still_there_leaves_the_close_in_flight"
PEER_GONE = T + "test_a_close_still_pending_when_the_peer_has_gone_is_cancelled_and_released"

SKIP_CHECK = "            if ws in self._closing or _is_closed(ws):\n"
DROP_FORGET = "        for ws in sockets:\n            await self.disconnect(ws)\n"
FORGET_THEN_CLOSE = DROP_FORGET + "        closes = []\n"
LOG_LINE = '        logger.info("Broadcast of seq %s failed'
WAIT = "await asyncio.wait(closes, timeout=self._send_timeout_seconds)"
IS_CLOSED = 'return WebSocketState.DISCONNECTED in (getattr(websocket, "application_state", None), getattr(websocket, "client_state", None))'
LOOP_STATE = '            if getattr(websocket, "application_state", None) is WebSocketState.DISCONNECTED:\n'
LOOP_CHECK = LOOP_STATE + "                await _drain_until_disconnect(websocket)\n                return\n            raw = await websocket.receive_text()\n"
DRAIN_CALL = "                await _drain_until_disconnect(websocket)\n                return\n"
DRAIN_RECEIVE = "        message = await websocket.receive()\n"
DRAIN_TEST = '        if message.get("type") == "websocket.disconnect":\n'
RETRIEVE = "        if not closing.cancelled() and closing.exception() is not None:\n"
PEER_GONE_GUARD = '        if closing is not None and getattr(websocket, "client_state", None) is WebSocketState.DISCONNECTED:\n'
CHUNK_LOOP = "        for sub_message in self._maybe_chunk_message(message, quiet=not self._active_connections):\n            enriched = self._assign_seq_and_buffer(sub_message)\n"

#: (arm, file, [(old, new), ...], named tests -- any one failing kills the arm -- or the reason it survives)
ARMS: list[tuple[str, str, list[tuple[str, str]], list[str] | str]] = [
    # --- round 1's fifteen arms -------------------------------------------------------------------------------------
    ("r1_no_close", MANAGER, [(SKIP_CHECK, "            if 1:\n")], [RAISES, RESUME]),
    ("r1_close_code_1001", MANAGER, [("_BROADCAST_DROP_CLOSE_CODE = 1011", "_BROADCAST_DROP_CLOSE_CODE = 1001")], [RAISES]),
    ("r1_close_reason_empty", MANAGER, [("reason=_BROADCAST_DROP_CLOSE_REASON)", 'reason="")')], [RAISES]),
    ("r1_no_already_closed_check", MANAGER, [(SKIP_CHECK, "            if ws in self._closing:\n")], [SERVER_CLOSED, GONE, PEER_LEFT]),
    ("r1_no_client_state_check", MANAGER, [('(getattr(websocket, "application_state", None), getattr(websocket, "client_state", None))', '(getattr(websocket, "application_state", None),)')], [PEER_LEFT]),
    ("r1_no_dedupe", MANAGER, [(SKIP_CHECK, "            if _is_closed(ws):\n")], [OVERLAP]),
    ("r1_unbounded_wait", MANAGER, [(WAIT, "await asyncio.wait(closes)")], [SLOW_CLOSE, ONE_WAIT]),
    ("r1_cancel_on_timeout", MANAGER, [(WAIT, "[c.cancel() for c in (await asyncio.wait(closes, timeout=self._send_timeout_seconds))[1]]")], [SLOW_CLOSE]),
    ("r1_sequential_waits", MANAGER, [("            closes.append(closing)\n", "            await asyncio.wait({closing}, timeout=self._send_timeout_seconds)\n")], [CONCURRENT, ONE_WAIT]),
    ("r1_close_before_forget", MANAGER, [(FORGET_THEN_CLOSE, "        closes = []\n"), (LOG_LINE, DROP_FORGET + LOG_LINE)], [FORGOTTEN_FIRST]),
    ("r1_close_not_released", MANAGER, [("        self._closing.pop(websocket, None)\n", "        self._closing.get(websocket)\n")], [SLOW_CLOSE, RAISES]),
    ("r1_close_outcome_not_retrieved", MANAGER, [(RETRIEVE, "        if not closing.cancelled() and 0:\n")], [CLOSE_FAILS]),
    ("r1_drop_logged_at_warning", MANAGER, [(LOG_LINE, '        logger.warning("Broadcast of seq %s failed')], [INFO, TIMES_OUT]),
    ("r1_no_drain_check", STREAM, [(LOOP_STATE, "            if 0:\n")], [DRAINS, LATE_PONG]),
    ("r1_drain_returns_on_first_frame", STREAM, [(DRAIN_TEST, "        if 1:\n")], [DRAINS, LATE_PONG]),
    # --- the round-1 code validator's twenty-two mutants -------------------------------------------------------------
    ("v_slot_released_on_every_disconnect", MANAGER, [("meta = self._connection_meta.pop(websocket, None)", "meta = self._connection_meta.get(websocket)")], [SLOT_ONCE]),
    (
        "v_drop_keeps_slot_until_handler",
        MANAGER,
        [(DROP_FORGET, "        async with self._lock:\n            for ws in sockets:\n                self._active_connections.discard(ws)\n")],
        "by design: this is the alternative the owner has not ruled on (hold the connection and per-IP slots until the handler's own disconnect). The slot test asserts end states only, so that neither timing is locked in.",
    ),
    ("v_closed_socket_not_forgotten", MANAGER, [(DROP_FORGET, "        for ws in sockets:\n            if not _is_closed(ws):\n                await self.disconnect(ws)\n")], [GONE, SERVER_CLOSED, PEER_LEFT]),
    ("v_closing_recorded_after_yield", MANAGER, [("            closing = asyncio.create_task(self._close_dropped(ws))\n", "            await asyncio.sleep(0)\n            closing = asyncio.create_task(self._close_dropped(ws))\n")], [OVERLAP]),
    ("v_closing_not_recorded", MANAGER, [("            self._closing[ws] = closing\n", "")], [SLOW_CLOSE, OVERLAP]),
    ("v_is_closed_client_side_only", MANAGER, [(IS_CLOSED, 'return getattr(websocket, "client_state", None) is WebSocketState.DISCONNECTED')], [SERVER_CLOSED, GONE]),
    ("v_is_closed_app_side_only", MANAGER, [(IS_CLOSED, 'return getattr(websocket, "application_state", None) is WebSocketState.DISCONNECTED')], [PEER_LEFT]),
    ("v_only_first_failed_socket_closed", MANAGER, [("        closes = []\n        for ws in sockets:\n", "        closes = []\n        for ws in sockets[:1]:\n")], [CONCURRENT, ONE_WAIT]),
    ("v_wait_scaled_by_close_count", MANAGER, [(WAIT, "await asyncio.wait(closes, timeout=self._send_timeout_seconds * len(closes))")], [ONE_WAIT]),
    ("v_wait_first_completed", MANAGER, [(WAIT, "await asyncio.wait(closes, timeout=self._send_timeout_seconds, return_when=asyncio.FIRST_COMPLETED)")], [SLOW_CLOSE, ONE_WAIT]),
    ("v_no_wait_for_closes", MANAGER, [(WAIT, "await asyncio.sleep(0)")], [RAISES, CLOSE_FAILS, CONCURRENT, SLOW_CLOSE, ONE_WAIT]),
    ("v_wait_ten_send_timeouts", MANAGER, [(WAIT, "await asyncio.wait(closes, timeout=self._send_timeout_seconds * 10)")], [SLOW_CLOSE, ONE_WAIT]),
    ("v_close_awaited_inline_unbounded", MANAGER, [("        if closes:\n            " + WAIT + "\n", "        for closing in closes:\n            await asyncio.gather(closing, return_exceptions=True)\n")], [SLOW_CLOSE, ONE_WAIT]),
    ("v_close_exception_not_retrieved", MANAGER, [(RETRIEVE, "        if closing.cancelled():\n")], [CLOSE_FAILS]),
    (
        "v_drop_after_last_chunk",
        MANAGER,
        [(CHUNK_LOOP + "            disconnected = []\n", "        disconnected = []\n" + CHUNK_LOOP)],
        "equivalent on a real socket: the list of failed sockets is no longer reset per chunk, so a later chunk's step hands _drop a socket it has already forgotten and is closing or has closed, which _drop skips. The one difference is a repeated INFO line. The per-chunk loop is main's and no test of a chunked broadcast with a failing socket exists.",
    ),
    ("v_recv_loop_checks_client_state", STREAM, [('if getattr(websocket, "application_state", None) is WebSocketState.DISCONNECTED:', 'if getattr(websocket, "client_state", None) is WebSocketState.DISCONNECTED:')], [DRAINS, LATE_PONG, BEFORE_LOOP]),
    ("v_recv_loop_continues_after_drain", STREAM, [(DRAIN_CALL, "                await _drain_until_disconnect(websocket)\n                continue\n")], [DRAINS, LATE_PONG, BEFORE_LOOP]),
    ("v_drain_uses_receive_text", STREAM, [(DRAIN_RECEIVE, '        message = {"type": "websocket.receive", "text": await websocket.receive_text()}\n')], [DRAINS, LATE_PONG, BEFORE_LOOP]),
    (
        "v_drain_swallows_runtime_error",
        STREAM,
        [(DRAIN_RECEIVE, "        try:\n            message = await websocket.receive()\n        except RuntimeError:\n            return\n")],
        "equivalent: Starlette's receive() raises RuntimeError only after a disconnect has been received, and the drain returns on that disconnect, so the added handler is unreachable.",
    ),
    ("v_closed_check_only_after_a_receive", STREAM, [(LOOP_CHECK, "            raw = await websocket.receive_text()\n" + LOOP_STATE + DRAIN_CALL)], [BEFORE_LOOP]),
    ("v_drain_returns_on_any_message", STREAM, [(DRAIN_TEST + "            return\n", "        return\n")], [DRAINS, LATE_PONG]),
    ("v_return_without_drain", STREAM, [(DRAIN_CALL, "                return\n")], [DRAINS, LATE_PONG, BEFORE_LOOP]),
    # --- this round's own ------------------------------------------------------------------------------------------
    # The smallest breach of the bound: twice the send timeout. It must fail the test NAMED for the bound.
    ("r2_wait_two_send_timeouts", MANAGER, [(WAIT, "await asyncio.wait(closes, timeout=self._send_timeout_seconds * 2)")], [SLOW_CLOSE]),
    # The slot is never released by the handler's own disconnect path when the broadcast forgot the socket first.
    ("r2_slot_never_released", MANAGER, [("                self._release_per_ip_slot(meta.get(\"source_ip\"))\n", "                self._per_ip_counts.get(meta.get(\"source_ip\"))\n")], [SLOT_ONCE, DRAINS, BEFORE_LOOP]),
    # Round 2's one code change: disconnect() cancels a close still pending once the peer has gone.
    ("r2_pending_close_kept_when_the_peer_has_gone", MANAGER, [("            closing.cancel()\n", "            closing.done()\n")], [PEER_GONE]),
    ("r2_pending_close_cancelled_on_any_disconnect", MANAGER, [(PEER_GONE_GUARD, "        if closing is not None:\n")], [PEER_THERE, OVERLAP]),
]

SPECIAL = ("control", "canary", "main")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build(tree: Path, arms_dir: Path, arm: str, rel: str | None, edits: list[tuple[str, str]], main_src: Path) -> tuple[Path, str | None]:
    dest = arms_dir / arm
    if dest.exists():
        shutil.rmtree(dest)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(tree / "juniper-service-core" / "juniper_service_core", dest / "juniper_service_core", ignore=ignore)
    shutil.copytree(tree / "juniper-service-core" / "tests", dest / "tests", ignore=ignore)
    if arm == "main":
        shutil.copyfile(main_src / "manager.py", dest / MANAGER)
        shutil.copyfile(main_src / "training_stream.py", dest / STREAM)
    elif arm == "canary":
        path = dest / MANAGER
        path.write_text('raise ImportError("N4_R2_MUTATION_CANARY")\n' + path.read_text(encoding="utf-8"), encoding="utf-8")
    elif rel is not None:
        path = dest / rel
        text = path.read_text(encoding="utf-8")
        for old, new in edits:
            if text.count(old) != 1:
                return dest, f"expected exactly one occurrence of {old!r} in {rel}, found {text.count(old)}"
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
    stale = sorted(str(p) for p in dest.rglob("__pycache__"))
    return dest, (f"stale bytecode directories {stale}" if stale else None)


def _run(tree: Path, out: Path, python: str, dest: Path, arm: str) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tree / "juniper-model-core")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cfg = tree / "juniper-service-core" / "pyproject.toml"
    log = out / "logs" / f"{arm}.log"
    basetemp = out / "bt" / arm
    cmd = [python, "-m", "pytest", "-c", str(cfg), "--rootdir", str(dest), "-p", "no:cacheprovider", f"--basetemp={basetemp}", "-o", "addopts=-ra -q --strict-markers -p no:dash -p no:playwright", *WS_SUITES]
    with log.open("w", encoding="utf-8") as handle:
        rc = subprocess.run(cmd, cwd=dest, env=env, stdout=handle, stderr=subprocess.STDOUT, timeout=1200, check=False).returncode
    shutil.rmtree(basetemp, ignore_errors=True)
    text = log.read_text(encoding="utf-8")
    failed = sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+)", text, flags=re.MULTILINE)))
    tail = [line for line in text.splitlines() if re.search(r"\d+ (passed|failed|error)", line)]
    return {"exit": rc, "failed": failed, "summary": tail[-1] if tail else None, "log": str(log)}


def _judge(arm: str, expectation: list[str] | str, error: str | None, run: dict) -> dict:
    row = {"arm": arm, **run}
    if error is not None:
        return {**row, "verdict": "ERROR", "error": error, "as_expected": False}
    if isinstance(expectation, str):
        survived = run["exit"] == 0
        return {**row, "verdict": "survived" if survived else "killed", "expected": "survives", "why_it_survives": expectation, "as_expected": survived}
    hits = sorted(name for name in run["failed"] if name in expectation)
    return {**row, "verdict": "killed" if hits else "survived", "expected": "killed", "named_failures": hits, "as_expected": bool(hits)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python", required=True)
    args = parser.parse_args()
    tree, out = args.tree.resolve(), args.out.resolve()
    (out / "logs").mkdir(parents=True, exist_ok=True)
    (out / "bt").mkdir(parents=True, exist_ok=True)
    main_src = out / "main_src"
    main_src.mkdir(parents=True, exist_ok=True)
    for name in ("manager.py", "training_stream.py"):
        blob = subprocess.run(["git", "show", f"origin/main:juniper-service-core/juniper_service_core/websocket/{name}"], cwd=tree, capture_output=True, check=True).stdout
        (main_src / name).write_bytes(blob)
    sources = [tree / "juniper-service-core" / MANAGER, tree / "juniper-service-core" / STREAM, tree / "juniper-service-core" / NEW_TESTS]
    before = {str(p.relative_to(tree)): _sha256(p) for p in sources}
    arms_dir = out / "arms"
    arms_dir.mkdir(parents=True, exist_ok=True)

    plan: list[tuple[str, str | None, list[tuple[str, str]], list[str] | str]] = [(name, None, [], []) for name in SPECIAL] + ARMS
    built = [(arm, expectation, *_build(tree, arms_dir, arm, rel, edits, main_src)) for arm, rel, edits, expectation in plan]
    with ThreadPoolExecutor(max_workers=4) as pool:
        runs = list(pool.map(lambda item: _run(tree, out, args.python, item[2], item[0]), built))
    after = {str(p.relative_to(tree)): _sha256(p) for p in sources}
    shutil.rmtree(arms_dir, ignore_errors=True)
    shutil.rmtree(out / "bt", ignore_errors=True)

    special = {arm: run for (arm, _, _, _), run in zip(built, runs, strict=True) if arm in SPECIAL}
    rows = [_judge(arm, expectation, error, run) for (arm, expectation, _, error), run in zip(built, runs, strict=True) if arm not in SPECIAL]
    new_file_failures_on_main = sorted(name for name in special["main"]["failed"] if name.startswith(T))
    canary_ok = special["canary"]["exit"] != 0 and len(special["canary"]["failed"]) == len(WS_SUITES)
    verdict = {
        "arms": len(rows),
        "killed": sum(1 for row in rows if row["verdict"] == "killed"),
        "survived": sorted(row["arm"] for row in rows if row["verdict"] == "survived"),
        "errors": sorted(row["arm"] for row in rows if row["verdict"] == "ERROR"),
        "all_as_expected": all(row["as_expected"] for row in rows),
        "control_passes": special["control"]["exit"] == 0,
        "control_summary": special["control"]["summary"],
        "canary_fails_every_suite": canary_ok,
        "new_file_tests_failing_on_main": len(new_file_failures_on_main),
        "main_summary": special["main"]["summary"],
        "tree_unchanged": before == after,
    }
    record = {"python": args.python, "suites": WS_SUITES, "tree_sha256_before": before, "tree_sha256_after": after, "verdict": verdict, "control": special["control"], "canary": special["canary"], "main": {**special["main"], "new_file_failures": new_file_failures_on_main}, "arms": rows}
    (out / "mutants.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(verdict, indent=1))
    for row in rows:
        print(f"{row['arm']:38s} {row['verdict']:9s} expected={row.get('expected', '?'):9s} exit={row['exit']} {row['summary']}")
    ok = verdict["all_as_expected"] and verdict["control_passes"] and canary_ok and verdict["tree_unchanged"] and not verdict["errors"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
