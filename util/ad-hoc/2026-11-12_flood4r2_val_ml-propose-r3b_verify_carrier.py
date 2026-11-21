#!/usr/bin/env python3
"""
Verify the ml-propose carrier (round 3b) before it is read: every file against its manifest's sha256, and the status of
its work tree re-derived without running a version-control command inside it.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 6)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
A stopped mutation helper once left a mutant in a carrier's source file. A validator therefore compares each carrier
file with the last sha256 its builder recorded before it builds on the tree, and again as its last step. The carrier
worktree is read-only to the validator, and the plumbing may not be run there, so the status is re-derived: the base
commit's tree is listed from the VALIDATOR's own worktree, each path of it is hashed as a blob from the carrier's
bytes, and every other file is put to the ignore rules (also from the validator's worktree).

Usage:
    python3 <this> --own-worktree <validator worktree> --out <json> [--compare <an earlier json of this script>]
Exit 0 = every manifest file matches, and the modified/added/deleted sets are the manifest's; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess  # nosec B404 - fixed argv: read-only plumbing in the validator's own worktree
import sys
from pathlib import Path

ML = Path.home() / "Development" / "python" / "Juniper" / "juniper-ml"
CARRIER = ML / ".claude" / "worktrees" / "agent-a211deee35ec85ad3"
DELIVERABLES = CARRIER / "tmp" / "flood4r2" / "ml-propose" / "r3b"
TEXTS = ("pr_title.txt", "pr_body.txt", "commit_body.txt", "changelog_entry.txt", "manifest.json", "dispositions.json", "stamps.json", "open_questions.json", "REPORT.txt")
LFS_HEAD = b"version https://git-lfs.github.com/spec/v1"


def run(root: Path, *argv: str, data: "bytes | None" = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *argv], cwd=root, input=data, capture_output=True, check=False)  # nosec B603 B607


def blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\x00" % len(data) + data, usedforsecurity=False).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def base_tree(own: Path, base: str) -> dict:
    listed = run(own, "ls-tree", "-r", "-z", base)
    if listed.returncode != 0:
        raise SystemExit("ls-tree failed: " + listed.stderr.decode("utf-8", "replace"))
    tree = {}
    for record in listed.stdout.split(b"\x00"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        mode, kind, sha = meta.decode().split()
        tree[path.decode("utf-8", "surrogateescape")] = (mode, kind, sha)
    return tree


def walk(root: Path) -> list:
    found = []
    for here, dirs, files in os.walk(root):
        rel = os.path.relpath(here, root)
        if rel == ".":
            dirs[:] = [name for name in dirs if name not in ("tmp", ".git")]
            files = [name for name in files if name != ".git"]
        for name in files:
            found.append(name if rel == "." else os.path.join(rel, name))
        for name in list(dirs):
            if os.path.islink(os.path.join(here, name)):
                found.append(name if rel == "." else os.path.join(rel, name))
    return found


def is_lfs_match(own: Path, sha: str, data: bytes) -> bool:
    pointer = run(own, "cat-file", "blob", sha).stdout
    if not pointer.startswith(LFS_HEAD):
        return False
    fields = dict(line.split(b" ", 1) for line in pointer.splitlines() if b" " in line)
    return fields.get(b"oid") == b"sha256:" + sha256(data).encode() and fields.get(b"size") == str(len(data)).encode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--own-worktree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    own = args.own_worktree.resolve()

    manifest = json.loads((DELIVERABLES / "manifest.json").read_text(encoding="utf-8"))
    base = manifest["base_sha"]
    report = {"carrier": str(CARRIER), "base_sha": base, "manifest_status": manifest.get("status"), "files": [], "problems": []}
    for entry in manifest["files"]:
        target = CARRIER / entry["path"]
        actual = sha256(target.read_bytes()) if target.is_file() else None
        report["files"].append({"path": entry["path"], "status": entry.get("status"), "manifest_sha256": entry.get("sha256"), "sha256": actual, "ok": actual == entry.get("sha256")})
        if actual != entry.get("sha256"):
            report["problems"].append(f"{entry['path']}: sha256 {str(actual)[:12]} is not the manifest's {str(entry.get('sha256'))[:12]}")

    tree = base_tree(own, base)
    on_disk = set(walk(CARRIER))
    modified, deleted, lfs_same = [], [], 0
    for path, (mode, kind, sha) in sorted(tree.items()):
        if kind != "blob":
            continue
        target = CARRIER / path
        if mode == "120000":
            if not target.is_symlink():
                (deleted if not target.exists() else modified).append(path)
            elif blob_sha1(os.readlink(target).encode("utf-8", "surrogateescape")) != sha:
                modified.append(path)
            continue
        if not target.is_file():
            deleted.append(path)
            continue
        data = target.read_bytes()
        if blob_sha1(data) == sha:
            continue
        if is_lfs_match(own, sha, data):
            lfs_same += 1
            continue
        modified.append(path)
    untracked = sorted(path for path in on_disk if path not in tree)
    ignored = set()
    if untracked:
        checked = run(own, "check-ignore", "--no-index", "-z", "--stdin", data="\x00".join(untracked).encode("utf-8", "surrogateescape"))
        ignored = {item.decode("utf-8", "surrogateescape") for item in checked.stdout.split(b"\x00") if item}
    added = [path for path in untracked if path not in ignored]

    want_modified = sorted(entry["path"] for entry in manifest["files"] if entry.get("status") == "modified")
    want_added = sorted(entry["path"] for entry in manifest["files"] if entry.get("status") == "added")
    report["derived_status"] = {"modified": modified, "added": added, "deleted": deleted, "lfs_files_equal_to_their_pointers": lfs_same, "untracked_and_ignored": len(ignored), "tracked_paths_in_base": len(tree)}
    if modified != want_modified:
        report["problems"].append(f"modified set differs from the manifest: only on disk {sorted(set(modified) - set(want_modified))}, only in manifest {sorted(set(want_modified) - set(modified))}")
    if added != want_added:
        report["problems"].append(f"added set differs from the manifest: only on disk {sorted(set(added) - set(want_added))}, only in manifest {sorted(set(want_added) - set(added))}")
    if deleted:
        report["problems"].append(f"deleted paths: {deleted}")

    report["deliverables"] = {name: sha256((DELIVERABLES / name).read_bytes()) for name in TEXTS if (DELIVERABLES / name).is_file()}
    if args.compare:
        earlier = json.loads(args.compare.read_text(encoding="utf-8"))
        before = {row["path"]: row["sha256"] for row in earlier["files"]}
        now = {row["path"]: row["sha256"] for row in report["files"]}
        report["compared_with"] = str(args.compare)
        report["changed_since_then"] = sorted(path for path in set(before) | set(now) if before.get(path) != now.get(path))
        report["deliverables_changed_since_then"] = sorted(name for name in set(earlier.get("deliverables", {})) | set(report["deliverables"]) if earlier.get("deliverables", {}).get(name) != report["deliverables"].get(name))
        if report["changed_since_then"]:
            report["problems"].append(f"carrier files changed since {args.compare.name}: {report['changed_since_then']}")
    report["ok"] = not report["problems"]
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("ok", "problems", "derived_status")}, indent=1))
    print(f"{sum(1 for row in report['files'] if row['ok'])} of {len(report['files'])} manifest files match their sha256")
    if args.compare:
        print("changed since the earlier run:", report["changed_since_then"], "deliverables:", report["deliverables_changed_since_then"])
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
