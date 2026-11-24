"""
Scan Python files for the seven CodeQL shapes the flood-4 briefs say the prescreen does not model, and say which hits
a carrier ADDS over a baseline copy of the same file.

The shapes (session-4 addendum: the first four; session-5 addendum, "THREE MORE CODEQL SHAPES": the last three):

  constant-conditional      an `if` / `elif` / conditional expression whose test is a literal
  unused-global             a module-level name that is assigned and never read in the module (`__all__`-listed and
                            dunder names excepted; `pytestmark` is reported, marked as the known false positive)
  import-both-ways          a module imported as `import X` and as `from X import ...`
  bare-await                a statement that is only `await <name>`
  redefined-before-read     an assignment to a local followed, with no read of it between, by another assignment to
                            it: the next statement, or the first statements of a `try:` body that follows
  attribute-overwrite       a subclass `__init__` that assigns `self.x` after `super().__init__()` when a base class in
                            the same file assigns `self.x` too (a base outside the file is listed as "unchecked-base")
  except-baseexception      `except BaseException:` or a bare `except:` whose body has no `raise`

It is a screen, not CodeQL: it reads syntax only, so it can miss a shape that needs data flow and can report one CodeQL
would not. With --baseline-root, each file is also scanned in the baseline tree and a hit is printed as NEW only when
the baseline copy has no hit with the same shape and source line text.

Usage: python <this> [--baseline-root <dir> --root <dir>] <files...>   (files relative to --root when it is given)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt (TRAPS), tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt (THREE MORE CODEQL SHAPES);
         juniper-cascor fix/ws-resume-losses, round 3
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path


def names_loaded(node: ast.AST) -> set:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Load, ast.Del))}


def simple_targets(stmt: ast.stmt) -> set:
    """The plain names a statement assigns at its own level (an Assign or AnnAssign with a value)."""
    out = set()
    if isinstance(stmt, ast.Assign):
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                out.add(target.id)
    elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None and isinstance(stmt.target, ast.Name):
        out.add(stmt.target.id)
    return out


def stmt_value(stmt: ast.stmt) -> ast.AST:
    return stmt.value if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and stmt.value is not None else ast.Pass()


def redefinitions(body: list) -> list:
    """(line, name) for an assignment whose value nothing can read before the name is assigned again."""
    hits = []
    for first, second in zip(body, body[1:]):
        for name in simple_targets(first):
            if isinstance(second, (ast.Assign, ast.AnnAssign)):
                if name in simple_targets(second) and name not in names_loaded(stmt_value(second)):
                    hits.append((first.lineno, name))
            elif isinstance(second, ast.Try):
                for inner in second.body:
                    if name in names_loaded(inner):
                        break
                    if name in simple_targets(inner):
                        readers = second.handlers + second.orelse + second.finalbody
                        if not any(name in names_loaded(part) for part in readers):
                            hits.append((first.lineno, name))
                        break
    return hits


def init_self_assignments(cls: ast.ClassDef) -> tuple:
    """(attributes `__init__` assigns to self, those assigned after a super().__init__() call)."""
    every, after_super = set(), set()
    for item in cls.body:
        if isinstance(item, ast.FunctionDef) and item.name == "__init__":
            seen_super = False
            for stmt in item.body:
                calls = [n for n in ast.walk(stmt) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "__init__"]
                for node in ast.walk(stmt):
                    if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and isinstance(node.value, ast.Name) and node.value.id == "self":
                        every.add(node.attr)
                        if seen_super:
                            after_super.add(node.attr)
                if calls:
                    seen_super = True
    return every, after_super


def scan(path: Path) -> list:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source, filename=str(path))
    hits = []

    def add(shape: str, lineno: int, note: str = "") -> None:
        hits.append({"shape": shape, "line": lineno, "text": lines[lineno - 1].strip() if 0 < lineno <= len(lines) else "", "note": note})

    plain_imports, from_imports = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp)) and isinstance(node.test, ast.Constant):
            add("constant-conditional", node.lineno)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                plain_imports.setdefault(alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            from_imports.setdefault(node.module, node.lineno)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Await) and isinstance(node.value.value, ast.Name):
            add("bare-await", node.lineno)
        elif isinstance(node, ast.ExceptHandler):
            catches_all = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "BaseException")
            if catches_all and not any(isinstance(n, ast.Raise) for n in ast.walk(node)):
                add("except-baseexception", node.lineno)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for block in ast.walk(node):
                for field in ("body", "orelse", "finalbody"):
                    body = getattr(block, field, None)
                    if isinstance(body, list) and body and isinstance(body[0], ast.stmt):
                        for lineno, name in redefinitions(body):
                            add("redefined-before-read", lineno, name)
    for module in sorted(set(plain_imports) & set(from_imports)):
        add("import-both-ways", from_imports[module], module)

    exported = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in stmt.targets) and isinstance(stmt.value, (ast.List, ast.Tuple)):
            exported = {e.value for e in stmt.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
    read_anywhere = names_loaded(tree)
    for stmt in tree.body:
        for name in sorted(simple_targets(stmt)):
            if name not in read_anywhere and name not in exported and not (name.startswith("__") and name.endswith("__")):
                add("unused-global", stmt.lineno, name + (" (known false positive: pytest reads it)" if name == "pytestmark" else ""))

    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for cls in classes.values():
        _, after_super = init_self_assignments(cls)
        for base in cls.bases:
            base_name = base.id if isinstance(base, ast.Name) else None
            if base_name in classes:
                base_attrs, _ = init_self_assignments(classes[base_name])
                for attr in sorted(after_super & base_attrs):
                    add("attribute-overwrite", cls.lineno, f"{cls.name}.{attr} also assigned by {base_name}.__init__")
            elif after_super and base_name not in ("object", "Exception"):
                add("unchecked-base", cls.lineno, f"{cls.name} assigns {sorted(after_super)} after super().__init__(); base {ast.unparse(base)} is outside this file")
    # A redefinition found through several enclosing blocks is one hit.
    unique = {(h["shape"], h["line"], h["note"]): h for h in hits}
    return sorted(unique.values(), key=lambda h: (h["line"], h["shape"]))


#: The literal greps the briefs name, as (label, regex), applied line by line.
LITERAL_GREPS = [
    ("bare await statement", r"^\s+await [A-Za-z_][A-Za-z_0-9]*\s*$"),
    ("constant conditional", r"^\s*(if|elif|while) (True|False|None|[0-9]+)\s*:"),
    ("except BaseException or bare except", r"except BaseException|except\s*:"),
    ("import of a module by `import X`", r"^\s*import [A-Za-z_][A-Za-z_0-9.]*( as [A-Za-z_][A-Za-z_0-9]*)?\s*$"),
]


def literal_greps(paths: list) -> None:
    """Print every line the briefs' own greps match, and each default assigned on the line before a `try:`."""
    for label, pattern in LITERAL_GREPS:
        regex = re.compile(pattern)
        print(f"## {label}: {pattern}")
        count = 0
        for path in paths:
            lines = path.read_text(encoding="utf-8").splitlines()
            from_modules = {m.group(1) for m in (re.match(r"\s*from ([A-Za-z_][A-Za-z_0-9.]*) import ", line) for line in lines) if m}
            for number, line in enumerate(lines, 1):
                if not regex.search(line):
                    continue
                if label.startswith("import of a module"):
                    # Only an `import X` whose X is also imported `from X import ...` in the same file is the shape.
                    if line.split()[1] not in from_modules:
                        continue
                count += 1
                print(f"   {path.name}:{number}: {line.strip()}")
        print(f"   [{count} line(s)]")
    print("## an assignment on the line before a `try:`")
    count = 0
    for path in paths:
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, 1):
            if re.match(r"^\s*try:\s*$", line) and number > 1 and re.match(r"^\s*[A-Za-z_][A-Za-z_0-9]* = ", lines[number - 2]):
                count += 1
                print(f"   {path.name}:{number - 1}: {lines[number - 2].strip()}")
    print(f"   [{count} line(s); each is read by eye: the shape needs the try body to re-assign the name before any read]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", help="the tree the files are relative to")
    ap.add_argument("--baseline-root", help="a tree holding the baseline copies (same relative paths)")
    ap.add_argument("--out", help="write the full result as JSON")
    ap.add_argument("--literal-greps", action="store_true", help="also print the briefs' literal greps over the files")
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()
    root = Path(args.root) if args.root else None
    if args.literal_greps:
        literal_greps([root / rel if root else Path(rel) for rel in args.files])
    result = {"root": args.root, "baseline_root": args.baseline_root, "files": {}}
    new_total = 0
    for rel in args.files:
        path = root / rel if root else Path(rel)
        hits = scan(path)
        baseline_keys = None
        if args.baseline_root:
            base_path = Path(args.baseline_root) / rel
            baseline_keys = {(h["shape"], h["text"]) for h in scan(base_path)} if base_path.exists() else set()
        for hit in hits:
            hit["new"] = baseline_keys is None or (hit["shape"], hit["text"]) not in baseline_keys
            new_total += hit["new"]
        result["files"][rel] = hits
        print(f"{rel}: {len(hits)} hit(s), {sum(h['new'] for h in hits)} new")
        for hit in hits:
            print(f"   {'NEW ' if hit['new'] else 'base'} {hit['shape']:<22} line {hit['line']:<5} {hit['note'] or hit['text'][:110]}")
    result["new_hits"] = new_total
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
            fh.write("\n")
    print("new hits:", new_total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
