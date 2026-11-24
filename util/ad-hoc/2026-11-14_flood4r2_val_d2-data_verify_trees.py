#!/usr/bin/env python3
"""
Verify, read-only, the carrier and the two validator worktrees of juniper-data's "run the unrun tests" carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (Cursor flood-4 session 8: finishing the d2-unrun-tests validation after VF was cut off)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session8/BRIEF_S8_ADDENDUM.txt ("a killed validator can leave a MUTANT in its own worktrees"),
         util/ad-hoc/2026-11-12_flood4r2_val_d2-data_mutants.py (the eight files its mutants touch)

Nothing is written into any tree. Checks:
  C  : every file of CD/sha256_final.txt re-hashed; `status --porcelain` names exactly the manifest's 16 paths.
  V0 : the same 14 hashes (the carrier's copies laid over its base); the two deleted paths are absent.
  V1 : every path of landing/V1_landed.json carries the sha256 recorded there (a delete is absent).
  V0, V1 : the eight product files a mutant may touch carry the sha256 VF logged BEFORE its mutation run
       (PROGRESS.txt, 2026-11-13T03:25:21Z), and `status --porcelain` names no path outside the 16.

Usage: 2026-11-14_flood4r2_val_d2-data_verify_trees.py --out <json> [--v1-landed <json>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

WORKTREES = Path.home() / "Development" / "python" / "Juniper" / "worktrees"
CARRIER = WORKTREES / "juniper-data--test--run-the-unrun-tests--20261112-1815--c68e6b4c"
DELIVERABLES = CARRIER / "tmp" / "flood4-fix" / "d2-unrun-tests"
V0 = WORKTREES / "juniper-data--val--flood4r2-d2-unrun-tests-base--20261112-2110--c68e6b4c"
V1 = WORKTREES / "juniper-data--val--flood4r2-d2-unrun-tests--20261112-2110--3cf8867c"
SCRATCH = Path(__file__).resolve().parents[2] / "tmp" / "flood4r2-val" / "d2-unrun-tests-s7"

DELETED = ("juniper_data/tests/api/__init__.py", "juniper_data/tests/api/test_batch_operations.py")
PRODUCT_BEFORE = {
    "juniper_data/api/app.py": "9442bfc4282ada6c9e30bfd83f84bac4850ff9abdec9cf01d19add88560e6721",
    "juniper_data/api/constants.py": "f6cef53b0b964d781a54f142cc15ae3409fc1c92c6b0284f44ac8db7b466e01f",
    "juniper_data/api/routes/datasets.py": "a734b2b246cb05e57b1e62f706c9e3d1996037cf9d11dada5d2e59b2c279360d",
    "juniper_data/api/routes/health.py": "84da8da04d9b0d0360750b76253b9608f96e95c151f95c0a47ba3e4e2c9dc7be",
    "juniper_data/api/settings.py": "3e72f893a0d761e4fc176e0364864a5a347b43eee059be99e982c7406a5ab654",
    "juniper_data/storage/cached.py": "c32d8de52791c03f96a1b6ab9b977693c97bd9a39ad85ed7356bb4dd9e14e37e",
    "juniper_data/storage/hf_store.py": "b85eeb4d7188a69daf09e32846fb3972c2aeaf42d9a500b45b3cf1d39a60fa5d",
    "juniper_data/storage/local_fs.py": "f7ca5de8776f9c59f8492b2438ec87863297ab133cc811df76b7c71516533764",
}


def sha256_of(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def porcelain(tree: Path) -> dict[str, str]:
    done = subprocess.run(["git", "-C", str(tree), "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True)
    return {line[3:]: line[:2] for line in done.stdout.splitlines() if line}


def head_of(tree: Path) -> str:
    return subprocess.run(["git", "-C", str(tree), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def final_hashes() -> dict[str, str]:
    rows = {}
    for line in (DELIVERABLES / "sha256_final.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            rows[name.strip()] = digest
    return rows


def check_hashes(tree: Path, expected: dict[str, str | None]) -> list[str]:
    return [f"{name}: expected {want}, found {sha256_of(tree / name)}" for name, want in expected.items() if sha256_of(tree / name) != want]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", required=True)
    parser.add_argument("--v1-landed", default=str(SCRATCH / "landing" / "V1_landed.json"))
    ns = parser.parse_args()
    manifest_paths = set(final_hashes()) | set(DELETED)
    landed = {row["path"]: row["sha256"] for row in json.loads(Path(ns.v1_landed).read_text(encoding="utf-8"))["applied"]}
    report: dict = {}
    for label, tree, expected in (
        ("C", CARRIER, {**final_hashes(), **{name: None for name in DELETED}}),
        ("V0", V0, {**final_hashes(), **{name: None for name in DELETED}, **PRODUCT_BEFORE}),
        ("V1", V1, {**landed, **PRODUCT_BEFORE}),
    ):
        status = porcelain(tree)
        report[label] = {
            "tree": str(tree),
            "head": head_of(tree),
            "files_checked": len(expected),
            "mismatches": check_hashes(tree, expected),
            "status_paths": len(status),
            "status_outside_the_16": sorted(set(status) - manifest_paths),
            "the_16_missing_from_status": sorted(manifest_paths - set(status)),
        }
        row = report[label]
        print(f"{label}: head {row['head'][:12]} | {row['files_checked']} files, {len(row['mismatches'])} mismatches | status {row['status_paths']} paths, outside {row['status_outside_the_16']}, missing {row['the_16_missing_from_status']}")
        for line in row["mismatches"]:
            print(f"   MISMATCH {line}")
    Path(ns.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    clean = all(not row["mismatches"] and not row["status_outside_the_16"] and not row["the_16_missing_from_status"] for row in report.values())
    print("ALL CLEAN" if clean else "NOT CLEAN")
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
