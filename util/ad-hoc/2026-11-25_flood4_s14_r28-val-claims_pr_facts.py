"""
Read merge facts and changed files of juniper-canopy PRs, and map PR head branches to PR numbers (gh GETs only).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 claims lens of carrier r28 (juniper-canopy's load-sensitive relay test).

Usage:
    python3 -I <this file> --repo pcalnon/juniper-canopy --out <file.json> --prs 773 783 ... --branches <b1> <b2> ...
        [--watch <path> ...]

For each PR: `gh pr view N --json number,title,state,mergedAt,mergeCommit,headRefName,baseRefName,createdAt,files`;
the output keeps the file list only for paths named by --watch (prefix match) plus the total file count. For each
branch: `gh pr list --state all --head B --json number,title,state,mergedAt,createdAt`. Nothing is written to GitHub.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - fixed gh argv lists, no shell
import sys
from pathlib import Path


def gh_json(argv: list[str]):
    cp = subprocess.run(["gh", *argv], capture_output=True, text=True, check=False)  # nosec B603 B607 - fixed argv
    if cp.returncode != 0:
        return {"error": cp.stderr.strip()[:400]}
    return json.loads(cp.stdout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prs", nargs="*", default=[])
    ap.add_argument("--branches", nargs="*", default=[])
    ap.add_argument("--watch", nargs="*", default=[])
    args = ap.parse_args()
    result: dict = {"prs": {}, "branches": {}}
    for n in args.prs:
        d = gh_json(["pr", "view", str(n), "--repo", args.repo, "--json", "number,title,state,mergedAt,mergeCommit,headRefName,baseRefName,createdAt,files"])
        if isinstance(d, dict) and "files" in d:
            files = [f.get("path") for f in d.get("files") or []]
            d["files_total"] = len(files)
            d["files_watched"] = [p for p in files if any(p.startswith(w) for w in args.watch)]
            del d["files"]
            mc = d.get("mergeCommit") or {}
            d["mergeCommit"] = mc.get("oid") if isinstance(mc, dict) else mc
        result["prs"][str(n)] = d
    for b in args.branches:
        result["branches"][b] = gh_json(["pr", "list", "--repo", args.repo, "--state", "all", "--head", b, "--json", "number,title,state,mergedAt,createdAt"])
    Path(args.out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    for n, d in result["prs"].items():
        if "error" in d:
            print(f"#{n}: ERROR {d['error']}")
        else:
            print(f"#{n}: {d['state']} mergedAt={d.get('mergedAt')} merge={str(d.get('mergeCommit'))[:8]} head={d.get('headRefName')} files={d.get('files_total')} watched={d.get('files_watched')} :: {d.get('title')[:90]}")
    for b, d in result["branches"].items():
        print(f"{b}: {[(x.get('number'), x.get('state'), x.get('mergedAt')) for x in d] if isinstance(d, list) else d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
