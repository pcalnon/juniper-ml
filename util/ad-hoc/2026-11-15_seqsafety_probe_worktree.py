#!/usr/bin/env python3
"""Run the sequence-safety screens on a worktree's UNCOMMITTED change, through a dangling probe commit.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- investigation (pre-push check for the Python 3.15 informational-leg PRs)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: memory note reference_sequence_safety_local_repro.md, § "run the screens on a PROBE COMMIT before every
         signed push" (ml#2552 -> ml#2554: a carrier passed every local check and failed CI's Sequence Safety);
         util/open_signed_pr.py (which writes the real commit this probe stands in for)

Why this exists
---------------
The screens (``juniper-symbol-loss-check``, ``juniper-docs-additions-check``) diff two COMMITS, and a change landed
through ``util/open_signed_pr.py`` is an uncommitted tree until the signed API commit exists, which cannot be
amended. This builds the commit the API would build -- the CURRENT base's tree with the named paths taken from the
worktree, parent = the base -- through a private index file, so neither HEAD, the real index nor any ref moves. The
object is dangling and is never pushed; ``git gc`` collects it. Building from the current base matters: an old tree
parented on a new base makes every file the base gained look LOST.

Usage
-----
    python3 util/ad-hoc/2026-11-15_seqsafety_probe_worktree.py --worktree . --base origin/main \\
        --paths-file tmp/py315/ml-paths.txt --message-file <title + blank line + body> \\
        --python /opt/miniforge3/envs/JuniperCascor1/bin/python3.14 \\
        --scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash'

Exit 0 when both screens pass, 1 when either fails, 2 on a usage or git error.
"""

from __future__ import annotations

import argparse
import os
import subprocess  # nosec B404
import sys
from pathlib import Path


def git(worktree: Path, *args: str, env: dict[str, str] | None = None, stdin: str | None = None) -> str:
    proc = subprocess.run(["git", "-C", str(worktree), *args], env=env, input=stdin, capture_output=True, text=True)  # nosec B603 B607
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--base", required=True, help="ref the PR's commit will be parented on (fetch it first)")
    ap.add_argument("--paths-file", required=True, type=Path, help="one repo-relative path per line")
    ap.add_argument("--message-file", required=True, type=Path, help="the commit message (trailers are read from it)")
    ap.add_argument("--python", required=True, help="interpreter with juniper-ci-tools installed")
    ap.add_argument("--scope", action="append", default=[], help="symbol-loss scope glob (repeatable)")
    args = ap.parse_args()
    wt = args.worktree.resolve()
    paths = [p.strip() for p in args.paths_file.read_text(encoding="utf-8").splitlines() if p.strip()]
    base = git(wt, "rev-parse", args.base)
    index = wt / "tmp" / f"seqsafety-probe-{os.getpid()}.index"
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    try:
        git(wt, "read-tree", base, env=env)
        git(wt, "update-index", "--add", "--", *paths, env=env)
        tree = git(wt, "write-tree", env=env)
    finally:
        index.unlink(missing_ok=True)
    probe = git(wt, "-c", "commit.gpgsign=false", "commit-tree", tree, "-p", base, "-F", str(args.message_file.resolve()))
    print(f"probe commit {probe[:12]} (dangling, never pushed) on base {base[:12]}")
    print("changed:", git(wt, "diff", "--stat", base, probe).splitlines()[-1])
    scope_args = [a for s in args.scope for a in ("--scope", s)]
    rc = 0
    for module, extra in (("juniper_ci_tools.cli_symbol_loss_check", scope_args), ("juniper_ci_tools.cli_docs_additions_check", [])):
        cmd = [args.python, "-m", module, *extra, "--base", base, "--head", probe]
        proc = subprocess.run(cmd, cwd=wt, capture_output=True, text=True)  # nosec B603
        print(f"--- {module}: rc={proc.returncode}")
        print((proc.stdout + proc.stderr).strip()[-3000:])
        rc = rc or proc.returncode
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
