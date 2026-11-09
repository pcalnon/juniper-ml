#!/usr/bin/env python3
"""
Inventory, compare and harvest the flood-4 provenance scripts scattered over this arc's worktrees.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 disposition record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (sec 7);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-round1-carriers-landed-record-next.md (step 2e)

WHY THIS EXISTS
The flood-4 builders and validators each worked in an isolated agent worktree and left their scripts there,
untracked. `git worktree remove` deletes untracked files, so the scripts must reach the record PR before any
of those worktrees is cleaned up. The same name can exist in several worktrees (a validator re-ran a builder's
script, or copied it before the builder revised it), so a blind copy could ship an older revision. This lists
every copy, groups them by name and sha256, and refuses to choose silently: a name whose copies differ is
resolved only by an explicit --prefer rule, or it is reported and skipped.

Usage:
  2026-11-08_flood4_harvest_scripts.py --dest <worktree> --source <worktree> [--source ...]
        [--glob '2026-11-0[78]_flood4_*'] [--prefer <worktree>] [--deprioritize <worktree>] [--apply]
Without --apply nothing is written; the report says what would be copied.
"""

import argparse
import fnmatch
import hashlib
import os
import shutil
import sys


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dest", required=True, help="worktree that receives the scripts (its util/ad-hoc/)")
    ap.add_argument("--source", action="append", default=[], help="worktree to harvest from (repeatable)")
    ap.add_argument("--glob", default="2026-11-0[78]_flood4_*")
    ap.add_argument("--prefer", action="append", default=[], help="worktree whose copy wins a conflict (repeatable, in priority order)")
    ap.add_argument("--deprioritize", action="append", default=[], help="worktree whose copy loses every conflict")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    roots = [a.dest] + [s for s in a.source if os.path.realpath(s) != os.path.realpath(a.dest)]
    copies = dict()  # name -> list of (root, path, sha, mtime)
    for root in roots:
        d = os.path.join(root, "util", "ad-hoc")
        if not os.path.isdir(d):
            print("MISSING %s" % d)
            continue
        for name in sorted(os.listdir(d)):
            if not fnmatch.fnmatch(name, a.glob):
                continue
            p = os.path.join(d, name)
            if not os.path.isfile(p) or os.path.islink(p):
                continue
            copies.setdefault(name, []).append((root, p, sha256(p), os.path.getmtime(p)))

    total = sum(len(v) for v in copies.values())
    print("copies %d under %d names in %d worktrees" % (total, len(copies), len(roots)))
    prefer = [os.path.realpath(p) for p in a.prefer]
    depri = set(os.path.realpath(p) for p in a.deprioritize)
    to_copy, conflicts, unresolved = [], [], []
    for name, cs in sorted(copies.items()):
        shas = sorted(set(c[2] for c in cs))
        dest_copy = [c for c in cs if os.path.realpath(c[0]) == os.path.realpath(a.dest)]
        if len(shas) == 1:
            if not dest_copy:
                to_copy.append((name, cs[0][1]))
            continue
        # Copies differ: resolve by --prefer order, then by dropping --deprioritize; never by mtime alone.
        conflicts.append(name)
        chosen = None
        for pr in prefer:
            hit = [c for c in cs if os.path.realpath(c[0]) == pr]
            if hit:
                chosen = hit[0]
                break
        if chosen is None:
            rest = [c for c in cs if os.path.realpath(c[0]) not in depri]
            if len(set(c[2] for c in rest)) == 1:
                chosen = rest[0]
        detail = "; ".join("%s %s %s" % (os.path.basename(c[0]), c[2][:8], int(c[3])) for c in cs)
        if chosen is None:
            unresolved.append(name)
            print("UNRESOLVED %s :: %s" % (name, detail))
            continue
        print("CONFLICT %s -> %s (%s) :: %s" % (name, os.path.basename(chosen[0]), chosen[2][:8], detail))
        if not dest_copy or dest_copy[0][2] != chosen[2]:
            to_copy.append((name, chosen[1]))

    print("to copy: %d; conflicts: %d; unresolved: %d" % (len(to_copy), len(conflicts), len(unresolved)))
    for name, src in to_copy:
        print("  %s <- %s" % (name, src))
    if unresolved:
        print("REFUSING: resolve every UNRESOLVED name with --prefer / --deprioritize first")
        return 2
    if a.apply:
        dd = os.path.join(a.dest, "util", "ad-hoc")
        for name, src in to_copy:
            shutil.copy2(src, os.path.join(dd, name))
        print("copied %d" % len(to_copy))
    return 0


if __name__ == "__main__":
    sys.exit(main())
