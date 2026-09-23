#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_push_signed_commit.py
# Author:        Paul Calnon
#
# Date Created:  2026-09-22
# Last Modified: 2026-09-22
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Status:        ad-hoc -- one-off
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       juniper-canopy#650, juniper-ml#1966
# Superseded:    for new use by util/push_signed_commit.py (append to an existing branch) and util/open_signed_pr.py (create a branch); RETAINED here as provenance.
#
# Description:
#    Push a SIGNED commit (additions + deletions) to a new branch via GitHub's GraphQL
#    `createCommitOnBranch`, then leave the branch ready for a PR.
#
#    Why GraphQL rather than git or the REST contents API:
#      * Every Juniper repo enforces `required_signatures`. An UNSIGNED commit blocks the merge with
#        every check green and nothing naming the cause, and the repair force-resets the branch,
#        which closes the PR.
#      * Local `git commit -S` HANGS headless (gpg pinentry has no tty).
#      * REST `PUT /contents` does NOT sign. Only `createCommitOnBranch` does.
#
#    It also refuses to run from a dirty assumption: the expected head OID is read immediately
#    before the commit and passed as `expectedHeadOid`, so a concurrent push fails this rather than
#    silently building on a head that moved.
#
#    Usage:
#      python3 util/ad-hoc/2026-09-22_push_signed_commit.py \
#          --repo pcalnon/juniper-canopy --branch fix/my-branch \
#          --src-dir /path/with/edited/files \
#          --add pyproject.toml --add .github/workflows/ci.yml \
#          --delete conf/requirements_bak.txt \
#          --title "fix(ci): ..." --body-file /path/to/commit_message_body.txt
#####################################################################################################################################################################################################

from __future__ import annotations

import argparse
import base64
import json
import subprocess
from pathlib import Path

GRAPHQL = """
mutation ($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) {
    commit { oid url signature { isValid state } }
  }
}
"""


def gh(args: list[str], stdin: str | None = None) -> str:
    r = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"gh {' '.join(args[:3])} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--base", default="main")
    ap.add_argument("--src-dir", required=True)
    ap.add_argument("--add", action="append", default=[])
    ap.add_argument("--delete", action="append", default=[])
    ap.add_argument("--title", required=True)
    ap.add_argument("--body-file", required=True)
    a = ap.parse_args()

    src = Path(a.src_dir)
    owner, name = a.repo.split("/")

    base_sha = gh(["api", f"repos/{a.repo}/commits/{a.base}", "-q", ".sha"])
    print(f"base {a.base} = {base_sha}")

    # Create the branch if it does not already exist.
    existing = subprocess.run(
        ["gh", "api", f"repos/{a.repo}/git/ref/heads/{a.branch}", "-q", ".object.sha"],
        capture_output=True, text=True,
    )
    if existing.returncode == 0:
        head = existing.stdout.strip()
        print(f"branch {a.branch} already exists at {head}")
    else:
        gh(["api", f"repos/{a.repo}/git/refs", "-X", "POST",
            "-f", f"ref=refs/heads/{a.branch}", "-f", f"sha={base_sha}"])
        head = base_sha
        print(f"created branch {a.branch} at {head}")

    additions = []
    for rel in a.add:
        p = src / rel
        if not p.is_file():
            raise SystemExit(f"ABORT: addition missing from --src-dir: {rel}")
        additions.append({
            "path": rel,
            "contents": base64.b64encode(p.read_bytes()).decode("ascii"),
        })
    deletions = [{"path": rel} for rel in a.delete]

    body = Path(a.body_file).read_text(encoding="utf-8")

    variables = {
        "input": {
            "branch": {
                "repositoryNameWithOwner": f"{owner}/{name}",
                "branchName": a.branch,
            },
            "message": {"headline": a.title, "body": body},
            "expectedHeadOid": head,
            "fileChanges": {"additions": additions, "deletions": deletions},
        }
    }

    print(f"committing {len(additions)} addition(s), {len(deletions)} deletion(s)")
    out = gh(
        ["api", "graphql", "-f", f"query={GRAPHQL}", "--input", "-"],
        stdin=json.dumps({"query": GRAPHQL, "variables": variables}),
    )
    data = json.loads(out)
    if "errors" in data:
        raise SystemExit(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
    commit = data["data"]["createCommitOnBranch"]["commit"]
    print(f"commit  {commit['oid']}")
    print(f"url     {commit['url']}")
    print(f"signed  isValid={commit['signature']['isValid']} state={commit['signature']['state']}")
    if not commit["signature"]["isValid"]:
        raise SystemExit("ABORT: commit is not validly signed; required_signatures will block the merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
