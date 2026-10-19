"""
Flag modules imported with both `import M` and `from M import ...` (CodeQL py/import-and-import-from).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-18
Status: ad-hoc — one-off (screening the turing Session 1 Python files after juniper-ml#2242)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2242; util/ad-hoc/2026-10-05_codeql_python_prescreen.py (the general pre-screen, which
         does not cover this query); util/ad-hoc/README.md § CodeQL scans this directory

Why: on juniper-ml#2242 CodeQL posted a note-level `py/import-and-import-from` comment on
`import unittest` + `from unittest import mock`. A `main` pull_request rule sets
`required_review_thread_resolution: true`, so even that note blocked the merge with every check green. The
repo idiom that avoids it is `import unittest` + `import unittest.mock as mock`. This screen ran over the
remaining Session 1 files before their PRs opened; it found nothing.

Correction (2026-10-19): the general pre-screen does cover this query. Its `import-and-import-from` rule
(standard-library modules only, as calibrated on juniper-ml#2157) has been there since it landed in
juniper-ml#2183, and on the file CodeQL flagged in #2242 (`tests/test_claude_agent_guard.py` at `afb75f71`)
it reports exactly that alert. This screen differs mainly in also flagging non-standard-library modules,
which CodeQL did not flag on #2157.

Usage:
    python3 -I util/ad-hoc/2026-10-18_codeql_import_and_import_from_screen.py FILE.py [FILE.py ...]

Exit 0 when no file has the pattern; 1 when any does.
"""
import ast
import sys
from pathlib import Path

hits = 0
for p in map(Path, sys.argv[1:]):
    tree = ast.parse(p.read_text(encoding="utf-8"))
    plain, froms = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                plain.setdefault(a.name, node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            froms.setdefault(node.module, node.lineno)
    both = sorted(set(plain) & set(froms))
    for m in both:
        hits += 1
        print(f"{p}: '{m}' imported at line {plain[m]} and from-imported at line {froms[m]}")
    if not both:
        print(f"clean  {p}")
sys.exit(1 if hits else 0)
