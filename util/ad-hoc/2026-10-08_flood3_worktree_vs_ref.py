#!/usr/bin/env python3
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  ad-hoc helper (Cursor flood #3 disposition, final record PR assembly)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
#
# Ad-hoc, single-use. Before the flood-3 record PR is assembled from this session's worktree,
# every changed or untracked path is classified against a ref: NEW (absent there), SAME (blob
# identical) or DIFF. Only NEW files belong in the record PR; a SAME file is already on main
# (re-uploading it is a no-op at best), and a DIFF file is either a stale copy that would REVERT
# main or real work that has to be reconciled by hand -- never uploaded wholesale.
"""Usage: 2026-10-08_flood3_worktree_vs_ref.py <ref> [--out FILE]

Reads `git status --porcelain=v1 -uall` in the current directory. Prints counts and every
non-NEW path (SAME paths under tests/ are summarised, not listed). Exit 1 if any DIFF exists.
"""
import subprocess
import sys


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False)  # nosec B603 B607


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    ref = argv[1]
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else None
    status = _git("status", "--porcelain=v1", "-uall")
    if status.returncode != 0:
        print(status.stderr.strip(), file=sys.stderr)
        return 2
    rows, counts = [], {"NEW": 0, "SAME": 0, "DIFF": 0}
    for line in status.stdout.splitlines():
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        there = _git("rev-parse", "--verify", "-q", f"{ref}:{path}")
        if there.returncode != 0:
            kind = "NEW"
        else:
            here = _git("hash-object", path).stdout.strip()
            kind = "SAME" if here == there.stdout.strip() else "DIFF"
        counts[kind] += 1
        rows.append(f"{kind} {line[:2].strip() or '??'} {path}")
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(rows) + "\n")
    print(counts)
    same_tests = sum(1 for r in rows if r.startswith("SAME") and r.split()[-1].startswith("tests/"))
    if same_tests:
        print(f"SAME tests/* x{same_tests}")
    for r in rows:
        if r.startswith("NEW") or (r.startswith("SAME") and r.split()[-1].startswith("tests/")):
            continue
        print(r)
    return 1 if counts["DIFF"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
