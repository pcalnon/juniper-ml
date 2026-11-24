"""
Append one UTC-stamped line to the r32 pause carriers' PROGRESS.txt files.

Usage: python3 2026-11-15_flood4r2_r32-cascor_progress.py "<message>" [--doc-too]

The fix carrier's PROGRESS.txt (worktree B) is canonical. With --doc-too the same
line is also appended to the document carrier's PROGRESS.txt (worktree A), so the
doc carrier's directory carries its own milestones. The stamp is read from the clock
at the moment of writing, never typed by hand.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (flood-4 round 2, the r32 pause check-then-act carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor#756 ("What this does not close", seventh item); the Overtoad's ruling of 2026-11-13
"""

import datetime
import sys
from pathlib import Path

WORKTREES = Path.home() / "Development" / "python" / "Juniper" / "worktrees"
FIX_PROGRESS = WORKTREES / "juniper-cascor--fix--pause-check-then-act--20261115-0532--a1b0409d" / "tmp" / "flood4-fix" / "r32-pause-fix" / "PROGRESS.txt"
DOC_PROGRESS = WORKTREES / "juniper-cascor--docs--pause-stop-start-overlap--20261115-0532--a1b0409d" / "tmp" / "flood4-fix" / "r32-pause-doc" / "PROGRESS.txt"


def main(argv):
    args = [a for a in argv if a != "--doc-too"]
    if len(args) != 1 or not args[0].strip():
        print("usage: progress.py '<message>' [--doc-too]", file=sys.stderr)
        return 2
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{stamp} {args[0].strip()}\n"
    targets = [FIX_PROGRESS]
    if "--doc-too" in argv:
        targets.append(DOC_PROGRESS)
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(line)
    sys.stdout.write(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
