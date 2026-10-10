#!/usr/bin/env python3
"""
Insert an "archived verbatim" header directly after the H1 of agent-written validation reports.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-05
Status: ad-hoc — one-off archiving step
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (its evidence directory,
         reports/2026-10-04_consolidated-development-plan/)

What it does
------------
For each file: line 1 must be the H1. It inserts, after the H1, a blanket ``<!-- markdownlint-disable -->`` (the
reports are archived verbatim, so their lint findings are not fixed) and a one-line note saying what the file is and
where its findings are dispositioned. Nothing else in the file changes. It is idempotent: a file whose first
non-blank line after the H1 is already the disable comment is left alone.

Only agent-written reports get a note: ``extraction-*.md`` and ``round<N>-lane*.md``. Anything else is skipped and
the exit status is 1, so a wrong glob is visible.

Usage
-----
    python3 util/ad-hoc/2026-10-05_archive_report_headers.py reports/2026-10-04_consolidated-development-plan/extraction-P1-backup.md ...
"""
import re
import sys
from pathlib import Path

MARK = "<!-- markdownlint-disable -->"
PLAN = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md"


def note_for(name: str):
    lane = re.match(r"round(\d+)-lane", name)
    if lane:
        n = lane.group(1)
        return f"> **Archived verbatim.** A round-{n} validation lane report for `{PLAN}`. Its findings are dispositioned in `round{n}-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4."
    if name.startswith("extraction-"):
        return f"> **Archived verbatim.** An extraction report for `{PLAN}`. Corrections found by validation are in the `round*-reconciliation.md` files in this directory, and the plan's §10. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4."
    return None


def main() -> int:
    rc = 0
    for arg in sys.argv[1:]:
        path = Path(arg)
        head, _, rest = path.read_text().partition("\n")
        if not head.startswith("# "):
            print("SKIP (line 1 is not an H1):", path)
            rc = 1
            continue
        if rest.lstrip("\n").startswith(MARK):
            print("already headed:", path)
            continue
        note = note_for(path.name)
        if note is None:
            print("SKIP (not an agent-written report):", path)
            rc = 1
            continue
        path.write_text(head + "\n\n" + MARK + "\n\n" + note + "\n\n" + rest.lstrip("\n"))
        print("headed:", path)
    return rc


if __name__ == "__main__":
    sys.exit(main())
