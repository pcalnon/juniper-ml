"""
Assemble the validator's test tree for the ruling-17 canopy lockfile-print carrier: three-way each carrier file onto current main.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: Cursor flood-4 disposition, Overtoad ruling 17 ("canopy: dead error path"), session-5 validation

For every file the carrier worktree changed against its base, this reports whether main changed the
same file since the base, and writes the validator copy: a plain copy when main did not move the
file, otherwise `git merge-file -p <carrier> <base> <main>`. It never writes to the carrier worktree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=check)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--carrier", required=True, type=Path, help="carrier worktree (read-only)")
    parser.add_argument("--copy", required=True, type=Path, help="validator worktree (written)")
    parser.add_argument("--base", required=True, help="carrier base sha")
    parser.add_argument("--main", required=True, help="current main sha (the copy's HEAD)")
    parser.add_argument("--scratch", required=True, type=Path, help="scratch dir for merge inputs and the report")
    args = parser.parse_args()

    status = _git(args.carrier, "status", "--porcelain=v1", "-uall").stdout.decode()
    changed: list[tuple[str, str]] = []
    for line in status.splitlines():
        code, path = line[:2], line[3:]
        if path.startswith("tmp/"):
            continue
        changed.append((code, path))

    main_changed = set(_git(args.carrier, "diff", "--name-only", args.base, args.main).stdout.decode().split("\n"))
    main_changed.discard("")

    head = _git(args.copy, "rev-parse", "HEAD").stdout.decode().strip()
    if not head.startswith(args.main):
        print(f"copy HEAD {head} is not {args.main}", file=sys.stderr)
        return 2

    report: dict[str, object] = {"base": args.base, "main": args.main, "copy_head": head, "main_changed_files": sorted(main_changed), "files": []}
    merge_dir = args.scratch / "assemble"
    merge_dir.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, object]] = []
    for code, path in changed:
        carrier_bytes = (args.carrier / path).read_bytes()
        entry: dict[str, object] = {"path": path, "status": code, "carrier_sha256": _sha256(carrier_bytes), "main_changed": path in main_changed}
        base_blob = _git(args.carrier, "rev-parse", f"{args.base}:{path}", check=False)
        main_blob = _git(args.carrier, "rev-parse", f"{args.main}:{path}", check=False)
        entry["base_blob"] = base_blob.stdout.decode().strip() if base_blob.returncode == 0 else None
        entry["main_blob"] = main_blob.stdout.decode().strip() if main_blob.returncode == 0 else None
        target = args.copy / path
        if entry["base_blob"] == entry["main_blob"]:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(carrier_bytes)
            entry["method"] = "copy (base blob == main blob)"
        else:
            flat = path.replace("/", "__")
            base_file = merge_dir / f"{flat}.base"
            main_file = merge_dir / f"{flat}.main"
            base_file.write_bytes(_git(args.carrier, "show", f"{args.base}:{path}").stdout)
            main_file.write_bytes(_git(args.carrier, "show", f"{args.main}:{path}").stdout)
            merged = subprocess.run(["git", "merge-file", "-p", str(args.carrier / path), str(base_file), str(main_file)], capture_output=True, check=False)
            entry["method"] = f"git merge-file -p (exit {merged.returncode}: conflicts)" if merged.returncode else "git merge-file -p (clean)"
            target.write_bytes(merged.stdout)
        entry["copy_sha256"] = _sha256(target.read_bytes())
        files.append(entry)
    report["files"] = files
    out = args.scratch / "assemble_report.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
