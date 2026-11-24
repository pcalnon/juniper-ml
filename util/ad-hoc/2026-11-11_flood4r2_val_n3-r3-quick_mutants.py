"""
Re-run the N-3 round-3 WebSocket suites and the validator's own mutants of the two new wire behaviours.

Everything that writes happens in the validator's COPY worktree (juniper-cascor origin/main 9f632eac with the carrier's
11 files copied in); the carrier itself is only hashed, before and after. Order:

1. delete every ``__pycache__`` under COPY/src and MAIN/src (stale bytecode would mask a mutant);
2. ``clean-main``: main's own five WebSocket test files in the pristine MAIN worktree (the baseline count);
3. three phases in COPY, each against the six WebSocket test files: ``main-sources`` (the three source files as
   9f632eac has them, under the carrier's tests: which new tests fail on main), ``r2-sources`` (round 2's three source
   files: which tests round 3's two changes answer) and ``carrier``;
4. the mutants: each edit must match exactly once and must change the file; the run's failing tests are recorded; the
   file is restored from memory and its sha256 re-checked.

Every pytest run gets a fresh bytecode prefix and basetemp under the validator's scratch directory, ``-n 4`` at most,
and ``JUNIPER_CASCOR_LOG_DIR`` removed from its environment.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses (N-3 round 3, code findings F2, F4 and F5)
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
PRIMARY = JUNIPER / "juniper-cascor"
CARRIER = WORKTREES / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
COPY = WORKTREES / "juniper-cascor--val--n3-r3-quick--20261111-1958--9f632eac"
MAIN = WORKTREES / "juniper-cascor--val--n3-r3-quick-main--20261111-1958--9f632eac"
R2_SNAPSHOT = CARRIER / "tmp" / "flood4-fix" / "n3-r3" / "snapshots" / "r2"
OUT = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert" / "tmp" / "flood4r2-val" / "n3-r3-quick-s5" / "mutants"
R3_BASE = "9f632eaca3b93bdc547869aad9a0354208ed4076"
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"

MANAGER = "src/api/websocket/manager.py"
STREAM = "src/api/websocket/training_stream.py"
OBS = "src/api/observability.py"
SOURCES = [MANAGER, STREAM, OBS]
NEW_TESTS = "src/tests/unit/api/test_websocket_resume_continuity.py"
CHANGED_TESTS = [NEW_TESTS, "src/tests/unit/api/test_training_stream_coverage.py", "src/tests/unit/api/test_metrics_obs_wire_02.py", "src/tests/unit/api/test_websocket_manager.py"]
OTHER_WS_TESTS = ["src/tests/unit/api/test_websocket_seq_replay.py", "src/tests/unit/api/test_ws_broadcast_fault_isolation.py"]
WS_TEST_FILES = CHANGED_TESTS + OTHER_WS_TESTS

CLAMPED = "        events = ws_manager.replay_since(max(last_seq, 0))\n"
GUARD = '    data = msg.get("data")\n    if not isinstance(data, dict):\n        return None, None\n    return data.get("last_seq"), data.get("server_instance_id")\n'
HANDLER_PROMOTE = (
    "        if not resumed:\n"
    "            # Promote to active (now eligible for broadcasts). A resumed\n"
    "            # socket is active already: _handle_resume promoted it once its\n"
    "            # replay, and anything broadcast meanwhile, had been sent.\n"
    "            await ws_manager.promote_to_active(websocket)\n"
)
CATCH_UP_CALL = '    if not await ws_manager.promote_to_active(websocket, replayed_through=replayed_through):\n        await _abort("the catch-up after the replay did not complete")\n'
MALFORMED_CHECK = "    if client_server_id is None or not _is_seq_cursor(last_seq):\n"


def guard_with(condition: str) -> str:
    return '    data = msg.get("data")\n    if ' + condition + ':\n        return None, None\n    return data.get("last_seq"), data.get("server_instance_id")\n'


MUTANTS = [
    # F2: the handler must not promote a resumed socket a second time.
    {"name": "V-MP-handler-promotes-unconditionally-as-main-does", "edits": [(STREAM, HANDLER_PROMOTE, "        # Promote to active (now eligible for broadcasts)\n        await ws_manager.promote_to_active(websocket)\n")]},
    {"name": "Q-VMP2-second-cursorless-promotion-inside-handle-resume", "edits": [(STREAM, CATCH_UP_CALL, CATCH_UP_CALL + "    await ws_manager.promote_to_active(websocket)\n")]},
    # F4: a negative last_seq is read as 0 in the handshake.
    {"name": "Q4a-negative-cursor-unclamped", "edits": [(STREAM, CLAMPED, "        events = ws_manager.replay_since(last_seq)\n")]},
    {"name": "Q4b-clamped-at-1-so-seq-1-is-skipped", "edits": [(STREAM, CLAMPED, "        events = ws_manager.replay_since(max(last_seq, 1))\n")]},
    {"name": "Q4c-negative-read-as-its-absolute-value", "edits": [(STREAM, CLAMPED, "        events = ws_manager.replay_since(abs(last_seq))\n")]},
    {"name": "Q4d-clamped-at-minus-1", "edits": [(STREAM, CLAMPED, "        events = ws_manager.replay_since(max(last_seq, -1))\n")]},
    {"name": "Q4e-only-minus-1-read-as-0", "edits": [(STREAM, CLAMPED, "        events = ws_manager.replay_since(0 if last_seq == -1 else last_seq)\n")]},
    {"name": "Q4f-ALTERNATIVE-negative-refused-as-malformed", "edits": [(STREAM, MALFORMED_CHECK, "    if client_server_id is None or not _is_seq_cursor(last_seq) or last_seq < 0:\n")]},
    {"name": "Q4g-catch-up-clamp-removed-handshake-clamp-kept", "edits": [(MANAGER, "        cursor = max(replayed_through, 0)\n", "        cursor = replayed_through\n")]},
    # F5: a resume frame whose data is not an object is malformed_resume.
    {"name": "Q5a-data-read-unguarded-as-main-does", "edits": [(STREAM, GUARD, '    data = msg.get("data", {})\n    return data.get("last_seq"), data.get("server_instance_id")\n')]},
    {"name": "Q5b-guard-covers-null-only", "edits": [(STREAM, GUARD, guard_with("data is None"))]},
    {"name": "Q5c-guard-lets-a-list-through", "edits": [(STREAM, GUARD, guard_with("not isinstance(data, (dict, list))"))]},
    {"name": "Q5d-guard-lets-a-string-through", "edits": [(STREAM, GUARD, guard_with("not isinstance(data, (dict, str))"))]},
    {"name": "Q5e-guard-lets-a-float-through", "edits": [(STREAM, GUARD, guard_with("not isinstance(data, (dict, float))"))]},
    {"name": "Q5f-guard-lets-a-bool-through", "edits": [(STREAM, GUARD, guard_with("not isinstance(data, (dict, bool))"))]},
    {"name": "Q5g-guard-lets-any-number-through", "edits": [(STREAM, GUARD, guard_with("not isinstance(data, (dict, int, float))"))]},
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(tree: Path, rels: list) -> dict:
    return {rel: sha256(tree / rel) for rel in rels}


def delete_stale_pycache(tree: Path) -> int:
    stale = sorted((tree / "src").rglob("__pycache__"))
    for d in stale:
        shutil.rmtree(d)
    return len(stale)


def run(label: str, tree: Path, files: list) -> dict:
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
        log.write("$ (cwd " + str(tree) + ") env -u JUNIPER_CASCOR_LOG_DIR " + " ".join(cmd) + "\n")
        log.flush()
        rc = subprocess.run(cmd, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    cases = list(ET.parse(junit).getroot().iter("testcase")) if junit.exists() else []
    failed = sorted(f"{c.get('classname')}::{c.get('name')}" for c in cases if c.find("failure") is not None or c.find("error") is not None)
    return {
        "exit_status": rc,
        "seconds": round(time.monotonic() - t0, 1),
        "tests": len(cases),
        "failed": len(failed),
        "failed_in_the_new_file": sum(1 for fid in failed if "test_websocket_resume_continuity" in fid),
        "failed_test_functions": sorted({fid.split("::")[-1].split("[")[0] for fid in failed}),
        "failed_ids": failed,
    }


#: The validator's proposed addition to the F5 test (finding on the two surviving guard mutants): a float and a bool.
PROPOSED_TEST_EDITS = [
    (
        '@pytest.mark.parametrize("raw_data", ["null", "[]", \'"last_seq"\', "7"])\n',
        '@pytest.mark.parametrize("raw_data", ["null", "[]", \'"last_seq"\', "7", "1.5", "true"])\n',
    ),
    (
        '    """``data`` that is null, a list, a string or a number carries no cursor: ``malformed_resume``, and counted.\n',
        '    """``data`` that is null, a list, a string, a number or a boolean carries no cursor: ``malformed_resume``, and counted.\n',
    ),
]


