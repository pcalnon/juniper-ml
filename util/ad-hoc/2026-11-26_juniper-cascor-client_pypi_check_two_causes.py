#!/usr/bin/env python3
"""Give juniper-cascor-client's docs/REFERENCE.md both causes of a failed ``Verify PyPI serves exactly these files``, every edit an anchor asserted to match once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- one-off (a follow-up to juniper-cascor-client#206, the one-artifact template sweep's port: it brings
        that port's docs level with the other six ports on one point)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (policy of 2026-08-25)
Related: util/ad-hoc/2026-11-26_juniper-cascor-client_one_artifact_sweep_port.py (#206's writer, which wrote the
         paragraph this corrects); util/open_signed_pr.py (uploads the files this writes, whole)

Why
---
juniper-cascor-client#206 (merged 2026-11-26 as ``beb6b349``) left one paragraph in ``docs/REFERENCE.md`` § CI/CD
Pipeline Reference that gives a failed ``Verify PyPI serves exactly these files`` one cause: a MISMATCH (PyPI lists a
file this run did not build, or another sha256), whose fix is a new patch version. The step's other failure is a
TIMEOUT: it gave up waiting, because PyPI's JSON did not list the files in time. That is index lag: the files are
already on PyPI, and "Re-run failed jobs" on the run whose check gave up (the release run, or the republish's dispatch
run), within 30 days of that run, uploads the same bytes again, which the index accepts, and repeats the check.
juniper-cascor's ``docs/ci_cd/MANUAL.md`` keeps the two apart (its failure table's mismatch row, and its "A JSON check
gives up after 20 attempts" row), and the other ports' docs now do too: juniper-cascor-worker#238 (its review's R-1
named the run), juniper-data-client#274 (its review's F1, MAJOR there) and juniper-canopy#844.

On a fresh clone of ``main`` this writes:

- ``docs/REFERENCE.md``: that paragraph becomes a lead-in and two bullets, one per cause, in the same place (after the
  "When rung 1 refuses, or the release run failed before PyPI:" list, outside it). Its ``**Version:**`` gets a patch
  bump and its ``**Last Updated:**`` the ``--date``, header and footer, as #195, #196, #199 and #206 did.
- ``CHANGELOG.md``: one ``[Unreleased]`` / ``### Fixed`` entry, after the section's last one.

Nothing else. A post-condition compares the lines each file loses and gains with exactly the expected ones, and
refuses otherwise.

    python3 -I util/ad-hoc/2026-11-26_juniper-cascor-client_pypi_check_two_causes.py --tree <fresh clone> [--date YYYY-MM-DD]

``--date`` (default: today, UTC) is the day ``**Last Updated:**`` takes; take it from ``date -u`` at upload time.
Exit status: 0 when every edit applied; 1 when an anchor did not match exactly once or a post-condition failed
(nothing is written then); 2 on a usage error. A second run on the same tree refuses ("anchor matched 0 times") and
writes nothing.
"""

from __future__ import annotations

import argparse
import collections
import datetime
import difflib
import hashlib
import re
import sys
from pathlib import Path

REFERENCE_PATH = "docs/REFERENCE.md"
CHANGELOG_PATH = "CHANGELOG.md"

#: The line after the paragraph, which keeps the paragraph's place: the anchor includes it.
NEXT_LINE_START = "Each rung acts on the workflow as of the tag: "

#: The paragraph #206 wrote (docs/REFERENCE.md:729 at beb6b349): the mismatch cause alone.
OLD_PARAGRAPH = "A failed `Verify PyPI serves exactly these files` is not in that list: the step runs after the upload, so this run's files are already on PyPI. If PyPI lists a file this run did not build, or another sha256, find which upload put it there; only a new patch version ships tested files under a clean version.\n"

#: Its replacement: the same lead-in, then one bullet per cause.
NEW_PARAGRAPH = """\
A failed `Verify PyPI serves exactly these files` is not in that list: the step runs after the upload, so this run's files are already on PyPI. It has two causes, and they need different fixes:

- **A mismatch** (PyPI lists a file this run did not build, or another sha256): find which upload put it there; only a new patch version ships tested files under a clean version.
- **The check gave up waiting** (PyPI's JSON did not list the files in time): index lag, not a wrong file. **Re-run failed jobs** on the run whose check gave up (the release run, or the republish's dispatch run), within 30 days of that run. The re-run job uploads the same bytes again, which the index accepts, and repeats the check. Re-running the job needs a fresh `pypi` approval.
"""

