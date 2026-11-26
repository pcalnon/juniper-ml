"""
Filter a `gh pr list --json number,title,mergedAt,mergeCommit,files` dump to the PRs that touched a path prefix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, builder r23l: re-verify ruling 23's "Lifecycle races beside N-2" on today's main)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2557

Usage: python3 <this file> DUMP.json PREFIX [PREFIX ...]
Prints one line per matching PR (number, mergedAt, merge sha, title) and the matching paths beneath it.
"""

import json
import sys


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8") as fh:
        prs = json.load(fh)
    prefixes = argv[2:]
    print(f"PRs in dump: {len(prs)}")
    hits = 0
    for pr in sorted(prs, key=lambda p: p.get("mergedAt") or ""):
        paths = [f.get("path", "") for f in (pr.get("files") or [])]
        matched = [p for p in paths if any(p.startswith(x) for x in prefixes)]
        if not matched:
            continue
        hits += 1
        sha = (pr.get("mergeCommit") or {}).get("oid", "")[:8]
        print(f"#{pr['number']} {pr.get('mergedAt')} {sha} {pr.get('title')}")
        for p in matched:
            print(f"    {p}")
        if len(paths) >= 100:
            print(f"    (NOTE: {len(paths)} files listed; gh caps the files list at 100, so a match may be missing)")
    print(f"matching PRs: {hits}")
    capped = [pr["number"] for pr in prs if len(pr.get("files") or []) >= 100]
    print(f"PRs whose file list may be capped at 100: {capped}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
