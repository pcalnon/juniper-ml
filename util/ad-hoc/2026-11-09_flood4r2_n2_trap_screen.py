#!/usr/bin/env python3
"""CodeQL trap screen: the seven alert shapes the prescreen does not model, found by AST.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use verification)
Author:      Paul Calnon
Version:     0.2.0
License:     MIT License
Created:     2026-11-09
Status:      ad-hoc -- one-off verification
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     the flood-4 session-4 and session-5 briefs' CodeQL traps (juniper-ml#2534, alert 1088;
             juniper-ml#2545, refused on three more shapes); §8, ruling 11 of
             notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Reports, per file:

- ``constant-conditional``: an ``if`` / ``elif`` / ``while`` / conditional expression whose test is
  a literal constant (``if True:``);
- ``dual-import``: a module imported both as ``import X`` and ``from X import Y``;
- ``unused-global``: a module-level name bound by assignment that no code in the file reads and
  ``__all__`` does not list (dunder names are skipped);
- ``bare-await``: an expression statement that is only ``await <name>`` or ``await <a.b>``;
- ``redefined-before-read``: a name assigned and then assigned again in the same block with
  nothing reading it in between, or assigned again as the first statement of a ``try:`` that
  follows, when every handler leaves (``raise`` / ``return`` / ``continue`` / ``break``) and none
  reads the name: the first value is dead;
- ``overwritten-attribute``: in a subclass's ``__init__``, ``self.x = ...`` after
  ``super().__init__(...)`` when a base class's ``__init__`` already assigns ``self.x``. Bases are
  resolved by name among the classes of every file given, so pass the base's file too;
- ``except-baseexception``: ``except BaseException`` (alone or in a tuple) or a bare ``except:``
  whose handler does not re-raise.

It is a screen, not CodeQL's data flow: a finding is a candidate to read by hand, and no finding
is not a proof.

Exit status: 0 when no file has a finding, 1 when one does, 2 when a file cannot be parsed.

Usage:
    python3 util/ad-hoc/2026-11-09_flood4r2_n2_trap_screen.py FILE [FILE ...]
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def _module_all(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets) and isinstance(node.value, (ast.List, ast.Tuple)):
            names.update(elt.value for elt in node.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str))
    return names


def _plain_target(node: ast.stmt) -> str | None:
    """The name a statement binds, when it is ``name = value`` or ``name: T = value``; else None."""
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
        return node.target.id
    return None


def _mentions(node: ast.AST, name: str) -> bool:
    return any(isinstance(sub, ast.Name) and sub.id == name for sub in ast.walk(node))


def _reads(node: ast.AST, name: str) -> bool:
    return any(isinstance(sub, ast.Name) and sub.id == name and isinstance(sub.ctx, ast.Load) for sub in ast.walk(node))


def _rebinds_without_reading(node: ast.stmt, name: str) -> bool:
    return _plain_target(node) == name and not _reads(node, name)


def _no_path_reads_the_first_value(node: ast.Try, name: str) -> bool:
    """True when the ``try`` rebinds ``name`` first and no handler can pass the old value on.

    Every handler must end by leaving (``raise`` / ``return`` / ``continue`` / ``break``), and no
    handler or ``finally`` may read the name; otherwise the first value can still be read.
    """
    leaves = (ast.Raise, ast.Return, ast.Continue, ast.Break)
    if any(_reads(part, name) for part in [*node.handlers, *node.finalbody]):
        return False
    return all(handler.body and isinstance(handler.body[-1], leaves) for handler in node.handlers)


def _redefined(body: list[ast.stmt]) -> list[tuple[int, str, str]]:
    found = []
    for index, node in enumerate(body):
        name = _plain_target(node)
        if name is None or isinstance(node.value, (ast.Yield, ast.YieldFrom, ast.Await)):
            continue
        for later in body[index + 1 :]:
            if _rebinds_without_reading(later, name):
                found.append((node.lineno, "redefined-before-read", f"{name} (assigned again at line {later.lineno})"))
            elif isinstance(later, ast.Try) and later.body and _rebinds_without_reading(later.body[0], name) and _no_path_reads_the_first_value(later, name):
                found.append((node.lineno, "redefined-before-read", f"{name} (assigned again at line {later.body[0].lineno}, first in a try whose handlers all leave without reading it)"))
            if _mentions(later, name):
                break
    return found


def _init_attributes(cls: ast.ClassDef) -> tuple[dict[str, int], int | None]:
    """``self.x`` assignments in ``__init__`` (name -> line), and the line of ``super().__init__``."""
    attributes: dict[str, int] = {}
    super_line = None
    for item in cls.body:
        if isinstance(item, ast.FunctionDef) and item.name == "__init__":
            for sub in ast.walk(item):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "__init__" and isinstance(sub.func.value, ast.Call) and isinstance(sub.func.value.func, ast.Name) and sub.func.value.func.id == "super":
                    super_line = sub.lineno
                targets = sub.targets if isinstance(sub, ast.Assign) else [sub.target] if isinstance(sub, (ast.AnnAssign, ast.AugAssign)) else []
                for target in targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                        attributes.setdefault(target.attr, target.lineno)
    return attributes, super_line


def _base_names(cls: ast.ClassDef) -> list[str]:
    return [base.id if isinstance(base, ast.Name) else base.attr for base in cls.bases if isinstance(base, (ast.Name, ast.Attribute))]


def _findings(tree: ast.Module, classes: dict[str, ast.ClassDef]) -> list[tuple[int, str, str]]:
    found: list[tuple[int, str, str]] = []
    plain: dict[str, int] = {}
    from_: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.IfExp)) and isinstance(node.test, ast.Constant):
            found.append((node.lineno, "constant-conditional", repr(node.test.value)))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                plain.setdefault(alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            from_.setdefault(node.module, node.lineno)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Await) and isinstance(node.value.value, (ast.Name, ast.Attribute)):
            found.append((node.lineno, "bare-await", ast.unparse(node.value)))
        elif isinstance(node, ast.ExceptHandler):
            caught = [node.type] if node.type is not None and not isinstance(node.type, ast.Tuple) else list(node.type.elts) if node.type is not None else []
            catches_everything = node.type is None or any(isinstance(item, ast.Name) and item.id == "BaseException" for item in caught)
            reraises = any(isinstance(sub, ast.Raise) and sub.exc is None for sub in ast.walk(node))
            if catches_everything and not reraises:
                found.append((node.lineno, "except-baseexception", "bare except" if node.type is None else ast.unparse(node.type)))
        elif isinstance(node, ast.ClassDef):
            own, super_line = _init_attributes(node)
            inherited: dict[str, str] = {}
            pending = _base_names(node)
            seen: set[str] = set()
            while pending:
                base = pending.pop()
                if base in seen or base not in classes:
                    continue
                seen.add(base)
                for attribute in _init_attributes(classes[base])[0]:
                    inherited.setdefault(attribute, base)
                pending.extend(_base_names(classes[base]))
            if super_line is not None:
                found.extend((line, "overwritten-attribute", f"self.{attribute} (already assigned by {inherited[attribute]}.__init__)") for attribute, line in own.items() if attribute in inherited and line > super_line)
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if isinstance(block, list) and block and isinstance(block[0], ast.stmt):
                found.extend(_redefined(block))
    found.extend((plain[name], "dual-import", name) for name in sorted(set(plain) & set(from_)))

    exported = _module_all(tree)
    loads = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        for target in targets:
            if isinstance(target, ast.Name) and not (target.id.startswith("__") and target.id.endswith("__")) and target.id not in loads and target.id not in exported:
                found.append((node.lineno, "unused-global", target.id))
    return sorted(set(found))


def main(argv: list[str] | None = None) -> int:
    paths = [Path(p) for p in (sys.argv[1:] if argv is None else argv)]
    if not paths:
        print(__doc__.splitlines()[0], file=sys.stderr)
        return 2
    trees = []
    classes: dict[str, ast.ClassDef] = {}
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            print(f"{path}: cannot parse: {exc}", file=sys.stderr)
            return 2
        trees.append((path, tree))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.setdefault(node.name, node)
    total = 0
    for path, tree in trees:
        for lineno, kind, detail in _findings(tree, classes):
            total += 1
            print(f"{path}:{lineno}: {kind}: {detail}")
    print(f"{total} finding(s) in {len(paths)} file(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
