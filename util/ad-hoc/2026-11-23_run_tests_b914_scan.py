"""
Report same-line implicit concatenations of string literals, the B914 shape of flake8-bugbear 26.11.22.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2615 (its test plan: 0 sites); main's #2609 took the B914 fixes

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Its control input, b914_control.py, moved with the data: it holds `x = ["a" "b"]` and `y = f"{x}" "c"`, and the scan reports both (re-run on 2026-11-24: 2 sites, exit 1).

Original docstring, verbatim:

Scratch: report same-line implicit concatenations of string literals (flake8-bugbear 26.11.22's B914 shape).
"""

import sys
import tokenize
from pathlib import Path

SKIP = {tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT}


def units(path: Path):
    """(kind, start_line, end_line) for each token, an f-string collapsed into one STRING unit."""
    depth = 0
    with path.open("rb") as handle:
        for tok in tokenize.tokenize(handle.readline):
            if tok.type == getattr(tokenize, "FSTRING_START", -1):
                if depth == 0:
                    start = tok.start[0]
                depth += 1
                continue
            if tok.type == getattr(tokenize, "FSTRING_END", -1):
                depth -= 1
                if depth == 0:
                    yield ("STRING", start, tok.end[0])
                continue
            if depth:
                continue
            if tok.type in SKIP:
                continue
            yield ("STRING" if tok.type == tokenize.STRING else "OTHER", tok.start[0], tok.end[0])


hits = 0
for name in sys.argv[1:]:
    previous = None
    for unit in units(Path(name)):
        if previous and previous[0] == "STRING" and unit[0] == "STRING" and previous[2] == unit[1]:
            print(f"{name}:{unit[1]}: implicit concatenation on one line")
            hits += 1
        previous = unit
print(f"{hits} site(s)")
sys.exit(1 if hits else 0)
