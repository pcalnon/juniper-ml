#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : worktree hygiene
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Is it safe to converge this worktree onto origin/main by discarding local state?

Only if every locally modified or untracked file that ALSO exists on the target ref is
byte-identical to the target's copy -- i.e. the local edits already landed upstream (the
usual case for a session that commits through the GitHub API, which never touches the
working tree). Anything that differs is unlanded work and must not be discarded; see
[[reference_stale_local_checkout_clobbers_your_own_work]].

Reports three buckets and exits 1 if any file is in the third:

  SAME      modified/untracked locally, identical on the ref -> safe to discard
  LOCAL-NEW absent from the ref                              -> keep (nothing to clobber)
  DIVERGED  present on the ref and DIFFERENT                 -> STOP

Usage:
  python util/ad-hoc/2026-09-12_worktree_converge_precheck.py --ref origin/main
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--show", type=int, default=12, help="how many paths to list per bucket")
    args = ap.parse_args()

    paths = []
    for line in git("status", "--porcelain").splitlines():
        status, _, path = line[:2], line[2], line[3:]
        if status.strip() in {"M", "??", "A", "AM", "MM"}:
            paths.append(path.strip().strip('"'))

    same, local_new, diverged = [], [], []
    for rel in paths:
        local = REPO / rel
        if not local.is_file():
            continue
        r = subprocess.run(["git", "-C", str(REPO), "show", f"{args.ref}:{rel}"], capture_output=True)
        if r.returncode != 0:
            local_new.append(rel)
            continue
        (same if r.stdout == local.read_bytes() else diverged).append(rel)

    for label, bucket in (("SAME", same), ("LOCAL-NEW", local_new), ("DIVERGED", diverged)):
        print(f"{label}: {len(bucket)}")
        for rel in bucket[: args.show]:
            print(f"    {rel}")
        if len(bucket) > args.show:
            print(f"    ... and {len(bucket) - args.show} more")

    if diverged:
        print(f"\nSTOP: {len(diverged)} file(s) differ from {args.ref} and would be lost.", file=sys.stderr)
        return 1
    print(f"\nSafe: every local file is identical to {args.ref} or absent from it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
