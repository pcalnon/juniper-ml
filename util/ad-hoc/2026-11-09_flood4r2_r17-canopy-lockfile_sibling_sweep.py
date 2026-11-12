"""
Read-only sweep: which Juniper repos' workflows call `gh api graphql` bare, ahead of an unreachable `.errors` check.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4, owner ruling 17 ("canopy: dead error path"); juniper-canopy lockfile-update.yml

juniper-canopy's lockfile-update.yml says juniper-data, -cascor, -data-client, -cascor-client
and -cascor-worker carry the same regen commit step. This lists, for each repository's
default branch (GitHub contents API, GET only), every workflow line that runs
``gh api graphql`` and whether it has the defect's shape: a bare statement (not inside
``if``, not followed by ``||``, not inside ``$(...)``) with a later ``.errors`` check in the
same file, which ``set -e`` makes unreachable because gh exits 1 on GraphQL errors.

Usage::

    python3 util/ad-hoc/2026-11-09_flood4r2_r17-canopy-lockfile_sibling_sweep.py --out <json path>

Nothing is written to any repository; no mutating request is sent.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess  # nosec B404 - read-only gh api GETs
import sys
from pathlib import Path

OWNER = "pcalnon"
REPOS = (
    "juniper-canopy",
    "juniper-data",
    "juniper-cascor",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-ml",
    "juniper-recurrence",
    "juniper-deploy",
)
GH_GRAPHQL = re.compile(r"\bgh api graphql\b")


def gh_get(path: str) -> object | None:
    proc = subprocess.run(["gh", "api", "-X", "GET", path], capture_output=True, text=True, check=False, timeout=60)  # nosec B603 B607 - read-only GET
    if proc.returncode != 0:
        return None
    return json.loads(proc.stdout)


def classify(text: str) -> list[dict]:
    lines = text.splitlines()
    rows = []
    for number, line in enumerate(lines, start=1):
        code = line.split("#", 1)[0] if line.lstrip().startswith("#") else line
        if not GH_GRAPHQL.search(code):
            continue
        stripped = code.strip()
        bare = stripped.startswith("gh api graphql") and "||" not in stripped and not stripped.startswith("if ")
        later_errors_check = any(".errors" in later and "jq" in later for later in lines[number:])
        rows.append({"line": number, "text": stripped[:200], "bare": bare, "later_errors_check": later_errors_check, "defect_shape": bare and later_errors_check})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = []
    for repo in REPOS:
        listing = gh_get(f"repos/{OWNER}/{repo}/contents/.github/workflows")
        if not isinstance(listing, list):
            report.append({"repo": repo, "error": "no workflow listing"})
            continue
        for entry in listing:
            name = entry.get("name", "")
            if not name.endswith((".yml", ".yaml")):
                continue
            blob = gh_get(f"repos/{OWNER}/{repo}/contents/.github/workflows/{name}")
            if not isinstance(blob, dict) or "content" not in blob:
                report.append({"repo": repo, "workflow": name, "error": "unreadable"})
                continue
            text = base64.b64decode(blob["content"]).decode("utf-8", errors="replace")
            rows = classify(text)
            if rows:
                report.append({"repo": repo, "workflow": name, "blob_sha": blob.get("sha"), "gh_graphql_calls": rows})
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for item in report:
        if "error" in item:
            print(f"{item['repo']}/{item.get('workflow', '')}: {item['error']}")
            continue
        for row in item["gh_graphql_calls"]:
            print(f"{item['repo']}/{item['workflow']}:{row['line']} defect_shape={row['defect_shape']} bare={row['bare']} errors_check_after={row['later_errors_check']}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
