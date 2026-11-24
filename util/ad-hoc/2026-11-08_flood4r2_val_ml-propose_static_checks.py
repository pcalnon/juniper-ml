#!/usr/bin/env python3
"""Sweep files for CodeQL's py/implicit-string-concatenation-in-list shape, which the prescreen does not predict.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (independent validation of the Cursor flood-4 round-2 "ml-propose" carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the ml-propose carrier; memory note reference_implicit_string_concat_in_list_blocks_merge

For every element of a List / Tuple / Set display that is a string constant built from MORE THAN ONE adjacent
string token, print ``file:line``. ``util/ad-hoc/2026-10-05_codeql_python_prescreen.py`` predicts unused imports,
locals and globals and unclosed files, but not this query, whose unresolved thread also blocks a merge.
Read-only. Exit 1 when any element is found.
"""

from __future__ import annotations

import ast
import io
import sys
import tokenize
from pathlib import Path


def adjacent_literals(segment: str) -> int:
    """Top-level string literals in ``segment``: a STRING or an f-string's start at f-string depth 0, so the
    quoted arguments inside an f-string's replacement field (``f"{x.replace('-', '_')}"``) are not counted."""
    fs_start = getattr(tokenize, "FSTRING_START", -1)
    fs_end = getattr(tokenize, "FSTRING_END", -2)
    depth = 0
    count = 0
    try:
        for tok in tokenize.generate_tokens(io.StringIO(segment).readline):
            if tok.type == fs_start:
                if depth == 0:
                    count += 1
                depth += 1
            elif tok.type == fs_end:
                depth -= 1
            elif tok.type == tokenize.STRING and depth == 0:
                count += 1
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return 0
    return count


def main(argv: "list[str]") -> int:
    hits = 0
    for name in argv:
        src = Path(name).read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
                for elt in node.elts:
                    if isinstance(elt, (ast.Constant, ast.JoinedStr)) and (isinstance(elt, ast.JoinedStr) or isinstance(elt.value, str)):
                        seg = ast.get_source_segment(src, elt) or ""
                        if adjacent_literals(seg) > 1:
                            hits += 1
                            print(f"{name}:{elt.lineno}: implicit string concatenation inside a {type(node).__name__} display")
    print(f"{hits} implicit-concatenation element(s) in {len(argv)} file(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
