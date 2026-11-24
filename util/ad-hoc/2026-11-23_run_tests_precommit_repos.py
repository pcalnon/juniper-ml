"""
Map pre-commit's cache directories to their repo and rev, to find the pinned black.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2615

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: map pre-commit cache directories to their repo + rev (to find the pinned black).
"""
import sqlite3
from pathlib import Path

db = Path.home() / ".cache" / "pre-commit" / "db.db"
with sqlite3.connect(db) as conn:
    for repo, ref, path in conn.execute("SELECT repo, ref, path FROM repos"):
        if "black" in repo or "isort" in repo or "flake8" in repo:
            print(repo, ref, path)
