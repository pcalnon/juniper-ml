"""
Freeze the upload set into upload-snapshot/ with each file's sha256, so every signed push is made from, and verified against, one frozen copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2615, #2621 and #2629

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: freeze the upload set into a snapshot directory and record each file's sha256 (verify the PR against it).
"""

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAP = Path(__file__).with_name("upload-snapshot")
FILES = [
    "util/run_tests.py",
    "tests/test_run_tests.py",
    "tests/test_release_train_registry.py",
    "AGENTS.md",
    ".github/workflows/ci.yml",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
    "CHANGELOG.md",
    "docs/REFERENCE.md",
]

if sys.argv[1:] == ["--verify"]:
    record = dict(line.split("  ", 1)[::-1] for line in Path(__file__).with_name("upload-snapshot.sha256").read_text().splitlines())
    bad = [rel for rel in FILES if hashlib.sha256((SNAP / rel).read_bytes()).hexdigest() != record[rel]]
    print("snapshot intact" if not bad else f"CHANGED: {bad}")
    sys.exit(1 if bad else 0)

if SNAP.exists():
    shutil.rmtree(SNAP)
lines = []
for rel in FILES:
    target = SNAP / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / rel, target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    lines.append(f"{digest}  {rel}")
    print(f"{digest[:16]}  {target.stat().st_size:>8}  {rel}")
Path(__file__).with_name("upload-snapshot.sha256").write_text("\n".join(lines) + "\n")
