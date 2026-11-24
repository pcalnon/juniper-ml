"""
Freeze a D-14 carrier into the layout the sequence-safety probe reads: paths.txt, snapshot/ and plan.json.

``--repo`` is a carrier worktree (the juniper-ml one is this worktree). Every changed or untracked path that
``git status --porcelain --untracked-files=all`` lists, ``tmp/`` excepted, becomes an ``add <path>`` line (a deleted
path a ``delete <path>`` line), its bytes are copied to ``<out>/snapshot/<path>``, and ``plan.json`` records the
``origin/main`` sha the carrier was built on. The orchestrator worktree's
``util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py`` then builds a dangling ``git commit-tree`` probe commit on
that main from the freeze and runs CI's two screens on it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--own", action="store_true", help="the repo is the worktree this runs in (plain git, no -C)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    prefix = ["git"] if args.own else ["git", "-C", str(args.repo)]
    cwd = args.repo if args.own else Path.cwd()
    status = subprocess.run([*prefix, "status", "--porcelain", "--untracked-files=all"], cwd=cwd, capture_output=True, text=True, check=True).stdout
    main_sha = subprocess.run([*prefix, "rev-parse", "origin/main"], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()
    if args.out.exists():
        shutil.rmtree(args.out)
    (args.out / "snapshot").mkdir(parents=True)
    lines = []
    for line in status.splitlines():
        code, path = line[:2].strip(), line[3:]
        if path.startswith("tmp/"):
            continue
        if code == "D":
            lines.append(f"delete {path}")
            continue
        target = args.out / "snapshot" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.repo / path, target)
        lines.append(f"add {path}")
    (args.out / "paths.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (args.out / "plan.json").write_text(json.dumps({"main_sha": main_sha, "paths": len(lines)}, indent=1) + "\n", encoding="utf-8")
    print(f"froze {len(lines)} paths of {args.repo} on origin/main {main_sha[:8]} into {args.out}")


if __name__ == "__main__":
    main()
