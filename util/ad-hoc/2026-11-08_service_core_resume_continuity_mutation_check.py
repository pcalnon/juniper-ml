#!/usr/bin/env python3
"""
Mutation check: the juniper-service-core resume-continuity pins must FAIL on every reverted piece of the fix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (test-efficacy evidence)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-service-core/juniper_service_core/websocket/manager.py,
         juniper-service-core/juniper_service_core/websocket/training_stream.py,
         juniper-service-core/tests/test_websocket_resume_continuity.py,
         notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (its juniper-service-core
         ``resume_ok`` defect row: a broadcast with no socket active was never numbered, and one that
         landed during the replay reached the resuming client by neither path)

The fix has two halves. ``broadcast`` sequences and buffers a message with no socket active; and
``promote_to_active(..., replayed_through=...)`` sends whatever landed during the replay before the
socket goes live, while ``_handle_resume`` uses it and closes 1011 rather than leave a hole. Each arm
below reverts or breaks one piece, runs the three WebSocket suites, and requires the tests it names
to fail.

The checkout is never modified. Every arm copies the whole ``juniper-service-core`` sub-package
(package, tests and the ``pyproject.toml`` that holds the pytest config) into a scratch tree under
this repository's ``tmp/``, mutates the copy, and runs pytest on the copied tests. It has to be the
whole sub-package: ``tests/`` is a package, so pytest puts its parent first on ``sys.path``, and a
mutated package placed anywhere else would be shadowed by the checkout's. A canary run first proves
the point: the copy's ``manager.py`` raises on import, and the suites must fail with that message.
A signal or a hang therefore cannot leave a mutant behind; each run is bounded by a subprocess
timeout, and by ``--timeout`` per test when the interpreter has pytest-timeout.

The whole-file revert of ``training_stream.py`` reads it at ``PRE_FIX_REF``, the ``main`` commit
the fix was built on, so the arm still means "before the fix" once the fix is committed. An arm
whose anchor does not occur exactly once is an error ("measured nothing"), never a skip.
PYTHONDONTWRITEBYTECODE=1 and a copy that leaves out every ``__pycache__``, so no stale .pyc can
stand in for a mutant. pytest's exit status and summary are read directly (no pipe).

Usage:
    python3 util/ad-hoc/2026-11-08_service_core_resume_continuity_mutation_check.py [--python PY] [--json OUT] [--keep-trees]
Exit: 0 when the canary is seen, the unmutated copy passes before and after, and every arm fails
every test it names; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUBPACKAGE = "juniper-service-core"
MANAGER = "juniper_service_core/websocket/manager.py"
STREAM = "juniper_service_core/websocket/training_stream.py"
SUITES = (
    "tests/test_websocket_resume_continuity.py",
    "tests/test_websocket_training_stream.py",
    "tests/test_websocket_manager_extra.py",
)
#: The ``main`` commit the fix was built on: ``training_stream.py`` there is the pre-fix handler.
PRE_FIX_REF = "cef03a06528c1a26cfd6be499417af80f1f7f19f"
#: Arm ``new`` value meaning "the whole file as committed at PRE_FIX_REF", i.e. before the fix.
PRE_FIX_VERSION = object()
#: Scratch trees live here, in the repository's own gitignored tmp/ (Juniper convention), never in a system temp dir.
SCRATCH_ROOT = REPO / "tmp" / "service-core-resume-mutation"
RUN_TIMEOUT_S = 600
TEST_TIMEOUT_S = 120
CANARY = "resume-continuity mutation canary: the copied package is the one imported"

RC = "test_websocket_resume_continuity.py::"
TS = "test_websocket_training_stream.py::"
MX = "test_websocket_manager_extra.py::"
STRESS = RC + "test_resume_interleaved_with_broadcasts_delivers_every_seq_once_in_order["

NO_SOCKET_PINS = (
    RC + "test_a_broadcast_with_no_socket_connected_is_sequenced_and_buffered",
    RC + "test_resume_replays_what_was_broadcast_while_nobody_was_connected",
    RC + "test_a_broadcast_during_the_only_clients_pending_handshake_is_replayed",
    RC + "test_a_disabled_replay_buffer_still_sequences_but_buffers_nothing",
    RC + "test_with_nobody_connected_the_buffer_keeps_its_maxlen_and_an_evicted_resume_is_refused",
    RC + "test_a_chunked_broadcast_made_while_nobody_was_connected_is_replayed_whole",
    RC + "test_splitting_a_broadcast_nobody_receives_is_logged_at_debug_not_info",
    MX + "test_broadcast_without_connections_is_sequenced_and_buffered_but_not_sent",
)
DELIVERY_PINS = (
    RC + "test_a_broadcast_that_lands_while_the_replay_is_being_sent_reaches_the_resuming_client",
    RC + "test_a_broadcast_scheduled_during_a_yielding_replay_send_is_delivered",
    RC + "test_a_broadcast_while_the_resuming_socket_waits_for_the_manager_lock_is_not_lost",
    RC + "test_a_chunked_broadcast_that_lands_during_the_replay_arrives_whole_and_in_order",
)
EVICTED = RC + "test_a_resume_whose_catch_up_was_evicted_is_closed_not_promoted_over_the_gap"
REPLAY_SEND_FAILS = RC + "test_a_replay_frame_that_fails_to_send_ends_the_resume_instead_of_leaving_a_hole"
CATCH_UP_SEND_FAILS = RC + "test_a_catch_up_frame_that_fails_to_send_ends_the_resume_instead_of_leaving_a_hole"
CATCH_UP_TIMES_OUT = RC + "test_a_catch_up_send_that_times_out_ends_the_resume"
RAISES_AFTER_RESUME_OK = RC + "test_a_manager_that_raises_after_resume_ok_closes_the_socket_instead_of_sending_a_snapshot"
SHUTDOWN = RC + "test_a_shutdown_during_the_catch_up_ends_the_resume_without_a_warning"
CHECK_THEN_ADD = RC + "test_a_broadcast_scheduled_at_the_catch_ups_last_check_reaches_the_socket_live"
ASSIGN_THEN_COPY = RC + "test_a_seq_the_catch_up_sends_is_not_sent_to_the_socket_again_live"
FRAME_AS_LIVE = RC + "test_the_catch_up_sends_a_buffered_frame_exactly_as_the_live_fan_out_did"
CUT_POINTS = RC + "test_replay_since_returns_exactly_the_tail_after_every_cut_point"
NEGATIVE_CURSOR = RC + "test_promote_with_a_negative_cursor_delivers_from_the_first_seq"
NOT_RESURRECTED = RC + "test_promote_with_a_cursor_does_not_resurrect_a_socket_disconnected_during_the_catch_up"
LOCK_QUEUE = RC + "test_a_broadcast_queued_on_the_lock_behind_the_catch_ups_last_check_reaches_the_socket_live"
HANG_UP = RC + "test_a_client_that_hangs_up_mid_resume_ends_it_at_info_not_warning["

CATCH_UP_UNDER_LOCK = """\
        while True:
            async with self._lock:
                if websocket not in self._pending_connections:
                    if websocket in self._active_connections:
                        return True  # already active: it receives every broadcast
                    # Disconnected or closed meanwhile (a shutdown, say): never resurrect it.
                    logger.info("Resume catch-up stopped after seq %s: the socket was disconnected or closed; not promoted", cursor)
                    return False
                try:
                    missed = self.replay_since(cursor)
                except ReplayOutOfRange as exc:
                    logger.warning("Resume catch-up from seq %s failed: %s; the socket is not promoted", cursor, exc)
                    return False
                if not missed:
