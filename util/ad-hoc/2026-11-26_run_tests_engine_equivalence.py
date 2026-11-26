#!/usr/bin/env python3
"""
Prove a run_tests conversion changes nothing: export a repo's tree, capture a runner's --list / --dry-run / --help
output for a fixed set of cases, and compare two captures case by case.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-26
Status: ad-hoc -- the run_tests engine extraction (juniper_ci_tools.run_tests, juniper-ci-tools 0.10.0)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-EXTRACTION-PROPOSAL.md § 4.3 step 4 ("each
         conversion PR must show the same --list and --dry-run output before and after")

Subcommands
-----------
- ``export --repo R [--ref REF] --dest DIR``: fetch ``origin`` in the sibling primary ``Juniper/R`` (refs only),
  then write the tree at REF (default ``origin/main``) into DIR with ``git archive``. DIR must not exist. The export
  is not a git checkout, so the runner's checkout line carries no git state, the same for both runs.
- ``capture --runner FILE --cases FILE --out DIR [--checkout DIR] [--pythonpath DIR]``: run the runner once per case
  (a line: a name, a tab, the arguments as shell words) with ``--color never``, and write each case's arguments,
  exit code, stdout and stderr to ``DIR/<name>.txt``. ``--pythonpath`` is the runner's own PYTHONPATH (a checkout's
  ``juniper-ci-tools/``, to run an engine that is not installed); the engine removes PYTHONPATH from its children.
  A checkout line's "N uncommitted" and head are masked: a conversion is itself an uncommitted change.
- ``compare BEFORE AFTER``: for each case, IDENTICAL or the differing lines. Exit 1 when any case differs, so a
  difference is never read as a pass; the differences a conversion intends are for the PR to name.

Nothing is written under the system temp directory: DIR is the caller's (this arc used the juniper-ml worktree's
gitignored ``tmp/``).
"""

from __future__ import annotations

import argparse
import difflib
import io
import os
import re
import shlex
import subprocess  # nosec B404 - git and the runner under test, fixed argv
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]


def juniper_root() -> Path:
    """The ecosystem directory: the parent of the primary checkout that holds this checkout's .git (a worktree's too)."""
    common = subprocess.run(["git", "-C", str(HERE), "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True, text=True, check=True).stdout.strip()  # nosec B603 B607
    return Path(common).parent.parent


def git(repo: Path, *args: str, binary: bool = False) -> bytes | str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise SystemExit(f"git -C {repo} {' '.join(args)}: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout if binary else proc.stdout.decode()


def cmd_export(args: argparse.Namespace) -> int:
    repo = juniper_root() / args.repo
    if not (repo / ".git").exists():
        raise SystemExit(f"not a sibling checkout: {repo}")
    dest = Path(args.dest).absolute()
    if dest.exists():
        raise SystemExit(f"{dest} exists: export into a new directory")
    git(repo, "fetch", "origin", "--quiet")
    sha = str(git(repo, "rev-parse", args.ref)).strip()
    data = git(repo, "archive", "--format=tar", sha, binary=True)
    dest.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:  # type: ignore[arg-type]
        tar.extractall(dest, filter="data")
    print(f"{args.repo} {args.ref} = {sha} -> {dest}")
    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    runner = Path(args.runner).absolute()
    out = Path(args.out).absolute()
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    if args.pythonpath:
        env["PYTHONPATH"] = str(Path(args.pythonpath).absolute())
    cwd = Path(args.checkout).absolute() if args.checkout else runner.parents[1]
    for raw in Path(args.cases).read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        name, _, words = raw.partition("\t")
        argv = [sys.executable, str(runner), "--color", "never", *(["--checkout", str(cwd)] if args.checkout else []), *shlex.split(words)]
        proc = subprocess.run(argv, capture_output=True, text=True, env=env, cwd=cwd, timeout=600, check=False)  # nosec B603
        text = f"$ {shlex.join(argv[2:])}\nexit={proc.returncode}\n--- stdout\n{proc.stdout}--- stderr\n{proc.stderr}"
        text = re.sub(r"\d+ uncommitted\)", "N uncommitted)", text)
        text = re.sub(r"@ [0-9a-f]{10},", "@ HEAD,", text)
        (out / f"{name}.txt").write_text(text, encoding="utf-8")
        print(f"{name}: exit {proc.returncode}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    before, after = Path(args.before), Path(args.after)
    names = sorted({path.name for path in before.glob("*.txt")} | {path.name for path in after.glob("*.txt")})
    differing = 0
    for name in names:
        left = (before / name).read_text(encoding="utf-8").splitlines() if (before / name).is_file() else ["(missing)"]
        right = (after / name).read_text(encoding="utf-8").splitlines() if (after / name).is_file() else ["(missing)"]
        if left == right:
            print(f"IDENTICAL  {name}")
            continue
        differing += 1
        print(f"DIFFERS    {name}")
        for line in difflib.unified_diff(left, right, "before", "after", n=0, lineterm=""):
            if not line.startswith(("---", "+++", "@@")):
                print(f"    {line}")
    print(f"{len(names) - differing} of {len(names)} cases identical")
    return 1 if differing else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    export.add_argument("--repo", required=True)
    export.add_argument("--ref", default="origin/main")
    export.add_argument("--dest", required=True)
    capture = sub.add_parser("capture")
    capture.add_argument("--runner", required=True)
    capture.add_argument("--cases", required=True)
    capture.add_argument("--out", required=True)
    capture.add_argument("--checkout")
    capture.add_argument("--pythonpath")
    compare = sub.add_parser("compare")
    compare.add_argument("before")
    compare.add_argument("after")
    args = parser.parse_args()
    return {"export": cmd_export, "capture": cmd_capture, "compare": cmd_compare}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
