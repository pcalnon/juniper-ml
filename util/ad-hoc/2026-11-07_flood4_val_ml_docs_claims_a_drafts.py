"""
Dump the flood-4 juniper-ml drafts' own diffs (merge-base..head) for the docs-carrier claims validator, slice A.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 juniper-ml docs carrier validation, claims lens slice A
         (drafts #2409 #2412 #2417 #2418 #2422 #2426 #2428 #2432 #2433 #2437 and their paired tests drafts)

Usage: python3 2026-11-07_flood4_val_ml_docs_claims_a_drafts.py <base_sha> <out_dir> <pr> [<pr> ...]

For each PR, reads refs/flood4/pr/<pr> (already fetched), computes merge-base(<base_sha>, head) and writes
<out_dir>/draft_<pr>.diff.txt (git diff merge-base head) plus <out_dir>/drafts_index.json. Read-only: it runs
only `git merge-base`, `git rev-parse` and `git diff` in the current working directory.
"""

import json
import os
import subprocess
import sys


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    base, out_dir, prs = argv[1], argv[2], argv[3:]
    os.makedirs(out_dir, exist_ok=True)
    index = {}
    for pr in prs:
        ref = f"refs/flood4/pr/{pr}"
        head = git("rev-parse", ref).strip()
        mb = git("merge-base", base, head).strip()
        diff = git("diff", mb, head)
        stat = git("diff", "--stat", mb, head)
        path = os.path.join(out_dir, f"draft_{pr}.diff.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(diff)
        index[pr] = {"head": head, "merge_base": mb, "diff": path, "stat": stat.strip().splitlines()[-1] if stat.strip() else ""}
    with open(os.path.join(out_dir, "drafts_index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=1)
    for pr, row in index.items():
        print(pr, row["head"][:8], row["merge_base"][:8], row["stat"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
