#!/usr/bin/env python3
"""
Copy the owner's ``CODECOV_TOKEN`` into each Juniper repository's Dependabot secret store, so a Dependabot PR's Codecov upload is authenticated like any other PR's.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-04
Status: ad-hoc — one-off (flood-3: owner ruling 2026-11-04, "add CODECOV_TOKEN to all active repos' dependabot secrets")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§4 Codecov row, §6); util/ad-hoc/2026-10-29_codecov_token_secret_census.py

The OWNER runs this, in a real terminal (it needs a TTY for the hidden prompt):

    python3 -I util/ad-hoc/2026-11-04_set_codecov_token_dependabot_secrets.py            # one token for every repo
    python3 -I util/ad-hoc/2026-11-04_set_codecov_token_dependabot_secrets.py --per-repo # a prompt per repo (Enter reuses the previous one)
    python3 -I util/ad-hoc/2026-11-04_set_codecov_token_dependabot_secrets.py --dry-run  # prompts and validates, sets nothing

GitHub never returns a secret's value, so the token cannot be copied from the Actions store; it is typed (or pasted) at a
``getpass`` prompt. It is never printed, logged, put in argv or written to disk: it reaches ``gh secret set --app dependabot``
on stdin only. A value that is not a 36-character UUID (the shape every Codecov upload log here reports, "Token length: 36")
is refused before anything is set. Afterwards each store is re-read with a ``gh api`` GET and its ``updated_at`` printed.
Exit 0 when every repository holds the secret, 1 otherwise.
"""

from __future__ import annotations

import argparse
import getpass
import json
import re
import subprocess  # nosec B404 - fixed gh argv, no shell
import sys

REPOS = ["juniper-ml", "juniper-cascor", "juniper-data", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-canopy", "juniper-deploy", "juniper-recurrence"]
NAME = "CODECOV_TOKEN"
UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def ask(prompt: str) -> str:
    value = getpass.getpass(prompt).strip()
    if value and not UUID.match(value):
        raise SystemExit(f"refused: the value is {len(value)} characters and not a UUID; nothing was set")
    return value


def stored(repo: str) -> str | None:
    p = subprocess.run(["gh", "api", f"repos/pcalnon/{repo}/dependabot/secrets"], capture_output=True, text=True)  # nosec B603 B607
    if p.returncode != 0:
        return None
    for s in json.loads(p.stdout).get("secrets", []):
        if s["name"] == NAME:
            return s["updated_at"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-repo", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("repos", nargs="*", default=REPOS)
    args = ap.parse_args()
    if not sys.stdin.isatty():
        raise SystemExit("refused: run this in a terminal (the token is read at a hidden prompt)")
    tokens: dict[str, str] = {}
    previous = ""
    for repo in args.repos if args.per_repo else args.repos[:1]:
        label = repo if args.per_repo else "all repositories"
        value = ask(f"{NAME} for {label}{' (Enter = previous)' if previous else ''}: ") or previous
        if not value:
            raise SystemExit("refused: empty value; nothing was set")
        tokens[repo] = previous = value
    if not args.per_repo:
        tokens = {r: previous for r in args.repos}
    failed = 0
    for repo in args.repos:
        if args.dry_run:
            print(f"{repo}\tDRY-RUN (valid UUID, not set)")
            continue
        p = subprocess.run(["gh", "secret", "set", NAME, "--app", "dependabot", "-R", f"pcalnon/{repo}"], input=tokens[repo], capture_output=True, text=True)  # nosec B603 B607
        when = stored(repo)
        ok = p.returncode == 0 and when is not None
        failed += not ok
        print(f"{repo}\t{'SET' if ok else 'FAILED'}\tupdated_at={when}" + ("" if ok else f"\t{p.stderr.strip()[:160]}"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
