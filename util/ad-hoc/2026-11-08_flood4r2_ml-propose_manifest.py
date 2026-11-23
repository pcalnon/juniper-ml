#!/usr/bin/env python3
"""Assemble the flood-4 round-2 "ml-propose" carrier's manifest.json from the build's own records.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (the Cursor flood-4 round-2 "ml-propose" carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507; Overtoad ruling "Carry + extend propose.py";
         util/ad-hoc/2026-11-07_flood4_ml_tests_manifest.py (round 1's generator, which this adapts)

Inputs, all under ``<scratch>`` (the carrier's scratch directory): ``name_status.txt`` (``git status --porcelain``
of the worktree), ``mut/mutation_results.json`` (2026-11-08_flood4r2_ml-propose_mutation_check.py),
``logs/prove_summary.json`` (2026-11-08_flood4r2_ml-propose_prove_reference_cochanges.py) and ``checks.json``
(the checks run, written by hand from their logs, each naming its command, result and log). Each mutant's line
number is read from the worktree's ``util/release_train/propose.py``, where its ``old`` text starts.

Usage: python3 util/ad-hoc/2026-11-08_flood4r2_ml-propose_manifest.py <scratch-dir> <worktree> <base-sha>

Revised 2026-11-09 after round-2 validation: each file row carries the worktree file's sha256, and the manifest
points at ``<scratch>/dispositions.json``, the record of what was done with each validator finding.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

STATUS = {"M": "modified", "A": "added", "D": "deleted", "?": "added"}


def _load(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    scratch, worktree, base = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    propose_text = (worktree / "util" / "release_train" / "propose.py").read_text(encoding="utf-8")
    files = []
    for line in (scratch / "name_status.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        code, path = line[:2].strip(), line[3:]
        target = worktree / path
        sha = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        files.append({"path": path, "status": STATUS.get(code[:1], code), "sha256": sha})
    mutation_record = _load(scratch / "mut" / "mutation_results.json")
    mutations = []
    for m in mutation_record["mutants"]:
        start = propose_text.find(m["old"])
        line_no = propose_text.count("\n", 0, start) + 1 if start >= 0 else None
        first_old = m["old"].strip().splitlines()[0]
        first_new = m["new"].strip().splitlines()[0]
        mutations.append(
            {
                "test_file": "tests/test_release_train_propose.py",
                "mutant": f"util/release_train/propose.py:{line_no} ({m['id']}, {m['helper']}): `{first_old}` -> `{first_new}`",
                "result": m["result"],
                "log": m["log"],
            }
        )
    prove = _load(scratch / "logs" / "prove_summary.json")
    manifest = {
        "repo": "juniper-ml",
        "carrier": "ml-propose",
        "base_sha": base,
        "worktree": str(worktree),
        "files": files,
        "carried": [
            {
                "pr": 2507,
                "head_sha": prove["gate_sha"],
                "title": "test(reference): pin the compatibility matrix and recurrence sentence to pyproject",
                "taken": [],
                "fixes": [],
                "dropped": [
                    "tests/test_pyproject_extras.py (ReferenceCompatibilityMatrixTest, the draft's only file): it rides the separate juniper-ml tests carrier, per the ruling. Its head blob "
                    + prove["gate_blob"]
                    + " was only RUN here, as the check that a proposal stays green"
                ],
                "outcome": "not-carried",
                "reason": "The Overtoad ruling 'Carry + extend propose.py': this carrier is the propose.py extension that keeps proposals green under #2507's tests; it carries none of the draft's content.",
            }
        ],
        "checks": _load(scratch / "checks.json"),
        "mutations": mutations,
        "open_questions": _load(scratch / "open_questions.json"),
        "dispositions": str(scratch / "dispositions.json"),
    }
    with open(scratch / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    print(f"wrote {scratch / 'manifest.json'}: {len(files)} files, {len(mutations)} mutants, {len(manifest['checks'])} checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
