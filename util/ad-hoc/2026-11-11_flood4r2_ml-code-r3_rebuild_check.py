#!/usr/bin/env python3
"""
Check a three-way rebuild: the lines the rebuilt file changes against main equal the lines the carrier changed against its base.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3 rebuild)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_rebuild.py and ..._resolve.py; the session-4 addendum's trap
         ("a hand-inserted entry once nearly reverted another PR's entry").

Usage (from the round-3 worktree root):
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_rebuild_check.py <out dir>/rebuild <repo-relative path> [...]

For each path, reads <rebuild dir>/<path with / as __>.{base,carrier,main} and the worktree's file, and compares
two multisets of changed lines: base -> carrier (what the carrier did) and main -> worktree (what the rebuilt
file does to main). Prints the lines that are in one and not the other; after a correct rebuild those are only
the re-derived stamps and the lines a later edit of the rebuilt file changed. Exit 0 always: the output is read.
"""
import collections
import difflib
import sys
from pathlib import Path


def changed(old: str, new: str) -> collections.Counter:
    out = collections.Counter()
    for line in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0):
        if line[:1] in "+-" and line[:3] not in ("+++", "---"):
            out[line] += 1
    return out


def main() -> int:
    rebuild = Path(sys.argv[1])
    for rel in sys.argv[2:]:
        stem = rel.replace("/", "__")
        base, carrier, head = ((rebuild / (stem + suffix)).read_bytes().decode("utf-8") for suffix in (".base", ".carrier", ".main"))
        tree = Path(rel).read_bytes().decode("utf-8")
        did, does = changed(base, carrier), changed(head, tree)
        only_carrier, only_tree = did - does, does - did
        print("%s: carrier changed %d line(s) against its base; the rebuilt file changes %d against main" % (rel, sum(did.values()), sum(does.values())))
        for label, lines in (("only in base->carrier", only_carrier), ("only in main->rebuilt", only_tree)):
            print("  %s: %d" % (label, sum(lines.values())))
            for line in sorted(lines):
                print("    %s" % line[:230])
    return 0


if __name__ == "__main__":
    sys.exit(main())
