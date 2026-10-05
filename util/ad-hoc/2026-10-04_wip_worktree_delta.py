#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File:          2026-10-04_wip_worktree_delta.py
# Author:        Paul Calnon
# Version:       1.0.0
# License:       MIT License
# -----------------------------------------------------------------------------
# Purpose: inventory (and optionally transplant) the UNCOMMITTED delta of a
# sibling worktree WITHOUT running git inside it.
#
# A worktree-isolated Claude Code session may not run git against another
# worktree of the same repository (`git -C <sibling>` is refused), and an
# uncommitted file there is invisible to git everywhere else. This script reads
# the sibling's files directly and compares them with a commit from the shared
# object store, which the calling worktree CAN read:
#
#   tracked   = paths in `git ls-tree -r <base>`; modified when the on-disk blob
#               id differs, deleted when the file is missing
#   untracked = files on disk that are not in <base>, filtered through
#               `git check-ignore` run in THIS worktree (same .gitignore rules)
#
# Subcommands:
#   list      print M/D/?? lines, one per path
#   transplant --onto-dir <dir>
#             3-way merge each modified tracked file (base=<base>:path,
#             ours=<dir>/path, theirs=sibling file) with `git merge-file`, and
#             copy each untracked file; prints CONFLICT for any merge that does
#             not apply cleanly and leaves conflict markers for inspection.
#
# Read-only against the sibling: it never writes there and never runs git there.
# -----------------------------------------------------------------------------
import argparse
import hashlib
import os
import shutil
import subprocess
import sys

SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules"}


def git(*args, input_text=None):
    """Run git in the CURRENT working directory and return stdout."""
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, input=input_text).stdout


def blob_id(path):
    """Git blob SHA-1 of a file's bytes, or of a symlink's target string."""
    if os.path.islink(path):
        data = os.readlink(path).encode()
    else:
        with open(path, "rb") as fh:
            data = fh.read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def tracked_entries(base):
    entries = {}
    for line in git("ls-tree", "-r", "--full-tree", base).splitlines():
        meta, path = line.split("\t", 1)
        mode, _kind, sha = meta.split()
        entries[path] = (mode, sha)
    return entries


def walk_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            full = os.path.join(dirpath, name)
            yield os.path.relpath(full, root)


def lfs_paths(paths):
    """Paths whose `filter` attribute is lfs: on disk they are smudged content, in git a pointer."""
    if not paths:
        return set()
    out = git("check-attr", "filter", "--stdin", input_text="\n".join(paths) + "\n")
    return {line.split(": filter: ")[0] for line in out.splitlines() if line.endswith(": filter: lfs")}


def delta(sibling, base):
    entries = tracked_entries(base)
    lfs = lfs_paths(sorted(entries))
    modified, deleted = [], []
    for path, (mode, sha) in sorted(entries.items()):
        if mode == "160000" or path in lfs:
            continue  # submodule gitlink, or an LFS pointer that never matches the smudged file
        full = os.path.join(sibling, path)
        if not os.path.lexists(full):
            deleted.append(path)
        elif blob_id(full) != sha:
            modified.append(path)
    # `.git` at the top of a linked worktree is a FILE naming its gitdir, never content.
    candidates = sorted(p for p in walk_files(sibling) if p not in entries and p != ".git")
    ignored = set()
    if candidates:
        proc = subprocess.run(["git", "check-ignore", "--no-index", "--stdin"], capture_output=True, text=True, input="\n".join(candidates) + "\n")
        ignored = set(proc.stdout.splitlines())
    untracked = [p for p in candidates if p not in ignored]
    return modified, deleted, untracked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sibling", required=True, help="absolute path of the sibling worktree")
    parser.add_argument("--base", required=True, help="the commit the sibling's working tree is based on (its HEAD)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    tp = sub.add_parser("transplant")
    tp.add_argument("--onto-dir", required=True, help="worktree to receive the delta (usually this one)")
    args = parser.parse_args()

    modified, deleted, untracked = delta(args.sibling, args.base)
    if args.cmd == "list":
        for p in modified:
            print(f"M  {p}")
        for p in deleted:
            print(f"D  {p}")
        for p in untracked:
            print(f"?? {p}")
        print(f"# modified={len(modified)} deleted={len(deleted)} untracked={len(untracked)}", file=sys.stderr)
        return 0

    conflicts = 0
    for p in modified:
        ours = os.path.join(args.onto_dir, p)
        theirs = os.path.join(args.sibling, p)
        base_text = git("show", f"{args.base}:{p}")
        base_tmp = ours + ".transplant-base"
        with open(base_tmp, "w") as fh:
            fh.write(base_text)
        try:
            if not os.path.exists(ours):
                print(f"CONFLICT {p}: absent in target (deleted upstream?)")
                conflicts += 1
                continue
            rc = subprocess.run(["git", "merge-file", "-L", "main", "-L", "base", "-L", "wip", ours, base_tmp, theirs]).returncode
            if rc != 0:
                print(f"CONFLICT {p}: {rc} hunk(s)")
                conflicts += 1
            else:
                print(f"MERGED   {p}")
        finally:
            os.unlink(base_tmp)
    for p in deleted:
        print(f"DELETE?  {p} (not applied; review by hand)")
    for p in untracked:
        dst = os.path.join(args.onto_dir, p)
        if os.path.exists(dst):
            if blob_id(dst) == blob_id(os.path.join(args.sibling, p)):
                print(f"SAME     {p}")
                continue
            print(f"EXISTS   {p}: target differs; not overwritten")
            conflicts += 1
            continue
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        shutil.copy2(os.path.join(args.sibling, p), dst)
        print(f"COPIED   {p}")
    print(f"# conflicts={conflicts}", file=sys.stderr)
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
