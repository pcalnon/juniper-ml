#!/usr/bin/env python3
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  ad-hoc evaluation helper (Cursor flood #3, "clients" slice)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
#
# Ad-hoc, single-use. Mutation check for fleet test PRs: apply ONE exact-string mutation to a
# production / workflow file in a disposable evaluation worktree, run the named tests, report
# whether they now FAIL (mutation killed), then restore the original bytes and prove the
# restore by content hash. Never commits; the target worktree must be a disposable one.
"""Apply a single mutation, run tests, restore.

Usage:
    2026-10-08_flood3_clients_mutate.py --repo R --file F --old OLD --new NEW
        [--count N] [--python PY] [--runner pytest|unittest] -- <test args...>

Exit 0 when the mutation is KILLED (tests fail) and the file is restored byte-identical;
exit 1 when the mutation SURVIVES; exit 2 on a usage / restore error.
"""
import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--count", type=int, default=1, help="exact number of occurrences to replace (must match)")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--runner", choices=["pytest", "unittest"], default="pytest")
    ap.add_argument("--pythonpath", default=None, help="PYTHONPATH for the test run (default: --repo)")
    ap.add_argument("--unset-env", action="append", default=[], help="environment variable to drop for the test run")
    ap.add_argument("tests", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    tests = [t for t in args.tests if t != "--"]
    repo = Path(args.repo).resolve()
    target = repo / args.file
    original = target.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    found = text.count(args.old)
    if found != args.count:
        print(f"USAGE: expected {args.count} occurrence(s) of OLD in {args.file}, found {found}")
        return 2
    target.write_bytes(text.replace(args.old, args.new).encode("utf-8"))
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = args.pythonpath or str(repo)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for name in args.unset_env:
            env.pop(name, None)
        if args.runner == "pytest":
            cmd = [args.python, "-s", "-m", "pytest", "-p", "no:cacheprovider", "-o", "addopts=", "-q", "-x", *tests]
        else:
            cmd = [args.python, "-s", "-m", "unittest", *tests]
        proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, env=env, timeout=900)
        tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-6:])
    finally:
        target.write_bytes(original)
    restored = hashlib.sha256(target.read_bytes()).hexdigest() == digest
    verdict = "KILLED" if proc.returncode != 0 else "SURVIVED"
    print(f"mutation {args.file}: {args.old!r} -> {args.new!r}")
    print(f"tests rc={proc.returncode} -> {verdict}; restored byte-identical={restored}")
    print(tail)
    if not restored:
        return 2
    return 0 if verdict == "KILLED" else 1


if __name__ == "__main__":
    sys.exit(main())
