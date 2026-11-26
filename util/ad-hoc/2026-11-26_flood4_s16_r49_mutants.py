"""
Apply one named mutant to a juniper-canopy tree, run a test command against it, and restore the file byte for byte.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26) (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
    section 8); flood-4 session 16 builder r49 (the non-vacuity check of the reworked X7 health test)

Usage:
    python3 -I <this file> --tree <canopy tree> --mutant M1|M2|M3 --record <json file> -- <command ...>
The mutant is an exact substitution that must match exactly once (else nothing is changed and the script exits 2).
sha256 of the file is recorded before, after mutation and after restore; the restore runs in a finally: block, and a
mismatch after restore exits 3. The command (normally the fenced run-lane helper) runs with cwd = the tree.

    M1  src/main.py GET /api/status: `return await offload(backend.get_status)` -> `return backend.get_status()`
        (the call back on the event loop: the pre-fix shape, the regression T-A2 pins)
    M2  src/backend/admission.py offload(): `await asyncio.to_thread(_issue, ...)` -> `_issue(...)` (every offloaded
        site runs inline on the loop again)
    M3  src/main.py GET /api/status: the call made on a worker thread while the loop waits synchronously for its result
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - runs the given test command
import sys
import time
from pathlib import Path

MUTANTS = {
    "M1": ("src/main.py", "    if status_cache is not None:\n        return status_cache.for_status()\n    return await offload(backend.get_status)\n", "    if status_cache is not None:\n        return status_cache.for_status()\n    return backend.get_status()\n"),
    "M2": ("src/backend/admission.py", "            return await asyncio.to_thread(_issue, fn, _deadline.get(), *args, **kwargs)\n", "            return _issue(fn, _deadline.get(), *args, **kwargs)\n"),
    "M3": (
        "src/main.py",
        "    if status_cache is not None:\n        return status_cache.for_status()\n    return await offload(backend.get_status)\n",
        '    if status_cache is not None:\n        return status_cache.for_status()\n    return __import__("concurrent.futures", fromlist=["ThreadPoolExecutor"]).ThreadPoolExecutor(max_workers=1).submit(backend.get_status).result()\n',
    ),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", required=True)
    parser.add_argument("--mutant", required=True, choices=sorted(MUTANTS))
    parser.add_argument("--record", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    tree = Path(args.tree).resolve()
    relpath, old, new = MUTANTS[args.mutant]
    target = tree / relpath
    original = target.read_bytes()
    text = original.decode("utf-8")
    record = {"mutant": args.mutant, "file": relpath, "tree": str(tree), "sha256_before": sha(original), "command": command}
    if text.count(old) != 1:
        record["error"] = f"pattern matched {text.count(old)} times, expected 1; nothing changed"
        Path(args.record).write_text(json.dumps(record, indent=1), encoding="utf-8")
        print(json.dumps(record))
        return 2
    started = time.time()
    try:
        target.write_bytes(text.replace(old, new, 1).encode("utf-8"))
        record["sha256_mutated"] = sha(target.read_bytes())
        proc = subprocess.run(command, cwd=tree, check=False)  # nosec B603 - caller-supplied test command
        record["command_exit"] = proc.returncode
    finally:
        target.write_bytes(original)
        record["sha256_after"] = sha(target.read_bytes())
        record["restored_identical"] = record["sha256_after"] == record["sha256_before"]
        record["seconds"] = round(time.time() - started, 1)
        Path(args.record).write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(json.dumps({k: record[k] for k in ("mutant", "file", "sha256_before", "sha256_mutated", "sha256_after", "restored_identical", "command_exit", "seconds")}))
    return 0 if record["restored_identical"] else 3


if __name__ == "__main__":
    sys.exit(main())
