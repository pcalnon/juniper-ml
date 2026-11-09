#!/usr/bin/env python3
"""
Close the drafts a merged flood-4 carrier carried, each with a comment naming the carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 draft closes)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; flood-3 record sec 6
         ("A named carrier slot that resolves to nothing must block a close")

WHY THIS EXISTS
The owner's ruling (2026-11-06, re-granted 2026-11-07): a carried draft is closed, with a comment naming its
carrier, ONLY after that carrier merges. This refuses unless the carrier PR is MERGED, skips any draft that is
no longer open, and skips (reporting it) any draft whose head moved after the builder carried it -- new
content on a draft would otherwise be closed away unread. Default is a dry run that prints every comment.

Usage:
  2026-11-07_flood4_close_carried.py --repo juniper-data --carrier-pr 519 --manifest <manifest.json> \
      [--only 509,510] [--execute]
"""

import argparse
import json
import subprocess
import sys

OWNER = "pcalnon"
RECORD = "notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md"


def gh(args):
    p = subprocess.run(["gh"] + args, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def pr_json(repo, n, fields):
    rc, out, _err = gh(["pr", "view", str(n), "--repo", "%s/%s" % (OWNER, repo), "--json", fields])
    if rc != 0:
        return None
    return json.loads(out)


def clip(items, limit=4, width=260):
    out = []
    for it in (items or [])[:limit]:
        s = str(it).replace("\n", " ").strip()
        out.append(s if len(s) <= width else s[: width - 3] + "...")
    if items and len(items) > limit:
        out.append("(+%d more in the carrier's PR body)" % (len(items) - limit))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--carrier-pr", type=int, required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()

    carrier = pr_json(a.repo, a.carrier_pr, "state,mergeCommit,title")
    if not carrier or carrier.get("state") != "MERGED" or not carrier.get("mergeCommit"):
        print("REFUSED: carrier #%d is not MERGED (%s)" % (a.carrier_pr, carrier and carrier.get("state")))
        return 1
    sha = carrier["mergeCommit"]["oid"][:8]
    with open(a.manifest, encoding="utf-8") as fh:
        m = json.load(fh)
    only = set(int(x) for x in a.only.split(",") if x.strip())
    rc_all = 0
    for c in m["carried"]:
        n = int(c["pr"])
        if only and n not in only:
            continue
        cur = pr_json(a.repo, n, "state,headRefOid,isDraft")
        if not cur:
            print("#%d: SKIP (could not read)" % n)
            rc_all = 2
            continue
        if cur["state"] != "OPEN":
            print("#%d: SKIP (already %s)" % (n, cur["state"]))
            continue
        want = (c.get("head_sha") or "").strip()
        if want and not cur["headRefOid"].startswith(want[:7]) and not want.startswith(cur["headRefOid"][:7]):
            print("#%d: SKIP -- head moved since carried (carried %s, now %s); re-evaluate it" % (n, want[:8], cur["headRefOid"][:8]))
            rc_all = 2
            continue
        outcome = c.get("outcome", "carried")
        lines = ["Closing: this draft's content was evaluated under the owner's flood-4 consolidation ruling (2026-11-06) and %s **#%d** (squash-merged as `%s`)." % ("is carried by" if outcome != "not-carried" else "was considered for", a.carrier_pr, sha)]
        if outcome == "not-carried":
            lines.append("")
            lines.append("**Not carried:** %s" % (c.get("reason") or "see the carrier's PR body"))
        else:
            taken = clip(c.get("taken"))
            fixes = clip(c.get("fixes"))
            dropped = clip(c.get("dropped"))
            if taken:
                lines.append("")
                lines.append("**Taken:** " + "; ".join(taken))
            lines.append("")
            lines.append("**Fixed on the way in:** " + ("; ".join(fixes) if fixes else "nothing -- carried as drafted"))
            if dropped:
                lines.append("")
                lines.append("**Dropped:** " + "; ".join(dropped))
        lines.append("")
        lines.append("A carried draft is closed only after its carrier merges. GitHub keeps this PR's diff. The disposition is recorded in juniper-ml `%s`." % RECORD)
        body = "\n".join(lines)
        print("=== #%d (%s) ===\n%s\n" % (n, outcome, body))
        if a.execute:
            rc, out, err = gh(["pr", "close", str(n), "--repo", "%s/%s" % (OWNER, a.repo), "--comment", body])
            print("#%d: close exit %d %s" % (n, rc, (err or out).strip()[:200]))
            if rc != 0:
                rc_all = 2
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
