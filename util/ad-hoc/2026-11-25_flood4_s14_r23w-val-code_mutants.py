"""
Code lens mutants of ruling 23's fix (juniper-service-core WebSocket tier): each in a scratch copy of the sub-package.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

For each mutant: copy SRC (the assembled juniper-service-core directory) to WORK/<id>/juniper-service-core, apply
one exact old->new replacement (old must occur exactly once), run the carrier's new test file first, and, when it
survives that, the whole service-core suite (both with -x). A canary mutant must be killed and the unmutated copy
must pass. SRC's files are hashed before and after: the run never writes to SRC.

Usage:
  python <this file> --src SRC_SC_DIR --work WORK_DIR --python PY --runenv RUNENV --out OUT.json [--jobs 4] [--only ID,ID]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import time

M = "juniper_service_core/websocket/manager.py"
C = "juniper_service_core/websocket/control_stream.py"
NEW = "tests/test_websocket_unsendable_late_frame_and_slot.py"

MUTANTS = [
    # --- (a) the refusal ---
    ("a1_no_ensure_ascii_false", M, 'json.dumps({**frame, "seq": 0, "emitted_at_monotonic": 0.0}, separators=(",", ":"), ensure_ascii=False).encode("utf-8")', 'json.dumps({**frame, "seq": 0, "emitted_at_monotonic": 0.0}, separators=(",", ":")).encode("utf-8")'),
    ("a2_no_utf8_encode", M, 'ensure_ascii=False).encode("utf-8")\n    except Exception', "ensure_ascii=False)\n    except Exception"),
    ("a3_seq_not_overridden", M, 'json.dumps({**frame, "seq": 0, "emitted_at_monotonic": 0.0}, separators', "json.dumps(frame, separators"),
    ("a4_refuse_before_chunking", M, "        frames = self._maybe_chunk_message(message, quiet=not self._active_connections)\n        if self._refuse_unsendable(message, frames):", "        if self._refuse_unsendable(message, [message]):\n            return\n        frames = self._maybe_chunk_message(message, quiet=not self._active_connections)\n        if False:"),
    ("a5_refuse_after_seq", M, "        if self._refuse_unsendable(message, frames):\n            return\n        for sub_message in frames:\n            enriched = self._assign_seq_and_buffer(sub_message)\n", "        for sub_message in frames:\n            enriched = self._assign_seq_and_buffer(sub_message)\n            if self._refuse_unsendable(message, [sub_message]):\n                return\n"),
    ("a6_no_count", M, "            self._unserializable_messages_total += 1\n", "            pass\n"),
    ("a7_log_exception_text", M, "            type(error).__name__,\n        )\n        return True", "            f'{type(error).__name__}: {error}',\n        )\n        return True"),
    ("a8_log_at_warning", M, "        logger.error(\n            \"Broadcast refused", "        logger.warning(\n            \"Broadcast refused"),
    ("a9_counted_as_send_failure", M, "            self._unserializable_messages_total += 1\n", "            self._unserializable_messages_total += 1\n            self._send_failures += 1\n"),
    ("a10_catch_only_typeerror", M, "    except Exception as exc:  # noqa: BLE001 - whatever is raised here is a property of the frame", "    except TypeError as exc:  # noqa: BLE001 - whatever is raised here is a property of the frame"),
    ("a11_check_first_frame_only", M, "map(_transport_error, frames)", "map(_transport_error, frames[:1])"),
    # --- (c) the slots ---
    ("c1_release_at_drop_as_main", M, "        async with self._lock:\n            for ws in sockets:\n                # One its handler has disconnected already is gone, slots and all; never resurrect it.\n                if ws in self._active_connections:\n                    self._active_connections.discard(ws)\n                    self._dropped.add(ws)\n", "        for ws in sockets:\n            await self.disconnect(ws)\n"),
    ("c2_drop_not_counted_globally", M, "                    self._dropped.add(ws)\n", "                    pass\n"),
    ("c3_resurrect_disconnected", M, "                if ws in self._active_connections:\n                    self._active_connections.discard(ws)\n                    self._dropped.add(ws)\n", "                self._active_connections.discard(ws)\n                self._dropped.add(ws)\n"),
    ("c4_connect_total_ignores_dropped", M, "        async with self._lock:\n            total = len(self._active_connections) + len(self._pending_connections) + len(self._dropped)\n            if total >= self._max_connections:\n                await websocket.close(code=1013, reason=\"Maximum connections reached\")\n                logger.warning(\"Connection rejected: limit of %d reached\", self._max_connections)\n                return False\n\n            source_ip = self._source_ip(websocket)\n            if not self._check_and_reserve_per_ip_slot(source_ip):\n                await websocket.close(code=1013, reason=\"Per-IP connection limit reached\")\n                logger.warning(\"Connection rejected: per-IP", "        async with self._lock:\n            total = len(self._active_connections) + len(self._pending_connections)\n            if total >= self._max_connections:\n                await websocket.close(code=1013, reason=\"Maximum connections reached\")\n                logger.warning(\"Connection rejected: limit of %d reached\", self._max_connections)\n                return False\n\n            source_ip = self._source_ip(websocket)\n            if not self._check_and_reserve_per_ip_slot(source_ip):\n                await websocket.close(code=1013, reason=\"Per-IP connection limit reached\")\n                logger.warning(\"Connection rejected: per-IP"),
    ("c5_pending_total_ignores_dropped", M, "        async with self._lock:\n            total = len(self._active_connections) + len(self._pending_connections) + len(self._dropped)\n            if total >= self._max_connections:\n                await websocket.close(code=1013, reason=\"Maximum connections reached\")\n                logger.warning(\"Connection rejected: limit of %d reached\", self._max_connections)\n                return False\n\n            source_ip = self._source_ip(websocket)\n            if not self._check_and_reserve_per_ip_slot(source_ip):\n                await websocket.close(code=1013, reason=\"Per-IP connection limit reached\")\n                logger.warning(\"Pending", "        async with self._lock:\n            total = len(self._active_connections) + len(self._pending_connections)\n            if total >= self._max_connections:\n                await websocket.close(code=1013, reason=\"Maximum connections reached\")\n                logger.warning(\"Connection rejected: limit of %d reached\", self._max_connections)\n                return False\n\n            source_ip = self._source_ip(websocket)\n            if not self._check_and_reserve_per_ip_slot(source_ip):\n                await websocket.close(code=1013, reason=\"Per-IP connection limit reached\")\n                logger.warning(\"Pending"),
    ("c6_disconnect_keeps_dropped", M, "            self._dropped.discard(websocket)\n            meta = self._connection_meta.pop(websocket, None)", "            meta = self._connection_meta.pop(websocket, None)"),
    ("c7_close_all_keeps_dropped", M, "            self._pending_connections.clear()\n            self._dropped.clear()\n", "            self._pending_connections.clear()\n"),
    ("c8_established_ignores_dropped", M, "self.connection_count + len(self._pending_connections) + len(self._dropped)", "self.connection_count + len(self._pending_connections)"),
    ("c9_stats_dropped_key_wrong", M, '"dropped_connections": len(self._dropped),', '"dropped_connections": 0,'),
    # --- (b) /ws/control ---
    ("b1_no_top_of_loop_check", C, "    while True:\n        if _closed_by_server(websocket):\n            await _drain_until_disconnect(websocket)\n            return\n        try:", "    while True:\n        try:"),
    ("b2_no_after_receive_check", C, "        if _closed_by_server(websocket):\n            continue  # a frame that completed", "        if False:\n            continue  # a frame that completed"),
    ("b3_no_idle_check", C, "            if _closed_by_server(websocket):\n                continue  # the heartbeat closed it while this receive waited: drain\n", ""),
    ("b4_send_unless_closed_always_sends", C, "    if _closed_by_server(websocket):\n        return False\n    await websocket.send_json(message)\n    return True", "    await websocket.send_json(message)\n    return True"),
    ("b5_reject_closes_twice", C, "    await _send_unless_closed(websocket, create_control_ack_message(\"unknown\", \"error\", error=error))\n    if _closed_by_server(websocket):\n        await _drain_until_disconnect(websocket)\n        return\n", "    await _send_unless_closed(websocket, create_control_ack_message(\"unknown\", \"error\", error=error))\n"),
    ("b6_drain_no_state_guard", C, "    while getattr(websocket, \"client_state\", None) is not WebSocketState.DISCONNECTED:\n        message = await websocket.receive()", "    while True:\n        message = await websocket.receive()"),
    ("b7_closed_by_server_reads_client_state", C, "    return getattr(websocket, \"application_state\", None) is WebSocketState.DISCONNECTED", "    return getattr(websocket, \"client_state\", None) is WebSocketState.DISCONNECTED"),
    ("b8_success_ack_unguarded", C, "        if not await _send_unless_closed(websocket, create_control_ack_message(command, \"success\", data=result, command_id=command_id)):\n            logger.info(", "        await websocket.send_json(create_control_ack_message(command, \"success\", data=result, command_id=command_id))\n        if False:\n            logger.info("),
    ("b9_value_error_ack_unguarded", C, "        await _send_unless_closed(websocket, create_control_ack_message(command, \"error\", error=str(exc), command_id=command_id))", "        await websocket.send_json(create_control_ack_message(command, \"error\", error=str(exc), command_id=command_id))"),
    ("b10_timeout_ack_unguarded", C, "        await _send_unless_closed(websocket, create_control_ack_message(command, \"error\", error=f\"Command timed out after {timeout}s\", command_id=command_id))", "        await websocket.send_json(create_control_ack_message(command, \"error\", error=f\"Command timed out after {timeout}s\", command_id=command_id))"),
    ("b11_exception_ack_unguarded", C, "        await _send_unless_closed(websocket, create_control_ack_message(command, \"error\", error=\"Command execution failed\", command_id=command_id))", "        await websocket.send_json(create_control_ack_message(command, \"error\", error=\"Command execution failed\", command_id=command_id))"),
    ("b12_drain_returns_at_once", C, "    while getattr(websocket, \"client_state\", None) is not WebSocketState.DISCONNECTED:\n        message = await websocket.receive()\n        if message.get(\"type\") == \"websocket.disconnect\":\n            return\n", "    return\n"),
    # --- canary ---
    ("canary_break_close_code", M, "_BROADCAST_DROP_CLOSE_CODE = 1011", "_BROADCAST_DROP_CLOSE_CODE = 1012"),
]


def tree_digest(root: pathlib.Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc"):
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def run_pytest(py: str, runenv: str, cwd: pathlib.Path, target: str, basetemp: pathlib.Path) -> tuple[int, str]:
    cmd = ["bash", runenv, py, "-m", "pytest", target, "-x", "-p", "no:cacheprovider", f"--basetemp={basetemp}"]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=900, check=False)
    first = ""
    for line in proc.stdout.splitlines():
        if line.startswith("FAILED") or line.startswith("ERROR"):
            first = line[:240]
            break
    if not first and proc.returncode not in (0,):
        first = (proc.stdout.strip().splitlines() or [""])[-1][:240]
    return proc.returncode, first


def one(mutant, args) -> dict:
    mid, rel, old, new = mutant
    work = args.work / mid
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(args.src, work / "juniper-service-core", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
    target = work / "juniper-service-core" / rel
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    rec = {"id": mid, "file": rel, "occurrences": count}
    if mid != "control_unmutated":
        if count != 1:
            rec["status"] = "INVALID (old text occurs %d times)" % count
            return rec
        target.write_text(text.replace(old, new, 1), encoding="utf-8")
    t0 = time.monotonic()
    rc_new, first_new = run_pytest(args.python, args.runenv, work, f"juniper-service-core/{NEW}", work / "bt_new")
    rec["new_file_exit"], rec["new_file_first_failure"] = rc_new, first_new
    if rc_new == 0:
        rc_all, first_all = run_pytest(args.python, args.runenv, work, "juniper-service-core/tests", work / "bt_all")
        rec["suite_exit"], rec["suite_first_failure"] = rc_all, first_all
        killed = rc_all != 0
        rec["killed_by"] = "suite (not the new file)" if killed else None
    else:
        killed = True
        rec["killed_by"] = "new file"
    rec["status"] = "KILLED" if killed else "SURVIVED"
    rec["wall_s"] = round(time.monotonic() - t0, 1)
    shutil.rmtree(work / "juniper-service-core", ignore_errors=True)
    return rec


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--src", required=True, type=pathlib.Path)
    parser.add_argument("--work", required=True, type=pathlib.Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--runenv", required=True)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    before = tree_digest(args.src)
    only = {x for x in args.only.split(",") if x}
    todo = [m for m in MUTANTS if not only or m[0] in only]
    todo.append(("control_unmutated", M, "", ""))
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.jobs, 4))) as pool:
        for rec in pool.map(lambda m: one(m, args), todo):
            results.append(rec)
            print(json.dumps(rec), flush=True)
    after = tree_digest(args.src)
    mutants = [r for r in results if r["id"] not in ("control_unmutated",) and not r["id"].startswith("canary")]
    summary = {
        "src_digest_before": before, "src_digest_after": after, "src_unchanged": before == after,
        "mutants": len(mutants), "killed": sum(r["status"] == "KILLED" for r in mutants),
        "survived": [r["id"] for r in mutants if r["status"] == "SURVIVED"],
        "invalid": [r["id"] for r in mutants if r["status"].startswith("INVALID")],
        "canary": next((r["status"] for r in results if r["id"].startswith("canary")), None),
        "control_unmutated": next((r["status"] for r in results if r["id"] == "control_unmutated"), None),
        "results": results,
    }
    args.out.write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
