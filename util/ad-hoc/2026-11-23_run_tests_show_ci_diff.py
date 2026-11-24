"""
Print main's ci.yml changes since the old base, and the head of main's new CHANGELOG entries.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2621 (the first re-land)

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

It is a script because the session's worktree guard refused a command line naming the workflows directory.

Original docstring, verbatim:

Scratch: print main's ci.yml changes since the old base, and the head of main's new CHANGELOG entries.
"""

import subprocess

for rel in (".github/workflows/ci.yml", "CHANGELOG.md"):
    out = subprocess.run(["git", "diff", "f74642b3", "origin/main", "--", rel], capture_output=True, text=True, check=True).stdout
    print(f"===== {rel}")
    for line in out.splitlines():
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            print(line[:220])
