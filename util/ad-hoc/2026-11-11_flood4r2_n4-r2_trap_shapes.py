#!/usr/bin/env python3
"""
The seven CodeQL shapes the prescreen does not model, searched for in the given Python files.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (pre-merge screen for the N-4 round-2 carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (section 8, ruling 11);
         util/ad-hoc/2026-10-05_codeql_python_prescreen.py (the prescreen these shapes escape)

Adapted from the round-1 code validator's helper (same rules), with its known-answer fixture embedded. Usage::

    python3 <this file> [--base-dir <dir holding the files' base copies, by basename>] FILE [FILE ...]
    python3 <this file> --known-answer

Reports, per file:

(1) a bare ``await <name>`` statement;
(2) a constant in a conditional (``if`` / ``while`` / ternary on a literal; ``while True`` is listed separately, as idiom);
(3) a module-level name assigned and never read in the file (not in ``__all__``, not dunder);
(4) a module imported both as ``import X`` and ``from X import Y``;
(5) a handler for ``BaseException``, or a bare ``except`` clause, whose body never re-raises;
(6) a subclass ``__init__`` that assigns ``self.x`` after ``super().__init__()`` where the base class's ``__init__`` also
    assigns it (bases defined in the same file, plus Starlette's WebSocket and logging.Handler); an assignment after
    ``super().__init__()`` with an unknown base is listed as "review";
(7) a local assigned and then assigned again in the same block before anything reads it, or a default assigned just
    before a ``try:`` whose body re-assigns it while no handler can let the default be read (a heuristic, not a CFG).

With ``--base-dir``, a hit whose source line also exists in the base copy is marked "(on base)". The exit status is 1
when any hit is neither on base, nor idiom, nor a "review" line. ``--known-answer`` scans an embedded fixture holding
one instance of each shape, and three near-misses that must not be flagged, and exits 0 only on the exact answer.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BARE_AWAIT = re.compile(r"^\s+await [A-Za-z_][A-Za-z_0-9]*\s*$")
UNUSED_NAME_OK = re.compile(r"^(_+|__.*|empty|dummy|.*unused.*)$")
KNOWN_BASE_ATTRS = {
    "WebSocket": {"scope", "_receive", "_send", "client_state", "application_state"},
    "Handler": {"filters", "_name", "level", "formatter", "_closed", "lock"},
}
NON_BLOCKING = {"while-true-idiom", "review-assigns-after-super"}

#: One instance of each shape (never imported or run), and three near-misses: an unknown base, a default the handler
#: lets through, and a broad handler that re-raises. The "@@" breaks keep a plain-text search of this file for the
#: shapes from matching the fixture; they are removed before it is parsed.
FIXTURE = '''import asyncio
import os
from os import path

LEFTOVER = 3


class Base:
    def __init__(self):
        self.level = 1


class Child(Base):
    def __init__(self):
        super().__init__()
        self.level = 2


class Elsewhere(dict):
    def __init__(self):
        super().__init__()
        self.extra = 2


async def shapes(task):
    aw@@ait task
    if Tr@@ue:
        print(os.sep, path.sep)
    rc = compute()
    rc = compute()
    result = compute()
    try:
        result = compute()
    except ValueError:
        return None
    kept = compute()
    try:
        kept = compute()
    except ValueError:
        print("the default is read below")
    try:
        await asyncio.sleep(0)
    except Base@@Exception:
        print("swallowed")
    try:
        await asyncio.sleep(0)
    except Base@@Exception:
        raise
    return rc, result, kept


def compute():
    return 1
'''.replace("@@", "")
FIXTURE_ANSWER = [
    ("imported-both-ways", 3),
    ("unused-global", 5),
    ("overwrites-inherited-attribute", 16),
    ("review-assigns-after-super", 22),
    ("bare-await", 26),
    ("constant-conditional", 27),
    ("variable-defined-multiple-times", 29),
    ("variable-defined-multiple-times", 31),
    ("except-baseexception-no-reraise", 43),
]


def reads(node: ast.AST, name: str) -> bool:
    return any(isinstance(sub, ast.Name) and sub.id == name and isinstance(sub.ctx, (ast.Load, ast.Del)) for sub in ast.walk(node))


def simple_literal(value: ast.expr) -> bool:
    """CodeQL's "uninteresting" first definition: None, True, False, zero, the empty string, an empty list/tuple/dict."""
    if isinstance(value, ast.Constant):
        inner = value.value
        if inner is None or isinstance(inner, bool):
            return True
        return (isinstance(inner, (int, float)) and inner == 0) or (isinstance(inner, str) and inner == "")
    if isinstance(value, (ast.List, ast.Tuple)):
        return not value.elts
    return isinstance(value, ast.Dict) and not value.keys


