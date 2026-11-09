#!/usr/bin/env python3
"""
Check that every test file and test function the flood-4 docs carrier's ADDED lines name exists in the working tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs carrier, check D-ml-docs)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the docs carrier must not name a test that the tree it lands on does not have.

Reads `git diff -U0 <base> -- <paths>` and collects, from the added lines only, every `test_*.py` file name and
every `test_<name>` identifier. A file name passes when some file of that basename exists under a `tests/`
directory of the working tree (a path given with directories must exist as written); an identifier passes when
`def test_<name>` (or `async def`) appears in a tracked or untracked test file. Each miss is printed; exit 1 if any.

Usage: 2026-11-07_flood4_ml_docs_test_names_check.py [--ignore NAME ...] <repo> <base> <path> [<path> ...]
  --ignore names an identifier the docs use that is not a test (e.g. the suite column `test_accuracy`).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

FILE_RE = re.compile(r"((?:[\w.-]+/)*test_[\w]+\.py)")
# A `Class.test_name` spelling must count too (round-3 F6: the first version's lookbehind skipped it).
NAME_RE = re.compile(r"(?<![\w/])(test_[A-Za-z0-9_]+)(?![\w.]*\.py)")


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__)
        return 2
    ignore: set[str] = set()
    while "--ignore" in argv:
        k = argv.index("--ignore")
        ignore.add(argv[k + 1])
        del argv[k : k + 2]
    repo, base, paths = Path(argv[1]), argv[2], argv[3:]
    diff = subprocess.run(["git", "-C", str(repo), "diff", "-U0", base, "--", *paths], capture_output=True, text=True, check=True).stdout
    added = [ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    files: set[str] = set()
    names: set[str] = set()
    for ln in added:
        files.update(FILE_RE.findall(ln))
        for n in NAME_RE.findall(ln):
            if not n.endswith(".py"):
                names.add(n)
    test_files = [p for p in repo.rglob("test_*.py") if "tests" in p.parts and "tmp" not in p.relative_to(repo).parts and ".git" not in p.parts]
    by_base: dict[str, list[Path]] = {}
    for p in test_files:
        by_base.setdefault(p.name, []).append(p)
    defs: set[str] = set()
    for p in test_files:
        defs.update(re.findall(r"^\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)", p.read_text(encoding="utf-8", errors="replace"), re.M))
    missing = 0
    for f in sorted(files):
        ok = (repo / f).exists() if "/" in f else f in by_base
        if not ok and "/" in f:
            ok = Path(f).name in by_base and any(str(p.relative_to(repo)).endswith(f) for p in by_base[Path(f).name])
        if not ok:
            missing += 1
            print(f"MISSING file: {f}")
    for n in sorted(names):
        if n in ignore:
            print(f"IGNORED (not a test name, per --ignore): {n}")
            continue
        if n not in defs:
            missing += 1
            print(f"MISSING test: {n}")
    distinct = {Path(f).name for f in files}
    print(f"named test files: {len(distinct)} distinct ({len(files)} spellings); named tests: {len(names - ignore)} (+{len(names & ignore)} ignored); missing: {missing}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
