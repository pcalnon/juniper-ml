#!/usr/bin/env python3
"""
Read each draft the ml-docs carrier claims to carry: its fetched head, its merge base with main, its own diff, and its
state on GitHub, so the manifest's "carried" table can be checked against the drafts themselves.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (Cursor flood-4 session 8: the ml-docs carrier's claims-lens validation, check B)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/ml-docs-s8/ (the validator's deliverables); juniper-ml#2479 #2483 #2487 #2494 #2490 #2470 #2484

Run from a juniper-ml checkout whose refs/flood4r2v/pr/<N> heads are fetched. Read-only: ``gh pr view`` only.

Usage:
  2026-11-14_flood4r2_val_ml-docs_drafts.py --manifest <manifest.json> --main origin/main --out <dir>
"""

import argparse
import json
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, check=True, text=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--main", default="origin/main")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(args.manifest, encoding="utf-8") as fh:
        manifest = json.load(fh)
    rows = []
    for item in manifest["carried"]:
        number = item.get("pr")
        if number is None:
            continue
        ref = f"refs/flood4r2v/pr/{number}"
        head = run(["git", "rev-parse", ref]).strip()
        base = run(["git", "merge-base", args.main, ref]).strip()
        stat = run(["git", "diff", "--numstat", base, ref])
        diff = run(["git", "diff", base, ref])
        (out / f"draft_{number}.diff").write_text(diff, encoding="utf-8")
        commits = run(["git", "log", "--format=%h %s", f"{base}..{ref}"])
        view = json.loads(run(["gh", "pr", "view", str(number), "--repo", "pcalnon/juniper-ml", "--json", "number,title,state,isDraft,headRefOid,headRefName"]))
        files = [line.split("\t") for line in stat.splitlines() if line]
        rows.append({
            "pr": number,
            "manifest_head": item.get("head_sha"),
            "fetched_head": head,
            "head_matches_manifest": head == item.get("head_sha"),
            "gh": view,
            "gh_head_matches_fetched": view.get("headRefOid") == head,
            "merge_base": base,
            "commits": commits.splitlines(),
            "files": [{"added": f[0], "deleted": f[1], "path": f[2]} for f in files],
        })
    (out / "drafts.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        print(row["pr"], row["gh"]["state"], "draft" if row["gh"]["isDraft"] else "ready", "head==manifest:", row["head_matches_manifest"], "gh==fetched:", row["gh_head_matches_fetched"], "base", row["merge_base"][:8], len(row["commits"]), "commits")
        for f in row["files"]:
            print("   ", f["added"], f["deleted"], f["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
