#!/usr/bin/env python3
"""
Compare juniper-data working trees with a commit, whole tree, and copy named files from one tree to another.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: finishing juniper-data's stage-3 carrier, session 6)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (is the carrier exactly main plus its five paths, and is the mutation twin the carrier?)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session6/BRIEF_S6_ADDENDUM.txt step 1 (verify the carrier before you touch it);
         2026-11-11_flood4r2_data-landing_parent_check.py (which compares only the paths main changed)

Usage:
    python3 <this> verify --repo <juniper-data primary> --ref <commit> --tree <name>=<worktree> [--tree ...]
                          --changed <added|modified|deleted>:<repo-relative path> [--changed ...] --out <json>
    python3 <this> sync --src <worktree> --dst <worktree> --path <repo-relative path> [--path ...] --out <json>

verify
    For each tree: every path the commit holds and every file the tree holds (tracked, or untracked and not ignored)
    is compared with the commit's blob by git blob id, computed here from the working file's bytes (a symlink's
    target for a symlink). The paths that differ must be EXACTLY the --changed set, each with the stated status.
    The tree's HEAD does not matter: a tree checked out at an older commit that holds the newer commit's bytes
    compares equal. Each changed path's sha256 is recorded. Exit 0 only when every tree matches.
sync
    Copies each named path's bytes from --src to --dst (parents created), then reads both back and compares their
    sha256. It writes nothing else. Exit 0 only when every pair is equal.

Read-only apart from sync's copies and the --out file. The git commands are rev-parse, ls-tree and ls-files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess  # nosec B404 - fixed argv: read-only git queries
import sys
from pathlib import Path


def _git(cwd: Path, *argv: str) -> bytes:
    proc = subprocess.run(["git", "-C", str(cwd), *argv], capture_output=True, check=True)  # nosec B603 B607
    return proc.stdout


def _working_bytes(path: Path) -> bytes:
    if path.is_symlink():
        return os.readlink(path).encode("utf-8")
    return path.read_bytes()


def _blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\x00" % len(data) + data, usedforsecurity=False).hexdigest()


def _ref_blobs(repo: Path, ref: str) -> dict[str, str]:
    blobs: dict[str, str] = {}
    for record in _git(repo, "ls-tree", "-r", "-z", ref).split(b"\x00"):
        if not record:
            continue
        meta, name = record.split(b"\t", 1)
        _mode, kind, blob = meta.decode("ascii").split()
        if kind == "blob":
            blobs[name.decode("utf-8")] = blob
    return blobs


def _tree_paths(tree: Path) -> set[str]:
    listed = _git(tree, "ls-files", "-z") + _git(tree, "ls-files", "-z", "--others", "--exclude-standard")
    return {name.decode("utf-8") for name in listed.split(b"\x00") if name}


def _differences(tree: Path, blobs: dict[str, str]) -> dict[str, str]:
    found: dict[str, str] = {}
    for path in sorted(set(blobs) | _tree_paths(tree)):
        target = tree / path
        present = target.is_symlink() or target.is_file()
        if path not in blobs:
            if present:
                found[path] = "added"
        elif not present:
            found[path] = "deleted"
        elif _blob_id(_working_bytes(target)) != blobs[path]:
            found[path] = "modified"
    return found


def _sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _verify(args: argparse.Namespace) -> dict:
    repo = args.repo.resolve()
    ref = _git(repo, "rev-parse", args.ref).decode("ascii").strip()
    blobs = _ref_blobs(repo, ref)
    expected = {}
    for item in args.changed:
        status, path = item.split(":", 1)
        expected[path] = status
    rows = []
    for item in args.tree:
        name, where = item.split("=", 1)
        tree = Path(where).resolve()
        found = _differences(tree, blobs)
        rows.append(
            {
                "tree": name,
                "worktree": str(tree),
                "head": _git(tree, "rev-parse", "HEAD").decode("ascii").strip(),
                "paths_that_differ_from_ref": found,
                "unexpected": {path: status for path, status in found.items() if expected.get(path) != status},
                "expected_but_identical_to_ref": sorted(path for path in expected if path not in found),
                "is_ref_plus_exactly_the_changed_set": found == expected,
                "sha256": {path: _sha256(tree / path) for path in sorted(expected)},
            }
        )
    return {"mode": "verify", "ref": ref, "paths_at_ref": len(blobs), "changed_set": expected, "trees": rows, "ok": all(row["is_ref_plus_exactly_the_changed_set"] for row in rows)}


def _sync(args: argparse.Namespace) -> dict:
    src = args.src.resolve()
    dst = args.dst.resolve()
    rows = []
    for path in args.path:
        target = dst / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((src / path).read_bytes())
        rows.append({"path": path, "sha256_src": _sha256(src / path), "sha256_dst": _sha256(target), "equal": _sha256(src / path) == _sha256(target)})
    return {"mode": "sync", "src": str(src), "dst": str(dst), "files": rows, "ok": all(row["equal"] for row in rows)}


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--repo", type=Path, required=True)
    verify.add_argument("--ref", required=True)
    verify.add_argument("--tree", action="append", required=True, help="<name>=<worktree>")
    verify.add_argument("--changed", action="append", default=[], help="<added|modified|deleted>:<path>")
    verify.add_argument("--out", type=Path, required=True)
    sync = sub.add_parser("sync")
    sync.add_argument("--src", type=Path, required=True)
    sync.add_argument("--dst", type=Path, required=True)
    sync.add_argument("--path", action="append", required=True)
    sync.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    report = _verify(args) if args.mode == "verify" else _sync(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    print(json.dumps(report, indent=1))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