def apply_edits(mutant: dict) -> None:
    for rel, old, new in mutant["edits"]:
        text = (COPY / rel).read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"{mutant['name']}: anchor occurs {text.count(old)} times in {rel}")
        (COPY / rel).write_text(text.replace(old, new), encoding="utf-8")


def proposed_f5_types(args, results: dict, save, restore, carrier_before: dict, tracked: list) -> int:
    """Does the proposed two-parameter addition to the F5 test pass on the carrier and kill the surviving mutants?"""
    test_path = COPY / NEW_TESTS
    original_test = test_path.read_bytes()
    try:
        text = original_test.decode("utf-8")
        for old, new in PROPOSED_TEST_EDITS:
            if text.count(old) != 1:
                raise SystemExit(f"proposed test edit: anchor occurs {text.count(old)} times")
            text = text.replace(old, new)
        test_path.write_text(text, encoding="utf-8")
        results["phases"]["carrier-with-proposed-test"] = run("phase-carrier-proposed-f5-types", COPY, [NEW_TESTS])
        save()
        for mutant in MUTANTS:
            if args.only is not None and not any(mutant["name"].startswith(p) for p in args.only):
                continue
            try:
                apply_edits(mutant)
                rec = run("mutant-proposed-f5-types-" + mutant["name"], COPY, [NEW_TESTS])
            finally:
                restore()
            rec["verdict"] = "KILLED" if rec["failed"] else "SURVIVED"
            results["mutants"][mutant["name"]] = rec
            save()
            print(f"{mutant['name']} (proposed test): {rec['verdict']} ({rec['failed']} of {rec['tests']} failed) {rec['failed_ids']}", flush=True)
    finally:
        test_path.write_bytes(original_test)
    results["copy_restored"] = hashes(COPY, tracked) == carrier_before
    results["carrier_unchanged"] = hashes(CARRIER, tracked) == carrier_before
    save()
    rec = results["phases"]["carrier-with-proposed-test"]
    print(f"phase carrier-with-proposed-test: {rec['tests']} tests, {rec['failed']} failed, exit {rec['exit_status']}")
    print(f"copy restored: {results['copy_restored']}; carrier unchanged: {results['carrier_unchanged']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="run only the mutants whose name starts with one of these")
    ap.add_argument("--skip-phases", action="store_true")
    ap.add_argument("--with-proposed-f5-types", action="store_true", help="patch COPY's new test file with the proposed F5 parameters for this run (restored afterwards); runs the new test file only")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    tracked = SOURCES + CHANGED_TESTS
    carrier_before = hashes(CARRIER, tracked)
    copy_before = hashes(COPY, tracked)
    if copy_before != carrier_before:
        raise SystemExit("COPY does not hold the carrier's files")
    results = {"copy": str(COPY), "carrier_sha256": carrier_before, "stale_pycache_deleted": {"copy": delete_stale_pycache(COPY), "main": delete_stale_pycache(MAIN)}, "phases": {}, "mutants": {}}
    suffix = "-proposed-f5-types" if args.with_proposed_f5_types else ""
    out_path = OUT / ("results" + suffix + ("" if args.only is None else "-" + "-".join(args.only)) + ".json")

    def save() -> None:
        out_path.write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")

    originals = {rel: (COPY / rel).read_bytes() for rel in SOURCES}
    source_hashes = {rel: carrier_before[rel] for rel in SOURCES}

    def restore() -> None:
        for rel, data in originals.items():
            (COPY / rel).write_bytes(data)
        if hashes(COPY, SOURCES) != source_hashes:
            raise SystemExit("restore failed: COPY's sources differ from the carrier's")

    if args.with_proposed_f5_types:
        return proposed_f5_types(args, results, save, restore, carrier_before, tracked)

    if not args.skip_phases:
        main_ws = [f for f in WS_TEST_FILES if f != NEW_TESTS]
        results["phases"]["clean-main"] = run("phase-clean-main", MAIN, main_ws)
        save()
        try:
            for rel in SOURCES:
                (COPY / rel).write_bytes(subprocess.run(["git", "-C", str(PRIMARY), "show", f"{R3_BASE}:{rel}"], capture_output=True, check=True).stdout)
            results["phases"]["main-sources"] = run("phase-main-sources", COPY, WS_TEST_FILES)
            for rel in SOURCES:
                shutil.copyfile(R2_SNAPSHOT / rel, COPY / rel)
            results["phases"]["r2-sources"] = run("phase-r2-sources", COPY, WS_TEST_FILES)
        finally:
            restore()
        results["phases"]["carrier"] = run("phase-carrier", COPY, WS_TEST_FILES)
        save()

    for mutant in MUTANTS:
        if args.only is not None and not any(mutant["name"].startswith(p) for p in args.only):
            continue
        try:
            apply_edits(mutant)
            if hashes(COPY, SOURCES) == source_hashes:
                raise SystemExit(f"{mutant['name']}: the edit changed nothing")
            rec = run("mutant-" + mutant["name"], COPY, WS_TEST_FILES)
        finally:
            restore()
        rec["verdict"] = "KILLED" if rec["failed"] else "SURVIVED"
        results["mutants"][mutant["name"]] = rec
        save()
        print(f"{mutant['name']}: {rec['verdict']} ({rec['failed']} of {rec['tests']} failed) {rec['failed_test_functions']}", flush=True)

    results["copy_restored"] = hashes(COPY, tracked) == carrier_before
    results["carrier_unchanged"] = hashes(CARRIER, tracked) == carrier_before
    save()
    for name, rec in results["phases"].items():
        print(f"phase {name}: {rec['tests']} tests, {rec['failed']} failed ({rec['failed_in_the_new_file']} in the new file), exit {rec['exit_status']}, {rec['seconds']} s")
    print(f"copy restored: {results['copy_restored']}; carrier unchanged: {results['carrier_unchanged']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
