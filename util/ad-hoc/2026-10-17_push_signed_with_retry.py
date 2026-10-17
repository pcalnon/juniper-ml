"""
Push files to an existing branch as GitHub-signed commits, one file per commit, retrying through a flaky link.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-17
Status: ad-hoc — one-off (landing the turing A4/B9 re-land of juniper-ml#2222 through a VPN tunnel)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/push_signed_commit.py (does each commit); notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md
         (the HTTP 499 trap: a large createCommitOnBranch can fail and still land, or land nothing);
         notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md

Why: from turing on 2026-10-17, through an ExpressVPN tunnel, every createCommitOnBranch of 180 KB or more
returned HTTP 499 while about 105 KB landed. Each retry must start from a fresh read of the branch head,
because a request that errored may still have landed. So, per file and per attempt:

  1. read the branch head;
  2. if the file's blob at that head already equals the local bytes, it landed: next file;
  3. otherwise run util/push_signed_commit.py pinned to that head (it verifies signature, parent and blobs);
  4. on failure, back off and go to 1. A permissions error (for example the OAuth `workflow` scope that a
     .github/workflows/ path needs) is not retried: it needs the owner, so the run stops with exit 3.

Exit codes: 0 every file landed; 1 attempts exhausted; 2 usage; 3 permissions (owner action needed).

Usage:
    python3 util/ad-hoc/2026-10-17_push_signed_with_retry.py --repo juniper-ml --branch B \\
        --file LOCAL:REPOPATH --message "headline" [--file ... --message ...] [--attempts 8]
    Each --file pairs with the --message at the same position.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUSH = REPO_ROOT / "util" / "push_signed_commit.py"
DELAYS = [30, 60, 120, 240, 300, 300, 300, 300, 300, 300]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True, timeout=180)


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # nosec B324 -- git's object id, not security


def read_head(owner: str, repo: str, branch: str) -> str | None:
    proc = gh(["api", f"repos/{owner}/{repo}/git/ref/heads/{branch}", "--jq", ".object.sha"])
    sha = proc.stdout.strip()
    return sha if proc.returncode == 0 and len(sha) == 40 else None


def remote_blob(owner: str, repo: str, path: str, ref: str) -> str | None:
    proc = gh(["api", f"repos/{owner}/{repo}/contents/{path}?ref={ref}", "--jq", ".sha"])
    sha = proc.stdout.strip()
    return sha if proc.returncode == 0 and len(sha) == 40 else None


def land(owner: str, repo: str, branch: str, local: str, repo_path: str, message: str, attempts: int) -> int:
    want = blob_sha(Path(local).read_bytes())
    for attempt in range(1, attempts + 1):
        head = read_head(owner, repo, branch)
        if head is None:
            log(f"{repo_path}: attempt {attempt}: could not read the head")
        else:
            if remote_blob(owner, repo, repo_path, head) == want:
                log(f"{repo_path}: landed (blob {want[:12]} at {head[:12]})")
                return 0
            log(f"{repo_path}: attempt {attempt}: pushing on {head[:12]}")
            proc = subprocess.run(
                [sys.executable, str(PUSH), "--repo", repo, "--owner", owner, "--branch", branch, "--expected-head", head, "--add", f"{local}:{repo_path}", "--message", message],
                capture_output=True,
                text=True,
                timeout=900,
            )
            if proc.returncode == 0:
                log(f"{repo_path}: landed and verified on attempt {attempt}")
                return 0
            err = (proc.stdout + proc.stderr).strip().splitlines()
            reason = next((line for line in err if line.startswith(("ERROR", "gh:", "REFUSED"))), err[-1] if err else "?")
            log(f"{repo_path}: attempt {attempt} failed: {reason}")
            if "does not have the correct permissions" in proc.stdout + proc.stderr:
                log(f"{repo_path}: permissions error -- owner action needed; not retrying")
                return 3
        if attempt < attempts:
            delay = DELAYS[min(attempt - 1, len(DELAYS) - 1)]
            log(f"{repo_path}: waiting {delay}s")
            time.sleep(delay)
    return 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--file", action="append", default=[], metavar="LOCAL:REPOPATH")
    ap.add_argument("--message", action="append", default=[])
    ap.add_argument("--attempts", type=int, default=8)
    args = ap.parse_args(argv)
    if not args.file or len(args.file) != len(args.message) or args.branch in ("main", "master"):
        print("ERROR: give one --message per --file, and a non-default branch", file=sys.stderr)
        return 2
    for spec, message in zip(args.file, args.message):
        local, _, repo_path = spec.partition(":")
        if not Path(local).is_file() or not repo_path:
            print(f"ERROR: bad --file {spec!r}", file=sys.stderr)
            return 2
        rc = land(args.owner, args.repo, args.branch, local, repo_path, message, args.attempts)
        if rc != 0:
            log(f"stopped at {repo_path} (exit {rc})")
            return rc
    log("all files landed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
