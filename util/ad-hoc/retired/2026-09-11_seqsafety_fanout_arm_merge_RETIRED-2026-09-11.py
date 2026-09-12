#!/usr/bin/env python3
"""
RETIRED 2026-09-11 — ITS CENTRAL PREMISE IS INVERTED. DO NOT RUN.

Status: retired 2026-09-11 (kept for provenance; it was executed against eight repos)

This script's docstring states:

    "GitHub's auto-merge net stores its own commit subject/body, and when armed WITHOUT
     them both fields are `null`. A squash that fires on a null body ships the SUBJECT
     ONLY -- dropping the [body]"

That is backwards, and independent consensus over 1877 PRs established the opposite:

* A `null` body is the SAFE state. The field was omitted at arm time, so the repository's
  `squash_merge_commit_message` (COMMIT_MESSAGES on all nine repos) resolves at MERGE
  time and the full body lands. Measured: 60 single-parent commits pushed AFTER arming,
  across 48 PRs, ZERO lost, at lags up to 40.7 hours. juniper-ml#1797 landed a
  26,052-character message from a null-body arm.
* A NON-NULL body is an ARM-TIME SNAPSHOT and is the hazard this script was meant to
  avoid. It binds when the net fires, so every commit pushed after the arm is dropped.
  Of the 29 PRs with a post-arm single-parent commit, 23 lost that commit's body.
  juniper-ml#1228 lost an `Allow-Symbol-Loss:` waiver that way and `Post-Merge Main
  Verification` failed on the landed SHA three seconds later; juniper-ml#1877 silently
  lost nine commit messages.

So this script installs the defect it was written to prevent. Two further problems:

* It arms from `commits[0]["messageBody"]` -- the FIRST commit only -- so on any
  multi-commit PR every later commit's message is dropped BY CONSTRUCTION, with no
  post-arm push required at all.
* It accepts `commitBody | length > 0` as "the only proof the arm took". `length` is 0
  for BOTH `null` and `""`, which is precisely the indistinguishability that produced the
  superseded diagnosis. The correct discriminator is the value, not its length.

It also performs `--disable-auto` then re-arms, a sequence that MERGES a mergeable PR on
the spot -- observed here on three sibling repos on 2026-09-11.

Replacement, none of which mutates auto-merge state:

* `util/safe_merge.py` `stale_snapshot_refusal` -- refuses at entry on a stored empty body.
* `util/ad-hoc/2026-09-10_soak_stopping_rule/armed_snapshot_staleness.py` -- measures
  whether an open PR's stored snapshot is already missing a commit.
* `util/ad-hoc/2026-09-10_soak_stopping_rule/trailer_loss_check.py` -- measures, after the
  fact, whether a merged PR's squash body lost a trailer its source commits carried.

The eight sibling PRs it armed have all merged; five landed from a snapshot body. Nothing
here needs re-running -- the correct action for a future fan-out is to arm with NO body
flags and let the default resolve at merge time.

ORIGINAL DOCSTRING FOLLOWS.
"""

