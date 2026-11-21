#!/usr/bin/env python3
"""
Extract each flood-4 round-2 ml-code draft's OWN hunks (merge-base..head) into the ml-code scratch dir.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 round 2, ml-code carrier (#2485 #2493 #2494 #2502 #2504 #2505 #2508 #2513);
         BRIEF_COMMON_R2 rule 7 (own hunks only, never a whole-file copy). Adapted from
         2026-11-07_flood4_canopy_extract_hunks.py.

Usage: 2026-11-08_flood4r2_ml_code_extract_hunks.py <juniper-ml worktree> <out dir>

For each PR head fetched as refs/flood4r2/pr/<N>, the base is origin/main. Writes
<out>/pr<N>.patch (merge-base..head), <out>/pr<N>.<file-slug>.patch per file,
<out>/pr<N>.stat.txt and <out>/extract_summary.json.
"""
import json
import subprocess
import sys
from pathlib import Path

PRS = (2485, 2493, 2494, 2502, 2504, 2505, 2508, 2513, 2470)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def main(argv: list[str]) -> int:
    repo = Path(argv[1]).resolve()
    out = Path(argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    main_sha = git(repo, "rev-parse", "origin/main").strip()
    summary: dict = {"origin_main": main_sha, "prs": {}}
    for num in PRS:
        head = git(repo, "rev-parse", f"refs/flood4r2/pr/{num}").strip()
        mbase = git(repo, "merge-base", main_sha, head).strip()
        patch = git(repo, "diff", "--no-color", "--no-ext-diff", mbase, head)
        stat = git(repo, "diff", "--numstat", mbase, head)
        commits = git(repo, "log", "--format=%H %G? %s", f"{mbase}..{head}")
        (out / f"pr{num}.patch").write_text(patch, encoding="utf-8")
        (out / f"pr{num}.stat.txt").write_text(stat + "\n" + commits, encoding="utf-8")
        files = []
        for line in stat.splitlines():
            add, rem, path = line.split("\t", 2)
            slug = path.replace("/", "__")
            per_file = git(repo, "diff", "--no-color", "--no-ext-diff", mbase, head, "--", path)
            (out / f"pr{num}.{slug}.patch").write_text(per_file, encoding="utf-8")
            changed_on_main = git(repo, "diff", "--name-only", mbase, main_sha, "--", path).strip() != ""
            files.append({"path": path, "added": add, "removed": rem, "main_changed_since_merge_base": changed_on_main})
        summary["prs"][str(num)] = {
            "head": head,
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
