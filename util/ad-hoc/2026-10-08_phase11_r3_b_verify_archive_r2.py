# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r3b/verify_archive_r2.py
# Written by Lane 11-R3B (adversarial, on round 2's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Rebuild each round-2 archived probe from its tmpfs source with the archiver's own header() (loaded by path, not
executed as main) and compare byte for byte with the file at 7af6a381 in the worktree. Prints only match status."""
import importlib.util
import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
spec = importlib.util.spec_from_file_location("arch", W / "util/ad-hoc/2026-10-05_archive_phase11_lane_probes.py")
arch = importlib.util.module_from_spec(spec)
sys.modules["arch"] = arch
spec.loader.exec_module(arch)
ok = 0
for lane, (dirname, label, files) in arch.LANES_R2.items():
    for name in files:
        src = arch.SCRATCH / dirname / name
        text = src.read_text(encoding="utf-8")
        body, shebang = text, ""
        if body.startswith("#!"):
            shebang, body = body.split("\n", 1)
            shebang += "\n"
        want = shebang + arch.header(label, src, 2) + body
        dst = W / "util/ad-hoc" / f"2026-10-05_phase11_r2_{lane}_{name}"
        got = dst.read_text(encoding="utf-8") if dst.exists() else None
        same = got == want
        ok += same
        print(f"{dst.name}: {'MATCH' if same else ('MISSING' if got is None else 'DIFF')}")
print(f"{ok} of {sum(len(f) for _d, _l, f in arch.LANES_R2.values())} match")
