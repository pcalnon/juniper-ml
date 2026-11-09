#!/usr/bin/env python3
"""
Independently re-derive the provenance of every file in the juniper-canopy flood-4 TESTS carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#789 #792 #794 #795; flood-4 validation brief (test correctness / fidelity lens)

Reads only git objects and `gh` (read-only); writes nothing to any repository. For each draft: the live
head on GitHub vs the fetched ref, merge-base with main, every path it changed (merge-base..head), and
whether main changed that path -- or a workflow the draft's test pins -- since the merge-base. For each
carried test file: the validation worktree's bytes vs the draft head blob (unified diff when they differ).
For CHANGELOG.md: whether the carrier's diff against main removes any line, and the drafts' own hunks.

    python3 2026-11-07_flood4_val_canopy_tests_fidelity.py <canopy primary> <validation worktree> <base sha>
"""

from __future__ import annotations

import difflib
import json
import subprocess
import sys
from pathlib import Path

DRAFTS = {
    "789": ["src/tests/regression/test_bandit_sarif_upload.py"],
    "792": ["src/tests/regression/test_lockfile_regen_empty_payload.py"],
    "794": ["src/tests/unit/test_agents_md_date_check.py"],
    "795": ["src/tests/regression/test_codecov_token_upload.py"],
}
PINNED_WORKFLOWS = [
    ".github/workflows/ci.yml",
    ".github/workflows/security-scan.yml",
    ".github/workflows/lockfile-update.yml",
    ".github/workflows/agents-md-touch-up.yml",
]


def git(repo: str, *args: str, check: bool = True) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=check).stdout


def gh_json(*args: str) -> dict:
    out = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if out.returncode != 0:
        return {"error": out.stderr.strip()}
    return json.loads(out.stdout)


def main() -> int:
    primary, worktree, base = sys.argv[1], sys.argv[2], sys.argv[3]
    main_sha = git(primary, "rev-parse", "origin/main").strip()
    print(f"origin/main={main_sha} base={base} equal={main_sha == base}")
    for pr, paths in DRAFTS.items():
        ref = f"refs/flood4/pr/{pr}"
        head = git(primary, "rev-parse", ref).strip()
        live = gh_json("pr", "view", pr, "--repo", "pcalnon/juniper-canopy", "--json", "headRefOid,state,isDraft,baseRefName,title")
        print(f"\n=== #{pr} fetched head {head}")
        print(f"    live: {live}")
        print(f"    live head == fetched head: {live.get('headRefOid') == head}")
        mb = git(primary, "merge-base", base, head).strip()
        print(f"    merge-base with base: {mb}")
        print("    draft name-status (merge-base..head):")
        for row in git(primary, "diff", "--name-status", mb, head).strip().splitlines():
            print("       ", row)
        changed_since = git(primary, "diff", "--name-only", mb, base, "--", *paths, *PINNED_WORKFLOWS, "CHANGELOG.md").strip()
        print(f"    paths/pinned workflows main changed since merge-base: {changed_since.splitlines() or '(none)'}")
        for path in paths:
            draft = subprocess.run(["git", "-C", primary, "show", f"{head}:{path}"], capture_output=True, check=False).stdout
            carried = (Path(worktree) / path).read_bytes()
            print(f"    {path}: draft {len(draft)} B, carried {len(carried)} B, identical={draft == carried}")
            if draft != carried:
                diff = difflib.unified_diff(
                    draft.decode("utf-8").splitlines(),
                    carried.decode("utf-8").splitlines(),
                    fromfile=f"#{pr} head:{path}",
                    tofile=f"carrier:{path}",
                    lineterm="",
                )
                for line in diff:
                    print("        " + line)
        if "CHANGELOG.md" in git(primary, "diff", "--name-only", mb, head).split():
            print("    draft CHANGELOG hunk (merge-base..head):")
            for line in git(primary, "diff", "-U1", mb, head, "--", "CHANGELOG.md").splitlines():
                print("        " + line)
    print("\n=== carrier CHANGELOG.md vs base")
    diff = git(worktree, "diff", "--numstat", base, "--", "CHANGELOG.md").strip()
    print(f"    numstat: {diff}")
    removed = [line for line in git(worktree, "diff", "-U0", base, "--", "CHANGELOG.md").splitlines() if line.startswith("-") and not line.startswith("---")]
    print(f"    removed lines: {len(removed)}")
    for line in removed:
        print("       ", line)
    heads = [line for line in (Path(worktree) / "CHANGELOG.md").read_text(encoding="utf-8").splitlines() if line.startswith("## [")]
    print(f"    first release headings: {heads[:3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