#: The one CHANGELOG entry, wrapped at the file's width (every [Unreleased] line is at most 120 columns).
CHANGELOG_ENTRY = """\
- **`docs/REFERENCE.md` gives both causes of a failed `Verify PyPI serves exactly these files`.** #206's text gave
  only a mismatch (PyPI lists a file this run did not build, or another sha256), which needs a new patch version. A
  check that gave up waiting is index lag: the files are already on PyPI, and "Re-run failed jobs" on the run whose
  check gave up, within 30 days of it, re-uploads the same bytes and repeats the check, behind a fresh `pypi` approval.
"""

CHANGELOG_WIDTH = 120


class Refused(Exception):
    """An edit could not be applied exactly; nothing is written."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str, where: str) -> str:
    count = text.count(old)
    if count != 1:
        raise Refused(f"{where}: anchor matched {count} times, expected 1: {old[:90]!r}")
    return text.replace(old, new)


def replace_each(text: str, old: str, new: str, count: int, where: str) -> str:
    """``replace_once`` for an anchor the file holds exactly ``count`` times (a header line its footer repeats)."""
    found = text.count(old)
    if found != count:
        raise Refused(f"{where}: anchor matched {found} times, expected {count}: {old[:90]!r}")
    return text.replace(old, new)


def changed_lines(old: str, new: str) -> "tuple[collections.Counter[str], collections.Counter[str]]":
    """The lines OLD loses and the lines NEW gains, as multisets (difflib's line diff, no context)."""
    removed: collections.Counter[str] = collections.Counter()
    added: collections.Counter[str] = collections.Counter()
    for line in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0):
        if line.startswith(("---", "+++", "@@")):
            continue
        if line.startswith("-"):
            removed[line[1:]] += 1
        elif line.startswith("+"):
            added[line[1:]] += 1
    return removed, added


def expect_changes(where: str, old: str, new: str, removed: "list[str]", added: "list[str]") -> None:
    """Refuse unless OLD -> NEW loses exactly REMOVED and gains exactly ADDED (each a list of whole lines)."""
    got_removed, got_added = changed_lines(old, new)
    want_removed, want_added = collections.Counter(removed), collections.Counter(added)
    if got_removed != want_removed or got_added != want_added:
        raise Refused(f"{where}: the change is not exactly the expected one: removed {dict(got_removed - want_removed)} unexpected / {dict(want_removed - got_removed)} missing; added {dict(got_added - want_added)} unexpected / {dict(want_added - got_added)} missing")


def reference(text: str, date: datetime.date) -> "tuple[str, list[str]]":
    """docs/REFERENCE.md: the paragraph, then a patch bump of both **Version:** lines and the date of both **Last Updated:** lines."""
    notes = []
    anchor_old = "\n\n" + OLD_PARAGRAPH + "\n" + NEXT_LINE_START
    anchor_new = "\n\n" + NEW_PARAGRAPH + "\n" + NEXT_LINE_START
    new = replace_once(text, anchor_old, anchor_new, REFERENCE_PATH)
    versions = sorted(set(re.findall(r"^\*\*Version:\*\* (\d+)\.(\d+)\.(\d+)$", new, flags=re.MULTILINE)))
    if len(versions) != 1:
        raise Refused(f"{REFERENCE_PATH}: its **Version:** lines disagree or are missing: {versions}")
    major, minor, patch = versions[0]
    old_version = f"**Version:** {major}.{minor}.{patch}"
    new_version = f"**Version:** {major}.{minor}.{int(patch) + 1}"
    new = replace_each(new, old_version + "\n", new_version + "\n", 2, REFERENCE_PATH)
    notes.append(f"{REFERENCE_PATH}: {old_version} -> {new_version} (header and footer)")
    dated = sorted({line for line in new.splitlines() if line.startswith("**Last Updated:** ")})
    if len(dated) != 1:
        raise Refused(f"{REFERENCE_PATH}: its '**Last Updated:** ' lines disagree or are missing: {dated}")
    old_date, new_date = dated[0], f"**Last Updated:** {date:%B} {date.day}, {date.year}"
    removed = [OLD_PARAGRAPH.rstrip("\n"), old_version, old_version]
    added = NEW_PARAGRAPH.rstrip("\n").split("\n") + [new_version, new_version]
    if old_date == new_date:
        notes.append(f"{REFERENCE_PATH}: {old_date!r} already names {date.isoformat()}: unchanged (header and footer)")
    else:
        new = replace_each(new, old_date + "\n", new_date + "\n", 2, REFERENCE_PATH)
        removed += [old_date, old_date]
        added += [new_date, new_date]
        notes.append(f"{REFERENCE_PATH}: {old_date!r} -> {new_date!r} (header and footer)")
    # The paragraph's blank line is a line it adds; the diff reports it like any other.
    expect_changes(REFERENCE_PATH, text, new, removed, added)
    if new.count(NEW_PARAGRAPH) != 1 or OLD_PARAGRAPH in new:
        raise Refused(f"{REFERENCE_PATH}: the new paragraph is not there exactly once, or the old one survived")
    return new, notes


