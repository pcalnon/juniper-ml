#!/usr/bin/env python3
"""
Check that juniper-data v0.16.0's published Release notes describe the commit its tag names.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register evidence, APD-ML-007)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use verifier
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

APD-ML-007: the release ceremony renders only the FIRST `## [<version>]` heading of the CHANGELOG it is
given, and by default tags the owning repo's main as it is at cut time, so the notes and the tag can
describe different trees. juniper-data 0.16.0 was exposed to both: #428 merged after the bump and left a
second `## [0.16.0]` heading. juniper-data#435 folded everything into one section before the cut.

This proves the outcome rather than assuming it, reading only GitHub (read-only `gh` calls):
  1. the commit the `v0.16.0` tag points at;
  2. that commit's CHANGELOG.md: exactly one `## [0.16.0]` heading, and an empty `## [Unreleased]`;
  3. the Release body's "What's New" region, compared with that section's body after its heading line.

Usage: python3 util/ad-hoc/2026-09-24_verify_data_0_16_0_notes_match_tag.py
Exit: 0 when the notes and the tagged CHANGELOG agree; 1 otherwise.
"""

from __future__ import annotations

import difflib
import json
import re
import subprocess

REPO = "pcalnon/juniper-data"
TAG = "v0.16.0"
VERSION = "0.16.0"


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def section(changelog: str, heading_re: str) -> list[str]:
    """Every section whose `## ` heading matches, each from its heading line up to the next `## ` heading."""
    lines = changelog.split("\n")
    starts = [i for i, line in enumerate(lines) if re.match(heading_re, line)]
    out = []
    for start in starts:
        end = next((j for j in range(start + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
        out.append("\n".join(lines[start:end]))
    return out


def main() -> int:
    ref = json.loads(gh("api", f"repos/{REPO}/git/ref/tags/{TAG}"))
    sha = ref["object"]["sha"]
    if ref["object"]["type"] == "tag":  # an annotated tag: follow it to its commit
        sha = json.loads(gh("api", f"repos/{REPO}/git/tags/{sha}"))["object"]["sha"]
    print(f"{TAG} -> {sha}")

    changelog = gh("api", f"repos/{REPO}/contents/CHANGELOG.md?ref={sha}", "-H", "Accept: application/vnd.github.raw")
    versions = section(changelog, rf"## \[{re.escape(VERSION)}\]")
    unreleased = section(changelog, r"## \[Unreleased\]")
    unreleased_body = "\n".join(unreleased[0].split("\n")[1:]).strip() if unreleased else "(no [Unreleased] heading)"
    print(f"`## [{VERSION}]` headings at the tagged commit: {len(versions)}")
    print(f"`## [Unreleased]` body at the tagged commit: {'EMPTY' if not unreleased_body else repr(unreleased_body[:120])}")

    body = json.loads(gh("release", "view", TAG, "--repo", REPO, "--json", "body"))["body"].replace("\r\n", "\n")
    match = re.search(r"\n## What's New\n(.*?)\n---\n\n## Known Issues", body, re.S)
    if not match or len(versions) != 1:
        print("FAIL: cannot compare (no What's New region, or not exactly one version section)")
        return 1
    notes = match.group(1).strip()
    tagged = "\n".join(versions[0].split("\n")[1:]).strip()
    bullets = len(re.findall(r"^- ", tagged, re.M))
    if notes == tagged:
        print(f"IDENTICAL: the Release's What's New region is the tagged commit's [{VERSION}] section body ({bullets} top-level bullets, {len(tagged)} chars)")
        return 0 if not unreleased_body else 1
    # The renderer drops the blank lines some CHANGELOG entries leave between list items. Say so
    # separately rather than calling that a content difference -- or hiding it.
    def solid(text: str) -> list[str]:
        return [line for line in text.split("\n") if line.strip()]

    if solid(notes) == solid(tagged):
        dropped = len(tagged.split("\n")) - len(notes.split("\n"))
        print(f"IDENTICAL APART FROM BLANK LINES: every non-blank line of the tagged [{VERSION}] section ({bullets} top-level bullets) is in the notes, in order; the notes drop {dropped} blank line(s) between list items")
        return 0 if not unreleased_body else 1
    print("DIFFERENT: the Release notes do not match the tagged commit's section")
    for line in difflib.unified_diff(tagged.split("\n"), notes.split("\n"), "tagged-changelog", "release-notes", lineterm="", n=1):
        print(line)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
