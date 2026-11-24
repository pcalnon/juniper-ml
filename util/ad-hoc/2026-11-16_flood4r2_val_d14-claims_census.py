"""
Re-derive the D-14 consumer census on each Juniper repository's origin/main: who calls replay_since or
promote_to_active(replayed_through=...), and who sends a /ws/training resume frame.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator MN2, claims lens, flood-4 session 9)
Created: 2026-11-16
Status: ad-hoc - investigation
Retire when: RETAINED - ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Cursor flood-4 disposition record (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md)

Usage: python3 <this file>
Read-only `git grep` on each repository's origin/main as last fetched (the sha and the FETCH_HEAD time are recorded);
writes <scratch>/census.json.
"""

import json
import subprocess
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
O = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert"
OUT = O / "tmp" / "flood4r2-val" / "d14-claims-lens" / "census.json"
REPOS = ("juniper-ml", "juniper-cascor", "juniper-data", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-canopy", "juniper-deploy", "juniper-recurrence", "juniper-harcot")
PATTERNS = {
    "replay_since": r"replay_since\(",
    "replayed_through": r"replayed_through\s*=",
    "resume_sender": r"[\"']type[\"']\s*:\s*[\"']resume[\"']",
}
EXCLUDE = (":!notes/", ":!**/notes/", ":!prompts/", ":!util/ad-hoc/", ":!reports/", ":!tmp/", ":!**/CHANGELOG.md", ":!docs/", ":!**/docs/", ":!**/*.md")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(JUNIPER / repo), *args], capture_output=True, text=True, check=False)


def main():
    result = {}
    for repo in REPOS:
        if not (JUNIPER / repo).is_dir():
            result[repo] = {"absent": True}
            continue
        sha = git(repo, "rev-parse", "origin/main").stdout.strip()
        head = JUNIPER / repo / ".git" / "FETCH_HEAD"
        row = {"origin_main": sha, "fetch_head_mtime": head.stat().st_mtime if head.exists() else None}
        for key, pattern in PATTERNS.items():
            res = git(repo, "grep", "-n", "-E", pattern, "origin/main", "--", ".", *EXCLUDE)
            hits = [line.split(":", 1)[1] for line in res.stdout.splitlines() if line]
            row[key] = hits
        result[repo] = row
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for repo, row in result.items():
        if row.get("absent"):
            print(repo, "absent")
            continue
        files = {key: sorted({hit.split(":", 1)[0] for hit in row[key]}) for key in PATTERNS}
        print(repo, row["origin_main"][:8], json.dumps(files))


if __name__ == "__main__":
    main()
