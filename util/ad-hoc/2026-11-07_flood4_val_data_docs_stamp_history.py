"""
Print each juniper-data doc's version/date stamp history on main, commit by commit (flood-4 docs validator).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 juniper-data docs carrier validation (juniper-data #509, #510, #511, #515)

Usage: python3 2026-11-07_flood4_val_data_docs_stamp_history.py <juniper-data repo> <base sha> <carrier worktree> [<draft ref> ...]

For each touched doc: every commit on <base sha> that changed it since 2026-10-01, with the header and footer
stamp lines after that commit; then the carrier's stamps; then each draft head's stamps. Read-only.
"""

import re
import subprocess
import sys

DOCS = [
    "docs/DEVELOPER_CHEATSHEET.md",
    "docs/DOCUMENTATION_OVERVIEW.md",
    "docs/QUICK_START.md",
    "docs/REFERENCE.md",
    "docs/USER_MANUAL.md",
    "docs/ci_cd/CICD_MANUAL.md",
    "docs/ci_cd/CICD_QUICK_START.md",
    "docs/ci_cd/CICD_REFERENCE.md",
]

STAMP = re.compile(r"\*\*(Version|Last Updated|Date):?\*\*:?\s*([^|*\n]+)")


def run(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True).stdout


def stamps(text):
    lines = text.splitlines()
    head = [ln for ln in lines[:12] if STAMP.search(ln)]
    foot = [ln for ln in lines[-6:] if STAMP.search(ln)]
    return head, foot


def main():
    repo, base, carrier = sys.argv[1], sys.argv[2], sys.argv[3]
    drafts = sys.argv[4:]
    for doc in DOCS:
        print(f"==== {doc}")
        log = run(repo, "log", "--format=%h %ad %s", "--date=short", "--since=2026-09-01", base, "--", doc).splitlines()
        for entry in reversed(log):
            sha = entry.split()[0]
            head, foot = stamps(run(repo, "show", f"{sha}:{doc}"))
            print(f"  {entry[:110]}")
            print(f"      head={head} foot={foot}")
        with open(f"{carrier}/{doc}", encoding="utf-8") as fh:
            head, foot = stamps(fh.read())
        print(f"  CARRIER head={head} foot={foot}")
        for ref in drafts:
            text = run(repo, "show", f"{ref}:{doc}")
            if text:
                head, foot = stamps(text)
                print(f"  DRAFT {ref} head={head} foot={foot}")


if __name__ == "__main__":
    main()
