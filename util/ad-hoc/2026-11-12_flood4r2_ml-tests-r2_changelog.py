#!/usr/bin/env python3
"""
Insert the ml-tests carrier's CHANGELOG entry at the END of the current `## [Unreleased]` / `### Added` subsection.

Round 1's helper put the entry below round 1's tests-carrier entry (juniper-ml#2517). On today's main that entry
no longer sits under `### Added`: juniper-ml#2360's merge left a `### Changed` heading between `### Added` and it
(the section now has `### Changed` twice), so round 1's helper refuses. The entry is an addition, so it goes
under the one `### Added` heading the section has, below every entry already there: below an existing entry of
its subsection, where an insertion at the subsection's top cannot conflict with it.

A RELEASE CUT EMPTIES `## [Unreleased]`: it writes a `## [X.Y.Z] - date` heading directly under it, and the
entries that were unreleased now belong to that release. The entry of a change that lands after the cut is
unreleased, so it must never follow them there. When `## [Unreleased]` has no `### Added`, this opens one: after
a leading `### Security` subsection when the section has one (the file's own order), else directly under the
`## [Unreleased]` heading, and always above the next release's heading.

Whatever it did, the tool then CHECKS the result: the entry must occur exactly once, and the nearest `## [`
heading above it must be `## [Unreleased]`. An entry found under a released heading fails the run (a three-way
merge with a release cut can put it there without a conflict). --check runs that check alone and writes nothing.

Refuses when `## [Unreleased]` has more than one `### Added`. Idempotent: an entry already present under
`## [Unreleased]` is left alone. With --replace OLD_ENTRY_FILE, an earlier version of the entry is replaced in place.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_changelog.py <entry file> [--replace <old entry file>]
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_changelog.py <entry file> --check

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_ml-tests_changelog.py (round 1's)
"""

import argparse
import re
import sys
from pathlib import Path

CHANGELOG = Path("CHANGELOG.md")
UNRELEASED = "## [Unreleased]"


def _placement(text: str, entry: str) -> str:
    """An empty string when the entry occurs once under `## [Unreleased]`; otherwise what is wrong."""
    if text.count(entry) != 1:
        return f"the entry occurs {text.count(entry)} times"
    above = re.findall(r"^## \[.*$", text[: text.index(entry)], re.M)
    if not above:
        return "the entry stands above every `## [` heading"
    if above[-1].strip() != UNRELEASED:
        return f"the entry stands under `{above[-1].strip()}`, not under `{UNRELEASED}`"
    return ""


def _open_added(section: str, entry: str) -> tuple:
    """The section with a new `### Added` subsection holding the entry, and where it was opened."""
    headings = [(match.start(), match.group(1).strip()) for match in re.finditer(r"^### (.+)\n", section, re.M)]
    if headings and headings[0][1] == "Security":
        at = headings[1][0] if len(headings) > 1 else len(section)
        where = "after `### Security`"
    elif headings:
        at = headings[0][0]
        where = f"above `### {headings[0][1]}`"
    else:
        at = len(section)
        where = "as the section's only subsection"
    return section[:at].rstrip("\n") + "\n\n### Added\n\n" + entry + "\n" + section[at:], where


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entry")
    ap.add_argument("--replace")
    ap.add_argument("--check", action="store_true", help="write nothing: the entry must occur once, under `## [Unreleased]`")
    args = ap.parse_args()
    entry = Path(args.entry).read_text(encoding="utf-8").rstrip("\n") + "\n"
    text = CHANGELOG.read_text(encoding="utf-8")
    if args.check or entry in text:
        wrong = _placement(text, entry)
        print("REFUSED: " + wrong if wrong else f"entry present once, under `{UNRELEASED}`")
        return 1 if wrong else 0
    if args.replace:
        old = Path(args.replace).read_text(encoding="utf-8").rstrip("\n") + "\n"
        if text.count(old) != 1:
            raise SystemExit(f"--replace: the old entry occurs {text.count(old)} times")
        result, done = text.replace(old, entry), "entry replaced in place"
    else:
        start = text.index(UNRELEASED)
        following_release = re.search(r"^## \[", text[start + 1 :], re.M)
        end = start + 1 + following_release.start() if following_release else len(text)
        section = text[start:end]
        added = [m.start() for m in re.finditer(r"^### Added\n", section, re.M)]
        if len(added) > 1:
            raise SystemExit(f"[Unreleased] has {len(added)} `### Added` headings")
        if added:
            next_heading = re.search(r"^### ", section[added[0] + 1 :], re.M)
            stop = added[0] + 1 + next_heading.start() if next_heading else len(section)
            body = section[added[0] : stop]
            existing = len(re.findall(r"^- \*\*", body, re.M))
            at = start + added[0] + len(body.rstrip("\n")) + 1
            result = text[:at] + "\n" + entry + text[at:]
            done = f"entry inserted at the end of [Unreleased] / ### Added, below {existing} existing entr{'y' if existing == 1 else 'ies'}"
        else:
            section, where = _open_added(section, entry)
            result = text[:start] + section + text[end:]
            done = f"[Unreleased] had no `### Added` (a release cut empties the section): one opened {where}, holding the entry"
    wrong = _placement(result, entry)
    if wrong:
        raise SystemExit(f"REFUSED, nothing written: {wrong}")
    CHANGELOG.write_text(result, encoding="utf-8")
    print(done)
    return 0


if __name__ == "__main__":
    sys.exit(main())
