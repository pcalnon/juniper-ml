#!/usr/bin/env python3
"""Lane A round 2: map every route in juniper-data's routes/datasets.py to whether its handler body calls
record_access (directly, or through a helper in the same file), at a given fetched copy.

AST-based: for each function decorated with @router.<method>(path), list the lines inside it that mention
record_access. Also lists any module-level helper that calls record_access and which handlers call that helper.
Usage: b06_record_access_routes.py <path to datasets.py>
"""
import ast
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding="utf-8")
tree = ast.parse(src)
lines = src.split("\n")


def calls_name(node, name):
    hits = []
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute) and n.attr == name:
            hits.append(n.lineno)
        elif isinstance(n, ast.Name) and n.id == name:
            hits.append(n.lineno)
    return sorted(set(hits))


funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
helpers = {f.name for f in funcs if calls_name(f, "record_access") and not f.decorator_list}
print("helpers calling record_access:", helpers or "none")
for f in funcs:
    route = None
    for d in f.decorator_list:
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in {"get", "post", "patch", "put", "delete", "head"}:
            path = d.args[0].value if d.args and isinstance(d.args[0], ast.Constant) else "?"
            route = f"{d.func.attr.upper():6} {path}"
    if route is None:
        continue
    direct = calls_name(f, "record_access")
    via = [h for h in helpers if calls_name(f, h)]
    print(f"{route:45} {f.name:32} def@{f.lineno:<5} record_access@{direct} via={via}")
