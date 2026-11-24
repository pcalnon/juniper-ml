#!/usr/bin/env python3
"""
Rebuild the juniper-deploy ruling-10 port's shared files three-way onto another ref (an open pull request's head, or a main that moved), never by copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-deploy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530;
         juniper-deploy#276 (open while the port was built; it edits ci.yml, CHANGELOG.md and AGENTS.md)

WHY THIS EXISTS
The port was built on juniper-deploy main dd299fbf. Another pull request that edits two of its files (ci.yml and
CHANGELOG.md) was open and expected to merge first. The brief's rule is a three-way rebuild
(`git merge-file -p <carrier's copy> <base's copy> <new copy>`), never the carrier's copy over the new one. This
script runs it for each named file, from read-only `git show` of the base and the target ref, writes each result to
<out>/merged/<path> with its conflict count, and checks that CHANGELOG.md's merged result still has the port's entry
under the TOP `## [Unreleased]` and its `### Security`. It writes only under --out; it never touches the carrier.

Usage:
  python3 <this> --carrier <port worktree> --repo <checkout holding both refs> --base <sha> --target <ref>
      --out <dir> --paths .github/workflows/ci.yml CHANGELOG.md [...]

Exit 0 = every file merged with no conflict and the CHANGELOG entry is where it belongs; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed argv: read-only git show and git merge-file on files this script wrote
import sys
from pathlib import Path

ENTRY_LEAD = "- **A pull request's Gitleaks scan covers its whole `base..head`, merge commits included.**"


def show(repo: Path, ref: str, rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{rel}"], capture_output=True, check=True, timeout=60).stdout  # nosec B603 B607


def changelog_placement(text: str) -> dict:
    lines = text.splitlines()
    entry = next((i for i, ln in enumerate(lines) if ln.startswith(ENTRY_LEAD)), None)
    releases = [i for i, ln in enumerate(lines) if ln.startswith("## [")]
    top = releases[0] if releases else None
    heading_above = next((lines[i] for i in range(entry, -1, -1) if lines[i].startswith("### ")), None) if entry is not None else None
    next_release = next((i for i in releases if entry is not None and i > entry), None)
    release_above = next((lines[i] for i in range(entry, -1, -1) if lines[i].startswith("## [")), None) if entry is not None else None
    return {
        "entry_line": None if entry is None else entry + 1,
        "top_release_heading": None if top is None else lines[top],
        "release_heading_above_entry": release_above,
        "subsection_above_entry": heading_above,
        "next_release_line": None if next_release is None else next_release + 1,
        "ok": entry is not None and release_above == "## [Unreleased]" and top is not None and lines[top] == "## [Unreleased]" and heading_above == "### Security",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--carrier", required=True, type=Path)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--base", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--paths", required=True, nargs="+")
    args = ap.parse_args()
    out = args.out.resolve()
    rows = []
    ok = True
    for rel in args.paths:
        work = out / "inputs" / rel.replace("/", "__")
        work.mkdir(parents=True, exist_ok=True)
        mine, base, theirs = work / "carrier", work / "base", work / "target"
        mine.write_bytes((args.carrier / rel).read_bytes())
        base.write_bytes(show(args.repo, args.base, rel))
        theirs.write_bytes(show(args.repo, args.target, rel))
        res = subprocess.run(["git", "merge-file", "-p", str(mine), str(base), str(theirs)], capture_output=True, check=False, timeout=60)  # nosec B603 B607
        merged = out / "merged" / rel
        merged.parent.mkdir(parents=True, exist_ok=True)
        merged.write_bytes(res.stdout)
        row = {
            "path": rel,
            "conflicts": res.returncode,
            "target_changed_it": base.read_bytes() != theirs.read_bytes(),
            "sha256": {"carrier": hashlib.sha256(mine.read_bytes()).hexdigest(), "base": hashlib.sha256(base.read_bytes()).hexdigest(), "target": hashlib.sha256(theirs.read_bytes()).hexdigest(), "merged": hashlib.sha256(res.stdout).hexdigest()},
            "merged": str(merged),
        }
        if rel == "CHANGELOG.md":
            row["placement"] = changelog_placement(res.stdout.decode("utf-8"))
            ok = ok and row["placement"]["ok"]
        ok = ok and res.returncode == 0
        rows.append(row)
        print(f"{rel}: conflicts={res.returncode} target_changed_it={row['target_changed_it']}" + (f" placement={row['placement']}" if "placement" in row else ""))
    (out / "three_way.json").write_text(json.dumps({"base": args.base, "target": args.target, "files": rows, "ok": ok}, indent=1) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
