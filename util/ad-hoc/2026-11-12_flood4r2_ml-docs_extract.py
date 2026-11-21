#!/usr/bin/env python3
"""
Extract each round-2 "ml-docs" draft's OWN hunks (merge-base..head) and its live metadata.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- one-off (Cursor flood-4 round-2 docs-carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2); adapted from
         util/ad-hoc/2026-11-07_flood4_ml_docs_extract.py (round 1), which reads refs/flood4/pr/<N>

For every PR number given, reads refs/flood4r2/pr/<N> (fetched beforehand in ONE fetch), computes the
merge-base with the base ref, lists the commits merge-base..head (so a draft stacked on another branch is
visible), writes the whole diff to <out>/raw/<N>.diff, one diff per changed file to
<out>/raw/<N>/<flattened path>.diff, and a per-draft summary to <out>/extract_summary.json. The title and the
live head SHA come from `gh pr view` (read-only), so a head that moved since the fetch is reported, not used.

Nothing is applied: a docs draft is carried sentence by sentence, each claim checked against the code first.

Usage: 2026-11-12_flood4r2_ml-docs_extract.py <base-ref> <out-dir> <N> [<N> ...]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REF_PREFIX = "refs/flood4r2/pr/"
GH_FIELDS = "title,headRefOid,headRefName,state,isDraft,baseRefName,createdAt"


def run(args: list[str]) -> str:
    proc = subprocess.run(args, cwd=str(REPO), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} -> {proc.returncode}: {proc.stderr.strip()[:400]}")
    return proc.stdout


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__)
        return 2
    base, out = argv[1], Path(argv[2])
    (out / "raw").mkdir(parents=True, exist_ok=True)
    summary = []
    for number in argv[3:]:
        head = run(["git", "rev-parse", REF_PREFIX + number]).strip()
        merge_base = run(["git", "merge-base", base, head]).strip()
        commits = run(["git", "log", "--format=%H %s", f"{merge_base}..{head}"]).strip().splitlines()
        raw = run(["git", "diff", "--no-color", "--no-ext-diff", f"{merge_base}..{head}"])
        numstat = run(["git", "diff", "--numstat", f"{merge_base}..{head}"]).strip().splitlines()
        (out / "raw" / f"{number}.diff").write_text(raw, encoding="utf-8")
        per_file_dir = out / "raw" / number
        per_file_dir.mkdir(parents=True, exist_ok=True)
        paths = [line.split("\t")[2] for line in numstat]
        for path in paths:
            one = run(["git", "diff", "--no-color", "--no-ext-diff", f"{merge_base}..{head}", "--", path])
            (per_file_dir / (path.replace("/", "__") + ".diff")).write_text(one, encoding="utf-8")
        meta = json.loads(run(["gh", "pr", "view", number, "--repo", "pcalnon/juniper-ml", "--json", GH_FIELDS]))
        summary.append(
            {
                "pr": int(number),
                "head_sha": head,
                "live_head": meta["headRefOid"],
                "head_moved": meta["headRefOid"] != head,
                "state": meta["state"],
                "is_draft": meta["isDraft"],
                "base": meta["baseRefName"],
                "branch": meta["headRefName"],
                "created_at": meta["createdAt"],
                "title": meta["title"],
                "merge_base": merge_base,
                "commits": commits,
                "numstat": numstat,
            }
        )
        print(f"#{number} head={head[:8]} live={meta['headRefOid'][:8]} moved={meta['headRefOid'] != head} mb={merge_base[:8]} commits={len(commits)} files={len(numstat)} state={meta['state']}")
        for line in numstat:
            print(f"    {line}")
    with open(out / "extract_summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
