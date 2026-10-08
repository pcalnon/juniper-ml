# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/replay_pass.py
# Written by Lane 11-R2B (adversarial, on round 1's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Replay the round-1 correction pass on scratch copies of the 1b7cf44b freeze; compare with b3c54692."""
import sys, importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("corr", sys.argv[1])
corr = importlib.util.module_from_spec(spec); sys.modules["corr"] = corr; spec.loader.exec_module(corr)
before = Path(sys.argv[2]).read_text(encoding="utf-8")
want = Path(sys.argv[3]).read_text(encoding="utf-8")
rb = Path(sys.argv[4]).read_text(encoding="utf-8")
rw = Path(sys.argv[5]).read_text(encoding="utf-8")
after = corr.apply(before, corr.SUBS)
record = corr.ROUND1_RECORD.replace("README_SUB_COUNT", str(len(corr.README_SUBS))).replace("SUB_COUNT", str(len(corr.SUBS)))
assert after.count("ROUND1_RECORD") == 1
after = after.replace("ROUND1_RECORD", record)
print("ledger replay identical to b3c54692:", after == want, len(after), len(want))
ra = corr.apply(rb, corr.README_SUBS)
print("README replay identical to b3c54692:", ra == rw)
if after != want:
    import difflib
    for l in list(difflib.unified_diff(want.splitlines(), after.splitlines(), lineterm="", n=0))[:40]:
        print(l[:200])
