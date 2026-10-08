#!/usr/bin/env python3
"""2026-10-08_fleet_flood3_census.py -- one-pass census of every open fleet PR, with the facts a disposition needs.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 3, 2026-10-04..06)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License
Created: 2026-10-08
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-07_fleet_backlog_census.py` (counts only), `2026-09-05_fleet_harvest_triage.py`
         (per-file NEW/DIVERGED/SAME against main), `util/fleet_triage/predict_merge.py`

WHY THIS EXISTS

The backlog census answers "how many"; a disposition needs, per PR: what class of change it is,
which files it truly touches and in which category (docs / tests / production / CI), how many
commits it carries (a fleet PR is not always one commit -- see the consolidation-traps memory),
whether its branch is behind main, and the state of the REQUIRED status contexts on its head.

The required set is read from each repo's live branch rules, never assumed from juniper-ml's:
a check that is green but not required tells us nothing about mergeability, and a required check
that never reported is MISSING, which is not the same as PENDING. A PR whose required context
was skipped (e.g. `Regression Tests` skipped because `Pre-commit` failed upstream) is reported as
SKIPPED, because "CI never ran most of these suites" was round 2's central quality finding.

A repo that cannot be read is reported as ERROR, never as zero.

Usage:
    2026-10-08_fleet_flood3_census.py --out <json> [--repo NAME ...] [--owner pcalnon] [--drafts-only]

Exit: 0 when every repo answered; 2 when any repo or PR could not be read.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv gh invocations, no shell
import sys
from collections import Counter

QUERY = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: OPEN, first: 25, after: $after, orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title isDraft createdAt updatedAt
        author { login }
        headRefName headRefOid baseRefName
        mergeable mergeStateStatus
        additions deletions changedFiles
        commits(first: 20) { totalCount nodes { commit { oid messageHeadline } } }
        files(first: 100) { nodes { path additions deletions changeType } }
        labels(first: 10) { nodes { name } }
        autoMergeRequest { enabledAt }
        lastCommit: commits(last: 1) {
          nodes { commit { statusCheckRollup { state contexts(first: 100) {
            nodes {
              __typename
              ... on CheckRun { name conclusion status }
              ... on StatusContext { context state }
            }
          } } } }
        }
      }
    }
  }
}
"""


def gh(args: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603 B607


def roster(owner: str) -> list[str]:
    res = gh(["repo", "list", owner, "--limit", "500", "--json", "name,isArchived"])
    if res.returncode != 0:
        raise SystemExit(f"ERROR: cannot enumerate {owner}'s repos: {res.stderr.strip()}")
    return sorted(r["name"] for r in json.loads(res.stdout) if not r.get("isArchived"))


def required_contexts(owner: str, repo: str) -> tuple[list[str], bool | None, str | None]:
    """(contexts, strict, error) from the live branch rules of `main`."""
    res = gh(["api", f"repos/{owner}/{repo}/rules/branches/main"])
    if res.returncode != 0:
        return [], None, res.stderr.strip() or "rules read failed"
    ctx: list[str] = []
    strict = None
    for rule in json.loads(res.stdout):
        if rule.get("type") == "required_status_checks":
            params = rule.get("parameters") or {}
            strict = bool(params.get("strict_required_status_checks_policy")) or bool(strict)
            ctx.extend(c["context"] for c in params.get("required_status_checks") or [])
    return sorted(set(ctx)), strict, None


def fetch_prs(owner: str, repo: str) -> list[dict]:
    out: list[dict] = []
    after = None
    while True:
        args = ["api", "graphql", "-f", f"query={QUERY}", "-F", f"owner={owner}", "-F", f"name={repo}"]
        if after:
            args += ["-F", f"after={after}"]
        res = gh(args)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip() or "graphql failed")
        data = json.loads(res.stdout)
        conn = data["data"]["repository"]["pullRequests"]
        out.extend(conn["nodes"])
        if not conn["pageInfo"]["hasNextPage"]:
            return out
        after = conn["pageInfo"]["endCursor"]


def file_category(path: str) -> str:
    low = path.lower()
    if low.startswith(".github/workflows/"):
        return "ci"
    if low.endswith(".md"):
        return "docs"
    base = low.rsplit("/", 1)[-1]
    if "/tests/" in f"/{low}" or base.startswith("test_") or base.endswith("_test.py") or low.startswith("tests/"):
        return "tests"
    if low.endswith((".yml", ".yaml", ".toml", ".cfg", ".ini", ".json", ".txt", ".lock")):
        return "config"
    return "prod"


def change_class(title: str) -> str:
    head = title.split(":", 1)[0].strip().lower()
    return head.split("(", 1)[0] if head else "other"


