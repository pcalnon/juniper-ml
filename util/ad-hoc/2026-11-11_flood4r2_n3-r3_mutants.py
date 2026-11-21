"""
Show that the N-3 round-3 tests fail on main and on the mutants they are meant to kill, and pass on the round-3 carrier.

Adapted from round 2's 2026-11-09_flood4r2_n3-r2_mutants.py: a new scratch worktree (at the origin/main the carrier
was rebuilt on), a "round2" phase in place of "round1", and four more mutants. It runs in a SCRATCH juniper-cascor
worktree, never in the carrier: each phase overlays a set of files into the scratch tree (verifying every copied
file's sha256), runs the six WebSocket test files, and records which tests failed. Each mutant is applied to the
carrier's sources in the scratch tree and restored byte-for-byte (sha256 checked) before the next. The carrier's own
files are hashed before and after the whole run. Every __pycache__ under the scratch tree's src/ is deleted first, and
each run gets a fresh, empty PYTHONPYCACHEPREFIX with bytecode writing off, so no run is served stale bytecode. The
scratch tree is put back to its HEAD at the end.

Phases:
  main      main's sources + the round-3 test files
  round2    round 2's sources (tmp/flood4-fix/n3-r3/snapshots/r2, hash-equal to round 2's manifest) + the round-3 test
            files: the tests that pin round 3's own code changes must fail here
  carrier   the round-3 carrier's sources + test files (must pass)
  <mutant>  the carrier with one mutant applied

Mutants: round 2's ten, V-MP (the code lens's surviving mutant, written as main's unconditional promotion rather than
as a constant conditional), MG (the handshake's clamp of a negative cursor removed) and MH / MH2 (the `data` type check
removed, or narrowed to null only).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses;
         tmp/flood4r2-val/n3-r2-code-lens/findings.json F2 (V-MP), F4, F5
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
WORKTREES = JUNIPER / "worktrees"
CARRIER = WORKTREES / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
SCRATCH = WORKTREES / "juniper-cascor--build--ws-resume-losses-n3-r3-scratch--20261111-1850--9f632eac"
R3 = CARRIER / "tmp" / "flood4-fix" / "n3-r3"
ROUND2 = R3 / "snapshots" / "r2"
OUT = R3 / "mutants"
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"

MANAGER = "src/api/websocket/manager.py"
STREAM = "src/api/websocket/training_stream.py"
OBS = "src/api/observability.py"
NEW_TESTS = "src/tests/unit/api/test_websocket_resume_continuity.py"
SOURCES = [MANAGER, STREAM, OBS]
CHANGED_TESTS = [
    NEW_TESTS,
    "src/tests/unit/api/test_training_stream_coverage.py",
    "src/tests/unit/api/test_metrics_obs_wire_02.py",
    "src/tests/unit/api/test_websocket_manager.py",
]
WS_TEST_FILES = CHANGED_TESTS + [
    "src/tests/unit/api/test_websocket_seq_replay.py",
    "src/tests/unit/api/test_ws_broadcast_fault_isolation.py",
]

#: The tests round 3 adds to NEW_TESTS (names as pytest reports them, parameters stripped).
ROUND3_TESTS = {
    "test_a_resumed_socket_is_promoted_once_through_the_catch_up_only": "code lens F2 (mutant V-MP)",
    "test_a_negative_last_seq_is_read_as_zero_whatever_the_buffer_holds": "code lens F4 (mutant MG)",
    "test_a_negative_last_seq_is_out_of_range_once_seq_1_has_left_the_buffer_as_zero_is": "code lens F4 (control: passes everywhere)",
    "test_a_resume_frame_whose_data_is_not_an_object_is_refused_as_malformed": "code lens F5 (mutants MH, MH2)",
}

#: _resume_cursor's body: the type check on a resume frame's `data`.
DATA_GUARD = '    data = msg.get("data")\n    if not isinstance(data, dict):\n        return None, None\n    return data.get("last_seq"), data.get("server_instance_id")\n'
#: The same read as main makes it: no type check, so a `data` that is not an object raises.
DATA_UNGUARDED = '    data = msg.get("data", {})\n    return data.get("last_seq"), data.get("server_instance_id")\n'

HANDLER_PROMOTE = (
    "        if not resumed:\n"
    "            # Promote to active (now eligible for broadcasts). A resumed\n"
    "            # socket is active already: _handle_resume promoted it once its\n"
    "            # replay, and anything broadcast meanwhile, had been sent.\n"
    "            await ws_manager.promote_to_active(websocket)\n"
)

MUTANTS = [
    {
        "name": "MA-two-lock-sections",
        "finding": "N3-03",
        "why": "the final check and the activation in two `async with self._lock` sections (validator n3-code's mutant MA)",
        "edits": [
            (
                MANAGER,
                "                if not missed:\n                    # No await between this check and the activation: a\n                    # broadcast numbered after the check fans out to the socket.\n                    self._activate(websocket)\n                    return True\n",
                "                if not missed:\n                    break\n",
            ),
            (
                MANAGER,
                '                cursor = event["seq"]\n\n    async def disconnect(',
                '                cursor = event["seq"]\n        async with self._lock:\n            self._activate(websocket)\n        return True\n\n    async def disconnect(',
            ),
        ],
    },
    {
        "name": "MB-no-catch-up-when-nothing-was-replayed",
        "finding": "N3-09",
        "why": "_handle_resume promotes unconditionally when the replay snapshot was empty (validator n3-code's mutant MB)",
        "edits": [
            (
                STREAM,
                '    if not await ws_manager.promote_to_active(websocket, replayed_through=replayed_through):\n        await _abort("the catch-up after the replay did not complete")\n',
                '    if not events:\n        await ws_manager.promote_to_active(websocket)\n    elif not await ws_manager.promote_to_active(websocket, replayed_through=replayed_through):\n        await _abort("the catch-up after the replay did not complete")\n',
            )
        ],
    },
    {
        "name": "MC-range-check-on-the-first-catch-up-pass-only",
        "finding": "N3-04",
        "why": "later catch-up passes read the buffer without replay_since's range check (validator n3-code's mutant MC)",
        "edits": [
            (MANAGER, "        cursor = max(replayed_through, 0)\n        while True:\n", "        cursor = max(replayed_through, 0)\n        first_pass = True\n        while True:\n"),
            (
                MANAGER,
                "                    missed = self.replay_since(cursor)\n",
                '                    missed = self.replay_since(cursor) if first_pass else [m for m in list(self._replay_buffer) if m["seq"] > cursor]\n                    first_pass = False\n',
            ),
        ],
    },
    {
        "name": "MC2-range-check-on-the-first-two-catch-up-passes-only",
        "finding": "N3-04",
        "why": "the range check runs on passes 1 and 2 only: 'every pass' needs a case past the second",
        "edits": [
            (MANAGER, "        cursor = max(replayed_through, 0)\n        while True:\n", "        cursor = max(replayed_through, 0)\n        checked_passes = 0\n        while True:\n"),
            (
                MANAGER,
                "                    missed = self.replay_since(cursor)\n",
                '                    missed = self.replay_since(cursor) if checked_passes < 2 else [m for m in list(self._replay_buffer) if m["seq"] > cursor]\n                    checked_passes += 1\n',
            ),
        ],
    },
    {
        "name": "MD1-no-integer-check-on-last_seq",
        "finding": "N3-06",
        "why": "_handle_resume refuses only a missing last_seq again (round 1's and main's check)",
        "edits": [(STREAM, "    if client_server_id is None or not _is_seq_cursor(last_seq):\n", "    if client_server_id is None or last_seq is None:\n")],
    },
    {
        "name": "MD2-a-bool-counts-as-a-seq",
        "finding": "N3-06",
        "why": "_is_seq_cursor accepts a bool (Python's bool is an int)",
        "edits": [(STREAM, "    return isinstance(value, int) and not isinstance(value, bool)\n", "    return isinstance(value, int)\n")],
    },
    {
        "name": "ME-no-check-above-the-last-seq",
        "finding": "N3-06",
        "why": "replay_since no longer refuses a cursor above the last seq numbered",
        "edits": [
            (
                MANAGER,
                '            newest_seq = self._next_seq - 1\n            if last_seq > newest_seq:\n                raise ReplayOutOfRange(f"Requested seq {last_seq} is above the last seq numbered, {newest_seq}")\n',
                "",
            )
        ],
    },
    {
        "name": "MF-the-newest-seq-itself-refused",
        "finding": "N3-06",
        "why": "off by one: a client holding the newest seq (nothing missed) is refused",
        "edits": [(MANAGER, "            if last_seq > newest_seq:\n", "            if last_seq >= newest_seq:\n")],
    },
    {
        "name": "M01-broadcast-returns-early-with-no-socket-active",
        "finding": "round 1 defect 1 (sanity: still killed)",
        "why": "the defect-1 guard restored",
        "edits": [(MANAGER, '        if self._refuse_unserializable(message, "broadcast"):\n            return\n        for sub_message', '        if not self._active_connections:\n            return\n        if self._refuse_unserializable(message, "broadcast"):\n            return\n        for sub_message')],
    },
    {
        "name": "M02-promotion-skips-the-catch-up",
        "finding": "round 1 defect 2 (sanity: still killed)",
        "why": "promote_to_active ignores replayed_through",
        "edits": [
            (
                MANAGER,
                "        if replayed_through is None:\n            async with self._lock:\n                self._activate(websocket)\n            return True\n        return await self._catch_up_and_activate(websocket, replayed_through)\n",
                "        async with self._lock:\n            self._activate(websocket)\n        return True\n",
            )
        ],
    },
    {
        "name": "V-MP-handler-promotes-again-after-resume",
        "finding": "round-2 code lens F2",
        "why": "the handler promotes every socket again, without a cursor, as main does (the code lens's surviving mutant V-MP)",
        "edits": [(STREAM, HANDLER_PROMOTE, "        await ws_manager.promote_to_active(websocket)\n")],
    },
    {
        "name": "MG-negative-cursor-not-clamped-in-the-handshake",
        "finding": "round-2 code lens F4",
        "why": "replay_since is handed the client's negative last_seq as it is (round 2's and main's call)",
        "edits": [(STREAM, "        events = ws_manager.replay_since(max(last_seq, 0))\n", "        events = ws_manager.replay_since(last_seq)\n")],
    },
    {
        "name": "MH-no-type-check-on-data",
        "finding": "round-2 code lens F5",
        "why": "`data` is read as main reads it, so a non-object `data` raises inside the handshake",
        "edits": [(STREAM, DATA_GUARD, DATA_UNGUARDED)],
    },
    {
        "name": "MH2-only-a-null-data-is-replaced",
        "finding": "round-2 code lens F5",
        "why": "the check covers null only: a list, a string or a number still raises",
        "edits": [(STREAM, "    if not isinstance(data, dict):\n", "    if data is None:\n")],
    },
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def overlay(src_root: Path, rels: list) -> dict:
    """Copy ``rels`` from ``src_root`` into the scratch tree; return their sha256s, verified after the copy."""
    hashes = {}
    for rel in rels:
        shutil.copyfile(src_root / rel, SCRATCH / rel)
        hashes[rel] = sha(src_root / rel)
        if sha(SCRATCH / rel) != hashes[rel]:
            raise SystemExit(f"overlay of {rel} did not copy byte-for-byte")
    return hashes


def failed_ids(junit: Path) -> list:
    if not junit.exists():
        return ["<no junit>"]
    root = ET.parse(junit).getroot()
    return sorted(f"{c.get('classname')}::{c.get('name')}" for c in root.iter("testcase") if c.find("failure") is not None or c.find("error") is not None)


def bare(test_id: str) -> str:
    return test_id.split("::")[-1].split("[")[0]


def run(label: str, files: list) -> dict:
    pyc = OUT / f"pycache-{label}"
    basetemp = OUT / f"basetemp-{label}"
    for stale in (pyc, basetemp):
        if stale.exists():
            shutil.rmtree(stale)
    pyc.mkdir(parents=True)
    junit = OUT / f"junit-{label}.xml"
    if junit.exists():
        junit.unlink()
    env = dict(os.environ)
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = str(pyc)
    cmd = [PYTHON, "-m", "pytest", "-p", "no:cacheprovider", "-m", "unit and not slow", "--timeout=120", "-n", "4", "-q", "-rfE", f"--junitxml={junit}", f"--basetemp={basetemp}", *files]
    t0 = time.monotonic()
    with open(OUT / f"{label}.log", "w", encoding="utf-8") as log:
        log.write("$ (cwd " + str(SCRATCH) + ") env -u JUNIPER_CASCOR_LOG_DIR PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=" + str(pyc) + " " + " ".join(cmd) + "\n")
        log.flush()
        rc = subprocess.run(cmd, cwd=SCRATCH, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    failed = failed_ids(junit)
    total = sum(1 for _ in ET.parse(junit).getroot().iter("testcase")) if junit.exists() else 0
    new_file_failed = sum(1 for fid in failed if "test_websocket_resume_continuity" in fid)
    round3_failed = sorted({bare(fid) for fid in failed if bare(fid) in ROUND3_TESTS})
    return {
        "exit_status": rc,
        "seconds": round(time.monotonic() - t0, 1),
        "tests": total,
        "failed": len(failed),
        "failed_in_the_new_file": new_file_failed,
        "failed_ids": failed,
        "round3_tests_failed": round3_failed,
        "log": str(OUT / f"{label}.log"),
    }


def delete_stale_pycache() -> int:
    stale = sorted((SCRATCH / "src").rglob("__pycache__"))
    for directory in stale:
        shutil.rmtree(directory)
    return len(stale)


def restore_scratch() -> str:
    """Put the scratch tree back to its HEAD: tracked files checked out, the overlaid new test file removed."""
    subprocess.run(["git", "-C", str(SCRATCH), "checkout", "--", *SOURCES, *CHANGED_TESTS[1:]], check=True)
    (SCRATCH / NEW_TESTS).unlink(missing_ok=True)
    return subprocess.run(["git", "-C", str(SCRATCH), "status", "--short", "--", "src"], check=True, capture_output=True, text=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="mutant-name prefixes (the phases always run unless --skip-phases)")
    ap.add_argument("--skip-phases", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "-C", str(SCRATCH), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    carrier_head = subprocess.run(["git", "-C", str(CARRIER), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    if head != carrier_head:
        raise SystemExit(f"the scratch tree is at {head} but the carrier is built on {carrier_head}")
    carrier_before = {rel: sha(CARRIER / rel) for rel in SOURCES + CHANGED_TESTS}
    results = {"scratch": str(SCRATCH), "scratch_head": head, "carrier": str(CARRIER), "carrier_sha256": carrier_before, "stale_pycache_dirs_deleted": delete_stale_pycache(), "phases": {}, "mutants": {}}
    if not args.skip_phases:
        # main: main's sources (checked out fresh from HEAD), the round-3 test files.
        subprocess.run(["git", "-C", str(SCRATCH), "checkout", "--", *SOURCES, *CHANGED_TESTS[1:]], check=True)
        overlay(CARRIER, CHANGED_TESTS)
        results["phases"]["main"] = {"sources": "origin/main " + head, **run("phase-main", WS_TEST_FILES)}
        # round2: round 2's sources (the snapshot taken before the rebuild, hash-checked against round 2's manifest).
        with open(CARRIER / "tmp" / "flood4-fix" / "n3-r2" / "manifest.json", encoding="utf-8") as fh:
            round2 = {row["path"]: row["sha256"] for row in json.load(fh)["files"]}
        for rel in SOURCES:
            if sha(ROUND2 / rel) != round2[rel]:
                raise SystemExit(f"{ROUND2 / rel} is not round 2's {rel}")
        overlay(ROUND2, SOURCES)
        results["phases"]["round2"] = {"sources": "round 2 (sha256 = tmp/flood4-fix/n3-r2/manifest.json)", **run("phase-round2", WS_TEST_FILES)}
    # carrier: every changed .py file from the round-3 carrier.
    carrier_hashes = overlay(CARRIER, SOURCES + CHANGED_TESTS)
    if not args.skip_phases:
        results["phases"]["carrier"] = {"sources": "round-3 carrier", **run("phase-carrier", WS_TEST_FILES)}
    for m in MUTANTS:
        if args.only and not any(m["name"].startswith(p) for p in args.only):
            continue
        originals = {}
        try:
            for rel, old, new in m["edits"]:
                path = SCRATCH / rel
                originals.setdefault(rel, path.read_bytes())
                text = path.read_text(encoding="utf-8")
                if text.count(old) != 1:
                    raise SystemExit(f"{m['name']}: edit matched {text.count(old)} times in {rel}")
                path.write_text(text.replace(old, new), encoding="utf-8")
            mutated = {rel: sha(SCRATCH / rel) for rel in originals}
            outcome = run(m["name"], WS_TEST_FILES)
        finally:
            for rel, data in originals.items():
                (SCRATCH / rel).write_bytes(data)
                if sha(SCRATCH / rel) != carrier_hashes[rel]:
                    raise SystemExit(f"RESTORE FAILED: {rel}")
        killed = bool(outcome["exit_status"] and outcome["failed"])
        really_mutated = all(mutated[rel] != carrier_hashes[rel] for rel in mutated)
        results["mutants"][m["name"]] = {"finding": m["finding"], "why": m["why"], "killed": killed, "mutated_sha256_differs_from_carrier": really_mutated, "restored_sha256_verified": True, **outcome}
        print(f"{m['name']}: {'KILLED' if killed else 'SURVIVED'} ({outcome['failed']} of {outcome['tests']} failed; round-3 tests failing: {outcome['round3_tests_failed']})")
    for name, phase in results["phases"].items():
        print(f"phase {name}: exit {phase['exit_status']}, {phase['failed']} of {phase['tests']} failed ({phase['failed_in_the_new_file']} in the new file); round-3 tests failing: {phase['round3_tests_failed']}")
    results["carrier_sha256_unchanged"] = {rel: sha(CARRIER / rel) == h for rel, h in carrier_before.items()}
    results["scratch_src_status_after_restore"] = restore_scratch()
    name = "results-" + ("_".join(args.only) if args.only else "all") + ".json"
    with open(OUT / name, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
        fh.write("\n")
    print("carrier unchanged:", all(results["carrier_sha256_unchanged"].values()), "| scratch src status after restore:", repr(results["scratch_src_status_after_restore"]), "->", OUT / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
