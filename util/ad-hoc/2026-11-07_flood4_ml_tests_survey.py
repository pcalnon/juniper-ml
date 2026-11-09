"""
Survey the 28 juniper-ml flood-4 test drafts: merge-base, changed files and own patch per draft.

Reads refs/flood4/pr/<N> (fetched beforehand in one `git fetch`), computes each draft's merge-base
with origin/main, writes `<scratch>/patches/pr<N>.patch` (merge-base..head, binary-safe) and a
`<scratch>/survey.json` with per-draft head sha, base sha, title, and name-status / numstat rows.
Read-only on git: it never checks out, commits or pushes.

Usage: python3 util/ad-hoc/2026-11-07_flood4_ml_tests_survey.py <scratch-dir>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md (flood-4 consolidation)
"""

import json
import subprocess
import sys
from pathlib import Path

PRS = [2466, 2419, 2427, 2430, 2436, 2439, 2441, 2443, 2445, 2447, 2451, 2458, 2461, 2463, 2425, 2413, 2414, 2416, 2429, 2431, 2434, 2421, 2448, 2459, 2410, 2455, 2403, 2407]


def run(*args: str) -> str:
    return subprocess.run(list(args), check=True, capture_output=True, text=True).stdout


def main() -> int:
    scratch = Path(sys.argv[1]).resolve()
    (scratch / "patches").mkdir(parents=True, exist_ok=True)
    titles = {}
    try:
        raw = run("gh", "pr", "list", "--repo", "pcalnon/juniper-ml", "--state", "open", "--limit", "200", "--json", "number,title,headRefOid,baseRefName,isDraft")
        for row in json.loads(raw):
            titles[row["number"]] = row
    except subprocess.CalledProcessError as exc:
        print(f"gh pr list failed: {exc.stderr}", file=sys.stderr)
    main_sha = run("git", "rev-parse", "origin/main").strip()
    out = {"origin_main": main_sha, "prs": []}
    for n in PRS:
        ref = f"refs/flood4/pr/{n}"
        head = run("git", "rev-parse", ref).strip()
        base = run("git", "merge-base", "origin/main", ref).strip()
        ns = [line.split("\t") for line in run("git", "diff", "--name-status", base, head).splitlines() if line]
        num = [line.split("\t") for line in run("git", "diff", "--numstat", base, head).splitlines() if line]
        patch = run("git", "diff", "--binary", "--full-index", base, head)
        (scratch / "patches" / f"pr{n}.patch").write_text(patch)
        meta = titles.get(n, {})
        out["prs"].append(
            {
                "pr": n,
                "head": head,
                "merge_base": base,
                "base_is_main": base == main_sha,
                "title": meta.get("title"),
                "gh_head": meta.get("headRefOid"),
                "baseRefName": meta.get("baseRefName"),
                "isDraft": meta.get("isDraft"),
                "name_status": ns,
                "numstat": num,
            }
        )
        print(f"#{n} head={head[:10]} base={base[:10]} gh_head_match={meta.get('headRefOid') == head} title={meta.get('title')!r}")
        for row in num:
            print(f"    {row[0]:>5} {row[1]:>5} {row[2]}")
    with open(scratch / "survey.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