def rollup(pr: dict, required: list[str]) -> dict:
    nodes = (pr.get("lastCommit") or {}).get("nodes") or []
    roll = ((nodes[0] or {}).get("commit") or {}).get("statusCheckRollup") if nodes else None
    seen: dict[str, str] = {}
    for c in ((roll or {}).get("contexts") or {}).get("nodes") or []:
        if c.get("__typename") == "CheckRun":
            name = c.get("name")
            if c.get("status") != "COMPLETED":
                verdict = "PENDING"
            else:
                verdict = (c.get("conclusion") or "UNKNOWN").upper()
        else:
            name = c.get("context")
            verdict = (c.get("state") or "UNKNOWN").upper()
        if not name:
            continue
        # A context reported more than once (re-runs) keeps its worst reading.
        rank = {"FAILURE": 5, "ERROR": 5, "CANCELLED": 4, "TIMED_OUT": 4, "ACTION_REQUIRED": 4, "STARTUP_FAILURE": 4, "PENDING": 3, "EXPECTED": 3, "SKIPPED": 2, "NEUTRAL": 1, "SUCCESS": 0}
        if name not in seen or rank.get(verdict, 3) > rank.get(seen[name], 3):
            seen[name] = verdict
    req = {}
    for name in required:
        req[name] = seen.get(name, "MISSING")
    tally = Counter(req.values())
    failing_any = sorted(n for n, v in seen.items() if v in ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "STARTUP_FAILURE"))
    return {
        "rollup_state": (roll or {}).get("state"),
        "required": req,
        "required_tally": dict(tally),
        "failing_any": failing_any,
    }


def compare(owner: str, repo: str, head_sha: str) -> dict:
    res = gh(["api", f"repos/{owner}/{repo}/compare/main...{head_sha}", "--jq", "{ahead_by, behind_by, status}"])
    if res.returncode != 0:
        return {"error": res.stderr.strip()[:200]}
    return json.loads(res.stdout)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", action="append", help="repo name(s); default: every non-archived repo in the org")
    ap.add_argument("--drafts-only", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    repos = args.repo or roster(args.owner)
    report: dict = {"owner": args.owner, "repos": {}}
    errors = 0
    for repo in repos:
        entry: dict = {"prs": []}
        ctx, strict, err = required_contexts(args.owner, repo)
        entry.update(required_contexts=ctx, strict=strict, rules_error=err)
        try:
            prs = fetch_prs(args.owner, repo)
        except (RuntimeError, KeyError, TypeError, json.JSONDecodeError) as exc:
            entry["error"] = str(exc)[:300]
            errors += 1
            report["repos"][repo] = entry
            print(f"{repo:24s} ERROR {exc}", file=sys.stderr)
            continue
        for pr in prs:
            if args.drafts_only and not pr.get("isDraft"):
                continue
            files = (pr.get("files") or {}).get("nodes") or []
            cats = Counter(file_category(f["path"]) for f in files)
            commits = pr.get("commits") or {}
            row = {
                "number": pr["number"],
                "title": pr["title"],
                "class": change_class(pr["title"]),
                "author": (pr.get("author") or {}).get("login"),
                "draft": pr.get("isDraft"),
                "created": pr.get("createdAt"),
                "head_ref": pr.get("headRefName"),
                "head_sha": pr.get("headRefOid"),
                "base_ref": pr.get("baseRefName"),
                "mergeable": pr.get("mergeable"),
                "merge_state": pr.get("mergeStateStatus"),
                "auto_merge": bool(pr.get("autoMergeRequest")),
                "additions": pr.get("additions"),
                "deletions": pr.get("deletions"),
                "changed_files": pr.get("changedFiles"),
                "files_truncated": (pr.get("changedFiles") or 0) > len(files),
                "commit_count": commits.get("totalCount"),
                "commit_headlines": [n["commit"]["messageHeadline"] for n in commits.get("nodes") or []],
                "files": [{"path": f["path"], "add": f["additions"], "del": f["deletions"], "type": f["changeType"], "cat": file_category(f["path"])} for f in files],
                "categories": dict(cats),
                "labels": [lb["name"] for lb in (pr.get("labels") or {}).get("nodes") or []],
                "checks": rollup(pr, ctx),
                "compare": compare(args.owner, repo, pr["headRefOid"]),
            }
            entry["prs"].append(row)
        report["repos"][repo] = entry
        n = len(entry["prs"])
        if n:
            print(f"{repo:24s} {n:3d} PR(s)  required={len(ctx)} strict={strict}")
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    total = sum(len(e.get("prs", [])) for e in report["repos"].values())
    print(f"total={total} errors={errors} -> {args.out}")
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
