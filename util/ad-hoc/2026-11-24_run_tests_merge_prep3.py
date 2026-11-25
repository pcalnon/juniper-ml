"""
The same three-way merge for the second re-land, base ca9762404a, into rehome3/.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2629

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Its original docstring was copied from the first re-land's script and still names f74642b3 and rehome2/; the code uses ca9762404a and rehome3/.

Original docstring, verbatim:

Scratch: three-way merge each of my edited tracked files (mine, base f74642b3, theirs origin/main) into rehome2/.

Writes rehome2/<path with / as __>.merged (with diff3 conflict markers where both sides changed the same lines) and
prints the conflict count per file. Touches nothing in the worktree.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("rehome3")
BASE = "ca9762404a"
THEIRS = "origin/main"
FILES = [".github/workflows/ci.yml", "AGENTS.md", "CHANGELOG.md", "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md", "docs/REFERENCE.md", "tests/test_release_train_registry.py"]

OUT.mkdir(exist_ok=True)
total = 0
for rel in FILES:
    stem = rel.replace("/", "__")
    mine, base, theirs = OUT / f"{stem}.mine", OUT / f"{stem}.base", OUT / f"{stem}.theirs"
    mine.write_bytes((ROOT / rel).read_bytes())
    base.write_bytes(subprocess.run(["git", "show", f"{BASE}:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout)
    theirs.write_bytes(subprocess.run(["git", "show", f"{THEIRS}:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout)
    proc = subprocess.run(["git", "merge-file", "-p", "--diff3", "-L", "mine", "-L", "base", "-L", "main", str(mine), str(base), str(theirs)], capture_output=True, check=False)
    (OUT / f"{stem}.merged").write_bytes(proc.stdout)
    conflicts = proc.returncode if proc.returncode > 0 else 0
    total += conflicts
    print(f"{conflicts:>3} conflict(s)  {rel}")
print(f"total {total}")
sys.exit(0)
