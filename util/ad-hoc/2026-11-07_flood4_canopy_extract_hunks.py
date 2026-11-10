#!/usr/bin/env python3
"""
Extract each juniper-canopy flood-4 draft's OWN hunks (merge-base..head) into the canopy scratch dir.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation (canopy #789-#796); BRIEF_COMMON rule 7 (own hunks only, never a whole-file copy)

Usage: 2026-11-07_flood4_canopy_extract_hunks.py <canopy repo> <out dir>

For each PR head fetched as refs/flood4/pr/<N>, the base is the PR's own base branch
(origin/main, except #796 which is stacked on origin/fix/mnist-declared-params-778). Writes
<out>/pr<N>.patch (merge-base..head), <out>/pr<N>.stat.txt and <out>/extract_summary.json.
"""
import json
import subprocess
import sys
from pathlib import Path

PRS = {
    789: "origin/main",
    790: "origin/main",
    791: "origin/main",
    792: "origin/main",
    793: "origin/main",
    794: "origin/main",
    795: "origin/main",
    796: "origin/fix/mnist-declared-params-778",
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def main(argv: list[str]) -> int:
    repo = Path(argv[1]).resolve()
    out = Path(argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    main_sha = git(repo, "rev-parse", "origin/main").strip()
    summary = {"origin_main": main_sha, "prs": {}}
    for num, base in PRS.items():
        head = git(repo, "rev-parse", f"refs/flood4/pr/{num}").strip()
        base_sha = git(repo, "rev-parse", base).strip()
        mbase = git(repo, "merge-base", base_sha, head).strip()
        patch = git(repo, "diff", "--no-color", "--no-ext-diff", mbase, head)
        stat = git(repo, "diff", "--numstat", mbase, head)
        commits = git(repo, "log", "--format=%H %s", f"{mbase}..{head}")
        base_tree = git(repo, "rev-parse", f"{base_sha}^{{tree}}").strip()
        main_tree = git(repo, "rev-parse", f"{main_sha}^{{tree}}").strip()
        (out / f"pr{num}.patch").write_text(patch, encoding="utf-8")
        (out / f"pr{num}.stat.txt").write_text(stat + "\n" + commits, encoding="utf-8")
        files = []
        for line in stat.splitlines():
            add, rem, path = line.split("\t", 2)
            files.append({"path": path, "added": add, "removed": rem})
        summary["prs"][str(num)] = {
            "head": head,
            "base_ref": base,
            "base_sha": base_sha,
            "base_tree_equals_main_tree": base_tree == main_tree,
            "merge_base": mbase,
            "merge_base_is_main": mbase == main_sha,
            "commits": commits.strip().splitlines(),
            "files": files,
        }
    (out / "extract_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
