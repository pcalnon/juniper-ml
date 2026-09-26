#!/usr/bin/env python3
"""Lane B r2: F541-style scan (an f-string with no placeholder) over the touched ad-hoc tools, by AST."""
import ast
import sys
from pathlib import Path

for p in sorted(Path(sys.argv[1]).glob("*.py")):
    tree = ast.parse(p.read_text(encoding="utf-8"))
    hits = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.JoinedStr) and not any(isinstance(v, ast.FormattedValue) for v in n.values)]
    print(f"{p.name}: {hits if hits else 'none'}")
