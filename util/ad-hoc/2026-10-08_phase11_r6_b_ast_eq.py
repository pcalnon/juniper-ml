# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6b.lTWETu/ast_eq.py
# Written by Lane 11-R6B (adversarial, on round 5's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R6B: are the round-5 probes after the CodeQL third run AST-equivalent to the archiver's output?

Undo each `with open(X) as fh: S(fh)` into S(open(X)) in the fixed file, drop the imports the run removed from
the pre-fix file, and compare ast.dump. Also confirm no dropped name is read anywhere in the pre-fix file.
"""

import ast
import sys
from pathlib import Path

sys.dont_write_bytecode = True
S = Path(__file__).resolve().parent
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite/util/ad-hoc")
DROPPED = {
    "2026-10-08_phase11_r5_a_cq_ast.py": {"sys"},
    "2026-10-08_phase11_r5_a_lane_transcripts.py": {"re", "sys"},
    "2026-10-08_phase11_r5_a_prescreen_branch.py": {"sys"},
    "2026-10-08_phase11_r5_a_triglag.py": set(),
}


class Unwith(ast.NodeTransformer):
    def visit_With(self, node):
        self.generic_visit(node)
        if len(node.items) == 1 and isinstance(node.items[0].optional_vars, ast.Name) and node.items[0].optional_vars.id == "fh" and len(node.body) == 1:
            call = node.items[0].context_expr

            class Sub(ast.NodeTransformer):
                def visit_Name(self, n):
                    return call if (n.id == "fh" and isinstance(n.ctx, ast.Load)) else n

            return Sub().visit(node.body[0])
        return node


class DropImports(ast.NodeTransformer):
    def __init__(self, names):
        self.names = names

    def visit_Import(self, node):
        keep = [a for a in node.names if (a.asname or a.name) not in self.names]
        if not keep:
            return None
        node.names = keep
        return node


for name, dropped in sorted(DROPPED.items()):
    pre_src = (S / "prefix" / name).read_text(encoding="utf-8")
    post_src = (W / name).read_text(encoding="utf-8")
    pre = DropImports(dropped).visit(ast.parse(pre_src))
    post = Unwith().visit(ast.parse(post_src))
    same = ast.dump(pre) == ast.dump(post)
    reads = {n.id for n in ast.walk(ast.parse(pre_src)) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    attr_bases = {n.value.id for n in ast.walk(ast.parse(pre_src)) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    used = sorted(d for d in dropped if d in reads or d in attr_bases)
    print(f"{name}: AST-equivalent={same}; dropped names read in pre-fix: {used or 'none'}")
# instrument adequacy: a one-token mutation must be caught
pre_src = (S / "prefix" / "2026-10-08_phase11_r5_a_triglag.py").read_text(encoding="utf-8")
mut = pre_src.replace("encoding=\"utf-8\"", "encoding=\"latin-1\"", 1)
print("mutation caught:", ast.dump(ast.parse(mut)) != ast.dump(ast.parse(pre_src)))
