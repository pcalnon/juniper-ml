"""
Write the unified diff of each draft's head blob against the file the landed tree holds (the carrier's fixes).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent, flood-4 session 7)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --repo <own worktree> --landed <landed tree> --out-dir <dir> --pair 2469:tests/test_x.py ...
"""

import argparse
import difflib
import subprocess
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--landed", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--pair", nargs="+", required=True)
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for pair in args.pair:
        number, path = pair.split(":", 1)
        done = subprocess.run(["git", "show", "refs/flood4r2v/pr/%s:%s" % (number, path)], cwd=args.repo, capture_output=True, text=True, check=False)
        if done.returncode != 0:
            print("%s: no head blob (%s)" % (pair, done.stderr.strip()))
            continue
        head = done.stdout.splitlines(keepends=True)
        landed = (Path(args.landed) / path).read_text(encoding="utf-8").splitlines(keepends=True)
        diff = list(difflib.unified_diff(head, landed, "draft#%s/%s" % (number, path), "landed/%s" % path, n=1))
        plus = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        minus = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
        target = out_dir / ("%s__%s.diff" % (number, path.replace("/", "__")))
        target.write_text("".join(diff), encoding="utf-8")
        print("%-60s +%d -%d -> %s" % (pair, plus, minus, target.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
