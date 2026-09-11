#!/usr/bin/env python3
"""2026-09-11_seqsafety_fanout_status.py -- status of the eight sequence-safety comment PRs.

Project: juniper-ml
Sub-Project: CI documentation integrity (cross-repo fan-out)
Application: ad-hoc status
Author: Paul Calnon
License: MIT License

A fan-out across eight repos has eight independent CI runs, and polling them by hand is
where a red one gets missed -- the eye slides over a wall of near-identical green rows. This
prints one line per PR with the counts that decide whether it can merge, and a final line
that says whether ANY repo is not ready, so the answer is read once rather than reconstructed
eight times.

EXIT CODES

  * 0 -- every PR merged or mergeable-and-green;
  * 1 -- at least one PR has failures or is still running (this is a status, not an error --
    the code just lets a caller loop);
  * 2 -- a PR could not be read. Not folded into 1: unreadable is not the same as not ready.

Usage:
    python3 util/ad-hoc/2026-09-11_seqsafety_fanout_status.py
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 -- fixed argv, no shell

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


def main(argv=None) -> int:
    unreadable, not_ready = [], []
    for repo, num in sorted(PRS.items()):
        p = subprocess.run(  # nosec B603 B607
            [
                "gh", "pr", "view", str(num), "--repo", f"pcalnon/{repo}",
                "--json", "state,mergeStateStatus,statusCheckRollup,url",
            ],
            capture_output=True, text=True, timeout=120,
        )
        if p.returncode != 0:
            unreadable.append(repo)
            print(f"  {repo:24} #{num:<5} UNREADABLE: {p.stderr.strip()[:60]}")
            continue
        d = json.loads(p.stdout)
        roll = d.get("statusCheckRollup") or []
        pending = [c for c in roll if c.get("status") != "COMPLETED"]
        failed = [c for c in roll if c.get("conclusion") in ("FAILURE", "TIMED_OUT", "CANCELLED")]
        state, msta = d.get("state"), d.get("mergeStateStatus")
        flag = ""
        if state != "MERGED" and (pending or failed):
            not_ready.append(repo)
            flag = "  <-- not ready"
        elif state != "MERGED":
            not_ready.append(repo)
        print(
            f"  {repo:24} #{num:<5} {state:<8} {msta:<9} "
            f"checks={len(roll):<3} pending={len(pending):<3} failed={len(failed)}{flag}"
        )
        for c in failed:
            print(f"        FAILED: {c.get('name') or c.get('context')}")

    print(f"\n{len(PRS) - len(not_ready) - len(unreadable)} ready/merged, "
          f"{len(not_ready)} not ready, {len(unreadable)} unreadable")
    if unreadable:
        return 2
    return 1 if not_ready else 0


if __name__ == "__main__":
    raise SystemExit(main())
