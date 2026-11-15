#!/usr/bin/env python3
"""
Read today's state of the pull requests the "ml-tests" carrier's texts name, one `gh pr view` each, and save it.

A text that says a pull request is open, a draft, merged, or at a given head is checked against GitHub on the day
it is written: a merge an hour ago makes a validated sentence false. This reads, for every number given, the
state, draft flag, head commit, title, the merge / close / update times and the requirement ids (JR-...) its body
cites, stamps each row with the UTC clock at the moment it was read, and writes the list as JSON. It only reads;
it changes nothing on GitHub.

The repository is the one this checkout's `origin` names (gh resolves it from the working directory).

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_gh_state.py --out <json> N [N ...]

Exit 0 when every number was read; 1 when one could not be.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, the finish of round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_manifest.py (which compares the carried drafts with this file)
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FIELDS = "number,state,isDraft,headRefOid,title,updatedAt,mergedAt,closedAt,mergeCommit,baseRefName,body"
JR_ID = re.compile(r"\bJR-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}\b")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("numbers", nargs="+", type=int)
    args = ap.parse_args()
    rows, failed = [], []
    for number in args.numbers:
        done = subprocess.run(["gh", "pr", "view", str(number), "--json", FIELDS], capture_output=True, text=True, check=False, timeout=120)
        if done.returncode != 0:
            failed.append(f"#{number}: {done.stderr.strip()[:200]}")
            continue
        row = json.loads(done.stdout)
        # The body is not kept: only the requirement ids it cites (a pull request body's `## Requirements` lists them).
        row["jr_ids_in_body"] = sorted(set(JR_ID.findall(row.pop("body", "") or "")))
        row["read_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows.append(row)
        merge = (row.get("mergeCommit") or {}).get("oid", "")
        print(f"#{row['number']} {row['state']} draft={row['isDraft']} head={row['headRefOid'][:10]} merged={row.get('mergedAt')} {merge[:8]} JR={row['jr_ids_in_body'] or 'none'} | {row['title'][:80]}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
        fh.write("\n")
    if failed:
        print("NOT READ:\n" + "\n".join(failed), file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
