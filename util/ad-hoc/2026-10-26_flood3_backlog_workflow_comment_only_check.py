#!/usr/bin/env python3
"""Report whether two copies of a GitHub workflow differ only in comments (YAML comments and full-line shell comments).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — investigation (flood-3 backlog rows A / C / D / F / G / I verification)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md §4

A YAML comment never reaches the parsed document, but a ``#`` line inside a ``run: |`` block is part
of the step's script string. So "the parsed YAML is unchanged" is true of a header-only edit and false
of an edit to a comment inside a ``run:`` block. This check answers the narrower question that matters
for review: with full-line shell comments removed from every multi-line string, are the two parsed
documents identical? If so, no executed line changed.

Usage:
    2026-10-26_flood3_backlog_workflow_comment_only_check.py OLD.yml NEW.yml [OLD.yml NEW.yml ...]

Prints one verdict per pair: IDENTICAL (the parsed YAML is unchanged), COMMENT-ONLY (only shell
comment lines inside run strings differ), or CODE-CHANGED (an executed line differs; the first
differing path is named). Exit status is 0 when no pair is CODE-CHANGED, 1 otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


def _strip_shell_comments(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _normalise(node):
    if isinstance(node, dict):
        return {key: _normalise(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_normalise(item) for item in node]
    if isinstance(node, str) and "\n" in node:
        return _strip_shell_comments(node)
    return node


def _first_difference(old, new, path: str = "$") -> str | None:
    if type(old) is not type(new):
        return path
    if isinstance(old, dict):
        for key in sorted(set(old) | set(new), key=str):
            if key not in old or key not in new:
                return f"{path}.{key}"
            found = _first_difference(old[key], new[key], f"{path}.{key}")
            if found:
                return found
        return None
    if isinstance(old, list):
        if len(old) != len(new):
            return f"{path}[len {len(old)} != {len(new)}]"
        for index, (left, right) in enumerate(zip(old, new)):
            found = _first_difference(left, right, f"{path}[{index}]")
            if found:
                return found
        return None
    return None if old == new else path


def main(argv: list[str]) -> int:
    if not argv or len(argv) % 2:
        print(__doc__)
        return 2
    code_changed = False
    for old_path, new_path in zip(argv[0::2], argv[1::2]):
        old = yaml.safe_load(Path(old_path).read_text(encoding="utf-8"))
        new = yaml.safe_load(Path(new_path).read_text(encoding="utf-8"))
        if old == new:
            verdict = "IDENTICAL"
        elif _normalise(old) == _normalise(new):
            verdict = "COMMENT-ONLY"
        else:
            code_changed = True
            verdict = f"CODE-CHANGED at {_first_difference(_normalise(old), _normalise(new))}"
        print(f"{verdict:60s} {new_path}")
    return 1 if code_changed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
