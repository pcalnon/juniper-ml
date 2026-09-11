#!/usr/bin/env python3
"""2026-09-11_seqsafety_fanout_open_prs.py -- open the eight sibling comment-drift PRs.

Project: juniper-ml
Sub-Project: CI documentation integrity (cross-repo fan-out)
Application: ad-hoc driver
Author: Paul Calnon
License: MIT License

WHAT THIS DOES

Drives `util/open_signed_pr.py` once per sibling for the `sequence-safety.yml` comment
correction produced by `util/ad-hoc/2026-09-11_seqsafety_comment_fanout.py --out DIR`.

Each PR gets the SAME body but a DIFFERENT commit message, because the message names that
repo's own ruleset id -- the whole claim is "this repo's ruleset requires this context", and
a shared message would make eight PRs assert one repo's evidence.

WHY A DRIVER AND NOT EIGHT COMMANDS

Eight hand-typed invocations is eight chances to paste the wrong repo's patched file into
the wrong repo's PR, and the failure would be invisible: the workflow is near-identical
across siblings, so a mis-paste produces a plausible diff. Here the file, the repo and the
ruleset id all derive from one key.

SAFE TO RE-RUN. `open_signed_pr.py` refuses when the branch or an open PR already exists, so
a partial run is resumed by re-running it; already-done repos report REFUSED and are counted
separately from failures.

EXIT CODES

  * 0 -- every repo opened (or already had its PR);
  * 1 -- at least one repo failed for a reason that is not "already done";
  * 2 -- the patched-file directory is missing or incomplete.

Usage:
    python3 util/ad-hoc/2026-09-11_seqsafety_fanout_open_prs.py --patched DIR [--dry-run]
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
from pathlib import Path

BRANCH = "ci/sequence-safety-required-comment-drift"
TITLE = "ci(sequence-safety): the header calls a REQUIRED check advisory"
WORKFLOW = ".github/workflows/sequence-safety.yml"

# repo -> its own ruleset id, read from the live API by
# util/ad-hoc/2026-09-11_fleet_required_context_probe.py on 2026-09-11.
RULESETS = {
    "juniper-cascor": 15081045,
    "juniper-canopy": 14249530,
    "juniper-data": 14748749,
    "juniper-data-client": 13316681,
    "juniper-cascor-client": 13490605,
    "juniper-cascor-worker": 14250447,
    "juniper-deploy": 14715370,
    "juniper-recurrence": 20634527,
}

MESSAGE = """ci(sequence-safety): the header calls a REQUIRED check advisory

`Sequence Safety` is a required status check in {repo}'s branch ruleset ({rid}), and
this workflow's header says it is "ADVISORY, NOT a required check" that "never blocks a
merge", with promotion described as a future owner decision. The promotion happened;
nobody edited the header. A reader who trusts it takes a red Sequence Safety for
non-blocking and waits for a merge that cannot happen -- which is how the juniper-ml
instance was found, on ml#1837.

The premise was measured rather than assumed: the 2026-09-09 handoff generalised from
juniper-ml's ruleset to eight repos whose rulesets nobody had read. Were the check
genuinely advisory here, this header would be correct and editing it would introduce the
defect. It is required in all nine.

Comment text only -- the parsed YAML is identical before and after. "Never wired into the
CI Quality Gate" is KEPT, because it is still true and is a different claim from "not
required"; conflating the two is what produced the drift.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_0142dJD2GUxBkoWxbieagNGQ"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--patched", required=True, help="directory of <repo>.yml patched files")
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--repos", nargs="*", default=sorted(RULESETS))
    args = ap.parse_args(argv)

    patched = Path(args.patched)
    missing = [r for r in args.repos if not (patched / f"{r}.yml").is_file()]
    if missing:
        print(f"patched file(s) missing for: {', '.join(missing)}", file=sys.stderr)
        return 2

    opened, already, failed = [], [], []
    for repo in args.repos:
        local = patched / f"{repo}.yml"
        cmd = [
            sys.executable, "util/open_signed_pr.py",
            "--repo", repo,
            "--branch", BRANCH,
            "--add", f"{local}:{WORKFLOW}",
            "--message", MESSAGE.format(repo=repo, rid=RULESETS[repo]),
            "--title", TITLE,
            "--body-file", args.body_file,
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # nosec B603
        tail = (p.stdout + p.stderr).strip().splitlines()
        last = tail[-1] if tail else "(no output)"
        if p.returncode == 0:
            opened.append(repo)
            print(f"  OK       {repo:24} {last[:90]}")
        elif p.returncode == 1:
            already.append(repo)
            print(f"  REFUSED  {repo:24} {last[:90]}")
        else:
            failed.append(f"{repo}: {last[:160]}")
            print(f"  FAILED   {repo:24} {last[:90]}")

    print(f"\nopened {len(opened)}, refused/already {len(already)}, failed {len(failed)}")
    if failed:
        print("failures:", file=sys.stderr)
        for f in failed:
            print(f"    {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
