#!/usr/bin/env python3
"""
Extract each Cursor flood-4 juniper-ml docs draft's OWN hunks (merge-base..head), stamp hunks stripped.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs-carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md; flood-3 helper
         util/ad-hoc/2026-10-08_flood3_strip_stamp_hunks.py (invoked unchanged)

For every PR number given, reads refs/flood4/pr/<N> (fetched beforehand in ONE git fetch), computes the
merge-base with the base ref, lists the commits merge-base..head (so a draft that carries another PR's
pre-squash commit is visible), writes the raw diff to <out>/raw/<N>.diff and the stamp-stripped diff to
<out>/own/<N>.diff, and a per-draft summary to <out>/extract_summary.json. Titles and the live head SHA
come from `gh pr view` (read-only), so a head that moved since the fetch is reported, not silently used.

Usage: 2026-11-07_flood4_ml_docs_extract.py <repo> <base-ref> <out-dir> <N> [<N> ...]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

STRIP = Path(__file__).resolve().parent / "2026-10-08_flood3_strip_stamp_hunks.py"


def run(args: list[str], cwd: str | None = None) -> str:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} -> {proc.returncode}: {proc.stderr.strip()[:400]}")
    return proc.stdout


def main(argv: list[str]) -> int:
    if len(argv) < 5:
        print(__doc__)
        return 2
    repo, base, out = argv[1], argv[2], Path(argv[3])
    (out / "raw").mkdir(parents=True, exist_ok=True)
    (out / "own").mkdir(parents=True, exist_ok=True)
    summary = []
    for n in argv[4:]:
        ref = f"refs/flood4/pr/{n}"
        head = run(["git", "-C", repo, "rev-parse", ref]).strip()
        mb = run(["git", "-C", repo, "merge-base", base, head]).strip()
        commits = run(["git", "-C", repo, "log", "--format=%H %s", f"{mb}..{head}"]).strip().splitlines()
        raw = run(["git", "-C", repo, "diff", "--no-color", "--no-ext-diff", f"{mb}..{head}"])
        stat = run(["git", "-C", repo, "diff", "--numstat", f"{mb}..{head}"]).strip().splitlines()
        raw_path = out / "raw" / f"{n}.diff"
        own_path = out / "own" / f"{n}.diff"
        raw_path.write_text(raw, encoding="utf-8")
        strip_log = run([sys.executable, str(STRIP), str(raw_path), str(own_path)])
        meta = json.loads(run(["gh", "pr", "view", n, "--repo", "pcalnon/juniper-ml", "--json", "title,headRefOid,headRefName,state,isDraft,baseRefName"]))
        summary.append(
            {
                "pr": int(n),
                "head_sha": head,
                "live_head": meta["headRefOid"],
                "head_moved": meta["headRefOid"] != head,
                "state": meta["state"],
                "is_draft": meta["isDraft"],
                "base": meta["baseRefName"],
                "branch": meta["headRefName"],
                "title": meta["title"],
                "merge_base": mb,
                "commits": commits,
                "numstat": stat,
                "stamps_neutralised": strip_log.strip().splitlines()[-1] if strip_log.strip() else "",
            }
        )
        print(f"#{n} head={head[:8]} live={meta['headRefOid'][:8]} mb={mb[:8]} commits={len(commits)} files={len(stat)} {strip_log.strip().splitlines()[-1] if strip_log.strip() else ''}")
    with open(out / "extract_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
