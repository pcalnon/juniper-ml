#!/usr/bin/env python3
"""2026-10-08_fleet_flood3_pr_actions.py -- the GitHub mutations a fleet disposition needs, each gated.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 3, 2026-10-04..06)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License
Created: 2026-10-08
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-05_fleet_close_superseded.py` (round 2's closer, whose comment text is round-2
         specific), `2026-09-05_auto_merge_shepherd.py` (keeps an ARMED PR synced until it lands)

WHY THIS EXISTS

`gh pr edit` is dead on this box (gh 2.46.0 asks for the retired `projectCards` field), so every PR
mutation here goes through the API. Each subcommand re-reads the PR's live state first, because fleet
PRs are touched concurrently by other sessions and by the owner's sweeper, and acts only on the state
it expects:

    state   print state / draft / mergeStateStatus / auto-merge / behind_by for each PR
    ready   mark a DRAFT ready for review (GraphQL markPullRequestReadyForReview); no-op otherwise
    arm     enable native auto-merge (SQUASH) on an OPEN, non-draft PR; no-op if already armed
    close   comment and close, from a JSON spec; a CARRIED PR is closed ONLY when its carrier is
            MERGED -- closing against a merely-open carrier strands the content if that carrier is
            later abandoned, and a bot PR closed by mistake is never reopened by its author

`close` is a dry run unless `--execute` is given. `ready` and `arm` act immediately -- they are
reversible (`convertPullRequestToDraft`, `disablePullRequestAutoMerge`) and gated on the owner's
merge approval for this set (2026-10-08 session).

Close spec (JSON list):
    {"repo": "juniper-ml", "pr": 2129, "carrier": 2190 | null, "comment_file": "<path>"}

Usage:
    2026-10-08_fleet_flood3_pr_actions.py state --repo juniper-ml --pr 2119 --pr 2122
    2026-10-08_fleet_flood3_pr_actions.py ready --repo juniper-ml --pr 2119
    2026-10-08_fleet_flood3_pr_actions.py arm   --repo juniper-ml --pr 2119
    2026-10-08_fleet_flood3_pr_actions.py close --spec closes.json [--execute]

Exit: 0 when every requested action succeeded or was a correct no-op; 1 when any was refused or
      failed; 2 when a PR could not be read.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv gh invocations, no shell
import sys
from pathlib import Path

OWNER = "pcalnon"

PR_QUERY = """
query($owner: String!, $name: String!, $n: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $n) {
      id number state isDraft merged mergeStateStatus headRefOid headRefName baseRefName
      autoMergeRequest { enabledAt mergeMethod }
    }
  }
}
"""


def gh(args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, timeout=180, check=False)  # nosec B603 B607


def read_pr(repo: str, n: int) -> dict:
    res = gh(["api", "graphql", "-f", f"query={PR_QUERY}", "-F", f"owner={OWNER}", "-F", f"name={repo}", "-F", f"n={n}"])
    if res.returncode != 0:
        raise RuntimeError(f"{repo}#{n}: read failed: {res.stderr.strip()[:200]}")
    pr = json.loads(res.stdout)["data"]["repository"]["pullRequest"]
    if pr is None:
        raise RuntimeError(f"{repo}#{n}: no such PR")
    cmp = gh(["api", f"repos/{OWNER}/{repo}/compare/{pr['baseRefName']}...{pr['headRefOid']}", "--jq", ".behind_by"])
    pr["behind_by"] = cmp.stdout.strip() if cmp.returncode == 0 else "?"
    return pr


def mutate(query: str, **variables: str) -> tuple[bool, str]:
    args = ["api", "graphql", "-f", f"query={query}"]
    for k, v in variables.items():
        args += ["-F", f"{k}={v}"]
    res = gh(args)
    if res.returncode != 0:
        return False, (res.stderr or res.stdout).strip()[:300]
    body = json.loads(res.stdout)
    if body.get("errors"):
        return False, json.dumps(body["errors"])[:300]
    return True, "ok"


def fmt(repo: str, pr: dict) -> str:
    auto = (pr.get("autoMergeRequest") or {}).get("mergeMethod") or "-"
    return f"{repo}#{pr['number']}: state={pr['state']} draft={pr['isDraft']} merged={pr['merged']} merge_state={pr['mergeStateStatus']} auto={auto} behind_by={pr['behind_by']} head={pr['headRefOid'][:10]}"


def cmd_state(repo: str, prs: list[int]) -> int:
    rc = 0
    for n in prs:
        try:
            print(fmt(repo, read_pr(repo, n)))
        except RuntimeError as exc:
            print(f"READ-FAILED {exc}")
            rc = 2
    return rc


def cmd_ready(repo: str, prs: list[int]) -> int:
    rc = 0
    for n in prs:
        try:
            pr = read_pr(repo, n)
        except RuntimeError as exc:
            print(f"READ-FAILED {exc}")
            rc = max(rc, 2)
            continue
        if pr["state"] != "OPEN":
            print(f"{repo}#{n}: SKIP not open ({pr['state']})")
            continue
        if not pr["isDraft"]:
            print(f"{repo}#{n}: already ready")
            continue
        ok, msg = mutate("mutation($id: ID!) { markPullRequestReadyForReview(input: {pullRequestId: $id}) { pullRequest { isDraft } } }", id=pr["id"])
        print(f"{repo}#{n}: {'READY' if ok else 'FAILED ' + msg}")
        rc = rc if ok else max(rc, 1)
    return rc


def cmd_arm(repo: str, prs: list[int]) -> int:
    rc = 0
    for n in prs:
        try:
            pr = read_pr(repo, n)
        except RuntimeError as exc:
            print(f"READ-FAILED {exc}")
            rc = max(rc, 2)
            continue
        if pr["state"] != "OPEN" or pr["isDraft"]:
            print(f"{repo}#{n}: REFUSED (state={pr['state']} draft={pr['isDraft']}); arm needs an open, ready PR")
            rc = max(rc, 1)
            continue
        if pr.get("autoMergeRequest"):
            print(f"{repo}#{n}: already armed ({pr['autoMergeRequest'].get('mergeMethod')})")
            continue
        ok, msg = mutate(
            "mutation($id: ID!) { enablePullRequestAutoMerge(input: {pullRequestId: $id, mergeMethod: SQUASH}) { pullRequest { autoMergeRequest { enabledAt } } } }",
            id=pr["id"],
        )
        print(f"{repo}#{n}: {'ARMED (squash)' if ok else 'FAILED ' + msg}")
        rc = rc if ok else max(rc, 1)
    return rc


def cmd_close(spec_path: str, execute: bool) -> int:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    rc = 0
    for item in spec:
        repo, n, carrier = item["repo"], int(item["pr"]), item.get("carrier")
        comment = Path(item["comment_file"]).read_text(encoding="utf-8").strip()
        try:
            pr = read_pr(repo, n)
        except RuntimeError as exc:
            print(f"READ-FAILED {exc}")
            rc = max(rc, 2)
            continue
        if pr["state"] != "OPEN":
            print(f"{repo}#{n}: SKIP not open ({pr['state']}, merged={pr['merged']})")
            continue
        if carrier:
            try:
                cpr = read_pr(item.get("carrier_repo", repo), int(carrier))
            except RuntimeError as exc:
                print(f"{repo}#{n}: REFUSED carrier unreadable: {exc}")
                rc = max(rc, 1)
                continue
            if not cpr["merged"]:
                print(f"{repo}#{n}: REFUSED carrier #{carrier} is not MERGED (state={cpr['state']})")
                rc = max(rc, 1)
                continue
        if not execute:
            print(f"{repo}#{n}: WOULD comment ({len(comment)} chars) and close" + (f" (carrier #{carrier} merged)" if carrier else ""))
            continue
        res = gh(["api", "-X", "POST", f"repos/{OWNER}/{repo}/issues/{n}/comments", "-F", "body=@-"], stdin=comment)
        if res.returncode != 0:
            print(f"{repo}#{n}: FAILED to comment: {res.stderr.strip()[:200]}")
            rc = max(rc, 1)
            continue
        res = gh(["api", "-X", "PATCH", f"repos/{OWNER}/{repo}/pulls/{n}", "-f", "state=closed"])
        if res.returncode != 0:
            print(f"{repo}#{n}: commented but FAILED to close: {res.stderr.strip()[:200]}")
            rc = max(rc, 1)
            continue
        print(f"{repo}#{n}: CLOSED")
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("state", "ready", "arm"):
        sp = sub.add_parser(name)
        sp.add_argument("--repo", required=True, help="bare repo name, e.g. juniper-ml")
        sp.add_argument("--pr", type=int, action="append", required=True)
    sc = sub.add_parser("close")
    sc.add_argument("--spec", required=True)
    sc.add_argument("--execute", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "state":
        return cmd_state(args.repo, args.pr)
    if args.cmd == "ready":
        return cmd_ready(args.repo, args.pr)
    if args.cmd == "arm":
        return cmd_arm(args.repo, args.pr)
    return cmd_close(args.spec, args.execute)


if __name__ == "__main__":
    sys.exit(main())
