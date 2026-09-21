#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

Move (add + delete) a file on an EXISTING branch of a sibling repo, in ONE GitHub-signed commit.

WHY THIS EXISTS
---------------
`util/open_signed_pr.py` supports `--delete` but refuses when the branch already exists.
`util/ad-hoc/2026-09-08_append_signed_commit.py` appends to an existing branch but has **no
delete verb**. A misplaced file on an open PR falls between the two.

The Contents REST API (`PUT`/`DELETE /repos/.../contents/...`) is NOT an option: only the
GraphQL `createCommitOnBranch` mutation produces a GitHub-SIGNED commit. All nine Juniper repos
carry `required_signatures`, and an unsigned commit anywhere in a branch's history blocks the
merge with every check GREEN and nothing naming the cause. So this reuses the same mutation.

It pins `expectedHeadOid` to the branch's current head, so a concurrent push fails loudly
rather than being clobbered.

Usage:
    python3 2026-09-21_signed_move_on_branch.py \\
        --repo juniper-recurrence --branch my-branch \\
        --add /local/file.py:new/repo/path.py \\
        --delete old/repo/path.py \\
        --headline "..." [--body "..."] [--owner pcalnon] [--dry-run]
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

MUTATION = """mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid url } }
}"""


def gh(args: list[str], stdin: str | None = None) -> str:
    p = subprocess.run(["gh", *args], capture_output=True, text=True, input=stdin)
    if p.returncode != 0:
        print(p.stderr.strip(), file=sys.stderr)
        raise SystemExit(2)
    return p.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--add", action="append", default=[], metavar="LOCAL:REPOPATH")
    ap.add_argument("--delete", action="append", default=[], metavar="REPOPATH")
    ap.add_argument("--headline", required=True)
    ap.add_argument("--body", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not a.add and not a.delete:
        print("ERROR: nothing to do -- pass --add and/or --delete")
        return 2

    nwo = f"{a.owner}/{a.repo}"
    head = gh(["api", f"repos/{nwo}/git/ref/heads/{a.branch}", "--jq", ".object.sha"])
    print(f"{nwo}:{a.branch} head = {head}")

    additions = []
    for spec in a.add:
        local, _, repo_path = spec.partition(":")
        data = Path(local).read_bytes()
        additions.append({"path": repo_path, "contents": base64.b64encode(data).decode()})
        print(f"  + {repo_path}  ({len(data)} bytes)")
    deletions = [{"path": p} for p in a.delete]
    for p in a.delete:
        print(f"  - {p}")

    payload = {
        "query": MUTATION,
        "variables": {"input": {
            "branch": {"repositoryNameWithOwner": nwo, "branchName": a.branch},
            "expectedHeadOid": head,
            "message": {"headline": a.headline, "body": a.body},
            "fileChanges": {"additions": additions, "deletions": deletions},
        }},
    }

    if a.dry_run:
        print("(dry run)")
        return 0

    out = gh(["api", "graphql", "--input", "-"], stdin=json.dumps(payload))
    result = json.loads(out)
    if "errors" in result:
        print(json.dumps(result["errors"], indent=2))
        return 2
    commit = result["data"]["createCommitOnBranch"]["commit"]
    print(f"signed commit {commit['oid'][:12]}  {commit['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
