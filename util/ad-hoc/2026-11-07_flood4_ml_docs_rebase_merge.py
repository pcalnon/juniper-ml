#!/usr/bin/env python3
"""
3-way merge the flood-4 docs carrier's files onto a new base: ours = the checked-out HEAD, base = the old base, theirs = stored blobs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs-carrier rebase onto the tests carrier)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/ml-docs/work/rebase_theirs_blobs.txt (path -> theirs blob, the unbumped carrier on 303ccc0b)

For each `path theirs-blob` line, runs `git merge-file -p --object-id <HEAD:path> <old-base:path> <theirs>` and
writes the result over `path` in the working tree. git's exit status is the conflict count; it is printed per file
so a conflicted file is resolved by hand, never silently. Nothing is staged or committed.

Usage: 2026-11-07_flood4_ml_docs_rebase_merge.py <repo> <old-base> <blob-map.txt> [--only PATH ...]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def rev(repo: str, spec: str) -> str:
    return subprocess.run(["git", "-C", repo, "rev-parse", spec], capture_output=True, text=True, check=True).stdout.strip()


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__)
        return 2
    repo, old_base, blob_map = argv[1], argv[2], Path(argv[3])
    only = set(argv[argv.index("--only") + 1 :]) if "--only" in argv else None
    total = 0
    for line in blob_map.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 2 or not parts[1].isalnum() or len(parts[1]) != 40:
            continue
        path, theirs = parts
        if only is not None and path not in only:
            continue
        ours = rev(repo, f"HEAD:{path}")
        base = rev(repo, f"{old_base}:{path}")
        # File mode: `merge-file --object-id` hits "BUG: repository.c:171" in this worktree (git 2.53).
        # The three inputs go to a scratch dir under non-markdown names and are deleted at once.
        scratch = Path(repo) / "tmp" / "flood4" / "ml-docs" / "work" / "merge3"
        scratch.mkdir(parents=True, exist_ok=True)
        names = {}
        for label, blob in (("ours", ours), ("base", base), ("theirs", theirs)):
            data = subprocess.run(["git", "-C", repo, "cat-file", "blob", blob], capture_output=True, check=True).stdout
            names[label] = scratch / f"{path.replace('/', '__')}.{label}"
            names[label].write_bytes(data)
        try:
            proc = subprocess.run(["git", "merge-file", "-p", "-L", "ours (tests carrier)", "-L", "base (303ccc0b)", "-L", "theirs (docs carrier)", str(names["ours"]), str(names["base"]), str(names["theirs"])], capture_output=True, text=True, check=False)
        finally:
            for p in names.values():
                p.unlink()
        if proc.returncode < 0 or (proc.returncode > 0 and "<<<<<<<" not in proc.stdout):
            print(f"{path}: ERROR rc={proc.returncode} {proc.stderr.strip()[:200]}")
            return 2
        (Path(repo) / path).write_text(proc.stdout, encoding="utf-8")
        total += proc.returncode
        print(f"{path}: conflicts={proc.returncode} (ours {ours[:8]}, base {base[:8]}, theirs {theirs[:8]})")
    print(f"total conflicts: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
