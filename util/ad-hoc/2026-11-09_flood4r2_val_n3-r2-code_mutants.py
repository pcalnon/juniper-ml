"""
Re-run the N-3 round-2 builder's mutants (MA, MB, MC, MC2 and the rest) and a set of the validator's own variants
against the round-2 tests, in the validator's own juniper-cascor worktree, and record which tests kill each.

The carrier's changed files are copied (sha256-verified) into a SCRATCH worktree at origin/main 7640d420; each mutant
is an exact-string edit (old text must occur exactly once) applied there, the six WebSocket test files are run, and
the file is restored byte-for-byte (sha256 checked) before the next mutant. The carrier itself is only read.

Usage:
    python3 2026-11-09_flood4r2_val_n3-r2-code_mutants.py [--workers N] [--only PREFIX ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
WORKTREES = JUNIPER / "worktrees"
CARRIER = WORKTREES / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
SCRATCH = WORKTREES / "juniper-cascor--val--flood4r2-n3-r2-code-mutants--20261109-0924--7640d420"
OUT = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert" / "tmp" / "flood4r2-val" / "n3-r2-code-lens" / "mutants"
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"

MANAGER = "src/api/websocket/manager.py"
STREAM = "src/api/websocket/training_stream.py"
OBS = "src/api/observability.py"
NEW_TESTS = "src/tests/unit/api/test_websocket_resume_continuity.py"
COPIED = [
    MANAGER,
    STREAM,
    OBS,
    NEW_TESTS,
    "src/tests/unit/api/test_training_stream_coverage.py",
    "src/tests/unit/api/test_metrics_obs_wire_02.py",
    "src/tests/unit/api/test_websocket_manager.py",
]
TEST_FILES = COPIED[3:] + ["src/tests/unit/api/test_websocket_seq_replay.py", "src/tests/unit/api/test_ws_broadcast_fault_isolation.py"]

_FINAL_CHECK = "                if not missed:\n                    # No await between this check and the activation: a\n                    # broadcast numbered after the check fans out to the socket.\n                    self._activate(websocket)\n                    return True\n"
_PROMOTE_CALL = '    if not await ws_manager.promote_to_active(websocket, replayed_through=replayed_through):\n        await _abort("the catch-up after the replay did not complete")\n'

MUTANTS = [
    # ---- the builder's, verbatim (tmp/flood4-fix/n3-r2 mutants script) ----
    {"name": "MA-two-lock-sections", "origin": "builder", "edits": [(MANAGER, _FINAL_CHECK, "                if not missed:\n                    break\n"), (MANAGER, '                cursor = event["seq"]\n\n    async def disconnect(', '                cursor = event["seq"]\n        async with self._lock:\n            self._activate(websocket)\n        return True\n\n    async def disconnect(')]},
    {"name": "MB-no-catch-up-when-nothing-was-replayed", "origin": "builder", "edits": [(STREAM, _PROMOTE_CALL, '    if not events:\n        await ws_manager.promote_to_active(websocket)\n    elif not await ws_manager.promote_to_active(websocket, replayed_through=replayed_through):\n        await _abort("the catch-up after the replay did not complete")\n')]},
    {"name": "MC-range-check-on-the-first-catch-up-pass-only", "origin": "builder", "edits": [(MANAGER, "        cursor = max(replayed_through, 0)\n        while True:\n", "        cursor = max(replayed_through, 0)\n        first_pass = True\n        while True:\n"), (MANAGER, "                    missed = self.replay_since(cursor)\n", '                    missed = self.replay_since(cursor) if first_pass else [m for m in list(self._replay_buffer) if m["seq"] > cursor]\n                    first_pass = False\n')]},
    {"name": "MC2-range-check-on-the-first-two-catch-up-passes-only", "origin": "builder", "edits": [(MANAGER, "        cursor = max(replayed_through, 0)\n        while True:\n", "        cursor = max(replayed_through, 0)\n        checked_passes = 0\n        while True:\n"), (MANAGER, "                    missed = self.replay_since(cursor)\n", '                    missed = self.replay_since(cursor) if checked_passes < 2 else [m for m in list(self._replay_buffer) if m["seq"] > cursor]\n                    checked_passes += 1\n')]},
    {"name": "MD1-no-integer-check-on-last_seq", "origin": "builder", "edits": [(STREAM, "    if client_server_id is None or not _is_seq_cursor(last_seq):\n", "    if client_server_id is None or last_seq is None:\n")]},
    {"name": "MD2-a-bool-counts-as-a-seq", "origin": "builder", "edits": [(STREAM, "    return isinstance(value, int) and not isinstance(value, bool)\n", "    return isinstance(value, int)\n")]},
    {"name": "ME-no-check-above-the-last-seq", "origin": "builder", "edits": [(MANAGER, '            newest_seq = self._next_seq - 1\n            if last_seq > newest_seq:\n                raise ReplayOutOfRange(f"Requested seq {last_seq} is above the last seq numbered, {newest_seq}")\n', "")]},
    {"name": "MF-the-newest-seq-itself-refused", "origin": "builder", "edits": [(MANAGER, "            if last_seq > newest_seq:\n", "            if last_seq >= newest_seq:\n")]},
    # ---- the validator's own variants ----
    {"name": "V-MA3-await-inside-the-final-window", "origin": "validator", "why": "an await between the final check and the activation, inside the one lock section", "edits": [(MANAGER, _FINAL_CHECK, "                if not missed:\n                    await asyncio.sleep(0)\n                    self._activate(websocket)\n                    return True\n")]},
    {"name": "V-MA5-final-check-before-the-lock", "origin": "validator", "why": "the range check / emptiness test read before acquiring self._lock, the activation inside it", "edits": [(MANAGER, "        while True:\n            async with self._lock:\n                if websocket not in self._pending_connections:\n", "        while True:\n            try:\n                pre = self.replay_since(cursor)\n            except ReplayOutOfRange:\n                return False\n            async with self._lock:\n                if websocket not in self._pending_connections:\n"), (MANAGER, "                if not missed:\n                    # No await", "                if not pre:\n                    # No await")]},
    {"name": "V-MB-dup-cursor-not-advanced-by-the-replay", "origin": "validator", "why": "the catch-up starts from the client's last_seq, re-sending the replay", "edits": [(STREAM, "    if not await ws_manager.promote_to_active(websocket, replayed_through=replayed_through):\n", "    if not await ws_manager.promote_to_active(websocket, replayed_through=last_seq):\n")]},
    {"name": "V-MB-skip-cursor-is-current-seq", "origin": "validator", "why": "the catch-up starts from the current seq, skipping what was broadcast during the replay", "edits": [(STREAM, "    if not await ws_manager.promote_to_active(websocket, replayed_through=replayed_through):\n", "    if not await ws_manager.promote_to_active(websocket, replayed_through=ws_manager.current_seq):\n")]},
    {"name": "V-MC3-range-check-skipped-on-the-first-pass", "origin": "validator", "why": "passes 2+ run replay_since; pass 1 reads the raw buffer", "edits": [(MANAGER, "        cursor = max(replayed_through, 0)\n        while True:\n", "        cursor = max(replayed_through, 0)\n        first_pass = True\n        while True:\n"), (MANAGER, "                    missed = self.replay_since(cursor)\n", '                    missed = [m for m in list(self._replay_buffer) if m["seq"] > cursor] if first_pass else self.replay_since(cursor)\n                    first_pass = False\n')]},
    {"name": "V-MC-swallow-out-of-range", "origin": "validator", "why": "an eviction is treated as nothing left to send", "edits": [(MANAGER, '                    logger.warning("Resume catch-up from seq %s failed: %s; the socket is not promoted", cursor, exc)\n                    return False\n', '                    logger.warning("Resume catch-up from seq %s failed: %s; the socket is not promoted", cursor, exc)\n                    missed = []\n')]},
    {"name": "V-MG1-abort-returns-instead-of-raising", "origin": "validator", "why": "_abort_resume closes but returns, so _handle_resume carries on", "edits": [(STREAM, "    raise WebSocketDisconnect(code=RESUME_INCOMPLETE_CLOSE_CODE, reason=RESUME_INCOMPLETE_CLOSE_REASON)\n", "    return None  # type: ignore[return-value]\n")]},
    {"name": "V-MG2-abort-without-the-close", "origin": "validator", "why": "_abort_resume raises without sending the 1011 close", "edits": [(STREAM, "        await websocket.close(code=RESUME_INCOMPLETE_CLOSE_CODE, reason=RESUME_INCOMPLETE_CLOSE_REASON)\n", "        pass\n")]},
    {"name": "V-MH-abort-not-counted", "origin": "validator", "why": "an aborted resume is not counted as replay_incomplete", "edits": [(STREAM, '        _emit_outcome("replay_incomplete")\n', "")]},
    {"name": "V-MI-broadcast-yields-after-numbering", "origin": "validator", "why": "broadcast awaits between numbering a message and copying the active set", "edits": [(MANAGER, "            enriched = self._assign_seq_and_buffer(sub_message)\n            disconnected = []\n", "            enriched = self._assign_seq_and_buffer(sub_message)\n            await asyncio.sleep(0)\n            disconnected = []\n")]},
    {"name": "V-MJ-integral-float-is-a-seq", "origin": "validator", "why": "_is_seq_cursor accepts 2.0", "edits": [(STREAM, "    return isinstance(value, int) and not isinstance(value, bool)\n", "    return (isinstance(value, int) and not isinstance(value, bool)) or (isinstance(value, float) and value.is_integer())\n")]},
    {"name": "V-MK-no-clamp-on-a-negative-cursor", "origin": "validator", "why": "the catch-up passes a negative cursor straight to replay_since", "edits": [(MANAGER, "        cursor = max(replayed_through, 0)\n", "        cursor = replayed_through\n")]},
    {"name": "V-ML-resurrects-a-disconnected-socket", "origin": "validator", "why": "a socket neither pending nor active is reported promoted", "edits": [(MANAGER, "                    return websocket in self._active_connections\n", "                    return True\n")]},
    {"name": "V-MM-resume-ok-failure-ignored", "origin": "validator", "why": "resume_ok's failed send no longer aborts", "edits": [(STREAM, '        await _abort("resume_ok was not delivered")\n', "        pass\n")]},
    {"name": "V-MN-replay-frame-failure-ignored", "origin": "validator", "why": "a replay frame's failed send is skipped over", "edits": [(STREAM, "            await _abort(f\"replayed seq {event.get('seq')} was not delivered\")\n", "            pass\n")]},
    {"name": "V-MO-catch-up-send-failure-ignored", "origin": "validator", "why": "a catch-up frame's failed send is skipped over", "edits": [(MANAGER, '                    logger.warning("Resume catch-up failed: seq %s was not sent; the socket is not promoted", event.get("seq"))\n                    return False\n', '                    logger.warning("Resume catch-up failed: seq %s was not sent; the socket is not promoted", event.get("seq"))\n')]},
    {"name": "V-MP-handler-promotes-again-after-resume", "origin": "validator", "why": "the handler promotes unconditionally after a resume too (old call restored)", "edits": [(STREAM, "        if not resumed:\n            # Promote to active (now eligible for broadcasts). A resumed\n", "        if True:\n            # Promote to active (now eligible for broadcasts). A resumed\n")]},
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def failed_ids(junit: Path) -> list:
    if not junit.exists():
        return ["<no junit>"]
    root = ET.parse(junit).getroot()
    return sorted(f"{c.get('classname')}::{c.get('name')}" for c in root.iter("testcase") if c.find("failure") is not None or c.find("error") is not None)


def run(label: str, workers: int) -> dict:
    pyc = OUT / f"pycache-{label}"
    basetemp = OUT / f"basetemp-{label}"
    for stale in (pyc, basetemp):
        if stale.exists():
            shutil.rmtree(stale)
    pyc.mkdir(parents=True)
    junit = OUT / f"junit-{label}.xml"
    env = dict(os.environ)
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = str(pyc)
    cmd = [PYTHON, "-m", "pytest", "-p", "no:cacheprovider", "-m", "unit and not slow", "--timeout=120", "-q", "-rfE", f"--junitxml={junit}", f"--basetemp={basetemp}"]
    if workers:
        cmd += ["-n", str(workers)]
    cmd += TEST_FILES
    t0 = time.monotonic()
    with open(OUT / f"{label}.log", "w", encoding="utf-8") as log:
        rc = subprocess.run(cmd, cwd=SCRATCH, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    failed = failed_ids(junit)
    total = sum(1 for _ in ET.parse(junit).getroot().iter("testcase")) if junit.exists() else 0
    shutil.rmtree(pyc, ignore_errors=True)
    return {"exit_status": rc, "seconds": round(time.monotonic() - t0, 1), "tests": total, "failed": len(failed), "failed_ids": failed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--skip-baseline", action="store_true")
    args = ap.parse_args()
    if args.workers > 4:
        raise SystemExit("parallelism is capped at 4 workers")
    OUT.mkdir(parents=True, exist_ok=True)
    carrier_before = {rel: sha(CARRIER / rel) for rel in COPIED}
    for rel in COPIED:
        shutil.copyfile(CARRIER / rel, SCRATCH / rel)
        if sha(SCRATCH / rel) != carrier_before[rel]:
            raise SystemExit(f"copy of {rel} is not byte-identical")
    results = {"scratch": str(SCRATCH), "carrier_sha256": carrier_before, "baseline": None, "mutants": {}}
    if not args.skip_baseline:
        results["baseline"] = run("baseline-carrier", args.workers)
        print(f"baseline: exit {results['baseline']['exit_status']}, {results['baseline']['failed']} of {results['baseline']['tests']} failed", flush=True)
    for m in MUTANTS:
        if args.only and not any(m["name"].startswith(p) for p in args.only):
            continue
        originals = {}
        for rel, old, new in m["edits"]:
            path = SCRATCH / rel
            if rel not in originals:
                originals[rel] = path.read_bytes()
            text = path.read_text(encoding="utf-8")
            if text.count(old) != 1:
                for orig_rel, data in originals.items():
                    (SCRATCH / orig_rel).write_bytes(data)
                raise SystemExit(f"{m['name']}: edit text occurs {text.count(old)} times in {rel}")
            path.write_text(text.replace(old, new), encoding="utf-8")
        try:
            res = run(m["name"], args.workers)
        finally:
            for rel, data in originals.items():
                (SCRATCH / rel).write_bytes(data)
                if sha(SCRATCH / rel) != carrier_before[rel]:
                    raise SystemExit(f"{m['name']}: restore of {rel} failed")
        res["verdict"] = "KILLED" if res["failed"] else "SURVIVED"
        res["origin"] = m["origin"]
        res["why"] = m.get("why", "")
        results["mutants"][m["name"]] = res
        new_file_kills = sorted({fid.split("::")[-1] for fid in res["failed_ids"] if "test_websocket_resume_continuity" in fid})
        print(f"{m['name']}: {res['verdict']} ({res['failed']} of {res['tests']} failed; {len(new_file_kills)} in the new file: {new_file_kills[:4]})", flush=True)
    results["carrier_unchanged"] = carrier_before == {rel: sha(CARRIER / rel) for rel in COPIED}
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"carrier unchanged: {results['carrier_unchanged']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
