"""
Build a scratch copy of juniper-service-core with some of juniper-cascor#754's resume rules applied, to MEASURE a design.

This is a measuring instrument for the design check, not a change to any repository: it copies an extracted
``juniper_service_core`` package and its ``tests`` into a scratch directory and applies up to four textual edits there,
so the wire probe and the package's own tests can say what each rule would change and what it would cost.

  data      a resume frame whose ``data`` is not an object carries no cursor (answered ``malformed_resume``)
  integer   a ``last_seq`` that is not a plain integer is answered ``malformed_resume`` (checked before the instance id)
  negative  a negative ``last_seq`` is read as 0 in the handshake
  upper     ``WebSocketManager.replay_since`` refuses a cursor above the last seq numbered

Every edit replaces text that must occur exactly once in the source file; the script stops if it does not. It writes
the sha256 of every file it changed to ``prototype.json`` in the destination.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor#754; the design check of whether juniper-service-core follows cascor's two new resume answers
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

STREAM = "juniper_service_core/websocket/training_stream.py"
MANAGER = "juniper_service_core/websocket/manager.py"

EDITS = {
    "data": (
        STREAM,
        '    data = msg.get("data", {})\n',
        '    data = msg.get("data")\n    if not isinstance(data, dict):\n        data = {}\n',
    ),
    "integer": (
        STREAM,
        "    if last_seq is None or client_server_id is None:\n",
        "    if client_server_id is None or not isinstance(last_seq, int) or isinstance(last_seq, bool):\n",
    ),
    "negative": (
        STREAM,
        "        events = ws_manager.replay_since(last_seq)\n",
        "        events = ws_manager.replay_since(max(last_seq, 0))\n",
    ),
    "upper": (
        MANAGER,
        '                raise ReplayOutOfRange(f"Requested seq {last_seq} older than oldest buffered seq {oldest_seq}")\n',
        '                raise ReplayOutOfRange(f"Requested seq {last_seq} older than oldest buffered seq {oldest_seq}")\n'
        "            newest_seq = self._next_seq - 1\n"
        "            if last_seq > newest_seq:\n"
        '                raise ReplayOutOfRange(f"Requested seq {last_seq} is above the last seq numbered, {newest_seq}")\n',
    ),
}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--src", type=Path, required=True, help="directory holding juniper_service_core and tests")
    parser.add_argument("--dest", type=Path, required=True, help="scratch directory to create; must not exist")
    parser.add_argument("--rules", required=True, help="comma-separated subset of: " + ", ".join(EDITS))
    args = parser.parse_args()

    rules = [rule for rule in args.rules.split(",") if rule]
    unknown = [rule for rule in rules if rule not in EDITS]
    if unknown:
        raise SystemExit(f"unknown rule(s): {unknown}")
    if args.dest.exists():
        raise SystemExit(f"{args.dest} exists; choose a new directory")

    args.dest.mkdir(parents=True)
    for name in ("juniper_service_core", "tests"):
        shutil.copytree(args.src / name, args.dest / name, ignore=shutil.ignore_patterns("__pycache__"))

    record = {"src": str(args.src), "rules": rules, "files": {}}
    for rule in rules:
        relative, old, new = EDITS[rule]
        path = args.dest / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"rule {rule}: the text to replace occurs {text.count(old)} times in {relative}, not once")
        path.write_text(text.replace(old, new), encoding="utf-8")
    for relative in sorted({EDITS[rule][0] for rule in rules}):
        record["files"][relative] = {"before": sha256_of(args.src / relative), "after": sha256_of(args.dest / relative)}

    with open(args.dest / "prototype.json", "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=1)
        handle.write("\n")
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()
