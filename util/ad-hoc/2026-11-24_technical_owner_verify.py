#!/usr/bin/env python3
"""
Verify the technical-owner sweep's working-tree diff: every change is an "Overtoad" put back to "owner", and nothing else.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — migration check (the technical-owner sweep that follows juniper-ml#2606)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_technical_owner_restore.py (makes the diff this checks)

For every file the checkout changed against HEAD it checks, independently of the restore tool:

- the file is a regular file at HEAD and in the checkout, with the same line count;
- each changed line equals HEAD's line with some "Overtoad" tokens replaced in place by "owner", and some
  "The Overtoad" by "Owner" or "The owner" (a sentence that began "The owner"), with no other difference;
- the number of tokens put back, summed over every file, equals ``--expect``.

Usage: python3 util/ad-hoc/2026-11-24_technical_owner_verify.py --repo . --expect 340 --exclude CHANGELOG.md
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

TOKEN = re.compile(r"(The Overtoad|Overtoad)")


def git(repo: str, *args: str) -> str:
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args[:3])} failed: {proc.stderr.strip()[:300]}")
    return proc.stdout


def restored_count(old: str, new: str) -> int | None:
    """How many tokens of OLD became owner/Owner in NEW; None if NEW differs from OLD in any other way."""
    pieces = TOKEN.split(old)
    # "The Overtoad" is either a renamed "Owner" or "The " followed by a renamed "owner" ("The owner must be ...")
    pattern = "".join(re.escape(p) if k % 2 == 0 else ("(The Overtoad|Owner|The owner)" if p == "The Overtoad" else "(Overtoad|owner)") for k, p in enumerate(pieces))
    match = re.fullmatch(pattern, new)
    if not match:
        return None
    return sum(1 for k in range(1, len(pieces), 2) if match.group((k + 1) // 2) != pieces[k])


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--expect", type=int, required=True)
    ap.add_argument("--exclude", nargs="*", default=[], help="changed files that are not restorations (the CHANGELOG entry)")
    args = ap.parse_args(argv)
    repo = os.path.abspath(args.repo)
    total, failures, files = 0, [], 0
    for path in git(repo, "diff", "--name-only").split():
        if path in args.exclude:
            print(f"excluded: {path}")
            continue
        files += 1
        meta = git(repo, "ls-tree", "HEAD", "--", path).split()
        if not meta or meta[0] not in ("100644", "100755") or os.path.islink(os.path.join(repo, path)):
            failures.append(f"{path}: not a regular file at HEAD and on disk")
            continue
        old = git(repo, "show", f"HEAD:{path}").split("\n")
        with open(os.path.join(repo, path), encoding="utf-8", newline="") as handle:
            new = handle.read().split("\n")
        if len(old) != len(new):
            failures.append(f"{path}: line count {len(old)} -> {len(new)}")
            continue
        for number, (a, b) in enumerate(zip(old, new), 1):
            if a == b:
                continue
            count = restored_count(a, b)
            if not count:
                failures.append(f"{path}:{number}: differs beyond a restored token")
                continue
            total += count
    print(f"{files} file(s), {total} token(s) put back, {len(failures)} failure(s); expected {args.expect}")
    for failure in failures:
        print("FAIL", failure)
    return 0 if not failures and total == args.expect else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
