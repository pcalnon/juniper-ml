"""
Survey how main phrases the person after #2606's "owner" -> "Overtoad" rename, and where this arc's new text still said "owner".

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2629 (the second re-land), after juniper-ml#2606

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: how does origin/main phrase the person after the "owner" -> "Overtoad" rename, and where does MY new text
still say "owner"? Prints main's phrasing around the expressions I use, then every "owner" in my changed lines.
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def show(ref: str, rel: str) -> str:
    return subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout


main_text = show("origin/main", "AGENTS.md") + show("origin/main", "docs/REFERENCE.md") + show("origin/main", "CHANGELOG.md")
for pattern in ("directive, 2026-10-26", "policy 2026-08-25", "rulings, 2026-10-26", "ruling of 2026-11-14", "Overtoad's", "Overtoad directive", "The Overtoad"):
    hits = [m.group(0) for m in re.finditer(r".{0,45}" + re.escape(pattern) + r".{0,20}", main_text)][:2]
    print(f"{pattern!r:28} {hits}")

print("\n=== 'owner' in my new or changed lines (worktree vs ca976240, plus the two new files) ===")
diff = subprocess.run(["git", "diff", "-U0", "ca9762404a", "--", "AGENTS.md", "CHANGELOG.md", "docs/REFERENCE.md", "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md", "tests/test_release_train_registry.py", ".github/workflows/ci.yml"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
current = None
for line in diff.splitlines():
    if line.startswith("+++ "):
        current = line[6:]
    elif line.startswith("+") and re.search(r"[Oo]wner", line):
        for m in re.finditer(r".{0,50}[Oo]wner.{0,30}", line):
            print(f"{current}: {m.group(0)}")
for rel in ("util/run_tests.py", "tests/test_run_tests.py"):
    for number, line in enumerate((ROOT / rel).read_text().splitlines(), 1):
        for m in re.finditer(r".{0,50}[Oo]wner.{0,30}", line):
            print(f"{rel}:{number}: {m.group(0)}")