def simple_target(stmt: ast.stmt) -> tuple[str | None, bool]:
    """The name a plain ``name = value`` statement assigns, and whether its value is a simple literal."""
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        return stmt.targets[0].id, simple_literal(stmt.value)
    return None, False


def assigns_first(block: list, name: str) -> bool:
    """Whether the first statement of ``block`` that touches ``name`` assigns it without reading it."""
    for stmt in block:
        target, _ = simple_target(stmt)
        if target == name and not reads(stmt.value, name):
            return True
        if reads(stmt, name) or any(isinstance(sub, ast.Name) and sub.id == name for sub in ast.walk(stmt)):
            return False
    return False


def terminates(block: list) -> bool:
    return bool(block) and isinstance(block[-1], (ast.Raise, ast.Return, ast.Continue, ast.Break))


def dead_stores(block: list, lines: list) -> list:
    hits = []
    for index, stmt in enumerate(block):
        name, literal = simple_target(stmt)
        if name is None or literal or UNUSED_NAME_OK.match(name):
            continue
        for later in block[index + 1 :]:
            later_name, _ = simple_target(later)
            if later_name == name and not reads(later.value, name):
                hits.append(("variable-defined-multiple-times", stmt.lineno, lines[stmt.lineno - 1].strip()))
                break
            if isinstance(later, ast.Try) and assigns_first(later.body, name):
                handlers_safe = all(terminates(handler.body) or assigns_first(handler.body, name) for handler in later.handlers)
                if handlers_safe and not any(reads(node, name) for node in later.finalbody):
                    hits.append(("variable-defined-multiple-times", stmt.lineno, lines[stmt.lineno - 1].strip() + "   <- default before try"))
                break
            if any(isinstance(sub, ast.Name) and sub.id == name for sub in ast.walk(later)):
                break
    return hits


def _self_attrs(node: ast.AST) -> list[tuple[ast.AST, str]]:
    """Every ``self.<attr> = ...`` target under ``node``, with the assigning statement."""
    found = []
    for sub in ast.walk(node):
        targets = sub.targets if isinstance(sub, ast.Assign) else [sub.target] if isinstance(sub, ast.AnnAssign) else []
        for target in targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                found.append((sub, target.attr))
    return found


