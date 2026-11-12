#!/usr/bin/env python3
"""
Rebuild the N-4 round-2 carrier on a newer main: save the uncommitted files, then put them back three-way.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (main moved under the carrier: juniper-ml#2360 merged while it was being built)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (section 8, ruling 11)

Two steps, with ``git reset --hard origin/main`` run by hand between them (in this worktree only)::

    python3 <this file> save  --tree <worktree root> --saved <dir>
    python3 <this file> apply --tree <worktree root> --saved <dir> --onto <rev> [--write]

``save`` copies every file ``git status --porcelain --untracked-files=all`` reports (ignored paths such as ``tmp/``
never appear) into ``<saved>/files/`` at its repository path, and records the base (``HEAD``) and each sha256 in
``<saved>/saved.json``. It refuses when ``<saved>/saved.json`` already exists.

``apply`` puts each saved file back. Where ``<base>:<path>`` and ``<onto>:<path>`` are the same blob (or the path is in
neither), main did not touch the file and the saved copy is used. Where they differ, the file is rebuilt with
``git merge-file -p <saved copy> <base's copy> <onto's copy>``; a conflict, or a file added or deleted on one side
only, is a problem and nothing is written for it. Results go to ``<saved>/merged/`` and the report to
``<saved>/apply-report.json`` (``apply.json`` with ``--write``); only ``--write`` copies them into the tree, and it
refuses unless the tree's ``HEAD`` is ``<onto>``. Exit status 1 on any problem.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _git(tree: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=tree, capture_output=True, check=False)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _blob(tree: Path, rev: str, path: str) -> bytes | None:
    done = _git(tree, "show", f"{rev}:{path}")
    return done.stdout if done.returncode == 0 else None


def save(tree: Path, saved: Path) -> int:
    record_path = saved / "saved.json"
    if record_path.exists():
        print(f"refusing: {record_path} exists")
        return 1
    files = []
    for line in _git(tree, "status", "--porcelain", "--untracked-files=all").stdout.decode().splitlines():
        code, rel = line[:2].strip(), line[3:]
        source = tree / rel
        if not source.is_file():
            print(f"refusing: {rel} ({code}) is not a file")
            return 1
        target = saved / "files" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        files.append({"path": rel, "status": code, "sha256": _sha256(target.read_bytes())})
    record = {"base_sha": _git(tree, "rev-parse", "HEAD").stdout.decode().strip(), "files": sorted(files, key=lambda entry: entry["path"])}
    record_path.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"saved {len(files)} file(s) from base {record['base_sha']}")
    return 0


def apply(tree: Path, saved: Path, onto: str, write: bool) -> int:
    record = json.loads((saved / "saved.json").read_text(encoding="utf-8"))
    base = record["base_sha"]
    onto_sha = _git(tree, "rev-parse", onto).stdout.decode().strip()
    head_sha = _git(tree, "rev-parse", "HEAD").stdout.decode().strip()
    problems = []
    if write and head_sha != onto_sha:
        problems.append(f"--write refused: HEAD {head_sha} is not {onto} ({onto_sha})")
    merged_dir = saved / "merged"
    rows = []
    for entry in record["files"]:
        rel = entry["path"]
        mine = (saved / "files" / rel).read_bytes()
        row = {"path": rel, "saved_sha256": _sha256(mine), "saved_matches_record": _sha256(mine) == entry["sha256"]}
        if not row["saved_matches_record"]:
            problems.append(f"{rel}: the saved copy changed since it was saved")
        base_blob, onto_blob = _blob(tree, base, rel), _blob(tree, onto_sha, rel)
        if base_blob == onto_blob:
            row["how"] = "saved copy (main did not touch it)"
            result = mine
        elif base_blob is None or onto_blob is None:
            row["how"] = "REFUSED: added or deleted on one side only"
            problems.append(f"{rel}: {row['how']}")
            rows.append(row)
            continue
        else:
            work = saved / "threeway" / rel.replace("/", "__")
            work.parent.mkdir(parents=True, exist_ok=True)
            names = {}
            for label, data in (("mine", mine), ("base", base_blob), ("main", onto_blob)):
                names[label] = Path(f"{work}.{label}")
                names[label].write_bytes(data)
            done = _git(tree, "merge-file", "-p", str(names["mine"]), str(names["base"]), str(names["main"]))
            row["how"] = "three-way: git merge-file -p <saved> <base> <main>"
            row["merge_file_exit"] = done.returncode
            result = done.stdout
            if done.returncode != 0:
                problems.append(f"{rel}: merge-file exit {done.returncode} (conflicts)")
        row["result_sha256"] = _sha256(result)
        row["result_is_saved_copy"] = result == mine
        target = merged_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result)
        rows.append(row)
    wrote = write and not problems
    if wrote:
        for row in rows:
            destination = tree / row["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(merged_dir / row["path"], destination)
    report = {"base_sha": base, "onto": onto, "onto_sha": onto_sha, "head_sha": head_sha, "wrote": wrote, "files": rows, "problems": problems}
    (saved / ("apply.json" if write else "apply-report.json")).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        print(f"{row['how']:<52} {row['path']}")
    print(f"base {base[:8]} -> {onto} {onto_sha[:8]}; wrote: {wrote}; problems: {problems}")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("save", "apply"):
        one = sub.add_parser(name)
        one.add_argument("--tree", required=True, type=Path)
        one.add_argument("--saved", required=True, type=Path)
        if name == "apply":
            one.add_argument("--onto", required=True)
            one.add_argument("--write", action="store_true")
    args = parser.parse_args()
    tree, saved = args.tree.resolve(), args.saved.resolve()
    if args.mode == "save":
        return save(tree, saved)
    return apply(tree, saved, args.onto, args.write)


if __name__ == "__main__":
    sys.exit(main())
