#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R4A.mG5yhk/ka_lines.py
# Written by Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R4A: the prescreen's predicted (file, line, rule) on the rebuilt pre-fix Phase 10 probes vs juniper-ml#2157's
CodeQL threads (path, line, rule), fetched with a GET."""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
A = W / "util" / "ad-hoc"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


pre = load("pre", A / "2026-10-05_codeql_python_prescreen.py")
cf = load("cf", A / "2026-10-05_phase10_r1_probes_close_files.py")
pred = set()
with tempfile.TemporaryDirectory() as td:
    for suffix in pre.PR2157:
        fixed = (A / f"{cf.PREFIX}{suffix}").read_text(encoding="utf-8")
        before = fixed
        for old, new in cf.EDITS[suffix]:
            before = before.replace(new, old)
        p = Path(td) / f"{cf.PREFIX}{suffix}"
        p.write_text(before, encoding="utf-8")
        for ln, rule, _m in pre._scan(p):
            pred.add((f"{cf.PREFIX}{suffix}", ln, {"open-not-closed": "File is not always closed", "unused-import": "Unused import"}.get(rule, rule)))
out = subprocess.run(["gh", "api", "repos/pcalnon/juniper-ml/pulls/2157/comments?per_page=100", "--paginate", "--jq",
                      '.[] | select(.user.login | test("advanced-security|codeql"; "i")) | [.path, (.line // .original_line), (.body | split("\\n")[0])] | @json'],
                     capture_output=True, text=True, check=True).stdout.splitlines()
gh = set()
for l in out:
    path, line, head = json.loads(l)
    gh.add((path.split("/")[-1], line, head.replace("## CodeQL / ", "").strip()))
print("predicted", len(pred), "github", len(gh), "identical sets:", pred == gh)
print("only predicted:", sorted(pred - gh))
print("only on github:", sorted(gh - pred))
