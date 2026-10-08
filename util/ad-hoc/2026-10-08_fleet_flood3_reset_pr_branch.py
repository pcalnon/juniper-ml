#!/usr/bin/env python3
"""2026-10-08_fleet_flood3_reset_pr_branch.py -- re-cut an open PR's branch as ONE signed commit on current main.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 3, 2026-10-04..06)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License
Created: 2026-10-08
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `util/open_signed_pr.py` (whose `create_branch` / `create_signed_commit` this reuses),
         `2026-09-08_push_signed_commit.py` (APPENDS to a branch; this REPLACES its history)

WHY THIS EXISTS

Some fleet PRs are right in content and wrong in shape: their branch carries another session's
already-squashed commits, or a lockfile auto-regen commit that main has since superseded, so
`update-branch` stops on a conflict that has nothing to do with the PR's own change. The repo
requires signed commits and a headless session cannot sign locally, so a local rebase + force-push
is not available either.

This keeps the PR (number, discussion, author) and replaces only its branch: a temporary branch is
cut at the base's current tip, the PR's final files land there as ONE GitHub-signed commit
(GraphQL `createCommitOnBranch`), and the PR's head ref is force-moved to that commit. The PR then
shows exactly the change that will land, on top of current main, with no carried history.

GUARDS

- `--expect-tip` must equal the branch's CURRENT tip (read from `git/ref`, not from the PR object:
  juniper-canopy#721's PR head was stale -- 973c8680 -- while its branch had moved to 033d7311).
  A mismatch means someone else pushed; nothing is changed.
- `--base-sha`, when given, must equal the base branch's current tip.
- The tip is re-read immediately before the force-move.
- The temporary branch is deleted afterwards, even on failure after its creation.

Usage:
    2026-10-08_fleet_flood3_reset_pr_branch.py --repo juniper-canopy --pr 721 \\
        --expect-tip 033d7311e57c9d43135a2985f7f992ab14b9f9ea [--base-sha <main sha>] \\
        --add LOCAL:REPOPATH [...] [--delete REPOPATH ...] --message "..." [--commit-body-file F] [--dry-run]

Exit: 0 reset done (or dry run ok); 1 refused (guard tripped); 2 API failure.
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
_SPEC = importlib.util.spec_from_file_location("open_signed_pr", HERE.parents[1] / "open_signed_pr.py")
osp = importlib.util.module_from_spec(_SPEC)
sys.modules["open_signed_pr"] = osp
_SPEC.loader.exec_module(osp)


def branch_tip(owner: str, repo: str, branch: str) -> str:
    return osp.gh(["api", f"repos/{owner}/{repo}/git/ref/heads/{branch}", "--jq", ".object.sha"]).strip()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--expect-tip", required=True, help="the PR branch's current tip (full sha)")
    ap.add_argument("--base-sha", default=None, help="require the base branch tip to equal this")
    ap.add_argument("--add", action="append", default=[], metavar="LOCAL:REPOPATH")
    ap.add_argument("--delete", action="append", default=[], metavar="REPOPATH")
    ap.add_argument("--message", required=True)
    ap.add_argument("--commit-body-file", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    owner, repo = args.owner, args.repo
    pr = osp.json.loads(osp.gh(["api", f"repos/{owner}/{repo}/pulls/{args.pr}"]))
    if pr["state"] != "open":
        print(f"REFUSED: {repo}#{args.pr} is {pr['state']}")
        return 1
    if pr["head"]["repo"]["full_name"] != f"{owner}/{repo}":
        print("REFUSED: head branch lives in another repository")
        return 1
    branch, base = pr["head"]["ref"], pr["base"]["ref"]
    tip = branch_tip(owner, repo, branch)
    if tip != args.expect_tip:
        print(f"REFUSED: {branch} tip is {tip}, expected {args.expect_tip} (PR object says {pr['head']['sha']})")
        return 1
    base_sha = osp.resolve_base_sha(owner, repo, base)
    if args.base_sha and base_sha != args.base_sha:
        print(f"REFUSED: {base} is at {base_sha}, expected {args.base_sha}")
        return 1

    additions = []
    for spec in args.add:
        local, repo_path = osp.parse_add(spec)
        raw = Path(local).read_bytes()
        additions.append((repo_path, base64.b64encode(raw).decode("ascii")))
    body = Path(args.commit_body_file).read_text(encoding="utf-8").strip() if args.commit_body_file else None

    print(f"{repo}#{args.pr}: branch {branch} {tip[:10]} -> new commit on {base}@{base_sha[:10]}")
    for repo_path, contents in additions:
        print(f"  add    {repo_path} ({len(base64.b64decode(contents))} bytes)")
    for repo_path in args.delete:
        print(f"  delete {repo_path}")
    if args.dry_run:
        print("dry run: nothing changed")
        return 0

    tmp = f"flood3-tmp/{repo}-pr{args.pr}-{int(time.time())}"
    osp.create_branch(owner, repo, tmp, base_sha)
    try:
        oid = osp.create_signed_commit(owner, repo, tmp, args.message, additions, base_sha, deletions=args.delete or None, commit_body=body)
        now = branch_tip(owner, repo, branch)
        if now != args.expect_tip:
            print(f"REFUSED: {branch} moved to {now} while the commit was being built; new commit {oid} left unreferenced")
            return 1
        osp.gh(["api", "-X", "PATCH", f"repos/{owner}/{repo}/git/refs/heads/{branch}", "-f", f"sha={oid}", "-F", "force=true"])
    except osp.GhError as exc:
        print(f"FAILED: {exc}")
        return 2
    finally:
        try:
            osp.gh(["api", "-X", "DELETE", f"repos/{owner}/{repo}/git/refs/heads/{tmp}"])
        except osp.GhError as exc:
            print(f"warning: could not delete temporary branch {tmp}: {exc}")
    after = branch_tip(owner, repo, branch)
    print(f"RESET {repo}#{args.pr}: {branch} now {after} (signed commit {oid}; base {base_sha[:10]})")
    return 0 if after == oid else 2


if __name__ == "__main__":
    sys.exit(main())
