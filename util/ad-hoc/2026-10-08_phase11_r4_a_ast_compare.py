#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R4A.mG5yhk/ast_compare.py
# Written by Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R4A: do the CodeQL edits change what any round-1/2 probe computes?

For each util/ad-hoc/2026-10-05_phase11_r{1,2}_*.py changed between 7af6a381 and adcba49f:
  * parse both versions;
  * in the NEW tree, undo every `with open(X) as fh: BODY` by substituting `open(X)` for `fh` in BODY and splicing BODY in;
  * in the OLD tree, drop import aliases / assignment targets that the NEW tree no longer has, but only after checking
    that the dropped name is never loaded anywhere in the OLD file (else: a real change);
  * compare ast.dump of the two; report residual differences.
Also checks that only comment lines changed in the header, and that every non-header, non-code change is a comment.
"""
import ast
import copy
import difflib
import subprocess
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")


def git(*a):
    return subprocess.run(["git", *a], cwd=W, check=True, capture_output=True, text=True).stdout


def show(rev, path):
    return git("show", f"{rev}:{path}")


class Unwith(ast.NodeTransformer):
    def visit_body(self, body):
        out = []
        for st in body:
            st = self.visit(st)
            if isinstance(st, ast.With) and len(st.items) == 1 and isinstance(st.items[0].optional_vars, ast.Name) and st.items[0].optional_vars.id == "fh":
                call = st.items[0].context_expr
                for inner in st.body:
                    out.append(SubFh(call).visit(copy.deepcopy(inner)))
            else:
                out.append(st)
        return out

    def generic_visit(self, node):
        for field in ("body", "orelse", "finalbody"):
            if hasattr(node, field) and isinstance(getattr(node, field), list):
                setattr(node, field, self.visit_body(getattr(node, field)))
        for h in getattr(node, "handlers", []) or []:
            h.body = self.visit_body(h.body)
        return node


class SubFh(ast.NodeTransformer):
    def __init__(self, call):
        self.call = call

    def visit_Name(self, n):
        if n.id == "fh":
            return copy.deepcopy(self.call)
        return n


def loaded_names(tree):
    s = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            s.add(n.id)
        if isinstance(n, ast.Attribute):
            pass
    return s


def import_aliases(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                out.append((a.asname or a.name).split(".")[0])
    return out


def strip_dropped(old_tree, new_tree, report):
    """Remove from old_tree the import aliases and bindings that new_tree lacks; check each is never loaded in old."""
    old_loads = loaded_names(old_tree)
    new_imports = set(import_aliases(new_tree))
    # imports
    for n in ast.walk(old_tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            keep = []
            for a in n.names:
                nm = (a.asname or a.name).split(".")[0]
                if nm in new_imports:
                    keep.append(a)
                else:
                    used = nm in old_loads
                    report.append(f"    dropped import {nm!r}: loaded anywhere in old file? {used}")
            n.names = keep
    # remove empty import statements & bindings missing in new
    new_dump = ast.dump(new_tree)

    class Dropper(ast.NodeTransformer):
        def generic_visit(self, node):
            super().generic_visit(node)
            for field in ("body", "orelse", "finalbody"):
                if hasattr(node, field) and isinstance(getattr(node, field), list):
                    lst = []
                    for st in getattr(node, field):
                        if isinstance(st, (ast.Import, ast.ImportFrom)) and not st.names:
                            continue
                        if isinstance(st, ast.Assign) and ast.dump(st) not in new_dump:
                            tgts = [t for t in st.targets]
                            names = []
                            for t in tgts:
                                for x in ast.walk(t):
                                    if isinstance(x, ast.Name):
                                        names.append(x.id)
                            # narrowed tuple assignment, e.g. eps, start, prev = [], None, False
                            if len(tgts) == 1 and isinstance(tgts[0], ast.Tuple) and isinstance(st.value, ast.Tuple):
                                pairs = list(zip(tgts[0].elts, st.value.elts))
                                for k in range(len(pairs)):
                                    reduced = [p for j, p in enumerate(pairs) if j != k]
                                    cand = ast.Assign(targets=[ast.Tuple(elts=[p[0] for p in reduced], ctx=ast.Store())], value=ast.Tuple(elts=[p[1] for p in reduced], ctx=ast.Load()), lineno=st.lineno)
                                    if ast.dump(cand, include_attributes=False) in new_dump:
                                        dn = pairs[k][0].id
                                        report.append(f"    narrowed tuple binding drops {dn!r}: loaded anywhere in old file? {dn in old_loads}; RHS elt {ast.unparse(pairs[k][1])}")
                                        lst.append(cand)
                                        break
                                else:
                                    lst.append(st)
                                continue
                            if all(nm not in old_loads for nm in names):
                                report.append(f"    dropped binding {names}: loaded anywhere in old file? False; RHS: {ast.unparse(st.value)[:90]}")
                                continue
                            report.append(f"    binding {names} differs and IS loaded somewhere")
                        lst.append(st)
                    setattr(node, field, lst)
            return node

    return Dropper().visit(old_tree)


def code_only(text):
    """Source with comment-only lines removed (to show the non-comment diff)."""
    return [l for l in text.splitlines() if not l.lstrip().startswith("#")]


def main():
    files = [l for l in git("diff", "--name-only", "7af6a381", "adcba49f", "--", "util/ad-hoc/").splitlines() if "_phase11_r1_" in l or "_phase11_r2_" in l]
    print(len(files), "round-1/2 probes changed")
    bad = 0
    for f in files:
        old, new = show("7af6a381", f), show("adcba49f", f)
        report = []
        to, tn = ast.parse(old), ast.parse(new)
        tn2 = Unwith().visit(copy.deepcopy(tn))
        to2 = strip_dropped(copy.deepcopy(to), tn2, report)
        eq = ast.dump(to2) == ast.dump(tn2)
        # header: which comment lines changed
        dl = [l for l in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0) if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        comment_changes = [l for l in dl if l[1:].lstrip().startswith("#")]
        code_changes = [l for l in dl if not l[1:].lstrip().startswith("#")]
        hdr_ok = any("modified 2026-10-08 only for CodeQL" in l for l in comment_changes) and any("lane's file, unmodified" in l for l in comment_changes if l.startswith("-"))
        print(f"{'EQUIV' if eq else 'DIFF '} hdr_amended={hdr_ok} code_lines_changed={len(code_changes)} {f.split('/')[-1]}")
        for r in report:
            print(r)
        if not eq:
            bad += 1
            for l in difflib.unified_diff(ast.dump(to2, indent=1).splitlines(), ast.dump(tn2, indent=1).splitlines(), lineterm="", n=1):
                print("      ", l[:160])
    print("non-equivalent:", bad)


if __name__ == "__main__":
    main()
