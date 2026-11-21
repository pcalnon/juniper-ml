#!/usr/bin/env python3
"""
Print the pull-request census's entries for named pull requests, and its range and read-time summary, from the saved JSON.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-deploy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530;
         util/ad-hoc/2026-11-11_flood4r2_r10-data-client_pr_census.py (writes the JSON this reads)

WHY THIS EXISTS
The census helper prints one summary line per exposed pull request; a port's texts need each exposed pull request's
commit list (SHAs, parents, subjects), its head SHA and dates, and the census's range (lowest and highest number,
earliest and latest creation, base branches, counts of merges). This reads them out of the saved JSON without
re-querying GitHub. It prints SHAs, parents, dates and subjects only.

Usage:
    python3 <this> --census <saved census json> [--pr N ...]
"""

from __future__ import annotations

import argparse
import collections
import json
import subprocess  # nosec B404 - fixed argv: read-only git merge-base --is-ancestor
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--census", required=True, type=Path)
    ap.add_argument("--pr", type=int, nargs="*", default=[])
    ap.add_argument("--from-number", type=int, default=0, help="also summarise the pull requests numbered at least this")
    ap.add_argument("--repo-dir", type=Path, help="a checkout of the repository, to test each merge's other parents against --base-ref (read-only git merge-base)")
    ap.add_argument("--base-ref", default="origin/main")
    args = ap.parse_args()
    with open(args.census, encoding="utf-8") as fh:
        data = json.load(fh)
    prs = data["rows"]
    print("top-level keys:", sorted(data.keys()))
    print("summary:", json.dumps({k: v for k, v in data.items() if k != "rows"})[:1200])
    numbers = sorted(int(p["number"]) for p in prs)
    print(f"pull requests: {len(prs)}; numbers {numbers[0]}..{numbers[-1]}")
    created = sorted(str(p.get("created_at") or p.get("createdAt") or "") for p in prs)
    print(f"created: {created[0]} .. {created[-1]}")
    bases = collections.Counter(str(p.get("base") or p.get("base_ref") or p.get("baseRefName") or "?") for p in prs)
    print("bases:", dict(bases))
    print("entry keys:", sorted(prs[0].keys()))
    if args.from_number:
        late = [p for p in prs if int(p["number"]) >= args.from_number]
        with_merge = [p for p in late if p["merges"]]
        print(
            f"from #{args.from_number}: {len(late)} pull requests (#{min(int(p['number']) for p in late)}..#{max(int(p['number']) for p in late)}),"
            f" largest {max(p['commits'] for p in late)} commits, {len(with_merge)} with a merge commit, {sum(p['merges'] for p in late)} merge commits,"
            f" brought-in own commits {sum(len(p['merge_brought_in_own_commit']) for p in late)},"
            f" first-parent-outside {sum(len(p['merge_first_parent_outside']) for p in late)},"
            f" lost non-merge {sum(len(p['action_window']['lost_non_merge']) for p in late)},"
            f" bases {dict(collections.Counter(p['base_ref'] for p in late))}"
        )
        # A merge's non-first parents: are any of them commits of the same pull request?
        own_side = 0
        for p in late:
            own = {c["sha"] for c in p["graph"]}
            own_side += sum(1 for c in p["graph"] if len(c["parents"]) > 1 and any(x in own for x in c["parents"][1:]))
        print(f"from #{args.from_number}: merges whose other parent is a commit of the same pull request: {own_side}")
        if args.repo_dir:
            # Is each merge's other parent a commit of the base branch (an ancestor of --base-ref)?
            on_base, off_base = 0, []
            for p in late:
                for c in p["graph"]:
                    for other in c["parents"][1:]:
                        res = subprocess.run(["git", "-C", str(args.repo_dir), "merge-base", "--is-ancestor", other, args.base_ref], capture_output=True, check=False, timeout=60)  # nosec B603 B607
                        if res.returncode == 0:
                            on_base += 1
                        else:
                            off_base.append((p["number"], c["sha"][:10], other[:10], res.returncode))
            print(f"from #{args.from_number}: merge parents (other than the first) that are commits of {args.base_ref}: {on_base}; not: {off_base}")
    for p in prs:
        if int(p["number"]) not in args.pr:
            continue
        shown = {k: v for k, v in p.items() if k != "graph"}
        print(json.dumps(shown, indent=None)[:1500])
        for c in p.get("graph") or []:
            print("   ", c["sha"][:10], "parents", [x[:10] for x in c["parents"]], c["date"], c["subject"][:90])
    return 0


if __name__ == "__main__":
    sys.exit(main())
