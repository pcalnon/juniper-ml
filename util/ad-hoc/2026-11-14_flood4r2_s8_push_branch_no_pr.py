#!/usr/bin/env python3
"""
Push ONE signed commit from a frozen landing snapshot to a NEW branch, open NO pull request, read every pushed blob
back, and optionally dispatch a workflow on the branch -- so a landing is validated on a pushed branch before any pull
request exists for the Overtoad's PR sweeper to arm and merge.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (Cursor flood-4 session 8: the ml-tests landing, whose macOS job log is read BEFORE merging)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_land_open_pr.py (the same freeze checks, then a pull request),
         util/push_signed_commit.py (does the signed commit)

Why: the Overtoad's sweeper arms any open pull request and it merges when its required checks go green (see
reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it in the session memory). A carrier whose evidence must be
read in a CI log before it merges therefore has to be run on a branch with no pull request first. juniper-ml's ci.yml
keeps `workflow_dispatch` for exactly that case, and its macOS job runs every host-tooling suite on a dispatch.

Usage:
  2026-11-14_flood4r2_s8_push_branch_no_pr.py --repo <repo> --branch <new branch> --freeze <dir> --texts <dir>
      [--dispatch ci.yml ...] [--dry-run]

<freeze> holds paths.txt, snapshot.sha256, snapshot/ and plan.json; <texts> holds title.txt and commit_body.txt.
Refuses when any frozen file's sha256 has changed, when main has moved off the freeze's base, when the snapshot holds
a file paths.txt does not list, or when the branch already exists. Opening the pull request later is one
`gh pr create --head <branch>` call: this script never opens one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

OWNER = "pcalnon"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout  # nosec B603 B607 -- fixed argv


def gh_bytes(*args: str) -> bytes:
    return subprocess.run(["gh", *args], capture_output=True, check=True).stdout  # nosec B603 B607 -- fixed argv


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--texts", required=True)
    parser.add_argument("--dispatch", action="append", default=[], help="workflow file to dispatch on the branch after the push (repeatable)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    freeze = Path(args.freeze)
    texts = Path(args.texts)
    snapshot = freeze / "snapshot"
    plan = json.loads((freeze / "plan.json").read_text(encoding="utf-8"))
    sums = {}
    for line in (freeze / "snapshot.sha256").read_text(encoding="utf-8").splitlines():
        digest, path = line.split("  ", 1)
        sums[path] = digest
    adds, deletes = [], []
    for line in (freeze / "paths.txt").read_text(encoding="utf-8").splitlines():
        verb, path = line.split(" ", 1)
        (adds if verb == "add" else deletes).append(path)
    on_disk = sorted(str(p.relative_to(snapshot)) for p in snapshot.rglob("*") if p.is_file())
    if on_disk != sorted(adds):
        print(f"REFUSED: snapshot files {sorted(set(on_disk) ^ set(adds))} differ from paths.txt")
        return 1
    for path in adds:
        if hashlib.sha256((snapshot / path).read_bytes()).hexdigest() != sums[path]:
            print(f"REFUSED: {path} changed since the freeze")
            return 1
    base = plan["main_sha"]
    live_main = json.loads(gh("api", f"repos/{OWNER}/{args.repo}/commits/main", "--jq", "{sha: .sha}"))["sha"]
    if live_main != base:
        print(f"REFUSED: main is {live_main[:8]} now; the freeze was built on {base[:8]} -- re-freeze")
        return 1
    probe = subprocess.run(["gh", "api", f"repos/{OWNER}/{args.repo}/git/ref/heads/{args.branch}", "--jq", ".object.sha"], capture_output=True, text=True)  # nosec B603 B607
    branch_at_base = probe.returncode == 0 and probe.stdout.strip() == base
    if probe.returncode == 0 and not branch_at_base:
        print(f"REFUSED: branch {args.branch} already exists at {probe.stdout.strip()[:8]}, not at the base {base[:8]}")
        return 1
    title = (texts / "title.txt").read_text(encoding="utf-8").strip()
    print(f"freeze verified: {len(adds)} adds, {len(deletes)} deletes, main {base[:8]}; branch {args.branch} " + ("exists at the base" if branch_at_base else "is new"))
    if args.dry_run:
        print("[dry-run] would create the branch at main, push one signed commit, read the blobs back" + (f", dispatch {args.dispatch}" if args.dispatch else ""))
        return 0

    # Run this WITHOUT a wrapper that points DBUS_SESSION_BUS_ADDRESS at a dead bus: gh reads its token from the
    # keyring over D-Bus, and an unauthenticated POST is answered 404 (a GET of a public repository still works).
    if not branch_at_base:
        gh("api", "-X", "POST", f"repos/{OWNER}/{args.repo}/git/refs", "-f", f"ref=refs/heads/{args.branch}", "-f", f"sha={base}")
    cmd = [sys.executable, str(ROOT / "util" / "push_signed_commit.py"), "--repo", args.repo, "--branch", args.branch, "--expected-head", base, "--message", title, "--commit-body-file", str(texts / "commit_body.txt")]
    for path in adds:
        cmd += ["--add", f"{snapshot / path}:{path}"]
    for path in deletes:
        cmd += ["--delete", path]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))  # nosec B603 -- fixed argv
    print(proc.stdout[-3000:])
    if proc.returncode != 0:
        print(proc.stderr[-3000:])
        return proc.returncode

    head = json.loads(gh("api", f"repos/{OWNER}/{args.repo}/branches/{args.branch}", "--jq", "{sha: .commit.sha}"))["sha"]
    bad = []
    for path in adds:
        data = gh_bytes("api", "-H", "Accept: application/vnd.github.raw", f"repos/{OWNER}/{args.repo}/contents/{path}?ref={head}")
        if hashlib.sha256(data).hexdigest() != sums[path]:
            bad.append(path)
    for path in deletes:
        gone = subprocess.run(["gh", "api", f"repos/{OWNER}/{args.repo}/contents/{path}?ref={head}"], capture_output=True, text=True)  # nosec B603 B607
        if gone.returncode == 0:
            bad.append(f"{path} (still present)")
    commit = json.loads(gh("api", f"repos/{OWNER}/{args.repo}/commits/{head}", "--jq", "{verified: .commit.verification.verified, parents: [.parents[].sha]}"))
    print(f"head {head}: signature verified={commit['verified']}; parents {[p[:8] for p in commit['parents']]}; read back {len(adds) - len([b for b in bad if b in adds])}/{len(adds)} blobs" + (f"; MISMATCH {bad}" if bad else ""))
    if bad or commit["parents"] != [base]:
        return 1
    for workflow in args.dispatch:
        gh("workflow", "run", workflow, "--repo", f"{OWNER}/{args.repo}", "--ref", args.branch)
        print(f"dispatched {workflow} on {args.branch}")
    if args.dispatch:
        time.sleep(20)
        runs = gh("api", f"repos/{OWNER}/{args.repo}/actions/runs?head_sha={head}", "--jq", "[.workflow_runs[] | (.id|tostring) + \" \" + .event + \" \" + .name + \"=\" + .status] | join(\", \")")
        print(f"actions runs on {head[:8]} after 20 s: {runs.strip() or 'NONE YET'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
