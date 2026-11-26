"""
Apply one r28 mutant to a juniper-canopy tree, run the given commands against it (concurrently), restore byte for
byte in a finally, and record sha256 before, mutated and after.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 builder r28

Usage:
    python <this file> --tree <canopy tree> --mutant <id> --out <record .json> -- <command> [--and <command> ...]

Each command is run with subprocess (no shell), all at once, while the mutant is applied; the script waits for all.
Mutants (each replaces text that must occur exactly once):
    M1  relay:   extract_network_topology called inline on the loop (the regression the relay test pins)
    M2  connect: is_alive called inline
    M3  attach:  attach_to_existing called inline
    M4  sync:    CascorStateSync.sync called inline
    M5  relay:   offloaded to a thread, but the loop thread blocks on the result ("offload theatre")
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - runs the r28 lane runner
import sys
import time
from pathlib import Path

ADAPTER = "src/backend/cascor_service_adapter.py"
BACKEND = "src/backend/service_backend.py"
MUTANTS = {
    "M1": (ADAPTER, "topology = await asyncio.to_thread(self.extract_network_topology)", "topology = self.extract_network_topology()"),
    "M2": (ADAPTER, "return bool(await asyncio.to_thread(self._client.is_alive))", "return bool(self._client.is_alive())"),
    "M3": (BACKEND, "has_network = await asyncio.to_thread(self._adapter.attach_to_existing)", "has_network = self._adapter.attach_to_existing()"),
    "M4": (BACKEND, "self._synced_state = await asyncio.to_thread(CascorStateSync(self._adapter.client).sync)", "self._synced_state = CascorStateSync(self._adapter.client).sync()"),
    "M5": (ADAPTER, "topology = await asyncio.to_thread(self.extract_network_topology)", "topology = __import__('concurrent.futures').futures.ThreadPoolExecutor(1).submit(self.extract_network_topology).result()"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", required=True)
    parser.add_argument("--mutant", required=True, choices=sorted(MUTANTS))
    parser.add_argument("--out", required=True)
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    rest = args.rest[1:] if args.rest and args.rest[0] == "--" else args.rest
    commands, current = [], []
    for token in rest:
        if token == "--and":
            commands.append(current)
            current = []
        else:
            current.append(token)
    if current:
        commands.append(current)
    rel, old, new = MUTANTS[args.mutant]
    target = Path(args.tree) / rel
    original = target.read_bytes()
    record = {"mutant": args.mutant, "file": rel, "old": old, "new": new, "sha256_before": sha(target), "commands": commands}
    text = original.decode("utf-8")
    if text.count(old) != 1:
        record["error"] = f"expected exactly one occurrence, found {text.count(old)}"
        Path(args.out).write_text(json.dumps(record, indent=1), encoding="utf-8")
        print(json.dumps(record))
        return 2
    try:
        target.write_bytes(text.replace(old, new).encode("utf-8"))
        record["sha256_mutated"] = sha(target)
        start = time.time()
        procs = [subprocess.Popen(cmd) for cmd in commands]  # nosec B603
        record["exit_codes"] = [p.wait() for p in procs]
        record["seconds"] = round(time.time() - start, 1)
    finally:
        target.write_bytes(original)
        record["sha256_after"] = sha(target)
        record["restored_byte_for_byte"] = record["sha256_after"] == record["sha256_before"]
        Path(args.out).write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(json.dumps({k: record.get(k) for k in ("mutant", "exit_codes", "seconds", "restored_byte_for_byte")}))
    return 0 if record["restored_byte_for_byte"] else 1


if __name__ == "__main__":
    sys.exit(main())
