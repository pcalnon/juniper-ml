#!/usr/bin/env python3
"""
Resolve the two suite-count conflicts left when the ml-code carrier (round 3) moves onto a main that added suites.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3: the move onto juniper-ml#2360's main)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_rebase.py (writes the merges this resolves);
         util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_resolve.py (the first rebuild's five conflicts).

Usage (from the worktree root, right after the rebase script's ``apply``):
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_resolve2.py <suites the carrier adds> <YYYY-MM-DD>

The count is derived, not given: the ``python3 -m unittest -v tests/...`` lines of the worktree's
.github/workflows/ci.yml (main's list and the carrier's, merged). Each ``git merge-file`` conflict block
(ours = the carrier, theirs = main) is then replaced:
- AGENTS.md, "# Run all tests -- the full ordered list of N" -> that count. main's N must be the count less the
  carrier's suites;
- docs/REFERENCE.md, the running tally of the Test Suite Reference (one long line a side) -> main's line, with the
  carrier's clause ("**N** on <date> with the flood-4 round-2 code carrier's five (...)") after main's last
  clause and before "The drift script above counts". main's last tally must be the count less the carrier's suites.
Two more sites carry the count and merge WITHOUT a conflict, so a merge leaves them at the old base's figure: the
carrier's Version History row in docs/REFERENCE.md ("five suites registered (N)") and its CHANGELOG.md entry
("Five new suites, N in CI's regression list"). Both are set to the count; each must occur exactly once.
Any other conflict shape, or a count that does not add up, aborts with exit 1 and nothing is written.
"""
import re
import sys
from pathlib import Path

_BLOCK = re.compile(r"^<<<<<<< [^\n]*\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]*\n", re.MULTILINE | re.DOTALL)
_MARKER = re.compile(r"^(<<<<<<<|=======|>>>>>>>)( |$)", re.MULTILINE)
_COUNT_LINE = re.compile(r"# Run all tests -- the full ordered list of (\d+) `python3 -m unittest`\n")
_CLAUSE = re.compile(r"\*\*\d+\*\* on \d{4}-\d{2}-\d{2} with the flood-4 round-2 code carrier's five (\([^)]*\))")
_TALLY = re.compile(r"\*\*(\d+)\*\*")
_ROW_COUNT = re.compile(r"five suites registered \(\d+\)")
_ENTRY_COUNT = re.compile(r"Five new suites, \d+ in CI's regression list")
_ANCHOR = "). The drift script above counts"


def one_block(text: str, name: str) -> re.Match:
    blocks = list(_BLOCK.finditer(text))
    if len(blocks) != 1 or len(_MARKER.findall(text)) != 3:
        raise SystemExit("%s: expected exactly one conflict block, found %d (and %d marker lines)" % (name, len(blocks), len(_MARKER.findall(text))))
    return blocks[0]


def resolve_agents(text: str, total: int, mine: int) -> str:
    block = one_block(text, "AGENTS.md")
    ours, theirs = _COUNT_LINE.fullmatch(block.group(1)), _COUNT_LINE.fullmatch(block.group(2))
    if ours is None or theirs is None or int(theirs.group(1)) != total - mine:
        raise SystemExit("AGENTS.md: the conflict is not the suite-count line, or main's count is not %d" % (total - mine))
    print("AGENTS.md suite count: carrier %s / main %s -> %d" % (ours.group(1), theirs.group(1), total))
    return text[: block.start()] + "# Run all tests -- the full ordered list of %d `python3 -m unittest`\n" % total + text[block.end() :]


def resolve_reference(text: str, total: int, mine: int, date: str) -> str:
    block = one_block(text, "docs/REFERENCE.md")
    ours, theirs = block.group(1), block.group(2)
    clause = _CLAUSE.search(ours)
    tallies = _TALLY.findall(theirs.split(_ANCHOR)[0])
    if clause is None or ours.count("\n") != 1 or theirs.count("\n") != 1 or theirs.count(_ANCHOR) != 1 or not tallies or int(tallies[-1]) != total - mine:
        raise SystemExit("docs/REFERENCE.md: the conflict is not the running tally, or main's last tally is not %d" % (total - mine))
    added = "), **%d** on %s with the flood-4 round-2 code carrier's five %s. The drift script above counts" % (total, date, clause.group(1))
    print("REFERENCE running tally: main's line (last tally %s), then the carrier's clause as **%d** on %s" % (tallies[-1], total, date))
    return text[: block.start()] + theirs.replace(_ANCHOR, added) + text[block.end() :]


def main(argv: list) -> int:
    if len(argv) != 3 or not argv[1].isdigit() or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", argv[2]):
        print("usage: <suites the carrier adds> <YYYY-MM-DD>")
        return 1
    mine, date = int(argv[1]), argv[2]
    total = len(re.findall(r"^\s+python3 -m unittest -v tests/", Path(".github/workflows/ci.yml").read_bytes().decode("utf-8"), flags=re.MULTILINE))
    agents, reference, changelog = Path("AGENTS.md"), Path("docs/REFERENCE.md"), Path("CHANGELOG.md")
    new_agents = resolve_agents(agents.read_bytes().decode("utf-8"), total, mine)
    new_reference = resolve_reference(reference.read_bytes().decode("utf-8"), total, mine, date)
    # The two sites that merge WITHOUT a conflict, and so would keep the count of the old base.
    new_reference, rows = _ROW_COUNT.subn("five suites registered (%d)" % total, new_reference)
    new_changelog, entries = _ENTRY_COUNT.subn("Five new suites, %d in CI's regression list" % total, changelog.read_bytes().decode("utf-8"))
    if rows != 1 or entries != 1:
        print("expected the count once in the Version History row and once in CHANGELOG.md, found %d and %d; nothing written" % (rows, entries))
        return 1
    if _MARKER.search(new_agents) or _MARKER.search(new_reference) or _MARKER.search(new_changelog):
        print("conflict markers remain; nothing written")
        return 1
    agents.write_bytes(new_agents.encode("utf-8"))  # bytes in, bytes out: no newline translation
    reference.write_bytes(new_reference.encode("utf-8"))
    changelog.write_bytes(new_changelog.encode("utf-8"))
    print("Version History row and CHANGELOG.md: the count set to %d" % total)
    print("ci.yml lists %d suites: main's %d and the carrier's %d" % (total, total - mine, mine))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
