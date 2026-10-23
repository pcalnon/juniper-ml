#!/usr/bin/env python3
"""List the PRs merged since a release tag that a CHANGELOG section never mentions.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc — one-off (pre-flight for the juniper-cascor 0.12.0 and juniper-data 0.17.1 cuts)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: memory reference_release_train_ceremony_traps_2026-09-09 (seventh trap: the notes ship
         the CHANGELOG section, and nothing checks it describes the release)

Why
---
The ceremony renders the Release body from the CHANGELOG's ``[<version>]`` section, and a
Release body cannot be re-cut. A fix PR that merged without touching the CHANGELOG ships in the
wheel but not in the notes (canopy 0.8.0 lost three poll fixes that way). This compares every
squash-merge subject ``… (#NNN)`` in ``<tag>..<ref>`` with the ``#NNN`` references inside the
section, and prints the PRs the section never names. A PR the section describes WITHOUT its
number is reported too; a human reads each one and decides.

Usage
-----
    2026-10-10_changelog_pr_coverage.py --repo-dir <checkout> --tag v0.11.0 [--ref origin/main] \
        [--section Unreleased] [--changelog CHANGELOG.md]

Exit 0 when every PR is referenced, 1 when any is not, 2 on misuse.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
from pathlib import Path

_SUBJECT_PR = re.compile(r"\(#(\d+)\)\s*$")


def _section(text: str, name: str) -> str:
    pat = re.compile(r"^##\s*\[" + re.escape(name) + r"\]", re.IGNORECASE)
    out, inside = [], False
    for line in text.splitlines():
        if pat.match(line):
            inside = True
            continue
        if inside and re.match(r"^##\s", line) and not line.startswith("###"):
            break
        if inside:
            out.append(line)
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-dir", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--section", default="Unreleased")
    ap.add_argument("--changelog", default="CHANGELOG.md")
    args = ap.parse_args(argv)
    repo = Path(args.repo_dir).resolve()
    log = subprocess.run(  # nosec B603 B607
        ["git", "log", "--first-parent", "--format=%h%x09%s", f"{args.tag}..{args.ref}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    text = subprocess.run(  # nosec B603 B607
        ["git", "show", f"{args.ref}:{args.changelog}"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    section = _section(text, args.section)
    if not section.strip():
        print(f"section [{args.section}] is empty or absent in {args.ref}:{args.changelog}", file=sys.stderr)
        return 2
    referenced = set(re.findall(r"#(\d+)", section))
    missing, covered, unnumbered = [], 0, []
    for line in log:
        sha, _, subject = line.partition("\t")
        m = _SUBJECT_PR.search(subject)
        if not m:
            unnumbered.append(f"{sha} {subject}")
            continue
        if m.group(1) in referenced:
            covered += 1
        else:
            missing.append(f"#{m.group(1)} {sha} {subject}")
    print(f"{len(log)} first-parent commits in {args.tag}..{args.ref}; {covered} PRs referenced in [{args.section}]")
    for row in missing:
        print(f"  NOT REFERENCED  {row}")
    for row in unnumbered:
        print(f"  NO PR NUMBER    {row}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
