#!/usr/bin/env python3
"""Append one GitHub-signed commit to an EXISTING branch that already has an open PR.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-10

Why this exists
---------------
``util/open_signed_pr.py`` is the sanctioned signed-commit path (GPG/YubiKey signing is
unavailable headless, and ``required_signatures`` blocks an unsigned commit anywhere in a
branch's history). But it carries a DUP-GUARD that refuses when the branch already has an
open PR -- correct for its job, and it means there is no supported way to push a follow-up
commit to a PR already in flight.

That came up landing ml#1884: the per-PR symbol-loss screen flagged two deliberately
renamed test methods, and the fix is an enumerated ``Allow-Symbol-Loss:`` commit trailer,
which must appear in a commit inside the PR's ``base..HEAD`` range -- i.e. a second commit
on a branch whose PR is already open.

This reuses ``open_signed_pr``'s own ``create_signed_commit`` rather than reimplementing the
mutation, so both paths produce identical commits. ``expectedHeadOid`` is read live from the
branch, so a concurrent push fails the mutation instead of silently clobbering.

Usage
-----
    python3 util/ad-hoc/2026-09-10_soak_stopping_rule/append_signed_commit.py \\
        --branch fix/soak-stopping-rule-fails-open \\
        --add tests/test_foo.py:tests/test_foo.py \\
        --message "test(soak): ..." --commit-body-file BODY.txt

If this is needed a third time it should graduate to ``util/`` proper -- most likely as a
``--allow-existing-pr`` flag on ``open_signed_pr.py`` rather than as a separate script.
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import pathlib
import subprocess  # nosec B404 - fixed argv, no shell
import sys

HERE = pathlib.Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]


def _load_open_signed_pr():
    """Import util/open_signed_pr.py by path; it is a script, not an importable module."""
    target = REPO_ROOT / "util" / "open_signed_pr.py"
    spec = importlib.util.spec_from_file_location("open_signed_pr", target)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {target}")
    mod = importlib.util.module_from_spec(spec)
    # Register BEFORE exec_module: a @dataclass in a path-loaded module resolves its own
    # __module__ through sys.modules and dies at import time otherwise.
    sys.modules["open_signed_pr"] = mod
    spec.loader.exec_module(mod)
    return mod


def branch_head_oid(owner: str, repo: str, branch: str) -> str:
    out = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", "api", f"repos/{owner}/{repo}/git/ref/heads/{branch}"],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)["object"]["sha"]


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", default="juniper-ml")
    ap.add_argument("--branch", required=True)
    ap.add_argument("--add", action="append", default=[], metavar="LOCAL:REPOPATH")
    ap.add_argument("--delete", action="append", default=[], metavar="REPOPATH",
                    help="remove a path in the same commit (repeatable)")
    ap.add_argument("--message", required=True)
    ap.add_argument("--commit-body-file", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    osp = _load_open_signed_pr()

    # TUPLES, not dicts. `create_signed_commit` does `for path, contents in additions`,
    # and iterating a dict yields its KEYS -- so passing [{"path": p, "contents": c}]
    # unpacks to path="path", contents="contents" and lands a file literally named
    # `path` whose body is base64-decoded "contents" (binary junk), while the file you
    # meant to commit is never written. That happened on ml#1884's waiver commit
    # (12a53757) and is why the assertion below exists: the mutation succeeds either
    # way, so nothing fails until CI's end-of-file-fixer trips on a stray `path`.
    additions: list[tuple[str, str]] = []
    for spec in args.add:
        local, _, repopath = spec.partition(":")
        if not repopath:
            raise SystemExit(f"--add needs LOCAL:REPOPATH, got {spec!r}")
        data = pathlib.Path(local).read_bytes()
        additions.append((repopath, base64.b64encode(data).decode("ascii")))
    if not additions and not args.delete:
        raise SystemExit("nothing to commit: pass at least one --add or --delete")
    for item in additions:
        if not (isinstance(item, tuple) and len(item) == 2):
            raise SystemExit(f"addition must be a (repo_path, b64) tuple, got {item!r}")

    body = None
    if args.commit_body_file:
        body = pathlib.Path(args.commit_body_file).read_text(encoding="utf-8")

    head = branch_head_oid(args.owner, args.repo, args.branch)
    print(f"branch {args.branch} head {head[:12]}")
    print(f"adding {len(additions)} file(s): {[p for p, _ in additions]}")
    if args.delete:
        print(f"deleting {len(args.delete)} path(s): {args.delete}")
    if args.dry_run:
        print("(dry run -- nothing written)")
        return 0

    oid = osp.create_signed_commit(
        args.owner, args.repo, args.branch, args.message,
        additions, head, deletions=args.delete or None, commit_body=body,
    )
    print(f"signed commit {oid[:12]} on {args.owner}/{args.repo}:{args.branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
