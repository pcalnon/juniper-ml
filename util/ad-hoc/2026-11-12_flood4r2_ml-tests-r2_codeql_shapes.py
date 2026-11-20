#!/usr/bin/env python3
"""
Scan Python files for the seven CodeQL shapes the flood-4 addenda name, which the prescreen models only in part.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the ml-propose validation's scanner of 2026-11-11, copied here with its logic unchanged (it was written
         in a validator's scratch directory and is in no checkout); util/ad-hoc/2026-10-05_codeql_python_prescreen.py

WHY THIS EXISTS
Each of these shapes opened a CodeQL review thread that blocked a merge with every check green (juniper-ml#2534,
juniper-ml#2545). The screen is deliberately wider than CodeQL, so every hit is a line to read, not a verdict:

1. constant-conditional   an `if` / conditional expression / `assert` whose test is a literal;
2. unused-global          a module-level name bound by assignment and never read in the module (any case);
3. import-both-ways       a module imported as `import m` and as `from m import ...`;
4. bare-await             an expression statement that is `await <name>`;
5. redefined-before-read  a name assigned twice in one block with no read between, or just before a `try:` whose
                          body assigns it first;
6. attribute-overwrite    `self.x` assigned in a subclass `__init__` after `super().__init__()` when a base class in
                          the same file assigns `self.x` too;
7. except-base            `except BaseException` or a bare `except:` whose body does not re-raise.
Also: an implicit string concatenation inside a list, tuple or set display (tokenize).

Usage:
    python3 <this> FILE [FILE ...] [--out <json>]      exit 1 when anything is reported
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import sys
import tokenize
from pathlib import Path


def names_read(node: ast.AST) -> set:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Load, ast.Del))}


def assigned_names(stmt: ast.stmt) -> list:
    if isinstance(stmt, ast.Assign):
        return [t.id for t in stmt.targets if isinstance(t, ast.Name)]
    if isinstance(stmt, ast.AnnAssign) and stmt.value is not None and isinstance(stmt.target, ast.Name):
        return [stmt.target.id]
    return []


def first_binding_before_read(body: list, name: str) -> bool:
    """True when ``body`` assigns ``name`` (a plain assignment) before any statement reads it."""
    for stmt in body:
        if name in names_read(stmt):
            return False
        if name in assigned_names(stmt):
            return True
    return False


def scan_block(body: list, path: str, hits: list) -> None:
    for index, stmt in enumerate(body):
        for name in assigned_names(stmt):
            for later in body[index + 1 :]:
                if isinstance(later, ast.Try) and first_binding_before_read(later.body, name) and not any(name in names_read(part) for handler in later.handlers for part in handler.body):
                    hits.append((path, stmt.lineno, "redefined-before-read", f"{name} is set, then the try body at line {later.lineno} sets it again"))
                    break
                if name in names_read(later):
                    break
                if name in assigned_names(later):
                    hits.append((path, stmt.lineno, "redefined-before-read", f"{name} is assigned again at line {later.lineno} before any read"))
                    break
                if not isinstance(later, (ast.Assign, ast.AnnAssign, ast.Expr)):
                    break


def scan_file(path: Path) -> list:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    hits: list = []
    label = str(path)
    plain_imports, from_imports = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.Assert)) and isinstance(node.test, ast.Constant):
            hits.append((label, node.lineno, "constant-conditional", ast.unparse(node.test)))
        if isinstance(node, ast.While) and isinstance(node.test, ast.Constant) and not node.test.value:
            hits.append((label, node.lineno, "constant-conditional", "while with a false literal"))
        if isinstance(node, ast.Import):
            plain_imports.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            from_imports.add(node.module)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Await) and isinstance(node.value.value, ast.Name):
            hits.append((label, node.lineno, "bare-await", ast.unparse(node)))
        if isinstance(node, ast.ExceptHandler):
            broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "BaseException") or (isinstance(node.type, ast.Tuple) and any(isinstance(e, ast.Name) and e.id == "BaseException" for e in node.type.elts))
            if broad and not any(isinstance(n, ast.Raise) for part in node.body for n in ast.walk(part)):
                hits.append((label, node.lineno, "except-base", "handler catches BaseException and does not re-raise"))
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if isinstance(block, list) and block and isinstance(block[0], ast.stmt):
                scan_block(block, label, hits)
    for module in sorted(plain_imports & from_imports):
        hits.append((label, 0, "import-both-ways", module))
    read_anywhere = names_read(tree)
    exported = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in stmt.targets) and isinstance(stmt.value, (ast.List, ast.Tuple)):
            exported = {e.value for e in stmt.value.elts if isinstance(e, ast.Constant)}
    for stmt in tree.body:
        for name in assigned_names(stmt):
            if name not in read_anywhere and name not in exported and not (name.startswith("__") and name.endswith("__")):
                hits.append((label, stmt.lineno, "unused-global", name))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    def init_attrs(cls: ast.ClassDef) -> dict:
        found = {}
        for item in cls.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                for n in ast.walk(item):
                    if isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Store) and isinstance(n.value, ast.Name) and n.value.id == "self":
                        found.setdefault(n.attr, n.lineno)
        return found

    for cls in classes.values():
        own = init_attrs(cls)
        for base in cls.bases:
            if isinstance(base, ast.Name) and base.id in classes:
                for attr, lineno in own.items():
                    if attr in init_attrs(classes[base.id]):
                        hits.append((label, lineno, "attribute-overwrite", f"{cls.name}.__init__ assigns self.{attr}, which {base.id}.__init__ assigns too"))
    string_ends = {tokenize.STRING, getattr(tokenize, "FSTRING_END", tokenize.STRING)}
    brackets: list = []
    fstring_depth = 0
    previous = None
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == getattr(tokenize, "FSTRING_START", None):
            if fstring_depth == 0 and previous is not None and previous.type in string_ends and brackets and brackets[-1] in "[{":
                hits.append((label, token.start[0], "implicit-concat-in-display", token.string[:40]))
            fstring_depth += 1
        elif token.type == getattr(tokenize, "FSTRING_END", None):
            fstring_depth -= 1
        elif fstring_depth == 0 and token.type == tokenize.OP and token.string in "([{":
            brackets.append(token.string)
        elif fstring_depth == 0 and token.type == tokenize.OP and token.string in ")]}" and brackets:
            brackets.pop()
        elif fstring_depth == 0 and token.type == tokenize.STRING and previous is not None and previous.type in string_ends and brackets and brackets[-1] in "[{":
            hits.append((label, token.start[0], "implicit-concat-in-display", token.string[:40]))
        if fstring_depth == 0 and token.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT):
            previous = token
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    hits: list = []
    for path in args.files:
        hits.extend(scan_file(path))
    for path, lineno, rule, detail in hits:
        print(f"{path}:{lineno}: {rule}: {detail}")
    print(f"{len(hits)} hit(s) in {len(args.files)} file(s)")
    if args.out is not None:
        args.out.write_text(json.dumps([{"path": p, "line": n, "rule": r, "detail": d} for p, n, r, d in hits], indent=2) + "\n", encoding="utf-8")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