"""
CATCH_UP_READ_BEFORE_LOCK = """\
        while True:
            try:
                missed = self.replay_since(cursor)
            except ReplayOutOfRange as exc:
                logger.warning("Resume catch-up from seq %s failed: %s; the socket is not promoted", cursor, exc)
                return False
            async with self._lock:
                if websocket not in self._pending_connections:
                    return websocket in self._active_connections
                if not missed:
"""
EXCEPTION_ROUTING = """\
    try:
        await _deliver_resume(websocket, ws_manager, last_seq, events)
    except WebSocketDisconnect:
        raise
    except Exception as exc:  # noqa: BLE001 - after resume_ok, any failure ends the resume
        await _abort_resume(websocket, f"{type(exc).__name__} while resuming", exc_info=exc)
"""
CATCH_UP_SEND = '                if not await self._send_json(websocket, frame):\n'
CATCH_UP_FAILED_SEND = """\
                if not await self._send_json(websocket, frame):
                    # INFO, as the live fan-out logs a failed send: most often the client went
                    # away or a shutdown closed the socket, and _send_json has already logged a
                    # send that timed out at WARNING.
                    logger.info("Resume catch-up failed: seq %s was not delivered; the socket is not promoted", frame.get("seq"))
                    return False
"""


@dataclass(frozen=True)
class Arm:
    name: str
    path: str  # relative to the sub-package
    old: str
    new: object  # str, or PRE_FIX_VERSION
    must_fail: tuple[str, ...]


ARMS = (
    Arm(
        "no-socket loss: broadcast returns early with no socket active",
        MANAGER,
        "        for sub_message in self._maybe_chunk_message(message, quiet=not self._active_connections):\n",
        "        if not self._active_connections:\n            return\n        for sub_message in self._maybe_chunk_message(message, quiet=not self._active_connections):\n",
        NO_SOCKET_PINS + (NEGATIVE_CURSOR, NOT_RESURRECTED, CUT_POINTS),
    ),
    Arm(
        "replay race: training_stream.py reverted to PRE_FIX_REF (replay while pending, promote afterwards)",
        STREAM,
        "",
        PRE_FIX_VERSION,
        DELIVERY_PINS + (EVICTED, REPLAY_SEND_FAILS, CATCH_UP_SEND_FAILS, CATCH_UP_TIMES_OUT, RAISES_AFTER_RESUME_OK, SHUTDOWN),
    ),
    Arm(
        "replay race: _handle_resume promotes without the cursor",
        STREAM,
        "    if not await ws_manager.promote_to_active(websocket, replayed_through=replayed_through):\n",
        "    if not await ws_manager.promote_to_active(websocket):\n",
        DELIVERY_PINS + (CATCH_UP_SEND_FAILS, CATCH_UP_TIMES_OUT, SHUTDOWN, TS + "test_handle_resume_success_replays_events"),
    ),
    Arm(
        "replay race: no catch-up (activate on the first pass)",
        MANAGER,
        "                if not missed:\n                    self._activate(websocket)\n                    return True\n",
        "                self._activate(websocket)\n                return True\n",
        DELIVERY_PINS + (CATCH_UP_SEND_FAILS, CATCH_UP_TIMES_OUT, SHUTDOWN, NEGATIVE_CURSOR, ASSIGN_THEN_COPY, FRAME_AS_LIVE),
    ),
    Arm(
        "an await between the catch-up's last check and the activation",
        MANAGER,
        "                if not missed:\n                    self._activate(websocket)\n",
        "                if not missed:\n                    await asyncio.sleep(0)\n                    self._activate(websocket)\n",
        (CHECK_THEN_ADD,),
    ),
    Arm(
        "the catch-up's last check and the activation in two holds of the lock",
        MANAGER,
        "                if not missed:\n                    self._activate(websocket)\n                    return True\n            for frame in missed:\n",
        "            if not missed:\n                async with self._lock:\n                    self._activate(websocket)\n                return True\n            for frame in missed:\n",
        (LOCK_QUEUE,),
    ),
    Arm(
        "an await between a broadcast's seq assignment and its copy of the active set",
        MANAGER,
        "            enriched = self._assign_seq_and_buffer(sub_message)\n            disconnected = []\n",
        "            enriched = self._assign_seq_and_buffer(sub_message)\n            await asyncio.sleep(0)\n            disconnected = []\n",
        (ASSIGN_THEN_COPY,),
    ),
    Arm("the last check is read before the lock is taken", MANAGER, CATCH_UP_UNDER_LOCK, CATCH_UP_READ_BEFORE_LOCK, (RC + "test_a_broadcast_while_the_resuming_socket_waits_for_the_manager_lock_is_not_lost",)),
    Arm("a negative cursor is not normalised", MANAGER, "        cursor = max(replayed_through, 0)\n", "        cursor = replayed_through\n", (NEGATIVE_CURSOR,)),
    Arm("the catch-up ignores a failed send", MANAGER, CATCH_UP_FAILED_SEND, "                await self._send_json(websocket, frame)\n", (CATCH_UP_SEND_FAILS, CATCH_UP_TIMES_OUT)),
    Arm("the catch-up sizes buffered frames again (send_personal_message)", MANAGER, CATCH_UP_SEND, "                if not await self.send_personal_message(websocket, frame):\n", (FRAME_AS_LIVE,)),
    Arm(
        "an evicted catch-up activates anyway",
        MANAGER,
        '                except ReplayOutOfRange as exc:\n                    logger.warning("Resume catch-up from seq %s failed: %s; the socket is not promoted", cursor, exc)\n                    return False\n',
        "                except ReplayOutOfRange:\n                    self._activate(websocket)\n                    return True\n",
        (EVICTED,),
    ),
    Arm(
        "a socket dropped during the catch-up is resurrected",
        MANAGER,
        '                    logger.info("Resume catch-up stopped after seq %s: the socket was disconnected or closed; not promoted", cursor)\n                    return False\n',
        "                    self._activate(websocket)\n                    return True\n",
        (NOT_RESURRECTED,),
    ),
    Arm(
        "a socket gone at the catch-up's check is logged as a WARNING",
        MANAGER,
        '                    logger.info("Resume catch-up stopped after seq %s: the socket was disconnected or closed; not promoted", cursor)\n',
        '                    logger.warning("Resume catch-up stopped after seq %s: the socket was disconnected or closed; not promoted", cursor)\n',
        (NOT_RESURRECTED,),
    ),
    Arm(
        "no membership check before catching up",
        MANAGER,
        '                if websocket not in self._pending_connections:\n                    if websocket in self._active_connections:\n                        return True  # already active: it receives every broadcast\n                    # Disconnected or closed meanwhile (a shutdown, say): never resurrect it.\n                    logger.info("Resume catch-up stopped after seq %s: the socket was disconnected or closed; not promoted", cursor)\n                    return False\n',
        "",
        (RC + "test_promote_with_a_cursor_leaves_an_already_active_socket_alone", NOT_RESURRECTED),
    ),
    Arm(
        "replay_since copies one frame too few after the cut",
        MANAGER,
        "        tail = list(itertools.islice(reversed(self._replay_buffer), len(self._replay_buffer) - idx))\n",
        "        tail = list(itertools.islice(reversed(self._replay_buffer), len(self._replay_buffer) - idx - 1))\n",
        (CUT_POINTS,),
    ),
    Arm("a split nobody receives is logged at INFO", MANAGER, "self._maybe_chunk_message(message, quiet=not self._active_connections)", "self._maybe_chunk_message(message, quiet=False)", (RC + "test_splitting_a_broadcast_nobody_receives_is_logged_at_debug_not_info",)),
    Arm(
        "a failed catch-up send is logged as a WARNING",
        MANAGER,
        'logger.info("Resume catch-up failed: seq %s was not delivered',
        'logger.warning("Resume catch-up failed: seq %s was not delivered',
        (SHUTDOWN, CATCH_UP_TIMES_OUT, HANG_UP + "catch_up]"),
    ),
    Arm(
        "an aborted catch-up is logged as a WARNING by the handler too",
        STREAM,
        '        await _abort_resume(websocket, "the catch-up after the replay did not complete", level=logging.INFO)\n',
        '        await _abort_resume(websocket, "the catch-up after the replay did not complete")\n',
        (SHUTDOWN, HANG_UP + "catch_up]"),
    ),
    Arm("an exception after resume_ok falls back to a fresh connect", STREAM, EXCEPTION_ROUTING, "    await _deliver_resume(websocket, ws_manager, last_seq, events)\n", (RAISES_AFTER_RESUME_OK, TS + "test_handle_resume_closes_when_the_manager_raises_after_resume_ok")),
    Arm(
        "the replay ignores a failed send",
        STREAM,
        "        if not await ws_manager.send_personal_message(websocket, event):\n            await _abort_resume(websocket, f\"replayed seq {event.get('seq')} was not delivered\", level=logging.INFO)\n",
        "        await ws_manager.send_personal_message(websocket, event)\n",
        (REPLAY_SEND_FAILS,),
    ),
    Arm(
        "a resume_ok that was not delivered is ignored",
        STREAM,
        '    ):\n        await _abort_resume(websocket, "resume_ok was not delivered", level=logging.INFO)\n',
        "    ):\n        pass\n",
        (TS + "test_handle_resume_closes_when_resume_ok_is_not_delivered",),
    ),
    Arm(
        "a client gone before resume_ok lands is logged as a WARNING",
        STREAM,
        '"resume_ok was not delivered", level=logging.INFO)',
        '"resume_ok was not delivered")',
        (HANG_UP + "resume_ok]",),
    ),
    Arm(
        "a replayed frame the client is gone for is logged as a WARNING",
        STREAM,
        "was not delivered\", level=logging.INFO)\n        replayed_through = event[\"seq\"]\n",
        "was not delivered\")\n        replayed_through = event[\"seq\"]\n",
        (HANG_UP + "replay]",),
    ),
    Arm(
        "an aborted resume is not closed",
        STREAM,
        "    with contextlib.suppress(Exception):\n        await websocket.close(code=_RESUME_INCOMPLETE_CLOSE_CODE, reason=_RESUME_INCOMPLETE_CLOSE_REASON)\n    raise WebSocketDisconnect(",
        "    raise WebSocketDisconnect(",
        (EVICTED, REPLAY_SEND_FAILS, CATCH_UP_SEND_FAILS, CATCH_UP_TIMES_OUT, RAISES_AFTER_RESUME_OK, TS + "test_handle_resume_closes_when_the_manager_cannot_keep_continuity", TS + "test_handle_resume_closes_when_the_manager_raises_after_resume_ok"),
    ),
)


def _short(nodeid: str) -> str:
    """``.../tests/test_x.py::name[param]`` -> ``test_x.py::name[param]``."""
    return nodeid.rsplit("tests/", 1)[-1]


def _copy_subpackage(dest: Path) -> Path:
    """Copy the sub-package (package, tests, pyproject) into ``dest``; return the copy's root."""
    root = dest / SUBPACKAGE
    shutil.copytree(REPO / SUBPACKAGE, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".ruff_cache", ".pytest_cache", "*.egg-info", "build", "dist"))
    return root


