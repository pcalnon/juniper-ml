#!/usr/bin/env python3
"""
Extract each juniper-data flood-4 draft's OWN hunks (merge-base..head) and commit list into a scratch dir.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data carriers)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md; flood-4 common brief rule 7

The brief forbids taking a draft's copy of a shared file wholesale: its base is stale. This writes, per PR,
`pr<N>_own.diff` (git diff merge-base..head, i.e. only the draft's own changes), `pr<N>_commits.txt`
(the commit list merge-base..head with parents) and `pr<N>_files.txt` (name-status), so the carrier can
re-apply only the draft's hunks onto current origin/main.

    python3 2026-11-07_flood4_data_extract_hunks.py --repo <juniper-data checkout> --out <scratch dir> 509 510 ...

Refs are read from refs/flood4/pr/<N> (fetched beforehand in one command).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def git(repo: str, *args: str) -> str:
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--main", default="refs/remotes/origin/main")
    ap.add_argument("prs", nargs="+")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    main_sha = git(args.repo, "rev-parse", args.main).strip()
    summary: list[str] = [f"origin/main {main_sha}"]
    for pr in args.prs:
        ref = f"refs/flood4/pr/{pr}"
        head = git(args.repo, "rev-parse", ref).strip()
        base = git(args.repo, "merge-base", args.main, ref).strip()
        commits = git(args.repo, "log", "--format=%H %P | %an | %s", f"{base}..{head}")
        files = git(args.repo, "diff", "--name-status", base, head)
        diff = git(args.repo, "diff", "--no-color", "--full-index", base, head)
        (out / f"pr{pr}_commits.txt").write_text(commits, encoding="utf-8")
        (out / f"pr{pr}_files.txt").write_text(files, encoding="utf-8")
        (out / f"pr{pr}_own.diff").write_text(diff, encoding="utf-8")
        behind = git(args.repo, "rev-list", "--count", f"{base}..{main_sha}").strip()
        summary.append(f"#{pr} head={head} merge_base={base} behind_main={behind} commits={len(commits.splitlines())} files={len(files.splitlines())}")
        for line in files.splitlines():
            summary.append(f"    {line}")
    (out / "extract_summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
