#!/usr/bin/env python3
"""
Verify a predecessor carrier tree, read-only, before a rebuild takes anything from it.

The predecessor (round 1 of the flood-4 round-2 "ml-tests" carrier) is an UNCOMMITTED working tree in another
juniper-ml worktree, where this session may not run git. So its state is derived from its files alone:

  1. every file its manifest lists is hashed (sha256) and compared with the hash the manifest recorded;
  2. `git status --porcelain` is emulated against the predecessor's base commit, whose tree THIS checkout's
     object store holds: every tracked path's git blob id is recomputed from the predecessor's file
     (`blob <len>\\0<bytes>`, a symlink hashed as its target), giving the modified and deleted sets. A path
     whose base blob is a Git LFS pointer is compared by the pointer's `oid sha256:` instead (the working
     tree holds the smudged file, so its blob id never equals the pointer's);
  3. every other file of the predecessor (outside .git, the linked worktree's own `.git` file included, and
     not ignored by this checkout's ignore rules) is listed as untracked.

The modified + untracked sets must equal the manifest's file list: a path outside it is a change the predecessor
never recorded (a killed mutation helper once left a mutant in a carrier's source file).

Usage (from this worktree's root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_verify_predecessor.py --predecessor <abs dir>
        --manifest <abs manifest.json> --base <sha> --out <json>

Exit 0 when every recorded hash matches and the changed set equals the manifest's; 1 otherwise.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2)
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}
LFS_SPEC = "version https://git-lfs.github.com/spec/v1"


def _git(*argv: str, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(["git", *argv], input=stdin, capture_output=True, text=True, check=False)


def _blob_id(path: Path, mode: str) -> str:
    data = os.readlink(path).encode() if mode == "120000" else path.read_bytes()
    return hashlib.sha1(b"blob %d\x00" % len(data) + data, usedforsecurity=False).hexdigest()


def _lfs_oid(blob_sha: str) -> str:
    """The `oid sha256:` of a Git LFS pointer blob, or "" when the blob is not a pointer."""
    size = _git("cat-file", "-s", blob_sha).stdout.strip()
    if not size.isdigit() or int(size) > 400:
        return ""
    text = _git("cat-file", "-p", blob_sha).stdout
    if not text.startswith(LFS_SPEC):
        return ""
    oids = [line.split("sha256:", 1)[1].strip() for line in text.splitlines() if line.startswith("oid sha256:")]
    return oids[0] if oids else ""


def _base_tree(base: str) -> dict:
    out = _git("ls-tree", "-r", base)
    if out.returncode != 0:
        raise SystemExit(f"git ls-tree {base}: {out.stderr.strip()}")
    tree = {}
    for line in out.stdout.splitlines():
        meta, path = line.split("\t", 1)
        mode, kind, sha = meta.split()
        if kind == "blob":
            tree[path] = (mode, sha)
    return tree


def _walk(root: Path) -> list:
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel_dir = Path(dirpath).relative_to(root)
        found += [str(rel_dir / name) if str(rel_dir) != "." else name for name in filenames]
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--predecessor", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    pred = Path(args.predecessor)
    with open(args.manifest, encoding="utf-8") as fh:
        manifest = json.load(fh)
    recorded = {f["path"]: f for f in manifest["files"]}

    hashes = []
    for path, row in sorted(recorded.items()):
        target = pred / path
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        hashes.append({"path": path, "status": row["status"], "recorded": row.get("sha256"), "actual": actual, "match": actual is not None and actual == row.get("sha256")})

    tree = _base_tree(args.base)
    modified, deleted, lfs_same = [], [], 0
    for path, (mode, sha) in sorted(tree.items()):
        target = pred / path
        if not (target.is_file() or target.is_symlink()):
            deleted.append(path)
        elif _blob_id(target, mode) != sha:
            oid = _lfs_oid(sha)
            if oid and hashlib.sha256(target.read_bytes()).hexdigest() == oid:
                lfs_same += 1
            else:
                modified.append(path)
    others = sorted(p for p in _walk(pred) if p not in tree and p != ".git")
    ignored = set(_git("check-ignore", "--stdin", stdin="\n".join(others) + "\n").stdout.splitlines()) if others else set()
    untracked = [p for p in others if p not in ignored]

    changed = sorted(set(modified) | set(untracked) | set(deleted))
    report = {
        "predecessor": str(pred),
        "manifest": args.manifest,
        "base": args.base,
        "manifest_files": len(recorded),
        "hash_matches": sum(1 for h in hashes if h["match"]),
        "hash_mismatches": [h for h in hashes if not h["match"]],
        "emulated_status": {"modified": modified, "deleted": deleted, "untracked": untracked, "lfs_pointer_paths_whose_smudged_file_matches": lfs_same},
        "changed_not_in_manifest": [p for p in changed if p not in recorded],
        "manifest_not_changed": [p for p in sorted(recorded) if p not in changed],
        "hashes": hashes,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    ok = not report["hash_mismatches"] and not report["changed_not_in_manifest"] and not report["manifest_not_changed"]
    print(f"manifest files: {len(recorded)}; sha256 matches: {report['hash_matches']}; mismatches: {len(report['hash_mismatches'])}")
    print(f"emulated status vs {args.base[:8]}: modified {len(modified)}, deleted {len(deleted)}, untracked (not ignored) {len(untracked)}; {lfs_same} LFS paths match their pointer's oid")
    print(f"changed but not in the manifest: {report['changed_not_in_manifest']}")
    print(f"in the manifest but unchanged: {report['manifest_not_changed']}")
    print("VERDICT:", "predecessor matches its manifest" if ok else "DIFFERENCE -- do not build on it until explained")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