def _env(copy_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join([str(copy_root), str(REPO / "juniper-model-core")])
    return env


def _has_pytest_timeout(python: str) -> bool:
    probe = subprocess.run([python, "-c", "import pytest_timeout"], capture_output=True, text=True, check=False, timeout=60)
    return probe.returncode == 0


def _run_suites(python: str, copy_root: Path, per_test_timeout: bool) -> dict:
    # The suites' ini already passes -q; a second -q would drop the "N passed in Xs" line.
    cmd = [python, "-m", "pytest", *SUITES, "-p", "no:cacheprovider", "-rfE"]
    if per_test_timeout:
        cmd.append(f"--timeout={TEST_TIMEOUT_S}")
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=copy_root, env=_env(copy_root), capture_output=True, text=True, check=False, timeout=RUN_TIMEOUT_S)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return {"exit": None, "failed": [], "summary": f"TIMED OUT after {RUN_TIMEOUT_S}s", "canary_seen": CANARY in out, "stdout_tail": out[-2000:], "seconds": round(time.monotonic() - started, 1)}
    failed = sorted({_short(line.split(" ", 1)[1].split(" - ", 1)[0]) for line in proc.stdout.splitlines() if line.startswith("FAILED ")})
    summary = next((line for line in reversed(proc.stdout.splitlines()) if " in " in line and ("passed" in line or "failed" in line or "error" in line)), proc.stdout.strip()[-200:])
    return {"exit": proc.returncode, "failed": failed, "summary": summary, "canary_seen": CANARY in proc.stdout, "stdout_tail": proc.stdout[-2000:], "seconds": round(time.monotonic() - started, 1)}


