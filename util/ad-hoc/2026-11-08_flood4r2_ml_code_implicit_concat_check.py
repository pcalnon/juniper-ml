#!/usr/bin/env python3
"""
Flag implicit string concatenation directly inside a list display, which CodeQL reports and the prescreen does not model.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 round-2 ml-code carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: reference_implicit_string_concat_in_list_blocks_merge.md (an unresolved CodeQL thread blocks merge);
         util/ad-hoc/2026-10-05_codeql_python_prescreen.py has no rule for py/implicit-string-concatenation-in-list.

Usage: python3 -I 2026-11-08_flood4r2_ml_code_implicit_concat_check.py <file.py> ...

Tokenizes each file and reports two adjacent string tokens whose innermost open bracket is ``[``.
A tuple or a call argument is not reported (the CodeQL query is scoped to lists). Exit 1 on a finding.
"""
import sys
import tokenize

SKIP = (tokenize.NL, tokenize.COMMENT, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT)


def scan(path: str) -> list:
    found = []
    stack = []
    prev = None
    with open(path, "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type == tokenize.OP and tok.string in "([{":
                stack.append(tok.string)
            elif tok.type == tokenize.OP and tok.string in ")]}" and stack:
                stack.pop()
            if tok.type in SKIP:
                continue
            if tok.type == tokenize.STRING and prev is not None and prev.type == tokenize.STRING and stack and stack[-1] == "[":
                found.append(tok.start[0])
            prev = tok
    return found


def main(argv: list) -> int:
    total = 0
    for path in argv[1:]:
        for line in scan(path):
            print("%s:%d: implicit string concatenation directly inside a list display" % (path, line))
            total += 1
    print("%d finding(s) in %d file(s)" % (total, len(argv) - 1))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
