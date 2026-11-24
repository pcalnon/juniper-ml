"""
Count each resolved file's added and removed lines against main's copy and against the original diff, for the first re-land (rehome2/).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2621

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: per-file +/- line counts of rehome2/final/ against origin/main's version (theirs), and against my old diff.
"""

import difflib
from pathlib import Path

HERE = Path(__file__).with_name("rehome2")
for path in sorted((HERE / "final").rglob("*")):
    if not path.is_file():
        continue
    rel = path.relative_to(HERE / "final").as_posix()
    stem = rel.replace("/", "__")
    theirs = (HERE / f"{stem}.theirs").read_text(encoding="utf-8").splitlines()
    final = path.read_text(encoding="utf-8").splitlines()
    mine = (HERE / f"{stem}.mine").read_text(encoding="utf-8").splitlines()
    base = (HERE / f"{stem}.base").read_text(encoding="utf-8").splitlines()

    def count(a, b):
        plus = minus = 0
        for line in difflib.unified_diff(a, b, lineterm="", n=0):
            if line.startswith("+") and not line.startswith("+++"):
                plus += 1
            elif line.startswith("-") and not line.startswith("---"):
                minus += 1
        return plus, minus

    print(f"{rel:45s} vs main +{count(theirs, final)[0]}/-{count(theirs, final)[1]}   (my old change vs base: +{count(base, mine)[0]}/-{count(base, mine)[1]})")