def _pre_fix_text(rel: str) -> str:
    return subprocess.run(["git", "show", f"{PRE_FIX_REF}:{SUBPACKAGE}/{rel}"], cwd=REPO, capture_output=True, text=True, check=True, timeout=60).stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--python", default=sys.executable, help="interpreter that runs pytest (default: this one)")
    parser.add_argument("--json", type=Path, help="write the results here")
    parser.add_argument("--keep-trees", action="store_true", help="keep each arm's scratch copy (default: remove it once measured)")
    args = parser.parse_args()

    run_dir = SCRATCH_ROOT / f"run-{time.strftime('%Y%m%dT%H%M%S')}-{os.getpid()}"
    run_dir.mkdir(parents=True)
    per_test_timeout = _has_pytest_timeout(args.python)
    results: dict = {"python": args.python, "suites": list(SUITES), "pre_fix_ref": PRE_FIX_REF, "scratch": str(run_dir), "per_test_timeout_s": TEST_TIMEOUT_S if per_test_timeout else None, "arms": []}
    ok = True

    def measure(label: str, mutate) -> dict:
        tree = run_dir / label
        try:
            copy_root = _copy_subpackage(tree)
            note = mutate(copy_root)
            run = _run_suites(args.python, copy_root, per_test_timeout)
            run["note"] = note
            return run
        finally:
            if not args.keep_trees:
                shutil.rmtree(tree, ignore_errors=True)

    def canary(copy_root: Path) -> str:
        target = copy_root / MANAGER
        # Appended, not prepended: ``from __future__`` must stay the module's first statement.
        target.write_text(target.read_text(encoding="utf-8") + f"\nraise ImportError({CANARY!r})\n", encoding="utf-8")
        return "manager.py raises on import"

    seen = measure("canary", canary)
    canary_ok = seen["exit"] not in (0, None) and seen["canary_seen"]
    results["canary"] = {"exit": seen["exit"], "summary": seen["summary"], "canary_seen": canary_ok}
    print(f"canary (copy's manager.py raises on import): exit={seen['exit']}  seen={canary_ok}")
    if not canary_ok:
        print("REFUSED: pytest did not import the copied package, so no arm would measure its mutant")
        ok = False

    baseline = measure("baseline", lambda _root: "unmutated copy")
    results["baseline"] = {k: baseline[k] for k in ("exit", "failed", "summary", "seconds")}
    print(f"baseline (unmutated copy): exit={baseline['exit']}  {baseline['summary']}")
    ok = ok and baseline["exit"] == 0 and not baseline["failed"]

    for index, arm in enumerate(ARMS, start=1):
        record: dict = {"arm": arm.name, "file": f"{SUBPACKAGE}/{arm.path}", "must_fail": list(arm.must_fail)}
        source = (REPO / SUBPACKAGE / arm.path).read_text(encoding="utf-8")
        if arm.new is PRE_FIX_VERSION:
            mutated = _pre_fix_text(arm.path)
            anchors = 1 if mutated != source else 0
        else:
            anchors = source.count(arm.old)
            mutated = source.replace(arm.old, str(arm.new), 1)
        record["anchor_matches"] = anchors
        if anchors != 1:
            record["verdict"] = "ERROR: anchor did not match exactly once -- nothing was measured"
            print(f"ERROR    {arm.name}: anchor matched {anchors} times")
            results["arms"].append(record)
            ok = False
            continue

        def apply(copy_root: Path, rel: str = arm.path, text: str = mutated) -> str:
            (copy_root / rel).write_text(text, encoding="utf-8")
            return "mutated copy"

        run = measure(f"arm-{index:02d}", apply)
        failed = run["failed"]
        missing = [t for t in arm.must_fail if t not in failed]
        killed = run["exit"] not in (0, None) and not missing
        record.update(
            {
                "exit": run["exit"],
                "summary": run["summary"],
                "seconds": run["seconds"],
                "failed_count": len(failed),
                "failed": failed,
                "must_fail_killed": f"{len(arm.must_fail) - len(missing)}/{len(arm.must_fail)}",
                "must_fail_survived": missing,
                "stress_seeds_failed": sum(1 for t in failed if t.startswith(STRESS)),
                "verdict": "KILLED" if killed else "SURVIVED",
            }
        )
        results["arms"].append(record)
        print(f"{record['verdict']:8} {arm.name}: {record['must_fail_killed']} named tests failed; {len(failed)} failed in all ({record['stress_seeds_failed']} of 40 stress seeds)")
        for test in missing:
            print(f"         survived: {test}")
        ok = ok and killed

    final = measure("final", lambda _root: "unmutated copy")
    results["final"] = {k: final[k] for k in ("exit", "failed", "summary", "seconds")}
    print(f"final (unmutated copy, after every arm): exit={final['exit']}  {final['summary']}")
    ok = ok and final["exit"] == 0 and not final["failed"]
    if not args.keep_trees:
        shutil.rmtree(run_dir, ignore_errors=True)
    killed_count = sum(1 for a in results["arms"] if a.get("verdict") == "KILLED")
    results["verdict"] = f"{killed_count}/{len(ARMS)} arms killed" + ("" if ok else " -- NOT CLEAN")
    print(results["verdict"])
    if args.json:
        args.json.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
