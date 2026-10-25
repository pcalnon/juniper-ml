#!/usr/bin/env python3
"""
Run ``pre-commit run --files`` on exactly the paths listed in a file, one per line.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (the PRs whose files this checks)

Why this exists
---------------
A plan PR here carries 80 or more new files, most of them untracked until the PR's signed commit lands. A
worktree-isolated session's command guard refuses ``pre-commit`` with a glob or behind ``xargs``, and typing 80
paths by hand invites a missed one. This reads the PR's own path list, refuses a path that is missing or is not a
regular file, and runs the hooks once on all of them. ``pre-commit run --files`` filters by each hook's path scope
only, so untracked files are linted (and may be rewritten) like tracked ones.

Usage
-----
    python3 util/ad-hoc/2026-10-10_precommit_on_path_list.py --list <paths.txt> [--pre-commit /opt/miniforge3/bin/pre-commit]

Exit: pre-commit's own exit code, or 2 when the list names a missing or irregular path.
"""
import argparse
import subprocess  # nosec B404 -- fixed argv, never a shell
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--list", required=True)
    ap.add_argument("--pre-commit", default="/opt/miniforge3/bin/pre-commit")
    args = ap.parse_args()
    paths = [line.strip() for line in Path(args.list).read_text(encoding="utf-8").splitlines() if line.strip()]
    bad = [p for p in paths if not Path(p).is_file() or Path(p).is_symlink()]
    if not paths or bad:
        print(f"refused: {len(bad)} missing or irregular path(s) of {len(paths)}: {bad[:5]}", file=sys.stderr)
        return 2
    print(f"pre-commit on {len(paths)} path(s) from {args.list}", flush=True)
    return subprocess.run([args.pre_commit, "run", "--files", *paths], check=False).returncode  # nosec B603


if __name__ == "__main__":
    sys.exit(main())
