#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml (cross-repo tooling)
# Application:   util/ad-hoc
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# Created:       2026-11-23
# Status:        ad-hoc (single arc: repair of the 2026-11-20 "owner -> Overtoad" rename PRs)
"""List the symlinks a commit turned into regular files, read from GitHub without a checkout.

Why this exists
---------------
``sed -i`` writes a regular file over every symlink it edits, so the owner's blind "owner -> Overtoad"
pass (2026-11-20) replaced links such as ``CLAUDE.md -> AGENTS.md`` with stale copies. Two of the rename
PRs (juniper-recurrence#237, juniper-deploy#281) merged before anyone looked. The PR files API shows a
type change only as a remove/add pair, so this compares the two trees' modes directly.

Usage
-----
    python3 2026-11-23_symlink_regressions.py REPO COMMIT [--owner pcalnon]

Compares COMMIT's first parent with COMMIT and prints every path that is a symlink (mode 120000) in the
parent but not in COMMIT, with the link target and the new mode. Exit 0 when there is none, 1 otherwise.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys


def gh(path: str) -> dict:
    out = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def tree_modes(owner: str, repo: str, sha: str) -> dict[str, tuple[str, str]]:
    data = gh(f"repos/{owner}/{repo}/git/trees/{sha}?recursive=1")
    if data.get("truncated"):
        raise SystemExit(f"tree {sha[:8]} is truncated; this tool needs the full listing")
    return {entry["path"]: (entry["mode"], entry["sha"]) for entry in data["tree"] if entry["type"] == "blob"}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repo")
    ap.add_argument("commit")
    ap.add_argument("--owner", default="pcalnon")
    args = ap.parse_args(argv)
    commit = gh(f"repos/{args.owner}/{args.repo}/commits/{args.commit}")
    parent = commit["parents"][0]["sha"]
    before = tree_modes(args.owner, args.repo, parent)
    after = tree_modes(args.owner, args.repo, commit["sha"])
    found = 0
    for path, (mode, blob) in sorted(before.items()):
        if mode != "120000":
            continue
        new_mode = after.get(path, ("(deleted)", ""))[0]
        if new_mode != "120000":
            target = base64.b64decode(gh(f"repos/{args.owner}/{args.repo}/git/blobs/{blob}")["content"]).decode()
            print(f"LINK->FILE {path} -> {target}  (now {new_mode})")
            found += 1
    links = sum(1 for mode, _ in before.values() if mode == "120000")
    print(f"{args.repo} {commit['sha'][:8]} (parent {parent[:8]}): {links} symlinks before, {found} turned into files")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
