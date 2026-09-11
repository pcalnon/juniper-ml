#!/usr/bin/env python3
"""2026-09-11_falsy_guard_triage.py -- triage the `or {}` population the census MEASURED.

Project: juniper-ml
Sub-Project: ad-hoc tooling (instrument repair)
Application: ad-hoc analysis
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

`util/ad-hoc/2026-09-11_falsy_guard_census.py` answers "where are the falsy guards?" and
says so plainly: *a count is not a verdict*. The 2026-09-11 handoff then carried its number
-- "117 live read-class sites across 19 files" -- into the standing-work list as if it were a
work queue. It is not one, for two reasons this tool exists to separate.

  1. THE CENSUS EMITS ONE ROW PER *USE*, NOT PER GUARD. `identity = stats.get('identity')
     or {}` at stats_summary.py:273 is used six times, so it appears six times. Summing rows
     counts the same line repeatedly. The unit of REPAIR is the guard; the unit of the census
     is the use. Both are correct for their own question and they must not be added together.

  2. A GUARD IS ONLY WRONG IF A TRUTHY NON-DICT CAN REACH IT. The defect class needs a value
     that is truthy and not a mapping -- a list, a string, a number. Whether one can arrive is
     a property of WHO WROTE the mapping being read, which the census deliberately does not
     model. An operator hand-writing YAML can type a list where a mapping belongs (this is
     ml#1895's `suite:` incident, exactly). A dict this same process built three lines earlier
     cannot.

WHAT IT ADDS

For every distinct guard it reports a PROVENANCE for the container being read -- the name to
the left of `.get(...)` -- traced back within the file:

  * `operator`  -- the container was parsed from a hand-authored artifact (`yaml.safe_load`,
    `json.load` of a config/suite/experiment file). A truthy non-dict is REACHABLE by typing.
  * `machine`   -- parsed from an artifact this codebase writes (manifest.json, registry.jsonl).
    Reachable only across a version skew, which is real but rarer and self-inflicted.
  * `derived`   -- the container is itself the product of an earlier guard or a literal built
    in this file. A non-dict cannot arrive without the earlier guard failing first.
  * `unknown`   -- provenance not resolvable inside this file (a parameter, an import).

LIMITS -- read these before quoting anything below

  * Provenance is traced WITHIN ONE FILE. A container arriving as a function parameter is
    `unknown`, not safe; this tool does not do interprocedural analysis and will not pretend to.
  * `operator` is a statement about REACHABILITY, not about a defect. It says a bad value can
    be typed, not that anything downstream breaks when it is. Only a failing test shows that,
    which is why the triage output is a CANDIDATE LIST and the fix list is shorter.
  * A `derived` verdict inherits the correctness of the guard it derives from. It is a reason
    to fix the PARENT, never a reason to call the child clean.
  * This tool reads; it writes nothing and gates nothing.

EXIT CODES

  * 0 -- ran and reported.
  * 2 -- no census JSON given, or it could not be read. A triage that examined nothing must
    not print zero and exit clean.

Usage:
    python3 util/ad-hoc/2026-09-11_falsy_guard_census.py --json util/ > /tmp/c.json
    python3 util/ad-hoc/2026-09-11_falsy_guard_triage.py /tmp/c.json
    python3 util/ad-hoc/2026-09-11_falsy_guard_triage.py /tmp/c.json --provenance operator
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Loaders that return whatever the FILE said. The container's shape is the author's choice.
_PARSE_CALLS = {"safe_load", "load", "loads", "full_load", "safe_load_all"}

# An artifact a human edits by hand -> a truthy non-dict is reachable by typing.
_OPERATOR_HINTS = (
    "experiment.yaml", "suite.yaml", "config.yaml", "config.json", "*.yaml", "*.yml",
    "suite", "experiment", "config", "spec", "plan",
)

# Uses that assume the value is a MAPPING. Must stay identical to the census's own set, or
# the blind-spot delta measures a different rule instead of the census's reach.
_DICT_METHODS = {"get", "items", "keys", "values", "setdefault", "pop", "update"}

# An artifact this codebase writes -> reachable only across a version skew.
_MACHINE_HINTS = (
    "manifest.json", "registry.jsonl", "meta.json", "index.jsonl", "baseline.json",
    "stats.json", "HOST.json", "run.json", "metrics.json", "report.json", "aggregate.csv",
)


def _container_of(guard: str) -> str | None:
    """The NAME whose mapping is being read: `stats` in `stats.get('identity') or {}`.

    The census renders the two forms differently and the assignment prefix must come off
    first, or the split form yields the ASSIGNED name (or nothing) instead of the container:

        inline:  (stats.get('identity') or {}).get('git')     -> stats
        split:   identity = stats.get('identity') or {}       -> stats, NOT identity
    """
    expr = guard
    # Strip a leading `name = ` / `name: T = ` assignment prefix (never an `==` comparison).
    m = re.match(r"\s*[A-Za-z_][A-Za-z0-9_]*(?:\s*:\s*[^=]+)?\s*=(?!=)\s*(.+)$", expr, re.S)
    if m:
        expr = m.group(1)
    m = re.match(r"\(?\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\.\s*get\s*\(|\[)", expr)
    return m.group(1) if m else None


class _ProvenanceIndex:
    """Where each name in a file got its value, to the extent one file can say."""

    def __init__(self, path: Path) -> None:
        self.parsed_from: dict[str, str] = {}   # name -> "operator" | "machine"
        self.derived: set[str] = set()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError):
            return

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            value = node.value

            # X = <anything> or <empty literal>  -> X is derived from an earlier guard
            if isinstance(value, ast.BoolOp) and isinstance(value.op, ast.Or):
                self.derived.add(name)
                continue

            # X = yaml.safe_load(...) / json.load(...) -> classify by what is being opened
            call = value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr in _PARSE_CALLS:
                blob = ast.dump(call)
                kind = self._classify(blob)
                if kind:
                    self.parsed_from[name] = kind

    @staticmethod
    def _classify(blob: str) -> str | None:
        low = blob.lower()
        if any(h in low for h in _MACHINE_HINTS):
            return "machine"
        # yaml is overwhelmingly hand-authored in this tree; json is mostly machine-written.
        if "yaml" in low or any(h in low for h in _OPERATOR_HINTS):
            return "operator"
        if "json" in low:
            return "machine"
        return None

    def verdict(self, name: str | None) -> str:
        if name is None:
            return "unknown"
        if name in self.parsed_from:
            return self.parsed_from[name]
        if name in self.derived:
            return "derived"
        return "unknown"


def _scope_bodies(tree: ast.AST):
    """Yield (scope_name, [statements at ANY depth within that scope]).

    A scope owns every statement under it EXCEPT those belonging to a nested function, which
    is its own scope. This is the part the census does not do: it reads only the DIRECT
    children of a scope body, so a guard inside `while:` / `try:` / `if:` is never registered.
    """
    scopes: list[tuple[str, list]] = []

    def walk(node, scope_name: str, sink: list) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                inner: list = []
                walk(child, child.name, inner)
                scopes.append((child.name, inner))
                continue
            if isinstance(child, ast.ClassDef):
                walk(child, scope_name, sink)
                continue
            if isinstance(child, ast.stmt):
                sink.append(child)
            walk(child, scope_name, sink)

    top: list = []
    walk(tree, "<module>", top)
    scopes.append(("<module>", top))
    return scopes


def deep_guard_scan(path: Path) -> list[tuple[int, str]]:
    """Read-class falsy guards at ANY nesting depth, on the CENSUS'S OWN criterion.

    Apples-to-apples matters here. The census reports a guard only when a dict-shaped USE of the
    guarded name follows it in the same scope with no intervening `isinstance`. A scan that
    dropped that requirement would find extra guards and the difference would measure the
    looser rule, not the census's blind spot -- the exact error this whole triage documents.
    So the use-requirement and the isinstance-suppression are both applied below; the ONLY
    difference from the census is that statements are collected at every depth.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return []
    out: list[tuple[int, str]] = []
    for _scope, stmts in _scope_bodies(tree):
        guarded: dict[str, tuple[int, str]] = {}
        typechecked: dict[str, int] = {}
        used: set[str] = set()

        for stmt in stmts:
            for node in ast.walk(stmt):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "isinstance"
                    and node.args
                    and isinstance(node.args[0], ast.Name)
                ):
                    typechecked.setdefault(node.args[0].id, node.lineno)

            if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                value = stmt.value
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                if isinstance(value, ast.BoolOp) and isinstance(value.op, ast.Or) and len(value.values) >= 2:
                    last = value.values[-1]
                    empty = (isinstance(last, ast.Dict) and not last.keys) or (
                        isinstance(last, ast.Call)
                        and isinstance(last.func, ast.Name)
                        and last.func.id == "dict"
                        and not last.args
                    )
                    head = value.values[0]
                    is_read = (
                        isinstance(head, ast.Call)
                        and isinstance(head.func, ast.Attribute)
                        and head.func.attr in _DICT_METHODS
                    ) or isinstance(head, ast.Subscript)
                    if empty and is_read:
                        for t in targets:
                            if isinstance(t, ast.Name):
                                guarded[t.id] = (stmt.lineno, ast.unparse(stmt)[:110])

            # A dict-shaped use of a guarded name, strictly after its assignment.
            for node in ast.walk(stmt):
                name = None
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in _DICT_METHODS
                    and isinstance(node.func.value, ast.Name)
                ):
                    name = node.func.value.id
                elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
                    name = node.value.id
                if name is None or name not in guarded:
                    continue
                if node.lineno <= guarded[name][0]:
                    continue
                if name in typechecked and typechecked[name] <= node.lineno:
                    continue
                used.add(name)

        out.extend(guarded[n] for n in used)
    return sorted(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("census_json", help="output of 2026-09-11_falsy_guard_census.py --json")
    ap.add_argument("--provenance", help="show only this provenance class")
    ap.add_argument("--include-adhoc", action="store_true", help="include util/ad-hoc/ one-shots")
    ap.add_argument("--blind-spot", action="store_true", help="report split-form guards the census cannot reach")
    args = ap.parse_args(argv)

    try:
        rows = json.loads(Path(args.census_json).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read census JSON: {exc}", file=sys.stderr)
        return 2
    if not rows:
        print("census JSON is empty -- refusing to report a clean triage", file=sys.stderr)
        return 2

    live = [
        r for r in rows
        if r.get("risk") == "read"
        and (args.include_adhoc or not r["file"].startswith("util/ad-hoc/"))
    ]

    # Collapse uses -> guards. THIS is the unit of repair.
    guards: dict[tuple, dict] = {}
    uses: Counter = Counter()
    for r in live:
        key = (r["file"], r["guard_line"], r["guard"])
        uses[key] += 1
        guards.setdefault(key, r)

    index_cache: dict[str, _ProvenanceIndex] = {}
    by_prov: dict[str, list] = defaultdict(list)
    for key, row in guards.items():
        path = row["file"]
        idx = index_cache.setdefault(path, _ProvenanceIndex(Path(path)))
        container = _container_of(row["guard"])
        by_prov[idx.verdict(container)].append((key, row, container, uses[key]))

    print(f"census rows (one per USE):      {len(live)}")
    print(f"distinct guards (unit of REPAIR): {len(guards)}   across {len({k[0] for k in guards})} file(s)")
    print()

    if args.blind_spot:
        seen = {(k[0], k[1]) for k in guards}
        missed: list[tuple[str, int, str]] = []
        for fpath in sorted({k[0] for k in guards} | {r["file"] for r in live}):
            for line, rendering in deep_guard_scan(Path(fpath)):
                if (fpath, line) not in seen:
                    missed.append((fpath, line, rendering))
        print("=== BLIND SPOT: split-form guards nested inside a control-flow block ===")
        print("The census reads only the DIRECT children of a scope body, so a guard inside")
        print("`while:` / `try:` / `if:` / `for:` is never registered. These are read-class")
        print("guards present in the same files and absent from the census:")
        print()
        for fpath, line, rendering in missed:
            print(f"  {fpath}:{line}")
            print(f"      {rendering}")
        print()
        print(f"  census distinct guards: {len(guards)}")
        print(f"  additionally found:     {len(missed)}")
        print(f"  floor, not a total:     {len(guards) + len(missed)}")
        print()
        return 0
    order = ["operator", "machine", "unknown", "derived"]
    print("by provenance of the CONTAINER being read:")
    for p in order:
        print(f"  {p:<9} {len(by_prov[p]):>4} guard(s)")
    print()

    show = [args.provenance] if args.provenance else order
    for p in show:
        items = by_prov.get(p) or []
        if not items:
            continue
        print(f"=== {p} ({len(items)} guard(s)) ===")
        for (fpath, line, guard), _row, container, n in sorted(items, key=lambda t: (t[0][0], t[0][1])):
            print(f"  {fpath}:{line}  [{n} use(s)]  container={container}")
            print(f"      {guard[:110]}")
        print()

    print("A provenance is not a verdict. `operator` means a truthy non-dict is REACHABLE by")
    print("typing, not that anything breaks when it arrives -- only a failing test shows that.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
