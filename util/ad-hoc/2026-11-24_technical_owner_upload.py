#!/usr/bin/env python3
"""
Upload the technical-owner sweep as GitHub-signed commits on a new branch made at main, then verify every blob.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — migration (the technical-owner sweep that follows juniper-ml#2606)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/push_signed_commit.py (makes each signed commit); util/ad-hoc/2026-11-23_pr2606_upload.py (the
    batching and the blob check this follows)

Why this exists
---------------
The sweep's 116 files are 12 MB, too much for one ``createCommitOnBranch`` call. The branch is made at the
exact main the files were built from (``--base``), never at the live main, so a merge that lands on main
during the upload can only make the PR behind, never be reverted by a whole-file upload.

Steps (``--execute``; the default is a dry run that prints the plan)
-------------------------------------------------------------------
1. refuse unless the worktree's HEAD is ``--base`` and nothing is staged; report whether main has moved
2. create ``refs/heads/BRANCH`` at ``--base`` (refused if the branch exists)
3. one signed commit per batch of at most ``--batch-bytes`` (paths sorted, so a rerun is deterministic), each
   pinned to the head before it
4. verify: each uploaded path's blob on the final head equals ``git hash-object`` of the local file, and
   the compare ``--base...head`` lists exactly the uploaded paths

Usage
-----
    python3 util/ad-hoc/2026-11-24_technical_owner_upload.py --worktree . --base SHA --branch NAME
        --paths-file FILE --message HEADLINE --body-file FILE [--batch-bytes 3000000] [--execute]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

OWNER, REPO = "pcalnon", "juniper-ml"
HERE = os.path.dirname(os.path.abspath(__file__))
PUSH = os.path.join(HERE, "..", "push_signed_commit.py")


def run(cmd: list[str], cwd: str | None = None) -> str:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"FAILED {' '.join(cmd[:6])}: {(proc.stdout + proc.stderr)[-1200:]}")
    return proc.stdout


def gh_json(*args: str):
    return json.loads(run(["gh", "api", *args]))


def batches(wt: str, paths: list[str], limit: int) -> list[list[str]]:
    out, current, size = [], [], 0
    for path in sorted(paths):
        nbytes = os.path.getsize(os.path.join(wt, path))
        if current and size + nbytes > limit:
            out.append(current)
            current, size = [], 0
        current.append(path)
        size += nbytes
    if current:
        out.append(current)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--base", required=True, help="FULL sha of the main the files were built from")
    ap.add_argument("--branch", required=True)
    ap.add_argument("--paths-file", required=True, help="one repository path per line: every file to upload")
    ap.add_argument("--message", required=True, help="commit headline; ' (k/n)' is appended")
    ap.add_argument("--body-file", required=True, help="commit body; its last paragraph is the trailers")
    ap.add_argument("--batch-bytes", type=int, default=3_000_000)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args(argv)
    wt = os.path.abspath(args.worktree)
    head = run(["git", "-C", wt, "rev-parse", "HEAD"]).strip()
    if head != args.base or len(args.base) != 40:
        raise SystemExit(f"REFUSED: the worktree's HEAD {head} is not --base {args.base} (a full sha)")
    if run(["git", "-C", wt, "diff", "--cached", "--name-only"]).strip():
        raise SystemExit("REFUSED: something is staged")
    with open(args.paths_file, encoding="utf-8") as handle:
        paths = [line.strip() for line in handle if line.strip()]
    for path in paths:
        full = os.path.join(wt, path)
        if os.path.islink(full) or not os.path.isfile(full):
            raise SystemExit(f"REFUSED: {path} is not a regular file")
    main_now = gh_json(f"repos/{OWNER}/{REPO}/git/ref/heads/main")["object"]["sha"]
    print(f"base {args.base[:8]}; main now {main_now[:8]}" + ("" if main_now == args.base else " (main has MOVED: the PR will be behind, never reverting)"))
    plan = batches(wt, paths, args.batch_bytes)
    for k, batch in enumerate(plan, 1):
        print(f"batch {k}/{len(plan)}: {len(batch)} file(s), {sum(os.path.getsize(os.path.join(wt, p)) for p in batch):,} bytes")
    if not args.execute:
        print("(dry run)")
        return 0
    exists = subprocess.run(["gh", "api", f"repos/{OWNER}/{REPO}/git/ref/heads/{args.branch}"], capture_output=True, text=True)
    if exists.returncode == 0:
        raise SystemExit(f"REFUSED: branch {args.branch} exists")
    run(["gh", "api", "-X", "POST", f"repos/{OWNER}/{REPO}/git/refs", "-f", f"ref=refs/heads/{args.branch}", "-f", f"sha={args.base}"])
    tip = args.base
    for k, batch in enumerate(plan, 1):
        cmd = ["python3", PUSH, "--repo", REPO, "--branch", args.branch, "--expected-head", tip, "--message", f"{args.message} ({k}/{len(plan)})", "--commit-body-file", args.body_file]
        for path in batch:
            cmd += ["--add", f"{os.path.join(wt, path)}:{path}"]
        out = run(cmd)
        tip = gh_json(f"repos/{OWNER}/{REPO}/git/ref/heads/{args.branch}")["object"]["sha"]
        print(f"batch {k}/{len(plan)} -> {tip[:8]}: {out.strip().splitlines()[-1] if out.strip() else ''}")
    tree = gh_json(f"repos/{OWNER}/{REPO}/git/trees/{tip}?recursive=1")
    if tree.get("truncated"):
        raise SystemExit("VERIFY: the tree listing is truncated; check the blobs another way")
    blobs = {entry["path"]: entry["sha"] for entry in tree["tree"] if entry["type"] == "blob"}
    bad = [p for p in paths if blobs.get(p) != run(["git", "-C", wt, "hash-object", p]).strip()]
    compare = gh_json(f"repos/{OWNER}/{REPO}/compare/{args.base}...{tip}")
    listed = sorted(f["filename"] for f in compare["files"])
    if bad or listed != sorted(paths):
        raise SystemExit(f"VERIFY FAILED: {len(bad)} blob mismatch(es) {bad[:5]}; compare lists {len(listed)} path(s), uploaded {len(paths)}")
    print(f"VERIFIED: {len(paths)} blob(s) equal the local files; the compare lists exactly them. head {tip}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
