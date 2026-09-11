#!/usr/bin/env python3
"""2026-09-11_falsy_guard_census.py -- `or {}` is a FALSY guard, and this finds where that matters.

Project: juniper-ml
Sub-Project: ad-hoc tooling (instrument repair)
Application: ad-hoc analysis
Author: Paul Calnon
License: MIT License

THE DEFECT CLASS

`x = blob.get("k") or {}` fixes `None` and `{}` and does nothing about a value that is
TRUTHY AND NOT A DICT -- a list, a string, a number -- which then raises `AttributeError`
on the next `.get`. ml#1781 fixed four such sites in `util/experiments/read_run_metrics.py`.

WHY THIS REPLACES `2026-09-06_untyped_json_read_census.py`

The 2026-09-09 handoff carried "28 unguarded chains remain across 7 files" from that census
while also recording that it is blind to the split-across-lines form and returns nothing on a
sibling repo. A number from an instrument with known blind spots is not a measurement, so the
instrument is rebuilt here rather than re-run. Three defects, all confirmed in its source
before this was written:

  1. SINGLE-EXPRESSION ONLY. `chains()` matches `(X.get(..) or {}).get(..)` -- one AST Call
     whose inner is a Call. The common form is two statements:

         cfg = blob.get("runtime") or {}      # <- the falsy guard
         ...
         width = cfg.get("threads")            # <- the unguarded use

     No node in that pair has a `.get` inside a `.get`, so the census sees nothing. This is
     the form the handoff names as live at `util/experiments/stats_summary.py:273-279`.

  2. A HARD-CODED ARTIFACT ROSTER GATES THE WHOLE FILE. `UNTRUSTED` lists ten juniper-ml
     filenames and `if not artifacts: continue` SKIPS the file entirely -- uncounted. Pointed
     at a sibling repo it reports zero, which is indistinguishable from clean. Here the
     roster only RANKS; nothing is skipped for failing it, and the split is reported.

  3. `isinstance` ANYWHERE IN THE FUNCTION COUNTS AS A GUARD. One unrelated `isinstance` in a
     200-line function suppressed every chain in it. Here a guard must mention the NAME that
     carries the falsy-guarded value.

WHAT IT REPORTS, AND WHAT IT DOES NOT

A site is `X = <expr> or <empty literal>` followed, in the same scope, by a DICT-SHAPED USE of
`X` (`.get`, `[...]`, `.items()`, `.keys()`, `.values()`, `**X`) with no `isinstance(X, ...)`
between them. Also the single-expression form the old census found, so nothing regresses.

It RANKS by whether the file reads an operator-written artifact; it does not rank by severity
and it is not a gate. A site whose `<expr>` provably yields a dict is a false positive and is
expected -- the census cannot know the type, which is the entire reason the pattern is a
problem in the first place.

EXIT CODES

  * 0 -- ran and reported (a count is not a verdict, so findings are not an error);
  * 2 -- no paths given, or a path could not be walked. A census that examined nothing must
    not print zero and exit clean.

Usage:
    python3 util/ad-hoc/2026-09-11_falsy_guard_census.py util/
    python3 util/ad-hoc/2026-09-11_falsy_guard_census.py --json ../juniper-cascor/src
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

# Artifacts written by a driver, an operator, or an older version of this code. These RANK a
# finding; they never gate one. Extend freely -- an unlisted artifact costs a rank, not a miss.
UNTRUSTED = (
    "manifest.json", "experiment.yaml", "registry.jsonl", "meta.json", "index.jsonl",
    "baseline.json", "HOST.json", "stats.json", "aggregate.csv", "summary.md",
    "config.yaml", "config.json", "suite.yaml", "run.json", "metrics.json", "report.json",
)

# Uses that assume the value is a MAPPING.
_DICT_METHODS = {"get", "items", "keys", "values", "setdefault", "pop", "update"}


def risk(expr: ast.AST) -> str:
    """How likely is the left operand of `or` to be a TRUTHY NON-DICT?

    The census cannot know a type, but it can tell three provenances apart, and they differ
    enormously in whether the falsy guard is hiding anything:

      * `read`  -- `X = blob.get("k") or {}` / `X = blob["k"] or {}`. The value came out of a
        mapping whose shape the reader did not choose. This is the ml#1781 shape and the only
        one where `or {}` is routinely load-bearing AND routinely wrong.
      * `call`  -- `X = f(...) or {}`. Depends entirely on `f`; worth a look, rarely a defect.
      * `local` -- `X = name or {}` / `X = self.attr or {}`. Overwhelmingly the
        default-parameter idiom (`opts = opts or {}`), where the author controls the type and
        the guard is exactly right.

    Reporting 396 flat sites would repeat the error this tool was built to correct -- a number
    that does not distinguish what it counted.
    """
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) and expr.func.attr in _DICT_METHODS:
        return "read"
    if isinstance(expr, ast.Subscript):
        return "read"
    if isinstance(expr, ast.Call):
        return "call"
    return "local"


def _is_empty_literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Dict) and not node.keys:
        return "{}"
    if isinstance(node, ast.List) and not node.elts:
        return "[]"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"dict", "list"} and not node.args:
        return f"{node.func.id}()"
    return None


class _ScopeVisitor(ast.NodeVisitor):
    """Collect, per scope, the falsy-guarded assignments and the later uses of those names."""

    def __init__(self) -> None:
        self.findings: list[dict] = []

    def _scan_scope(self, body: list, scope_name: str) -> None:
        # name -> (lineno, literal, rendering)
        guarded: dict = {}
        # name -> lineno of an isinstance() mentioning it
        typechecked: dict = {}

        for stmt in body:
            for node in ast.walk(stmt):
                # isinstance(NAME, ...) anywhere re-types that NAME from here on.
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "isinstance"
                    and node.args
                    and isinstance(node.args[0], ast.Name)
                ):
                    typechecked.setdefault(node.args[0].id, node.lineno)

            # `X = <expr> or <empty literal>`
            if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                value = stmt.value
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                if (
                    isinstance(value, ast.BoolOp)
                    and isinstance(value.op, ast.Or)
                    and len(value.values) >= 2
                ):
                    lit = _is_empty_literal(value.values[-1])
                    if lit:
                        lhs_risk = risk(value.values[0])
                        for t in targets:
                            if isinstance(t, ast.Name):
                                guarded[t.id] = (stmt.lineno, lit, ast.unparse(stmt)[:110], lhs_risk)

            # A dict-shaped USE of a guarded name, after its assignment.
            for node in ast.walk(stmt):
                name = None
                kind = None
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in _DICT_METHODS
                    and isinstance(node.func.value, ast.Name)
                ):
                    name, kind = node.func.value.id, f".{node.func.attr}()"
                elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
                    name, kind = node.value.id, "[...]"
                if name is None or name not in guarded:
                    continue
                assign_line, lit, rendering, lhs_risk = guarded[name]
                if node.lineno <= assign_line:
                    continue
                if name in typechecked and typechecked[name] <= node.lineno:
                    continue  # a real type guard reached it
                self.findings.append(
                    {
                        "scope": scope_name,
                        "name": name,
                        "guard_line": assign_line,
                        "guard": rendering,
                        "literal": lit,
                        "use_line": node.lineno,
                        "use": f"{name}{kind}",
                        "form": "split",
                        "risk": lhs_risk,
                    }
                )

    def visit_Module(self, node: ast.Module) -> None:  # noqa: N802
        self._scan_scope(node.body, "<module>")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._scan_scope(node.body, node.name)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]


def _inline_chains(tree: ast.Module) -> list[dict]:
    """The single-expression form the OLD census found -- kept so nothing regresses."""
    out: list[dict] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr not in _DICT_METHODS:
            continue
        inner = node.func.value
        if isinstance(inner, ast.BoolOp) and isinstance(inner.op, ast.Or):
            if _is_empty_literal(inner.values[-1]):
                out.append(
                    {
                        "scope": "-",
                        "name": "-",
                        "guard_line": node.lineno,
                        "guard": ast.unparse(node)[:110],
                        "literal": _is_empty_literal(inner.values[-1]),
                        "use_line": node.lineno,
                        "use": f"(... or {{}}).{node.func.attr}()",
                        "form": "inline",
                        "risk": risk(inner.values[0]),
                    }
                )
    return out


def scan(path: Path) -> tuple:
    src = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src)
    v = _ScopeVisitor()
    v.visit(tree)
    findings = v.findings + _inline_chains(tree)
    artifacts = sorted({a for a in UNTRUSTED if a in src})
    return findings, artifacts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", help="directories or files to scan")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    if not args.paths:
        print("no paths given -- refusing to report", file=sys.stderr)
        return 2

    files: list = []
    for p in args.paths:
        root = Path(p)
        if root.is_file() and root.suffix == ".py":
            files.append(root)
        elif root.is_dir():
            files += sorted(root.rglob("*.py"))
        else:
            print(f"not a python path: {p}", file=sys.stderr)
            return 2
    if not files:
        print("zero python files found -- refusing to report success", file=sys.stderr)
        return 2

    rows: list = []
    unparsed: list = []
    for f in files:
        try:
            findings, artifacts = scan(f)
        except (SyntaxError, OSError) as exc:
            unparsed.append(f"{f}: {exc}")
            continue
        for fd in findings:
            fd["file"] = str(f)
            fd["reads_untrusted"] = artifacts
            rows.append(fd)

    if args.as_json:
        print(json.dumps(rows, indent=2))
    else:
        by_file: dict = {}
        for r in rows:
            by_file.setdefault(r["file"], []).append(r)
        # Files reading operator-written artifacts first -- that is the rank, not a filter.
        ordered = sorted(
            by_file.items(),
            key=lambda kv: (not kv[1][0]["reads_untrusted"], -len(kv[1]), kv[0]),
        )
        for fname, fr in ordered:
            reads = [r for r in fr if r["risk"] == "read"]
            if not reads:
                continue  # printed in the tail summary; the `read` class is what needs eyes
            tag = f"  [reads {', '.join(fr[0]['reads_untrusted'])}]" if fr[0]["reads_untrusted"] else ""
            print(f"=== {fname} === {len(reads)} read-class site(s) of {len(fr)}{tag}")
            for r in sorted(reads, key=lambda x: x["use_line"]):
                if r["form"] == "inline":
                    print(f"    :{r['use_line']:<5} inline  {r['guard']}")
                else:
                    print(f"    :{r['guard_line']:<5} -> :{r['use_line']:<5} {r['scope']}()  "
                          f"{r['name']} = ... or {r['literal']}   then {r['use']}")
        split = sum(1 for r in rows if r["form"] == "split")
        inline = len(rows) - split
        by_risk = {k: sum(1 for r in rows if r["risk"] == k) for k in ("read", "call", "local")}
        read_files = len({r["file"] for r in rows if r["risk"] == "read"})
        print(f"\n{len(rows)} site(s) across {len(by_file)} file(s) "
              f"-- {split} split-across-statements, {inline} single-expression")
        print(f"by provenance of the guarded value: read={by_risk['read']} "
              f"(across {read_files} files), call={by_risk['call']}, local={by_risk['local']}")
        print(f"examined {len(files)} python file(s); {len(unparsed)} unparsed")
        print("Only the `read` class is listed above. `local` is the `opts = opts or {}` "
              "default-parameter idiom, where the author owns the type and the guard is right.")
        print("A count is not a verdict: a site whose expression provably yields a dict is a "
              "false positive, and this census cannot know the type.")

    if unparsed:
        print(f"\ncould not parse {len(unparsed)} file(s):", file=sys.stderr)
        for u in unparsed[:10]:
            print(f"    {u}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
