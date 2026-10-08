#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 5 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R5A.LBVRcz/cq_ast.py
# Written by Lane 11-R5A (measurement re-creation, artifact-first, on round 4's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R5A: does the CodeQL pass's --round r4 change what any round-4 probe computes?

For each edited probe: parse the pre-fix archive and the 684d70bc file; undo each `with open(X) as fh: S(fh)`
back to `S(open(X))`; drop from the pre-fix tree the imports/bindings the pass dropped, after checking that
nothing in the pre-fix file reads them (Name loads, attribute bases, getattr/globals strings, the raw text);
then compare ast.dump of the two modules. Comments are not in the AST, so the empty-except comment and the
header amendment are invisible by construction. Prints names, counts and verdicts only.
"""
import ast
import copy
import re
from pathlib import Path

S = Path(__file__).resolve().parent
PRE = S / "cq_prefix"
POST = S / "cq_expected"


class UndoWith(ast.NodeTransformer):
    """`with open(...) as fh: <one stmt>` -> that stmt with `fh` replaced by the open(...) call."""

    def visit_With(self, node):
        self.generic_visit(node)
        if len(node.items) == 1 and isinstance(node.items[0].optional_vars, ast.Name) and node.items[0].optional_vars.id == "fh":
            call = node.items[0].context_expr
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "open" and len(node.body) == 1:
                stmt = copy.deepcopy(node.body[0])

                class Sub(ast.NodeTransformer):
                    def visit_Name(self, n):
                        if n.id == "fh" and isinstance(n.ctx, ast.Load):
                            return copy.deepcopy(call)
                        return n

                return Sub().visit(stmt)
        return node


def reads(tree, name):
    n_load = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == name and isinstance(n.ctx, (ast.Load, ast.Del)))
    n_glob = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.Global, ast.Nonlocal)) and name in n.names)
    n_str = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and re.search(rf"\b{re.escape(name)}\b", n.value))
    return n_load, n_glob, n_str


def drop(tree, pred):
    class T(ast.NodeTransformer):
        def generic_visit(self, node):
            super().generic_visit(node)
            for field in ("body", "orelse", "finalbody", "handlers"):
                seq = getattr(node, field, None)
                if isinstance(seq, list):
                    setattr(node, field, [s for s in seq if not pred(s)])
            return node

    return T().visit(tree)


def is_import_of(name):
    def pred(s):
        if isinstance(s, ast.Import) and any((a.asname or a.name) == name for a in s.names):
            if len(s.names) != 1:
                raise SystemExit("multi-name import; handle by hand")
            return True
        return False

    return pred


def is_assign_to(name):
    def pred(s):
        return isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name) and s.targets[0].id == name

    return pred


DROPPED = {
    "2026-10-08_phase11_r4_a_prescreen_sweep.py": [("srcs", "assign")],
    "2026-10-08_phase11_r4_a_r3_probe_compare.py": [("hashlib", "import")],
    "2026-10-08_phase11_r4_b_myreader.py": [("sys", "import")],
}

bad = 0
for post in sorted(POST.glob("2026-10-08_phase11_r4_*.py")):
    pre = PRE / post.name
    a_src, b_src = pre.read_text(encoding="utf-8"), post.read_text(encoding="utf-8")
    if a_src == b_src:
        continue
    a, b = ast.parse(a_src), ast.parse(b_src)
    notes = []
    for name, kind in DROPPED.get(post.name, []):
        n_load, n_glob, n_str = reads(a, name)
        raw_hits = len(re.findall(rf"\b{re.escape(name)}\b", a_src))
        notes.append(f"{name}: loads={n_load} global-decls={n_glob} in-strings={n_str} raw-text-occurrences={raw_hits}")
        a = drop(a, is_import_of(name) if kind == "import" else is_assign_to(name))
    b = UndoWith().visit(b)
    same = ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)
    fh_pre = len(re.findall(r"\bfh\b", a_src))
    print(f"{post.name}: AST-equivalent after normalising: {same}; 'fh' in pre-fix: {fh_pre}; " + "; ".join(notes))
    bad += 0 if same else 1
print("mismatches:", bad)
