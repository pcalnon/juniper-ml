"""
Snapshot an uncommitted carrier tree, then rebuild it on a newer main: three-way for each file main changed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round 2 of the Overtoad's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt)

Usage:
    python3 <this file> --worktree <carrier worktree> --new-base <sha> --out <dir> [--apply]

The carrier is the worktree's uncommitted change set (tracked files modified in the working tree, plus untracked
files); anything staged, deleted or renamed is refused. For every carrier file the script saves three copies under
<dir>/{carrier,base,main}/ (base = the worktree's HEAD, main = --new-base) and a result under <dir>/merged/:

  * main did not change the file since base  -> the carrier's copy, unchanged;
  * main changed it                          -> `git merge-file -p <carrier> <base> <main>` (exit 0 = clean).

Without --apply nothing in the worktree changes (a snapshot plus a predicted rebuild). With --apply, and only when
every merge is clean: each file main changed is put back to its base content, the branch is fast-forwarded to
--new-base (so every file the carrier does not touch becomes main's), and the merged results are written into the
worktree. It then checks that HEAD is --new-base, that the change set names the same files, and that every carrier
file's sha256 equals its merged copy. <dir>/rebuild.json records every sha256 and exit code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Repo:
    """Plain git calls against one worktree."""

    def __init__(self, worktree: Path) -> None:
        self.worktree = worktree

    def run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        proc = subprocess.run(["git", "-C", str(self.worktree), *args], capture_output=True)  # nosec B603 B607 - fixed argv
        if check and proc.returncode != 0:
            raise SystemExit(f"[rebuild] git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.decode(errors='replace')[-600:]}")
        return proc

    def head(self) -> str:
        return self.run("rev-parse", "HEAD").stdout.decode().strip()

    def blob(self, rev: str, path: str) -> bytes | None:
        """The file's bytes at ``rev``, or None when ``rev`` has no such path."""
        if self.run("cat-file", "-e", f"{rev}:{path}", check=False).returncode != 0:
            return None
        return self.run("show", f"{rev}:{path}").stdout

    def change_set(self) -> dict[str, str]:
        """Repo-relative path -> "modified" | "added" for the uncommitted change set; anything else is refused."""
        entries = [entry for entry in self.run("status", "--porcelain=v1", "--untracked-files=all", "-z").stdout.decode().split("\0") if entry]
        result: dict[str, str] = {}
        for entry in entries:
            code, path = entry[:2], entry[3:]
            if code == " M":
                result[path] = "modified"
            elif code == "??":
                result[path] = "added"
            else:
                raise SystemExit(f"[rebuild] refusing status {code!r} for {path}: the carrier must be unstaged modifications and untracked files only")
        return result


def save(root: Path, kind: str, path: str, data: bytes | None) -> Path | None:
    if data is None:
        return None
    target = root / kind / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def plan(repo: Repo, new_base: str, out: Path) -> dict:
    old_base = repo.head()
    files = []
    for path, status in sorted(repo.change_set().items()):
        carrier = (repo.worktree / path).read_bytes()
        base = repo.blob(old_base, path)
        main = repo.blob(new_base, path)
        carrier_copy = save(out, "carrier", path, carrier)
        base_copy = save(out, "base", path, base)
        main_copy = save(out, "main", path, main)
        record = {"path": path, "status": status, "carrier_sha256": sha256(carrier), "base_sha256": sha256(base) if base is not None else None, "main_sha256": sha256(main) if main is not None else None}
        if base is None and main is None:
            merged, record["how"], record["merge_exit"] = carrier, "new file; absent on main", None
        elif base is None or main is None:
            raise SystemExit(f"[rebuild] {path}: present on only one of base and main (base={base is not None}, main={main is not None}); resolve by hand")
        elif base == main:
            merged, record["how"], record["merge_exit"] = carrier, "main did not change it; carrier copy kept", None
        else:
            proc = subprocess.run(["git", "merge-file", "-p", "-L", "carrier", "-L", "base", "-L", "main", str(carrier_copy), str(base_copy), str(main_copy)], capture_output=True)  # nosec B603 B607 - fixed argv
            merged, record["how"], record["merge_exit"] = proc.stdout, "git merge-file -p <carrier> <base> <main>", proc.returncode
        save(out, "merged", path, merged)
        record["merged_sha256"] = sha256(merged)
        files.append(record)
    return {"worktree": str(repo.worktree), "old_base": old_base, "new_base": repo.run("rev-parse", new_base).stdout.decode().strip(), "files": files, "applied": False}


def apply(repo: Repo, record: dict, out: Path) -> None:
    unclean = [entry["path"] for entry in record["files"] if entry["merge_exit"] not in (None, 0)]
    if unclean:
        raise SystemExit(f"[rebuild] not applying: merge-file reported conflicts or an error for {unclean}")
    three_way = [entry["path"] for entry in record["files"] if entry["merge_exit"] == 0]
    before = repo.change_set()
    for path in three_way:
        repo.run("checkout", "--", path)
    repo.run("merge", "--ff-only", record["new_base"])
    for path in three_way:
        (repo.worktree / path).write_bytes((out / "merged" / path).read_bytes())
    after = repo.change_set()
    record["applied"] = True
    record["head_after"] = repo.head()
    record["change_set_same_files"] = sorted(before) == sorted(after)
    record["worktree_matches_merged"] = {entry["path"]: sha256((repo.worktree / entry["path"]).read_bytes()) == entry["merged_sha256"] for entry in record["files"]}
    if record["head_after"] != record["new_base"] or not record["change_set_same_files"] or not all(record["worktree_matches_merged"].values()):
        raise SystemExit(f"[rebuild] post-apply check FAILED: {json.dumps({k: record[k] for k in ('head_after', 'new_base', 'change_set_same_files', 'worktree_matches_merged')}, indent=1)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Snapshot a carrier tree and rebuild it on a newer main.")
    parser.add_argument("--worktree", required=True, type=Path)
    parser.add_argument("--new-base", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    repo = Repo(args.worktree.resolve())
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    record = plan(repo, args.new_base, out)
    if args.apply:
        apply(repo, record, out)
    (out / "rebuild.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    for entry in record["files"]:
        print(f"[rebuild] {entry['status']:8} {entry['path']}: {entry['how']}" + (f" (exit {entry['merge_exit']})" if entry["merge_exit"] is not None else ""))
    print(f"[rebuild] old base {record['old_base']} -> new base {record['new_base']}; applied={record['applied']}; files={len(record['files'])}; record {out / 'rebuild.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
