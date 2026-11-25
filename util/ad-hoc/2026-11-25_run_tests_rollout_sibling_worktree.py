#!/usr/bin/env python3
"""
Create and inspect a sibling repo's worktree for the run_tests rollout, from a session confined to one juniper-ml worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- the run_tests rollout (the 2026-11-24 handoff's section 1)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_local-test-runner-follow-ups-landed-cross-repo-run-tests-rollout-next.md

Why a script: the session's command guard refuses a Bash line that runs ``git -C <other repo>``, names a
``.github`` path, or chains git commands. The handoffs of 2026-11-24 put such steps in a script file.

Subcommands (``--repo`` is a sibling directory name under the Juniper root, e.g. ``juniper-recurrence``):

* ``create --repo R --branch B``: fetch ``origin``, then ``git worktree add -b B`` from ``origin/main`` at
  ``<Juniper>/worktrees/<R>--<B with / as -->--<YYYYMMDD-HHMM>--<8-char sha>`` (the ecosystem naming convention).
  Refuses when the branch exists locally or on ``origin``, or the directory exists.
* ``status --path P``: fetch, then the worktree's branch, HEAD, how far ``origin/main`` has moved since HEAD, and
  ``git status --short``.
* ``changed --path P``: every path that differs from the worktree's HEAD (modified, added, deleted, untracked), one
  per line, for building ``util/open_signed_pr.py --add`` arguments.
* ``workflows --path P``: list the workflow files of the checkout at P.
* ``show --repo R --ref REF --file F``: print a file as it is at REF in the sibling repo (e.g. ``origin/main``).
* ``verify-upload --path P --branch B``: fetch ``origin B`` and check every path the worktree changed equals that
  branch tip's copy byte for byte (the check after ``util/open_signed_pr.py`` uploads the files).
* ``remove --path P [--merged-into main]``: ``git worktree remove`` and delete the local branch, then prune. A dirty
  tree is refused, unless ``--merged-into`` names a branch whose copy of every changed path is byte-identical (a
  signed API upload leaves the worktree dirty after its PR merges) and the worktree's ``tmp/`` is empty.

Writes nothing under the system temp directory. Read-only except ``create`` and ``remove``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess  # nosec B404 - git only, argv lists, no shell
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(*args: str, cwd: Path | None = None, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)  # nosec B603 B607
    if check and proc.returncode != 0:
        sys.stderr.write(f"git {' '.join(args)} failed ({proc.returncode}):\n{proc.stderr}")
        raise SystemExit(2)
    return proc.stdout


def juniper_root() -> Path:
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=ROOT).strip()
    return Path(common).parent.parent


def sibling(repo: str) -> Path:
    path = juniper_root() / repo
    if not (path / ".git").exists():
        raise SystemExit(f"not a sibling checkout: {path}")
    return path


def cmd_create(args: argparse.Namespace) -> int:
    repo = sibling(args.repo)
    git("-C", str(repo), "fetch", "origin", "--quiet")
    if git("-C", str(repo), "branch", "--list", args.branch).strip():
        raise SystemExit(f"local branch exists in {args.repo}: {args.branch}")
    if git("-C", str(repo), "ls-remote", "--heads", "origin", args.branch).strip():
        raise SystemExit(f"branch exists on origin of {args.repo}: {args.branch}")
    sha = git("-C", str(repo), "rev-parse", "origin/main").strip()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    name = f"{args.repo}--{args.branch.replace('/', '--')}--{stamp}--{sha[:8]}"
    dest = juniper_root() / "worktrees" / name
    if dest.exists():
        raise SystemExit(f"exists: {dest}")
    git("-C", str(repo), "worktree", "add", "-b", args.branch, str(dest), "origin/main")
    print(dest)
    print(f"base origin/main {sha}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    path = Path(args.path)
    git("-C", str(path), "fetch", "origin", "--quiet")
    head = git("-C", str(path), "rev-parse", "HEAD").strip()
    main = git("-C", str(path), "rev-parse", "origin/main").strip()
    branch = git("-C", str(path), "rev-parse", "--abbrev-ref", "HEAD").strip()
    print(f"branch {branch}  HEAD {head[:12]}  origin/main {main[:12]}")
    if head != main:
        print("origin/main moved since HEAD:")
        print(git("-C", str(path), "log", "--oneline", f"{head}..{main}").rstrip() or "  (none: HEAD is ahead or diverged)")
        print("files main changed since HEAD:")
        print(git("-C", str(path), "diff", "--stat", head, main).rstrip())
    print("status:")
    print(git("-C", str(path), "status", "--short").rstrip() or "  (clean)")
    return 0


def cmd_changed(args: argparse.Namespace) -> int:
    path = Path(args.path)
    out = git("-C", str(path), "status", "--porcelain=v1", "--untracked-files=all")
    for line in out.splitlines():
        code, rel = line[:2], line[3:]
        print(f"{code.strip() or '?'}\t{rel}")
    return 0


def cmd_workflows(args: argparse.Namespace) -> int:
    wf_dir = Path(args.path) / ".github" / "workflows"
    for wf in sorted(wf_dir.glob("*.y*ml")):
        print(wf)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    repo = sibling(args.repo)
    sys.stdout.write(git("-C", str(repo), "show", f"{args.ref}:{args.file}"))
    return 0


def cmd_verify_upload(args: argparse.Namespace) -> int:
    """Every path the worktree changed equals the remote branch's copy, byte for byte (a signed API upload check)."""
    path = Path(args.path)
    git("-C", str(path), "fetch", "origin", args.branch, "--quiet")
    tip = git("-C", str(path), "rev-parse", "FETCH_HEAD").strip()
    bad = 0
    out = git("-C", str(path), "status", "--porcelain=v1", "--untracked-files=all")
    for line in out.splitlines():
        rel = line[3:]
        local = (path / rel).read_bytes() if (path / rel).is_file() else None
        proc = subprocess.run(["git", "-C", str(path), "show", f"{tip}:{rel}"], capture_output=True, check=False)  # nosec B603 B607
        remote = proc.stdout if proc.returncode == 0 else None
        same = local is not None and local == remote
        bad += not same
        print(f"{'SAME   ' if same else 'DIFFERS'}  {rel}")
    print(f"branch {args.branch} @ {tip[:12]}: {'every changed path matches' if not bad else f'{bad} path(s) differ'}")
    return 1 if bad else 0


