#!/usr/bin/env python
"""Upload a local branch's change to its GitHub branch as signed commits, in payload-sized groups, each pinned to the last.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9: landing the ledger's PR)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/push_signed_commit.py (each group is one call of its ``main``);
         memory reference_signed_commit_api_499_on_large_payloads.md

WHY. ``required_signatures`` is on and a local commit cannot be signed headless, so the only signed path is
GraphQL ``createCommitOnBranch``. Payloads of ~330 KB have come back HTTP 499 or 502, and some of those LANDED
anyway; a single 327 KB file landed on its third try (memory note reference_signed_commit_api_499_on_large_payloads).
Phase 9's change is well over a hundred files and ~2.5 MB, and the ledger alone is over 750 KB. So:

  * it refuses unless the tree is clean and --base is an ancestor of HEAD, so the bytes it uploads are
    exactly HEAD's and every file it does not upload keeps --base's content (round 4 of the ledger's
    validation, Lane R4-B, found the first version checked neither);

  * the files changed between --base and HEAD are packed, in path order, into groups of at most --max-bytes
    raw bytes (base64 adds a third); the ledger goes alone, last;
  * each group is one ``util/push_signed_commit.py`` call whose ``--expected-head`` is the previous group's
    commit, which must read back as the child of the one before it;
  * a call that fails is re-read before any retry: a head that moved to a child of the pinned one is a commit
    that landed despite the error, and anything else stops the run;
  * at the end, every uploaded path's blob on the branch head is compared with HEAD's blob here.

It refuses deletions and renames (not needed here, so not handled), and a branch not at --base.

Usage:
    gh api -X POST repos/pcalnon/juniper-ml/git/refs -f ref=refs/heads/<branch> -f sha=<full base sha>
    python3 util/ad-hoc/2026-09-24_push_phase9_signed_groups.py --base <full base sha> --branch <branch> [--dry-run]
"""

import argparse
import json
import subprocess  # nosec B404 - read-only git/gh helpers
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "util"))
import push_signed_commit as psc  # noqa: E402

SLUG = "pcalnon/juniper-ml"
LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"


def _out(*argv: str) -> str:
    return subprocess.run(argv, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout  # nosec B603


def branch_head(branch: str) -> str:
    return _out("gh", "api", f"repos/{SLUG}/branches/{branch}", "--jq", ".commit.sha").strip()


def parents_of(sha: str) -> list:
    return json.loads(_out("gh", "api", f"repos/{SLUG}/commits/{sha}", "--jq", "[.parents[].sha]"))


def pack(files: list, max_bytes: int) -> list:
    rest = sorted(f for f in files if f != LEDGER)
    groups, cur, size = [], [], 0
    for f in rest:
        n = (REPO_ROOT / f).stat().st_size
        if cur and size + n > max_bytes:
            groups.append(cur)
            cur, size = [], 0
        cur.append(f)
        size += n
    if cur:
        groups.append(cur)
    if LEDGER in files:
        groups.append([LEDGER])
    return groups


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, type=psc.full_sha, help="FULL sha the GitHub branch was created at")
    ap.add_argument("--branch", required=True)
    ap.add_argument("--max-bytes", type=int, default=250_000)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if _out("git", "status", "--porcelain").strip():
        print("REFUSED: the working tree is not clean, so the uploaded bytes would not be HEAD's", file=sys.stderr)
        return 1
    if subprocess.run(["git", "merge-base", "--is-ancestor", args.base, "HEAD"], cwd=REPO_ROOT, check=False).returncode != 0:  # nosec B603 B607
        print(f"REFUSED: --base {args.base} is not an ancestor of HEAD; rebase onto it first", file=sys.stderr)
        return 1
    status = [ln.split("\t") for ln in _out("git", "diff", "--name-status", args.base, "HEAD").splitlines() if ln]
    odd = [s for s in status if s[0] not in ("A", "M")]
    if odd:
        print(f"REFUSED: deletions/renames are not handled: {odd[:5]}", file=sys.stderr)
        return 1
    files = [s[1] for s in status]
    groups = pack(files, args.max_bytes)
    for i, g in enumerate(groups, 1):
        print(f"group {i}/{len(groups)}: {len(g)} files, {sum((REPO_ROOT / f).stat().st_size for f in g)} bytes")
    head = args.base
    if not args.dry_run and branch_head(args.branch) != head:
        print(f"REFUSED: {args.branch} is not at --base {head}", file=sys.stderr)
        return 1
    for i, g in enumerate(groups, 1):
        what = "the ledger" if g == [LEDGER] else f"{len(g)} files"
        argv = ["--repo", "juniper-ml", "--branch", args.branch, "--expected-head", head,
                "--message", f"docs(canopy-e2e): Phase 9 ledger PR, signed upload {i}/{len(groups)} -- {what}"]
        for f in g:
            argv += ["--add", f"{REPO_ROOT / f}:{f}"]
        if args.dry_run:
            if psc.main(argv + ["--dry-run"]) != 0:
                return 1
            continue
        for attempt in range(1, 6):
            rc = psc.main(argv)
            if rc != 0:
                time.sleep(20)  # a 499/502 commit can land after the client gave up: read the ref only after a pause
            now = branch_head(args.branch)
            if now != head:
                if parents_of(now) != [head]:
                    print(f"STOPPED: {args.branch} moved to {now}, which is not a child of {head}", file=sys.stderr)
                    return 1
                print(f"group {i}: landed as {now}{'' if rc == 0 else f' (despite exit {rc})'}")
                head = now
                break
            if rc == 0:
                print(f"STOPPED: exit 0 but {args.branch} did not move from {head}", file=sys.stderr)
                return 1
            print(f"group {i}: attempt {attempt} failed (exit {rc}) and nothing landed; retrying", file=sys.stderr)
        else:
            return 1
    if args.dry_run:
        print("dry run: nothing written")
        return 0
    bad = []
    for f in files:
        mine = _out("git", "rev-parse", f"HEAD:{f}").strip()
        theirs = _out("gh", "api", f"repos/{SLUG}/contents/{f}?ref={head}", "--jq", ".sha").strip()
        if mine != theirs:
            bad.append(f)
    print(f"blobs: {len(files) - len(bad)} of {len(files)} match HEAD's; head {head}")
    for f in bad:
        print(f"  MISMATCH {f}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
