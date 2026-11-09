#!/usr/bin/env python3
"""
Classify a docs carrier's deletion hunks (the Sequence Safety small-deletion WARNs) as stamp-only or content.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy docs carrier (validator finding D-F7)

Usage: 2026-11-07_flood4_canopy_docs_warn_hunks.py <git diff -U0 file>
"""

import re
import sys

STAMP = re.compile(r"^\*\*(Version|Last Updated|Date)(?:\*\*:|:\*\*)\s*\S.*$")


def main(argv: list[str]) -> int:
    path, hunks, cur = None, [], None
    with open(argv[1], encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for line in lines:
        if line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("@@"):
            cur = {"path": path, "head": line.split("@@")[1].strip(), "del": []}
            hunks.append(cur)
        elif line.startswith("-") and not line.startswith("---") and cur is not None:
            cur["del"].append(line[1:])
    with_del = [h for h in hunks if h["del"]]
    stamp = [h for h in with_del if all(STAMP.match(d) for d in h["del"])]
    content = [h for h in with_del if h not in stamp]
    print(f"deletion hunks: {len(with_del)}  stamp-only: {len(stamp)}  content: {len(content)}")
    for h in content:
        print(f"CONTENT {h['path']} @@ {h['head']} -{len(h['del'])}: {h['del'][0][:100]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
