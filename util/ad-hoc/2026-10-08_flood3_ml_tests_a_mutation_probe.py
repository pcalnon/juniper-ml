#!/usr/bin/env python3
"""
Apply one-at-a-time source mutations, run a test command against each, and restore byte-exact.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-08
Status: ad-hoc — investigation (Cursor flood #3 evaluation, evaluator ml-tests-a)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood #3 evaluation brief (non-vacuity: "apply 1-3 targeted mutations to the
         production code under test, confirm the new tests fail, restore")

Usage:
    python3 util/ad-hoc/2026-10-08_flood3_mutation_probe.py SPEC.json

SPEC.json is a list of objects:
    {"id": "M1", "file": "util/ad-hoc/x.py", "old": "...", "new": "...",
     "count": 1, "test": ["python3", "-m", "unittest", "tests/test_x.py"]}

For each mutation: `old` must occur exactly `count` times (default 1) in `file`, else the
mutation is reported INVALID and nothing is changed. The file is rewritten with the replacement,
the test command runs with a FRESH, private bytecode cache (PYTHONPYCACHEPREFIX in a new temp dir
and PYTHONDONTWRITEBYTECODE=1 -- a stale .pyc of the unmutated source is the classic way a
mutation check reports a false SURVIVED), and the original bytes are restored in a `finally`.
The restore is verified by sha256; a mismatch aborts the whole run with exit 3.

Verdict per mutation: KILLED (test command exited non-zero), SURVIVED (exited 0), INVALID
(anchor not found the expected number of times), TIMEOUT (counted as KILLED but named).
Exit 0 always unless a restore failed (3) or the spec is unreadable (2).
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT_SECONDS = 600


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(spec_path: Path) -> int:
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read spec {spec_path}: {exc}", file=sys.stderr)
        return 2
    results = []
    for m in spec:
        path = Path(m["file"])
        original = path.read_bytes()
        text = original.decode("utf-8")
        want = int(m.get("count", 1))
        found = text.count(m["old"])
        if found != want:
            results.append((m["id"], "INVALID", f"anchor found {found}x, expected {want}x"))
            print(f"[{m['id']}] INVALID: anchor found {found}x, expected {want}x in {path}")
            continue
        mutated = text.replace(m["old"], m["new"])
        tail = ""
        try:
            path.write_bytes(mutated.encode("utf-8"))
            with tempfile.TemporaryDirectory(prefix="mutprobe-pyc-") as cache:
                env = dict(os.environ, PYTHONPYCACHEPREFIX=cache, PYTHONDONTWRITEBYTECODE="1")
                try:
                    proc = subprocess.run(m["test"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS, env=env, check=False)
                    verdict = "KILLED" if proc.returncode != 0 else "SURVIVED"
                    lines = (proc.stdout + proc.stderr).strip().splitlines()
                    tail = " | ".join(line for line in lines[-4:])
                except subprocess.TimeoutExpired:
                    verdict = "TIMEOUT"
        finally:
            path.write_bytes(original)
        if _sha(path.read_bytes()) != _sha(original):
            print(f"[{m['id']}] RESTORE FAILED for {path} -- aborting", file=sys.stderr)
            return 3
        results.append((m["id"], verdict, tail))
        print(f"[{m['id']}] {verdict}: {m.get('why', '')}\n      tail: {tail[:600]}")
    killed = sum(1 for _, v, _ in results if v in ("KILLED", "TIMEOUT"))
    valid = sum(1 for _, v, _ in results if v != "INVALID")
    print(f"SUMMARY {spec_path.name}: {killed}/{valid} killed ({len(results) - valid} invalid)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(run(Path(sys.argv[1])))
