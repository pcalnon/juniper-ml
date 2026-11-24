"""
Move the worktree from ca9762404a onto origin/main (b346a90a) and write the second re-land's resolved files from rehome3/final/.

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

Its original docstring was copied from the first re-land's script and still names f74642b3 and rehome2/; the code checks ca9762404a and reads rehome3/.

Original docstring, verbatim:

Scratch: move the worktree from f74642b3 to origin/main and write the resolved files (rehome2/final/).

Refuses before writing anything unless: HEAD is f74642b3, f74642b3 is an ancestor of origin/main, nothing is
staged, and the modified tracked files are exactly the six resolved ones. The untracked new files are not touched
(main added neither path). Every file's pre-move content is already in rehome2/*.mine and upload-snapshot/.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FINAL = Path(__file__).with_name("rehome3") / "final"
ALL = sorted(p.relative_to(FINAL).as_posix() for p in FINAL.rglob("*") if p.is_file())
FILES = [rel for rel in ALL if rel != "util/run_tests.py"]


def git(*args: str, check: bool = True) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=check).stdout.strip()


head = git("rev-parse", "HEAD")
main = git("rev-parse", "origin/main")
if not head.startswith("ca9762404a"):
    sys.exit(f"refused: HEAD is {head[:10]}, not ca9762404a")
if subprocess.run(["git", "merge-base", "--is-ancestor", head, main], cwd=ROOT).returncode != 0:
    sys.exit("refused: HEAD is not an ancestor of origin/main")
if git("diff", "--cached", "--name-only"):
    sys.exit("refused: something is staged")
modified = sorted(git("diff", "--name-only").splitlines())
if modified != FILES:
    sys.exit(f"refused: modified tracked files {modified} != resolved set {FILES}")

git("checkout", "--", *FILES)
git("merge", "--ff-only", "origin/main")
for rel in ALL:
    shutil.copyfile(FINAL / rel, ROOT / rel)
print(f"HEAD {head[:10]} -> {git('rev-parse', 'HEAD')[:10]} (origin/main {main[:10]}); wrote {len(FILES)} resolved files")
print(git("status", "--short"))
