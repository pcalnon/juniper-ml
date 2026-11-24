#!/usr/bin/env python3
"""
Census (GET only) of a repository's pull requests for the two shapes gitleaks-action's pull_request scan cuts short.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-data-client)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
gitleaks-action v3.0.0 (e0c47f4f) lists a pull request's commits with one unpaginated request (30 per page, oldest
first) and scans `--no-merges --first-parent <page[0]>^..<page[-1]>`. A pull request is exposed when it has more
than 30 commits, or when it holds a merge commit (the first-parent walk then leaves whatever the merge brought in).
This lists every pull request of the repository, reads each one's commit graph, and prints the exposed ones, so the
port's "defect on this repository's main" claim rests on the repository's own history. For each pull request it also
simulates the action's window from the listing itself (the first page, a first-parent walk from its last commit,
minus the ancestors of its first commit's parent) and names every non-merge commit of the pull request the walk
never reaches. The simulation stops where the walk leaves the pull request, so it does not count the base-branch
commits the action scanned instead; a job log does (`N commits scanned.`).

Every call is an explicit `gh api --method GET`. Nothing is written but --out. `--from-json` recomputes from a
census this script saved earlier, with no request.

Usage:
    python3 <this> --repo pcalnon/juniper-data-client --out <json> [--workers 4] [--from-json <saved census>]
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - fixed argv: gh api --method GET
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PAGE = 30


def get(path: str) -> list | dict:
    proc = subprocess.run(["gh", "api", "--method", "GET", path], capture_output=True, text=True, timeout=180, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise SystemExit(f"GET {path} failed ({proc.returncode}): {proc.stderr.strip()[:300]}")
    return json.loads(proc.stdout)


def get_all(path: str) -> list:
    """Every page of a list endpoint, 100 per page."""
    sep = "&" if "?" in path else "?"
    out: list = []
    page = 1
    while page:
        chunk = get(f"{path}{sep}per_page=100&page={page}")
        out.extend(chunk)
        page = page + 1 if len(chunk) == 100 else 0
    return out


def commits_of(repo: str, number: int) -> list[dict]:
    return [{"sha": c["sha"], "parents": [p["sha"] for p in c["parents"]], "date": c["commit"]["committer"]["date"], "subject": c["commit"]["message"].split("\n")[0][:100]} for c in get_all(f"repos/{repo}/pulls/{number}/commits")]


def action_window(commits: list[dict]) -> dict:
    """What the action's argv scans of a pull request, from the listing alone: `--no-merges --first-parent <page[0]>^..<page[-1]>`.

    The walk follows first parents from the page's last commit for as long as it stays inside the pull request (once
    it leaves, it is on the base branch, and this function does not follow it there). git excludes every ancestor of
    page[0]'s first parent; inside the pull request those are the commits reachable from that parent by any edge.
    Returns the pull request's non-merge commits the walk reaches, and the ones it never reaches.
    """
    by_sha = {c["sha"]: c for c in commits}
    page = commits[:PAGE]
    excluded: set[str] = set()
    stack = [page[0]["parents"][0]] if page[0]["parents"] else []
    while stack:
        sha = stack.pop()
        if sha in by_sha and sha not in excluded:
            excluded.add(sha)
            stack.extend(by_sha[sha]["parents"])
    reached = []
    cursor: str | None = page[-1]["sha"]
    while cursor in by_sha and cursor not in excluded:
        reached.append(cursor)
        cursor = by_sha[cursor]["parents"][0] if by_sha[cursor]["parents"] else None
    scanned = [sha for sha in reached if len(by_sha[sha]["parents"]) == 1]
    non_merge = [c["sha"] for c in commits if len(c["parents"]) == 1]
    return {"scanned_non_merge": len(scanned), "lost_non_merge": [sha[:10] for sha in non_merge if sha not in scanned], "walk_left_the_pull_request_at": cursor[:10] if cursor else None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--from-json", type=Path, help="recompute from a census this script saved earlier, with no request")
    args = ap.parse_args()
    if args.from_json:
        with open(args.from_json, encoding="utf-8") as fh:
            saved = json.load(fh)["rows"]
        pulls = [{"number": r["number"], "title": r["title"], "state": r["state"], "created_at": r["created_at"], "merged_at": r["merged_at"], "user": {"login": r["author"]}, "base": {"ref": r["base_ref"], "sha": r["base_sha"]}, "head": {"sha": r["head_sha"]}} for r in saved]
        graphs = {r["number"]: r["graph"] for r in saved}
    else:
        pulls = get_all(f"repos/{args.repo}/pulls?state=all")
        numbers = sorted(p["number"] for p in pulls)
        with ThreadPoolExecutor(max_workers=min(args.workers, 4)) as pool:
            graphs = dict(zip(numbers, pool.map(lambda n: commits_of(args.repo, n), numbers)))
    rows = []
    for p in sorted(pulls, key=lambda q: q["number"]):
        commits = graphs[p["number"]]
        in_pr = {c["sha"] for c in commits}
        merges = [c for c in commits if len(c["parents"]) > 1]
        # A merge whose FIRST parent is outside the pull request's own commits sends the first-parent walk off the branch.
        leaves = [c["sha"][:10] for c in merges if c["parents"][0] not in in_pr]
        # A merge whose SECOND parent is one of the pull request's commits brought that commit in from a side branch.
        brought_in = [c["sha"][:10] for c in merges if any(parent in in_pr for parent in c["parents"][1:])]
        rows.append(
            {
                "number": p["number"],
                "title": p["title"][:100],
                "state": p["state"],
                "created_at": p["created_at"],
                "merged_at": p["merged_at"],
                "author": p["user"]["login"],
                "base_ref": p["base"]["ref"],
                "base_sha": p["base"]["sha"],
                "head_sha": p["head"]["sha"],
                "commits": len(commits),
                "merges": len(merges),
                "non_merge": len(commits) - len(merges),
                "over_one_page": len(commits) > PAGE,
                "merge_first_parent_outside": leaves,
                "merge_brought_in_own_commit": brought_in,
                "action_window": action_window(commits) if commits else None,
                "graph": commits,
            }
        )
    exposed = [r for r in rows if r["over_one_page"] or r["merges"]]
    lost = {r["number"]: r["action_window"]["lost_non_merge"] for r in rows if r["action_window"] and r["action_window"]["lost_non_merge"]}
    summary = {
        "repo": args.repo,
        "pull_requests": len(rows),
        "largest": max((r["commits"] for r in rows), default=0),
        "over_one_page": [r["number"] for r in rows if r["over_one_page"]],
        "with_a_merge_commit": [r["number"] for r in rows if r["merges"]],
        "pull_requests_whose_own_non_merge_commit_the_action_window_misses": lost,
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")
    print(f"{args.repo}: {len(rows)} pull requests; largest has {summary['largest']} commits; over one page (>{PAGE}): {summary['over_one_page']}")
    print(f"pull requests whose own non-merge commit the action's window misses (simulated from each listing): {lost or 'none'}")
    print(f"with a merge commit: {len(exposed)}")
    for r in exposed:
        print(f"  #{r['number']} commits={r['commits']} merges={r['merges']} non_merge={r['non_merge']} first_parent_outside={len(r['merge_first_parent_outside'])} brought_in={len(r['merge_brought_in_own_commit'])} created={r['created_at'][:10]} merged={(r['merged_at'] or '-')[:10]} {r['author']}: {r['title'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
