"""
Screen Python files for the CodeQL review threads the 2026-10-05 prescreen does not model.

Each of these opened a merge-blocking review thread in the flood-4 arc (tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt):
  * a constant in a conditional (`if True:` / `if False:`; `while True:` is not flagged);
  * an unused module-level global (an assigned module-level name that is never read in the module);
  * a module imported both as `import X` and `from X import Y`;
  * a bare `await <name>` expression statement ("Statement has no effect").
Prints one line per finding and exits 1 when there is any, 0 when there is none.

Usage: python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_codeql_traps.py FILE [FILE ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-05_codeql_python_prescreen.py (the traps it does model)
"""

import ast
import sys
from pathlib import Path


def _findings(path: Path) -> list:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    assigned = []
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else ([node.target] if isinstance(node, ast.AnnAssign) else [])
        assigned += [(t.id, node.lineno) for t in targets if isinstance(t, ast.Name)]
    loaded = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    exported = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets) and isinstance(node.value, (ast.List, ast.Tuple)):
            exported = {e.value for e in node.value.elts if isinstance(e, ast.Constant)}
    out += [f"{path}:{line}: unused module-level global {name}" for name, line in assigned if name not in loaded and name not in exported and not name.startswith("__")]
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Constant):
            out.append(f"{path}:{node.lineno}: constant in a conditional")
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Await) and isinstance(node.value.value, ast.Name):
            out.append(f"{path}:{node.lineno}: bare await of a name")
    plain = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    froms = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    out += [f"{path}: {mod} imported both as `import` and `from ... import`" for mod in sorted(plain & froms)]
    return out


def main() -> int:
    findings = [f for arg in sys.argv[1:] for f in _findings(Path(arg))]
    print("\n".join(findings) if findings else f"no findings in {len(sys.argv) - 1} file(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
