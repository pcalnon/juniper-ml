#!/usr/bin/env python3
"""
Run a sibling checkout's Sequence Safety screens against its uncommitted work, without committing anything.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-26
Status: ad-hoc -- the run_tests rollout, copy 2 (juniper-data-client)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: memory reference_sequence_safety_local_repro (probe-commit the screens before every signed push)

The screens compare two commits, and a signed API upload (util/open_signed_pr.py) never makes a local one. This
builds a probe commit from the checkout's working tree -- through a throwaway index under ``--work`` (git's own index
is never touched), with ``--base`` as its parent -- and runs ``juniper-symbol-loss-check`` (with each ``--scope``)
and ``juniper-docs-additions-check`` from ``base`` to it, as the PR's CI would. No ref moves; the probe commit is a
dangling object git collects later. Exit: 0 when both screens pass, 1 otherwise, 2 on a setup error.
"""

from __future__ import annotations

import argparse
import os
import subprocess  # nosec B404 - git and the screens, fixed argv
import sys
from pathlib import Path


def run(argv: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, check=False)  # nosec B603 B607


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path, help="a directory under a repo's tmp/ for the throwaway index")
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--scope", action="append", default=[], help="symbol-loss scope glob (repeatable), as the workflow passes it")
    parser.add_argument("--message-file", type=Path, help="the probe commit's message, to test a waiver trailer the screens read (default: a fixed one)")
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    args.work.mkdir(parents=True, exist_ok=True)
    env = {key: value for key, value in os.environ.items() if key not in ("GIT_DIR", "GIT_WORK_TREE")}
    env.update(GIT_INDEX_FILE=str(args.work.resolve() / "probe.index"), GIT_AUTHOR_NAME="probe", GIT_AUTHOR_EMAIL="probe@example.invalid", GIT_COMMITTER_NAME="probe", GIT_COMMITTER_EMAIL="probe@example.invalid")
    base = run(["git", "rev-parse", args.base], checkout).stdout.strip()
    steps = [["git", "read-tree", base], ["git", "add", "-A"], ["git", "write-tree"]]
    out = ""
    for argv in steps:
        proc = run(argv, checkout, env)
        if proc.returncode != 0:
            sys.stderr.write(f"{' '.join(argv)} failed: {proc.stderr}")
            return 2
        out = proc.stdout.strip()
    message = ["-F", str(args.message_file.resolve())] if args.message_file else ["-m", "probe: the working tree, never pushed"]
    probe = run(["git", "commit-tree", out, "-p", base, *message], checkout, env)
    if probe.returncode != 0:
        sys.stderr.write(f"git commit-tree failed: {probe.stderr}")
        return 2
    head = probe.stdout.strip()
    print(f"base {base[:12]}  probe {head[:12]}  (no ref moved)")
    print(run(["git", "diff", "--stat", base, head], checkout).stdout.rstrip())
    failed = 0
    scopes = [part for scope in args.scope for part in ("--scope", scope)]
    for argv in (["juniper-symbol-loss-check", "--base", base, "--head", head, *scopes], ["juniper-docs-additions-check", "--base", base, "--head", head]):
        proc = run(argv, checkout)
        print(f"--- {' '.join(argv[:1])}: exit {proc.returncode}")
        print((proc.stdout + proc.stderr).rstrip())
        failed += proc.returncode != 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
