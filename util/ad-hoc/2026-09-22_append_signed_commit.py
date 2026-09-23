#!/usr/bin/env python3
"""Append a GitHub-signed commit to a branch that already has an open PR.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-09-22
Status:      ad-hoc -- cross-repo tooling
Retire when: promote to util/ if it is wanted a second time; otherwise RETAINED as provenance
Related:     util/open_signed_pr.py (the reference implementation; its DUP-GUARD is why this exists)
Superseded:  for new use by util/push_signed_commit.py -- the util/ promotion "Retire when" asked for; RETAINED here as provenance (owner policy 2026-08-25).

`util/open_signed_pr.py` opens a branch, a signed commit and a PR in one call, and refuses to run
when an open PR already exists for the branch -- correctly, because re-running it is almost always
a mistake. But a validation round that reports *after* the PR is open needs exactly one more signed
commit on that same branch, and `git commit` cannot supply one: the repos require
`required_signatures`, GPG/YubiKey signing is unavailable headless, and an unsigned commit anywhere
in the history blocks the merge with every check green.

So this does the one thing `open_signed_pr.py` will not: a GraphQL `createCommitOnBranch` against
an existing branch, which GitHub signs.

Whole-file uploads, like `open_signed_pr.py` -- so name ONLY the paths you changed. A path listed
here overwrites whatever is on the branch, including another session's work.

Usage:
    python3 util/ad-hoc/2026-09-22_append_signed_commit.py --branch <b> \\
        --message '<headline>' [--body '<body>'] --add <repo/path> [--add ...] [--dry-run]
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
from pathlib import Path

OWNER = "pcalnon"
REPO = "juniper-ml"

MUTATION = """
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid url } }
}
"""


def gh_json(args: list[str]) -> dict:
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed:\n{out.stderr.strip()}")
    return json.loads(out.stdout or "{}")


def head_oid(branch: str) -> str:
    data = gh_json(["api", f"repos/{OWNER}/{REPO}/git/ref/heads/{branch}"])
    return data["object"]["sha"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument("--body", default="")
    ap.add_argument("--add", action="append", default=[], metavar="REPO/PATH")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.add:
        raise SystemExit("--add is required (whole-file upload; name only what you changed)")

    additions = []
    for rel in args.add:
        p = Path(rel)
        if not p.is_file():
            raise SystemExit(f"no such file: {rel}")
        blob = p.read_bytes()
        additions.append({"path": rel, "contents": base64.b64encode(blob).decode("ascii")})
        print(f"  add {rel} ({len(blob):,} bytes)")

    oid = head_oid(args.branch)
    print(f"  branch {args.branch} @ {oid}")

    if args.dry_run:
        print("  (dry run; nothing written)")
        return 0

    # `gh api graphql --input -` wants ONE JSON object carrying both the query and the
    # variables; combining `-f query=…` with `--input -` is rejected ("A query attribute must
    # be specified and must be a string"). The file contents are far too large for argv, so
    # stdin is the only viable channel.
    payload = {
        "query": MUTATION,
        "variables": {
            "input": {
                "branch": {
                    "repositoryNameWithOwner": f"{OWNER}/{REPO}",
                    "branchName": args.branch,
                },
                "expectedHeadOid": oid,
                "message": {"headline": args.message, "body": args.body},
                "fileChanges": {"additions": additions},
            }
        },
    }
    out = subprocess.run(
        ["gh", "api", "graphql", "--input", "-"],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise SystemExit(f"createCommitOnBranch failed:\n{out.stderr.strip()}\n{out.stdout.strip()}")
    data = json.loads(out.stdout)
    commit = data["data"]["createCommitOnBranch"]["commit"]
    print(f"\nsigned commit {commit['oid'][:12]} -> {commit['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
