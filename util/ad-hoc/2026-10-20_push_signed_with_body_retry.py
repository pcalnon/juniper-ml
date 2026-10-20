#!/usr/bin/env python3
"""Push large files to an existing branch as GitHub-signed commits, one per file, with a commit BODY and a retry loop.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc)
Application:  canopy E2E validation arc -- Phase 14 landing from turing
Author:       Paul Calnon
Created:      2026-10-20
Status:       ad-hoc -- one-off landing helper; RETAINED as provenance (owner policy 2026-08-25)
Retire when:  RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:      util/push_signed_commit.py (does each commit); util/ad-hoc/2026-10-17_push_signed_with_retry.py (the same
              loop without a commit body; this one adds ``--commit-body-file`` so every commit carries the session's
              attribution trailer)
License:      MIT License

Per file and per attempt: read the branch head; if the file's blob at that head already equals the local bytes, it
landed (a request that errored may still have landed: the HTTP 499 trap); else run push_signed_commit.py pinned to
that head with the body file; on failure back off and retry. Exit 0 every file landed; 1 attempts exhausted; 3 a
permissions error (owner action).

Usage:
    python3 -I util/ad-hoc/2026-10-20_push_signed_with_body_retry.py --repo juniper-ml --branch B --body-file BODY \\
        --file LOCAL:REPOPATH --message "headline" [--file ... --message ...] [--attempts 6]
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess  # noqa: S404 -- gh and the repo's own push script, literal arguments
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUSH = REPO_ROOT / "util" / "push_signed_commit.py"
DELAYS = [30, 60, 120, 240, 300, 300, 300, 300]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def gh(args: list) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=False)  # noqa: S603, S607


def blob_sha(data: bytes) -> str:
    h = hashlib.sha1()  # noqa: S324 -- git's blob id
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


def branch_head(owner: str, repo: str, branch: str) -> str | None:
    r = gh(["api", f"repos/{owner}/{repo}/git/ref/heads/{branch}", "--jq", ".object.sha"])
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def remote_blob(owner: str, repo: str, head: str, path: str) -> str | None:
    r = gh(["api", f"repos/{owner}/{repo}/contents/{path}?ref={head}", "--jq", ".sha"])
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def land(owner: str, repo: str, branch: str, local: str, repo_path: str, message: str, body_file: str, attempts: int) -> int:
    want = blob_sha(Path(local).read_bytes())
    for attempt in range(1, attempts + 1):
        head = branch_head(owner, repo, branch)
        if not head:
            log(f"  could not read the head of {branch}; backing off")
            time.sleep(DELAYS[min(attempt - 1, len(DELAYS) - 1)])
            continue
        if remote_blob(owner, repo, head, repo_path) == want:
            log(f"  {repo_path}: already at {head[:8]} with the local bytes -- landed")
            return 0
        log(f"  {repo_path}: attempt {attempt} on head {head[:8]}")
        r = subprocess.run(  # noqa: S603
            [sys.executable, str(PUSH), "--repo", repo, "--owner", owner, "--branch", branch, "--expected-head", head, "--add", f"{local}:{repo_path}", "--message", message, "--commit-body-file", body_file],
            capture_output=True,
            text=True,
            check=False,
        )
        tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
        log("    " + " | ".join(tail))
        if r.returncode == 0:
            return 0
        if "scope" in (r.stdout + r.stderr) and "workflow" in (r.stdout + r.stderr):
            return 3
        time.sleep(DELAYS[min(attempt - 1, len(DELAYS) - 1)])
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--file", action="append", default=[], metavar="LOCAL:REPOPATH")
    ap.add_argument("--message", action="append", default=[])
    ap.add_argument("--attempts", type=int, default=6)
    args = ap.parse_args()
    if not args.file or len(args.file) != len(args.message) or args.branch in ("main", "master"):
        print("ERROR: give one --message per --file, and a non-default branch", file=sys.stderr)
        return 2
    for spec, message in zip(args.file, args.message, strict=True):
        local, _, repo_path = spec.partition(":")
        log(f"{repo_path} ({Path(local).stat().st_size} bytes)")
        rc = land(args.owner, args.repo, args.branch, local, repo_path, message, args.body_file, args.attempts)
        if rc:
            return rc
    log("every file landed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
