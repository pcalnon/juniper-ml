#!/usr/bin/env python3
"""
Compact live census of the Juniper ecosystem for re-baselining a plan: open PRs, recent merges, releases, PyPI.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-05
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (state refresh for v1.2.0)

Read-only: GitHub REST via ``gh api`` and the PyPI JSON API. No GraphQL (its quota is shared). Prints:
open PRs per repo (author / draft counts, non-bot PRs listed), merges to main since ``--since``, the newest GitHub
Release per repo, and the PyPI version of each published package.

It fails closed (round 9, R9A-08): a read that fails prints UNREADABLE, never "0 open" or "none", and the exit status
is then 3. A page that comes back full says that more may exist.

Usage
-----
    python3 util/ad-hoc/2026-10-05_ecosystem_live_census.py --since 2026-10-04T22:27:00Z
"""
import argparse
import collections
import datetime
import json
import subprocess
import sys
import urllib.request

REPOS = ["juniper-ml", "juniper-data", "juniper-data-client", "juniper-cascor", "juniper-cascor-client", "juniper-cascor-worker", "juniper-canopy", "juniper-deploy", "juniper-recurrence"]
PACKAGES = ["juniper-ml", "juniper-data", "juniper-cascor", "juniper-canopy", "juniper-recurrence", "juniper-observability", "juniper-service-core", "juniper-cascor-model", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker"]


FAILED = []


def gh(path):
    """GET a GitHub REST path. On any failure, record it and return None, so the caller prints UNREADABLE."""
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if out.returncode == 0:
        try:
            return json.loads(out.stdout)
        except json.JSONDecodeError:
            pass  # an unparsable body is a failed read: recorded below, so the caller prints UNREADABLE
    FAILED.append(path)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True, help="an ISO 8601 time with a zone, such as 2026-10-08T13:38:00Z")
    args = ap.parse_args()
    # GitHub answers a malformed `since` with success and no commits, which reads as "no merges" (round 10, R10A-07)
    try:
        when = datetime.datetime.fromisoformat(args.since.replace("Z", "+00:00"))
    except ValueError:
        when = None
    if when is None or when.tzinfo is None or "T" not in args.since:
        print(f"--since {args.since!r}: not an ISO 8601 time with a zone; nothing was read", file=sys.stderr)
        return 3
    # a future time reads as "no merges" too, and GitHub misreads some valid forms (`+00:00` decodes as a blank, a week
    # date as another day), so refuse the one and send the other as UTC with a Z (round 11: R11A-09, R11B1-10)
    if when > datetime.datetime.now(datetime.timezone.utc):
        print(f"--since {args.since!r}: in the future; nothing was read", file=sys.stderr)
        return 3
    args.since = when.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print("== open PRs")
    for r in REPOS:
        prs = gh(f"repos/pcalnon/{r}/pulls?state=open&per_page=100")
        if prs is None:
            print(f"{r}: UNREADABLE (gh api failed)")
            continue
        by = collections.Counter((p["user"]["login"], p["draft"]) for p in prs)
        humans = [f"#{p['number']} {p['title'][:70]}" for p in prs if not p["user"]["login"].endswith("[bot]")]
        print(f"{r}: {len(prs)} open; " + ", ".join(f"{u}{'(draft)' if d else ''}={n}" for (u, d), n in sorted(by.items())))
        if len(prs) == 100:
            print("     (a full page of 100: more may be open)")
        for h in humans:
            print("    ", h)
    print("== merges to main since", args.since)
    for r in REPOS:
        commits = gh(f"repos/pcalnon/{r}/commits?sha=main&since={args.since}&per_page=50")
        if commits is None:
            print(f"{r}: UNREADABLE (gh api failed)")
            continue
        for c in commits:
            print(f"{r}: {c['sha'][:8]} {c['commit']['committer']['date']} {c['commit']['message'].splitlines()[0][:100]}")
        if len(commits) == 50:
            print(f"{r}: (a full page of 50: more may have merged)")
    print("== newest GitHub Release per repo")
    for r in REPOS:
        rel = gh(f"repos/pcalnon/{r}/releases?per_page=1")
        if rel is None:
            print(f"{r}: UNREADABLE (gh api failed)")
            continue
        print(f"{r}: " + (f"{rel[0]['tag_name']} {rel[0]['published_at']}" if rel else "none"))
    print("== PyPI")
    for p in PACKAGES:
        try:
            d = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{p}/json", timeout=20))
            v = d["info"]["version"]
            up = max((f["upload_time_iso_8601"] for f in d["releases"].get(v, [])), default="?")
            print(f"{p}: {v} ({up})")
        except Exception as exc:  # noqa: BLE001 — a census reports what it could not read
            FAILED.append(p)
            print(f"{p}: UNREADABLE ({type(exc).__name__})")
    if FAILED:
        print(f"INCOMPLETE: {len(FAILED)} read(s) failed; a failed read is not '0 open' or 'none'", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
