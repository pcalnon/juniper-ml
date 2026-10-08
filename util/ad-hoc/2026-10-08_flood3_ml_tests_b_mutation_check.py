#!/usr/bin/env python3
"""Flood-3 evaluator helper: apply ONE exact-string mutation at a time, run a test, restore.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use evaluation helper)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-10-08
Status:      ad-hoc. Written by the flood-3 evaluator ``ml-tests-b`` to prove the new suites are not
             vacuous: each mutation is a one-token edit to the production code a suite claims to pin.

Spec: a JSON list of ``{"id", "file", "old", "new", "test", "count"?, "timeout"?}``. ``old`` must occur
exactly ``count`` times (default 1) or the mutation is reported ANCHOR-MISMATCH and NOT applied. The
original bytes are restored in a ``finally`` and re-hashed; a restore that does not match is reported
RESTORE-FAILED and the run exits 3. Every run uses a fresh ``PYTHONPYCACHEPREFIX`` so a stale ``.pyc``
of the unmutated source cannot answer for the mutated one.

Verdicts: KILLED (the test failed or errored under the mutation), SURVIVED (it still passed).

    python3 util/ad-hoc/2026-10-08_flood3_ml_tests_b_mutation_check.py --spec <spec.json> [--only ID ...] [--out results.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _summary(output: str) -> str:
    ran = re.findall(r"^Ran (\d+) tests?", output, flags=re.MULTILINE)
    tail = re.findall(r"^(OK.*|FAILED \(.*\))$", output, flags=re.MULTILINE)
    return f"ran={ran[-1] if ran else '?'} {tail[-1] if tail else 'no-verdict-line'}"


def run_one(mutation: dict) -> dict:
    path = ROOT / mutation["file"]
    original = path.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    expected = int(mutation.get("count", 1))
    count = text.count(mutation["old"])
    result = {"id": mutation["id"], "file": mutation["file"], "test": mutation["test"]}
    if count != expected:
        result.update(status="ANCHOR-MISMATCH", found=count, expected=expected)
        return result
    try:
        path.write_text(text.replace(mutation["old"], mutation["new"]), encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="mutcache-") as cache:
            os.environ["PYTHONPYCACHEPREFIX"] = cache
            proc = subprocess.run([sys.executable, "-m", "unittest", mutation["test"]], cwd=ROOT, capture_output=True, text=True, timeout=int(mutation.get("timeout", 600)), check=False)
    finally:
        path.write_bytes(original)
        os.environ.pop("PYTHONPYCACHEPREFIX", None)
    restored = hashlib.sha256(path.read_bytes()).hexdigest() == digest
    combined = proc.stdout + proc.stderr
    result.update(status="KILLED" if proc.returncode != 0 else "SURVIVED", returncode=proc.returncode, summary=_summary(combined), restored=restored)
    if proc.returncode != 0:
        failing = re.findall(r"^(?:FAIL|ERROR): (\S+)", combined, flags=re.MULTILINE)
        result["failing"] = failing[:12]
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    results = []
    for mutation in spec:
        if args.only and mutation["id"] not in args.only:
            continue
        outcome = run_one(mutation)
        results.append(outcome)
        print(f"{outcome['id']:<14} {outcome['status']:<16} {outcome.get('summary', '')}  restored={outcome.get('restored', 'n/a')}", flush=True)
        for name in outcome.get("failing", []):
            print(f"{'':<16}- {name}", flush=True)
        if outcome.get("restored") is False:
            print("RESTORE-FAILED: stop and inspect the file by hand", flush=True)
            return 3
    if args.out is not None:
        args.out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
