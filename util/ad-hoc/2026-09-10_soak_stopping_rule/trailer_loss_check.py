#!/usr/bin/env python3
"""Did a merged PR's squash commit lose any git trailer its source commits carried?

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-11

Why this exists
---------------
A NON-null `commitBody` on a GitHub auto-merge request is an ARM-TIME SNAPSHOT: any commit
pushed after arming is silently dropped from the squash message. Measured once in anger --
juniper-ml#1228 lost `Allow-Symbol-Loss: method:NetGuaranteeDocTest.test_docstring_states_the_
net_is_not_head_pinned` from a commit pushed 17 minutes after arming, and `Post-Merge Main
Verification` failed on the landed SHA three seconds after the merge.

`null` does NOT have this problem: it defers to the repo's `squash_merge_commit_message`
(here `COMMIT_MESSAGES`), which is resolved at MERGE time.

This checks the consequence directly, on the artifacts, rather than reasoning about arming:
for each PR, collect every trailer on every non-merge source commit, and report any that is
absent from the landed squash body.

Usage
-----
    python3 util/ad-hoc/2026-09-10_soak_stopping_rule/trailer_loss_check.py 1884 1894 1904
    python3 util/ad-hoc/2026-09-10_soak_stopping_rule/trailer_loss_check.py --recent 40

Read-only: `gh api` reads and `git log` reads. Mutates nothing.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv, no shell

REPO = "pcalnon/juniper-ml"
TRAILER_RE = re.compile(
    r"^(?:Allow-Symbol-Loss|Allow-Docs-Rewrite|Allow-Ceiling-Raise|Allow-Budget-Overrun|"
    r"Co-Authored-By|Claude-Session|Signed-off-by):.*$",
    re.IGNORECASE | re.MULTILINE,
)


def _gh(*args: str) -> str:
    return subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["gh", *args], capture_output=True, text=True, check=True
    ).stdout


def _git(*args: str) -> str:
    return subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def check(pr: int) -> dict:
    meta = json.loads(_gh("api", f"repos/{REPO}/pulls/{pr}"))
    if not meta.get("merged_at"):
        return {"pr": pr, "state": "NOT MERGED"}
    sha = meta["merge_commit_sha"]
    snap = (meta.get("auto_merge") or {}).get("commit_message")
    commits = json.loads(_gh("api", f"repos/{REPO}/pulls/{pr}/commits", "--paginate"))

    src: set[str] = set()
    for c in commits:
        if len(c.get("parents", [])) == 1:  # non-merge source commit
            src |= {m.group(0).strip() for m in TRAILER_RE.finditer(c["commit"]["message"])}

    try:
        body = _git("log", "-1", "--format=%B", sha)
    except subprocess.CalledProcessError:
        return {"pr": pr, "state": "SHA NOT LOCAL", "sha": sha}

    # CASE-INSENSITIVE. GitHub NORMALISES `Co-Authored-By:` to `Co-authored-by:` when it
    # aggregates co-authors, so an exact substring test reports a loss that did not happen.
    # Caught on ml#1894 and ml#1228, where the only true loss is the `Allow-Symbol-Loss:`
    # line. A check that cannot tell a rename from a removal is not a check.
    body_lc = body.lower()
    lost = sorted(t for t in src if t.lower() not in body_lc)
    return {
        "pr": pr,
        "sha": sha[:12],
        "arm": "NULL (merge-time)" if snap is None else f"SNAPSHOT {len(snap)}ch",
        "src_trailers": len(src),
        "lost": lost,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prs", nargs="*", type=int)
    ap.add_argument("--recent", type=int, default=0,
                    help="also check the N most recently merged PRs")
    args = ap.parse_args()

    targets = list(args.prs)
    if args.recent:
        rows = json.loads(_gh("pr", "list", "--repo", REPO, "--state", "merged",
                              "--limit", str(args.recent), "--json", "number"))
        targets += [r["number"] for r in rows]

    if not targets:
        ap.error("pass PR numbers or --recent N")

    bad = 0
    print(f"{'PR':>6}  {'sha':<13} {'arming':<20} {'trailers':>8}  lost")
    for pr in dict.fromkeys(targets):
        r = check(pr)
        if "lost" not in r:
            print(f"{pr:>6}  {r.get('state')}")
            continue
        mark = "" if not r["lost"] else "  <-- LOSS"
        bad += bool(r["lost"])
        print(f"{r['pr']:>6}  {r['sha']:<13} {r['arm']:<20} {r['src_trailers']:>8}  "
              f"{len(r['lost'])}{mark}")
        for t in r["lost"]:
            print(f"          LOST: {t[:100]}")
    print()
    print(f"{bad} PR(s) lost a trailer.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
