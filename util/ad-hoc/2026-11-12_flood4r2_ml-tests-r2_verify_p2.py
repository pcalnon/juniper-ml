#!/usr/bin/env python3
"""
Verify the round-2 "ml-tests" carrier a stopped builder left, read-only, before a rebuild takes anything from it.

The predecessor tree is UNCOMMITTED, in another juniper-ml worktree where this session may not run the
version-control tool, and its builder was stopped mid-task. So its state is derived from its files alone, and from
this checkout's object store, which holds the predecessor's base commit:

  1. THE LAST RECORD. The predecessor wrote its files' sha256 values to two files; both are read, the later one
     (by modification time) is named, and the two must agree on every path they share. Every recorded path is
     hashed now and compared.
  2. THE CHANGE LIST. `status --porcelain` is emulated against the base commit: every tracked path's blob id is
     recomputed from the predecessor's file (a symlink hashed as its target; a path whose base blob is an LFS
     pointer compared by the pointer's oid), and every other file not ignored by this checkout's ignore rules is
     listed as untracked. The modified + untracked set must equal the recorded path list, with nothing deleted.
  3. THE MUTATION RUN. Every row of the predecessor's mutation_results.json must show its target restored
     (sha256 before == after). Each target's CURRENT bytes are then compared with what they must be: the base
     commit's blob for a file the carrier does not change, the last record's sha256 for one it does. A target
     whose mutation-time hash differs from the last record is reported with the two hashes (the predecessor's own
     log must explain it before anything is built on that file).

Usage (from this worktree's root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_verify_p2.py --predecessor <abs dir> --scratch <its abs
        deliverables dir> --base <sha> --out <json>

Exit 0 when every recorded hash matches, the change list equals the record and every mutation target is as it
must be; 1 otherwise.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, the finish of round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_verify_predecessor.py (the same check, of round 1's tree)
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}
LFS_SPEC = "version https://git-lfs.github.com/spec/v1"


def _git(*argv: str, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(["git", *argv], input=stdin, capture_output=True, text=True, check=False)


def _git_bytes(*argv: str) -> bytes:
    return subprocess.run(["git", *argv], capture_output=True, check=True).stdout


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _blob_id(path: Path, mode: str) -> str:
    data = os.readlink(path).encode() if mode == "120000" else path.read_bytes()
    return hashlib.sha1(b"blob %d\x00" % len(data) + data, usedforsecurity=False).hexdigest()


def _lfs_oid(blob_sha: str) -> str:
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
        raise SystemExit(f"ls-tree {base}: {out.stderr.strip()}")
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


def _mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--predecessor", required=True, type=Path)
    ap.add_argument("--scratch", required=True, type=Path)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    pred, scratch = args.predecessor, args.scratch

    with open(scratch / "manifest.json", encoding="utf-8") as fh:
        manifest = json.load(fh)
    with open(scratch / "copy_tree_final_bytes.json", encoding="utf-8") as fh:
        copy_record = json.load(fh)
    from_manifest = {row["path"]: row["sha256"] for row in manifest["files"]}
    from_copy = {row["path"]: row["here"] for row in copy_record["rows"]}
    records = {name: _mtime(scratch / name) for name in ("manifest.json", "copy_tree_final_bytes.json", "files_round2.json", "PROGRESS.txt")}
    last_record = max(("manifest.json", "copy_tree_final_bytes.json"), key=lambda name: (scratch / name).stat().st_mtime)
    records_disagree = sorted(path for path in set(from_manifest) | set(from_copy) if from_manifest.get(path) != from_copy.get(path))
    recorded = from_copy if last_record == "copy_tree_final_bytes.json" else from_manifest

    hashes = []
    for path, expected in sorted(recorded.items()):
        actual = _sha256(pred / path)
        hashes.append({"path": path, "recorded": expected, "actual": actual, "match": actual == expected, "file_mtime": _mtime(pred / path) if (pred / path).is_file() else None})
    newer_than_record = [row["path"] for row in hashes if row["file_mtime"] and row["file_mtime"] > records[last_record]]

    tree = _base_tree(args.base)
    modified, deleted, lfs_same = [], [], 0
    for path, (mode, sha) in sorted(tree.items()):
        target = pred / path
        if not (target.is_file() or target.is_symlink()):
            deleted.append(path)
        elif _blob_id(target, mode) != sha:
            oid = _lfs_oid(sha)
            if oid and _sha256(target) == oid:
                lfs_same += 1
            else:
                modified.append(path)
    others = sorted(p for p in _walk(pred) if p not in tree and p != ".git")
    ignored = set(_git("check-ignore", "--stdin", stdin="\n".join(others) + "\n").stdout.splitlines()) if others else set()
    untracked = [p for p in others if p not in ignored]
    changed = sorted(set(modified) | set(untracked) | set(deleted))

    with open(scratch / "mutation" / "mutation_results.json", encoding="utf-8") as fh:
        mutation_rows = json.load(fh)
    unrestored = [f"row {i}: {row['target']}" for i, row in enumerate(mutation_rows) if not row.get("mutant_restored") or row.get("mutant_sha256_before") != row.get("mutant_sha256_after")]
    unrestored += [f"row {i} control: {row['target']}" for i, row in enumerate(mutation_rows) if "control_restored" in row and (not row["control_restored"] or row.get("control_sha256_before") != row.get("control_sha256_after"))]
    targets = {}
    for row in mutation_rows:
        targets.setdefault(row["target"], set()).add(row["mutant_sha256_before"])
    target_rows = []
    for target, at_mutation in sorted(targets.items()):
        now = _sha256(pred / target)
        if target in recorded:
            must_be, rule = recorded[target], f"the last record ({last_record})"
        else:
            must_be, rule = hashlib.sha256(_git_bytes("show", f"{args.base}:{target}")).hexdigest(), f"the base commit's blob ({args.base[:8]})"
        target_rows.append(
            {
                "target": target,
                "sha256_at_mutation_time": sorted(at_mutation),
                "sha256_now": now,
                "must_be": must_be,
                "rule": rule,
                "now_is_as_it_must_be": now == must_be,
                "mutation_time_hash_equals_must_be": sorted(at_mutation) == [must_be],
            }
        )
    targets_wrong = [row["target"] for row in target_rows if not row["now_is_as_it_must_be"]]
    targets_changed_after_mutation = [row["target"] for row in target_rows if not row["mutation_time_hash_equals_must_be"]]

    report = {
        "predecessor": str(pred),
        "base": args.base,
        "records": records,
        "last_record": last_record,
        "records_disagree_on": records_disagree,
        "recorded_paths": len(recorded),
        "hash_matches": sum(1 for row in hashes if row["match"]),
        "hash_mismatches": [row for row in hashes if not row["match"]],
        "files_with_a_modification_time_after_the_last_record": newer_than_record,
        "emulated_status": {"modified": modified, "deleted": deleted, "untracked": untracked, "lfs_pointer_paths_whose_smudged_file_matches": lfs_same},
        "changed_not_in_the_record": [p for p in changed if p not in recorded],
        "recorded_but_unchanged": [p for p in sorted(recorded) if p not in changed],
        "mutation": {"rows": len(mutation_rows), "not_restored": unrestored, "targets": target_rows, "targets_not_as_they_must_be": targets_wrong, "targets_whose_bytes_changed_after_the_mutation_run": targets_changed_after_mutation},
        "hashes": hashes,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    ok = not (report["hash_mismatches"] or records_disagree or report["changed_not_in_the_record"] or report["recorded_but_unchanged"] or deleted or unrestored or targets_wrong)
    print(f"records: {records}; the last is {last_record}; they disagree on: {records_disagree or 'nothing'}")
    print(f"recorded paths: {len(recorded)}; sha256 matches: {report['hash_matches']}; mismatches: {[row['path'] for row in report['hash_mismatches']] or 'none'}")
    print(f"files modified after the last record: {newer_than_record or 'none'}")
    print(f"emulated status vs {args.base[:8]}: modified {len(modified)}, deleted {len(deleted)}, untracked (not ignored) {len(untracked)}; {lfs_same} LFS paths match their pointer's oid")
    print(f"changed but not in the record: {report['changed_not_in_the_record'] or 'none'}; recorded but unchanged: {report['recorded_but_unchanged'] or 'none'}")
    print(f"mutation rows: {len(mutation_rows)}; not restored: {unrestored or 'none'}; targets not as they must be now: {targets_wrong or 'none'}")
    print(f"targets whose bytes changed between the mutation run and the last record: {targets_changed_after_mutation or 'none'}")
    print("VERDICT:", "the predecessor matches its last record" if ok else "DIFFERENCE -- do not build on it until explained")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
