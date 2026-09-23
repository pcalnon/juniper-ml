#!/usr/bin/env python3
"""Add ONE GitHub-signed commit to an EXISTING branch of any Juniper repo (createCommitOnBranch).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — wip (candidate for promotion next to util/open_signed_pr.py, with a hermetic test like tests/test_open_signed_pr.py)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/open_signed_pr.py (whose ``create_signed_commit`` this reuses verbatim); canopy#601 (the first PR it added a fix-up to)
Superseded: for new use by util/push_signed_commit.py, its promoted form (the same required --expected-head, plus a FULL-sha check, a default-branch refusal and a signature/parent read-back); RETAINED here as provenance.

Why this exists
---------------
``util/open_signed_pr.py`` opens a branch + signed commit + PR in one go and, by its safety
contract, REFUSES a branch that already exists. That leaves no way to land a follow-up commit on
a PR it opened -- a CI fix-up, a review change -- when the session cannot sign locally (the
signing subkey lives on a YubiKey that needs a touch; ``gpg: signing failed: Timeout``). This
script fills exactly that gap: it sends whole-file additions to an existing branch as one
GitHub-signed commit, pinned to ``--expected-head`` so a concurrent push fails loudly rather
than clobbering.

Like the helper it reuses, it sends WHOLE FILE contents: anything merged to those paths on the
branch since your worktree was synced is silently reverted. Sync and re-check the branch head
immediately before running, not when you start editing.

Usage
-----
    python util/ad-hoc/push_signed_commit.py \
        --repo juniper-canopy --branch fix/some-branch \
        --expected-head <full sha of the branch head you built on> \
        --add /local/path/file.py:src/path/file.py [--add ...] [--delete repo/path] \
        --message "headline" [--commit-body-file body.txt] [--dry-run]

Why it reads back what it wrote
-------------------------------
``create_signed_commit`` takes ``additions`` as ``(repo_path, base64_contents)`` TUPLES.
A caller that passes dicts instead gets its dict UNPACKED INTO ITS KEYS, and the commit
then writes a file literally named ``path`` containing ``base64.b64decode("contents")``
-- while never uploading the real file at all. It prints ``signed commit <sha>`` and looks
like a success. That happened on **nine branches** in one session (juniper-ml#1835), and
what eventually caught it was a pre-commit ``end-of-file-fixer`` tripping over the stray
binary, not anything that understood the problem.

This script builds tuples correctly and never had that bug. It verifies anyway, because
the failure mode is silent by construction: a write tool that cannot confirm its own write
will eventually report a success it did not achieve. After committing it re-reads every
added path from the branch and compares bytes, and confirms every deleted path is gone.

Exit 0 = commit landed and verified (or --dry-run), 1 = refused (head moved / branch
missing), 2 = hard error, INCLUDING "the commit landed but its content is wrong".
"""

from __future__ import annotations

import argparse
import base64
import os
import sys

_UTIL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _UTIL_DIR)

import open_signed_pr as osp  # noqa: E402  (util/ is not a package; sibling import by path)


def _branch_head(owner: str, repo: str, branch: str) -> str:
    out = osp.gh(["api", f"/repos/{owner}/{repo}/git/ref/heads/{branch}", "--jq", ".object.sha"], check=False)
    return (out or "").strip()


def _blob_at(owner: str, repo: str, ref: str, repo_path: str) -> "bytes | None":
    """Raw bytes of ``repo_path`` at ``ref``; None when the API returns nothing.

    ``ref`` goes in the QUERY STRING, not through ``-f``: ``gh api`` switches the request
    to POST as soon as any ``-f`` parameter is present, and the contents endpoint rejects
    that -- so an ``-f ref=`` read fails on a commit that is perfectly fine, and a verifier
    built that way accuses every path it checks.
    """
    out = osp.gh(["api", "-X", "GET", f"/repos/{owner}/{repo}/contents/{repo_path}?ref={ref}", "--jq", ".content"], check=False)
    if not (out or "").strip():
        return None
    return base64.b64decode(out.strip())


def _verify(owner: str, repo: str, branch: str, wanted: dict, deleted: list) -> int:
    """Re-read what was just written. Returns the number of paths that are wrong."""
    bad = 0
    for repo_path, raw in wanted.items():
        got = _blob_at(owner, repo, branch, repo_path)
        if got is None:
            print(f"  VERIFY FAIL {repo_path}: not readable on the branch after the commit", file=sys.stderr)
            bad += 1
        elif got != raw:
            print(f"  VERIFY FAIL {repo_path}: branch has {len(got)} bytes, expected {len(raw)}", file=sys.stderr)
            bad += 1
        else:
            print(f"  verified {repo_path} ({len(raw)} bytes)")
    for repo_path in deleted:
        if _blob_at(owner, repo, branch, repo_path) is not None:
            print(f"  VERIFY FAIL {repo_path}: still present after deletion", file=sys.stderr)
            bad += 1
        else:
            print(f"  verified {repo_path} is gone")
    return bad


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--owner", default="pcalnon")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--expected-head", required=True, help="full sha the branch MUST still be at (the head you built on)")
    parser.add_argument("--add", action="append", default=[], type=osp.parse_add, metavar="LOCAL:REPOPATH")
    parser.add_argument("--delete", action="append", default=[], metavar="REPOPATH")
    parser.add_argument("--message", required=True, help="commit headline")
    parser.add_argument("--commit-body-file", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-verify", action="store_true", help="skip the post-commit read-back (you almost never want this)")
    args = parser.parse_args(argv)

    if not args.add and not args.delete:
        print("ERROR: nothing to commit -- give at least one --add or --delete", file=sys.stderr)
        return 2

    additions = []
    wanted = {}
    for local, repo_path in args.add:
        try:
            with open(local, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"ERROR: cannot read {local}: {exc}", file=sys.stderr)
            return 2
        additions.append((repo_path, base64.b64encode(raw).decode("ascii")))
        wanted[repo_path] = raw

    commit_body = None
    if args.commit_body_file:
        try:
            with open(args.commit_body_file, encoding="utf-8") as fh:
                commit_body = fh.read()
        except OSError as exc:
            print(f"ERROR: cannot read --commit-body-file {args.commit_body_file}: {exc}", file=sys.stderr)
            return 2

    head = _branch_head(args.owner, args.repo, args.branch)
    if not head:
        print(f"REFUSED: branch {args.branch} does not exist on {args.owner}/{args.repo}", file=sys.stderr)
        return 1
    if head != args.expected_head:
        print(f"REFUSED: {args.branch} is at {head}, not the expected {args.expected_head} -- sync, re-apply, re-check", file=sys.stderr)
        return 1

    print(f"branch {args.owner}/{args.repo}:{args.branch} @ {head}")
    for repo_path, _contents in additions:
        print(f"  add     {repo_path}")
    for repo_path in args.delete:
        print(f"  delete  {repo_path}")
    print(f"  message {args.message}")
    if args.dry_run:
        print("  (dry run: nothing written)")
        return 0

    try:
        oid = osp.create_signed_commit(args.owner, args.repo, args.branch, args.message, additions, head, args.delete or None, commit_body)
    except osp.GhError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"signed commit {oid} on {args.owner}/{args.repo}:{args.branch}")

    if args.no_verify:
        return 0
    bad = _verify(args.owner, args.repo, args.branch, wanted, args.delete)
    if bad:
        print(f"VERIFY FAILED for {bad} path(s) -- a commit landed, but its CONTENT is not what was sent", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
