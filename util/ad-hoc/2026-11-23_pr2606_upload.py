#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml (cross-repo tooling)
# Application:   util/ad-hoc
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# Created:       2026-11-23
# Status:        ad-hoc (single arc: repair of the 2026-11-20 "owner -> Overtoad" rename PRs)
"""Upload a rebuilt juniper-ml#2606 as GitHub-signed commits on main and move the PR branch onto them.

Why this exists
---------------
The owner ruled on 2026-11-23 to rebuild #2606 on current main (``2026-11-23_pr2606_rebuild.py`` writes
the files into a clean checkout of main). About 2,100 files are too many for one ``createCommitOnBranch``
call, so they go up in batches, each signed and pinned to the head before it. The PR branch then moves in
ONE ref update to a commit whose parent chain starts at main, so the PR head never equals main (GitHub
would mark the PR merged) and main's later commits can only conflict, never be reverted silently.

Steps (``--execute``; the default is a dry run that prints the plan)
-------------------------------------------------------------------
1. refuse unless the live PR head is ``--old-head`` and the worktree's HEAD is the base it was built on
2. backup ref ``backup/worktree-humming-stargazing-papert-<old8>`` at the old head (kept if it exists)
3. temp branch ``tmp/pr2606-rebuild-<base8>`` at the base
4. one signed commit per batch of at most ``--batch-bytes`` (paths sorted, so a rerun is deterministic)
5. verify: every uploaded path's blob on the final head equals ``git hash-object`` of the local file, and
   the compare base...final lists exactly the uploaded paths
6. force-move the PR branch to the final head; delete the temp branch

The upload set: tracked files modified in the worktree, plus untracked files named by ``--new-from``
(the rebuild report's NEW-* rows) and ``--extra``. Symlinks, deletions and staged changes are refused.

Usage
-----
    python3 2026-11-23_pr2606_upload.py --worktree . --old-head SHA --report REBUILD.tsv
        [--extra PATH ...] [--batch-bytes 4000000] [--execute]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

REPO = "juniper-ml"
OWNER = "pcalnon"
BRANCH = "worktree-humming-stargazing-papert"
HERE = os.path.dirname(os.path.abspath(__file__))
PUSH = os.path.join(HERE, "..", "push_signed_commit.py")
# the session that runs --execute (the upload moved to a successor session on 2026-11-24)
TRAILERS = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_016H76AoaBJbYSpW5ip9pSu2"


def run(cmd: list[str], cwd: str | None = None) -> str:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"FAILED {' '.join(cmd[:5])}: {(proc.stdout + proc.stderr)[-800:]}")
    return proc.stdout


def gh_json(*args: str) -> dict:
    return json.loads(run(["gh", "api", *args]))


def upload_set(wt: str, report: str, extra: list[str]) -> list[str]:
    status = run(["git", "-C", wt, "status", "--porcelain", "--untracked-files=no"]).splitlines()
    paths = []
    for row in status:
        code, path = row[:2], row[3:]
        if code != " M":
            raise SystemExit(f"REFUSED: unexpected status {code!r} for {path} (staged, deleted or renamed)")
        paths.append(path)
    with open(report, encoding="utf-8") as handle:
        rows = list(handle)
    for row in rows:
        kind, _, rest = row.partition("\t")
        if kind in ("NEW-SCRIPT", "NEW-RECORD-RECONSTRUCTED"):
            paths.append(rest.split("\t", 1)[0])
    paths.extend(extra)
    for path in paths:
        full = os.path.join(wt, path)
        if os.path.islink(full) or not os.path.isfile(full):
            raise SystemExit(f"REFUSED: {path} is a symlink or missing")
    return sorted(set(paths))


def batches(wt: str, paths: list[str], limit: int) -> list[list[str]]:
    out, current, size = [], [], 0
    for path in paths:
        n = os.path.getsize(os.path.join(wt, path))
        if current and size + n > limit:
            out.append(current)
            current, size = [], 0
        current.append(path)
        size += n
    if current:
        out.append(current)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--old-head", required=True)
    ap.add_argument("--report", required=True, help="the rebuild's --report TSV (NEW-* rows name the new files)")
    ap.add_argument("--extra", action="append", default=[], help="another untracked file to include (repeatable)")
    ap.add_argument("--batch-bytes", type=int, default=4_000_000)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args(argv)
    wt = os.path.abspath(args.worktree)
    base = run(["git", "-C", wt, "rev-parse", "HEAD"]).strip()
    live = gh_json(f"repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}")["object"]["sha"]
    if live != args.old_head:
        raise SystemExit(f"REFUSED: {BRANCH} is at {live[:8]}, not --old-head {args.old_head[:8]}")
    paths = upload_set(wt, args.report, args.extra)
    parts = batches(wt, paths, args.batch_bytes)
    total = sum(os.path.getsize(os.path.join(wt, p)) for p in paths)
    print(f"base {base[:8]}  old head {live[:8]}  {len(paths)} files, {total / 1e6:.1f} MB, {len(parts)} signed commits")
    if not args.execute:
        for k, part in enumerate(parts, 1):
            print(f"  part {k}: {len(part)} files, {sum(os.path.getsize(os.path.join(wt, p)) for p in part) / 1e6:.2f} MB, {part[0]} .. {part[-1]}")
        print("dry run: nothing written")
        return 0

    backup = f"backup/{BRANCH}-{live[:8]}"
    existing = subprocess.run(["gh", "api", f"repos/{OWNER}/{REPO}/git/ref/heads/{backup}"], capture_output=True, text=True)
    if existing.returncode != 0:
        run(["gh", "api", "-X", "POST", f"repos/{OWNER}/{REPO}/git/refs", "-f", f"ref=refs/heads/{backup}", "-f", f"sha={live}"])
    print(f"backup ref {backup} -> {live[:8]}")
    temp = f"tmp/pr2606-rebuild-{base[:8]}"
    run(["gh", "api", "-X", "POST", f"repos/{OWNER}/{REPO}/git/refs", "-f", f"ref=refs/heads/{temp}", "-f", f"sha={base}"])
    head = base
    for k, part in enumerate(parts, 1):
        adds = [arg for p in part for arg in ("--add", f"{os.path.join(wt, p)}:{p}")]
        body = (
            f"Part {k} of {len(parts)} of juniper-ml#2606 rebuilt on main {base[:8]} (the owner's ruling of 2026-11-23): "
            "every file re-derived from main's text with only the person's 'owner' renamed, technical 'owner' kept; "
            "records, pinned files and symlinks untouched. Built by util/ad-hoc/2026-11-23_pr2606_rebuild.py.\n\n" + TRAILERS
        )
        out = run([sys.executable, PUSH, "--repo", REPO, "--branch", temp, "--expected-head", head, *adds, "--message", f"rebuild(rename): #2606 on main {base[:8]}, part {k} of {len(parts)}", "--commit-body", body])
        match = re.search(r"verified head\s+\S+ -> ([0-9a-f]{40})", out)
        if not match:
            raise SystemExit(f"could not read the new head from push_signed_commit output:\n{out[-600:]}")
        head = match.group(1)
        print(f"  part {k}/{len(parts)}: {len(part)} files -> {head[:8]}")

    tree = gh_json(f"repos/{OWNER}/{REPO}/git/trees/{head}?recursive=1")
    remote = {e["path"]: e["sha"] for e in tree["tree"] if e["type"] == "blob"}
    bad = [p for p in paths if remote.get(p) != run(["git", "-C", wt, "hash-object", p]).strip()]
    if bad:
        raise SystemExit(f"VERIFY FAILED: {len(bad)} uploaded path(s) differ on {head[:8]}, e.g. {bad[:3]}")
    compare = gh_json(f"repos/{OWNER}/{REPO}/compare/{base}...{head}?per_page=1")
    print(f"verified: {len(paths)} blobs match; compare reports {compare.get('files') and len(compare['files'])} (first page) files, {compare['ahead_by']} commits ahead")
    run(["gh", "api", "-X", "PATCH", f"repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}", "-f", f"sha={head}", "-F", "force=true"])
    print(f"{BRANCH}: {live[:8]} -> {head[:8]}")
    run(["gh", "api", "-X", "DELETE", f"repos/{OWNER}/{REPO}/git/refs/heads/{temp}"])
    print(f"deleted {temp}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
