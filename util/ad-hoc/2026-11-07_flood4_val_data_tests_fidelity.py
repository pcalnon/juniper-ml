#!/usr/bin/env python3
"""
Independently re-derive the provenance of every file in the juniper-data flood-4 TESTS carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#512 #513 #514 #516 #517; flood-4 validation brief (fidelity lens)

Reads only git objects (the carrier worktree's INDEX, the drafts' head commits, origin/main); writes
nothing to any repository. For each draft: merge-base with main, every path it changed (merge-base..head),
and whether main changed that path since the merge-base. For each carrier path: index blob vs main blob vs
draft head blob, and for a path main already has, the lines main has that the carrier lacks.

Optionally (third argument) copies the carrier's INDEX blobs into a validation worktree, byte-exact.

    python3 2026-11-07_flood4_val_data_tests_fidelity.py <carrier worktree> <juniper-data primary> [<copy-to worktree>]
"""

from __future__ import annotations

import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

DRAFTS = ["512", "513", "514", "516", "517"]


def git(repo: str, *args: str, check: bool = True) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=check).stdout


def git_bytes(repo: str, *args: str) -> bytes:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, check=True).stdout


def blob_of(repo: str, rev_path: str) -> str | None:
    out = subprocess.run(["git", "-C", repo, "rev-parse", "--verify", "--quiet", rev_path], capture_output=True, text=True)
    return out.stdout.strip() or None


def main() -> int:
    carrier, primary = sys.argv[1], sys.argv[2]
    copy_to = sys.argv[3] if len(sys.argv) > 3 else None
    main_sha = git(primary, "rev-parse", "origin/main").strip()
    head = git(carrier, "rev-parse", "HEAD").strip()
    print(f"origin/main={main_sha} carrier HEAD={head} equal={main_sha == head}")
    unstaged = git(carrier, "diff", "--name-only").strip()
    untracked = git(carrier, "ls-files", "--others", "--exclude-standard").strip()
    print(f"carrier unstaged changes: {unstaged or '(none)'}; untracked: {untracked or '(none)'}")
    staged = git(carrier, "diff", "--cached", "--name-status", "HEAD").strip().splitlines()
    print("carrier staged name-status vs HEAD:")
    for row in staged:
        print("   ", row)
    carrier_paths = [row.split("\t", 1)[1] for row in staged]

    print("\n=== drafts ===")
    draft_paths: dict[str, list[str]] = {}
    for n in DRAFTS:
        ref = f"refs/flood4/pr/{n}"
        hsha = git(primary, "rev-parse", ref).strip()
        mb = git(primary, "merge-base", main_sha, hsha).strip()
        commits = git(primary, "log", "--format=%h %s", f"{mb}..{hsha}").strip()
        ns = git(primary, "diff", "--name-status", mb, hsha).strip().splitlines()
        print(f"#{n} head={hsha} merge-base={mb}")
        print("  commits:")
        for c in commits.splitlines():
            print("    ", c)
        draft_paths[n] = []
        for row in ns:
            st, path = row.split("\t", 1)
            draft_paths[n].append(path)
            main_moved = git(primary, "diff", "--name-only", mb, main_sha, "--", path).strip()
            in_carrier = path in carrier_paths
            print(f"  {st} {path}  main-changed-since-mb={'YES' if main_moved else 'no'}  in-carrier={in_carrier}")
        # Files the draft READS (workflows/scripts) moved on main since its merge-base?
        moved = git(primary, "diff", "--name-only", mb, main_sha, "--", ".github/workflows", "scripts", "util", "juniper_data/api", "Makefile", "pyproject.toml").strip()
        print(f"  main moved since mb (workflows/scripts/util/api/Makefile/pyproject): {moved.splitlines() if moved else '(none)'}")

    print("\n=== carrier paths ===")
    for path in carrier_paths:
        idx = blob_of(carrier, f":{path}")
        mainb = blob_of(primary, f"{main_sha}:{path}")
        owners = [n for n, ps in draft_paths.items() if path in ps]
        heads = {n: blob_of(primary, f"refs/flood4/pr/{n}:{path}") for n in owners}
        same = {n: (b == idx) for n, b in heads.items()}
        print(f"{path}: index={idx} main={mainb} draft-owners={owners} equal-to-head={same}")
        if mainb is not None and idx is not None:
            old = git_bytes(primary, "cat-file", "-p", mainb).decode().splitlines()
            new = git_bytes(carrier, "cat-file", "-p", idx).decode().splitlines()
            removed = [ln for ln in difflib.ndiff(old, new) if ln.startswith("- ")]
            added = [ln for ln in difflib.ndiff(old, new) if ln.startswith("+ ")]
            print(f"   vs main: +{len(added)} -{len(removed)}")
            for ln in removed:
                print(f"   REMOVED-FROM-MAIN: {ln[2:]!r}")
        if copy_to and idx is not None:
            data = git_bytes(carrier, "cat-file", "-p", idx)
            dest = Path(copy_to) / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            print(f"   copied -> {dest} sha256={hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
