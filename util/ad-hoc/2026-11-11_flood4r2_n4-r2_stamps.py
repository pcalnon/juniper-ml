#!/usr/bin/env python3
"""
Derive and check the doc stamps the N-4 round-2 carrier bumps, and write them as stamps.json.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (deliverable assembly for the N-4 fix, round 2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (section 8, ruling 11)

Usage::

    python3 <this file> --tree <worktree root> --date <YYYY-MM-DD> --out <stamps.json> [--mention <file> ...]

For ``docs/REFERENCE.md`` and ``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`` it reads each stamp line in the tree and at
the tree's ``HEAD`` (``git show``), and requires: the Version is HEAD's plus one in the last component, bumped once;
a file's header and footer agree; every date is ``--date``; and the new Version History row of REFERENCE carries the
new Version and ``--date`` and sits directly after the row with the highest version at HEAD (the table is not in
version order). Each ``--mention`` file is searched for the two new versions and the lines naming them are listed.
The exit status is 1 when any requirement fails; the JSON is written either way, with the failures in ``problems``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REFERENCE = "docs/REFERENCE.md"
CHEATSHEET = "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"
#: (file, field, line pattern with one group: the value)
SITES = [
    (REFERENCE, "header Version", r"^\*\*Version:\*\* (\S+)$", 0),
    (REFERENCE, "header Last Updated", r"^\*\*Last Updated:\*\* (\S+)$", 0),
    (REFERENCE, "footer Last Updated", r"^\*\*Last Updated:\*\* (\S+)$", -1),
    (REFERENCE, "footer Version", r"^\*\*Version:\*\* (\S+)$", -1),
    (CHEATSHEET, "header Version", r"^\*\*Version\*\*: (\S+)$", 0),
    (CHEATSHEET, "header Date", r"^\*\*Date\*\*: (\S+)$", 0),
    (CHEATSHEET, "footer Last Updated", r"^\*\*Last Updated:\*\* (\S+)$", -1),
    (CHEATSHEET, "footer Version", r"^\*\*Version:\*\* (\S+)$", -1),
]
ROW = re.compile(r"^\| (\d+)\.(\d+)\.(\d+)\s*\| (\S+) \|")

PURPOSE = "Every doc stamp the N-4 round-2 carrier bumps, so a carrier that lands after it (the service-core stop-then-start fix N-2, and the other pending juniper-ml carriers) can re-derive its own stamps mechanically, and so this one can be re-stamped if main moves first. 'old' is the value on the base (origin/main); 'new' is this tree's value."
REDERIVE_RULES = {
    "order": "This carrier lands FIRST of the pending juniper-ml carriers, so it takes main's values plus one: docs/REFERENCE.md 0.6.66 -> 0.6.67 and docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md 1.0.66 -> 1.0.67. A carrier that lands after it reads the values then on main and adds one again (0.6.68 and 1.0.68 for the next one).",
    "version": "Take each doc's Version on main at merge time and add 1 to the last component, once. A file's header and footer Version move together.",
    "date": "The merge date in UTC, YYYY-MM-DD. A file's header and footer dates move together, and the Version History row takes the same date. This tree carries 2026-11-12, the UTC date of the build; if it lands on a later day, set all five date sites to that day.",
    "version_history_row": "Set the row's version to the re-derived REFERENCE Version and its date to the merge date, and insert it directly after the row with the highest version on main at merge time. That row is not the table's last: the table is not in version order.",
    "mentions": "CHANGELOG.md's pointer entry names both new versions ('docs/REFERENCE.md (0.6.67) and docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md (1.0.67)'), as do commit_body.txt and pr_body.txt (its Docs section names main's value and the new one, its Merge notes the new ones). Set every one to the re-derived values. No other text in the carrier names a stamp, and no text refers to the entry above or below a CHANGELOG entry.",
    "how": "If main moved: rebuild each shared doc with `git merge-file -p <this tree's file> <the base's file> <main's file>` (util/ad-hoc/2026-11-11_flood4r2_n4-r2_rebuild.py saves the changed files and does this step) and inspect the result. Where main's own stamps moved too (another carrier landed first), the merge can take a Version line without a conflict and leave it one short, and the two Version History rows conflict: keep main's row, put this change's row after it, and re-stamp by these rules. Then run this helper again: it exits 1 when a header and footer disagree, a Version is not the base's plus one, a date is not --date, or the row is not directly after the base's highest row. It was done once already: built on 9063ebf3, rebuilt on 187e3258 after juniper-ml#2360, which changed both docs without moving a stamp.",
    "not_stamps": "The service-core package version is not bumped (pyproject.toml and _version.py stay 0.7.2), nor juniper-ml's. AGENTS.md is not changed: no root suite is added (the new test file is a juniper-service-core suite, collected by ci-service-core.yml's directory run), so its Last Updated does not move. docs/QUICK_START.md and docs/DOCUMENTATION_OVERVIEW.md are not changed.",
}


def _find(lines: list[str], pattern: str, which: int) -> tuple[int, str, str]:
    hits = [(number, line, re.match(pattern, line).group(1)) for number, line in enumerate(lines, 1) if re.match(pattern, line)]
    return hits[which]


def _rows(lines: list[str]) -> list[tuple[tuple[int, int, int], int, str, str]]:
    start = next(number for number, line in enumerate(lines, 1) if line.strip() == "## Version History")
    rows = []
    for number, line in enumerate(lines[start:], start + 1):
        match = ROW.match(line)
        if match:
            rows.append((tuple(int(part) for part in match.groups()[:3]), number, match.group(4), line))
        elif rows and line.startswith("## "):
            break
    return rows


def _bump(version: str) -> str:
    head, last = version.rsplit(".", 1)
    return f"{head}.{int(last) + 1}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--mention", action="append", default=[])
    args = parser.parse_args()
    tree = args.tree.resolve()
    head_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tree, capture_output=True, text=True, check=True).stdout.strip()
    text = {rel: ((tree / rel).read_text(encoding="utf-8").splitlines(), subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=tree, capture_output=True, text=True, check=True).stdout.splitlines()) for rel in (REFERENCE, CHEATSHEET)}
    problems: list[str] = []
    sites = []
    new_versions: dict[str, set[str]] = {REFERENCE: set(), CHEATSHEET: set()}
    for rel, field, pattern, which in SITES:
        mine, base = text[rel]
        line_new, _, new = _find(mine, pattern, which)
        line_old, text_old, old = _find(base, pattern, which)
        sites.append({"file": rel, "field": field, "line_on_main": line_old, "line_in_this_tree": line_new, "text_on_main": text_old, "old": old, "new": new})
        if "Version" in field:
            new_versions[rel].add(new)
            if new != _bump(old):
                problems.append(f"{rel} {field}: {new} is not main's {old} bumped once")
        elif new != args.date:
            problems.append(f"{rel} {field}: {new} is not {args.date}")
    for rel, versions in new_versions.items():
        if len(versions) != 1:
            problems.append(f"{rel}: header and footer Version differ: {sorted(versions)}")
    reference_version = sorted(new_versions[REFERENCE])[0]
    mine_rows, base_rows = _rows(text[REFERENCE][0]), _rows(text[REFERENCE][1])
    highest_on_main = max(base_rows)
    new_rows = [row for row in mine_rows if ".".join(str(part) for part in row[0]) == reference_version]
    row_record: dict = {"file": REFERENCE, "section": "## Version History", "inserted_after": {"rule": "the highest-version row on main at merge time (not the table's last row)", "on_this_base": {"line_on_main": highest_on_main[1], "row_starts": highest_on_main[3][:60]}}}
    if len(new_rows) != 1:
        problems.append(f"{REFERENCE}: {len(new_rows)} Version History rows for {reference_version}")
    else:
        row = new_rows[0]
        previous = text[REFERENCE][0][row[1] - 2]
        row_record.update({"line_in_this_tree": row[1], "date": row[2], "row": row[3]})
        if row[2] != args.date:
            problems.append(f"{REFERENCE}: the {reference_version} row is dated {row[2]}, not {args.date}")
        if previous != highest_on_main[3]:
            problems.append(f"{REFERENCE}: the {reference_version} row does not directly follow main's highest row ({'.'.join(str(part) for part in highest_on_main[0])})")
    wanted = sorted(new_versions[REFERENCE] | new_versions[CHEATSHEET])
    mentions = []
    for name in args.mention:
        path = Path(name) if Path(name).is_absolute() else tree / name
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            found = [value for value in wanted if value in line]
            if found:
                mentions.append({"file": name, "line": number, "values": found, "text": line.strip()[:200]})
    out = {"purpose": PURPOSE, "base": {"ref": "origin/main", "sha": head_sha}, "date": args.date, "rederive_rules": REDERIVE_RULES, "stamp_sites": sites, "version_history_row": row_record, "mentions": mentions, "problems": problems}
    args.out.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"sites": len(sites), "mentions": len(mentions), "problems": problems}, indent=1))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
