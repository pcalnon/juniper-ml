#!/usr/bin/env python3
"""
Append ONE GitHub-signed commit to an EXISTING branch of a sibling repo.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/open_signed_pr.py (whose createCommitOnBranch mutation this reuses);
         juniper-cascor#632 (the PR this was built to extend)
Superseded: for new use by util/push_signed_commit.py (pinned --expected-head, read-back); RETAINED here as provenance (owner policy 2026-08-25).

WHY. ``util/open_signed_pr.py`` refuses when the branch already exists -- by design,
it never force-updates a ref it did not create. But a PR that needs a SECOND signed
commit (a review found the fix incomplete; CI needs a follow-up) has no path: a local
commit is unsigned and ``required_signatures`` blocks the merge. This is the missing
verb -- the same mutation, pinned to the branch's CURRENT head so a concurrent push
fails loudly instead of being clobbered. It does not open PRs and does not create
branches.

Usage:
    python util/ad-hoc/2026-09-08_append_signed_commit.py \\
        --repo juniper-cascor --branch fix/snapshot-restore-seed-numpy-scalar \\
        --add /local/path:repo/path [--add ...] \\
        --message "fix(...): ..." [--body-file body.md] [--owner pcalnon] [--dry-run]
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_UTIL = os.path.dirname(_HERE)


def _load_open_signed_pr():
    spec = importlib.util.spec_from_file_location("_osp", os.path.join(_UTIL, "open_signed_pr.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--add", action="append", default=[], help="LOCAL_PATH:REPO_PATH (repeatable)")
    ap.add_argument("--message", required=True)
    ap.add_argument("--body-file", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if not args.add:
        print("nothing to add", file=sys.stderr)
        return 2

    osp = _load_open_signed_pr()
    additions = []
    for spec in args.add:
        local, repo_path = osp.parse_add(spec)
        with open(local, "rb") as fh:
            additions.append((repo_path, base64.b64encode(fh.read()).decode("ascii")))

    head = subprocess.run(
        ["gh", "api", f"repos/{args.owner}/{args.repo}/git/ref/heads/{args.branch}", "--jq", ".object.sha"],
        capture_output=True,
        text=True,
        check=False,
    )
    expected = head.stdout.strip()
    if head.returncode != 0 or not expected:
        print(f"REFUSED: branch {args.branch} not found on {args.owner}/{args.repo}: {head.stderr.strip()}", file=sys.stderr)
        return 1
    # Read through pathlib so the handle is closed deterministically: a bare
    # ``open(...).read()`` leaves it to the garbage collector, which CodeQL flags
    # (py/file-not-closed) and which is a real leak on any non-refcounting runtime.
    body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else None

    print(f"{'DRY-RUN ' if args.dry_run else ''}{args.owner}/{args.repo}:{args.branch} @ {expected}")
    for repo_path, contents in additions:
        print(f"  add    {repo_path} ({len(base64.b64decode(contents))} bytes)")
    print(f"  commit {args.message}")
    if args.dry_run:
        print("  (nothing written)")
        return 0
    oid = osp.create_signed_commit(args.owner, args.repo, args.branch, args.message, additions, expected, commit_body=body)
    print(f"signed commit {oid[:12]} on {args.owner}/{args.repo}:{args.branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
