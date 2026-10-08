#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r4b.5mnsCd/codeql_check.py
# Written by Lane 11-R4B (adversarial, on round 3's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Replay the CodeQL fix pass on the probes as they stood before it (r1/r2 at 7af6a381; r3 rebuilt by the archiver from
the lanes' scratch sources) and compare with adcba49f byte for byte; then check every dropped name is never read, and
that, with the edits normalised away, each probe's AST is unchanged. Also checks the 12 unedited r3 archives."""
import ast
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
HERE = Path(__file__).resolve().parent
M = HERE / "codeql" / "util" / "ad-hoc"
if M.exists():
    shutil.rmtree(HERE / "codeql")
M.mkdir(parents=True)


def show(rev, rel):
    r = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=W, capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


arch = load("arch", W / "util/ad-hoc/2026-10-05_archive_phase11_lane_probes.py")
fix = load("fix", W / "util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py")
# --- build the "before" tree
before = {}
for suffix in fix.EDITS:
    rel = f"util/ad-hoc/{fix.PREFIX[suffix[:2]]}{suffix}"
    if suffix.startswith(("r1", "r2")):
        before[suffix] = show("7af6a381", rel)
for lane, (dirname, label, files) in arch.LANES_R3.items():
    for name in files:
        src = arch.SCRATCH / dirname / name
        text = src.read_text(encoding="utf-8")
        body, shebang = text, ""
        if body.startswith("#!"):
            shebang, body = body.split("\n", 1)
            shebang += "\n"
        archived = shebang + arch.header(label, src, 3) + body
        suffix = f"r3_{lane}_{name}"
        if suffix in fix.EDITS:
            before[suffix] = archived
        else:
            at = show("adcba49f", f"util/ad-hoc/2026-10-08_phase11_{suffix}")
            print(f"unedited r3 archive {suffix}: {'MATCH' if at == archived else 'MISMATCH'}")
for suffix, text in before.items():
    (M / f"{fix.PREFIX[suffix[:2]]}{suffix}").write_text(text, encoding="utf-8")
for f in ("2026-10-05_phase11_probes_codeql_fixes.py", "2026-10-05_codeql_python_prescreen.py"):
    (M / f).write_bytes((W / "util/ad-hoc" / f).read_bytes())
r = subprocess.run([sys.executable, str(M / "2026-10-05_phase11_probes_codeql_fixes.py")], capture_output=True, text=True)
print("fix pass:", r.stdout.strip().splitlines()[-2:], r.stderr.strip()[:300], "rc", r.returncode)
bad = 0
for suffix in fix.EDITS:
    fn = f"{fix.PREFIX[suffix[:2]]}{suffix}"
    got = (M / fn).read_text(encoding="utf-8")
    want = show("adcba49f", f"util/ad-hoc/{fn}")
    if got != want:
        bad += 1
        print("REPLAY MISMATCH", fn)
print(f"replay: {len(fix.EDITS) - bad} of {len(fix.EDITS)} byte-identical to adcba49f")


# --- semantics: dropped names never read; AST equal after normalising the edits away
def loads(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            out.add(n.id)
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
            out.add(n.value.id)
    return out


class Unwith(ast.NodeTransformer):
    """with open(X) as fh: <stmts using fh>  ->  <stmts with fh replaced by open(X)>"""

    def visit_With(self, node):
        self.generic_visit(node)
        if len(node.items) == 1 and isinstance(node.items[0].optional_vars, ast.Name) and node.items[0].optional_vars.id == "fh":
            call = node.items[0].context_expr

            class Sub(ast.NodeTransformer):
                def visit_Name(self, n):
                    return call if n.id == "fh" else n

            return [Sub().visit(s) for s in node.body]
        return node


def strip_imports(tree):
    tree.body = [s for s in tree.body if not isinstance(s, (ast.Import, ast.ImportFrom))]
    for n in ast.walk(tree):
        if hasattr(n, "body") and isinstance(n.body, list):
            n.body = [s for s in n.body if not isinstance(s, (ast.Import, ast.ImportFrom))] or n.body
    return tree


for suffix, edits in fix.EDITS.items():
    fn = f"{fix.PREFIX[suffix[:2]]}{suffix}"
    old_t, new_t = before[suffix], show("adcba49f", f"util/ad-hoc/{fn}")
    old, new = ast.parse(old_t), ast.parse(new_t)
    notes = []
    for o, n, kind in edits:
        if kind in ("import", "local", "global"):
            o_names = {a.asname or a.name.split(".")[0] for s in ast.parse(o.strip() if kind == "import" else "if 1:\n" + o).body for x in ast.walk(s) if isinstance(x, (ast.Import, ast.ImportFrom)) for a in x.names} if kind == "import" else set()
            n_names = {a.asname or a.name.split(".")[0] for s in ast.parse(n.strip()).body for x in ast.walk(s) if isinstance(x, (ast.Import, ast.ImportFrom)) for a in x.names} if (kind == "import" and n.strip()) else set()
            if kind == "import":
                dropped = o_names - n_names
            else:
                to = {t.id for s in ast.walk(ast.parse(__import__("textwrap").dedent(o))) if isinstance(s, ast.Assign) for tg in s.targets for t in ast.walk(tg) if isinstance(t, ast.Name)}
                tn = {t.id for s in ast.walk(ast.parse(__import__("textwrap").dedent(n))) if isinstance(s, ast.Assign) for tg in s.targets for t in ast.walk(tg) if isinstance(t, ast.Name)} if n.strip() else set()
                dropped = to - tn
            read = dropped & loads(old)
            notes.append(f"{kind} drop {sorted(dropped)} read-in-old={sorted(read)}")
    # normalise: new -> unwith; both -> strip imports; old -> remove dropped local/global statements by text
    old_n = old_t
    for o, n, kind in edits:
        if kind in ("local", "global"):
            old_n = old_n.replace(o, n, 1)
    a = ast.dump(strip_imports(ast.parse(old_n)))
    b = ast.dump(strip_imports(Unwith().visit(ast.parse(new_t))))
    print(f"{suffix}: AST equal after normalising = {a == b}; {'; '.join(notes)}")
