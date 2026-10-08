#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use, read-only. For each canopy docs PR head in the slice, print:
#   * own commits (origin/main..head),
#   * merge-base vs origin/main and how far behind it is,
#   * `git merge-tree --write-tree origin/main <head>` result (clean / conflicted paths),
#   * the true delta: `git diff --stat origin/main <merged-tree>`.
# It never writes to the repository (merge-tree --write-tree only adds objects).
"""Structural census of the canopy docs slice (flood #3)."""

from __future__ import annotations

import subprocess
import sys

REPO = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--flood3-eval--canopy-docs--20261008"

HEADS = {
    698: "7986344fc2854521abe4f2aec7be06edfc2c3239",
    700: "ec5adb1ba42bedc599eafb9c30807733d3d57e48",
    703: "8eb0ee93de2fcaf3b6a897c87b5b363ad4553210",
    706: "e9c222feaa542a3d2854ff9b74af19fed9f1ee8b",
    713: "d34dbe4bfde03cb87630c93c13c48549d33ee3d4",
    714: "c481eda93b8b12b297b36e96cc1a88262a487cf5",
    716: "6b3beb6abb716c5af38e13016e70451c45370416",
    717: "66602020ef289347ab3baf951a36ff5a3d70a536",
    723: "83e8c9a60c2945fbfdd653068bf534ed007fe0e8",
    725: "9c89fe02a1d640436e31046fda2ecdfb3deda435",
    726: "19ed73e5bcb56270589cc7ceecf53628ec314e61",
}


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, check=check)


def main() -> int:
    main_sha = git("rev-parse", "origin/main").stdout.strip()
    print(f"origin/main = {main_sha}")
    for pr, head in HEADS.items():
        print(f"\n===== #{pr} head {head[:10]}")
        own = git("log", "--format=%h %s", f"origin/main..{head}").stdout.strip()
        print("own commits:\n  " + own.replace("\n", "\n  "))
        mb = git("merge-base", "origin/main", head).stdout.strip()
        behind = git("rev-list", "--count", f"{mb}..origin/main").stdout.strip()
        mb_subj = git("log", "-1", "--format=%h %s", mb).stdout.strip()
        print(f"merge-base: {mb_subj}  (main is {behind} commits ahead of it)")
        mt = git("merge-tree", "--write-tree", "--name-only", "origin/main", head, check=False)
        lines = mt.stdout.strip().splitlines()
        tree = lines[0] if lines else ""
        if mt.returncode == 0:
            print("merge-tree: CLEAN")
        else:
            conflicted = []
            for ln in lines[1:]:
                if not ln.strip():
                    break
                conflicted.append(ln.strip())
            print(f"merge-tree: CONFLICT (exit {mt.returncode}) paths: {conflicted}")
        stat = git("diff", "--stat=200", "origin/main", tree, check=False).stdout.rstrip()
        print("true delta (origin/main -> merged tree):\n" + stat)
        own_stat = git("diff", "--stat=200", mb, head).stdout.rstrip()
        print("own diff (merge-base -> head):\n" + own_stat)
    return 0


if __name__ == "__main__":
    sys.exit(main())
