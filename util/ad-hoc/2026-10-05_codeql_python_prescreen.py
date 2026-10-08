#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-05
# Status      : ad-hoc — one-off; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Predict the CodeQL Python alerts that block a juniper-ml PR, before the PR is opened.

An unresolved CodeQL review thread blocks a merge while every check reads green (memory
``reference_codeql_unused_global_cascor``), and pyflakes-clean is not CodeQL-clean: juniper-ml#2157 drew 20
threads on archived lane probes (19 ``py/file-not-always-closed``, 1 ``py/unused-import``), and ml#2176 drew 12
on tuple unpacking pyflakes never flags. This screen approximates the rules those PRs hit, from the AST:

- ``open-not-closed``: an ``open(...)`` call that is not the context expression of a ``with`` item;
- ``unused-import``: an imported name never read in the module (``__all__`` and ``__future__`` honoured);
- ``import-and-import-from``: one standard-library module imported both with ``import m`` and ``from m import …``;
- ``unused-local``: a name bound in a function (plain or tuple target) and never read in it;
- ``unused-global``: a module-level lower-case name bound by assignment (plain or tuple) and never read anywhere;
- ``empty-except``: an ``except`` body that is only ``pass`` with no comment on its lines;
- ``no-effect``: an expression statement that is not a call, an ``await``, a ``yield`` or a docstring;
- ``catch-base-exception``: a bare ``except:``;
- ``multiple-definition``: a name assigned again in the same block, in straight-line code, before it is read.

It is a predictor, not CodeQL: it can miss alerts (CodeQL's flow analysis is wider) and over-report (an
underscore-prefixed name is skipped, as CodeQL does; ``del`` and ``global`` are counted as reads). Read its
output as the list to look at, then fix the code, never suppress it.

