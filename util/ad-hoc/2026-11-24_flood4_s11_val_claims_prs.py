#!/usr/bin/env python3
"""
Read, with read-only GraphQL queries, every pull request / issue the flood-4 record update names (validator V1).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11, validator V1 claims lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (validation of the record update's PR claims)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md sections 1, 4, 6, 8;
         independent of util/ad-hoc/2026-11-24_flood4_s11_record_prs.py (the drafter's)

What it does
------------
For each ``repo#number`` given (``--items``, or the built-in list), runs one ``gh api graphql`` query
(``repository(owner: "pcalnon", name: ...) { issueOrPullRequest(number: N) { ... } }``) and records: kind, title,
state, isDraft, author, createdAt, closedAt, mergedAt, merge commit oid, head/base ref, additions/deletions, changed
file count, the first 100 file paths, and the last 5 comments (author, createdAt, first 600 characters). Query only;
nothing is mutated.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_val_claims_prs.py --out <file.json>
    python3 util/ad-hoc/2026-11-24_flood4_s11_val_claims_prs.py --items juniper-ml#2632 juniper-data#536 --out <file.json>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

OWNER = "pcalnon"

QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issueOrPullRequest(number: $number) {
      __typename
      ... on PullRequest {
        title state isDraft createdAt closedAt mergedAt url
        author { login }
        mergeCommit { oid }
        headRefName baseRefName additions deletions changedFiles
        files(first: 100) { nodes { path } }
        comments(last: 5) { nodes { author { login } createdAt body } }
      }
      ... on Issue {
        title state createdAt closedAt url
        author { login }
        comments(last: 5) { nodes { author { login } createdAt body } }
      }
    }
  }
}
"""

ML_ROUND2 = [2469, 2470, 2471, 2472, 2475, 2476, 2477, 2478, 2479, 2480, 2481] + list(range(2483, 2497)) + list(range(2499, 2506)) + [2507, 2508, 2509, 2512, 2513, 2514, 2515]

DEFAULT = (
    [f"juniper-ml#{n}" for n in [2360, 2554, 2552, 2531, 2534, 2584, 2579, 2581, 2557, 2547, 2625, 2618, 2587, 2631, 2632, 2545, 2606, 2524, 2404, 2406, 2517, 2519, 2460, 2598, 2530, 2626, 2630, 2627, 2623]]
    + [f"juniper-ml#{n}" for n in ML_ROUND2]
    + [f"juniper-data#{n}" for n in [530, 537, 529, 532, 536, 539, 540, 542, 544, 546, 549, 520, 521, 522, 523, 524, 518, 519]]
    + [f"juniper-data-client#{n}" for n in [260, 263, 265]]
    + [f"juniper-cascor-client#{n}" for n in [196, 198, 200]]
    + [f"juniper-cascor-worker#{n}" for n in [230, 231, 233]]
    + [f"juniper-cascor#{n}" for n in [753, 754, 756, 761, 764, 769, 776, 768]]
    + [f"juniper-deploy#{n}" for n in [277, 280]]
    + [f"juniper-canopy#{n}" for n in [822, 815, 814, 807, 798, 799, 800, 801, 824, 797, 802]]
)


def fetch(item: str) -> dict:
    repo, num = item.split("#")
    cmd = ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"owner={OWNER}", "-f", f"name={repo}", "-F", f"number={num}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return {"item": item, "error": proc.stderr.strip()[:500]}
    node = (((json.loads(proc.stdout).get("data") or {}).get("repository") or {}).get("issueOrPullRequest")) or {}
    rec = {"item": item, "kind": node.get("__typename")}
    for key in ("title", "state", "isDraft", "createdAt", "closedAt", "mergedAt", "url", "headRefName", "baseRefName", "additions", "deletions", "changedFiles"):
        rec[key] = node.get(key)
    rec["author"] = (node.get("author") or {}).get("login")
    rec["mergeCommit"] = (node.get("mergeCommit") or {}).get("oid")
    rec["files"] = [f["path"] for f in ((node.get("files") or {}).get("nodes") or [])]
    rec["comments"] = [{"author": (c.get("author") or {}).get("login"), "createdAt": c.get("createdAt"), "body": (c.get("body") or "")[:600]} for c in ((node.get("comments") or {}).get("nodes") or [])]
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--items", nargs="*", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    items = args.items or DEFAULT
    out = [fetch(i) for i in items]
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    errs = sum(1 for r in out if "error" in r)
    print(f"{len(out)} items, {errs} errors -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
