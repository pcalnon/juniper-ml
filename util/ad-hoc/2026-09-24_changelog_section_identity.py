#!/usr/bin/env python3
"""
Prove a released CHANGELOG section is byte-identical at two refs, and that an edit only MOVED lines.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#437 (X8), whose CHANGELOG entry merged under the RELEASED ``## [0.16.0]``
         heading 22 minutes after v0.16.0 was cut at ``39d1cab2``. The fix moves it to
         ``[Unreleased]``; this script is the evidence that the fix restored the released section
         exactly and changed nothing else.

Why a byte comparison, and why of the SECTION
---------------------------------------------
A release's notes are rendered from its version section. After a cut, the only correct content for
that section on ``main`` is what it held at the tag: anything added later describes code the release
does not contain, and the NEXT release's notes silently omit it. Comparing whole files cannot say
this, because ``[Unreleased]`` legitimately moves on; comparing the section can.

The section runs from its ``## [<version>]`` heading to the next ``## [`` heading. The heading must
occur exactly once: ``util/release_train/ceremony.py`` reads a version section first-match only, so
a duplicated version heading is itself the defect (juniper-data#428 left one), and this refuses it
rather than comparing whichever copy comes first.

Usage
-----
    # 1. The released section: at the tag vs. at a branch (or a local file)
    python3 util/ad-hoc/2026-09-24_changelog_section_identity.py section \
        --repo pcalnon/juniper-data --section 0.16.0 --ref v0.16.0 --against fix/some-branch
    python3 util/ad-hoc/2026-09-24_changelog_section_identity.py section \
        --repo pcalnon/juniper-data --section 0.16.0 --ref v0.16.0 --against-file ./CHANGELOG.md

    # 2. The edit only moved lines: every line of BASE is still in CANDIDATE, and CANDIDATE adds
    #    only the lines named by --allow-added (repeatable; exact line text, e.g. "### Changed").
    python3 util/ad-hoc/2026-09-24_changelog_section_identity.py multiset \
        --base ./CHANGELOG.main.md --candidate ./CHANGELOG.md --allow-added "### Changed" --allow-added ""

Exit 0 = identical / only moved, 1 = differs (a diff is printed), 2 = usage or fetch error.
"""

from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path


def fetch(repo: str, path: str, ref: str) -> str:
    """Return ``path`` at ``ref`` in ``repo`` (owner/name) through the contents API, raw."""
    proc = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}", "-H", "Accept: application/vnd.github.raw"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"error: fetching {repo}:{path}@{ref} failed: {proc.stderr.strip()}")
    return proc.stdout


def extract_section(text: str, version: str, label: str) -> list[str]:
    """Lines from the single ``## [version]`` heading up to, not including, the next ``## [``."""
    lines = text.splitlines(keepends=True)
    heading = f"## [{version}]"
    starts = [i for i, line in enumerate(lines) if line.startswith(heading)]
    if len(starts) != 1:
        raise SystemExit(f"error: {label}: expected exactly one '{heading}' heading, found {len(starts)} (lines {[i + 1 for i in starts]})")
    start = starts[0]
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## [")), len(lines))
    return lines[start:end]


def digest(lines: list[str]) -> str:
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()[:12]


def cmd_section(args: argparse.Namespace) -> int:
    ref_text = fetch(args.repo, args.path, args.ref)
    if args.against_file:
        cand_text = Path(args.against_file).read_text(encoding="utf-8")
        cand_label = f"file {args.against_file}"
    else:
        cand_text = fetch(args.repo, args.path, args.against)
        cand_label = f"{args.repo}:{args.path}@{args.against}"
    ref_label = f"{args.repo}:{args.path}@{args.ref}"
    ref_sec = extract_section(ref_text, args.section, ref_label)
    cand_sec = extract_section(cand_text, args.section, cand_label)
    print(f"  reference  {ref_label}: [{args.section}] {len(ref_sec)} lines, sha256 {digest(ref_sec)}")
    print(f"  candidate  {cand_label}: [{args.section}] {len(cand_sec)} lines, sha256 {digest(cand_sec)}")
    if ref_sec == cand_sec:
        print(f"  IDENTICAL: [{args.section}] is byte-for-byte what it was at {args.ref}")
        return 0
    print(f"  DIFFERS: [{args.section}] is not what it was at {args.ref}")
    sys.stdout.writelines(difflib.unified_diff(ref_sec, cand_sec, fromfile=ref_label, tofile=cand_label))
    return 1


def cmd_multiset(args: argparse.Namespace) -> int:
    base = Path(args.base).read_text(encoding="utf-8").splitlines()
    cand = Path(args.candidate).read_text(encoding="utf-8").splitlines()
    lost = collections.Counter(base) - collections.Counter(cand)
    gained = collections.Counter(cand) - collections.Counter(base)
    allowed = collections.Counter(args.allow_added or [])
    unexpected = gained - allowed
    print(f"  base {args.base}: {len(base)} lines; candidate {args.candidate}: {len(cand)} lines")
    print(f"  lines lost: {sum(lost.values())}; lines gained: {sum(gained.values())} ({dict(gained)})")
    if lost or unexpected:
        for line, n in sorted(lost.items()):
            print(f"  LOST x{n}: {line!r}")
        for line, n in sorted(unexpected.items()):
            print(f"  UNEXPECTED x{n}: {line!r}")
        return 1
    print("  ONLY MOVED: no line lost, and every gained line is an allowed addition")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sec = sub.add_parser("section", help="compare one version section at two refs")
    sec.add_argument("--repo", required=True, help="owner/name, e.g. pcalnon/juniper-data")
    sec.add_argument("--path", default="CHANGELOG.md")
    sec.add_argument("--section", required=True, help="the version inside the brackets, e.g. 0.16.0")
    sec.add_argument("--ref", required=True, help="the reference ref, normally the release tag")
    grp = sec.add_mutually_exclusive_group(required=True)
    grp.add_argument("--against", help="a branch, tag or sha to compare with the reference")
    grp.add_argument("--against-file", help="a local file to compare with the reference")
    sec.set_defaults(func=cmd_section)
    mul = sub.add_parser("multiset", help="prove an edit only moved lines")
    mul.add_argument("--base", required=True)
    mul.add_argument("--candidate", required=True)
    mul.add_argument("--allow-added", action="append", help="an exact line the edit may add (repeatable)")
    mul.set_defaults(func=cmd_multiset)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
