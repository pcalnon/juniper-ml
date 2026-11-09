#!/usr/bin/env python3
"""
Turn a flood-4 builder's deliverables into the exact inputs of a signed carrier PR.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 carrier PRs)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md;
         util/ad-hoc/2026-11-07_flood4_signed_push_batches.py (consumes the outputs)

WHY THIS EXISTS
Each builder wrote <dir>/manifest.json, pr_body.txt (line 1 `TITLE: ...`), commit_body.txt. A PR needs a
title, a body ending in the session attribution, a commit body ending in the commit trailers, and the list
of repo paths to upload -- never the builders' util/ad-hoc provenance scripts (those ship in the record
PR) and never a scratch file. It also copies those paths from the carrier worktree into a frozen snapshot,
recording each file's sha256, so the push uploads exactly what was validated.

Usage:
  2026-11-07_flood4_prep_pr_texts.py --deliverables <dir> --worktree <carrier worktree> --out <dir>
Writes <out>/title.txt, pr_body.txt, commit_body.txt, paths.txt, snapshot/<paths>, snapshot.sha256.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys

PR_FOOTER = (
    "\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\n"
    "https://claude.ai/code/session_016H76AkDcCiXYbCPvFZoorS\n"
)
COMMIT_TRAILERS = (
    "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
    "Claude-Session: https://claude.ai/code/session_016H76AkDcCiXYbCPvFZoorS\n"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deliverables", required=True)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    with open(os.path.join(a.deliverables, "manifest.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    with open(os.path.join(a.deliverables, "pr_body.txt"), encoding="utf-8") as fh:
        body = fh.read()
    first, _, rest = body.partition("\n")
    if not first.startswith("TITLE:"):
        print("REFUSED: pr_body.txt line 1 is not 'TITLE: ...'")
        return 1
    title = first[len("TITLE:"):].strip()
    with open(os.path.join(a.deliverables, "commit_body.txt"), encoding="utf-8") as fh:
        commit_body = fh.read().rstrip("\n")

    paths, skipped = [], []
    for f in manifest["files"]:
        p = f["path"]
        if f.get("status") == "deleted":
            print("REFUSED: deletions are not handled by this prep (%s)" % p)
            return 1
        if p.startswith("util/ad-hoc/") or p.startswith("tmp/"):
            skipped.append(p)
            continue
        paths.append(p)

    os.makedirs(a.out, exist_ok=True)
    snap = os.path.join(a.out, "snapshot")
    if os.path.exists(snap):
        print("REFUSED: %s exists; a snapshot is frozen once taken" % snap)
        return 1
    lines = []
    for p in paths:
        src = os.path.join(a.worktree, p)
        dst = os.path.join(snap, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        with open(dst, "rb") as fh:
            lines.append("%s  %s" % (hashlib.sha256(fh.read()).hexdigest(), p))
    with open(os.path.join(a.out, "snapshot.sha256"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(a.out, "title.txt"), "w", encoding="utf-8") as fh:
        fh.write(title + "\n")
    with open(os.path.join(a.out, "pr_body.txt"), "w", encoding="utf-8") as fh:
        fh.write(rest.strip("\n") + PR_FOOTER)
    with open(os.path.join(a.out, "commit_body.txt"), "w", encoding="utf-8") as fh:
        fh.write(commit_body + COMMIT_TRAILERS)
    with open(os.path.join(a.out, "paths.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(paths) + "\n")
    print("title: %s" % title)
    print("paths: %d (skipped %d: %s)" % (len(paths), len(skipped), ", ".join(skipped) if skipped else "-"))
    print("base_sha (manifest): %s" % manifest.get("base_sha"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
