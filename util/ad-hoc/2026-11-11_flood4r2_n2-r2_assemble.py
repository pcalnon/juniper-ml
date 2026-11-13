#!/usr/bin/env python3
"""Bring an earlier build of the N-2 carrier (an uncommitted tree on an older base) onto this worktree's HEAD.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use build step)
Author:      Paul Calnon
Version:     0.2.0
License:     MIT License
Created:     2026-11-11
Status:      ad-hoc -- one-off (round 2 of the N-2 carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
             (juniper-service-core's stop-then-start race); the carrier's manifest.json

Used twice: to bring the round-1 carrier (another worktree, base f85fbc8b) onto 9063ebf3, and to
bring this worktree's own round-2 files, snapshotted with ``--snapshot-to``, onto a newer ``main``.

For every file the carrier's manifest lists:

- the carrier's copy is checked against the manifest's sha256 (a mismatch is fatal: the carrier
  moved after its manifest was written);
- this worktree's copy must still be HEAD's (an added file must be absent), so a second run cannot
  overwrite later edits; ``--force`` skips that refusal (the worktree's copy is then ignored: a
  rebuilt file is merged from HEAD's blob, never from the worktree's copy);
- a file ``main`` did NOT change since the carrier's base is copied in;
- a file ``main`` DID change since the base is rebuilt with
  ``git merge-file -p <carrier's copy> <base's copy> <main's copy>`` (never the carrier's copy over
  main's). A conflict is fatal and the worktree's file is left alone; the conflicted output is
  kept beside the three inputs for a resolution by hand. The inputs and the result are kept under
  ``--scratch``/threeway/ and the result's diff against main's copy is summarised (inserted and
  deleted line counts).

``--snapshot-to <dir> <path> ...`` does the other half: it copies the named files of this worktree
into ``<dir>`` and writes ``<dir>/manifest.json`` (HEAD as the base, each file's status against
HEAD, each sha256), which a later run takes as ``--carrier <dir> --manifest <dir>/manifest.json``.

It writes only inside this worktree and the directories named. It reads the carrier tree as plain
files and never runs git there. Output: one JSON document (``--out``) naming the HEAD used and each
file's action.

Exit status: 0 when every file was placed (or snapshotted), 1 when a file was refused or
conflicted, 2 on a usage error.

Usage (from this worktree's root):
    python3 util/ad-hoc/2026-11-11_flood4r2_n2-r2_assemble.py --carrier <carrier tree> [--manifest <file>] \\
        --scratch <scratch dir> --out <scratch dir>/assemble.json [--force]
    python3 util/ad-hoc/2026-11-11_flood4r2_n2-r2_assemble.py --snapshot-to <dir> <path> [<path> ...]
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, check=False)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _blob(ref: str, rel: str) -> bytes | None:
    """The file's bytes at ``ref``, or None when the path does not exist there."""
    shown = _git("show", f"{ref}:{rel}")
    return shown.stdout if shown.returncode == 0 else None