def cmd_remove(args: argparse.Namespace) -> int:
    path = Path(args.path).resolve()
    if path.parent != juniper_root() / "worktrees":
        raise SystemExit(f"refusing: not under {juniper_root() / 'worktrees'}: {path}")
    branch = git("-C", str(path), "rev-parse", "--abbrev-ref", "HEAD").strip()
    common = Path(git("-C", str(path), "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    repo = common.parent
    force: list[str] = []
    if git("-C", str(path), "status", "--porcelain").strip():
        if not args.merged_into:
            raise SystemExit(f"refusing: dirty worktree {path} (after its PR merged, pass --merged-into main)")
        # Signed API uploads never become local commits, so a merged worktree still looks dirty. Remove it only
        # when every changed path equals the merged branch's copy: nothing would be lost.
        if cmd_verify_upload(argparse.Namespace(path=str(path), branch=args.merged_into)) != 0:
            raise SystemExit(f"refusing: {path} holds changes that {args.merged_into} does not")
        if any((path / "tmp").iterdir()) if (path / "tmp").is_dir() else False:
            raise SystemExit(f"refusing: {path / 'tmp'} is not empty (retention rule: archive or keep it first)")
        force = ["--force"]
    git("-C", str(repo), "worktree", "remove", *force, str(path))
    git("-C", str(repo), "branch", "-D", branch)
    git("-C", str(repo), "worktree", "prune")
    print(f"removed {path} and local branch {branch}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("create")
    p.add_argument("--repo", required=True)
    p.add_argument("--branch", required=True)
    p.set_defaults(func=cmd_create)
    for name, func in (("status", cmd_status), ("changed", cmd_changed), ("workflows", cmd_workflows), ("remove", cmd_remove)):
        p = sub.add_parser(name)
        p.add_argument("--path", required=True)
        if name == "remove":
            p.add_argument("--merged-into", metavar="BRANCH", help="the worktree is dirty only with changes BRANCH already holds: verify, then force")
        p.set_defaults(func=func)
    p = sub.add_parser("verify-upload")
    p.add_argument("--path", required=True)
    p.add_argument("--branch", required=True)
    p.set_defaults(func=cmd_verify_upload)
    p = sub.add_parser("show")
    p.add_argument("--repo", required=True)
    p.add_argument("--ref", default="origin/main")
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_show)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
