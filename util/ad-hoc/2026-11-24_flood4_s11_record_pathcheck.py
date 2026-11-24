#!/usr/bin/env python3
"""
Check that every file path the flood-4 record update adds exists on origin/main (git cat-file -e).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- path check for the record update
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; util/ad-hoc/2026-11-24_flood4_s11_record_apply.py

What it does
------------
Takes the record before (``--before``) and after (``--after``) the update, finds the lines the update added, and
pulls out every backticked token and every markdown link target in them. A token that looks like a juniper-ml path
(it holds a "/" or ends in a file suffix, after a trailing ``:NNN`` or ``#anchor`` is cut) is checked with
``git -C <repo> cat-file -e <ref>:<path>``. A token with a glob or an ellipsis, or one that names another
repository's file, cannot be checked that way: it is listed as SKIPPED with the reason, for a reader to judge.
Exit 1 when any checked path is missing.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_record_pathcheck.py --before <main copy> --after <updated> [--repo .] [--ref origin/main]
"""

from __future__ import annotations

import argparse
import re
import subprocess

SUFFIXES = (".md", ".py", ".yml", ".yaml", ".toml", ".json", ".bash", ".txt")


def candidates(text: str) -> list[str]:
    found = re.findall(r"`([^`\n]+)`", text)
    found += re.findall(r"\]\(([^)\s]+)\)", text)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--ref", default="origin/main")
    args = ap.parse_args()
    with open(args.before, encoding="utf-8") as fh:
        old = set(fh.read().split("\n"))
    with open(args.after, encoding="utf-8") as fh:
        added = [line for line in fh.read().split("\n") if line not in old]
    seen: dict[str, str] = {}
    for line in added:
        for token in candidates(line):
            path = re.sub(r"(:\d+(-\d+)?|#[\w-]+)$", "", token.strip())
            if path in seen:
                continue
            if " " in path or not ("/" in path or path.endswith(SUFFIXES)):
                continue
            if any(c in path for c in "*?[]{}…"):
                seen[path] = "SKIPPED (glob or ellipsis)"
                continue
            if path.endswith("/"):
                seen[path] = "SKIPPED (directory)"
                continue
            if "/" not in path:
                seen[path] = "SKIPPED (bare file name; another repository's file or a name in prose)"
                continue
            ok = subprocess.run(["git", "-C", args.repo, "cat-file", "-e", f"{args.ref}:{path}"], capture_output=True).returncode == 0
            seen[path] = "OK" if ok else "MISSING"
    missing = 0
    for path, verdict in sorted(seen.items()):
        print(f"{verdict:8} {path}")
        missing += verdict == "MISSING"
    print(f"{len(added)} added line(s); {sum(v == 'OK' for v in seen.values())} OK, {missing} MISSING, {sum(v.startswith('SKIPPED') for v in seen.values())} skipped")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
