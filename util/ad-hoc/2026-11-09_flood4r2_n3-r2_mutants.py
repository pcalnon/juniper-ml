"""
Show that the N-3 round-2 tests fail on main, on round 1's code where they pin new behaviour, and on the mutants they
are meant to kill -- and pass on the round-2 carrier.

Runs in a SCRATCH juniper-cascor worktree at origin/main, never in the carrier: each phase overlays a set of files
into the scratch tree (verifying every copied file's sha256), runs the six WebSocket test files, and records which
tests failed. Each mutant is applied to the round-2 carrier's sources in the scratch tree and restored byte-for-byte
(sha256 checked) before the next. The carrier's own files are hashed before and after the whole run.

Phases:
  main      main's sources + the round-2 test files
  round1    round 1's sources (read from validator n3-code's scratch worktree, which holds them hash-identical) + the
            round-2 test files
  carrier   the round-2 carrier's sources + test files (must pass)
  <mutant>  the carrier with one mutant applied

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses;
         validator findings N3-03, N3-04, N3-06, N3-09 (tmp/flood4r2-val/n3-code-lens/findings.json)
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
SCRATCH = WORKTREES / "juniper-cascor--build--ws-resume-losses-n3-r2-scratch--20261109-0831--7640d420"
ROUND1 = WORKTREES / "juniper-cascor--validate--ws-resume-losses-n3-code--20261109-0324--f3dfee8c"
OUT = CARRIER / "tmp" / "flood4-fix" / "n3-r2" / "mutants"
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

#: The round-2 tests: the ones the fix-up adds to NEW_TESTS (names as pytest reports them, parameters stripped).
ROUND2_TESTS = {
    "test_a_broadcast_during_resume_ok_with_nothing_to_replay_still_arrives": "N3-09 (mutant MB)",
    "test_a_task_queued_on_the_manager_lock_cannot_come_between_the_final_check_and_the_activation": "N3-03 (mutant MA)",
    "test_an_eviction_during_any_catch_up_pass_closes_the_resume_without_a_hole": "N3-04 (mutant MC)",
    "test_a_last_seq_that_is_not_a_plain_integer_is_refused_as_malformed": "N3-06 (non-integer cursor)",
    "test_a_last_seq_above_the_last_seq_numbered_is_refused_out_of_range": "N3-06 (cursor above the last seq)",
    "test_replay_since_and_the_catch_up_refuse_a_cursor_above_the_last_seq_numbered": "N3-06 (cursor above the last seq)",
}

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


def run(label: str, files: list) -> dict:
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
    cmd = [PYTHON, "-m", "pytest", "-p", "no:cacheprovider", "-m", "unit and not slow", "--timeout=120", "-n", "4", "-q", "-rfE", f"--junitxml={junit}", f"--basetemp={basetemp}", *files]
    t0 = time.monotonic()
    with open(OUT / f"{label}.log", "w", encoding="utf-8") as log:
        rc = subprocess.run(cmd, cwd=SCRATCH, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    failed = failed_ids(junit)
    total = sum(1 for _ in ET.parse(junit).getroot().iter("testcase")) if junit.exists() else 0
    round2_failed = sorted({fid.split("::")[-1].split("[")[0] for fid in failed if fid.split("::")[-1].split("[")[0] in ROUND2_TESTS})
    return {"exit_status": rc, "seconds": round(time.monotonic() - t0, 1), "tests": total, "failed": len(failed), "failed_ids": failed, "round2_tests_failed": round2_failed, "log": str(OUT / f"{label}.log")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="mutant-name prefixes (phases main/round1/carrier always run unless --skip-phases)")
    ap.add_argument("--skip-phases", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "-C", str(SCRATCH), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    carrier_before = {rel: sha(CARRIER / rel) for rel in SOURCES + CHANGED_TESTS}
    results = {"scratch": str(SCRATCH), "scratch_head": head, "carrier": str(CARRIER), "carrier_sha256": carrier_before, "phases": {}, "mutants": {}}
    if not args.skip_phases:
        # main: main's sources (checked out fresh from HEAD), the round-2 test files.
        subprocess.run(["git", "-C", str(SCRATCH), "checkout", "--", *SOURCES, *CHANGED_TESTS[1:]], check=True)
        overlay(CARRIER, CHANGED_TESTS)
        results["phases"]["main"] = {"sources": "origin/main " + head, **run("phase-main", WS_TEST_FILES)}
        # round1: round 1's sources (validator n3-code's scratch copy, hash-checked against the frozen round-1 record).
        with open(CARRIER / "tmp" / "flood4-fix" / "n3-r2" / "hashes_round1.json", encoding="utf-8") as fh:
            round1 = {row["path"]: row["sha256"] for row in json.load(fh)["files"]}
        for rel in SOURCES:
            if sha(ROUND1 / rel) != round1[rel]:
                raise SystemExit(f"{ROUND1 / rel} is not round 1's {rel}")
        overlay(ROUND1, SOURCES)
        results["phases"]["round1"] = {"sources": "round 1 (sha256 = tmp/flood4-fix/n3-r2/hashes_round1.json)", **run("phase-round1", WS_TEST_FILES)}
    # carrier: every changed .py file from the round-2 carrier.
    carrier_hashes = overlay(CARRIER, SOURCES + CHANGED_TESTS)
    if not args.skip_phases:
        results["phases"]["carrier"] = {"sources": "round-2 carrier", **run("phase-carrier", WS_TEST_FILES)}
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
            outcome = run(m["name"], WS_TEST_FILES)
        finally:
            for rel, data in originals.items():
                (SCRATCH / rel).write_bytes(data)
                if sha(SCRATCH / rel) != carrier_hashes[rel]:
                    raise SystemExit(f"RESTORE FAILED: {rel}")
        killed = bool(outcome["exit_status"] and outcome["failed"])
        results["mutants"][m["name"]] = {"finding": m["finding"], "why": m["why"], "killed": killed, "restored_sha256_verified": True, **outcome}
        print(f"{m['name']}: {'KILLED' if killed else 'SURVIVED'} ({outcome['failed']} of {outcome['tests']} failed; round-2 tests failing: {outcome['round2_tests_failed']})")
    for name, phase in results["phases"].items():
        print(f"phase {name}: exit {phase['exit_status']}, {phase['failed']} of {phase['tests']} failed; round-2 tests failing: {phase['round2_tests_failed']}")
    results["carrier_sha256_unchanged"] = {rel: sha(CARRIER / rel) == h for rel, h in carrier_before.items()}
    name = "results-" + ("_".join(args.only) if args.only else "all") + ".json"
    with open(OUT / name, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
        fh.write("\n")
    print("carrier unchanged:", all(results["carrier_sha256_unchanged"].values()), "->", OUT / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
