"""
Compare each uploaded file's sha256 on main's squash commit with the frozen upload snapshot.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2629 (on d7709ef7, every uploaded file was byte-for-byte the snapshot)

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: compare each uploaded file's sha256 on origin/main's merge commit with the frozen upload snapshot.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMIT = sys.argv[1]
record = dict(line.split("  ", 1)[::-1] for line in Path(__file__).with_name("upload-snapshot.sha256").read_text().splitlines())
bad = 0
for rel, digest in sorted(record.items()):
    blob = subprocess.run(["git", "show", f"{COMMIT}:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout
    same = hashlib.sha256(blob).hexdigest() == digest
    bad += not same
    print(f"{'same' if same else 'DIFFERS'}  {rel}")
print("every uploaded file is on main byte-for-byte" if not bad else f"{bad} file(s) differ")
sys.exit(1 if bad else 0)
