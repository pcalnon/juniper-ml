#!/usr/bin/env python3
"""
Compare each file of the juniper-data flood-4 tests carrier with the draft PR head blob it came from.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data tests carrier)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#512 #513 #514 #516 #517; flood-4 common brief rule 7

A carried file should equal the draft's head blob unless the carrier deliberately fixed it. Prints
`SAME` or `DIFF` per file with both blob ids, and for a DIFF the unified diff, so every deviation from the
draft is visible and attributable.

    python3 2026-11-07_flood4_data_blob_compare.py <tests worktree> <juniper-data primary>
"""

from __future__ import annotations

import difflib
import subprocess
import sys

CARRIED = [
    ("512", "juniper_data/tests/unit/test_bandit_sarif_upload.py"),
    ("512", "juniper_data/tests/unit/test_check_module_coverage.py"),
    ("512", "juniper_data/tests/unit/test_run_coverage_gates.py"),
    ("513", "juniper_data/tests/unit/test_publish_image_manifest_identity.py"),
    ("514", "juniper_data/tests/unit/test_publish_manifest_tag_gates.py"),
    ("516", "juniper_data/tests/unit/test_testpypi_install_verify.py"),
    ("517", "juniper_data/tests/unit/test_middleware.py"),
]


def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def main(argv: list[str]) -> int:
    worktree, primary = argv[1], argv[2]
    diffs = 0
    for pr, path in CARRIED:
        head = git(primary, "rev-parse", f"refs/flood4/pr/{pr}:{path}").strip()
        mine = git(worktree, "hash-object", path).strip()
        if head == mine:
            print(f"SAME #{pr} {path} {mine}")
            continue
        diffs += 1
        print(f"DIFF #{pr} {path} draft={head} carrier={mine}")
        draft_text = git(primary, "cat-file", "-p", head)
        with open(f"{worktree}/{path}", encoding="utf-8") as fh:
            carrier_text = fh.read()
        sys.stdout.writelines(difflib.unified_diff(draft_text.splitlines(keepends=True), carrier_text.splitlines(keepends=True), f"draft #{pr}/{path}", f"carrier/{path}"))
    print(f"{len(CARRIED) - diffs}/{len(CARRIED)} carried files equal their draft head blob")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
