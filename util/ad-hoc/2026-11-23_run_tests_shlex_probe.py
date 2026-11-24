"""
Confirm shlex's punctuation_chars behaviour on the workflow line shapes that util/run_tests.py splits.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2615

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: confirm shlex punctuation_chars behaviour on the workflow line shapes.
"""
import shlex


def split(line):
    lex = shlex.shlex(line, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = "#"
    return list(lex)


for line in [
    'pip install --upgrade "pip>=26.1.1" && pip install -e ".[test]"',
    'pip install "juniper-ci-tools>=0.9.0,<0.10.0"',
    "python -m pytest --cov=juniper_doc_tools --cov-report=term-missing --cov-report=json:coverage.json --cov-fail-under=85",
    'juniper-coverage-gap-map --coverage-json coverage.json --enforce --omit "*/__main__.py"',
    "pip install wheel  # trailing comment",
    "a#b c",
    "a&&b",
    "echo foo | tee x",
    'python3 -m unittest -v tests/test_x.py  # also tests/test_ghost.py',
    "cmd 2>&1",
    'make test PYTEST="$VIRTUAL_ENV/bin/python -m pytest"',
    "python3 util/soak_ledger.py verify-probes",
]:
    print(repr(line), "->", split(line))
