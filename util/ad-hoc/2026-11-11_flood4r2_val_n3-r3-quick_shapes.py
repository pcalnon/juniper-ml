"""
Screen Python files, by syntax, for the seven CodeQL shapes the flood-4 addenda name and the prescreen does not model.

The shapes (each has opened a merge-blocking review thread in this arc):

  constant-conditional    ``if`` / ``elif`` / a conditional expression whose test is a literal (``while True`` is not one)
  unused-global           a module-level name bound by a plain assignment and read nowhere in the module
  import-both-ways        one module imported as ``import X`` and as ``from X import Y``
  bare-await              an expression statement that is only ``await <name>``
  defined-twice           a local assigned, then assigned again by the first statement of the ``try`` that follows
  overwritten-attribute   a subclass ``__init__`` that assigns ``self.x`` after calling ``super().__init__``
  except-base             ``except BaseException`` or a bare ``except`` whose body has no bare ``raise``

Usage: ``<this script> --pair NEW OLD [--pair NEW OLD ...] [FILE ...]``. A pair reports only the hits NEW has and OLD
lacks (compared by shape and name, not by line); a lone FILE reports every hit. The result is a list to read, not a
verdict: these are syntactic screens.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; tmp/flood4/session4 and session5 addenda (CodeQL shapes)
"""

import argparse
import ast
import json
from pathlib import Path


def hits(path: Path) -> list:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []

    def add(shape: str, node: ast.AST, name: str) -> None:
        found.append({"shape": shape, "line": getattr(node, "lineno", 0), "name": name})

    read_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    read_names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    exported = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in stmt.targets) and isinstance(stmt.value, (ast.List, ast.Tuple)):
            exported |= {e.value for e in stmt.value.elts if isinstance(e, ast.Constant)}
    for stmt in tree.body:
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target] if isinstance(stmt, ast.AnnAssign) else []
        for target in targets:
            if isinstance(target, ast.Name) and not target.id.startswith("__") and target.id not in read_names and target.id not in exported:
                add("unused-global", stmt, target.id)

    plain, from_ = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                plain.setdefault(alias.name, node)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            from_.setdefault(node.module, node)
        elif isinstance(node, (ast.If, ast.IfExp)) and isinstance(node.test, ast.Constant):
            add("constant-conditional", node, repr(node.test.value))
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Await) and isinstance(node.value.value, ast.Name):
            add("bare-await", node, node.value.value.id)
        elif isinstance(node, ast.ExceptHandler):
            base = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "BaseException")
            reraises = any(isinstance(n, ast.Raise) and n.exc is None for n in ast.walk(node))
            if base and not reraises:
                add("except-base", node, "bare" if node.type is None else "BaseException")
        elif isinstance(node, ast.ClassDef) and node.bases:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    seen_super = False
                    for stmt in item.body:
                        calls = [c for c in ast.walk(stmt) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "__init__"]
                        if calls:
                            seen_super = True
                            continue
                        if seen_super and isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                            for target in stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]:
                                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                                    add("overwritten-attribute", stmt, f"{node.name}.{target.attr}")
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if not isinstance(block, list):
                continue
            for first, second in zip(block, block[1:]):
                if isinstance(first, ast.Assign) and len(first.targets) == 1 and isinstance(first.targets[0], ast.Name) and isinstance(second, ast.Try) and second.body:
                    opener = second.body[0]
                    again = isinstance(opener, ast.Assign) and any(isinstance(t, ast.Name) and t.id == first.targets[0].id for t in opener.targets)
                    reads = again and any(isinstance(n, ast.Name) and n.id == first.targets[0].id and isinstance(n.ctx, ast.Load) for n in ast.walk(opener.value))
                    if again and not reads:
                        add("defined-twice", first, first.targets[0].id)
    for module in sorted(set(plain) & set(from_)):
        add("import-both-ways", from_[module], module)
    return sorted(found, key=lambda h: (h["line"], h["shape"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", nargs=2, action="append", default=[], metavar=("NEW", "OLD"))
    ap.add_argument("--json")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args()
    report = {}
    for new, old in args.pair:
        old_keys = {(h["shape"], h["name"]) for h in hits(Path(old))}
        report[new] = {"compared_with": old, "new_hits": [h for h in hits(Path(new)) if (h["shape"], h["name"]) not in old_keys]}
    for name in args.files:
        report[name] = {"compared_with": None, "new_hits": hits(Path(name))}
    total = 0
    for name, rec in report.items():
        total += len(rec["new_hits"])
        print(f"{name}: {len(rec['new_hits'])} hit(s)" + (" not in " + rec["compared_with"] if rec["compared_with"] else ""))
        for h in rec["new_hits"]:
            print(f"    {h['line']}: {h['shape']}: {h['name']}")
    print(f"{total} hit(s) in {len(report)} file(s)")
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
