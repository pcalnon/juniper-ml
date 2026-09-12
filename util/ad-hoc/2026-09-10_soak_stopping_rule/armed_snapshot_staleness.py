#!/usr/bin/env python3
"""Is a PR's armed auto-merge body a STALE snapshot? Read-only, pre-merge.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-11

Why this exists
---------------
GitHub's auto-merge request stores `commitBody` in one of THREE states, and they are not
equally safe:

* ``null``  -- the field was OMITTED at arm time. The repo's ``squash_merge_commit_message``
  (here ``COMMIT_MESSAGES``) is resolved at MERGE time, so commits pushed after arming are
  still included. This is what ``gh pr merge --auto --squash`` with no body flags produces,
  and it is SAFE. ``util/safe_merge.py`` is in this cohort.
* ``""``    -- an actual empty string. It is NOT the same as ``null``: it overrides the repo
  default and the squash lands with NO body at all, immediately, with no push required.
  Measured on juniper-ml#1831, whose landed commit ``63de2fbb`` is a single line.
* non-empty -- an ARM-TIME SNAPSHOT. It lands byte-for-byte, so every commit pushed AFTER the
  arm is silently dropped from the squash message. Measured on juniper-ml#1228, which lost
  ``Allow-Symbol-Loss: method:NetGuaranteeDocTest.test_docstring_states_the_net_is_not_head_pinned``
  from a commit pushed 17 minutes after arming; ``Post-Merge Main Verification`` failed on the
  landed SHA three seconds after the merge.

The hazard is structural in this fleet rather than rare: `strict_required_status_checks_policy`
with `allow_update_branch: false` means an armed PR goes BEHIND on every sibling merge and must
be updated, and each update pushes a commit AFTER the arm.

This measures the third state directly -- it compares each non-merge commit's subject and
trailers against the stored snapshot and reports what is already missing. It does NOT mutate:
it never arms, disarms, merges or pushes. Disarm-and-re-arm is deliberately NOT offered, because
re-arming a mergeable PR MERGES IT ON THE SPOT (observed on three sibling repos 2026-09-11), and
that is precisely the premature merge ``util/safe_merge.py`` exists to prevent.

Usage
-----
    python3 util/ad-hoc/2026-09-10_soak_stopping_rule/armed_snapshot_staleness.py --open
    python3 util/ad-hoc/2026-09-10_soak_stopping_rule/armed_snapshot_staleness.py 1912 1913

Exit 0 clean, 1 if any PR carries a stale or empty snapshot, 2 on usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv, no shell
import sys

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


def classify(pr: int) -> dict:
    meta = json.loads(_gh("api", f"repos/{REPO}/pulls/{pr}"))
    am = meta.get("auto_merge")
    if am is None:
        return {"pr": pr, "state": "NO NET", "risk": "none"}
    body = am.get("commit_message")
    if body is None:
        return {"pr": pr, "state": "NULL (merge-time)", "risk": "none"}
    if body == "":
        return {"pr": pr, "state": "EMPTY STRING", "risk": "TOTAL",
                "note": "overrides the repo default; the squash will land with NO body"}

    commits = json.loads(_gh("api", f"repos/{REPO}/pulls/{pr}/commits", "--paginate"))
    lc = body.lower()
    non_merge = [c for c in commits if len(c.get("parents", [])) == 1]
    # SUBJECTS ARE ONLY EXPECTED IN THE BODY WHEN THERE ARE 2+ COMMITS. GitHub documents
    # COMMIT_MESSAGES as "the commit title and message if the pull request contains only 1
    # commit, or the pull request title and list of commits if it contains 2 or more". So on
    # a single-commit PR the subject belongs in the HEADLINE and its absence from the body is
    # CORRECT -- checking it there reported both live PRs as stale when neither was. Caught
    # 2026-09-11 before it was reported as a finding against another session's work.
    check_subjects = len(non_merge) >= 2
    missing_subjects, missing_trailers = [], []
    for c in non_merge:
        msg = c["commit"]["message"]
        subject = msg.split("\n", 1)[0].strip()
        if check_subjects and subject.lower() not in lc:
            missing_subjects.append((c["sha"][:10], subject[:60]))
        # Trailers are ALWAYS expected: they live in the commit body under both forms.
        for m in TRAILER_RE.finditer(msg):
            t = m.group(0).strip()
            # Case-insensitive: GitHub normalises `Co-Authored-By` to `Co-authored-by`.
            if t.lower() not in lc:
                missing_trailers.append((c["sha"][:10], t[:80]))
    return {
        "pr": pr,
        "state": f"SNAPSHOT {len(body)}ch",
        "risk": "STALE" if (missing_subjects or missing_trailers) else "fresh",
        "missing_subjects": missing_subjects,
        "missing_trailers": missing_trailers,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prs", nargs="*", type=int)
    ap.add_argument("--open", action="store_true", help="check every open PR")
    args = ap.parse_args()

    targets = list(args.prs)
    if args.open:
        rows = json.loads(_gh("api", f"repos/{REPO}/pulls?state=open&per_page=100"))
        targets += [r["number"] for r in rows]
    if not targets:
        ap.error("pass PR numbers or --open")

    bad = 0
    for pr in dict.fromkeys(targets):
        r = classify(pr)
        flag = ""
        if r["risk"] == "STALE":
            flag = "  <-- STALE: these will NOT reach main"
            bad += 1
        elif r["risk"] == "TOTAL":
            flag = "  <-- EMPTY: the whole body is lost"
            bad += 1
        print(f"PR {r['pr']:>5}  {r['state']:<22} risk={r['risk']:<6}{flag}")
        if r.get("note"):
            print(f"           {r['note']}")
        for sha, subj in r.get("missing_subjects", []):
            print(f"           missing commit  {sha}  {subj}")
        for sha, t in r.get("missing_trailers", []):
            print(f"           MISSING TRAILER {sha}  {t}")
    print()
    print(f"{bad} PR(s) carry a stale or empty snapshot.")
    if bad:
        print("Remedy is the OPERATOR's call and is deliberately not automated here:")
        print("  merge now (before another commit lands), or disarm and re-arm with NO body")
        print("  flags so the body resolves at merge time. Re-arming a mergeable PR MERGES IT.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