"""2026-09-11_seqsafety_fanout_arm_merge.py -- arm auto-merge on the eight fan-out PRs, with a BODY.

Project: juniper-ml
Sub-Project: CI documentation integrity (cross-repo fan-out)
Application: ad-hoc driver
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS AND NOT `gh pr merge --auto` EIGHT TIMES

GitHub's auto-merge net stores its own commit subject/body, and when armed WITHOUT them both
fields are `null`. A squash that fires on a null body ships the SUBJECT ONLY -- dropping the
commit message and, with it, the `Co-Authored-By:` / `Claude-Session:` trailers. Measured on
juniper-ml#1886 and #1890 in this same session: both were completed BY THE NET rather than by
a local merge, so arming it with a body was load-bearing, not belt-and-braces.

Worse, the obvious repair silently does nothing:

    gh pr merge N --squash --auto --subject ... --body-file ...   # on an ALREADY-ARMED PR
    -> exit 0, no output, fields still null

So each PR is DISARMED first and then re-armed, and the result is read back -- a non-zero
`commitBody | length` is the only proof the arm took. `null` and `""` both render as length 0
in jq, so "it looks empty" cannot distinguish armed-empty from not-armed.

The body is each PR's OWN first commit message, fetched per repo. These PRs were opened by
`util/open_signed_pr.py`, so that message is the full rationale including the repo's own
ruleset id -- sharing one body across eight repos would make eight PRs assert one repo's
evidence.

EXIT CODES

  * 0 -- every PR armed with a non-empty body (or already merged);
  * 1 -- at least one PR could not be armed, or read back with an empty body;
  * 2 -- nothing to do.

Usage:
    python3 util/ad-hoc/2026-09-11_seqsafety_fanout_arm_merge.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
import tempfile
from pathlib import Path

PRS = {
    "juniper-canopy": 617,
    "juniper-cascor": 643,
    "juniper-cascor-client": 162,
    "juniper-cascor-worker": 182,
    "juniper-data": 393,
    "juniper-data-client": 198,
    "juniper-deploy": 210,
    "juniper-recurrence": 167,
}


def _gh(args, check=False):
    p = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=180)  # nosec B603 B607
    if check and p.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])}: {p.stderr.strip()[:200]}")
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    failures: list = []
    for repo, num in sorted(PRS.items()):
        ref = f"pcalnon/{repo}#{num}"
        p = _gh(["pr", "view", str(num), "--repo", f"pcalnon/{repo}", "--json",
                 "state,commits,title,autoMergeRequest"])
        if p.returncode != 0:
            failures.append(f"{ref}: unreadable")
            print(f"  {repo:24} UNREADABLE")
            continue
        d = json.loads(p.stdout)
        if d.get("state") == "MERGED":
            print(f"  {repo:24} already MERGED")
            continue

        commits = d.get("commits") or []
        if not commits:
            failures.append(f"{ref}: no commits")
            print(f"  {repo:24} NO COMMITS")
            continue
        msg = commits[0].get("messageBody") or ""
        headline = commits[0].get("messageHeadline") or d.get("title") or ""
        if not msg.strip():
            failures.append(f"{ref}: commit body is empty -- refusing to arm with nothing")
            print(f"  {repo:24} EMPTY COMMIT BODY -- refusing")
            continue

        if args.dry_run:
            print(f"  {repo:24} would arm: subject={headline[:40]!r} body={len(msg)} chars")
            continue

        # DISARM FIRST. Re-arming an already-armed PR is a silent no-op.
        if d.get("autoMergeRequest"):
            _gh(["pr", "merge", str(num), "--repo", f"pcalnon/{repo}", "--disable-auto"])

        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write(msg)
            body_path = fh.name
        try:
            arm = _gh([
                "pr", "merge", str(num), "--repo", f"pcalnon/{repo}",
                "--squash", "--auto",
                "--subject", f"{headline} (#{num})",
                "--body-file", body_path,
            ])
        finally:
            Path(body_path).unlink(missing_ok=True)

        if arm.returncode != 0:
            failures.append(f"{ref}: arm failed: {arm.stderr.strip()[:120]}")
            print(f"  {repo:24} ARM FAILED: {arm.stderr.strip()[:70]}")
            continue

        # Read back -- the only proof the arm took. STATE FIRST: `--auto` on a PR that is
        # already mergeable MERGES IT IMMEDIATELY rather than arming, and the PR then has no
        # autoMergeRequest at all. Reading `commitBody` first conflates "armed with nothing"
        # with "merged, so there is no net to inspect" -- which is exactly what the first run
        # of this tool did, reporting three successful merges (cascor-client#162, deploy#210,
        # recurrence#167) as empty-body failures. Their squashes carry the full body.
        back = _gh(["pr", "view", str(num), "--repo", f"pcalnon/{repo}",
                    "--json", "autoMergeRequest,state"])
        bd = json.loads(back.stdout)
        if bd.get("state") == "MERGED":
            print(f"  {repo:24} MERGED immediately (was already mergeable)")
            continue
        got = (bd.get("autoMergeRequest") or {}).get("commitBody") or ""
        if not got:
            failures.append(f"{ref}: armed but commitBody is EMPTY")
            print(f"  {repo:24} ARMED WITH EMPTY BODY -- the no-op case")
            continue
        print(f"  {repo:24} armed, body={len(got)} chars")

    print(f"\n{len(PRS) - len(failures)} of {len(PRS)} armed/merged; {len(failures)} failure(s)")
    if failures:
        for f in failures:
            print(f"    {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
