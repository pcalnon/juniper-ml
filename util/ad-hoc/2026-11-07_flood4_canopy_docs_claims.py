#!/usr/bin/env python3
"""
Re-derive the code-span claims in the canopy flood-4 docs carrier's added lines against the tree on main.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy docs carrier (#790 #791 #793 #796)

Usage: 2026-11-07_flood4_canopy_docs_claims.py <docs worktree> <stripped patch>...

For every `code span` in a line the drafts add, classify it and look it up in the worktree (whose
code, tests and workflows are main's; only docs differ):
  path    -> exists relative to the repo root, src/, src/tests/ or .github/workflows/
  test    -> a Test* class or test_* function defined somewhere under src/tests/
  symbol  -> an identifier that occurs in src/, .github/, conf/ or util/ (word match, non-docs)
  other   -> printed for a human read (commands, values, YAML fragments)
Tokens not found are listed first; nothing is judged automatically beyond existence.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

SPAN = re.compile(r"`([^`]+)`")
PATHLIKE = re.compile(r"^[\w.\-/*]+\.(py|ya?ml|md|toml|json|lock|txt|cfg|ini|sh|bash)$|^[\w.\-]+/[\w.\-/]*$")
TESTNAME = re.compile(r"^(Test\w+|test_\w+)$")
IDENT = re.compile(r"^[A-Za-z_][\w.]*$")


def grep(root: Path, pattern: str, paths: list[str]) -> bool:
    proc = subprocess.run(["git", "-C", str(root), "grep", "-q", "-w", "-F", "-e", pattern, "--", *paths], capture_output=True)
    return proc.returncode == 0


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve()
    tokens: dict[str, set] = {}
    for patch in argv[2:]:
        current = None
        for line in Path(patch).read_text(encoding="utf-8").splitlines():
            if line.startswith("+++ b/"):
                current = line[6:]
            elif line.startswith("+") and not line.startswith("+++"):
                for tok in SPAN.findall(line[1:]):
                    tokens.setdefault(tok.strip(), set()).add(f"{Path(patch).name.split('.')[0]}:{current}")
    results = []
    for tok, where in sorted(tokens.items()):
        kind, found = "other", None
        if PATHLIKE.match(tok) and not tok.startswith(("http", "-")):
            kind = "path"
            cands = [tok, f"src/{tok}", f"src/tests/{tok}", f".github/workflows/{tok}"]
            found = any((root / c).exists() for c in cands) or any(root.glob(tok)) if "*" in tok else any((root / c).exists() for c in cands)
        elif TESTNAME.match(tok):
            kind = "test"
            found = grep(root, tok, ["src/tests"])
        elif IDENT.match(tok) and len(tok) > 3 and ("_" in tok or "." in tok or any(c.isupper() for c in tok[1:])):
            kind = "symbol"
            found = grep(root, tok.split(".")[-1], ["src", ".github", "conf", "util", "pyproject.toml", ".gitleaks.toml"])
        results.append({"token": tok, "kind": kind, "found": found, "where": sorted(where)})
    missing = [r for r in results if r["found"] is False]
    print(f"tokens={len(results)} path/test/symbol checked={sum(1 for r in results if r['found'] is not None)} NOT FOUND={len(missing)}")
    for r in missing:
        print(f"NOT FOUND [{r['kind']}] {r['token']!r} in {r['where']}")
    print(json.dumps({"summary": {"tokens": len(results), "not_found": len(missing)}}, indent=None))
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
