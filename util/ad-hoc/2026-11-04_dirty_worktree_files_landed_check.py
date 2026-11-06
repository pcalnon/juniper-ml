#!/usr/bin/env python3
"""Check whether each dirty file in a worktree is already on GitHub main (now or in its history).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-04
Status: ad-hoc -- one-off (the P12 worktree cleanup, owner ruling 2026-11-03)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-04_p12_worktree_cleanup_check.bash (which reports these trees as dirty)

Why
---
Sessions land work through util/open_signed_pr.py, which uploads whole files through the GitHub API and never
commits locally. The worktree they wrote from therefore stays "dirty" after the PR merges, although its content is
on main. This script computes each dirty file's git blob sha locally (no git needed) and compares it with the blob
of that path on main, and with the blobs in the path's last 40 commits on main. A file is LANDED when its exact
bytes appear there. Anything else is NOT-LANDED, which means its content exists only in the worktree.

Usage
-----
    python3 util/ad-hoc/2026-11-04_dirty_worktree_files_landed_check.py <repo> <worktree> <relpath> [<relpath> ...]

Prints one line per path; exit 0 when every path is LANDED, 1 otherwise. Read-only.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def blob_sha(data: bytes) -> str:
    """Return git's blob sha1 for ``data``."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def gh_json(endpoint: str):
    """Return the parsed JSON of a gh api GET, or None when it fails (e.g. 404)."""
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def main_blobs(repo: str, path: str) -> set[str]:
    """Return the blob shas of ``path`` at main and at each of its last 40 commits on main."""
    blobs = set()
    head = gh_json(f"repos/pcalnon/{repo}/contents/{path}?ref=main")
    if isinstance(head, dict) and head.get("sha"):
        blobs.add(head["sha"])
    commits = gh_json(f"repos/pcalnon/{repo}/commits?sha=main&path={path}&per_page=40") or []
    for commit in commits:
        entry = gh_json(f"repos/pcalnon/{repo}/contents/{path}?ref={commit['sha']}")
        if isinstance(entry, dict) and entry.get("sha"):
            blobs.add(entry["sha"])
    return blobs


def main() -> int:
    repo, worktree, paths = sys.argv[1], Path(sys.argv[2]), sys.argv[3:]
    all_landed = True
    for rel in paths:
        local = worktree / rel
        if not local.is_file():
            print(f"NOT-LANDED  {rel}  (missing locally)")
            all_landed = False
            continue
        sha = blob_sha(local.read_bytes())
        blobs = main_blobs(repo, rel)
        if sha in blobs:
            print(f"LANDED      {rel}")
        else:
            all_landed = False
            print(f"NOT-LANDED  {rel}  (local {sha[:8]}; {len(blobs)} main blob(s) compared)")
    return 0 if all_landed else 1


if __name__ == "__main__":
    sys.exit(main())
