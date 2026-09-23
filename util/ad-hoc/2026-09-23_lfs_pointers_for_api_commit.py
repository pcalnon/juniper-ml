"""
Prepare LFS-tracked files for a GitHub API (signed) commit: store each in the local LFS object store,
write its POINTER text to a mirror directory, and print the oids to push.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — tooling
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/open_signed_pr.py, util/push_signed_commit.py (both upload file BYTES, which for an
         LFS-tracked path must be the pointer, never the image)

Why: juniper-ml's ``.gitattributes`` routes ``*.png`` / ``*.jpg`` through Git LFS, and the existing
report screenshots on main are pointers. ``createCommitOnBranch`` commits whatever bytes it is given,
so uploading the PNG itself would put a raw blob where every clone expects a pointer. The fix is the
same split ``git push`` does: the object goes to the LFS store (``git lfs push --object-id``), the
pointer goes into the commit.

Usage (from the repo's worktree root):
    python3 util/ad-hoc/2026-09-23_lfs_pointers_for_api_commit.py <pointer-out-dir> <file> [<file> ...]
Then:
    git lfs push --object-id origin <oid> [<oid> ...]      # the oids this prints
and pass ``<pointer-out-dir>/<file>:<file>`` to the commit tool for each file.
"""

import subprocess
import sys
from pathlib import Path


def main():
    out_dir = Path(sys.argv[1]).resolve()
    files = sys.argv[2:]
    oids = []
    for rel in files:
        path = Path(rel)
        data = path.read_bytes()
        # ``git lfs clean`` is the filter git runs on ``git add``: it copies the content into
        # .git/lfs/objects and writes the pointer to stdout.
        pointer = subprocess.run(["git", "lfs", "clean", "--", rel], input=data, capture_output=True, check=True).stdout
        text = pointer.decode()
        if not text.startswith("version https://git-lfs.github.com/spec/v1"):
            raise SystemExit(f"{rel}: not an LFS pointer:\n{text[:200]}")
        oid = next(line.split(":", 1)[1] for line in text.splitlines() if line.startswith("oid sha256:"))
        size = next(int(line.split(" ", 1)[1]) for line in text.splitlines() if line.startswith("size "))
        if size != len(data):
            raise SystemExit(f"{rel}: pointer size {size} != file size {len(data)}")
        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(pointer)
        oids.append(oid)
        print(f"{oid} {size:>9} {rel}")
    print("OIDS " + " ".join(oids))


if __name__ == "__main__":
    main()
