#!/usr/bin/env python3
"""
Open ONE signed PR from a frozen landing snapshot, after re-verifying the freeze, then read every pushed blob back
from the PR head and report the head's Actions runs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 session 4: landing the fix carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/open_signed_pr.py (does the push), util/ad-hoc/2026-11-09_flood4r2_land_snapshot.py (the freeze)

Usage:
  2026-11-09_flood4r2_land_open_pr.py --repo <repo> --branch <branch> --freeze <dir> --texts <dir> [--dry-run]

<freeze> holds paths.txt, snapshot.sha256 and snapshot/; <texts> holds title.txt, pr_body.md, commit_body.txt.
The commit headline is the title. Refuses when any frozen file's sha256 has changed, when main has moved off the
sha the freeze was built on (plan.json), or when the snapshot holds a file paths.txt does not list.
After the push: every added path is fetched from the PR head (contents API, raw) and compared byte for byte.
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


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def gh_bytes(*args: str) -> bytes:
    return subprocess.run(["gh", *args], capture_output=True, check=True).stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--texts", required=True)
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
    live_main = json.loads(gh("api", f"repos/{OWNER}/{args.repo}/commits/main", "--jq", "{sha: .sha}"))["sha"]
    if live_main != plan["main_sha"]:
        print(f"REFUSED: main is {live_main[:8]} now; the freeze was built on {plan['main_sha'][:8]} -- re-freeze")
        return 1
    title = (texts / "title.txt").read_text(encoding="utf-8").strip()
    cmd = [sys.executable, "util/open_signed_pr.py", "--repo", args.repo, "--branch", args.branch, "--base", "main", "--message", title, "--commit-body-file", str(texts / "commit_body.txt"), "--title", title, "--body-file", str(texts / "pr_body.md")]
    for path in adds:
        cmd += ["--add", f"{snapshot / path}:{path}"]
    for path in deletes:
        cmd += ["--delete", path]
    if args.dry_run:
        cmd.append("--dry-run")
    print(f"freeze verified: {len(adds)} adds, {len(deletes)} deletes, main {live_main[:8]}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout[-3000:])
    if proc.returncode != 0:
        print(proc.stderr[-3000:])
        return proc.returncode
    if args.dry_run:
        return 0
    head = json.loads(gh("api", f"repos/{OWNER}/{args.repo}/branches/{args.branch}", "--jq", "{sha: .commit.sha}"))["sha"]
    bad = []
    for path in adds:
        data = gh_bytes("api", "-H", "Accept: application/vnd.github.raw", f"repos/{OWNER}/{args.repo}/contents/{path}?ref={head}")
        if hashlib.sha256(data).hexdigest() != sums[path]:
            bad.append(path)
    for path in deletes:
        probe = subprocess.run(["gh", "api", f"repos/{OWNER}/{args.repo}/contents/{path}?ref={head}"], capture_output=True, text=True)
        if probe.returncode == 0:
            bad.append(f"{path} (still present)")
    verified = gh("api", f"repos/{OWNER}/{args.repo}/commits/{head}", "--jq", ".commit.verification.verified")
    print(f"head {head}: signature verified={verified.strip()}; read back {len(adds) - len([b for b in bad if b in adds])}/{len(adds)} blobs" + (f"; MISMATCH {bad}" if bad else ""))
    time.sleep(20)
    runs = gh("api", f"repos/{OWNER}/{args.repo}/actions/runs?head_sha={head}", "--jq", "[.workflow_runs[] | .name + \"=\" + .status] | join(\", \")")
    print(f"actions runs on {head[:8]} after 20 s: {runs.strip() or 'NONE YET'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
