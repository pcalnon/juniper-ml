#!/usr/bin/env python3
"""
Render the flood-4 record's sec 5 per-PR disposition tables from the carriers' manifests and live PR states.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 disposition record)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md;
         util/ad-hoc/2026-10-08_fleet_flood3_disposition_render.py (round 3's equivalent)

WHY THIS EXISTS
A hand-typed disposition table drifts from what happened. This reads each builder's manifest (per-draft
outcome and one-line reason) and asks GitHub for each draft's live state and each carrier's merge commit, so
every row says what is true at render time. A draft whose carrier has not merged renders as "carrier open".

Usage:
  2026-11-07_flood4_disposition_render.py --config <json> [--out <file>]
Config: {"carriers": [{"repo": "juniper-data", "kind": "tests", "pr": 518, "manifest": "<path>"}, ...],
         "extra": [{"repo": "juniper-ml", "pr": 2404, "kind": "docs", "outcome": "round 3", "reason": "..."}]}
"""

import argparse
import json
import subprocess
import sys

OWNER = "pcalnon"


def gh_pr(repo, n, fields):
    p = subprocess.run(["gh", "pr", "view", str(n), "--repo", "%s/%s" % (OWNER, repo), "--json", fields], capture_output=True, text=True)
    if p.returncode != 0:
        return dict()
    return json.loads(p.stdout)


def cell(s, width=420):
    s = (s or "").replace("|", "\\|").replace("\n", " ").strip()
    return s if len(s) <= width else s[: width - 3] + "..."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    with open(a.config, encoding="utf-8") as fh:
        cfg = json.load(fh)

    rows = dict()
    counts = dict()
    for c in cfg.get("carriers", []):
        repo = c["repo"]
        carrier = gh_pr(repo, c["pr"], "state,mergeCommit") if c.get("pr") else dict()
        merged = carrier.get("state") == "MERGED"
        csha = (carrier.get("mergeCommit") or {}).get("oid", "")[:8]
        with open(c["manifest"], encoding="utf-8") as fh:
            m = json.load(fh)
        for e in m["carried"]:
            n = int(e["pr"])
            live = gh_pr(repo, n, "state,title")
            outcome = e.get("outcome", "carried")
            where = ("#%d (`%s`)" % (c["pr"], csha)) if merged else ("#%s (open)" % c.get("pr") if c.get("pr") else "not opened")
            verb = dict([("carried", "carried in"), ("carried-with-fix", "carried with fixes in"), ("not-carried", "not carried; closed with")]).get(outcome, outcome)
            state = live.get("state", "?")
            rows.setdefault(repo, []).append((n, live.get("title") or e.get("title", ""), c["kind"], "%s %s; **%s**" % (verb, where, state.lower()), e.get("reason", "")))
            key = (repo, outcome)
            counts[key] = counts.get(key, 0) + 1
    for x in cfg.get("extra", []):
        live = gh_pr(x["repo"], x["pr"], "state,title")
        rows.setdefault(x["repo"], []).append((int(x["pr"]), live.get("title", ""), x.get("kind", ""), "%s; **%s**" % (x["outcome"], live.get("state", "?").lower()), x.get("reason", "")))
        key = (x["repo"], x["outcome"])
        counts[key] = counts.get(key, 0) + 1

    # A draft split across two carriers (e.g. a docs draft whose Test Suite Reference line rode in the tests
    # carrier) appears in both manifests: merge it into ONE row, joining its outcomes and evaluations.
    for repo in list(rows):
        merged = dict()
        for n, title, kind, outcome, reason in rows[repo]:
            if n in merged:
                t0, k0, o0, r0 = merged[n]
                merged[n] = (t0 or title, k0 if k0 == kind else "%s + %s" % (k0, kind), "%s; and %s" % (o0, outcome), "%s / %s" % (r0, reason) if reason and reason != r0 else r0)
            else:
                merged[n] = (title, kind, outcome, reason)
        rows[repo] = [(n,) + v for n, v in merged.items()]

    out = []
    for repo in sorted(rows):
        rs = sorted(rows[repo])
        out.append("### %s (%d)" % (repo, len(rs)))
        out.append("")
        out.append("| PR | title | kind | outcome | evaluation |")
        out.append("|---|---|---|---|---|")
        for n, title, kind, outcome, reason in rs:
            out.append("| #%d | %s | %s | %s | %s |" % (n, cell(title, 160), kind, outcome, cell(reason)))
        out.append("")
    text = "\n".join(out)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    print("--- counts: " + ", ".join("%s/%s=%d" % (r, o, n) for (r, o), n in sorted(counts.items())), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
