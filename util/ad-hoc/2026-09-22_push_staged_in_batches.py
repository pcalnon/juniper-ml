#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Land this worktree's STAGED files on an existing PR branch as size-capped GitHub-signed commits.

A headless session cannot sign locally (the signing subkey needs a YubiKey touch), and one
``createCommitOnBranch`` call carrying ~3 MB risks the HTTP 499 recorded in memory
(``reference_signed_commit_api_499_on_large_payloads``). This batches the staged set by size and hands
each batch to ``util/ad-hoc/push_signed_commit.py``. That tool pins ``--expected-head``, and after each
commit it re-reads every file it wrote and compares bytes. Before every batch this re-reads the branch
head with ``git ls-remote``, so a concurrent push fails loudly rather than being clobbered.

Files whose bytes already match the branch head are skipped, so a re-run after a partial failure
resumes where it stopped. Deletions are not handled: it refuses if the staged set contains any.

Usage:
    python3 util/ad-hoc/2026-09-22_push_staged_in_batches.py --branch <branch> --message "<headline>" \\
        --commit-body-file <body.txt> [--max-bytes 800000] [--dry-run]
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUSH = ROOT / "util" / "ad-hoc" / "push_signed_commit.py"


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument("--commit-body-file", required=True)
    ap.add_argument("--max-bytes", type=int, default=800_000)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    status = _git("diff", "--cached", "--name-status").splitlines()
    if any(line.startswith("D") for line in status):
        print("REFUSED: the staged set contains a deletion; this tool only adds", file=sys.stderr)
        return 1
    paths = [line.split("\t", 1)[1] for line in status if line]
    _git("fetch", "origin", args.branch)
    pending = []
    for p in paths:
        local = (ROOT / p).read_bytes()
        try:
            remote = subprocess.run(["git", "-C", str(ROOT), "show", f"FETCH_HEAD:{p}"], check=True, capture_output=True).stdout
        except subprocess.CalledProcessError:
            remote = None
        if remote != local:
            pending.append((p, len(local)))
    print(f"{len(paths)} staged, {len(pending)} differ from the branch head")

    batches, cur, size = [], [], 0
    for p, n in pending:
        if cur and size + n > args.max_bytes:
            batches.append(cur)
            cur, size = [], 0
        cur.append(p)
        size += n
    if cur:
        batches.append(cur)

    for i, batch in enumerate(batches, 1):
        head = _git("ls-remote", "origin", f"refs/heads/{args.branch}").split()[0]
        cmd = [sys.executable, str(PUSH), "--repo", "juniper-ml", "--branch", args.branch, "--expected-head", head,
               "--message", f"{args.message} ({i}/{len(batches)})", "--commit-body-file", args.commit_body_file]
        for p in batch:
            cmd += ["--add", f"{ROOT / p}:{p}"]
        if args.dry_run:
            cmd.append("--dry-run")
        print(f"batch {i}/{len(batches)}: {len(batch)} files on head {head[:8]}", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
        for line in tail:
            print(f"  {line}")
        if r.returncode != 0:
            print(f"STOPPED at batch {i}: exit {r.returncode}. Re-run to resume; landed files are skipped.", file=sys.stderr)
            return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
