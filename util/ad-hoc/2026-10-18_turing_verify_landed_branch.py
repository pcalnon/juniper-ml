"""
Independently verify a branch landed from turing: exact file set vs base, every blob equals local, every commit GitHub-verified.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-18
Status: ad-hoc — one-off (landing the turing bring-up Session 1 PRs juniper-ml#2242, #2245, #2247, #2249 and the A5 PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-17_push_signed_with_retry.py (does the pushes this checks);
         notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md

Why: the retry driver verifies each commit as it lands, but a branch built one file per commit can still end up
with a stray or missing path, or a blob that matches an older local copy. Before opening each PR this re-reads the
whole branch from scratch: `git diff --name-only BASE...origin/BRANCH` must equal the expected set exactly, every
expected blob must equal `git hash-object` of the local file, a path prefixed with "-" must be absent on the
branch, and every commit in BASE..BRANCH must carry `verification.verified == true` (required_signatures).

Usage:
    python3 -I util/ad-hoc/2026-10-18_turing_verify_landed_branch.py REPO BASE_SHA BRANCH PATH [PATH ...] [-DELETED_PATH ...]

Exit 0 when the branch is exactly right; 1 otherwise.
"""
import json
import subprocess
import sys

repo, base, branch, *args = sys.argv[1:]
# A path prefixed with "-" must be deleted on the branch.
deleted = {a[1:] for a in args if a.startswith("-")}
paths = [a[1:] if a.startswith("-") else a for a in args]


def run(*args: str) -> str:
    return subprocess.run(list(args), check=True, capture_output=True, text=True).stdout


run("git", "fetch", "origin", "--quiet")
ref = f"origin/{branch}"
changed = sorted(run("git", "diff", "--name-only", f"{base}...{ref}").split())
want = sorted(paths)
ok = changed == want
print(f"file set {'MATCHES' if ok else 'DIFFERS'}: {len(changed)} changed vs {len(want)} expected")
if not ok:
    print("  changed only:", sorted(set(changed) - set(want)))
    print("  expected only:", sorted(set(want) - set(changed)))

for p in want:
    if p in deleted:
        gone = subprocess.run(["git", "cat-file", "-e", f"{ref}:{p}"], capture_output=True).returncode != 0
        ok &= gone
        print(f"{'GONE' if gone else 'STILL-PRESENT'}  {p}")
        continue
    remote = run("git", "rev-parse", f"{ref}:{p}").strip()
    local = run("git", "hash-object", p).strip()
    same = remote == local
    ok &= same
    print(f"{'SAME' if same else 'DIFF'}  {p}")

shas = run("git", "rev-list", f"{base}..{ref}").split()
for sha in shas:
    c = json.loads(run("gh", "api", f"repos/pcalnon/{repo}/commits/{sha}", "--jq", "{v: .commit.verification.verified, r: .commit.verification.reason, m: (.commit.message|split(\"\\n\")[0])}"))
    ok &= bool(c["v"])
    print(f"{'VERIFIED' if c['v'] else 'UNVERIFIED'} ({c['r']})  {sha[:8]}  {c['m']}")

print("BRANCH OK" if ok else "BRANCH NOT OK")
sys.exit(0 if ok else 1)