def _line_delta(old: bytes, new: bytes) -> dict[str, int]:
    inserted = deleted = 0
    matcher = difflib.SequenceMatcher(a=old.decode("utf-8").splitlines(), b=new.decode("utf-8").splitlines(), autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            deleted += i2 - i1
        if tag in ("replace", "insert"):
            inserted += j2 - j1
    return {"inserted_lines": inserted, "deleted_lines": deleted}


def _place(entry: dict, carrier: Path, base: str, changed: set[str], threeway_dir: Path, force: bool) -> dict:
    rel = entry["path"]
    src = carrier / rel
    dest = REPO_ROOT / rel
    carrier_bytes = src.read_bytes()
    row = {"path": rel, "status": entry["status"], "manifest_sha256": entry["sha256"], "carrier_sha256": _sha256_bytes(carrier_bytes)}
    if row["carrier_sha256"] != entry["sha256"]:
        row["error"] = "the carrier's copy does not match the manifest's sha256"
        return row
    head_bytes = _blob("HEAD", rel)
    worktree_bytes = dest.read_bytes() if dest.is_file() else None
    if worktree_bytes != head_bytes and not force:
        row["error"] = "this worktree's copy is not HEAD's (already assembled or edited); pass --force to overwrite"
        return row
    if entry["status"] == "added":
        if head_bytes is not None:
            row["error"] = "the manifest says added, but HEAD already has this path"
            return row
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        row["action"] = "copied (added; HEAD does not have it)"
    elif rel in changed:
        base_bytes = _blob(base, rel)
        if base_bytes is None or head_bytes is None:
            row["error"] = "main changed this path since the base, but one side does not have it"
            return row
        work = threeway_dir / rel.replace("/", "__")
        work.mkdir(parents=True, exist_ok=True)
        (work / "carrier").write_bytes(carrier_bytes)
        (work / "base").write_bytes(base_bytes)
        (work / "main").write_bytes(head_bytes)
        merged = _git("merge-file", "-p", str(work / "carrier"), str(work / "base"), str(work / "main"))
        row["action"] = "three-way (git merge-file -p carrier base main)"
        row["merge_exit"] = merged.returncode
        if merged.returncode != 0:
            (work / "merged_with_conflicts").write_bytes(merged.stdout)
            row["error"] = f"merge-file exited {merged.returncode} (a positive status is the number of conflicts); the conflicted output is in {work / 'merged_with_conflicts'}"
            return row
        (work / "merged").write_bytes(merged.stdout)
        dest.write_bytes(merged.stdout)
        row["main_sha256"] = _sha256_bytes(head_bytes)
        row["base_sha256"] = _sha256_bytes(base_bytes)
        row["merged_vs_main"] = _line_delta(head_bytes, merged.stdout)
        row["carrier_vs_base"] = _line_delta(base_bytes, carrier_bytes)
        row["threeway_inputs"] = str(work)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        row["action"] = "copied (main did not change it since the base)"
    row["assembled_sha256"] = _sha256_bytes(dest.read_bytes())
    return row


def _snapshot(dest_root: Path, paths: list[str]) -> int:
    """Copy this worktree's ``paths`` into ``dest_root`` and write its manifest (HEAD as the base)."""
    head = _git("rev-parse", "HEAD").stdout.decode().strip()
    files = []
    for rel in paths:
        source = REPO_ROOT / rel
        if not source.is_file():
            print(f"not a file in this worktree: {rel}", file=sys.stderr)
            return 2
        target = dest_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        files.append({"path": rel, "status": "added" if _blob("HEAD", rel) is None else "modified", "sha256": _sha256_bytes(target.read_bytes())})
    with open(dest_root / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump({"base_sha": head, "files": files}, fh, indent=1)
    print(json.dumps({"base_sha": head, "files": len(files), "modified": sum(1 for entry in files if entry["status"] == "modified"), "added": sum(1 for entry in files if entry["status"] == "added")}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--carrier", type=Path, help="the carrier tree to bring in (read as plain files)")
    parser.add_argument("--manifest", type=Path, help="the carrier's manifest.json (default: tmp/flood4-fix/n2/manifest.json under the carrier)")
    parser.add_argument("--scratch", type=Path, help="a scratch directory in this worktree's tmp/")
    parser.add_argument("--out", type=Path, help="the JSON report to write")
    parser.add_argument("--force", action="store_true", help="overwrite a worktree copy that is no longer HEAD's")
    parser.add_argument("--snapshot-to", type=Path, help="instead: copy the named paths of this worktree into this directory, with a manifest")
    parser.add_argument("paths", nargs="*", help="with --snapshot-to: the repository-relative files to snapshot")
    args = parser.parse_args(argv)

    if args.snapshot_to is not None:
        if not args.paths:
            parser.error("--snapshot-to needs at least one path")
        return _snapshot(args.snapshot_to, args.paths)
    if args.carrier is None or args.scratch is None or args.out is None or args.paths:
        parser.error("--carrier, --scratch and --out are required (and no paths) unless --snapshot-to is given")
    manifest_path = args.manifest if args.manifest is not None else args.carrier / "tmp" / "flood4-fix" / "n2" / "manifest.json"
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    base = manifest["base_sha"]
    head = _git("rev-parse", "HEAD").stdout.decode().strip()
    origin_main = _git("rev-parse", "origin/main").stdout.decode().strip()
    changed = set(_git("diff", "--name-only", base, "HEAD").stdout.decode().split())
    threeway_dir = args.scratch / "threeway"
    rows = [_place(entry, args.carrier, base, changed, threeway_dir, args.force) for entry in manifest["files"]]
    failed = [row["path"] for row in rows if "error" in row]
    result = {
        "head": head,
        "origin_main": origin_main,
        "head_is_origin_main": head == origin_main,
        "carrier": str(args.carrier),
        "carrier_base": base,
        "main_changed_since_base": sorted(changed & {entry["path"] for entry in manifest["files"]}),
        "files": rows,
        "failed": failed,
        "ok": not failed,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    print(json.dumps({key: result[key] for key in ("head", "head_is_origin_main", "main_changed_since_base", "failed", "ok")}, indent=1))
    for row in rows:
        print(f"{row['path']}\t{row.get('action', 'REFUSED: ' + row.get('error', ''))}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
