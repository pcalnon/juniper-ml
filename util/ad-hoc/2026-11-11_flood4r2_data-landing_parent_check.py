#!/usr/bin/env python3
"""
Check that the live main still is the tree a landing stage was built on, path by path.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (stages 1 and 2 landed; is stage 3's recorded parent what main now holds?)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: 2026-11-11_flood4r2_data-landing_manifest.py (which records ``parent_sha256`` per file);
         notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
    python3 <this> --repo <juniper-data primary> --ref <live main sha> --manifest <stage manifest.json> --out <json>

Two questions, both answered by sha256 of file bytes:
  1. For each path the stage changes: does the blob at --ref equal the manifest's ``parent_sha256`` (or, for a path
     the stage adds, is it absent at --ref)? If so the stage's copy can be laid over --ref verbatim.
  2. For every OTHER path that differs between the stage worktree's HEAD and --ref: does the stage worktree hold
     exactly --ref's bytes? If so the stage worktree IS --ref plus the stage's own files, and what was measured in
     it was measured on the tree that will land.
Exit 0 only when both hold for every path. Read-only: git show, git diff --name-only, and file reads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed argv: read-only git queries
import sys
from pathlib import Path


def _git(repo: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *argv], capture_output=True, check=False)  # nosec B603 B607


def _blob_sha(repo: Path, ref: str, path: str) -> str | None:
    shown = _git(repo, "show", f"{ref}:{path}")
    return hashlib.sha256(shown.stdout).hexdigest() if shown.returncode == 0 else None


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    with open(args.manifest, encoding="utf-8") as fh:
        manifest = json.load(fh)
    worktree = Path(manifest["worktree"])
    ref = _git(repo, "rev-parse", args.ref).stdout.decode().strip()
    head = _git(worktree, "rev-parse", "HEAD").stdout.decode().strip()
    own = {entry["path"]: entry for entry in manifest["files"]}

    own_rows = []
    for path, entry in own.items():
        at_ref = _blob_sha(repo, ref, path)
        own_rows.append({"path": path, "status": entry["status"], "parent_sha256": entry.get("parent_sha256"), "sha256_at_ref": at_ref, "ref_is_the_recorded_parent": at_ref == entry.get("parent_sha256")})

    moved = sorted(set(_git(repo, "diff", "--name-only", head, ref).stdout.decode().split()) - set(own))
    other_rows = []
    for path in moved:
        target = worktree / path
        in_tree = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        at_ref = _blob_sha(repo, ref, path)
        other_rows.append({"path": path, "sha256_in_stage_worktree": in_tree, "sha256_at_ref": at_ref, "identical": in_tree == at_ref})

    report = {
        "ref": ref,
        "stage_worktree_head": head,
        "stage": manifest["stage"],
        "own_files": own_rows,
        "own_files_all_match": all(row["ref_is_the_recorded_parent"] for row in own_rows),
        "other_paths_ref_changed_since_the_worktree_head": other_rows,
        "other_paths_all_identical": all(row["identical"] for row in other_rows),
    }
    report["stage_worktree_is_ref_plus_the_stage"] = report["own_files_all_match"] and report["other_paths_all_identical"]
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    print(json.dumps(report, indent=1))
    return 0 if report["stage_worktree_is_ref_plus_the_stage"] else 1


if __name__ == "__main__":
    sys.exit(main())
