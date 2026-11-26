#!/usr/bin/env python3
"""
Mutation check for ruling 23's "WebSocket gaps beside N-4": each fixed site restored to main's behaviour, one arm each.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, builder r23w: test-efficacy evidence for the three fixes)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23);
         util/ad-hoc/2026-11-11_flood4r2_n4-r2_mutation_check.py (N-4's, whose mechanics this follows)

Usage: python3 <this file> --tree <tree root> --out <scratch dir> --python <interpreter>

The tree is never modified: the sha256 of the two fixed modules and the new test file are recorded before and after
(and the run fails if they differ). Each arm copies the tree's juniper-service-core/juniper_service_core and
juniper-service-core/tests (no __pycache__) into <out>/arms/<arm>/, applies exact-text replacements (each old string
must occur exactly once, or the arm is an ERROR) and runs the new test file and N-4's
(tests/test_websocket_broadcast_drop_close.py) there with -c <tree>'s pyproject.toml,
PYTHONDONTWRITEBYTECODE=1 and PYTHONPATH = the tree's juniper-model-core only; tests/ is a package, so the copy's
root comes first on sys.path. The canary arm (the copy's manager.py raises on import) must fail, which proves the
copy is what runs; the control arm (no change) must pass. An arm is KILLED when at least one test it names fails.
At most four arms run at once. The arm copies are removed afterwards; logs and mutants.json stay in <out>.
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
CONTROL = "juniper_service_core/websocket/control_stream.py"
NEW = "tests/test_websocket_unsendable_late_frame_and_slot.py"
N4 = "tests/test_websocket_broadcast_drop_close.py"
T = NEW + "::"
T4 = N4 + "::"
WATCHED = [MANAGER, CONTROL, NEW]
#: The forget block of the fixed _drop (moved by the re-expressed N-4 arm below).
_FORGET = "        async with self._lock:\n            for ws in sockets:\n                # One its handler has disconnected already is gone, slots and all; never resurrect it.\n                if ws in self._active_connections:\n                    self._active_connections.discard(ws)\n                    self._dropped.add(ws)\n"
_LOG = "        # INFO, as a failed send is logged elsewhere"

_REFUSED = [T + f"test_an_unsendable_broadcast_is_refused_before_it_takes_a_seq_and_closes_no_socket[{i}]" for i in ("datetime", "lone-surrogate", "circular")]
_REJECT = [T + f"test_a_rejected_frame_whose_ack_crosses_the_heartbeat_close_is_not_closed_twice[{i}]" for i in ("oversize", "malformed-json", "non-object")]

#: (arm, file, [(old, new)], tests that must fail -- at least one)
ARMS: list[tuple[str, str, list[tuple[str, str]], list[str]]] = [
    ("a1_no_refusal", MANAGER, [("        if self._refuse_unsendable(message, frames):\n            return\n", "")], _REFUSED + [T + "test_a_resume_across_a_refused_broadcast_is_continuous"]),
    ("a2_refuse_before_chunking_as_cascor", MANAGER, [("error = next((err for err in map(_transport_error, frames) if err is not None), None)", "error = _transport_error(message)")], [T + "test_an_oversized_message_with_the_same_value_is_still_delivered_byte_for_byte"]),
    ("a3_no_seq_placeholders", MANAGER, [('json.dumps({**frame, "seq": 0, "emitted_at_monotonic": 0.0}, ', "json.dumps(frame, ")], [T + "test_a_message_whose_own_seq_field_the_broadcast_overwrites_is_still_delivered"]),
    ("a4_no_utf8_encode", MANAGER, [('ensure_ascii=False).encode("utf-8")', "ensure_ascii=False)")], [_REFUSED[1]]),
    ("a5_logs_the_value", MANAGER, [("            type(error).__name__,\n        )", '            f"{type(error).__name__}: {error}",\n        )')], [T + "test_a_refused_broadcast_is_logged_at_error_without_its_value"]),
    ("a6_not_counted", MANAGER, [("            self._unserializable_messages_total += 1\n        msg_type", "            pass\n        msg_type")], _REFUSED),
    ("a7_refused_after_the_seq", MANAGER, [("        frames = self._maybe_chunk_message(message, quiet=not self._active_connections)\n        if self._refuse_unsendable(message, frames):\n            return\n", "        frames = self._maybe_chunk_message(message, quiet=not self._active_connections)\n        if self._refuse_unsendable(message, frames):\n            self._assign_seq_and_buffer(frames[0])\n            return\n")], _REFUSED),
    ("b1_no_check_before_receive", CONTROL, [("    while True:\n        if _closed_by_server(websocket):\n            await _drain_until_disconnect(websocket)\n            return\n        try:", "    while True:\n        try:")], [T + "test_a_command_still_running_when_the_heartbeat_closes_is_not_acknowledged"]),
    ("b2_no_check_after_receive", CONTROL, [("        if _closed_by_server(websocket):\n            continue  # a frame that completed the receive in progress when the server closed: drain, not dispatch\n", "")], [T + "test_a_late_command_after_the_heartbeat_close_is_neither_executed_nor_acknowledged"]),
    ("b3_no_check_at_the_idle_timeout", CONTROL, [("            if _closed_by_server(websocket):\n                continue  # the heartbeat closed it while this receive waited: drain\n", "")], [T + "test_the_idle_timeout_after_a_heartbeat_close_does_not_close_again"]),
    ("b4_ack_sent_after_the_close", CONTROL, [("    if _closed_by_server(websocket):\n        return False\n    await websocket.send_json(message)", "    await websocket.send_json(message)")], [T + "test_a_command_still_running_when_the_heartbeat_closes_is_not_acknowledged"]),
    ("b5_reject_closes_regardless", CONTROL, [("    if _closed_by_server(websocket):\n        await _drain_until_disconnect(websocket)\n        return\n    await websocket.close(code=code, reason=reason)", "    await websocket.close(code=code, reason=reason)")], _REJECT),
    ("b6_oversize_site_as_main", CONTROL, [('            await _reject_and_close(websocket, "Message too large", 1009, "Message too large")', '            await websocket.send_json(create_control_ack_message("unknown", "error", error="Message too large"))\n            await websocket.close(code=1009, reason="Message too large")')], [_REJECT[0]]),
    ("b7_malformed_site_as_main", CONTROL, [('            await _reject_and_close(websocket, "Invalid JSON", 1003, "Malformed JSON")', '            await websocket.send_json(create_control_ack_message("unknown", "error", error="Invalid JSON"))\n            await websocket.close(code=1003, reason="Malformed JSON")')], [_REJECT[1]]),
    ("b8_non_object_site_as_main", CONTROL, [('            await _reject_and_close(websocket, "Invalid control message", 1003, "Malformed JSON")', '            await websocket.send_json(create_control_ack_message("unknown", "error", error="Invalid control message"))\n            await websocket.close(code=1003, reason="Malformed JSON")')], [_REJECT[2]]),
    ("b9_drain_returns_at_once", CONTROL, [('    while getattr(websocket, "client_state", None) is not WebSocketState.DISCONNECTED:\n        message = await websocket.receive()', "    while 0:\n        message = await websocket.receive()")], [T + "test_a_late_pong_after_the_heartbeat_close_does_not_end_the_control_handler_with_an_error"]),
    ("b10_drain_ignores_a_received_disconnect", CONTROL, [('    while getattr(websocket, "client_state", None) is not WebSocketState.DISCONNECTED:\n        message = await websocket.receive()', "    while 1:\n        message = await websocket.receive()")], [T + "test_the_control_drain_returns_at_once_when_the_disconnect_was_already_received"]),
    ("c1_drop_releases_the_slots_as_main", MANAGER, [("        async with self._lock:\n            for ws in sockets:\n                # One its handler has disconnected already is gone, slots and all; never resurrect it.\n                if ws in self._active_connections:\n                    self._active_connections.discard(ws)\n                    self._dropped.add(ws)\n", "        for ws in sockets:\n            await self.disconnect(ws)\n")], [T + "test_a_dropped_socket_keeps_its_per_ip_slot_until_its_handler_returns", T + "test_a_dropped_socket_keeps_its_connection_slot_until_its_handler_returns"]),
    ("c2_connect_pending_cap_ignores_dropped", MANAGER, [("            ``True`` if accepted, ``False`` if a connection limit was reached.\n        \"\"\"\n        async with self._lock:\n            total = len(self._active_connections) + len(self._pending_connections) + len(self._dropped)", "            ``True`` if accepted, ``False`` if a connection limit was reached.\n        \"\"\"\n        async with self._lock:\n            total = len(self._active_connections) + len(self._pending_connections)")], [T + "test_a_dropped_socket_keeps_its_connection_slot_until_its_handler_returns"]),
    ("c3_connect_cap_ignores_dropped", MANAGER, [("            ``True`` if connected, ``False`` if a connection limit was reached.\n        \"\"\"\n        async with self._lock:\n            total = len(self._active_connections) + len(self._pending_connections) + len(self._dropped)", "            ``True`` if connected, ``False`` if a connection limit was reached.\n        \"\"\"\n        async with self._lock:\n            total = len(self._active_connections) + len(self._pending_connections)")], [T + "test_a_dropped_socket_registered_with_connect_keeps_its_connection_slot_until_disconnected"]),
    ("c4_disconnect_keeps_it_dropped", MANAGER, [("            self._dropped.discard(websocket)\n", "")], [T + "test_every_count_agrees_with_what_is_open_while_a_dropped_socket_closes", T + "test_a_dropped_socket_keeps_its_connection_slot_until_its_handler_returns"]),
    ("c5_drop_without_the_still_active_guard", MANAGER, [("                if ws in self._active_connections:\n", "                if 1:\n")], [T + "test_a_socket_disconnected_before_its_drop_is_not_held"]),
    ("c6_close_all_keeps_dropped", MANAGER, [("            self._dropped.clear()\n", "")], [T + "test_close_all_forgets_a_dropped_socket"]),
    ("c7_established_ignores_dropped", MANAGER, [('"connections": self.connection_count + len(self._pending_connections) + len(self._dropped),', '"connections": self.connection_count + len(self._pending_connections),')], [T + "test_every_count_agrees_with_what_is_open_while_a_dropped_socket_closes"]),
    # --- N-4's arms whose target lines this change rewrote, re-expressed on the new code (N-4's own helper reports them
    # as not applicable on this tree); v_slot_released_on_every_disconnect applies unchanged but no N-4 test sees it now
    # that a dropped socket passes through disconnect() once, so the new control is named for it.
    ("n4_r1_close_before_forget", MANAGER, [(_FORGET + "        closes = []\n", "        closes = []\n"), (_LOG, _FORGET + _LOG)], [T4 + "test_no_socket_is_closed_before_the_broadcast_has_forgotten_it"]),
    ("n4_v_closed_socket_not_forgotten", MANAGER, [("                if ws in self._active_connections:\n", "                if ws in self._active_connections and not _is_closed(ws):\n")], [T4 + "test_a_socket_whose_transport_is_gone_is_dropped_without_a_close_attempt", T4 + "test_a_socket_the_server_already_closed_is_not_closed_again", T4 + "test_a_socket_whose_peer_has_disconnected_is_not_closed"]),
    ("n4_v_slot_released_on_every_disconnect", MANAGER, [("meta = self._connection_meta.pop(websocket, None)", "meta = self._connection_meta.get(websocket)")], [T + "test_a_dropped_socket_releases_its_slots_once_however_often_it_is_disconnected"]),
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build(tree: Path, arms_dir: Path, arm: str, rel: str | None, edits: list[tuple[str, str]]) -> tuple[Path, str | None]:
    dest = arms_dir / arm
    if dest.exists():
        shutil.rmtree(dest)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(tree / "juniper-service-core" / "juniper_service_core", dest / "juniper_service_core", ignore=ignore)
    shutil.copytree(tree / "juniper-service-core" / "tests", dest / "tests", ignore=ignore)
    if arm == "canary":
        path = dest / MANAGER
        path.write_text(path.read_text(encoding="utf-8") + '\nraise ImportError("R23W_MUTATION_CANARY")\n', encoding="utf-8")
    elif rel is not None:
        path = dest / rel
        text = path.read_text(encoding="utf-8")
        for old, new in edits:
            if text.count(old) != 1:
                return dest, f"expected exactly one occurrence of {old!r} in {rel}, found {text.count(old)}"
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
    return dest, None


def _run(tree: Path, out: Path, python: str, dest: Path, arm: str) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tree / "juniper-model-core")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cfg = tree / "juniper-service-core" / "pyproject.toml"
    log = out / "logs" / f"{arm}.log"
    basetemp = out / "bt" / arm
    cmd = [python, "-m", "pytest", "-c", str(cfg), "--rootdir", str(dest), "-p", "no:cacheprovider", f"--basetemp={basetemp}", "-o", "addopts=-ra -q --strict-markers", NEW, N4]
    with log.open("w", encoding="utf-8") as handle:
        rc = subprocess.run(cmd, cwd=dest, env=env, stdout=handle, stderr=subprocess.STDOUT, timeout=900, check=False).returncode
    shutil.rmtree(basetemp, ignore_errors=True)
    text = log.read_text(encoding="utf-8")
    failed = sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+)", text, flags=re.MULTILINE)))
    tail = [line for line in text.splitlines() if re.search(r"\d+ (passed|failed|error)", line)]
    return {"exit": rc, "failed": failed, "summary": tail[-1] if tail else None, "log": str(log)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python", required=True)
    args = parser.parse_args()
    tree, out = args.tree.resolve(), args.out.resolve()
    (out / "logs").mkdir(parents=True, exist_ok=True)
    arms_dir = out / "arms"
    pkg = tree / "juniper-service-core"
    before = {rel: _sha256(pkg / rel) for rel in WATCHED}
    plan = [("canary", None, [], "fails"), ("control", None, [], "passes")] + [(a, f, e, k) for a, f, e, k in ARMS]
    rows: list[dict] = []
    try:

        def one(item):
            arm, rel, edits, expect = item
            dest, error = _build(tree, arms_dir, arm, rel, edits)
            run = _run(tree, out, args.python, dest, arm) if error is None else {"exit": None, "failed": [], "summary": None}
            row = {"arm": arm, "file": rel, **run}
            if error is not None:
                return {**row, "verdict": "ERROR", "error": error, "as_expected": False}
            if expect == "fails":
                return {**row, "verdict": "canary failed" if run["exit"] != 0 else "canary PASSED", "as_expected": run["exit"] != 0 and "R23W_MUTATION_CANARY" in Path(run["log"]).read_text(encoding="utf-8")}
            if expect == "passes":
                return {**row, "verdict": "control passed" if run["exit"] == 0 else "control FAILED", "as_expected": run["exit"] == 0}
            hits = sorted(name for name in run["failed"] if name in expect)
            return {**row, "verdict": "killed" if hits else "SURVIVED", "named_failures": hits, "as_expected": bool(hits)}

        with ThreadPoolExecutor(max_workers=4) as pool:
            rows = list(pool.map(one, plan))
    finally:
        after = {rel: _sha256(pkg / rel) for rel in WATCHED}
        shutil.rmtree(arms_dir, ignore_errors=True)
    result = {
        "python": args.python,
        "tree_sha256_before": before,
        "tree_sha256_after": after,
        "tree_unchanged": before == after,
        "arms": len(ARMS),
        "killed": sum(1 for r in rows if r.get("verdict") == "killed"),
        "all_as_expected": all(r.get("as_expected") for r in rows) and before == after,
        "rows": rows,
    }
    (out / "mutants.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    for r in rows:
        print(f"{r['arm']:45s} {r['verdict']:16s} {r.get('summary')}")
    print(f"arms {result['arms']}, killed {result['killed']}, tree unchanged {result['tree_unchanged']}, all as expected {result['all_as_expected']}")
    return 0 if result["all_as_expected"] else 1


if __name__ == "__main__":
    sys.exit(main())
