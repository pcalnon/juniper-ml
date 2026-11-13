#!/usr/bin/env python3
"""
Carry a worktree's UNCOMMITTED edits onto a moved ``origin/main``: fast-forward the worktree, three-way merge the overlap.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- written for the fork PRs of the R-OBS-SC-2 follow-ups, whose bases moved five times in a day
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/open_signed_pr.py (uploads WHOLE files, so an upload from a stale base reverts whatever main gained);
         util/ad-hoc/2026-11-12_upload_set_hashes.py (records the set this script changes: re-record after it)

Why
---
``util/open_signed_pr.py`` builds a signed commit from whole files, so the files have to be edited on the base the
branch is cut from. The edits are therefore kept uncommitted in a worktree whose HEAD is ``origin/main``. When
``main`` moves, HEAD has to follow, and a file both sides changed (``CHANGELOG.md``, every time) has to be merged.
``git stash`` would do it, but the stash stack is shared by every worktree of the repository and other sessions use
it. This script does the same thing with files:

1. fetch ``origin``; stop if HEAD already equals ``origin/main``, or if HEAD is not an ancestor of it;
2. for each locally modified tracked file that ``main`` also changed, run ``git merge-file`` on (mine, HEAD's,
   ``origin/main``'s) -- a conflict in ANY file stops the run before anything is written;
3. restore the modified tracked files to HEAD, fast-forward to ``origin/main``, and write back the merged or the
   unchanged-upstream contents. Untracked files are never touched. Every edited file is copied to the scratch
   directory (``<NNN>__<path with / as __>.mine``) before the restore, so a crash in this step loses nothing.

It refuses, before writing anything: a staged change, a mode change, a symlink or submodule, and an edited file that
``origin/main`` has deleted or renamed. ``--no-renames`` keeps a file main renamed from reading as untouched.

``--dry-run`` stops after step 2 and prints what it would do.

Usage
-----
    python3 util/ad-hoc/2026-11-12_rehome_worktree_edits_on_new_main.py --worktree DIR [--scratch DIR] [--dry-run]

Exit 0 when the worktree is on ``origin/main`` with its edits in place (or already was); 1 on a conflict or a refusal.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 -- git in argv form, no shell
import tempfile
from pathlib import Path


def git(worktree: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, check=check)  # nosec B603 B607


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--scratch", help="where the three versions of each merged file are kept (default: a new directory under $TMPDIR)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    worktree = Path(args.worktree).resolve()
    scratch = Path(args.scratch).resolve() if args.scratch else Path(tempfile.mkdtemp(prefix="rehome-"))
    scratch.mkdir(parents=True, exist_ok=True)

    git(worktree, "fetch", "--quiet", "origin")
    head = git(worktree, "rev-parse", "HEAD").stdout.decode().strip()
    main_sha = git(worktree, "rev-parse", "origin/main").stdout.decode().strip()
    print(f"worktree: {worktree}\nHEAD {head[:12]}  origin/main {main_sha[:12]}")
    if head == main_sha:
        print("result: already on origin/main; nothing to do")
        return 0
    if git(worktree, "merge-base", "--is-ancestor", head, main_sha, check=False).returncode != 0:
        print("result: REFUSED -- HEAD is not an ancestor of origin/main (this worktree has commits of its own)")
        return 1

    status = git(worktree, "status", "--porcelain=v1", "-z").stdout.decode("utf-8")
    modified: list[str] = []
    for entry in filter(None, status.split("\0")):
        code, name = entry[:2], entry[3:]
        if code == "??":
            continue
        if code != " M":
            # A staged change (``M `` or ``MM``) would be lost by the checkout below, so it is refused, not handled.
            print(f"result: REFUSED -- {name!r} has status {code!r}; this script handles unstaged modifications only")
            return 1
        modified.append(name)
    # --no-renames: with rename detection (git's default) a file main RENAMED is listed under its new name only, so
    # the edited old path would read as "main did not touch it" and be written back as a stray untracked file.
    upstream = set(filter(None, git(worktree, "diff", "--name-only", "--no-renames", "-z", head, main_sha).stdout.decode("utf-8").split("\0")))
    print(f"locally modified: {len(modified)}  changed on main since HEAD: {len(upstream)}")
    print(f"scratch (a copy of every edited file goes here first): {scratch}")

    # Everything this script cannot carry is refused BEFORE anything is written.
    for name in modified:
        path = worktree / name
        if path.is_symlink() or not path.is_file():
            print(f"result: REFUSED -- {name!r} is not a regular file (a symlink or a submodule); carry it by hand")
            return 1
        raw = git(worktree, "diff", "--raw", "--no-renames", "--", name).stdout.decode("utf-8", errors="replace")
        if raw.startswith(":") and raw[1:7] != raw[8:14]:
            print(f"result: REFUSED -- {name!r} has an uncommitted mode change ({raw[1:7]} -> {raw[8:14]}), which a restore would drop")
            return 1
        if git(worktree, "cat-file", "-e", f"{main_sha}:{name}", check=False).returncode != 0:
            print(f"result: REFUSED -- origin/main no longer has {name!r} (deleted or renamed there); carry the edit by hand")
            return 1

    contents: dict[str, bytes] = dict()
    originals: dict[str, bytes] = dict()
    conflicts: list[str] = []
    for number, name in enumerate(modified):
        mine = (worktree / name).read_bytes()
        originals[name] = mine
        # The index keeps two paths that differ only in "/" versus "__" apart.
        stem = f"{number:03d}__" + name.replace("/", "__")
        paths = dict((role, scratch / f"{stem}.{role}") for role in ("mine", "base", "theirs"))
        # EVERY edited file is copied out before anything destructive, the ones main did not touch included: if this
        # process dies between the checkout and the write-back below, the edits are in the scratch directory.
        paths["mine"].write_bytes(mine)
        if name not in upstream:
            contents[name] = mine
            print(f"  keep   {name}")
            continue
        paths["base"].write_bytes(git(worktree, "show", f"{head}:{name}").stdout)
        paths["theirs"].write_bytes(git(worktree, "show", f"{main_sha}:{name}").stdout)
        merged = subprocess.run(["git", "merge-file", "-p", str(paths["mine"]), str(paths["base"]), str(paths["theirs"])], capture_output=True, check=False)  # nosec B603 B607
        if merged.returncode != 0:
            conflicts.append(name)
            print(f"  CONFLICT {name} (git merge-file exit {merged.returncode}); the three versions are in {scratch}")
            continue
        contents[name] = merged.stdout
        (scratch / f"{stem}.merged").write_bytes(merged.stdout)
        print(f"  merge  {name}")
    if conflicts:
        print(f"result: CONFLICT in {len(conflicts)} file(s); nothing was changed")
        return 1
    if args.dry_run:
        print("result: dry run; nothing was changed")
        return 0

    if modified:
        git(worktree, "checkout", "--", *modified)
    # --no-overwrite-ignore: by default a fast-forward silently replaces an IGNORED local file that main now tracks.
    forwarded = git(worktree, "merge", "--ff-only", "--no-overwrite-ignore", main_sha, check=False)
    if forwarded.returncode != 0:
        # Put the edits back exactly as they were, from memory: HEAD has not moved.
        for name in modified:
            (worktree / name).write_bytes(originals[name])
        print(f"result: REFUSED -- fast-forward failed, edits restored: {forwarded.stderr.decode(errors='replace').strip()[:300]}")
        return 1
    for name, data in contents.items():
        (worktree / name).write_bytes(data)
    now = git(worktree, "rev-parse", "HEAD").stdout.decode().strip()
    print(f"HEAD is now {now[:12]}")
    print(git(worktree, "status", "--short").stdout.decode("utf-8").rstrip())
    print(git(worktree, "diff", "--stat").stdout.decode("utf-8").rstrip())
    print("result: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