``--known-answer`` checks the screen against juniper-ml#2157's 20 threads: it rebuilds the ten Phase 10 probes
as they were before ``2026-10-05_phase10_r1_probes_close_files.py`` fixed them (that script's edits, reversed),
and requires every one of the 20 alerts, by file and rule, and none of them on the fixed files.

Usage:
    python3 util/ad-hoc/2026-10-05_codeql_python_prescreen.py FILE [FILE ...]
    python3 util/ad-hoc/2026-10-05_codeql_python_prescreen.py --known-answer
Exit 1 when anything is reported (or the known answer fails).
"""

import ast
import importlib.util
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ADHOC = Path(__file__).resolve().parent
#: juniper-ml#2157's CodeQL threads, by probe suffix: (open-not-closed count, unused-import count)
PR2157 = {
    "b2_probe_toast.py": (1, 0),
    "b2_probe_relay.py": (4, 0),
    "b2_inspect_hist2.py": (1, 0),
    "b2_inspect_hist.py": (1, 0),
    "b2_check_lines.py": (1, 0),
    "a2_my_f060_stage_b.py": (1, 0),
    "a2_my_f060_stage_a.py": (1, 0),
    "a2_mutate.py": (2, 0),
    "a2_c3_captures.py": (3, 0),
    "a2_c1_timeline.py": (4, 1),
}


def _names_in_target(t):
    if isinstance(t, ast.Name):
        yield t
    elif isinstance(t, (ast.Tuple, ast.List)):
        for e in t.elts:
            yield from _names_in_target(e)
    elif isinstance(t, ast.Starred):
        yield from _names_in_target(t.value)


class _Scope:
    def __init__(self, node):
        self.node = node
        self.bound = {}  # name -> first binding node (assignment targets only)
        self.read = set()


def _scan(path: Path):
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    tree = ast.parse(src, filename=str(path))
    out = []

    # parents, and the set of open() calls that are a with-item's context expression
    with_ctx = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                with_ctx.add(id(item.context_expr))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open" and id(node) not in with_ctx:
            out.append((node.lineno, "open-not-closed", "open() outside a with statement"))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("open",) and isinstance(node.func.value, ast.Name) and node.func.value.id in ("io", "gzip", "bz2", "lzma") and id(node) not in with_ctx:
            out.append((node.lineno, "open-not-closed", f"{node.func.value.id}.open() outside a with statement"))

    # every Name read anywhere, and attribute roots
    all_reads = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Load, ast.Del)):
            all_reads.add(node.id)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            all_reads.update(node.names)
    dunder_all = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            if isinstance(node.value, (ast.List, ast.Tuple)):
                dunder_all.update(e.value for e in node.value.elts if isinstance(e, ast.Constant))
    # string-mentioned names (e.g. getattr by name, f-strings use Name nodes already)

    # imports
    plain, frm = defaultdict(list), defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                bound = a.asname or a.name.split(".")[0]
                plain[a.name].append(node.lineno)
                if bound not in all_reads and bound not in dunder_all:
                    out.append((node.lineno, "unused-import", f"import {a.name}" + (f" as {a.asname}" if a.asname else "")))
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            frm[node.module or ""].append(node.lineno)
            for a in node.names:
                bound = a.asname or a.name
                if a.name == "*":
                    continue
                if bound not in all_reads and bound not in dunder_all:
                    out.append((node.lineno, "unused-import", f"from {node.module} import {a.name}"))
    for mod in set(plain) & set(frm):
        # stdlib only: on #2157 CodeQL did not flag a cascor module imported both ways, which it cannot resolve
        if mod.split(".")[0] in sys.stdlib_module_names:
            out.append((min(plain[mod] + frm[mod]), "import-and-import-from", f"{mod} imported both ways"))

    # unused locals per function, unused module-level assignment targets
    def fn_scope(fn):
        bound, reads = {}, set()
        params = {a.arg for a in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs}
        if fn.args.vararg:
            params.add(fn.args.vararg.arg)
        if fn.args.kwarg:
            params.add(fn.args.kwarg.arg)
        nonlocal_or_global = set()
        for node in ast.walk(fn):
            if isinstance(node, (ast.Global, ast.Nonlocal)):
                nonlocal_or_global.update(node.names)
        for node in ast.walk(fn):
            if node is not fn and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                # names read in nested scopes count as reads of the enclosing one (closures)
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                        reads.add(sub.id)
                continue
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for t in targets:
                    for nm in _names_in_target(t):
                        bound.setdefault(nm.id, nm.lineno)
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
                pass  # loop targets: CodeQL reports these separately and rarely; skipped
            elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Load, ast.Del)):
                reads.add(node.id)
            elif isinstance(node, ast.AugAssign):
                pass
        for node in ast.walk(fn):
            if isinstance(node, ast.AugAssign):
                for nm in _names_in_target(node.target):
                    reads.add(nm.id)
        for name, ln in bound.items():
            if name.startswith("_") or name in params or name in nonlocal_or_global or name in reads:
                continue
            out.append((ln, "unused-local", f"{name} bound in {fn.name}() and never read"))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_scope(node)

    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        for t in targets:
            for nm in _names_in_target(t):
                if nm.id.startswith("_") or nm.id in all_reads or nm.id in dunder_all or nm.id.isupper():
                    continue
                out.append((nm.lineno, "unused-global", f"module-level {nm.id} never read"))
    # an UPPER-case module constant never read is not reported: CodeQL did not flag one on #2157

    # empty except without a comment
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            seg = lines[node.lineno - 1 : node.body[0].end_lineno]
            if not any("#" in s for s in seg):
                out.append((node.lineno, "empty-except", "except: pass with no comment"))

    # statements with no effect
    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr):
            continue
        v = node.value
        if isinstance(v, (ast.Call, ast.Await, ast.Yield, ast.YieldFrom)):
            continue
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            continue  # docstrings and string statements
        if isinstance(v, ast.Constant) and v.value is Ellipsis:
            continue
        out.append((node.lineno, "no-effect", ast.unparse(v)[:60]))

    # a bare `except:` (py/catch-base-exception)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            out.append((node.lineno, "catch-base-exception", "bare except:"))

    # straight-line redefinition before any read, within one block (py/multiple-definition, simplified:
    # only a plain assignment at the same level counts as the redefinition; any read anywhere in a
    # statement, nested scopes included, clears the pending value)
    def _loads(stmt):
        return {n.id for n in ast.walk(stmt) if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Load, ast.Del))} | {nm for n in ast.walk(stmt) if isinstance(n, (ast.Global, ast.Nonlocal)) for nm in n.names}

    def _block(stmts):
        pending = {}
        for st in stmts:
            if isinstance(st, ast.Assign):
                reads = _loads(st.value)
                for name in list(pending):
                    if name in reads:
                        del pending[name]
                for t in st.targets:
                    for nm in _names_in_target(t):
                        if nm.id in pending and not nm.id.startswith("_"):
                            out.append((pending[nm.id], "multiple-definition", f"{nm.id} redefined at line {nm.lineno} before it is read"))
                        pending[nm.id] = nm.lineno
                    if not isinstance(t, (ast.Name, ast.Tuple, ast.List)):
                        for name in list(pending):
                            if name in _loads(t):
                                del pending[name]
            else:
                reads = _loads(st)
                for name in list(pending):
                    if name in reads:
                        del pending[name]
                if isinstance(st, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Return, ast.Raise, ast.Break, ast.Continue)):
                    pending.clear()  # control flow: stop the straight-line reading here
        for st in stmts:
            for field in ("body", "orelse", "finalbody"):
                sub = getattr(st, field, None)
                if isinstance(sub, list) and sub and isinstance(sub[0], ast.stmt):
                    _block(sub)
            for h in getattr(st, "handlers", []) or []:
                _block(h.body)

    _block(tree.body)
    return sorted(set(out))


def known_answer() -> int:
    spec = importlib.util.spec_from_file_location("close_files", ADHOC / "2026-10-05_phase10_r1_probes_close_files.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        for suffix, (want_open, want_imp) in PR2157.items():
            fixed = (ADHOC / f"{mod.PREFIX}{suffix}").read_text(encoding="utf-8")
            before = fixed
            for old, new in mod.EDITS[suffix]:
                if before.count(new) != 1:
                    print(f"KNOWN-ANSWER: {suffix}: a fixed form is not there exactly once")
                    return 1
                before = before.replace(new, old)
            got = {}
            for label, text in (("before", before), ("fixed", fixed)):
                p = Path(td) / f"{label}_{suffix}"
                p.write_text(text, encoding="utf-8")
                got[label] = Counter(rule for _ln, rule, _m in _scan(p))
            ok = got["before"]["open-not-closed"] == want_open and got["before"]["unused-import"] == want_imp and got["fixed"]["open-not-closed"] == 0 and got["fixed"]["unused-import"] == 0
            bad += not ok
            print(f"{'ok  ' if ok else 'FAIL'} {suffix}: before open={got['before']['open-not-closed']}/{want_open} import={got['before']['unused-import']}/{want_imp}; fixed open={got['fixed']['open-not-closed']} import={got['fixed']['unused-import']}; other rules before/fixed: {sum(v for k, v in got['before'].items() if k not in ('open-not-closed', 'unused-import'))}/{sum(v for k, v in got['fixed'].items() if k not in ('open-not-closed', 'unused-import'))}")
    print("KNOWN-ANSWER " + ("PASS" if not bad else f"FAIL ({bad} file(s))"))
    return 1 if bad else 0


def main(argv) -> int:
    if not argv:
        print(__doc__)
        return 2
    if argv == ["--known-answer"]:
        return known_answer()
    total = 0
    for p in argv:
        path = Path(p)
        try:
            found = _scan(path)
        except SyntaxError as exc:
            print(f"{p}: SYNTAX ERROR {exc}")
            total += 1
            continue
        for ln, rule, msg in found:
            print(f"{p}:{ln}: {rule}: {msg}")
        total += len(found)
    print(f"{total} predicted alert(s) in {len(argv)} file(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
