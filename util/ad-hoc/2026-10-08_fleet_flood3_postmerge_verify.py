#!/usr/bin/env python3
"""2026-10-08_fleet_flood3_postmerge_verify.py -- prove each merged flood-3 PR's content is on main, by blob.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 3, 2026-10-04..06)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License
Created: 2026-10-08
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

WHY THIS EXISTS

A PR that reads MERGED has not necessarily shipped its last push (a pinned merge net can land an
older head; a squash can be built from a different object than the one reviewed). The content is
the claim, so this compares, for every file the PR changed, the blob at the PR's final head with
the blob on `main` -- through the contents API, so no local checkout is involved.

    SAME      blob identical on main                                   -> landed intact
    MOVED     differs, and a LATER commit on main touched the file     -> reported with that commit
    DIFFERS   differs and nothing later explains it                    -> a real loss: investigate
    DELETED   removed by the PR and absent on main                     -> landed

Usage:
    2026-10-08_fleet_flood3_postmerge_verify.py --data util/ad-hoc/2026-10-08_fleet_flood3_disposition.json [--extra repo:pr ...]

`--extra` adds PRs that are not in the data file (the carrier / consolidation PRs).

Exit: 0 everything SAME/DELETED/MOVED; 1 any DIFFERS; 2 a read failed.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv gh invocations, no shell
import sys
from pathlib import Path

OWNER = "pcalnon"


def gh_json(path: str):
    res = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=120, check=False)  # nosec B603 B607
    if res.returncode != 0:
        if '"Not Found"' in res.stdout or "404" in res.stderr:
            return None
        raise RuntimeError(f"{path}: {res.stderr.strip()[:200]}")
    return json.loads(res.stdout)


def blob_sha(repo: str, path: str, ref: str) -> str | None:
    data = gh_json(f"repos/{OWNER}/{repo}/contents/{path}?ref={ref}")
    return None if data is None else data.get("sha")


def later_touch(repo: str, path: str, since: str) -> str | None:
    commits = gh_json(f"repos/{OWNER}/{repo}/commits?path={path}&sha=main&since={since}&per_page=5") or []
    return commits[0]["sha"][:8] if commits else None


def verify(repo: str, n: int) -> tuple[str, list[str]]:
    pr = gh_json(f"repos/{OWNER}/{repo}/pulls/{n}")
    if not pr or not pr.get("merged"):
        return "NOT-MERGED", []
    head, merged_at = pr["head"]["sha"], pr["merged_at"]
    files = gh_json(f"repos/{OWNER}/{repo}/pulls/{n}/files?per_page=100") or []
    lines, worst = [], "SAME"
    for f in files:
        path = f["filename"]
        at_head = blob_sha(repo, path, head)
        on_main = blob_sha(repo, path, "main")
        if at_head is None and on_main is None:
            verdict = "DELETED"
        elif at_head == on_main:
            verdict = "SAME"
        else:
            touched = later_touch(repo, path, merged_at)
            verdict = f"MOVED (later {touched})" if touched else "DIFFERS"
        if verdict == "DIFFERS":
            worst = "DIFFERS"
        elif verdict.startswith("MOVED") and worst == "SAME":
            worst = "MOVED"
        lines.append(f"    {verdict:20s} {path}")
    return worst, lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--extra", action="append", default=[], metavar="REPO:PR")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    targets = [(e["repo"], e["pr"]) for e in data["prs"] if e["route"] == "merged"]
    targets += [(x.split(":")[0], int(x.split(":")[1])) for x in args.extra]
    rc = 0
    for repo, n in targets:
        try:
            worst, lines = verify(repo, n)
        except RuntimeError as exc:
            print(f"READ-FAILED {repo}#{n}: {exc}")
            rc = 2
            continue
        print(f"{worst:10s} {repo}#{n}")
        if args.verbose or worst not in ("SAME",):
            print("\n".join(lines))
        if worst in ("DIFFERS", "NOT-MERGED"):
            rc = max(rc, 1)
    return rc


if __name__ == "__main__":
    sys.exit(main())