def scan_text(text: str) -> list:
    lines = text.splitlines()
    tree = ast.parse(text)
    hits = []
    for number, line in enumerate(lines, 1):
        if BARE_AWAIT.match(line):
            hits.append(("bare-await", number, line.strip()))
    for node in ast.walk(tree):
        test = getattr(node, "test", None) if isinstance(node, (ast.If, ast.While, ast.IfExp)) else None
        if isinstance(test, ast.Constant):
            idiom = isinstance(node, ast.While) and test.value is True
            hits.append(("while-true-idiom" if idiom else "constant-conditional", node.lineno, lines[node.lineno - 1].strip()))
    plain = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in plain:
            hits.append(("imported-both-ways", node.lineno, lines[node.lineno - 1].strip()))
    assigned: dict[str, int] = {}
    exported: set = set()
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        for target in targets:
            if isinstance(target, ast.Name) and target.id == "__all__" and isinstance(getattr(node, "value", None), (ast.List, ast.Tuple)):
                exported = {elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)}
            elif isinstance(target, ast.Name) and not (target.id.startswith("__") and target.id.endswith("__")):
                assigned.setdefault(target.id, node.lineno)
    read = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    for name, lineno in assigned.items():
        if name not in read and name not in exported:
            hits.append(("unused-global", lineno, lines[lineno - 1].strip()))
    # (5) a BaseException handler, or a bare one, that never re-raises
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            kinds = [node.type] if not isinstance(node.type, ast.Tuple) else list(node.type.elts)
            broad = node.type is None or any(isinstance(kind, ast.Name) and kind.id == "BaseException" for kind in kinds)
            if broad and not any(isinstance(sub, ast.Raise) for sub in ast.walk(node)):
                hits.append(("except-baseexception-no-reraise", node.lineno, lines[node.lineno - 1].strip()))
    # (6) a subclass __init__ re-assigning what the base __init__ assigned
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    inits = {cls.name: item for cls in classes for item in cls.body if isinstance(item, ast.FunctionDef) and item.name == "__init__"}
    init_attrs = {name: {attr for _, attr in _self_attrs(item)} for name, item in inits.items()}
    for cls in classes:
        bases = [base.id if isinstance(base, ast.Name) else base.attr if isinstance(base, ast.Attribute) else "?" for base in cls.bases]
        if not bases or cls.name not in inits:
            continue
        known = [base for base in bases if base in init_attrs or base in KNOWN_BASE_ATTRS]
        inherited = set().union(*[init_attrs.get(base, set()) | KNOWN_BASE_ATTRS.get(base, set()) for base in bases])
        after_super = False
        for stmt in inits[cls.name].body:
            if any(isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "__init__" for sub in ast.walk(stmt)):
                after_super = True
                continue
            if not after_super:
                continue
            for sub, attr in _self_attrs(stmt):
                if attr in inherited:
                    hits.append(("overwrites-inherited-attribute", sub.lineno, lines[sub.lineno - 1].strip()))
                elif len(known) != len(bases):
                    hits.append(("review-assigns-after-super", sub.lineno, f"{lines[sub.lineno - 1].strip()}   <- base(s) {bases} not known"))
    # (7) dead stores, block by block
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if isinstance(block, list) and block and isinstance(block[0], ast.stmt):
                hits.extend(dead_stores(block, lines))
    return sorted(set(hits), key=lambda hit: (hit[1], hit[0]))


def known_answer() -> int:
    got = [(kind, lineno) for kind, lineno, _ in scan_text(FIXTURE)]
    ok = got == FIXTURE_ANSWER
    for kind, lineno in got:
        print(f"fixture:{lineno}: {kind}")
    print(f"known answer: {'PASS' if ok else 'FAIL'} ({len(got)} hits, {len(FIXTURE_ANSWER)} expected: 8 shapes found, 1 review line, 2 near-misses not flagged)")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if args == ["--known-answer"]:
        return known_answer()
    base_dir = None
    if args[:1] == ["--base-dir"]:
        base_dir, args = Path(args[1]), args[2:]
    if not args:
        print(__doc__)
        return 2
    blocking = 0
    for name in args:
        path = Path(name)
        base_lines: set[str] = set()
        if base_dir is not None and (base_dir / path.name).is_file():
            base_lines = {line.strip() for line in (base_dir / path.name).read_text(encoding="utf-8").splitlines()}
        for kind, lineno, line in scan_text(path.read_text(encoding="utf-8")):
            on_base = line in base_lines
            if kind not in NON_BLOCKING and not on_base:
                blocking += 1
            print(f"{name}:{lineno}: {kind}{' (on base)' if on_base else ''}: {line}")
    print(f"{blocking} hit(s) that are neither on base, idiom nor review-only, in {len(args)} file(s)")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
