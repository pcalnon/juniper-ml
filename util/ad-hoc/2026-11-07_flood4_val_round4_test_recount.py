#!/usr/bin/env python3
"""Round-4 validator helper: recount the test files and tests named by a docs carrier's added lines.

Project: Juniper
Sub-Project: juniper-ml
Application: flood-4 docs-carrier round-4 validation (ad hoc, single use)
Author: Paul Calnon
Version: 0.1.0
License: MIT License
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 4 (findings: tmp/flood4/ml-docs/val-round4/)

For each carrier file, diff the base commit's blob against the carrier copy (difflib, line level),
keep the inserted/replacement lines, and extract (a) every test-file spelling ``[path/]test_*.py``
and (b) every ``test_<name>`` token that is not a .py stem, including ``Class.test_name`` forms.
Each is then checked against the base tree in ONE git call per kind (ls-tree, grep), never a loop.

Usage: python3 -I <this> <repo_dir> <base_commit> <carrier_dir> <out_json> <rel_path>...
"""

from __future__ import annotations

import difflib
import json
import re
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path

FILE_RE = re.compile(r"(?<![\w./-])((?:[\w.-]+/)*test_[A-Za-z0-9_]+\.py)\b")
NAME_RE = re.compile(r"\btest_[A-Za-z0-9_]+\b")
CLASS_DOT_RE = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\.(test_[A-Za-z0-9_]+)\b")


def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout  # nosec B603 B607


def main() -> int:
    repo, base, carrier_dir, out_json, *rels = sys.argv[1:]
    added: list[tuple[str, int, str]] = []
    for rel in rels:
        try:
            old = git(repo, "show", f"{base}:{rel}").splitlines()
        except subprocess.CalledProcessError:
            old = []
        new = (Path(carrier_dir) / rel).read_text(encoding="utf-8").splitlines()
        sm = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
        for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
            if tag in ("insert", "replace"):
                added.extend((rel, j + 1, new[j]) for j in range(j1, j2))
    spellings: dict[str, list[str]] = {}
    names: dict[str, list[str]] = {}
    class_dot: dict[str, list[str]] = {}
    for rel, ln, text in added:
        for m in FILE_RE.finditer(text):
            spellings.setdefault(m.group(1), []).append(f"{rel}:{ln}")
        for m in CLASS_DOT_RE.finditer(text):
            class_dot.setdefault(f"{m.group(1)}.{m.group(2)}", []).append(f"{rel}:{ln}")
        stripped = FILE_RE.sub(" ", text)
        for m in NAME_RE.finditer(stripped):
            names.setdefault(m.group(0), []).append(f"{rel}:{ln}")
    basenames = sorted({s.rsplit("/", 1)[-1] for s in spellings})
    tree_files = git(repo, "ls-tree", "-r", "--name-only", base).splitlines()
    tree_base = {}
    for p in tree_files:
        tree_base.setdefault(p.rsplit("/", 1)[-1], []).append(p)
    missing_files = [b for b in basenames if b not in tree_base]
    prefixed_missing = [s for s in spellings if "/" in s and not any(p.endswith(s) for p in tree_base.get(s.rsplit("/", 1)[-1], []))]
    defined_raw = git(repo, "grep", "-h", "-o", "-E", r"def test_[A-Za-z0-9_]+", base, "--", "*.py")
    defined = {line.split(":", 1)[-1].replace("def ", "").strip() for line in defined_raw.splitlines()}
    stems = {b[:-3] for b in basenames}
    name_set = sorted(names)
    not_stem = [n for n in name_set if n not in stems]
    undefined = [n for n in not_stem if n not in defined]
    out = {
        "base": base,
        "added_lines": len(added),
        "test_file_spellings": len(spellings),
        "test_file_spelling_list": sorted(spellings),
        "test_files_distinct_basenames": len(basenames),
        "test_file_basenames": basenames,
        "missing_test_files": missing_files,
        "prefixed_spellings_not_matching_a_tree_path": prefixed_missing,
        "test_name_tokens_distinct": len(name_set),
        "test_name_tokens_that_are_file_stems": [n for n in name_set if n in stems],
        "test_names_not_stems": len(not_stem),
        "test_names_defined_on_tree": len([n for n in not_stem if n in defined]),
        "test_names_not_defined_on_tree": undefined,
        "class_dot_spellings": class_dot,
        "names_with_sites": {n: names[n] for n in name_set},
    }
    Path(out_json).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for key in ("added_lines", "test_file_spellings", "test_files_distinct_basenames", "missing_test_files", "prefixed_spellings_not_matching_a_tree_path", "test_name_tokens_distinct", "test_name_tokens_that_are_file_stems", "test_names_not_stems", "test_names_defined_on_tree", "test_names_not_defined_on_tree"):
        print(f"{key}: {out[key]}")
    print("class_dot_spellings:", sorted(class_dot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
