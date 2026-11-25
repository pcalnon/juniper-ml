"""
Resolve the second re-land onto origin/main b346a90a, renumber, apply the "owner" -> "Overtoad" rename to this arc's new text, and write rehome3/final/.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2629

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: resolve the re-land onto origin/main b346a90a, renumber, apply the "owner" -> "Overtoad" rename to my text.

Each replacement is asserted to apply exactly once. Writes rehome3/final/<path> for the six tracked files, and
rehome3/final/util/run_tests.py (the rename in its docstring, a comment and one message).
"""

import re
from pathlib import Path

HERE = Path(__file__).with_name("rehome3")
FINAL = HERE / "final"
ROOT = Path(__file__).resolve().parents[2]


def merged(rel: str) -> str:
    return (HERE / (rel.replace("/", "__") + ".merged")).read_text(encoding="utf-8")


def once(text: str, old: str, new: str, what: str) -> str:
    count = text.count(old)
    assert count == 1, f"{what}: expected exactly one {old[:70]!r}, found {count}"
    return text.replace(old, new)


CONFLICT = re.compile(r"<<<<<<< mine\n(.*?)\|\|\|\|\|\|\| base\n(.*?)=======\n(.*?)>>>>>>> main\n", re.S)


def resolve(text: str, choose, what: str, expected: int) -> str:
    hits = CONFLICT.findall(text)
    assert len(hits) == expected, f"{what}: expected {expected} conflict(s), found {len(hits)}"
    index = iter(range(expected))
    return CONFLICT.sub(lambda m: choose(next(index), m.group(1), m.group(2), m.group(3)), text)


def after_base(mine: str, base: str, what: str) -> str:
    """My side minus its leading base lines: what I added after the lines main has since reworded."""
    assert mine.startswith(base), f"{what}: my side does not start with the base lines"
    return mine[len(base) :]


def reference_choice(i, mine, base, main):
    if i in (0, 1):  # suite entries / utility entries: main's reworded lines, then my added block
        return main + after_base(mine, base, f"REFERENCE conflict {i}")
    if i == 2:  # version rows: main's (0.6.79 reworded, 0.6.80), then mine as 0.6.81 of today
        mine_row = after_base(mine, base, "REFERENCE rows")
        mine_row = once(mine_row, "| 0.6.80  | 2026-11-23 | The local test runner", "| 0.6.81  | 2026-11-24 | The local test runner", "REFERENCE my row")
        return main + mine_row
    # i == 3, the footer: main's date, my next version
    return once(main, "**Version:** 0.6.80", "**Version:** 0.6.81", "REFERENCE footer")


out = {}

reference = resolve(merged("docs/REFERENCE.md"), reference_choice, "docs/REFERENCE.md", 4)
reference = once(reference, "**Version:** 0.6.80\n**Status:** Active\n**Last Updated:** 2026-11-24", "**Version:** 0.6.81\n**Status:** Active\n**Last Updated:** 2026-11-24", "REFERENCE header")
reference = once(reference, "**263** on 2026-11-23 with the local test runner's", "**263** on 2026-11-24 with the local test runner's", "REFERENCE count date")
reference = once(reference, "which stay as provenance (owner policy 2026-08-25).", "which stay as provenance (Overtoad policy 2026-08-25).", "REFERENCE rename 1")
reference = once(reference, "is ever written under the system temp directory (owner directive, 2026-10-26).", "is ever written under the system temp directory (Overtoad directive, 2026-10-26).", "REFERENCE rename 2")
reference = once(reference, "The repo's `tmp/` is the owner's rule for temp files.", "The repo's `tmp/` is the Overtoad's rule for temp files.", "REFERENCE rename 3")
out["docs/REFERENCE.md"] = reference

changelog = merged("CHANGELOG.md")
changelog = once(changelog, "(docs version 0.6.80).", "(docs version 0.6.81).", "CHANGELOG docs version")
out["CHANGELOG.md"] = changelog

cheatsheet = merged("docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md")
cheatsheet = once(cheatsheet, "**Version**: 1.0.73\n**Date**: 2026-11-23", "**Version**: 1.0.73\n**Date**: 2026-11-24", "cheatsheet header date")
cheatsheet = once(cheatsheet, "**Last Updated:** 2026-11-23\n**Version:** 1.0.73", "**Last Updated:** 2026-11-24\n**Version:** 1.0.73", "cheatsheet footer date")
out["docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"] = cheatsheet

for rel in ("AGENTS.md", ".github/workflows/ci.yml", "tests/test_release_train_registry.py"):
    out[rel] = merged(rel)

runner = (ROOT / "util" / "run_tests.py").read_text(encoding="utf-8")
assert runner.count("(owner directive, 2026-10-26)") == 3, runner.count("(owner directive, 2026-10-26)")
runner = runner.replace("(owner directive, 2026-10-26)", "(Overtoad directive, 2026-10-26)")
out["util/run_tests.py"] = runner

for rel, text in out.items():
    assert "<<<<<<<" not in text and ">>>>>>>" not in text and "|||||||" not in text, f"{rel}: conflict markers left"
    target = FINAL / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"resolved {rel}")

leftover = [(rel, m.group(0)) for rel, text in out.items() for m in re.finditer(r".{0,40}\b[Oo]wner('s)? (directive|policy|rul)[^\n]{0,20}", text)]
print("person-sense 'owner' phrases left in the final files (any of main's own count too):", len(leftover))
