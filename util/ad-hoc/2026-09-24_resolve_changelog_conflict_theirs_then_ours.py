"""
Resolve every ``git merge-file`` conflict block in a file as THEIRS (main, verbatim) followed by OURS.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc — repair helper
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: memory "open_signed_pr whole-file clobber" (the git merge-file repair); used on juniper-cascor's
         CHANGELOG.md for F1, whose entry and #685's F2 entry were inserted at the same line

The recorded convention for a CHANGELOG conflict under signed (whole-file) commits: main's entries stay
VERBATIM and in place, and yours go below them. ``git merge-file <yours> <base> <main>`` leaves conflict
blocks when both sides inserted at the same point, which is the normal case for two entries at the head of
one ``### Fixed`` section. This rewrites each block as main's lines, then yours, and refuses a file with no
conflict or an unterminated one. Verify afterwards with ``git diff origin/main -- <file>``: only your
lines should appear.

Usage:
    python util/ad-hoc/2026-09-24_resolve_changelog_conflict_theirs_then_ours.py <file-with-conflict-markers>
"""

import sys
from pathlib import Path


def main(argv):
    path = Path(argv[1])
    lines = path.read_text().splitlines(keepends=True)
    out, ours, theirs, state, blocks = [], [], [], None, 0
    for line in lines:
        if line.startswith("<<<<<<< "):
            state, ours, theirs = "ours", [], []
        elif line.startswith("=======") and state == "ours":
            state = "theirs"
        elif line.startswith(">>>>>>> ") and state == "theirs":
            out.extend(theirs + ours)
            state, blocks = None, blocks + 1
        elif state == "ours":
            ours.append(line)
        elif state == "theirs":
            theirs.append(line)
        else:
            out.append(line)
    if state is not None or blocks == 0:
        print(f"refusing: blocks={blocks}, unterminated={state is not None}")
        return 2
    path.write_text("".join(out))
    print(f"resolved {blocks} block(s): theirs first, then ours")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
