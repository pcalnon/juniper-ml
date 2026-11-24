#!/usr/bin/env python3
"""
Validator check A for juniper-data's "run the unrun tests" carrier: prove from the syntax trees that no test body
changed, and say exactly what did.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 7: validating the d2-unrun-tests carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session7/briefs/VF_validate_data_unrun_tests.txt (check A)

Usage:
  2026-11-12_flood4r2_val_d2-data_ast_compare.py --repo <juniper-data checkout> --rev <sha> --tree <tree with the
      carrier laid over> --out <file.json> --pair <path at rev>=<path in tree> [--pair ...]

For each pair the module at ``<rev>:<old path>`` (read with ``git cat-file``) is compared with ``<tree>/<new path>``:

- every function, method and class is matched by its qualified name; a name on one side only is reported;
- for each function: the dump of its arguments, of its body (docstring included) and of each decorator;
- for each class: its bases, its keywords, each decorator, its docstring and its non-function statements;
- the module's own statements (imports, assignments, the docstring), as a multiset difference;
- the comment tokens of both sides, as a multiset difference (comments are not in the syntax tree).

Exit 0 when no function's arguments or body differ and no function or class exists on one side only; 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import subprocess
import sys
import tokenize
from collections import Counter
from pathlib import Path


def dump(node: ast.AST) -> str:
    return ast.dump(node, include_attributes=False)


def source_of(node: ast.AST) -> str:
    return ast.unparse(node)


def describe(tree: ast.Module) -> dict:
    functions: dict[str, dict] = {}
    classes: dict[str, dict] = {}
    module_statements: list[str] = []

    def visit_function(node: ast.FunctionDef | ast.AsyncFunctionDef, prefix: str) -> None:
        name = prefix + node.name
        if name in functions:
            name = f"{name}#{node.lineno}"
        functions[name] = {"kind": type(node).__name__, "args": dump(node.args), "returns": dump(node.returns) if node.returns else None, "body": [dump(statement) for statement in node.body], "decorators": [source_of(item) for item in node.decorator_list]}
        for inner in node.body:
            visit(inner, name + ".<locals>.")

    def visit_class(node: ast.ClassDef, prefix: str) -> None:
        name = prefix + node.name
        own = [source_of(statement) for statement in node.body if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        classes[name] = {"bases": [source_of(item) for item in node.bases], "keywords": [source_of(item.value) for item in node.keywords], "decorators": [source_of(item) for item in node.decorator_list], "docstring": ast.get_docstring(node, clean=False), "own_statements": own}
        for inner in node.body:
            visit(inner, name + ".")

    def visit(node: ast.AST, prefix: str) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visit_function(node, prefix)
        elif isinstance(node, ast.ClassDef):
            visit_class(node, prefix)

    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            visit(statement, "")
        else:
            module_statements.append(source_of(statement))
    return {"functions": functions, "classes": classes, "module_statements": module_statements}


def comments_of(text: str) -> list[str]:
    return [token.string for token in tokenize.generate_tokens(io.StringIO(text).readline) if token.type == tokenize.COMMENT]


def multiset_difference(old: list[str], new: list[str]) -> dict:
    before, after = Counter(old), Counter(new)
    return {"removed": sorted((before - after).elements()), "added": sorted((after - before).elements())}


def compare(old_text: str, new_text: str) -> dict:
    old, new = describe(ast.parse(old_text)), describe(ast.parse(new_text))
    report: dict = {"functions": {"old": len(old["functions"]), "new": len(new["functions"])}, "classes": {"old": len(old["classes"]), "new": len(new["classes"])}}
    report["functions_only_old"] = sorted(set(old["functions"]) - set(new["functions"]))
    report["functions_only_new"] = sorted(set(new["functions"]) - set(old["functions"]))
    report["classes_only_old"] = sorted(set(old["classes"]) - set(new["classes"]))
    report["classes_only_new"] = sorted(set(new["classes"]) - set(old["classes"]))
    body_changes, signature_changes, decorator_changes = [], [], []
    for name in sorted(set(old["functions"]) & set(new["functions"])):
        left, right = old["functions"][name], new["functions"][name]
        if left["body"] != right["body"]:
            body_changes.append(name)
        if (left["kind"], left["args"], left["returns"]) != (right["kind"], right["args"], right["returns"]):
            signature_changes.append(name)
        if left["decorators"] != right["decorators"]:
            decorator_changes.append({"function": name, **multiset_difference(left["decorators"], right["decorators"])})
    class_changes = []
    for name in sorted(set(old["classes"]) & set(new["classes"])):
        left, right = old["classes"][name], new["classes"][name]
        entry: dict = {}
        if left["decorators"] != right["decorators"]:
            entry["decorators"] = multiset_difference(left["decorators"], right["decorators"])
        if (left["bases"], left["keywords"]) != (right["bases"], right["keywords"]):
            entry["bases"] = {"old": left["bases"] + left["keywords"], "new": right["bases"] + right["keywords"]}
        if left["docstring"] != right["docstring"]:
            entry["docstring"] = {"old": left["docstring"], "new": right["docstring"]}
        own_old = [s for s in left["own_statements"] if not (left["docstring"] is not None and s == left["own_statements"][0])]
        own_new = [s for s in right["own_statements"] if not (right["docstring"] is not None and s == right["own_statements"][0])]
        if own_old != own_new:
            entry["own_statements"] = multiset_difference(own_old, own_new)
        if entry:
            class_changes.append({"class": name, **entry})
    report["function_bodies_changed"] = body_changes
    report["function_signatures_changed"] = signature_changes
    report["function_decorators_changed"] = decorator_changes
    report["classes_changed"] = class_changes
    report["module_statements"] = multiset_difference(old["module_statements"], new["module_statements"])
    report["comments"] = multiset_difference(comments_of(old_text), comments_of(new_text))
    old_lines, new_lines = old_text.splitlines(), new_text.splitlines()
    report["lines"] = {"old": len(old_lines), "new": len(new_lines), "delta": len(new_lines) - len(old_lines)}
    report["ok"] = not (body_changes or signature_changes or report["functions_only_old"] or report["functions_only_new"] or report["classes_only_old"] or report["classes_only_new"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--rev", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--pair", action="append", required=True)
    ns = parser.parse_args()
    result = {"rev": ns.rev, "tree": ns.tree, "pairs": {}}
    status = 0
    for pair in ns.pair:
        old_path, new_path = pair.split("=", 1)
        shown = subprocess.run(["git", "-C", ns.repo, "cat-file", "-p", f"{ns.rev}:{old_path}"], capture_output=True, check=True)
        report = compare(shown.stdout.decode("utf-8"), (Path(ns.tree) / new_path).read_text(encoding="utf-8"))
        result["pairs"][pair] = report
        if not report["ok"]:
            status = 1
        print(f"== {old_path}" + ("" if old_path == new_path else f" -> {new_path}"))
        print(f"   functions {report['functions']['old']} -> {report['functions']['new']}; classes {report['classes']['old']} -> {report['classes']['new']}; lines {report['lines']['old']} -> {report['lines']['new']} ({report['lines']['delta']:+d}); bodies changed {len(report['function_bodies_changed'])}; signatures changed {len(report['function_signatures_changed'])}; ok={report['ok']}")
        for item in report["function_decorators_changed"]:
            print(f"   function decorators: {item}")
        for item in report["classes_changed"]:
            print(f"   class: {json.dumps(item, ensure_ascii=False)}")
        print(f"   module statements removed: {report['module_statements']['removed']}")
        print(f"   module statements added:   {report['module_statements']['added']}")
        print(f"   comments removed: {report['comments']['removed']}")
        print(f"   comments added:   {report['comments']['added']}")
        for key in ("functions_only_old", "functions_only_new", "classes_only_old", "classes_only_new", "function_bodies_changed", "function_signatures_changed"):
            if report[key]:
                print(f"   {key}: {report[key]}")
    Path(ns.out).write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return status


if __name__ == "__main__":
    sys.exit(main())
