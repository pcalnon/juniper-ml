#!/usr/bin/env python3
"""
Run the static screens on the carrier: the CodeQL prescreen, the seven merge-blocking shapes, G-PATH and G-TMP.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3: screens before the PR is opened)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-05_codeql_python_prescreen.py; util/home_path_literal_check.py (gate G-PATH);
         util/ad-hoc/2026-11-08_flood4r2_ml_code_implicit_concat_check.py; the session-4 and session-5 brief addenda
         (seven CodeQL shapes the prescreen did not model when they were written, each of which opened a review
         thread that blocked a merge: a constant conditional, an unused module-level global, a module imported both
         ways, a bare ``await name``, a variable defined twice before it is read, an attribute a subclass
         ``__init__`` overwrites after ``super().__init__()``, and ``except BaseException`` or a bare ``except``).

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_screens.py <out.log>

The files are the Python files the worktree changes against HEAD (``git status``; added and modified). Each
tool runs as its own process on that list and its output goes to <out.log>. Gate G-TMP (the system temp-dir
literal check that juniper-ml#2360 added) is given every changed file, of any type. The shape screen below reads the
ADDED lines of each file (the whole file when it is new): a hit on a line HEAD already has is not this change's.
It reports, never fixes. Exit 0 when every tool exits 0 and the shape screen finds nothing.
"""
import ast
import re
import subprocess  # nosec B404 -- fixed argv: git and this repository's own screens
import sys
from pathlib import Path

CONSTANT_TEST = re.compile(r"^\s*(?:if|elif)\s+(?:True|False|None|[0-9]+)\s*:")
BARE_AWAIT = re.compile(r"^\s+await [A-Za-z_][A-Za-z_0-9]*\s*$")
BASE_EXCEPTION = re.compile(r"^\s*except\s*(?:BaseException\b.*)?:")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout  # nosec B603 B607


def changed_python() -> dict:
    """{path: the set of 1-based line numbers this change adds, or None when the whole file is new}."""
    files = {}
    for line in git("status", "--porcelain", "--untracked-files=all").splitlines():
        code, rel = line[:2], line[3:]
        if not rel.endswith(".py"):
            continue
        if code == "??":
            files[rel] = None
            continue
        added = set()
        for hunk in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", git("diff", "-U0", "HEAD", "--", rel), re.MULTILINE):
            start, count = int(hunk.group(1)), int(hunk.group(2) or "1")
            added.update(range(start, start + count))
        files[rel] = added
    return files


def overwritten_attributes(tree: ast.Module) -> list:
    """(line, class, attribute): a subclass ``__init__`` assigns ``self.x`` that a base class in the same file assigns."""

    def init_attributes(cls: ast.ClassDef) -> dict:
        found = {}
        for item in cls.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                for node in ast.walk(item):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, (ast.AnnAssign, ast.AugAssign)) else []
                    for target in targets:
                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                            found.setdefault(target.attr, node.lineno)
        return found

    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    hits = []
    for cls in classes.values():
        own = init_attributes(cls)
        for base in cls.bases:
            if isinstance(base, ast.Name) and base.id in classes:
                for attr in sorted(set(own) & set(init_attributes(classes[base.id]))):
                    hits.append((own[attr], cls.name, attr))
    return hits


def shape_screen(files: dict) -> list:
    hits = []
    for rel, added in files.items():
        text = Path(rel).read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), 1):
            if added is not None and number not in added:
                continue
            for name, pattern in (("constant conditional", CONSTANT_TEST), ("bare await", BARE_AWAIT), ("except BaseException or bare except", BASE_EXCEPTION)):
                if pattern.match(line):
                    hits.append("%s:%d: %s: %s" % (rel, number, name, line.strip()))
        for lineno, cls, attr in overwritten_attributes(ast.parse(text)):
            if added is None or lineno in added:
                hits.append("%s:%d: %s.__init__ assigns self.%s, which a base class in this file also assigns" % (rel, lineno, cls, attr))
    return hits


def main() -> int:
    out = Path(sys.argv[1])
    files = changed_python()
    names = sorted(files)
    lines = ["%d Python files (%d new, %d modified):" % (len(names), sum(1 for v in files.values() if v is None), sum(1 for v in files.values() if v is not None))] + ["  " + name for name in names]
    worst = 0
    tools = (
        ("CodeQL prescreen, known answer", [sys.executable, "-I", "util/ad-hoc/2026-10-05_codeql_python_prescreen.py", "--known-answer"]),
        ("CodeQL prescreen", [sys.executable, "-I", "util/ad-hoc/2026-10-05_codeql_python_prescreen.py"] + names),
        ("implicit string concatenation in a list", [sys.executable, "-I", "util/ad-hoc/2026-11-08_flood4r2_ml_code_implicit_concat_check.py"] + names),
        ("G-PATH (util/home_path_literal_check.py)", [sys.executable, "-I", "util/home_path_literal_check.py"] + [name for name in names if name.startswith("util/")]),
    )
    every = [line[3:] for line in git("status", "--porcelain", "--untracked-files=all").splitlines()]
    # G-TMP by name: its whole-scope form reads tracked files only, so it would not see a file this change adds.
    tools += (("G-TMP (util/tmp_path_literal_check.py), the %d changed files by name" % len(every), [sys.executable, "-I", "util/tmp_path_literal_check.py"] + every),)
    for label, argv in tools:
        proc = subprocess.run(argv, capture_output=True, text=True, check=False)  # nosec B603 -- fixed argv
        worst = max(worst, proc.returncode)
        lines += ["", "=== %s: exit %d" % (label, proc.returncode), (proc.stdout + proc.stderr).rstrip()[-3000:]]
    hits = shape_screen(files)
    lines += ["", "=== shapes on added lines (constant conditional, bare await, except BaseException / bare except, overwritten attribute): %d" % len(hits)] + hits
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[-12 - len(hits) :]))
    return 1 if worst or hits else 0


if __name__ == "__main__":
    sys.exit(main())
