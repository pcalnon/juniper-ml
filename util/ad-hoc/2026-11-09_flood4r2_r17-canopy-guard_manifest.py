"""
Assemble manifest.json for the ruling-17 canopy carrier from the build worktree, the census runs and a facts file.

Builder helper for the owner's ruling 17 ("canopy: tests hit :8050"). Reads the build worktree's uncommitted
changes (``git status --porcelain``, untracked files included) and hashes each file; summarises every merged
census JSON it is given (per-port connect and test counts, outcomes, failures); and merges a hand-kept facts
file holding the checks run, the mutations and the open questions, so the manifest restates only what a
command recorded.

Usage:
  python3 <this file> --wt <canopy build worktree> --base <sha> --facts <facts.json> --out <manifest.json>
      --census <tag>=<merged census json> ...

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 (flood-4 session 4), juniper-canopy unit-lane network guard
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - read-only git status in the build worktree
import sys
from pathlib import Path

STATUS = {"??": "added", "A": "added", "M": "modified", "D": "deleted"}


def _changed_files(wt: Path) -> list[dict]:
    output = subprocess.run(["git", "-C", str(wt), "status", "--porcelain", "--untracked-files=all"], check=True, capture_output=True, text=True).stdout  # nosec B603 B607 - fixed argv
    files = []
    for line in output.splitlines():
        code, path = line[:2].strip(), line[3:]
        entry = {"path": path, "status": STATUS.get(code, code)}
        target = wt / path
        if target.is_file():
            entry["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        files.append(entry)
    return sorted(files, key=lambda item: item["path"])


def _summary(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        record = json.load(fh)
    return {
        "file": str(path),
        "group_exits": record.get("groups"),
        "collected": record.get("collected"),
        "injected": record.get("injected"),
        "outcomes": record.get("outcomes"),
        "failed": record.get("failed"),
        "by_port": {port: {"connects": entry["connects"], "n_tests": entry["n_tests"], "verdicts": entry["verdicts"], "hosts": entry["hosts"]} for port, entry in record.get("by_port", {}).items()},
        "imported_outside_wt": record.get("imported_outside_wt"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--wt", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--facts", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--census", nargs="*", default=[])
    args = parser.parse_args()

    with open(args.facts, encoding="utf-8") as fh:
        facts = json.load(fh)
    census = {}
    for spec in args.census:
        tag, _, path = spec.partition("=")
        census[tag] = _summary(Path(path))
    manifest = {
        "repo": "pcalnon/juniper-canopy",
        "carrier": "r17-canopy-network-guard",
        "base_sha": args.base,
        "worktree": str(args.wt),
        "files": _changed_files(args.wt),
        "census": {**facts.get("census", {}), "runs": census},
        "checks": facts.get("checks", []),
        "mutations": facts.get("mutations", []),
        "open_questions": facts.get("open_questions", []),
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print(f"[r17-manifest] files={len(manifest['files'])} census_runs={sorted(census)} checks={len(manifest['checks'])} mutations={len(manifest['mutations'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
