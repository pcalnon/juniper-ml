#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-26_worktree_preserve_unique.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Copies every file that 2026-10-26_worktree_blob_classify.py marks */UNIQUE
#   (content that never existed in main's history) out of a cleanup target before
#   it is removed with --force, and appends each to <dest-root>/MANIFEST.tsv.
#   Used for the 2026-10-26 flood-3 cleanup; those copies live under juniper-ml's
#   gitignored tmp/worktree-cleanup-2026-10-26/.
#
# Usage:
#   python3 -I util/ad-hoc/2026-10-26_worktree_preserve_unique.py \
#       <dest-root> <classifier output file> <worktree>
# -----------------------------------------------------------------------------
"""Copy a cleanup target's UNIQUE files to a preservation folder before its removal."""

import shutil
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    dest_root, rows_file, wt = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    copied = 0
    with (dest_root / "MANIFEST.tsv").open("a", encoding="utf-8") as manifest:
        for line in rows_file.read_text().splitlines():
            parts = line.split(None, 2)
            if len(parts) != 3 or not parts[1].endswith("/UNIQUE"):
                continue
            state, verdict, rel = parts
            dst = dest_root / wt.name / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(wt / rel, dst)
            manifest.write(f"{wt.name}\t{state}\t{verdict}\t{rel}\n")
            copied += 1
    print(f"{wt.name}: preserved {copied}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
