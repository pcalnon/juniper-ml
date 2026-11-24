"""
Resolve the first re-land's three conflicts onto origin/main, renumber what main took, and write rehome2/final/.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2621

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: resolve the three conflicts of the rehome onto origin/main, renumber what main took, write rehome2/final/.

Resolutions (each asserted to apply exactly once):
- AGENTS.md: my runner lines, with the suite count main moved to 262 moved on to 263 (mine is the 263rd suite).
- docs/REFERENCE.md: main's "Running every suite" line with my clause appended as the 263rd suite; main's 0.6.79
  version row, then mine as 0.6.80 (263 suites); header and footer 0.6.80.
- CHANGELOG.md (merged cleanly): my entry names docs version 0.6.80 and 263 suites.
- docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md (merged cleanly): header and footer 1.0.73 (main took 1.0.72).
- .github/workflows/ci.yml, tests/test_release_train_registry.py: the clean merges, unchanged.
"""

import re
from pathlib import Path

HERE = Path(__file__).with_name("rehome2")
FINAL = HERE / "final"


def merged(rel: str) -> str:
    return (HERE / (rel.replace("/", "__") + ".merged")).read_text(encoding="utf-8")


def once(text: str, old: str, new: str, what: str) -> str:
    count = text.count(old)
    assert count == 1, f"{what}: expected exactly one {old[:60]!r}, found {count}"
    return text.replace(old, new)


CONFLICT = re.compile(r"<<<<<<< mine\n(.*?)\|\|\|\|\|\|\| base\n(.*?)=======\n(.*?)>>>>>>> main\n", re.S)


def resolve(text: str, choose, what: str, expected: int) -> str:
    hits = CONFLICT.findall(text)
    assert len(hits) == expected, f"{what}: expected {expected} conflict(s), found {len(hits)}"
    index = iter(range(expected))
    return CONFLICT.sub(lambda m: choose(next(index), m.group(1), m.group(2), m.group(3)), text)


out = {}

# AGENTS.md: mine's side (the runner lines) with the count moved on to 263.
agents = resolve(merged("AGENTS.md"), lambda i, mine, base, main: once(mine, "list of 262 `python3", "list of 263 `python3", "AGENTS count"), "AGENTS.md", 1)
out["AGENTS.md"] = agents


def reference_choice(i, mine, base, main):
    if i == 0:  # the "Running every suite" prose line: main's, plus my clause as the 263rd suite
        return once(main, ". The drift script above counts", ", **263** on 2026-11-23 with the local test runner's `tests/test_run_tests.py`. The drift script above counts", "REFERENCE prose")
    # the version rows: main's 0.6.79 first, then mine renumbered
    row = once(mine, "| 0.6.79  | 2026-11-23 | The local test runner", "| 0.6.80  | 2026-11-23 | The local test runner", "REFERENCE my row")
    row = once(row, "entry (262 suites)", "entry (263 suites)", "REFERENCE my row count")
    return main + row


reference = resolve(merged("docs/REFERENCE.md"), reference_choice, "docs/REFERENCE.md", 2)
reference = once(reference, "**Version:** 0.6.79\n**Status:** Active", "**Version:** 0.6.80\n**Status:** Active", "REFERENCE header")
reference = once(reference, "**Version:** 0.6.79\n**Maintainer:**", "**Version:** 0.6.80\n**Maintainer:**", "REFERENCE footer")
out["docs/REFERENCE.md"] = reference

changelog = merged("CHANGELOG.md")
assert "<<<<<<<" not in changelog
changelog = once(changelog, "(docs version 0.6.79).", "(docs version 0.6.80).", "CHANGELOG docs version")
changelog = once(changelog, "is wired into ci.yml (262 suites)", "is wired into ci.yml (263 suites)", "CHANGELOG suite count")
out["CHANGELOG.md"] = changelog

cheatsheet = merged("docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md")
assert "<<<<<<<" not in cheatsheet
cheatsheet = once(cheatsheet, "**Version**: 1.0.72\n**Date**: 2026-11-23", "**Version**: 1.0.73\n**Date**: 2026-11-23", "cheatsheet header")
cheatsheet = once(cheatsheet, "**Last Updated:** 2026-11-23\n**Version:** 1.0.72", "**Last Updated:** 2026-11-23\n**Version:** 1.0.73", "cheatsheet footer")
out["docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"] = cheatsheet

for rel in (".github/workflows/ci.yml", "tests/test_release_train_registry.py"):
    text = merged(rel)
    assert "<<<<<<<" not in text, rel
    out[rel] = text

for rel, text in out.items():
    assert "<<<<<<<" not in text and ">>>>>>>" not in text and "|||||||" not in text, f"{rel}: conflict markers left"
    target = FINAL / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"resolved {rel}")
