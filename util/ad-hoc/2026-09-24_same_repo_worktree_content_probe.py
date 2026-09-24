#!/usr/bin/env python3
"""Tell whether a SIBLING juniper-ml worktree holds anything that is not on origin/main -- without git in it.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc safety probe (canopy selection arc cleanup, W5)
Author:      Paul Calnon
License:     MIT License

Why this exists. A worktree-isolated Claude session may not run git against another worktree
of its OWN repo: ``git -C <sibling .claude/worktrees/x>`` is refused ("a worktree-isolated
session's git operations must target its own worktree"). That is a deliberate guard, so this
does not route around it by shelling git into the sibling. It reads the sibling's FILES, which
the guard allows, and asks this session's own git for the object database the two share:

* ``ls-tree`` of the sibling's HEAD (taken from ``git worktree list --porcelain``) and of
  ``origin/main``;
* a git blob id computed in-process for every file on disk, the same bytes git would hash;
* ``check-ignore --no-index`` against this worktree's ignore rules, to split untracked from
  ignored for anything HEAD does not track.

Each path is then one of: unchanged from HEAD; changed-or-new and IDENTICAL on origin/main
(shipped); changed-or-new and NOT on origin/main (review); ignored (listed with size, since
removal deletes it). LFS files are compared through their pointer's ``oid``. Read-only.

It answers "is anything here unshipped?" -- not "may this tree be removed?". Liveness and the
removal itself stay with the owner; this session does not remove a sibling worktree of its own repo.

Usage:
    python3 util/ad-hoc/2026-09-24_same_repo_worktree_content_probe.py <sibling-worktree-dir> [...]
"""
from __future__ import annotations

import hashlib
import os
import subprocess  # nosec B404 -- fixed-argv git calls in this session's own worktree
import sys
from pathlib import Path

SKIP_DIRS = {".git"}


def git(*args: str, stdin: str | None = None) -> str:
    p = subprocess.run(["git", *args], input=stdin, capture_output=True, text=True)  # nosec B603 B607 -- fixed-argv git from PATH
    if p.returncode not in (0, 1):  # check-ignore exits 1 when nothing matched
        raise SystemExit(f"git {' '.join(args[:3])} failed: {p.stderr.strip()[:200]}")
    return p.stdout


def tree(ref: str) -> dict[str, str]:
    out = {}
    for ln in git("ls-tree", "-r", "--full-tree", ref).splitlines():
        meta, path = ln.split("\t", 1)
        out[path] = meta.split()[2]
    return out


def head_of(wt: Path) -> str | None:
    cur = None
    for ln in git("worktree", "list", "--porcelain").splitlines():
        if ln.startswith("worktree "):
            cur = ln[9:]
        elif ln.startswith("HEAD ") and cur == str(wt):
            return ln[5:]
    return None


def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data, usedforsecurity=False).hexdigest()


def lfs_oid(pointer_blob: str) -> str | None:
    txt = git("cat-file", "blob", pointer_blob)
    if not txt.startswith("version https://git-lfs"):
        return None
    for ln in txt.splitlines():
        if ln.startswith("oid sha256:"):
            return ln.split(":", 1)[1]
    return None


def same(path: str, data: bytes, want: str | None) -> bool:
    if want is None:
        return False
    if blob_id(data) == want:
        return True
    oid = lfs_oid(want) if len(data) > 200 else None  # a smudged LFS file vs its pointer
    return oid is not None and hashlib.sha256(data).hexdigest() == oid


def walk(wt: Path):
    for root, dirs, files in os.walk(wt):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in files:
            full = Path(root, n)
            rel = str(full.relative_to(wt))
            if rel == ".git":
                continue
            if full.is_symlink():
                yield rel, os.readlink(full).encode()
            else:
                try:
                    yield rel, full.read_bytes()
                except OSError:
                    yield rel, None


def probe(wt: Path, main: dict[str, str]) -> int:
    head = head_of(wt)
    if head is None:
        print(f"{wt}: not a worktree of this repo")
        return 2
    htree = tree(head)
    unchanged, shipped, review, missing, untracked = 0, [], [], [], []
    seen = set()
    for rel, data in walk(wt):
        seen.add(rel)
        if data is None:
            review.append(f"{rel} (unreadable)")
            continue
        if rel in htree and same(rel, data, htree[rel]):
            unchanged += 1
        elif rel in htree:
            (shipped if same(rel, data, main.get(rel)) else review).append(rel)
        else:
            untracked.append((rel, data))
    ignored_raw = git("check-ignore", "--no-index", "--stdin", stdin="\n".join(r for r, _ in untracked) + "\n")
    ignored = set(ignored_raw.splitlines())
    ign_bytes: dict[str, int] = {}
    # origin/main FIRST: an ignored path can still be committed (force-added past the rule --
    # the A-N2 report's 92 files under `**/logs/` are), and then it is shipped, not debris.
    ign_files: list[str] = []
    for rel, data in untracked:
        if same(rel, data, main.get(rel)):
            shipped.append(rel)
        elif rel in ignored:
            top = rel.split("/", 1)[0] if "/" in rel else rel
            ign_bytes[top] = ign_bytes.get(top, 0) + len(data)
            ign_files.append(rel)
        else:
            review.append(f"{rel} (untracked)")
    for rel in htree:
        if rel not in seen and not (wt / rel).is_symlink():
            (shipped if rel not in main else missing).append(rel)
    print(f"== {wt.name}  HEAD {head[:8]}")
    print(f"   unchanged-from-HEAD {unchanged}   changed/new AND on origin/main {len(shipped)}   NOT on origin/main {len(review)}")
    for r in review[:40]:
        print(f"   REVIEW   {r}")
    if len(review) > 40:
        print(f"   ... +{len(review) - 40} more")
    for r in missing[:10]:
        print(f"   DELETED-LOCALLY-BUT-ON-MAIN {r}")
    for top, n in sorted(ign_bytes.items(), key=lambda kv: -kv[1]):
        print(f"   ignored  {top}  {n / 1e6:.2f} MB")
    authored = [f for f in ign_files if "__pycache__/" not in f and not f.endswith((".pyc", ".egg-info"))
                and ".egg-info/" not in f]
    for f in authored[:25]:
        print(f"   ignored-not-cache  {f}")
    if len(authored) > 25:
        print(f"   ... +{len(authored) - 25} more ignored non-cache files")
    return 1 if review else 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    main_tree = tree("origin/main")
    return max(probe(Path(a).resolve(), main_tree) for a in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
