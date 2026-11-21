"""
Verify the D-14 code lens's proposed fixes in the validator's copies, then restore the copies byte for byte.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (flood-4 round-2 validation, D-14 code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 disposition, D-14 (service-core resume cursor rules + shared answer table)

Usage: python3 <this file> --out <json> --logs <dir> --step floor|ml|cascor
floor:  the carrier's harness as it is, on the [test] extra's floors (uvicorn 0.29.0, websockets 12.0).
ml:     F1's fix in juniper-ml's harness (on websockets 17.4 and on the floors), and F3's fix (alone, and with the
        surviving clamp mutant, which it must kill).
cascor: F1's fix in juniper-cascor's harness, on cascor CI's websockets 17.4 / uvicorn 0.54.0.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
ML = JUNIPER / "worktrees" / "juniper-ml--val--flood4r2-d14-code--20261115-1554--edea2eb1"
CASCOR = JUNIPER / "worktrees" / "juniper-cascor--val--flood4r2-d14-code--20261115-1554--67588488"
PY312 = str(ML / "tmp" / "val-d14" / "venv312" / "bin" / "python")
PY_FLOOR = str(ML / "tmp" / "val-d14" / "venv312-floor" / "bin" / "python")
PY_CASCOR = str(CASCOR / "tmp" / "val-d14" / "venv-ci-ws" / "bin" / "python")
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
WARNING = "connect() must be used as a context manager"

ML_TABLE = "juniper-service-core/tests/test_websocket_resume_answer_table.py"
CASCOR_TABLE = "src/tests/unit/api/test_websocket_resume_answer_table.py"
CONTINUITY = "juniper-service-core/tests/test_websocket_resume_continuity.py"
TS = "juniper-service-core/juniper_service_core/websocket/training_stream.py"
MGR = "juniper-service-core/juniper_service_core/websocket/manager.py"
SVC_UNIT = [f"juniper-service-core/tests/{name}.py" for name in ("test_websocket_resume_continuity", "test_websocket_replay_continuity", "test_websocket_training_stream", "test_t2_websocket", "test_websocket_manager_extra")]

# F1: open the client as a context manager (the same three edits fit both harnesses, which share this code).
F1_EDITS = [
    (
        '    def __init__(self, port: int) -> None:\n        # websockets 15+ would route through a proxy named in the environment; this is loopback.\n        options = {"proxy": None} if "proxy" in inspect.signature(connect).parameters else {}\n        self._socket = connect(f"ws://127.0.0.1:{port}/ws/training", origin=ORIGIN, open_timeout=RECV_TIMEOUT_S, close_timeout=2.0, **options)\n        self.close: str | None = None\n',
        "    def __init__(self, connection) -> None:\n        self._socket = connection\n        self.close: str | None = None\n",
    ),
    ("    def shut(self) -> None:\n        self._socket.close()\n\n", ""),
    (
        "    client = _Client(server.port)\n    try:\n",
        '    # websockets 15+ would route through a proxy named in the environment; this is loopback.\n    options = {"proxy": None} if "proxy" in inspect.signature(connect).parameters else {}\n    with connect(f"ws://127.0.0.1:{server.port}/ws/training", origin=ORIGIN, open_timeout=RECV_TIMEOUT_S, close_timeout=2.0, **options) as connection:\n        client = _Client(connection)\n',
    ),
    ("        return {\"handshake\": handshake, \"live\": live}\n    finally:\n        client.shut()\n", "        return {\"handshake\": handshake, \"live\": live}\n"),
]
F3_EDITS = [("        mgr.replay_since(4)\n", "        mgr.replay_since(4)\n    with pytest.raises(ReplayOutOfRange):  # replay_since does not clamp; the handshake reads a negative as 0 first\n        mgr.replay_since(-1)\n")]
CLAMP_MUTANT = [
    (TS, "        events = ws_manager.replay_since(max(last_seq, 0))\n", "        events = ws_manager.replay_since(last_seq)\n"),
    (MGR, '        with self._seq_lock:\n            if self._replay_buffer_max_size <= 0:\n                raise ReplayOutOfRange("Replay buffer disabled")\n', '        last_seq = max(last_seq, 0)\n        with self._seq_lock:\n            if self._replay_buffer_max_size <= 0:\n                raise ReplayOutOfRange("Replay buffer disabled")\n'),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(root: Path, rel: str, edits: list) -> None:
    text = (root / rel).read_text(encoding="utf-8")
    for old, new in edits:
        if text.count(old) != 1:
            raise SystemExit(f"{rel}: edit text occurs {text.count(old)} times, not once: {old[:70]!r}")
        text = text.replace(old, new)
    (root / rel).write_text(text, encoding="utf-8")


def run(name: str, cwd: Path, argv: list, logs: Path) -> dict:
    env = {**os.environ, **{key: "" for key in SENTRY_DSN_NAMES}, "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus"}
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    log = logs / f"{name}.log"
    with open(log, "w", encoding="utf-8") as handle:
        code = subprocess.run(argv, cwd=str(cwd), env=env, stdout=handle, stderr=subprocess.STDOUT, timeout=900, check=False).returncode
    text = log.read_text(encoding="utf-8", errors="replace")
    counts = {key: int(match.group(1)) for key in ("failed", "passed", "error") for match in [re.search(rf"(\d+) {key}\b", text)] if match}
    row = {"name": name, "exit": code, "counts": counts, "websockets_deprecations": text.count(WARNING), "log": str(log)}
    print(f"{name}\texit={code}\t{counts}\tdeprecations={row['websockets_deprecations']}", flush=True)
    return row


def guarded(root: Path, rels: list, body) -> list:
    """Run ``body`` with the files restored to their original bytes afterwards, whatever happens."""
    original = {rel: (root / rel).read_bytes() for rel in rels}
    before = {rel: sha(root / rel) for rel in rels}
    try:
        return body()
    finally:
        for rel, data in original.items():
            (root / rel).write_bytes(data)
        after = {rel: sha(root / rel) for rel in rels}
        print(f"restored={after == before} {sorted(rels)}", flush=True)
        if after != before:
            raise SystemExit("a file did not restore to its original sha256")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--step", choices=("floor", "ml", "cascor"), required=True)
    args = parser.parse_args()
    args.logs.mkdir(parents=True, exist_ok=True)
    ml_table = [PY312, "-m", "pytest", ML_TABLE, "-p", "no:cacheprovider", "-W", "default"]
    floor_table = [PY_FLOOR, "-m", "pytest", ML_TABLE, "-p", "no:cacheprovider", "-W", "default"]
    unit = [PY312, "-m", "pytest", *SVC_UNIT, "-p", "no:cacheprovider"]
    rows: list = []
    if args.step == "floor":
        rows.append(run("floor-carrier-as-is", ML, floor_table, args.logs))
    elif args.step == "ml":

        def f1_body() -> list:
            apply(ML, ML_TABLE, F1_EDITS)
            return [run("f1-fixed-ws17", ML, ml_table, args.logs), run("f1-fixed-floor-ws12", ML, floor_table, args.logs)]

        rows += guarded(ML, [ML_TABLE], f1_body)

        def f3_body() -> list:
            apply(ML, CONTINUITY, F3_EDITS)
            out = [run("f3-fixed-carrier-code", ML, unit, args.logs)]
            for rel, old, new in CLAMP_MUTANT:
                apply(ML, rel, [(old, new)])
            out.append(run("f3-fixed-vs-clamp-mutant", ML, unit, args.logs))
            return out

        rows += guarded(ML, [CONTINUITY, TS, MGR], f3_body)
    else:

        def cascor_body() -> list:
            apply(CASCOR, CASCOR_TABLE, F1_EDITS)
            return [run("f1-fixed-cascor-ws17", CASCOR, [PY_CASCOR, "-m", "pytest", "-m", "unit and not slow", CASCOR_TABLE, "--timeout=60", "-p", "no:cacheprovider", "-W", "default"], args.logs)]

        rows += guarded(CASCOR, [CASCOR_TABLE], cascor_body)
    existing = []
    if args.out.exists():
        with open(args.out, encoding="utf-8") as handle:
            existing = json.load(handle)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(existing + rows, handle, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
