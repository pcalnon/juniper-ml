#!/usr/bin/env python3
"""Check a carrier tree against its manifest's sha256 values, and list what else in it differs from a commit, without running git in it.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use build step)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-12
Status:      ad-hoc -- one-off (landing step of the N-2 carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
             (juniper-service-core's stop-then-start race); util/ad-hoc/2026-11-11_flood4r2_n2-r2_assemble.py

Why: a builder that was stopped mid-run can leave a mutant in a carrier file, so a carrier is
compared with the hashes its builder last recorded before anything is built on it, and again as
the last step of the build that used it.

Two checks, both reading the tree as plain files:

- every file the manifest lists is hashed and compared with the manifest's ``sha256`` (and with a
  ``sha256sum``-style file, when ``--sha-file`` names one);
- with ``--base``, the stand-in for ``git status --porcelain`` in a tree where git may not be run:
  every path of that commit (listed from THIS checkout's object store) is compared with the tree's
  copy by git blob id, and the tree is walked for files the commit does not have. A file the commit
  holds as an LFS pointer is compared by the sha256 the pointer names. Ignored files are dropped
  with ``git check-ignore --no-index`` run in this checkout, so the answer follows this checkout's
  ignore files; a directory that ignores itself (a tool cache whose own ignore file has a bare
  ``*`` line) is skipped, and ``--prune`` names directories that are not walked at all.

The result should be exactly the manifest: its modified files differ from the commit, its added
files are new, and nothing else is modified, deleted or new.

Exit status: 0 when every hash matches and (with ``--base``) the tree differs from the commit in
the manifest's files only; 1 otherwise; 2 on a usage error.

Usage (from this worktree's root):
    python3 util/ad-hoc/2026-11-12_flood4r2_n2-land_verify_tree.py --tree <carrier tree> --manifest <manifest.json> \\
        [--sha-file <sha256 file>] [--base <commit>] [--prune <dir name> ...] [--out <report.json>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRUNE = (".git", "tmp", "node_modules", "__pycache__")


def _git(*args: str, data: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, input=data, capture_output=True, check=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _blob_id(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data, usedforsecurity=False).hexdigest()


def _lfs_oid(blob: str) -> str | None:
    """The sha256 an LFS pointer blob names (the checked-out file is then the real content), or None for an ordinary blob."""
    sized = _git("cat-file", "-s", blob)
    if sized.returncode != 0 or int(sized.stdout.decode().strip() or "0") > 1024:
        return None
    text = _git("cat-file", "blob", blob).stdout.decode("utf-8", "replace")
    if not text.startswith("version https://git-lfs.github.com/spec/"):
        return None
    for line in text.splitlines():
        if line.startswith("oid sha256:"):
            return line.split(":", 1)[1].strip()
    return None


def _ignores_itself(folder: Path, files: list[str]) -> bool:
    """A tool cache directory that carries its own ignore file with a bare ``*`` line (ruff, pytest and mypy write one)."""
    if ".gitignore" not in files:
        return False
    return any(line.strip() == "*" for line in (folder / ".gitignore").read_text(encoding="utf-8", errors="replace").splitlines())


def _hash_rows(tree: Path, manifest: dict, sha_file: Path | None) -> list[dict]:
    recorded = {}
    if sha_file is not None:
        for line in sha_file.read_text(encoding="utf-8").splitlines():
            digest, _, rel = line.strip().partition("  ")
            if rel:
                recorded[rel] = digest
    rows = []
    for entry in manifest["files"]:
        rel = entry["path"]
        source = tree / rel
        row = {"path": rel, "status": entry.get("status"), "manifest_sha256": entry.get("sha256"), "tree_sha256": _sha256(source) if source.is_file() else None}
        row["matches_manifest"] = row["tree_sha256"] is not None and row["tree_sha256"] == row["manifest_sha256"]
        if sha_file is not None:
            row["sha_file_sha256"] = recorded.get(rel)
            row["matches_sha_file"] = row["tree_sha256"] is not None and row["tree_sha256"] == recorded.get(rel)
        rows.append(row)
    return rows


def _status(tree: Path, base: str, prune: set[str]) -> dict:
    """What ``git status --porcelain`` would list for ``tree`` against ``base``: modified, deleted and new files."""
    listed = _git("ls-tree", "-r", "-z", base)
    if listed.returncode != 0:
        raise SystemExit(f"git ls-tree {base} failed: {listed.stderr.decode('utf-8', 'replace')}")
    tracked = {}
    for record in listed.stdout.decode("utf-8").split("\0"):
        if record:
            meta, _, rel = record.partition("\t")
            mode, kind, blob = meta.split()
            tracked[rel] = (mode, kind, blob)
    modified, deleted, not_compared, lfs_same = [], [], [], []
    for rel, (mode, kind, blob) in sorted(tracked.items()):
        source = tree / rel
        if kind != "blob" or mode == "120000":
            not_compared.append(rel)
        elif not source.is_file():
            deleted.append(rel)
        elif _blob_id(source) != blob:
            if _lfs_oid(blob) == _sha256(source):
                lfs_same.append(rel)
            else:
                modified.append(rel)
    walked, self_ignored = [], []
    for folder, names, files in os.walk(tree):
        if _ignores_itself(Path(folder), files):
            self_ignored.append(Path(folder).relative_to(tree).as_posix())
            names[:] = []
            continue
        names[:] = sorted(name for name in names if name not in prune)
        for name in sorted(files):
            rel = (Path(folder) / name).relative_to(tree).as_posix()
            if rel not in tracked and name not in prune:
                walked.append(rel)
    ignored = set()
    if walked:
        checked = _git("check-ignore", "--no-index", "-z", "--stdin", data="\0".join(walked).encode("utf-8"))
        if checked.returncode not in (0, 1):
            raise SystemExit(f"git check-ignore failed: {checked.stderr.decode('utf-8', 'replace')}")
        ignored = {rel for rel in checked.stdout.decode("utf-8").split("\0") if rel}
    new = [rel for rel in walked if rel not in ignored]
    return {
        "base": base,
        "tracked_at_base": len(tracked),
        "modified": modified,
        "deleted": deleted,
        "new": new,
        "new_but_ignored": len(ignored),
        "lfs_files_equal_to_their_pointer": len(lfs_same),
        "self_ignoring_directories": self_ignored,
        "not_compared": not_compared,
        "pruned_directories": sorted(prune),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", type=Path, required=True, help="the tree to check (read as plain files)")
    parser.add_argument("--manifest", type=Path, required=True, help="a manifest.json whose files carry path, status and sha256")
    parser.add_argument("--sha-file", type=Path, help="a sha256sum-style file to compare with as well")
    parser.add_argument("--base", help="a commit in this checkout's object store: list what else in the tree differs from it")
    parser.add_argument("--prune", action="append", default=[], help="a directory name the walk skips (added to: %s)" % ", ".join(DEFAULT_PRUNE))
    parser.add_argument("--out", type=Path, help="the JSON report to write")
    args = parser.parse_args(argv)

    with open(args.manifest, encoding="utf-8") as fh:
        manifest = json.load(fh)
    rows = _hash_rows(args.tree, manifest, args.sha_file)
    bad = [row["path"] for row in rows if not row["matches_manifest"] or row.get("matches_sha_file") is False]
    result = {"tree": str(args.tree), "manifest": str(args.manifest), "files": rows, "hash_mismatches": bad}
    ok = not bad
    if args.base is not None:
        status = _status(args.tree, args.base, set(DEFAULT_PRUNE) | set(args.prune))
        expect_modified = sorted(entry["path"] for entry in manifest["files"] if entry.get("status") == "modified")
        expect_new = sorted(entry["path"] for entry in manifest["files"] if entry.get("status") == "added")
        status["modified_is_the_manifests"] = sorted(status["modified"]) == expect_modified
        status["new_is_the_manifests"] = sorted(status["new"]) == expect_new
        status["unexpected"] = sorted((set(status["modified"]) - set(expect_modified)) | (set(status["new"]) - set(expect_new)) | set(status["deleted"]))
        status["missing"] = sorted((set(expect_modified) - set(status["modified"])) | (set(expect_new) - set(status["new"])))
        result["status_against_base"] = status
        ok = ok and status["modified_is_the_manifests"] and status["new_is_the_manifests"] and not status["deleted"]
    result["ok"] = ok
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=1)
    for row in rows:
        print(f"{'ok      ' if row['matches_manifest'] and row.get('matches_sha_file') is not False else 'MISMATCH'} {str(row['tree_sha256'])[:12]} {row['path']}")
    if args.base is not None:
        status = result["status_against_base"]
        shown = ("base", "tracked_at_base", "modified_is_the_manifests", "new_is_the_manifests", "deleted", "unexpected", "missing", "new_but_ignored", "lfs_files_equal_to_their_pointer", "self_ignoring_directories")
        print(json.dumps({key: status[key] for key in shown}, indent=1))
    print(f"files {len(rows)}, hash mismatches {len(bad)}, ok {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
