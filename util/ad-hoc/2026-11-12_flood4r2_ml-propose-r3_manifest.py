#!/usr/bin/env python3
"""
Write round 3's manifest.json for the ml-propose carrier: the changed files with sha256, plus the recorded evidence.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (round 3 of the ml-propose carrier, flood-4 session 5)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
The manifest is the builder's checkpoint: it is written early and rewritten at every milestone, so it must be
cheap to regenerate and must never disagree with the tree. The file list comes from `git status --porcelain`
in this worktree (the carrier is uncommitted on its base), each file's sha256 from the bytes on disk, and the
mutation rows from the mutation run's own JSON. Everything a person wrote (the checks, the open questions, what
changed this round) is read from JSON files in the scratch directory and copied in unchanged.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3_manifest.py --scratch tmp/flood4r2/ml-propose/r3
                                                                   --status in-progress|final
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed argv: read-only git plumbing in this script's own worktree
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS = {"M": "modified", "A": "added", "??": "added", "D": "deleted"}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout  # nosec B603 B607


def changed_files() -> list:
    rows = []
    for line in git("status", "--porcelain", "--untracked-files=all").splitlines():
        code, path = line[:2].strip(), line[3:]
        status = STATUS.get(code)
        if status is None:
            raise SystemExit(f"unexpected git status line: {line!r}")
        entry = {"path": path, "status": status}
        if status != "deleted":
            entry["sha256"] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        rows.append(entry)
    return sorted(rows, key=lambda row: row["path"])


def optional(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def mutation_rows(scratch: Path) -> list:
    results = optional(scratch / "mut" / "mutation_results.json", {})
    rows = []
    for row in results.get("mutants", []):
        entry = {
            "test_file": "tests/test_release_train_propose.py",
            "mutant": f"util/release_train/propose.py ({row['group']} {row['id']}, {row['what']}): `{row['old'].strip()}` -> `{row['new'].strip()}`",
            "result": row["result"],
            "run_against": row.get("run_against"),
            "killed_by": row.get("failing_tests"),
            "log": f"tmp/flood4r2/ml-propose/r3/mut/mut_{row['group']}_{row['id']}.log",
        }
        if "expected_survivor" in row:
            entry["why_it_survives"] = row["expected_survivor"]
        rows.append(entry)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--status", required=True, choices=("in-progress", "final"))
    args = parser.parse_args()
    scratch = args.scratch if args.scratch.is_absolute() else ROOT / args.scratch
    notes = optional(scratch / "manifest_input.json", {})
    manifest = {
        "repo": "juniper-ml",
        "carrier": "ml-propose",
        "round": 3,
        "status": args.status,
        "base_sha": git("rev-parse", "HEAD").strip(),
        "worktree": str(ROOT),
        "files": changed_files(),
        "carried": notes.get("carried", []),
        "what_changed_this_round": notes.get("what_changed_this_round", []),
        "done": notes.get("done", []),
        "remains": notes.get("remains", []),
        "checks": optional(scratch / "checks.json", []),
        "mutations": mutation_rows(scratch),
        "mutation_summary": optional(scratch / "mut" / "mutation_results.json", {}).get("summary"),
        "open_questions": optional(scratch / "open_questions.json", []),
        "stamps": "tmp/flood4r2/ml-propose/r3/stamps.json",
        "dispositions": "tmp/flood4r2/ml-propose/r3/dispositions.json",
        "scratch_outside_the_worktree": notes.get("scratch_outside_the_worktree", []),
    }
    (scratch / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"manifest.json: status={args.status} base={manifest['base_sha'][:8]} files={len(manifest['files'])} checks={len(manifest['checks'])} mutations={len(manifest['mutations'])} open_questions={len(manifest['open_questions'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
