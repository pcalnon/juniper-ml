# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6b.lTWETu/prescreen_branch.py
# Written by Lane 11-R6B (adversarial, on round 5's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R6B: run the repo's CodeQL prescreen over every .py file the branch adds or changes (read-only)."""

import importlib.util
import sys
from pathlib import Path

sys.dont_write_bytecode = True
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
S = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("prescreen", W / "util" / "ad-hoc" / "2026-10-05_codeql_python_prescreen.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
files = [ln.strip() for ln in (S / "branch_py.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
total = 0
for rel in files:
    found = mod._scan(W / rel)
    for ln, rule, msg in found:
        print(f"{rel}:{ln}: {rule}: {msg}")
    total += len(found)
print(f"{total} predicted alert(s) in {len(files)} file(s)")
# instrument adequacy: it must fire on the pre-fix round-5 probes
pre = sorted((S / "prefix").glob("*.py"))
n_pre = sum(len(mod._scan(p)) for p in pre)
print(f"pre-fix round-5 probes: {n_pre} alert(s) in {len(pre)} file(s)")
