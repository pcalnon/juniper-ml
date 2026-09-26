#!/usr/bin/env python3
"""Lane A round 2: re-derive the generic pre-commit hooks that apply to 990ef3f9's changed files (the
pre-commit-hooks v6 set: end-of-file-fixer, trailing-whitespace, check-merge-conflict, check-added-large-files
--maxkb=1000, check-ast, debug-statements, detect-private-key). reports/ is excluded by the config's global
exclude; notes/ is excluded from markdownlint; flake8/black/isort/mypy/bandit are scoped to scripts|tests.
Reads each file with `git show 990ef3f9:<path>` (read-only)."""
import ast
import re
import subprocess

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
files = subprocess.run(["git", "diff", "--name-only", "e2f87aae", "990ef3f9"], cwd=WT, capture_output=True, text=True).stdout.split()
EXCL = re.compile(r"^(reports/|prompts/|resources/|logs/|images/|data/)")
for f in files:
    b = subprocess.run(["git", "show", f"990ef3f9:{f}"], cwd=WT, capture_output=True).stdout
    if EXCL.match(f):
        print(f"skip (global exclude) {f}")
        continue
    t = b.decode("utf-8")
    probs = []
    if not t.endswith("\n") or t.endswith("\n\n"):
        probs.append("EOF")
    tw = [i + 1 for i, l in enumerate(t.split("\n")) if l != l.rstrip(" \t")]
    if tw:
        probs.append(f"trailing-ws lines {tw[:5]}")
    if re.search(r"^(<<<<<<< |=======$|>>>>>>> )", t, re.M):
        probs.append("merge-conflict marker")
    if len(b) > 1000 * 1024:
        probs.append(f"large {len(b)} bytes")
    if "-----BEGIN" in t and "PRIVATE KEY" in t:
        probs.append("private-key marker")
    if f.endswith(".py"):
        try:
            tree = ast.parse(t)
            dbg = [n.lineno for n in ast.walk(tree) if (isinstance(n, ast.Call) and getattr(n.func, "id", "") == "breakpoint")
                   or (isinstance(n, (ast.Import, ast.ImportFrom)) and any(a.name.split(".")[0] in {"pdb", "ipdb", "pudb"} for a in n.names))]
            if dbg:
                probs.append(f"debug statements at {dbg}")
        except SyntaxError as e:
            probs.append(f"AST: {e}")
    print(f"{'OK  ' if not probs else 'FAIL'} {f} {probs if probs else ''} ({len(b)} bytes)")
