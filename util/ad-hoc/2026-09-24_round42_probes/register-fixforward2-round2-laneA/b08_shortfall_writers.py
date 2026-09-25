#!/usr/bin/env python3
"""Lane A round 2: every write to self._dataset_shortfall in juniper-cascor's src/api/lifecycle/manager.py, by
enclosing function and line, at each given rev (local clone, read-only git show). Also lists reads.

A "write" is an Assign / AnnAssign / AugAssign whose target is the attribute `_dataset_shortfall` on any object,
plus any setattr(..., "_dataset_shortfall", ...) call.
Usage: b08_shortfall_writers.py <rev> [<rev> ...]
"""
import ast
import subprocess
import sys

REPO = "/home/pcalnon/Development/python/Juniper/juniper-cascor"
REL = "src/api/lifecycle/manager.py"
ATTR = "_dataset_shortfall"


def enclosing(tree):
    parent = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            parent[ch] = node
    return parent


for rev in sys.argv[1:]:
    p = subprocess.run(["git", "show", f"{rev}:{REL}"], cwd=REPO, capture_output=True, text=True)
    if p.returncode:
        print(f"== {rev}: {p.stderr.strip()}")
        continue
    tree = ast.parse(p.stdout)
    par = enclosing(tree)

    def func_of(n):
        while n in par:
            n = par[n]
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return n.name
        return "<module>"

    writes, reads = [], []
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]
        for t in targets:
            for sub in ast.walk(t):
                if isinstance(sub, ast.Attribute) and sub.attr == ATTR:
                    writes.append((node.lineno, func_of(node)))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "setattr" and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and node.args[1].value == ATTR:
            writes.append((node.lineno, func_of(node) + " (setattr)"))
        if isinstance(node, ast.Attribute) and node.attr == ATTR and isinstance(node.ctx, ast.Load):
            reads.append((node.lineno, func_of(node)))
    writes = sorted(set(writes))
    print(f"== {rev}: {len(writes)} write(s): " + ", ".join(f"{f} :{ln}" for ln, f in writes))
    print(f"   reads: " + ", ".join(f"{f} :{ln}" for ln, f in sorted(set(reads))))
