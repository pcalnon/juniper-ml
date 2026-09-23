"""Scratch scanner (agent-s): find `fixed sleep -> call/await-count lower-bound assertion` in tests.

Usage: python3 scan_sleep_count.py <tests-root>

For every (async) function in every test_*.py / conftest.py under <tests-root>, report each
`asyncio.sleep(<number>)` / `time.sleep(<number>)` / `anyio.sleep(<number>)` call (any
receiver named *sleep with a numeric literal first argument) that is FOLLOWED, in the same
function, by an assertion comparing a `.call_count` / `.await_count` (or len(...call_args_list))
with `>=` or `>` -- the "the loop ticks N times within a fixed window" shape. Also reports, as a
separate class, sleeps followed by `==` comparisons on those counters (exact-count-after-sleep).
"""

import ast
import pathlib
import sys

COUNT_ATTRS = {"call_count", "await_count"}
LIST_ATTRS = {"call_args_list", "await_args_list", "mock_calls"}


WIDE = "--wide" in sys.argv


def _is_counter(node):
    if isinstance(node, ast.Attribute) and node.attr in COUNT_ATTRS:
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len" and node.args:
        arg = node.args[0]
        if isinstance(arg, ast.Attribute) and arg.attr in LIST_ATTRS:
            return True
        if WIDE:
            return True  # any len(...) lower bound
    if WIDE:
        if isinstance(node, ast.Attribute) and "count" in node.attr.lower():
            return True
        if isinstance(node, ast.Name) and "count" in node.id.lower():
            return True
    return False


def _sleep_value(call):
    func = call.func
    name = func.attr if isinstance(func, ast.Attribute) else (func.id if isinstance(func, ast.Name) else None)
    if not name or not name.endswith("sleep"):
        return None
    if not call.args:
        return None
    arg = call.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, (int, float)):
        return float(arg.value)
    if WIDE:
        return float("nan")  # non-literal duration
    return None


def _compare_kinds(test):
    kinds = set()
    for node in ast.walk(test):
        if isinstance(node, ast.Compare):
            operands = [node.left] + list(node.comparators)
            for i, op in enumerate(node.ops):
                left, right = operands[i], operands[i + 1]
                if _is_counter(left) and isinstance(op, (ast.GtE, ast.Gt)):
                    kinds.add("lower-bound")
                elif _is_counter(right) and isinstance(op, (ast.LtE, ast.Lt)):
                    kinds.add("lower-bound")
                elif (_is_counter(left) or _is_counter(right)) and isinstance(op, ast.Eq):
                    kinds.add("exact")
    return kinds


def scan_function(fn):
    sleeps = []
    asserts = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            v = _sleep_value(node)
            if v is not None:
                sleeps.append((node.lineno, v))
        elif isinstance(node, ast.Assert):
            kinds = _compare_kinds(node.test)
            if kinds:
                asserts.append((node.lineno, kinds))
    hits = []
    for a_line, kinds in asserts:
        prior = [(ln, v) for ln, v in sleeps if ln < a_line]
        if prior:
            hits.append((a_line, kinds, prior))
    return hits


def main():
    root = pathlib.Path([a for a in sys.argv[1:] if not a.startswith("--")][0])
    files = sorted(p for p in root.rglob("*.py") if p.name.startswith("test_") or p.name == "conftest.py")
    lower, exact = [], []
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            print(f"SKIP (syntax) {path}: {exc}")
            continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for a_line, kinds, prior in scan_function(fn):
                rec = (str(path.relative_to(root.parent.parent)), fn.name, fn.lineno, a_line, prior)
                if "lower-bound" in kinds:
                    lower.append(rec)
                if "exact" in kinds:
                    exact.append(rec)
    print(f"files scanned: {len(files)}")
    print(f"\nLOWER-BOUND (>= / >) count assertions preceded by a fixed sleep: {len(lower)}")
    for path, fname, fline, aline, prior in lower:
        sl = ", ".join(f"L{ln}:{v:g}s" for ln, v in prior)
        print(f"  {path}:{aline}  {fname} (def L{fline})  sleeps[{sl}]")
    print(f"\nEXACT (==) count assertions preceded by a fixed sleep: {len(exact)}")
    for path, fname, fline, aline, prior in exact:
        sl = ", ".join(f"L{ln}:{v:g}s" for ln, v in prior)
        print(f"  {path}:{aline}  {fname} (def L{fline})  sleeps[{sl}]")


if __name__ == "__main__":
    main()
