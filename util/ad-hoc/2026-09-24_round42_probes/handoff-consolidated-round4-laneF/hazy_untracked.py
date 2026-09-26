#!/usr/bin/env python3
"""Round 4 lane F probe: every file in hazy-beaming-map that is NOT in its index, and whether
origin/main holds the same bytes at the same path. Read-only: open() on hazy, index parsed
from the binary file, git plumbing only in fizzy."""
import hashlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hazy import parse_index, INDEX, HAZY, FIZZY  # noqa: E402  (re-uses the parser; prints its own report first)

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".venv", "venv"}


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


_v, idx = parse_index(INDEX)
p = subprocess.run(["git", "--no-optional-locks", "ls-tree", "-r", "origin/main"], cwd=FIZZY, capture_output=True)
main = {}
for line in p.stdout.decode().splitlines():
    meta, path = line.split("\t", 1)
    main[path] = meta.split()[2]
print("\n\n==== untracked files in hazy ====")
same, differ, absent = [], [], []
for root, dirs, files in os.walk(HAZY):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        full = os.path.join(root, f)
        rel = os.path.relpath(full, HAZY)
        if rel in idx or rel == ".git":
            continue
        if os.path.islink(full):
            continue
        with open(full, "rb") as fh:
            b = blob_sha(fh.read())
        if rel in main:
            (same if main[rel] == b else differ).append(rel)
        else:
            absent.append(rel)
print("untracked total:", len(same) + len(differ) + len(absent))
print("identical to origin/main:", len(same))
print("differ from origin/main:", len(differ))
for r in differ:
    print("  D", r)
print("absent from origin/main:", len(absent))
for r in sorted(absent)[:60]:
    print("  A", r)
