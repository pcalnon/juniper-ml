"""
Mutation check for D-14: every changed function, both table-test harnesses, the shared table and the drift gate, each broken one way at a time in a COPY.

Three copies, none of them a carrier:
  svc    ``<scratch>/svc/``: juniper-service-core and juniper-model-core copied from the juniper-ml carrier
  cascor a juniper-cascor twin worktree (``--cascor-twin``) holding the carrier's fixture and table test
  eco    ``<scratch>/eco/``: a synthetic ecosystem root (``juniper-ml/`` with the drift gate and its copy of the
         table, ``juniper-cascor/`` with cascor's copy), where the gate runs with JUNIPER_DRIFT_TEST_FORCE_LOCAL=1

Each arm replaces one exact text (it must occur once) in one file of a copy, clears that copy's __pycache__,
runs the named tests, and restores the file in ``finally:``; the file's sha256 is checked before the arm and
after the restore. A baseline run of every target precedes the arms and must pass. An arm is KILLED when its
run fails (a nonzero exit with at least one failed test, or a collection error); SURVIVED otherwise.

Every run sets the six Sentry variables to the empty string and DBUS_SESSION_BUS_ADDRESS to a dead path.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python3.14"

SVC_STREAM = "juniper-service-core/juniper_service_core/websocket/training_stream.py"
SVC_MANAGER = "juniper-service-core/juniper_service_core/websocket/manager.py"
SVC_TABLE_TEST = "juniper-service-core/tests/test_websocket_resume_answer_table.py"
SVC_FIXTURE = "juniper-service-core/tests/fixtures/ws_resume_answers.json"
SVC_TESTS = ["juniper-service-core/tests/test_websocket_resume_continuity.py", SVC_TABLE_TEST, "juniper-service-core/tests/test_websocket_training_stream.py"]
CASCOR_STREAM = "src/api/websocket/training_stream.py"
CASCOR_MANAGER = "src/api/websocket/manager.py"
CASCOR_TABLE_TEST = "src/tests/unit/api/test_websocket_resume_answer_table.py"
CASCOR_FIXTURE = "src/tests/fixtures/ws_resume_answers.json"
GATE = "juniper-ml/tests/test_ws_resume_answer_table_drift.py"
ECO_ML_FIXTURE = "juniper-ml/juniper-service-core/tests/fixtures/ws_resume_answers.json"
ECO_CASCOR_FIXTURE = "juniper-cascor/src/tests/fixtures/ws_resume_answers.json"

#: A row whose answer every edit below changes: last_seq=3 (seq 3 of 5 held) in buffered5.
EDIT_OLD = '"buffered5": {"handshake": ["resume_ok(replayed_count=2)", "metrics#4", "metrics#5"], "live": ["metrics#6"]}'
EDIT_NEW = '"buffered5": {"handshake": ["resume_ok(replayed_count=3)", "metrics#4", "metrics#5"], "live": ["metrics#6"]}'

#: (arm id, copy, file, old text, new text, what it breaks)
ARMS = [
    # juniper-service-core: the four rules, the order of the checks, and the clamp's place
    ("svc-rule1-removed", "svc", SVC_STREAM, "    if not isinstance(data, dict):\n        data = {}  # null, a list, a string or a number carries no cursor\n", "", "rule 1 removed: a data that is not an object raises again"),
    ("svc-rule1-weakened-null-only", "svc", SVC_STREAM, "    if not isinstance(data, dict):\n", "    if data is None:\n", "rule 1 weakened: only a null data is read as {}"),
    ("svc-rule2-removed", "svc", SVC_STREAM, "if client_server_id is None or not isinstance(last_seq, int) or isinstance(last_seq, bool):", "if client_server_id is None or last_seq is None:", "rule 2 removed: back to the None check"),
    ("svc-rule2-bool-allowed", "svc", SVC_STREAM, " or not isinstance(last_seq, int) or isinstance(last_seq, bool):", " or not isinstance(last_seq, int):", "rule 2 weakened: a boolean passes as an integer"),
    ("svc-rule2-float-allowed", "svc", SVC_STREAM, " or not isinstance(last_seq, int) or isinstance(last_seq, bool):", " or not isinstance(last_seq, (int, float)) or isinstance(last_seq, bool):", "rule 2 weakened: a float (NaN, Infinity, 2.5) passes"),
    ("svc-rule3-removed", "svc", SVC_STREAM, "events = ws_manager.replay_since(max(last_seq, 0))", "events = ws_manager.replay_since(last_seq)", "rule 3 removed: a negative is answered by buffer state"),
    ("svc-rule3-weakened", "svc", SVC_STREAM, "events = ws_manager.replay_since(max(last_seq, 0))", "events = ws_manager.replay_since(max(last_seq, -1))", "rule 3 weakened: clamped to -1, not 0"),
    ("svc-rule4-removed", "svc", SVC_MANAGER, "            if last_seq > newest_seq:\n                raise ReplayOutOfRange(f\"Requested seq {last_seq} is above the last seq numbered, {newest_seq}\")\n", "", "rule 4 removed: a cursor above the last seq numbered is resume_ok again"),
    ("svc-rule4-off-by-one", "svc", SVC_MANAGER, "            if last_seq > newest_seq:\n", "            if last_seq > newest_seq + 1:\n", "rule 4 weakened: one past the newest seq passes"),
    ("svc-rule4-too-strict", "svc", SVC_MANAGER, "            if last_seq > newest_seq:\n", "            if last_seq >= newest_seq:\n", "rule 4 too strict: the newest seq itself is refused"),
    (
        "svc-checks-swapped",
        "svc",
        SVC_STREAM,
        "    if client_server_id is None or not isinstance(last_seq, int) or isinstance(last_seq, bool):\n",
        "    if client_server_id is not None and last_seq is not None and client_server_id != ws_manager.server_instance_id:\n        await ws_manager.send_personal_message(websocket, {\"type\": \"resume_failed\", \"timestamp\": time.time(), \"data\": {\"reason\": \"server_restarted\"}})\n        return False\n    if client_server_id is None or not isinstance(last_seq, int) or isinstance(last_seq, bool):\n",
        "the two checks swapped: server_instance_id is compared before the integer check",
    ),
    ("svc-clamp-above-integer-check", "svc", SVC_STREAM, '    last_seq = data.get("last_seq")\n', '    last_seq = data.get("last_seq")\n    if last_seq is not None:\n        last_seq = max(last_seq, 0)\n', "the clamp moved above the integer check"),
    # juniper-service-core's table-test harness and its copy of the table
    ("svc-harness-label-drops-count", "svc", SVC_TABLE_TEST, '        return f"resume_ok(replayed_count={data.get(\'replayed_count\')})"', '        return "resume_ok(replayed_count=0)"', "harness: the label ignores replayed_count"),
    ("svc-harness-no-live", "svc", SVC_TABLE_TEST, '        return {"handshake": handshake, "live": live}', '        return {"handshake": handshake, "live": []}', "harness: live frames are not read"),
    ("svc-harness-state-ignored", "svc", SVC_TABLE_TEST, '    manager = target.new_manager(state["replay_buffer_capacity"])', "    manager = target.new_manager(1024)", "harness: every state gets a 1024-slot buffer"),
    ("svc-row-edited-in-this-copy", "svc", SVC_FIXTURE, EDIT_OLD, EDIT_NEW, "the table: one row edited in juniper-ml's copy only"),
    # juniper-cascor: its handler broken (the table test must notice), its harness, its copy of the table
    ("cascor-rule2-removed", "cascor", CASCOR_STREAM, "    if client_server_id is None or not _is_seq_cursor(last_seq):", "    if client_server_id is None or last_seq is None:", "cascor's integer check removed"),
    ("cascor-rule4-removed", "cascor", CASCOR_MANAGER, "            if last_seq > newest_seq:\n", "            if False and last_seq > newest_seq:\n", "cascor's upper bound removed"),
    ("cascor-rule3-removed", "cascor", CASCOR_STREAM, "events = ws_manager.replay_since(max(last_seq, 0))", "events = ws_manager.replay_since(last_seq)", "cascor's clamp removed"),
    ("cascor-harness-no-live", "cascor", CASCOR_TABLE_TEST, '        return {"handshake": handshake, "live": live}', '        return {"handshake": handshake, "live": []}', "harness: live frames are not read"),
    ("cascor-row-edited-in-this-copy", "cascor", CASCOR_FIXTURE, EDIT_OLD, EDIT_NEW, "the table: one row edited in juniper-cascor's copy only"),
    # the drift gate, and a row edited in one copy as the gate sees it
    ("gate-row-edited-in-cascor-copy", "eco", ECO_CASCOR_FIXTURE, EDIT_OLD, EDIT_NEW, "the cascor copy differs by one row"),
    ("gate-row-edited-in-ml-copy", "eco", ECO_ML_FIXTURE, EDIT_OLD, EDIT_NEW, "the juniper-ml copy differs by one row"),
    ("gate-first-difference-blind", "eco", GATE, "    if mine == theirs:\n        return None\n", "    return None\n", "gate: first_difference reports no difference"),
    ("gate-absent-copy-skips", "eco", GATE, "    if not path.is_file():\n        return FAIL, (", "    if not path.is_file():\n        return SKIP, (", "gate: an absent copy skips instead of failing"),
    ("gate-root-never-found", "eco", GATE, "            if (candidate / _SIBLING_REPO).is_dir():\n                return candidate\n", "            if (candidate / _SIBLING_REPO).is_dir():\n                return None\n", "gate: the ecosystem root is never found"),
]


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def child_env(extra_pythonpath: list[str]) -> dict:
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}}
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/nonexistent/no-session-bus"
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    env["PYTHONPATH"] = os.pathsep.join(extra_pythonpath)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def clear_pycache(root: Path) -> None:
    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run_target(copy: str, roots: dict, log: Path) -> dict:
    """Run the tests of one copy; parse pytest's or unittest's summary."""
    if copy == "svc":
        command = [PYTHON, "-m", "pytest", *SVC_TESTS, "-p", "no:cacheprovider"]
        cwd, env = roots["svc"], child_env([str(roots["svc"] / "juniper-service-core"), str(roots["svc"] / "juniper-model-core")])
    elif copy == "cascor":
        command = [PYTHON, "-m", "pytest", "-m", "unit and not slow", CASCOR_TABLE_TEST, "--timeout=60", "-p", "no:cacheprovider"]
        cwd, env = roots["cascor"], child_env([])
    else:
        command = [PYTHON, "-m", "unittest", "-v", "tests/test_ws_resume_answer_table_drift.py"]
        cwd, env = roots["eco"] / "juniper-ml", child_env([])
        env["JUNIPER_DRIFT_TEST_FORCE_LOCAL"] = "1"
    started = time.monotonic()
    done = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=1200, check=False)
    log.write_text(done.stdout + "\n--- stderr ---\n" + done.stderr, encoding="utf-8")
    text = done.stdout + done.stderr
    failed = sum(int(n) for n in re.findall(r"(\d+) failed", text)) + sum(int(n) for n in re.findall(r"failures=(\d+)", text)) + sum(int(n) for n in re.findall(r"errors=(\d+)", text)) + sum(int(n) for n in re.findall(r"(\d+) errors?\b", text))
    return {"exit": done.returncode, "failed": failed, "seconds": round(time.monotonic() - started, 1), "log": str(log)}


def apply(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: the arm's text occurs {text.count(old)} times, not once")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--ml-carrier", type=Path, required=True, help="the juniper-ml carrier worktree (read only)")
    parser.add_argument("--cascor-carrier", type=Path, required=True, help="the juniper-cascor carrier worktree (read only)")
    parser.add_argument("--cascor-twin", type=Path, required=True, help="a juniper-cascor twin worktree holding the carrier's new files (mutated)")
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", default=None, help="a regex of arm ids to run")
    args = parser.parse_args()

    svc_root, eco_root = args.scratch / "svc", args.scratch / "eco"
    for root in (svc_root, eco_root):
        if root.exists():
            shutil.rmtree(root)
    ignore = shutil.ignore_patterns("__pycache__", "*.egg-info", ".pytest_cache")
    shutil.copytree(args.ml_carrier / "juniper-service-core", svc_root / "juniper-service-core", ignore=ignore)
    shutil.copytree(args.ml_carrier / "juniper-model-core", svc_root / "juniper-model-core", ignore=ignore)
    (eco_root / "juniper-ml" / "tests").mkdir(parents=True)
    shutil.copy2(args.ml_carrier / "tests" / "test_ws_resume_answer_table_drift.py", eco_root / GATE)
    (eco_root / ECO_ML_FIXTURE).parent.mkdir(parents=True)
    shutil.copy2(args.ml_carrier / SVC_FIXTURE, eco_root / ECO_ML_FIXTURE)
    (eco_root / ECO_CASCOR_FIXTURE).parent.mkdir(parents=True)
    shutil.copy2(args.cascor_carrier / CASCOR_FIXTURE, eco_root / ECO_CASCOR_FIXTURE)
    roots = {"svc": svc_root, "cascor": args.cascor_twin, "eco": eco_root}
    log_dir = args.scratch / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    touched = sorted({(copy, file) for _arm, copy, file, *_rest in ARMS})
    before = {f"{copy}:{file}": sha256_of(roots[copy] / file) for copy, file in touched}
    print("SHA256 BEFORE THE RUN")
    for key, digest in before.items():
        print(f"  {digest}  {key}")
    sys.stdout.flush()

    unapplicable = [arm_id for arm_id, copy, file, old, _new, _what in ARMS if (roots[copy] / file).read_text(encoding="utf-8").count(old) != 1]
    if unapplicable:
        raise SystemExit(f"arms whose text does not occur exactly once: {unapplicable}")

    result = {"roots": {name: str(path) for name, path in roots.items()}, "sha256_before": before, "baselines": {}, "arms": []}
    for copy in ("svc", "cascor", "eco"):
        clear_pycache(roots[copy])
        baseline = run_target(copy, roots, log_dir / f"baseline-{copy}.log")
        result["baselines"][copy] = baseline
        print(f"baseline {copy}: exit {baseline['exit']}, failed {baseline['failed']} ({baseline['seconds']} s)")
        sys.stdout.flush()
        if baseline["exit"] != 0:
            raise SystemExit(f"the {copy} baseline does not pass; no arm is meaningful")

    pattern = re.compile(args.only) if args.only else None
    for arm_id, copy, file, old, new, what in ARMS:
        if pattern is not None and not pattern.search(arm_id):
            continue
        path = roots[copy] / file
        original = path.read_bytes()
        if hashlib.sha256(original).hexdigest() != before[f"{copy}:{file}"]:
            raise SystemExit(f"{path} changed before arm {arm_id}")
        try:
            apply(path, old, new)
            clear_pycache(roots[copy])
            outcome = run_target(copy, roots, log_dir / f"{arm_id}.log")
        finally:
            # Restore from the recorded bytes: an empty ``new`` cannot be reversed by a replacement.
            path.write_bytes(original)
        after = sha256_of(path)
        if after != before[f"{copy}:{file}"]:
            raise SystemExit(f"{path} was not restored after arm {arm_id}: {after}")
        killed = outcome["exit"] != 0 and outcome["failed"] > 0
        result["arms"].append({"arm": arm_id, "copy": copy, "file": file, "what": what, "result": "killed" if killed else "survived", "sha256_after": after, **outcome})
        print(f"{arm_id}: {'KILLED' if killed else 'SURVIVED'} (exit {outcome['exit']}, failed {outcome['failed']}, {outcome['seconds']} s)")
        sys.stdout.flush()

    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1)
        handle.write("\n")


if __name__ == "__main__":
    main()
