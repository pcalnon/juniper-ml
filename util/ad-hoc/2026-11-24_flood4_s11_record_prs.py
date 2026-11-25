#!/usr/bin/env python3
"""
Read, from GitHub, the state of every pull request and issue the flood-4 record update names (read-only GraphQL).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- verifier for the record update (rulings 15-48 and the changed outcomes of rulings 1-14)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md sections 1, 4 and 8

Why
---
Every outcome the record states (a PR's number, state, merge time and merge commit, or a draft's close) is re-read
here rather than copied from a handoff. Only ``gh api graphql`` queries are sent; nothing is mutated.

What it does
------------
For each ``repo:number`` in ``--items`` (or the built-in list ``ITEMS``) it asks ``issueOrPullRequest`` for: kind,
title, author, state, isDraft, createdAt, closedAt, mergedAt, the merge commit, the head commit, and the last
``--comments`` comments (author, time, first 400 characters), and writes one JSON object per item to ``--out``.
Queries are batched per repository, 40 items at a time. The owner is ``--owner`` (default pcalnon).

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_record_prs.py --out <file.json> [--comments 2] [--items juniper-ml:2554 ...]
"""

from __future__ import annotations

import argparse
import json
import subprocess

ITEMS: dict[str, list[int]] = {
    "juniper-ml": [2404, 2406, *range(2469, 2510), 2512, 2513, 2514, 2515, 2524, 2530, 2531, 2534, 2545, 2547, 2552, 2554, 2555, 2557, 2562, 2579, 2581, 2584, 2587, 2604, 2606, 2618, 2619, 2625, 2626, 2629, 2630, 2631],
    "juniper-data": [*range(520, 525), 529, 530, 532, 534, 535, 536, 537, 539, 540, 542],
    "juniper-data-client": [260, 263],
    "juniper-cascor": [753, 754, 755, 756, 757, 761, 764, 768, 769, 772, 776],
    "juniper-cascor-client": [196, 198],
    "juniper-cascor-worker": [219, 230, 231, 233],
    "juniper-canopy": [*range(798, 802), 807, 808, 814, 815, 822, 824],
    "juniper-deploy": [277, 280],
}

FIELDS = """
  __typename
  ... on PullRequest { number title state isDraft createdAt closedAt mergedAt author { login } mergeCommit { oid } headRefOid
                       comments(last: %(n)d) { nodes { author { login } createdAt body } } }
  ... on Issue { number title state createdAt closedAt author { login }
                 comments(last: %(n)d) { nodes { author { login } createdAt body } } }
"""


def query(owner: str, repo: str, numbers: list[int], n_comments: int) -> dict:
    parts = [f"i{num}: issueOrPullRequest(number: {num}) {{ {FIELDS % {'n': n_comments}} }}" for num in numbers]
    gql = "query { repository(owner: %s, name: %s) { %s } }" % (json.dumps(owner), json.dumps(repo), "\n".join(parts))
    out = subprocess.run(["gh", "api", "graphql", "-f", f"query={gql}"], capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise SystemExit(f"gh api graphql failed for {repo}: {out.stderr.strip()}")
    return json.loads(out.stdout)["data"]["repository"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--items", nargs="*", help="repo:number pairs (default: the built-in list)")
    ap.add_argument("--comments", type=int, default=2)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    items: dict[str, list[int]] = {}
    if args.items:
        for spec in args.items:
            repo, num = spec.split(":")
            items.setdefault(repo, []).append(int(num))
    else:
        items = ITEMS

    rows: list[dict] = []
    for repo, numbers in items.items():
        for start in range(0, len(numbers), 40):
            data = query(args.owner, repo, numbers[start : start + 40], args.comments)
            for num in numbers[start : start + 40]:
                node = data.get(f"i{num}")
                if node is None:
                    rows.append({"repo": repo, "number": num, "kind": None})
                    continue
                row = {
                    "repo": repo,
                    "number": num,
                    "kind": node.get("__typename"),
                    "title": node.get("title"),
                    "author": (node.get("author") or {}).get("login"),
                    "state": node.get("state"),
                    "isDraft": node.get("isDraft"),
                    "createdAt": node.get("createdAt"),
                    "closedAt": node.get("closedAt"),
                    "mergedAt": node.get("mergedAt"),
                    "mergeCommit8": ((node.get("mergeCommit") or {}).get("oid") or "")[:8] or None,
                    "head8": (node.get("headRefOid") or "")[:8] or None,
                    "comments": [
                        {"author": (c.get("author") or {}).get("login"), "at": c.get("createdAt"), "body": (c.get("body") or "")[:400]}
                        for c in (node.get("comments") or {}).get("nodes", [])
                    ],
                }
                rows.append(row)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)
    print(f"{len(rows)} item(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