def changelog(text: str) -> "tuple[str, list[str]]":
    """CHANGELOG.md: append the entry to the end of [Unreleased]'s ### Fixed, which must exist exactly once."""
    if text.count("\n## [Unreleased]\n") != 1:
        raise Refused(f"{CHANGELOG_PATH}: no single '## [Unreleased]' heading")
    start = text.index("\n## [Unreleased]\n") + 1
    end = text.find("\n## [", start)
    end = len(text) if end < 0 else end + 1
    section = text[start:end]
    if section.count("\n### Fixed\n") != 1:
        raise Refused(f"{CHANGELOG_PATH}: [Unreleased] holds {section.count(chr(10) + '### Fixed' + chr(10))} '### Fixed' headings, expected 1")
    fixed = section.index("\n### Fixed\n")
    after = section.find("\n### ", fixed + 1)
    cut = len(section) if after < 0 else after + 1
    body = section[:cut].rstrip("\n")
    last_line = body.rsplit("\n", 1)[-1]
    rest = len(body) + 1  # past the newline that ends the section's last line
    new_section = body + "\n" + CHANGELOG_ENTRY + section[rest:]
    new = text[:start] + new_section + text[end:]
    expect_changes(CHANGELOG_PATH, text, new, [], CHANGELOG_ENTRY.rstrip("\n").split("\n"))
    if new.count(CHANGELOG_ENTRY) != 1:
        raise Refused(f"{CHANGELOG_PATH}: the entry is not there exactly once")
    wide = [line for line in CHANGELOG_ENTRY.splitlines() if len(line) > CHANGELOG_WIDTH]
    if wide:
        raise Refused(f"{CHANGELOG_PATH}: entry lines wider than {CHANGELOG_WIDTH}: {wide}")
    return new, [f"{CHANGELOG_PATH}: the entry follows the line {last_line[-70:]!r}"]


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help="a fresh clone of juniper-cascor-client main")
    parser.add_argument("--date", type=datetime.date.fromisoformat, default=datetime.datetime.now(datetime.timezone.utc).date(), help="YYYY-MM-DD (default: today, UTC)")
    args = parser.parse_args(argv)
    paths = {rel: args.tree / rel for rel in (REFERENCE_PATH, CHANGELOG_PATH)}
    for path in paths.values():
        if not path.is_file():
            print(f"REFUSED: {path} is missing")
            return 1
    old = {rel: path.read_bytes().decode("utf-8") for rel, path in paths.items()}
    try:
        new_reference, notes = reference(old[REFERENCE_PATH], args.date)
        new_changelog, more = changelog(old[CHANGELOG_PATH])
    except Refused as exc:
        print(f"REFUSED: {exc}")
        print("nothing written")
        return 1
    new = {REFERENCE_PATH: new_reference, CHANGELOG_PATH: new_changelog}
    for rel in paths:
        for number, line in enumerate(new[rel].split("\n"), start=1):
            if line != line.rstrip() or "\t" in line:
                if line not in old[rel].split("\n"):
                    print(f"REFUSED: {rel}:{number} gains trailing whitespace or a tab")
                    print("nothing written")
                    return 1
        if not new[rel].endswith("\n"):
            print(f"REFUSED: {rel} would lose its final newline")
            print("nothing written")
            return 1
    for rel, path in paths.items():
        path.write_bytes(new[rel].encode("utf-8"))
    for line in notes + more:
        print(line)
    for rel, path in paths.items():
        print(f"wrote {rel}: sha256 {sha256(path.read_bytes())} (was {sha256(old[rel].encode('utf-8'))})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
