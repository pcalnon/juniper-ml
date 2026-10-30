#!/usr/bin/env python3
"""
Split the image/PDF files a cleanup's blob classifier skipped into tracked and untracked, per target worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-29
Status: ad-hoc — one-off (flood-3 cleanup of 2026-10-29)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-26_worktree_blob_classify.py (its LFS_EXT skips these suffixes everywhere);
         notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§6: "a preservation tool's count is not the check")

Why this exists
---------------
``2026-10-26_worktree_blob_classify.py`` skips every image and PDF suffix, untracked files included, so
``2026-10-26_worktree_preserve_unique.py`` never copies them. Before a ``--force`` removal, list such files in
each target (a ``find`` over the LFS suffixes, pruning caches and venvs), then split them with this: a path
in the target's base tree listing (``git ls-tree -r <HEAD>``) is tracked and recoverable; any other must be
copied by hand.

    python3 -I util/ad-hoc/2026-10-29_cleanup_skipped_suffix_sweep.py <found-paths file> <worktree>=<base ls-tree listing> [...]

Run of record (2026-10-29, the four targets of ``tmp/worktree-cleanup-2026-10-29/``): 137 found, 132 tracked,
5 untracked (three juniper-ml#2381 evidence plots and two coverage-HTML icons), all copied by hand. Exit 0.
"""

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    found = [line.strip() for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
    untracked = []
    tracked = 0
    for pair in sys.argv[2:]:
        root, _, listing = pair.partition("=")
        paths = set()
        for line in Path(listing).read_text().splitlines():
            paths.add(line.split("\t", 1)[1])
        for path in found:
            if path.startswith(root.rstrip("/") + "/"):
                if path[len(root.rstrip("/")) + 1 :] in paths:
                    tracked += 1
                else:
                    untracked.append(path)
    print(f"tracked: {tracked}  untracked: {len(untracked)}  total: {len(found)}")
    for path in untracked:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
