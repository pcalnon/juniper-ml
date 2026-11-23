"""
Mutation check for the D-14 fix-up: every arm of the round-1 builder's run, every arm of the code lens's run, and the
arms this round adds, each applied to a COPY, never to a carrier.

Copies (made by ``--setup``; the carriers are only read):
  svc     ``<copies>/svc/``: juniper-service-core and juniper-model-core copied from the juniper-ml carrier
  eco     ``<copies>/eco/``: a synthetic ecosystem root, ``juniper-ml/`` holding the drift gate and juniper-ml's copy of
          the table, ``juniper-cascor/`` holding juniper-cascor's copy; the gate runs there with
          JUNIPER_DRIFT_TEST_FORCE_LOCAL=1, so both its decision controls and the byte comparison run
  cascor  a juniper-cascor twin worktree (``--cascor-twin``, clean main) into which ``--setup`` copies the carrier's
          two new files (the fixture and the table test)

``<copies>`` should sit outside every juniper-ml checkout's tmp/: juniper-ml's tests/test_release_train_registry.py
walks tmp/ and a copied pyproject.toml there fails it.

Each arm applies one or more edits (an exact text that must occur once, a JSON edit of a table copy, or main's bytes
of a file), drops the touched modules' bytecode (CPython trusts a .pyc whose size and whole-second mtime match),
runs its commands, and restores every touched file in ``finally:`` from the bytes read before the arm, checking the
sha256. An arm is KILLED when any of its commands exits non-zero, SURVIVED otherwise. Baselines (every command on
the unmutated copies) must pass first. Every run sets the six Sentry variables to "" and the session bus to a dead
path, and drops JUNIPER_CASCOR_LOG_DIR, GITHUB_ACTIONS and (outside eco) JUNIPER_DRIFT_TEST_FORCE_LOCAL.

Usage:
    python3 util/ad-hoc/2026-11-16_flood4r2_d14_mutants.py --setup --ml-carrier <path> --cascor-carrier <path>
        --cascor-twin <path> --copies <dir>
    python3 util/ad-hoc/2026-11-16_flood4r2_d14_mutants.py --group svc|eco|cascor --ml-carrier <path>
        --cascor-twin <path> --copies <dir> --main <juniper-ml main sha> --out <json> --logs <dir> [--only a,b]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table);
    util/ad-hoc/2026-11-15_flood4r2_d14_mutation_check.py (round 1's arms, whose engine this replaces)
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

PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python3.14"
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")

TS = "juniper-service-core/juniper_service_core/websocket/training_stream.py"
MGR = "juniper-service-core/juniper_service_core/websocket/manager.py"
TABLE_TEST = "juniper-service-core/tests/test_websocket_resume_answer_table.py"
FIXTURE = "juniper-service-core/tests/fixtures/ws_resume_answers.json"
C_TS = "src/api/websocket/training_stream.py"
C_MGR = "src/api/websocket/manager.py"
C_TABLE_TEST = "src/tests/unit/api/test_websocket_resume_answer_table.py"
C_FIXTURE = "src/tests/fixtures/ws_resume_answers.json"
GATE = "juniper-ml/tests/test_ws_resume_answer_table_drift.py"
ECO_ML_FIXTURE = "juniper-ml/juniper-service-core/tests/fixtures/ws_resume_answers.json"
ECO_CASCOR_FIXTURE = "juniper-cascor/src/tests/fixtures/ws_resume_answers.json"
SVC_UNIT_FILES = [f"juniper-service-core/tests/{name}.py" for name in ("test_websocket_resume_continuity", "test_websocket_replay_continuity", "test_websocket_training_stream", "test_t2_websocket", "test_websocket_manager_extra")]
CASCOR_WS_FILES = ["src/tests/unit/api/test_websocket_seq_replay.py", "src/tests/unit/api/test_websocket_resume_continuity.py", "src/tests/unit/api/test_websocket_manager.py"]

#: A row whose answer every edit below changes: last_seq=3 (seq 3 of 5 held) in buffered5.
EDIT_OLD = '"buffered5": {"handshake": ["resume_ok(replayed_count=2)", "metrics#4", "metrics#5"], "live": ["metrics#6"]}'
EDIT_NEW = '"buffered5": {"handshake": ["resume_ok(replayed_count=3)", "metrics#4", "metrics#5"], "live": ["metrics#6"]}'
OUT_OF_RANGE_IN_HANDLER = (
    "    if last_seq > ws_manager.current_seq:\n"
    "        await ws_manager.send_personal_message(\n"
    "            websocket,\n"
    '            {"type": "resume_failed", "timestamp": time.time(), "data": {"reason": "out_of_range"}},\n'
    "        )\n"
    "        return False\n\n"
)
RULE4 = '            newest_seq = self._next_seq - 1\n            if last_seq > newest_seq:\n                raise ReplayOutOfRange(f"Requested seq {last_seq} is above the last seq numbered, {newest_seq}")\n'
SWAPPED_SVC = (
    "    if client_server_id is not None and last_seq is not None and client_server_id != ws_manager.server_instance_id:\n"
    '        await ws_manager.send_personal_message(websocket, {"type": "resume_failed", "timestamp": time.time(), "data": {"reason": "server_restarted"}})\n'
    "        return False\n"
)
SWAPPED_CASCOR = (
    "    if client_server_id is not None and client_server_id != ws_manager.server_instance_id:\n"
    '        await ws_manager.send_personal_message(websocket, {"type": "resume_failed", "timestamp": time.time(), "data": {"reason": "server_restarted"}})\n'
    "        return False\n"
)
SNAPSHOT_OLD = '            elif kind == "initial_metrics":\n                if not snapshot_open:\n                    return labels\n                snapshot_open = False\n'
SNAPSHOT_NEW = '            elif kind == "initial_metrics":\n                return labels\n'
MGR_LOCK = '        with self._seq_lock:\n            if self._replay_buffer_max_size <= 0:\n                raise ReplayOutOfRange("Replay buffer disabled")\n'


def _row(table: dict, frame_id: str) -> dict:
    return next(row for row in table["frames"] if row["id"] == frame_id)


def _edit_live(table: dict) -> None:
    _row(table, "last_seq=6")["answers"]["buffered5"]["live"] = ["metrics#7"]


def _drop_last_row(table: dict) -> None:
    table["frames"].pop()


def _evicted_capacity_four(table: dict) -> None:
    table["states"]["evicted"]["replay_buffer_capacity"] = 4


JSON_EDITS = {"edit_live": _edit_live, "drop_last_row": _drop_last_row, "evicted_capacity_four": _evicted_capacity_four}
SVC_BOTH = ["svc_table", "svc_unit"]

#: name, group, what, [(file, old text | "json" | "main", new text | json edit name | None)], commands, source
ARMS = [
    # Round 1 (the builder's 26 arms).
    ("svc-rule1-removed", "svc", "rule 1 removed: a data that is not an object raises again", [(TS, "    if not isinstance(data, dict):\n        data = {}  # null, a list, a string or a number carries no cursor\n", "")], SVC_BOTH, "round1"),
    ("svc-rule1-weakened-null-only", "svc", "rule 1 weakened: only a null data is read as {}", [(TS, "    if not isinstance(data, dict):\n", "    if data is None:\n")], SVC_BOTH, "round1"),
    ("svc-rule2-removed", "svc", "rule 2 removed: back to the None check", [(TS, "if client_server_id is None or not isinstance(last_seq, int) or isinstance(last_seq, bool):", "if client_server_id is None or last_seq is None:")], SVC_BOTH, "round1"),
    ("svc-rule2-bool-allowed", "svc", "rule 2 weakened: a boolean passes as an integer", [(TS, " or not isinstance(last_seq, int) or isinstance(last_seq, bool):", " or not isinstance(last_seq, int):")], SVC_BOTH, "round1"),
    ("svc-rule2-float-allowed", "svc", "rule 2 weakened: a float (NaN, Infinity, 2.5) passes", [(TS, " or not isinstance(last_seq, int) or isinstance(last_seq, bool):", " or not isinstance(last_seq, (int, float)) or isinstance(last_seq, bool):")], SVC_BOTH, "round1"),
    ("svc-rule3-removed", "svc", "rule 3 removed: a negative is answered by buffer state", [(TS, "events = ws_manager.replay_since(max(last_seq, 0))", "events = ws_manager.replay_since(last_seq)")], SVC_BOTH, "round1"),
    ("svc-rule3-weakened", "svc", "rule 3 weakened: clamped to -1, not 0", [(TS, "events = ws_manager.replay_since(max(last_seq, 0))", "events = ws_manager.replay_since(max(last_seq, -1))")], SVC_BOTH, "round1"),
    ("svc-rule4-removed", "svc", "rule 4 removed: a cursor above the last seq numbered is resume_ok again", [(MGR, '            if last_seq > newest_seq:\n                raise ReplayOutOfRange(f"Requested seq {last_seq} is above the last seq numbered, {newest_seq}")\n', "")], SVC_BOTH, "round1"),
    ("svc-rule4-off-by-one", "svc", "rule 4 weakened: one past the newest seq passes", [(MGR, "            if last_seq > newest_seq:\n", "            if last_seq > newest_seq + 1:\n")], SVC_BOTH, "round1"),
    ("svc-rule4-too-strict", "svc", "rule 4 too strict: the newest seq itself is refused", [(MGR, "            if last_seq > newest_seq:\n", "            if last_seq >= newest_seq:\n")], SVC_BOTH, "round1"),
    ("svc-checks-swapped", "svc", "the two checks swapped: server_instance_id is compared before the integer check", [(TS, "    if client_server_id is None or not isinstance(last_seq, int) or isinstance(last_seq, bool):\n", SWAPPED_SVC + "    if client_server_id is None or not isinstance(last_seq, int) or isinstance(last_seq, bool):\n")], SVC_BOTH, "round1"),
    ("svc-clamp-above-integer-check", "svc", "the clamp moved above the integer check", [(TS, '    last_seq = data.get("last_seq")\n', '    last_seq = data.get("last_seq")\n    if last_seq is not None:\n        last_seq = max(last_seq, 0)\n')], SVC_BOTH, "round1"),
    ("svc-harness-label-drops-count", "svc", "harness: the label ignores replayed_count", [(TABLE_TEST, "        return f\"resume_ok(replayed_count={data.get('replayed_count')})\"", '        return "resume_ok(replayed_count=0)"')], ["svc_table"], "round1"),
    ("svc-harness-no-live", "svc", "harness: live frames are not read", [(TABLE_TEST, '        return {"handshake": handshake, "live": live}', '        return {"handshake": handshake, "live": []}')], ["svc_table"], "round1"),
    ("svc-harness-state-ignored", "svc", "harness: every state gets a 1024-slot buffer", [(TABLE_TEST, '    manager = target.new_manager(state["replay_buffer_capacity"])', "    manager = target.new_manager(1024)")], ["svc_table"], "round1"),
    ("svc-row-edited-in-this-copy", "svc", "the table: one row edited in juniper-ml's copy only", [(FIXTURE, EDIT_OLD, EDIT_NEW)], ["svc_table"], "round1"),
    ("cascor-rule2-removed", "cascor", "cascor's integer check removed", [(C_TS, "    if client_server_id is None or not _is_seq_cursor(last_seq):", "    if client_server_id is None or last_seq is None:")], ["cascor_table"], "round1"),
    ("cascor-rule4-removed", "cascor", "cascor's upper bound removed", [(C_MGR, "            if last_seq > newest_seq:\n", "            if False and last_seq > newest_seq:\n")], ["cascor_table"], "round1"),
    ("cascor-rule3-removed", "cascor", "cascor's clamp removed", [(C_TS, "events = ws_manager.replay_since(max(last_seq, 0))", "events = ws_manager.replay_since(last_seq)")], ["cascor_table"], "round1"),
    ("cascor-harness-no-live", "cascor", "harness: live frames are not read", [(C_TABLE_TEST, '        return {"handshake": handshake, "live": live}', '        return {"handshake": handshake, "live": []}')], ["cascor_table"], "round1"),
    ("cascor-row-edited-in-this-copy", "cascor", "the table: one row edited in juniper-cascor's copy only", [(C_FIXTURE, EDIT_OLD, EDIT_NEW)], ["cascor_table"], "round1"),
    ("gate-row-edited-in-cascor-copy", "eco", "the cascor copy differs by one row", [(ECO_CASCOR_FIXTURE, EDIT_OLD, EDIT_NEW)], ["eco_gate"], "round1"),
    ("gate-row-edited-in-ml-copy", "eco", "the juniper-ml copy differs by one row", [(ECO_ML_FIXTURE, EDIT_OLD, EDIT_NEW)], ["eco_gate"], "round1"),
    ("gate-first-difference-blind", "eco", "gate: first_difference reports no difference", [(GATE, "    if mine == theirs:\n        return None\n", "    return None\n")], ["eco_gate"], "round1"),
    ("gate-absent-copy-skips", "eco", "gate: an absent copy skips instead of failing", [(GATE, "    if not path.is_file():\n        return FAIL, (", "    if not path.is_file():\n        return SKIP, (")], ["eco_gate"], "round1"),
    ("gate-root-never-found", "eco", "gate: the ecosystem root is never found", [(GATE, "            if (candidate / _SIBLING_REPO).is_dir():\n                return candidate\n", "            if (candidate / _SIBLING_REPO).is_dir():\n                return None\n")], ["eco_gate"], "round1"),
    # The code lens's 21 arms.
    ("svc-main-source", "svc", "both source files back to main's (the carrier's tests against main's code)", [(TS, "main", None), (MGR, "main", None)], SVC_BOTH, "mn1"),
    ("svc-rule1-list-passes", "svc", "rule 1 weakened: a list data is not replaced by {}", [(TS, "    if not isinstance(data, dict):\n", "    if not isinstance(data, (dict, list)):\n")], SVC_BOTH, "mn1"),
    ("svc-rule2-integral-float-accepted", "svc", "rule 2 weakened: an integral float (3.0, 1e2, -1.0, -0.0) is read as an int", [(TS, "    # ``json.loads`` accepts ``NaN``", "    if isinstance(last_seq, float) and last_seq.is_integer():\n        last_seq = int(last_seq)\n    # ``json.loads`` accepts ``NaN``")], SVC_BOTH, "mn1"),
    ("svc-rule2-digit-string-accepted", "svc", "rule 2 weakened: a digit string ('3', '-1') is read as an int", [(TS, "    # ``json.loads`` accepts ``NaN``", '    if isinstance(last_seq, str) and last_seq.lstrip("-").isdigit():\n        last_seq = int(last_seq)\n    # ``json.loads`` accepts ``NaN``')], SVC_BOTH, "mn1"),
    ("svc-missing-id-reaches-mismatch", "svc", "a missing server_instance_id is no longer malformed: it falls through to the mismatch check", [(TS, "    if client_server_id is None or not isinstance(last_seq, int) or isinstance(last_seq, bool):\n", "    if not isinstance(last_seq, int) or isinstance(last_seq, bool):\n")], SVC_BOTH, "mn1"),
    ("svc-clamp-moved-into-replay-since", "svc", "rule 3's clamp moved from the handler into replay_since (wire-equivalent; changes the public replay_since)", [(TS, "        events = ws_manager.replay_since(max(last_seq, 0))\n", "        events = ws_manager.replay_since(last_seq)\n"), (MGR, MGR_LOCK, "        last_seq = max(last_seq, 0)\n" + MGR_LOCK)], SVC_BOTH, "mn1"),
    ("svc-rule4-moved-into-handler", "svc", "rule 4 moved from replay_since into the handler (wire-equivalent; replay_since returns [] above the newest again)", [(MGR, RULE4, ""), (TS, "    try:\n        # A cursor below 0 is read as 0", OUT_OF_RANGE_IN_HANDLER + "    try:\n        # A cursor below 0 is read as 0")], SVC_BOTH, "mn1"),
    ("svc-harness-snapshot-metrics-ends-handshake", "svc", "harness: the snapshot's initial_metrics is taken as the sentinel's answer", [(TABLE_TEST, SNAPSHOT_OLD, SNAPSHOT_NEW)], ["svc_table"], "mn1"),
    ("svc-harness-label-drops-seq", "svc", "harness: a numbered broadcast is labelled by its type only", [(TABLE_TEST, "        return f\"{kind}#{frame['seq']}\"\n", '        return f"{kind}"\n')], ["svc_table"], "mn1"),
    ("svc-table-live-edited-ml-copy", "svc", "table: one row's live answer edited in juniper-ml's copy only", [(FIXTURE, "json", "edit_live")], ["svc_table"], "mn1"),
    ("svc-table-row-deleted-ml-copy", "svc", "table: the last row deleted from juniper-ml's copy only", [(FIXTURE, "json", "drop_last_row")], ["svc_table"], "mn1"),
    ("svc-table-evicted-capacity-ml-copy", "svc", "table: the evicted state's capacity 3 -> 4 in juniper-ml's copy only", [(FIXTURE, "json", "evicted_capacity_four")], ["svc_table"], "mn1"),
    ("gate-absent-copy-branch-inverted", "eco", "gate: the absent-copy branch inverted (an existing copy fails, an absent one is read)", [(GATE, "    if not path.is_file():\n        return FAIL", "    if path.is_file():\n        return FAIL")], ["eco_gate"], "mn1"),
    ("gate-no-sibling-fails", "eco", "gate: no sibling checkout fails instead of skipping", [(GATE, '        return SKIP, f"no {_SIBLING_REPO} checkout', '        return FAIL, f"no {_SIBLING_REPO} checkout')], ["eco_gate"], "mn1"),
    ("gate-compares-data-not-bytes", "eco", "gate: copies holding the same data in different bytes pass", [(GATE, "    if mine == theirs:\n        return None\n", "    if json.loads(mine) == json.loads(theirs):\n        return None\n")], ["eco_gate"], "mn1"),
    ("gate-walks-two-levels", "eco", "gate: the upward walk stops after two levels (a nested session worktree finds no root)", [(GATE, "def find_ecosystem_root(start: Path, levels: int = 6)", "def find_ecosystem_root(start: Path, levels: int = 2)")], ["eco_gate"], "mn1"),
    ("cascor-rule1-removed", "cascor", "cascor's data guard removed: a data that is not an object raises at data.get", [(C_TS, '    data = msg.get("data")\n    if not isinstance(data, dict):\n        return None, None\n', '    data = msg.get("data", {})\n')], ["cascor_table"], "mn1"),
    ("cascor-checks-swapped", "cascor", "cascor: server_instance_id compared before the integer check", [(C_TS, "    if client_server_id is None or not _is_seq_cursor(last_seq):\n", SWAPPED_CASCOR + "    if client_server_id is None or not _is_seq_cursor(last_seq):\n")], ["cascor_table"], "mn1"),
    ("cascor-clamp-above-integer-check", "cascor", "cascor: a numeric cursor is clamped before the integer check", [(C_TS, "    if client_server_id is None or not _is_seq_cursor(last_seq):\n", "    if isinstance(last_seq, (int, float)) and not isinstance(last_seq, bool):\n        last_seq = max(last_seq, 0)\n    if client_server_id is None or not _is_seq_cursor(last_seq):\n")], ["cascor_table"], "mn1"),
    ("cascor-rule4-moved-into-handler", "cascor", "cascor: rule 4 moved from replay_since into the handler (wire-equivalent)", [(C_MGR, RULE4, ""), (C_TS, "    try:\n        # A cursor below 0 holds no more than 0 does", OUT_OF_RANGE_IN_HANDLER + "    try:\n        # A cursor below 0 holds no more than 0 does")], ["cascor_table", "cascor_ws"], "mn1"),
    ("cascor-harness-snapshot-metrics-ends-handshake", "cascor", "cascor harness: the snapshot's initial_metrics is taken as the sentinel's answer", [(C_TABLE_TEST, SNAPSHOT_OLD, SNAPSHOT_NEW)], ["cascor_table"], "mn1"),
    # This round.
    ("svc-replay-since-also-clamps", "svc", "replay_since reads a negative as 0 too (handler unchanged): the public method stops raising for a negative", [(MGR, MGR_LOCK, "        last_seq = max(last_seq, 0)\n" + MGR_LOCK)], ["svc_unit"], "round2"),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def roots_of(args) -> dict:
    return {"svc": args.copies / "svc", "eco": args.copies / "eco", "cascor": args.cascor_twin}


def commands_of(roots: dict) -> dict:
    svc_path = os.pathsep.join([str(roots["svc"] / "juniper-service-core"), str(roots["svc"] / "juniper-model-core")])
    return {
        "svc_table": (roots["svc"], [PYTHON, "-m", "pytest", TABLE_TEST, "-p", "no:cacheprovider", "-q"], {"PYTHONPATH": svc_path}),
        "svc_unit": (roots["svc"], [PYTHON, "-m", "pytest", *SVC_UNIT_FILES, "-p", "no:cacheprovider", "-q"], {"PYTHONPATH": svc_path}),
        "eco_gate": (roots["eco"] / "juniper-ml", [PYTHON, "-m", "unittest", "-v", "tests/test_ws_resume_answer_table_drift.py"], {"JUNIPER_DRIFT_TEST_FORCE_LOCAL": "1"}),
        "cascor_table": (roots["cascor"], [PYTHON, "-m", "pytest", "-m", "unit and not slow", C_TABLE_TEST, "--timeout=60", "-p", "no:cacheprovider", "-q"], {}),
        "cascor_ws": (roots["cascor"], [PYTHON, "-m", "pytest", "-m", "unit and not slow", *CASCOR_WS_FILES, "--timeout=60", "-p", "no:cacheprovider", "-q"], {}),
    }


def drop_bytecode(root: Path, rels) -> None:
    for rel in rels:
        path = root / rel
        if path.suffix == ".py":
            for cached in (path.parent / "__pycache__").glob(f"{path.stem}.*.pyc"):
                cached.unlink()


def main_bytes(ml_carrier: Path, main: str, rel: str) -> bytes:
    done = subprocess.run(["git", "show", f"{main}:{rel}"], cwd=str(ml_carrier), capture_output=True, timeout=60, check=True)
    return done.stdout


def mutated(args, rel: str, original: bytes, spec: str, payload) -> bytes:
    if spec == "main":
        return main_bytes(args.ml_carrier, args.main, rel)
    if spec == "json":
        table = json.loads(original.decode("utf-8"))
        JSON_EDITS[payload](table)
        return (json.dumps(table, indent=2) + "\n").encode("utf-8")
    text = original.decode("utf-8")
    if text.count(spec) != 1:
        raise SystemExit(f"{rel}: edit text occurs {text.count(spec)} times, not once: {spec[:80]!r}")
    return text.replace(spec, payload).encode("utf-8")


def run(commands: dict, command: str, logs: Path, label: str) -> dict:
    cwd, argv, extra = commands[command]
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus", "PYTHONDONTWRITEBYTECODE": "1"}
    for name in ("JUNIPER_CASCOR_LOG_DIR", "GITHUB_ACTIONS", "JUNIPER_DRIFT_TEST_FORCE_LOCAL", "PYTHONPATH"):
        env.pop(name, None)
    env.update(extra)
    log = logs / f"{label}.{command}.log"
    started = time.monotonic()
    with open(log, "w", encoding="utf-8") as handle:
        try:
            code = subprocess.run(argv, cwd=str(cwd), env=env, stdout=handle, stderr=subprocess.STDOUT, timeout=900, check=False).returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
    text = log.read_text(encoding="utf-8", errors="replace")
    counts = {key: int(match.group(1)) for key in ("failed", "passed", "error", "errors", "skipped") for match in [re.search(rf"(\d+) {key}\b", text)] if match}
    unit = re.search(r"FAILED \((.*?)\)", text)
    return {"command": command, "exit": code, "seconds": round(time.monotonic() - started, 1), "counts": counts, "unittest": unit.group(1) if unit else ("OK" if re.search(r"^OK", text, re.MULTILINE) else None), "log": str(log)}


def setup(args) -> int:
    roots = roots_of(args)
    ignore = shutil.ignore_patterns("__pycache__", "*.egg-info", ".pytest_cache", "build", "dist")
    for name in ("svc", "eco"):
        if roots[name].exists():
            shutil.rmtree(roots[name])
    shutil.copytree(args.ml_carrier / "juniper-service-core", roots["svc"] / "juniper-service-core", ignore=ignore)
    shutil.copytree(args.ml_carrier / "juniper-model-core", roots["svc"] / "juniper-model-core", ignore=ignore)
    for target, source in ((GATE, args.ml_carrier / "tests" / "test_ws_resume_answer_table_drift.py"), (ECO_ML_FIXTURE, args.ml_carrier / FIXTURE), (ECO_CASCOR_FIXTURE, args.cascor_carrier / C_FIXTURE)):
        (roots["eco"] / target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, roots["eco"] / target)
    for rel in (C_FIXTURE, C_TABLE_TEST):
        (roots["cascor"] / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.cascor_carrier / rel, roots["cascor"] / rel)
    print(json.dumps({"roots": {name: str(path) for name, path in roots.items()}}, indent=1))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--setup", action="store_true")
    parser.add_argument("--group", choices=("svc", "eco", "cascor"))
    parser.add_argument("--ml-carrier", type=Path, required=True)
    parser.add_argument("--cascor-carrier", type=Path)
    parser.add_argument("--cascor-twin", type=Path, required=True)
    parser.add_argument("--copies", type=Path, required=True)
    parser.add_argument("--main", default="origin/main")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--logs", type=Path)
    parser.add_argument("--only", default="", help="comma-separated arm names")
    parser.add_argument("--source", default="", help="comma-separated arm sources (round1, mn1, round2)")
    args = parser.parse_args()
    if args.setup:
        return setup(args)

    roots = roots_of(args)
    commands = commands_of(roots)
    root = roots[args.group]
    arms = [arm for arm in ARMS if arm[1] == args.group and (not args.only or arm[0] in args.only.split(",")) and (not args.source or arm[5] in args.source.split(","))]
    touched = sorted({rel for arm in arms for rel, _old, _new in arm[3]})
    baseline = {rel: (root / rel).read_bytes() for rel in touched}
    report = {"group": args.group, "root": str(root), "baseline_sha256": {rel: sha256_bytes(data) for rel, data in baseline.items()}, "baselines": [], "arms": []}
    print("SHA256 BEFORE THE RUN", json.dumps(report["baseline_sha256"], indent=1), flush=True)
    args.logs.mkdir(parents=True, exist_ok=True)

    # Every arm's edit must apply to the unmutated copy before anything runs.
    for name, _group, _what, edits, _commands, _source in arms:
        for rel, spec, payload in edits:
            mutated(args, rel, baseline[rel], spec, payload)

    for command in sorted({command for arm in arms for command in arm[4]}):
        drop_bytecode(root, touched)
        outcome = run(commands, command, args.logs, f"baseline-{args.group}")
        report["baselines"].append(outcome)
        print(f"baseline {command}: exit {outcome['exit']} {outcome['counts'] or outcome['unittest']}", flush=True)
        if outcome["exit"] != 0:
            raise SystemExit(f"baseline {command} does not pass; no arm is meaningful")

    for name, _group, what, edits, arm_commands, source in arms:
        row = {"arm": name, "source": source, "what": what, "runs": []}
        try:
            for rel, spec, payload in edits:
                (root / rel).write_bytes(mutated(args, rel, (root / rel).read_bytes(), spec, payload))
            drop_bytecode(root, touched)
            for command in arm_commands:
                row["runs"].append(run(commands, command, args.logs, name))
        finally:
            for rel, data in baseline.items():
                (root / rel).write_bytes(data)
            drop_bytecode(root, touched)
            row["restored"] = {rel: sha256_bytes((root / rel).read_bytes()) for rel in touched} == report["baseline_sha256"]
        row["killed_by"] = [item["command"] for item in row["runs"] if item["exit"] != 0]
        row["result"] = "killed" if row["killed_by"] else "survived"
        report["arms"].append(row)
        args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        summary = "; ".join(f"{item['command']}: exit {item['exit']} {item['counts'] or item['unittest']}" for item in row["runs"])
        print(f"{name}\t{row['result']}\trestored={row['restored']}\t{summary}", flush=True)
        if not row["restored"]:
            raise SystemExit("a file did not restore to its baseline sha256: stop")
    report["killed"] = sum(1 for row in report["arms"] if row["result"] == "killed")
    report["survived"] = [row["arm"] for row in report["arms"] if row["result"] == "survived"]
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"{args.group}: {report['killed']} of {len(report['arms'])} killed; survived {report['survived']}", flush=True)
    return 0 if not report["survived"] else 1


if __name__ == "__main__":
    sys.exit(main())
