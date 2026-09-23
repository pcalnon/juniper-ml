"""
Add ONE GitHub-signed commit to an EXISTING branch of any Juniper repo, pinned to the head you built on.

Project: juniper-ml
Sub-Project: cross-repo tooling
Author: Paul Calnon
Created: 2026-09-22
Status: permanent utility (promoted from util/ad-hoc/ -- see "Lineage" below)
Related: util/open_signed_pr.py (the new-branch sibling; this reuses its ``gh``, ``parse_add`` and
         ``create_signed_commit`` instead of carrying a copy of the mutation),
         util/ad-hoc/push_signed_commit.py (the ad-hoc driver that pinned the head; this generalises it)

Why this exists
---------------
``required_signatures`` is on in all 9 Juniper repos, and a local ``git commit`` hangs in a headless
session: the signing key is a YubiKey that needs a physical touch. The only headless path to a signed
commit is the GraphQL ``createCommitOnBranch`` mutation, which GitHub signs. REST ``PUT /contents``
creates an UNSIGNED commit, and an unsigned commit anywhere in a branch's history blocks the merge with
every check green and nothing naming the cause.

``util/open_signed_pr.py`` covers "new branch + PR" and deliberately REFUSES a branch that already
exists. Nothing promoted covered the other half -- one more commit on an open PR: a CI fix-up, a review
change, a sequence-safety waiver trailer. So ad-hoc drivers multiplied under ``util/ad-hoc/``, several
re-implementing the mutation and almost all of them reading ``expectedHeadOid`` LIVE from the branch.

Why the head is PINNED, not read live
-------------------------------------
Every ``--add`` uploads the WHOLE file. A driver that reads the branch head just before committing keeps
GitHub's guard against a push landing in the next few hundred milliseconds, and throws away the one that
matters: a push that landed while you were EDITING. The upload then silently reverts it. Pass the head
your edits are based on as ``--expected-head``; if the branch has moved since, this refuses. The
mutation's ``expectedHeadOid`` is that same pinned sha -- never a fresh read -- so a push that races the
commit itself is refused by GitHub as well.

Usage
-----
    python util/push_signed_commit.py \\
        --repo juniper-canopy \\
        --branch fix/some-branch \\
        --expected-head <FULL 40-char sha of the branch head your edits are based on> \\
        --add /local/path/file.py:src/path/file.py \\
        --message "fix(x): the follow-up" \\
        [--add ...] [--delete REPOPATH ...] [--commit-body TEXT | --commit-body-file FILE] \\
        [--owner pcalnon] [--dry-run]

Take the full sha from ``gh pr view <N> --repo pcalnon/<repo> --json headRefOid --jq .headRefOid``, or
from ``git rev-parse origin/<branch>`` right after a fetch. ``--add`` (LOCAL_PATH:REPO_PATH) and
``--delete`` (REPO_PATH) are repeatable; at least one is required, and no repo path may be named twice.
Waiver trailers (``Allow-Symbol-Loss:`` ...) belong in the commit BODY -- see ``create_signed_commit``.

Exit 0 = commit landed and read back clean (or --dry-run), 1 = refused (nothing written), 2 = hard
error: a usage error, a failed API call, or a commit that LANDED but did not read back as sent.

Safety contract
---------------
* ``--expected-head`` must be the FULL 40-hex sha; an abbreviation is refused before any API call.
  GitHub does not expand one: this tool would report a branch that never moved as moved, and
  ``PUT .../pulls/N/update-branch`` answers ``expected_head_sha=<short>`` with 422 "expected head sha
  didn't match current head ref" (observed 2026-09-07 on juniper-ml#1819) -- both read like a lost race
  when nothing raced.
* Refuses (exit 1) a branch that does not exist -- creating one is ``open_signed_pr.py``'s job -- and the
  repo's DEFAULT branch: this tool adds commits to PR branches, and a commit made straight onto the
  default branch skips review and CI, which server-side rules may not stop for an actor on a ruleset's
  bypass list. Only a 404 reads as "does not exist"; any other failed read is a hard error.
* Refuses (exit 1) when the branch head is not ``--expected-head``.
* After committing, reads back at the new commit: the branch head IS the new commit, the commit is
  verified (signed) and sits directly on ``--expected-head``, every added path holds exactly the bytes
  sent (compared as git blob shas, so file size does not matter), and every deleted path is gone. Any
  failure exits 2 and names the commit that landed.
* ``--dry-run`` performs the read-only resolution -- default branch, branch head, pin check -- and prints
  the plan; it creates no commit.

Lineage
-------
Promoted 2026-09-22. Each ad-hoc existing-branch driver under ``util/ad-hoc/`` now carries a line naming
this file as its replacement for new use. They are RETAINED as provenance under the owner policy of
2026-08-25 (``util/ad-hoc/README.md`` section "Lifecycle"); retiring any of them is an owner decision.

Tests: ``tests/test_push_signed_commit.py`` (hermetic; ``gh`` is a PATH stub that enforces
``expectedHeadOid`` the way GitHub does). ``util/`` is not covered by the pre-commit Python hooks, so that
suite is the gate.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
from urllib.parse import quote

_UTIL_DIR = os.path.dirname(os.path.abspath(__file__))
if _UTIL_DIR not in sys.path:
    sys.path.insert(0, _UTIL_DIR)

import open_signed_pr as osp  # noqa: E402  (util/ is not a package; sibling import by path)

FULL_SHA = re.compile(r"[0-9a-f]{40}")


def full_sha(value: str) -> str:
    """``argparse`` type for ``--expected-head``: the FULL 40-hex sha, lower-cased."""
    sha = value.strip().lower()
    if FULL_SHA.fullmatch(sha):
        return sha
    raise argparse.ArgumentTypeError(f"needs the FULL 40-character sha, got {value!r} ({len(value.strip())} characters). GitHub does not expand an abbreviation, so a short sha reads as a moved branch here and as a 422 'expected head sha didn't match' from update-branch -- a lost race that never happened. Take it from `gh pr view <N> --json headRefOid` or `git rev-parse origin/<branch>` after a fetch.")


def _url_path(path: str) -> str:
    """Quote a branch name or repo path for a REST URL path; ``/`` stays literal."""
    return quote(path, safe="/")


def _gh_read(args: list) -> "tuple[int, str, str]":
    """A READ-ONLY ``gh`` call keeping exit code, stdout AND stderr, so a 404 can be told from an outage."""
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _is_not_found(stderr: str) -> bool:
    return "HTTP 404" in stderr


def git_blob_sha(raw: bytes) -> str:
    """The sha git gives a file holding exactly these bytes -- what ``git hash-object`` prints."""
    return hashlib.sha1(b"blob %d\x00" % len(raw) + raw, usedforsecurity=False).hexdigest()


def default_branch(owner: str, repo: str) -> str:
    name = osp.gh(["api", f"repos/{owner}/{repo}", "--jq", ".default_branch"]).strip()
    if not name:
        raise osp.GhError(f"could not resolve the default branch of {owner}/{repo}")
    return name


def branch_head(owner: str, repo: str, branch: str) -> "str | None":
    """The branch's live head sha; None ONLY when the ref 404s.

    Any other failure raises. An outage or an auth error is not "the branch does not exist", and
    reporting it as one would send the operator off to create a branch that is already there.
    """
    rc, out, err = _gh_read(["api", f"repos/{owner}/{repo}/git/ref/heads/{_url_path(branch)}", "--jq", ".object.sha"])
    if rc != 0:
        if _is_not_found(err):
            return None
        raise osp.GhError(f"reading {owner}/{repo}:{branch} -> exit {rc}\n{err.strip()}")
    sha = out.strip()
    if not FULL_SHA.fullmatch(sha):
        raise osp.GhError(f"reading {owner}/{repo}:{branch} returned {sha!r}, not a sha")
    return sha


def read_back(owner: str, repo: str, branch: str, oid: str, parent: str, sent: dict, deleted: list) -> list:
    """Re-read what was just written, at the new commit. Returns the problems found (empty = clean)."""
    problems = []

    rc, out, err = _gh_read(["api", f"repos/{owner}/{repo}/git/ref/heads/{_url_path(branch)}", "--jq", ".object.sha"])
    head = out.strip() if rc == 0 else f"<unreadable: {err.strip()}>"
    if head == oid:
        print(f"  verified head      {branch} -> {oid}")
    else:
        problems.append(f"branch head is {head}, not the new commit {oid}: the ref did not move to it, or something moved it since")

    rc, out, err = _gh_read(["api", f"repos/{owner}/{repo}/git/commits/{oid}", "--jq", "{verified: .verification.verified, reason: .verification.reason, parents: [.parents[].sha]}"])
    try:
        commit = json.loads(out) if rc == 0 else {}
    except ValueError:
        commit = {}
    if not isinstance(commit, dict):
        commit = {}
    if commit.get("verified") is True:
        print(f"  verified signature (reason={commit.get('reason')})")
    else:
        reason = commit.get("reason") or err.strip() or "unreadable"
        problems.append(f"commit {oid} is NOT verified (reason={reason}); required_signatures will block the merge")
    parents = commit.get("parents")
    if parents == [parent]:
        print(f"  verified parent    {parent}")
    else:
        problems.append(f"commit {oid} has parents {parents}, not exactly [{parent}]")

    for repo_path, raw in sent.items():
        want = git_blob_sha(raw)
        rc, out, err = _gh_read(["api", f"repos/{owner}/{repo}/contents/{_url_path(repo_path)}?ref={oid}", "--jq", ".sha"])
        got = out.strip() if rc == 0 else f"<unreadable: {err.strip()}>"
        if got == want:
            print(f"  verified {repo_path} (blob {want[:12]}, {len(raw)} bytes)")
        else:
            problems.append(f"{repo_path}: the blob at {oid[:12]} is {got}, but the bytes sent hash to {want}")

    for repo_path in deleted:
        rc, out, err = _gh_read(["api", f"repos/{owner}/{repo}/contents/{_url_path(repo_path)}?ref={oid}", "--jq", ".sha"])
        if rc != 0 and _is_not_found(err):
            print(f"  verified {repo_path} is gone")
        elif rc == 0:
            problems.append(f"{repo_path}: still present at {oid[:12]} after the deletion")
        else:
            problems.append(f"{repo_path}: could not confirm it is gone ({err.strip()})")

    return problems


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True, help="the EXISTING branch to add the commit to (never the default branch)")
    ap.add_argument("--expected-head", required=True, type=full_sha, metavar="SHA", help="FULL 40-char sha the branch must still be at: the head your edits are based on")
    ap.add_argument("--add", action="append", default=[], type=osp.parse_add, metavar="LOCAL:REPOPATH", help="upload a WHOLE local file to REPOPATH (repeatable)")
    ap.add_argument("--delete", action="append", default=[], metavar="REPOPATH", help="repo path to delete in the same commit (repeatable)")
    ap.add_argument("--message", required=True, help="commit headline")
    ap.add_argument("--commit-body", default=None, help="commit message BODY -- sequence-safety waiver trailers (Allow-Symbol-Loss: ...) go here, not in the PR description; the trailer must survive the squash-merge")
    ap.add_argument("--commit-body-file", default=None, help="read the commit message body from a file (mutually exclusive with --commit-body)")
    ap.add_argument("--dry-run", action="store_true", help="resolve and check read-only, print the plan, write nothing")
    args = ap.parse_args(argv)

    if not args.add and not args.delete:
        print("ERROR: nothing to commit -- pass at least one --add or --delete.", file=sys.stderr)
        return 2
    named = [repo_path for _local, repo_path in args.add] + list(args.delete)
    twice = sorted({path for path in named if named.count(path) > 1})
    if twice:
        print(f"ERROR: repo path(s) named more than once across --add/--delete: {', '.join(twice)}", file=sys.stderr)
        return 2
    if args.commit_body is not None and args.commit_body_file is not None:
        print("ERROR: --commit-body and --commit-body-file are mutually exclusive", file=sys.stderr)
        return 2
    commit_body = args.commit_body
    if args.commit_body_file is not None:
        try:
            with open(args.commit_body_file, encoding="utf-8") as fh:
                commit_body = fh.read()
        except OSError as exc:
            print(f"ERROR: cannot read --commit-body-file {args.commit_body_file}: {exc}", file=sys.stderr)
            return 2

    additions = []
    sent = {}
    for local, repo_path in args.add:
        try:
            with open(local, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"ERROR: cannot read {local}: {exc}", file=sys.stderr)
            return 2
        # (repo_path, base64) TUPLES, which is what create_signed_commit unpacks. A dict here is
        # unpacked into its KEYS and lands a file literally named `path` -- the failure recorded in
        # util/ad-hoc/push_signed_commit.py's docstring; the read-back below would also catch it.
        additions.append((repo_path, base64.b64encode(raw).decode("ascii")))
        sent[repo_path] = raw

    slug = f"{args.owner}/{args.repo}"
    try:
        default = default_branch(args.owner, args.repo)
        if args.branch == default:
            print(f"REFUSED: {args.branch} is the default branch of {slug}. This tool adds commits to PR branches; open one with util/open_signed_pr.py.", file=sys.stderr)
            return 1
        head = branch_head(args.owner, args.repo, args.branch)
    except (osp.GhError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if head is None:
        print(f"REFUSED: branch {args.branch} does not exist on {slug}. Creating a branch is util/open_signed_pr.py's job.", file=sys.stderr)
        return 1
    if head != args.expected_head:
        print(f"REFUSED: {slug}:{args.branch} is at {head}, not the pinned --expected-head {args.expected_head}. Something landed after the head your edits are based on: sync, re-apply your edits on top of it, and re-run with the new head.", file=sys.stderr)
        return 1

    print(f"{'DRY-RUN ' if args.dry_run else ''}{slug}:{args.branch} @ {head} (== --expected-head)")
    for repo_path, raw in sent.items():
        print(f"  add    {repo_path} ({len(raw)} bytes)")
    for repo_path in args.delete:
        print(f"  delete {repo_path}")
    print(f"  commit {args.message}")
    if commit_body:
        print("  commit body:")
        for line in commit_body.splitlines():
            print(f"    {line}")
    if args.dry_run:
        print("  (nothing written)")
        return 0

    try:
        oid = osp.create_signed_commit(
            args.owner,
            args.repo,
            args.branch,
            args.message,
            additions,
            expected_head_oid=args.expected_head,
            deletions=args.delete or None,
            commit_body=commit_body,
        )
    except (osp.GhError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"No commit is known to have landed, but a request that timed out can still land one: re-read {slug}:{args.branch} (it was {args.expected_head}) before retrying.", file=sys.stderr)
        return 2
    print(f"signed commit {oid} on {slug}:{args.branch}")

    problems = read_back(args.owner, args.repo, args.branch, oid, args.expected_head, sent, args.delete)
    if problems:
        for problem in problems:
            print(f"  VERIFY FAIL {problem}", file=sys.stderr)
        print(f"VERIFY FAILED ({len(problems)} problem(s)): commit {oid} LANDED on {slug}:{args.branch} but did not read back as sent. Inspect it before building on it.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
