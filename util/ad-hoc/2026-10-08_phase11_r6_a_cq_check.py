#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6a/cq_check.py
# Written by Lane 11-R6A (measurement re-creation, artifact-first, on round 5's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Prescreen the round-5 probes before and after the CodeQL pass's third run, and show that its edits change
nothing a probe computes: dropped imports are never read, and the one `with` rewrite is AST-equivalent to the
original once undone."""
import ast
import difflib
import importlib.util
import sys
from pathlib import Path

S = Path("/tmp/tmp.y8saaB4Mk1")
spec = importlib.util.spec_from_file_location("prescreen", S / "cq/util/ad-hoc/2026-10-05_codeql_python_prescreen.py")
pre = importlib.util.module_from_spec(spec)
sys.modules["prescreen"] = pre
spec.loader.exec_module(pre)

total_before = total_after = 0
for p in sorted((S / "cq_pre").glob("*.py")):
    a = pre._scan(p)
    b = pre._scan(S / "cq/util/ad-hoc" / p.name)
    total_before += len(a)
    total_after += len(b)
    print(f"{p.name}: before {len(a)} {[x for x in a]} ; after {len(b)}")
print(f"TOTAL before {total_before}, after {total_after}")


class UndoWith(ast.NodeTransformer):
    """Turn `with open(X) as fh: <stmt using fh>` back into `<stmt with open(X) in place of fh>`."""

    def visit_With(self, node):
        self.generic_visit(node)
        if len(node.items) == 1 and isinstance(node.items[0].optional_vars, ast.Name) and node.items[0].optional_vars.id == "fh" and len(node.body) == 1:
            call = node.items[0].context_expr

            class Sub(ast.NodeTransformer):
                def visit_Name(self, n):
                    return call if n.id == "fh" else n

            return Sub().visit(node.body[0])
        return node


def names(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            pass
    return out


for p in sorted((S / "cq_pre").glob("*.py")):
    q = S / "cq/util/ad-hoc" / p.name
    ta, tb = ast.parse(p.read_text(encoding="utf-8")), ast.parse(q.read_text(encoding="utf-8"))
    if ast.dump(ta) == ast.dump(tb):
        print(f"{p.name}: AST identical (only comments changed)" if p.read_bytes() != q.read_bytes() else f"{p.name}: untouched")
        continue
    tb2 = UndoWith().visit(tb)
    ast.fix_missing_locations(tb2)
    # drop the imports the pass removed from the "before" tree, after checking nothing reads them
    imp_a = {(type(n).__name__, ast.dump(n)) for n in ta.body if isinstance(n, (ast.Import, ast.ImportFrom))}
    imp_b = {(type(n).__name__, ast.dump(n)) for n in tb.body if isinstance(n, (ast.Import, ast.ImportFrom))}
    dropped = imp_a - imp_b
    dropped_names = set()
    for n in ta.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)) and (type(n).__name__, ast.dump(n)) in dropped:
            for al in n.names:
                dropped_names.add((al.asname or al.name).split(".")[0])
    read = names(ta) & dropped_names
    ta2 = ast.Module(body=[n for n in ta.body if not (isinstance(n, (ast.Import, ast.ImportFrom)) and (type(n).__name__, ast.dump(n)) in dropped)], type_ignores=[])
    same = ast.dump(ta2) == ast.dump(tb2)
    print(f"{p.name}: dropped imports {sorted(dropped_names)}; any of them read in the original: {sorted(read) or 'none'}; "
          f"AST-equivalent after undoing the with and the drops: {same}")
    if not same:
        for line in difflib.unified_diff(ast.dump(ta2, indent=1).splitlines(), ast.dump(tb2, indent=1).splitlines(), lineterm="", n=1):
            print("   ", line)
