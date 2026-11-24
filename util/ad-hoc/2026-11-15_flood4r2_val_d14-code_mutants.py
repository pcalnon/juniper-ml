"""
The D-14 code lens's own mutants, run in the validator's copies (never in a carrier).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (flood-4 round-2 validation, D-14 code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 disposition, D-14 (service-core resume cursor rules + shared answer table)

Usage: python3 <this file> --group svc|eco|cascor --out <json> --logs <dir> [--only <arm>[,<arm>...]] [--hashes-only]
Each arm applies exact-string edits (each old text must occur once) or a JSON edit to files of one copy, runs the
arm's commands, then restores the original bytes in a `finally:` block and checks every touched file's sha256
against the baseline taken before the run. A command that exits non-zero kills the arm. Runs carry the six
Sentry variables as "" and no JUNIPER_CASCOR_LOG_DIR.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
ORCHESTRATOR = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert"
ML = JUNIPER / "worktrees" / "juniper-ml--val--flood4r2-d14-code--20261115-1554--edea2eb1"
CASCOR = JUNIPER / "worktrees" / "juniper-cascor--val--flood4r2-d14-code--20261115-1554--67588488"
ML_MAIN = "edea2eb16700aa0a712cfbaeea7a7e2291aac1e7"
SVC_PY = str(ML / "tmp" / "val-d14" / "venv312" / "bin" / "python")
CASCOR_PY = str(CASCOR / "tmp" / "val-d14" / "venv-ci-ws" / "bin" / "python")
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")

TS = "juniper-service-core/juniper_service_core/websocket/training_stream.py"
MGR = "juniper-service-core/juniper_service_core/websocket/manager.py"
TABLE_TEST = "juniper-service-core/tests/test_websocket_resume_answer_table.py"
FIXTURE = "juniper-service-core/tests/fixtures/ws_resume_answers.json"
GATE = "tests/test_ws_resume_answer_table_drift.py"
C_TS = "src/api/websocket/training_stream.py"
C_MGR = "src/api/websocket/manager.py"
C_TABLE_TEST = "src/tests/unit/api/test_websocket_resume_answer_table.py"

SVC_UNIT_FILES = [f"juniper-service-core/tests/{name}.py" for name in ("test_websocket_resume_continuity", "test_websocket_replay_continuity", "test_websocket_training_stream", "test_t2_websocket", "test_websocket_manager_extra")]
COMMANDS = {
    "svc_table": (ML, [SVC_PY, "-m", "pytest", TABLE_TEST, "-p", "no:cacheprovider"]),
    "svc_unit": (ML, [SVC_PY, "-m", "pytest", *SVC_UNIT_FILES, "-p", "no:cacheprovider"]),
    "eco_controls": (ML, [sys.executable, "-m", "unittest", GATE]),
    "cascor_table": (CASCOR, [CASCOR_PY, "-m", "pytest", "-m", "unit and not slow", C_TABLE_TEST, "--timeout=60", "-p", "no:cacheprovider"]),
    "cascor_ws": (CASCOR, [CASCOR_PY, "-m", "pytest", "-m", "unit and not slow", "src/tests/unit/api/test_websocket_seq_replay.py", "src/tests/unit/api/test_websocket_resume_continuity.py", "src/tests/unit/api/test_websocket_manager.py", "--timeout=60", "-p", "no:cacheprovider"]),
}

OUT_OF_RANGE_IN_HANDLER = (
    "    if last_seq > ws_manager.current_seq:\n"
    "        await ws_manager.send_personal_message(\n"
    "            websocket,\n"
    '            {"type": "resume_failed", "timestamp": time.time(), "data": {"reason": "out_of_range"}},\n'
    "        )\n"
    "        return False\n\n"
)
RULE4_SVC = '            newest_seq = self._next_seq - 1\n            if last_seq > newest_seq:\n                raise ReplayOutOfRange(f"Requested seq {last_seq} is above the last seq numbered, {newest_seq}")\n'
RULE4_CASCOR = RULE4_SVC
SWAPPED_CASCOR = (
    "    if client_server_id is not None and client_server_id != ws_manager.server_instance_id:\n"
    '        await ws_manager.send_personal_message(websocket, {"type": "resume_failed", "timestamp": time.time(), "data": {"reason": "server_restarted"}})\n'
    "        return False\n"
)
SNAPSHOT_OLD = '            elif kind == "initial_metrics":\n                if not snapshot_open:\n                    return labels\n                snapshot_open = False\n'
SNAPSHOT_NEW = '            elif kind == "initial_metrics":\n                return labels\n'


def _row(table: dict, frame_id: str) -> dict:
    return next(row for row in table["frames"] if row["id"] == frame_id)


def edit_live(table: dict) -> None:
    _row(table, "last_seq=6")["answers"]["buffered5"]["live"] = ["metrics#7"]


def drop_last_row(table: dict) -> None:
    table["frames"].pop()


def evicted_capacity_four(table: dict) -> None:
    table["states"]["evicted"]["replay_buffer_capacity"] = 4


JSON_EDITS = {"edit_live": edit_live, "drop_last_row": drop_last_row, "evicted_capacity_four": evicted_capacity_four}

ARMS = [
    # --- juniper-service-core handler and manager (svc) ---
    {"name": "svc-main-source", "group": "svc", "what": "both source files back to main's (the carrier's tests against main's code)", "edits": [(TS, "main", None), (MGR, "main", None)], "commands": ["svc_table", "svc_unit"]},
    {"name": "svc-rule1-list-passes", "group": "svc", "what": "rule 1 weakened: a list data is not replaced by {}", "edits": [(TS, "    if not isinstance(data, dict):\n", "    if not isinstance(data, (dict, list)):\n")], "commands": ["svc_table", "svc_unit"]},
    {"name": "svc-rule2-integral-float-accepted", "group": "svc", "what": "rule 2 weakened: an integral float (3.0, 1e2, -1.0, -0.0) is read as an int", "edits": [(TS, "    # ``json.loads`` accepts ``NaN``", "    if isinstance(last_seq, float) and last_seq.is_integer():\n        last_seq = int(last_seq)\n    # ``json.loads`` accepts ``NaN``")], "commands": ["svc_table", "svc_unit"]},
    {"name": "svc-rule2-digit-string-accepted", "group": "svc", "what": "rule 2 weakened: a digit string ('3', '-1') is read as an int", "edits": [(TS, "    # ``json.loads`` accepts ``NaN``", '    if isinstance(last_seq, str) and last_seq.lstrip("-").isdigit():\n        last_seq = int(last_seq)\n    # ``json.loads`` accepts ``NaN``')], "commands": ["svc_table", "svc_unit"]},
    {"name": "svc-missing-id-reaches-mismatch", "group": "svc", "what": "a missing server_instance_id is no longer malformed: it falls through to the mismatch check", "edits": [(TS, "    if client_server_id is None or not isinstance(last_seq, int) or isinstance(last_seq, bool):\n", "    if not isinstance(last_seq, int) or isinstance(last_seq, bool):\n")], "commands": ["svc_table", "svc_unit"]},
    {"name": "svc-clamp-moved-into-replay-since", "group": "svc", "what": "rule 3's clamp moved from the handler into replay_since (wire-equivalent; changes the public replay_since)", "edits": [(TS, "        events = ws_manager.replay_since(max(last_seq, 0))\n", "        events = ws_manager.replay_since(last_seq)\n"), (MGR, '        with self._seq_lock:\n            if self._replay_buffer_max_size <= 0:\n                raise ReplayOutOfRange("Replay buffer disabled")\n', '        last_seq = max(last_seq, 0)\n        with self._seq_lock:\n            if self._replay_buffer_max_size <= 0:\n                raise ReplayOutOfRange("Replay buffer disabled")\n')], "commands": ["svc_table", "svc_unit"]},
    {"name": "svc-rule4-moved-into-handler", "group": "svc", "what": "rule 4 moved from replay_since into the handler (wire-equivalent; replay_since returns [] above the newest again)", "edits": [(MGR, RULE4_SVC, ""), (TS, "    try:\n        # A cursor below 0 is read as 0", OUT_OF_RANGE_IN_HANDLER + "    try:\n        # A cursor below 0 is read as 0")], "commands": ["svc_table", "svc_unit"]},
    {"name": "svc-harness-snapshot-metrics-ends-handshake", "group": "svc", "what": "harness: the snapshot's initial_metrics is taken as the sentinel's answer", "edits": [(TABLE_TEST, SNAPSHOT_OLD, SNAPSHOT_NEW)], "commands": ["svc_table"]},
    {"name": "svc-harness-label-drops-seq", "group": "svc", "what": "harness: a numbered broadcast is labelled by its type only", "edits": [(TABLE_TEST, "        return f\"{kind}#{frame['seq']}\"\n", '        return f"{kind}"\n')], "commands": ["svc_table"]},
    {"name": "svc-table-live-edited-ml-copy", "group": "svc", "what": "table: one row's live answer edited in juniper-ml's copy only", "edits": [(FIXTURE, "json", "edit_live")], "commands": ["svc_table"]},
    {"name": "svc-table-row-deleted-ml-copy", "group": "svc", "what": "table: the last row deleted from juniper-ml's copy only", "edits": [(FIXTURE, "json", "drop_last_row")], "commands": ["svc_table", "eco_controls"]},
    {"name": "svc-table-evicted-capacity-ml-copy", "group": "svc", "what": "table: the evicted state's capacity 3 -> 4 in juniper-ml's copy only", "edits": [(FIXTURE, "json", "evicted_capacity_four")], "commands": ["svc_table"]},
    # --- juniper-ml drift gate (eco) ---
    {"name": "gate-absent-copy-branch-inverted", "group": "eco", "what": "gate: the absent-copy branch inverted (an existing copy fails, an absent one is read)", "edits": [(GATE, "    if not path.is_file():\n        return FAIL", "    if path.is_file():\n        return FAIL")], "commands": ["eco_controls"]},
    {"name": "gate-no-sibling-fails", "group": "eco", "what": "gate: no sibling checkout fails instead of skipping", "edits": [(GATE, '        return SKIP, f"no {_SIBLING_REPO} checkout', '        return FAIL, f"no {_SIBLING_REPO} checkout')], "commands": ["eco_controls"]},
    {"name": "gate-compares-data-not-bytes", "group": "eco", "what": "gate: copies holding the same data in different bytes pass", "edits": [(GATE, "    if mine == theirs:\n        return None\n", "    if json.loads(mine) == json.loads(theirs):\n        return None\n")], "commands": ["eco_controls"]},
    {"name": "gate-walks-two-levels", "group": "eco", "what": "gate: the upward walk stops after two levels (a nested session worktree finds no root)", "edits": [(GATE, "def find_ecosystem_root(start: Path, levels: int = 6)", "def find_ecosystem_root(start: Path, levels: int = 2)")], "commands": ["eco_controls"]},
    # --- juniper-cascor handler (unchanged by the carrier) against the carrier's table test ---
    {"name": "cascor-rule1-removed", "group": "cascor", "what": "cascor's data guard removed: a data that is not an object raises at data.get", "edits": [(C_TS, '    data = msg.get("data")\n    if not isinstance(data, dict):\n        return None, None\n', '    data = msg.get("data", {})\n')], "commands": ["cascor_table"]},
    {"name": "cascor-checks-swapped", "group": "cascor", "what": "cascor: server_instance_id compared before the integer check", "edits": [(C_TS, "    if client_server_id is None or not _is_seq_cursor(last_seq):\n", SWAPPED_CASCOR + "    if client_server_id is None or not _is_seq_cursor(last_seq):\n")], "commands": ["cascor_table"]},
    {"name": "cascor-clamp-above-integer-check", "group": "cascor", "what": "cascor: a numeric cursor is clamped before the integer check", "edits": [(C_TS, "    if client_server_id is None or not _is_seq_cursor(last_seq):\n", "    if isinstance(last_seq, (int, float)) and not isinstance(last_seq, bool):\n        last_seq = max(last_seq, 0)\n    if client_server_id is None or not _is_seq_cursor(last_seq):\n")], "commands": ["cascor_table"]},
    {"name": "cascor-rule4-moved-into-handler", "group": "cascor", "what": "cascor: rule 4 moved from replay_since into the handler (wire-equivalent)", "edits": [(C_MGR, RULE4_CASCOR, ""), (C_TS, "    try:\n        # A cursor below 0 holds no more than 0 does", OUT_OF_RANGE_IN_HANDLER + "    try:\n        # A cursor below 0 holds no more than 0 does")], "commands": ["cascor_table", "cascor_ws"]},
    {"name": "cascor-harness-snapshot-metrics-ends-handshake", "group": "cascor", "what": "cascor harness: the snapshot's initial_metrics is taken as the sentinel's answer", "edits": [(C_TABLE_TEST, SNAPSHOT_OLD, SNAPSHOT_NEW)], "commands": ["cascor_table"]},
]


def root_of(group: str) -> Path:
    return CASCOR if group == "cascor" else ML


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def drop_bytecode(root: Path, rels: list) -> None:
    """Delete the cached bytecode of every touched module.

    CPython accepts a ``.pyc`` whose recorded source size and whole-second mtime match the source. A mutant
    that keeps the file's size (``6`` -> ``2``), restored within the same second, otherwise leaves its own
    bytecode in force for the next run of the RESTORED file (observed on this run's gate-walks-two-levels).
    """
    for rel in rels:
        path = root / rel
        if path.suffix == ".py":
            for cached in (path.parent / "__pycache__").glob(f"{path.stem}.*.pyc"):
                cached.unlink()


def main_bytes(rel: str) -> bytes:
    proc = subprocess.run(["git", "show", f"{ML_MAIN}:{rel}"], cwd=str(ORCHESTRATOR), capture_output=True, timeout=60, check=True)
    return proc.stdout


def mutated(rel: str, original: bytes, spec: str, payload) -> bytes:
    """The bytes of ``rel`` after one edit: main's copy, a JSON edit, or one exact-string replacement."""
    if spec == "main":
        return main_bytes(rel)
    if spec == "json":
        table = json.loads(original.decode("utf-8"))
        JSON_EDITS[payload](table)
        return (json.dumps(table, indent=2) + "\n").encode("utf-8")
    text = original.decode("utf-8")
    count = text.count(spec)
    if count != 1:
        raise SystemExit(f"edit text occurs {count} times, not once: {spec[:80]!r}")
    return text.replace(spec, payload).encode("utf-8")


def run(command: str, logs: Path, arm: str) -> dict:
    cwd, argv = COMMANDS[command]
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus"}
    for name in ("JUNIPER_CASCOR_LOG_DIR", "GITHUB_ACTIONS", "JUNIPER_DRIFT_TEST_FORCE_LOCAL"):
        env.pop(name, None)
    log = logs / f"{arm}.{command}.log"
    started = time.monotonic()
    with open(log, "w", encoding="utf-8") as handle:
        try:
            code = subprocess.run(argv, cwd=str(cwd), env=env, stdout=handle, stderr=subprocess.STDOUT, timeout=900, check=False).returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
    with open(log, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    counts = {key: int(match.group(1)) for key in ("failed", "passed", "error", "errors") for match in [re.search(rf"(\d+) {key}\b", text)] if match}
    unit = re.search(r"FAILED \((.*?)\)", text)
    return {"command": command, "exit": code, "seconds": round(time.monotonic() - started, 1), "counts": counts, "unittest": unit.group(1) if unit else ("OK" if re.search(r"^OK", text, re.MULTILINE) else None), "log": str(log)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--group", choices=("svc", "eco", "cascor"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--only", default="")
    parser.add_argument("--hashes-only", action="store_true")
    args = parser.parse_args()
    arms = [arm for arm in ARMS if arm["group"] == args.group and (not args.only or arm["name"] in args.only.split(","))]
    root = root_of(args.group)
    touched = sorted({rel for arm in arms for rel, _, _ in arm["edits"]})
    baseline = {rel: (root / rel).read_bytes() for rel in touched}
    report = {"group": args.group, "root": str(root), "baseline_sha256": {rel: sha256_bytes(data) for rel, data in baseline.items()}, "arms": []}
    print(json.dumps(report["baseline_sha256"], indent=2))
    if args.hashes_only:
        return 0
    args.logs.mkdir(parents=True, exist_ok=True)
    for arm in arms:
        row = {"arm": arm["name"], "what": arm["what"], "runs": []}
        try:
            for rel, spec, payload in arm["edits"]:
                (root / rel).write_bytes(mutated(rel, (root / rel).read_bytes(), spec, payload))
            drop_bytecode(root, touched)
            for command in arm["commands"]:
                row["runs"].append(run(command, args.logs, arm["name"]))
        finally:
            for rel, data in baseline.items():
                (root / rel).write_bytes(data)
            drop_bytecode(root, touched)
            after = {rel: sha256_bytes((root / rel).read_bytes()) for rel in touched}
            row["restored"] = after == report["baseline_sha256"]
        row["killed_by"] = [run_row["command"] for run_row in row["runs"] if run_row["exit"] != 0]
        row["result"] = "killed" if row["killed_by"] else "survived"
        report["arms"].append(row)
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
        summary = "; ".join(f"{r['command']}: exit {r['exit']} {r['counts'] or r['unittest']}" for r in row["runs"])
        print(f"{arm['name']}\t{row['result']}\trestored={row['restored']}\t{summary}", flush=True)
        if not row["restored"]:
            raise SystemExit("a file did not restore to its baseline sha256: stop")
    return 0


if __name__ == "__main__":
    sys.exit(main())
