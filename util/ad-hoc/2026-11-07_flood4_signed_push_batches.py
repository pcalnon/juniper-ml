#!/usr/bin/env python3
"""
Open a carrier PR as GitHub-signed commits, in size-bounded batches, from a frozen snapshot.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 carrier PRs)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md;
         auto-memory reference_signed_commit_api_499_on_large_payloads.md (batches of 92-298 KB landed
         with zero 499s; a 499/502 can leave the ref at the base with no commit -- check the ref)

WHY THIS EXISTS
Only GraphQL createCommitOnBranch signs, and both util/open_signed_pr.py and util/push_signed_commit.py
upload WHOLE files. So (1) a carrier must be pushed from a frozen snapshot of its validated files, (2) a
path main changed since the carrier's base would be silently reverted, and (3) a large payload can time
out. This script refuses on (2), batches for (3), and after the last batch reads the branch's tree back
and compares every blob with `git hash-object` of the snapshot file.

Usage:
  2026-11-07_flood4_signed_push_batches.py --repo juniper-data --branch test/flood4-consolidated-tests \
      --base-sha <full sha the carrier was built on> --snapshot <dir holding repo-relative files> \
      --paths <file: one repo path per line> --title <PR title> --body-file <PR body> \
      --commit-body-file <commit body> [--max-batch-bytes 200000] [--dry-run]
Exit 0 = PR opened and every blob verified; 1 = refused before any write; 2 = failed after a write
(inspect the printed state).
"""

import argparse
import json
import os
import subprocess
import sys
import time

OWNER = "pcalnon"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
OPEN_SIGNED = os.path.join(REPO_ROOT, "util", "open_signed_pr.py")
PUSH_SIGNED = os.path.join(REPO_ROOT, "util", "push_signed_commit.py")


def run(cmd, check=True):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode != 0:
        sys.stderr.write("FAILED (%d): %s\n%s\n%s\n" % (p.returncode, " ".join(cmd[:6]), p.stdout[-2000:], p.stderr[-2000:]))
    return p


def gh_json(args):
    p = run(["gh", "api"] + args)
    if p.returncode != 0:
        return None
    return json.loads(p.stdout)


def branch_head(repo, branch):
    d = gh_json(["repos/%s/%s/git/ref/heads/%s" % (OWNER, repo, branch)])
    if not d or "object" not in d:
        return None
    return d["object"]["sha"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--base-sha", required=True)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--paths", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--commit-body-file", required=True)
    ap.add_argument("--max-batch-bytes", type=int, default=200000)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    with open(a.paths, encoding="utf-8") as fh:
        paths = [ln.strip() for ln in fh if ln.strip()]
    missing = [p for p in paths if not os.path.isfile(os.path.join(a.snapshot, p))]
    if missing:
        print("REFUSED: snapshot lacks %s" % missing)
        return 1

    # (2) whole-file clobber guard: nothing main changed since the base may be uploaded.
    main_sha = branch_head(a.repo, "main")
    print("main is %s; carrier base is %s" % (main_sha, a.base_sha))
    if main_sha != a.base_sha:
        cmp = gh_json(["repos/%s/%s/compare/%s...%s" % (OWNER, a.repo, a.base_sha, main_sha)])
        if cmp is None:
            print("REFUSED: compare API failed")
            return 1
        moved = sorted(set(f["filename"] for f in cmp.get("files", [])) & set(paths))
        print("main moved %d commits; carrier paths main touched since base: %s" % (cmp.get("ahead_by", -1), moved))
        if moved:
            print("REFUSED: rebuild those paths on current main first")
            return 1
    if branch_head(a.repo, a.branch) is not None:
        print("REFUSED: branch %s already exists" % a.branch)
        return 1

    # (3) size-bounded batches, input order kept, never splitting a file.
    batches, cur, size = [], [], 0
    for p in paths:
        n = os.path.getsize(os.path.join(a.snapshot, p))
        if cur and size + n > a.max_batch_bytes:
            batches.append(cur)
            cur, size = [], 0
        cur.append(p)
        size += n
    if cur:
        batches.append(cur)
    for i, b in enumerate(batches, 1):
        print("batch %d/%d: %d files, %d bytes" % (i, len(batches), len(b), sum(os.path.getsize(os.path.join(a.snapshot, p)) for p in b)))
    if a.dry_run:
        print("DRY RUN: nothing written")
        return 0

    def adds(b):
        out = []
        for p in b:
            out += ["--add", "%s:%s" % (os.path.join(a.snapshot, p), p)]
        return out

    n = len(batches)
    msg1 = a.title if n == 1 else "%s (1/%d)" % (a.title, n)
    p = run([sys.executable, OPEN_SIGNED, "--repo", a.repo, "--branch", a.branch, "--message", msg1,
             "--commit-body-file", a.commit_body_file, "--title", a.title, "--body-file", a.body_file] + adds(batches[0]), check=False)
    print(p.stdout[-1500:])
    if p.returncode != 0:
        sys.stderr.write(p.stderr[-1500:])
        print("open_signed_pr exit %d; branch head now %s (check before retrying)" % (p.returncode, branch_head(a.repo, a.branch)))
        return 2
    for i, b in enumerate(batches[1:], 2):
        for attempt in range(1, 4):
            head = branch_head(a.repo, a.branch)
            q = run([sys.executable, PUSH_SIGNED, "--repo", a.repo, "--branch", a.branch, "--expected-head", head,
                     "--message", "%s (%d/%d)" % (a.title, i, n), "--commit-body-file", a.commit_body_file] + adds(b), check=False)
            print(q.stdout[-800:])
            if q.returncode == 0:
                break
            after = branch_head(a.repo, a.branch)
            print("batch %d attempt %d exit %d; head %s -> %s" % (i, attempt, q.returncode, head, after))
            if after != head:
                print("head moved during a failed push: stop and inspect")
                return 2
            time.sleep(10 * attempt)
        else:
            return 2

    # read back: every snapshot blob must equal the branch's blob at that path.
    head = branch_head(a.repo, a.branch)
    tree = gh_json(["repos/%s/%s/git/trees/%s?recursive=1" % (OWNER, a.repo, head)])
    blobs = dict((t["path"], t["sha"]) for t in tree.get("tree", []) if t.get("type") == "blob")
    bad = []
    for path in paths:
        local = run(["git", "hash-object", os.path.join(a.snapshot, path)]).stdout.strip()
        if blobs.get(path) != local:
            bad.append((path, local, blobs.get(path)))
    print("read-back at %s: %d/%d blobs match" % (head, len(paths) - len(bad), len(paths)))
    for b in bad:
        print("MISMATCH %s local=%s branch=%s" % b)
    return 0 if not bad else 2


if __name__ == "__main__":
    sys.exit(main())
