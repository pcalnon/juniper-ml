#!/usr/bin/env python3
# Project:      juniper-ml
# Sub-Project:  util/ad-hoc
# Application:  flood-4 docs-carrier validation (fidelity lens)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Purpose:      Read-only: resolve every markdown link with a #fragment in the given files (worktree copy)
#               against GitHub-style heading slugs of the target file (fence-aware, duplicate slugs get -N),
#               and report fragments that do not resolve. The same check runs on origin/main's copy of the
#               source files so pre-existing breaks are separated from new ones. Also reports duplicate
#               slugs a carrier introduces (two headings that slug the same, making the second -1).
"""
Read-only: find the markdown #fragment links in the given files that do not resolve to a GitHub-style heading slug of their target, and the headings whose slug a carrier duplicates; report those that are new against origin/main.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 1, structure-and-fidelity lens (findings: tmp/flood4/ml-docs/val-fidelity/)
"""

import os
import re
import subprocess
import sys

files = sys.argv[1:]
LINK = re.compile(r"\[(?:[^\[\]]|\[[^\]]*\])*\]\(([^)\s]+)\)")


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("`", "")
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def heading_slugs(text):
    slugs = []
    seen = {}
    fence = None
    for line in text.splitlines():
        m = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if m:
            tok = m.group(1)
            if fence is None:
                fence = (tok[0], len(tok))
            elif tok[0] == fence[0] and len(tok) >= fence[1] and not m.group(2).strip():
                fence = None
            continue
        if fence:
            continue
        h = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if h:
            s = slugify(h.group(1))
            if s in seen:
                seen[s] += 1
                slugs.append(f"{s}-{seen[s]}")
            else:
                seen[s] = 0
                slugs.append(s)
    return slugs


def read(path, rev):
    if rev is None:
        try:
            with open(path, encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return None
    out = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def links_in(text):
    res = []
    fence = None
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if m:
            tok = m.group(1)
            if fence is None:
                fence = (tok[0], len(tok))
            elif tok[0] == fence[0] and len(tok) >= fence[1] and not m.group(2).strip():
                fence = None
            continue
        if fence:
            continue
        for lm in LINK.finditer(line):
            target = lm.group(1)
            if "#" in target and not re.match(r"^[a-z]+://", target):
                res.append((i, target))
    return res


def check(rev):
    broken = set()
    dup = {}
    cache = {}
    for f in files:
        src = read(f, rev)
        if src is None:
            continue
        slugs = heading_slugs(src)
        counts = {}
        for s in slugs:
            base = re.sub(r"-\d+$", "", s)
            counts[base] = counts.get(base, 0) + 1
        dup[f] = {s for s in slugs if re.search(r"-\d+$", s) and re.sub(r"-\d+$", "", s) in counts}
        for ln, target in links_in(src):
            path, frag = target.split("#", 1)
            tpath = os.path.normpath(os.path.join(os.path.dirname(f), path)) if path else f
            key = (tpath, rev)
            if key not in cache:
                t = read(tpath, rev)
                cache[key] = set(heading_slugs(t)) if t is not None else None
            tslugs = cache[key]
            if tslugs is None:
                continue  # missing file is the link checker's job
            if frag not in tslugs:
                broken.add((f, target))
    return broken, dup


new_broken, new_dup = check(None)
main_broken, main_dup = check("origin/main")
only_new = sorted(new_broken - main_broken)
print(f"broken fragment links: worktree={len(new_broken)} main={len(main_broken)} NEW={len(only_new)}")
for f, t in only_new:
    print(f"  NEW BROKEN: {f} -> {t}")
for f in files:
    added_dups = sorted(new_dup.get(f, set()) - main_dup.get(f, set()))
    if added_dups:
        print(f"  NEW DUPLICATE-SLUG HEADINGS in {f}: {added_dups}")
