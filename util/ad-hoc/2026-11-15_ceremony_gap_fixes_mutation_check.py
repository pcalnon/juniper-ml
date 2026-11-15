#!/usr/bin/env python3
"""Prove the release-train gap tests bind the code: each mutation of ceremony.py must fail the ceremony suite.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (the two release-train gaps the one-artifact publishers opened: HALT_BUILD, and a republish
        dispatch the monitor never saw)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/release_train/ceremony.py (classify_publish_run, publish_run_status); tests/test_release_train_ceremony.py
         (OneArtifactPublisherClassifyTest, PublishRunStatusDispatchTest)

Why
---
A green suite says the tests agree with the code, not that they would notice the fix going away. Each mutation below
removes one part of the fix, exactly once (refused otherwise), and the suite must then FAIL; the file is restored from
memory in a ``finally`` and its sha256 re-checked, so a killed run is the only way to leave a mutant (re-run this to see
"restored" or compare the sha256 it prints first).

    python3 -I util/ad-hoc/2026-11-15_ceremony_gap_fixes_mutation_check.py

Exit status: 0 when every mutation failed the suite and the file was restored byte-identical; 1 otherwise.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "util" / "release_train" / "ceremony.py"
SUITE = "tests/test_release_train_ceremony.py"
MUTATIONS = {
    "no HALT_BUILD check": ('    if any((j.get("conclusion") or "").lower() == "failure" for j in build_jobs):\n        return "HALT_BUILD"\n', ""),
    "HALT_BUILD not terminal in the monitor": ('("PENDING_PYPI_APPROVAL", "HALT_BUILD", "HALT_TESTPYPI"', '("PENDING_PYPI_APPROVAL", "HALT_TESTPYPI"'),
    "no dispatch listing": ("        if workflow_id:\n            out_d", "        if False:\n            out_d"),
    "no workflow-id filter on dispatch runs": (' and r.get("workflowDatabaseId") == workflow_id]', "]"),
    "build-failed files no issue": ('                "HALT_BUILD": ("build-failed",', '                "HALT_BUILD_X": ("build-failed",'),
    # The ml#2592 reviews: the image publisher's run on the same Release, a re-run's old id, the 20-run window, and the
    # merge rule between the release run and its dispatches.
    "image runs not dropped": ("    runs = [r for r in runs if is_pypi_publisher_run(r)]\n", ""),
    "ordered by id alone": ('key=lambda r: (r.get("startedAt") or "", r.get("databaseId") or 0))', 'key=lambda r: r.get("databaseId") or 0)'),
    "release listing not per tag": ('"--event", "release", "--branch", tag, ', '"--event", "release", '),
    "the newest dispatch always wins": ("            match = select_publish_run([match, *dispatched], tag) or match\n", '            match = max([match, *dispatched], key=lambda r: r.get("databaseId") or 0)\n'),
    "a skipped dispatch is not dropped": ("            match = select_publish_run([match, *dispatched], tag) or match\n", "            match = (dispatched or [match])[-1]\n"),
    # The round-2 review: gh does not list the PyPI run first, and the tie-breaks among unfinished or equal-start runs.
    "dispatch lookup keyed on the first listed run": ('        workflow_id = match.get("workflowDatabaseId")\n', '        workflow_id = runs[0].get("workflowDatabaseId") if runs else None\n'),
    "equal start times prefer the oldest id": ('key=lambda r: (r.get("startedAt") or "", r.get("databaseId") or 0))', 'key=lambda r: (r.get("startedAt") or "", -(r.get("databaseId") or 0)))'),
    "unfinished runs ordered by id alone": ("    return max(unfinished or live, key=", "    return max(unfinished, key=lambda r: r.get(\"databaseId\") or 0) if unfinished else max(live, key="),
}


def main() -> int:
    original = TARGET.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    print(f"ceremony.py sha256 before: {digest}")
    bad = 0
    try:
        for label, (old, new) in MUTATIONS.items():
            text = original.decode("utf-8")
            if text.count(old) != 1:
                print(f"REFUSED {label}: anchor matched {text.count(old)} times")
                bad += 1
                continue
            TARGET.write_text(text.replace(old, new), encoding="utf-8")
            proc = subprocess.run([sys.executable, "-m", "unittest", SUITE], cwd=ROOT, capture_output=True, text=True, check=False)
            tail = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else ""
            killed = proc.returncode != 0
            bad += not killed
            print(f"{'KILLED ' if killed else 'SURVIVED'} {label}: {tail}")
    finally:
        TARGET.write_bytes(original)
    after = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    print(f"ceremony.py sha256 after:  {after} ({'restored' if after == digest else 'NOT RESTORED'})")
    return 1 if bad or after != digest else 0


if __name__ == "__main__":
    sys.exit(main())
