#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r4b.5mnsCd/readers_cmp.py
# Written by Lane 11-R4B (adversarial, on round 3's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Run the release trace (report and --self-test) and the alias replay at 7af6a381 and adcba49f on both transcripts; compare."""
import hashlib
import subprocess
import sys
from pathlib import Path

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite"
S = Path(__file__).resolve().parent / "readers"
T = [
    W + "/reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json",
    W + "/reports/e2e-canopy-2026-09-02/f058-census-v2/run2/2026-10-05_census_live.json",
]
FILES = {"trace": "util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py", "replay": "util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py"}
for rev in ("7af6a381", "adcba49f"):
    for k, f in FILES.items():
        p = S / rev / Path(f).name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(subprocess.run(["git", "show", f"{rev}:{f}"], cwd=W, check=True, capture_output=True).stdout)
outs = {}
for rev in ("7af6a381", "adcba49f"):
    for ti, t in enumerate(T, 1):
        for mode, k, extra in (("report", "trace", []), ("selftest", "trace", ["--self-test"]), ("replay", "replay", [])):
            r = subprocess.run([sys.executable, str(S / rev / Path(FILES[k]).name), t] + extra, capture_output=True, text=True)
            outs[(rev, ti, mode)] = (r.returncode, r.stdout, r.stderr)
            (S / f"{rev}_T{ti}_{mode}.txt").write_text(r.stdout + "\n--stderr--\n" + r.stderr + f"\n--rc {r.returncode}--\n")
for ti in (1, 2):
    for mode in ("report", "selftest", "replay"):
        a, b = outs[("7af6a381", ti, mode)], outs[("adcba49f", ti, mode)]
        print(f"T{ti} {mode}: rc {a[0]} vs {b[0]}; identical={a == b}; sha {hashlib.sha256(b[1].encode()).hexdigest()[:12]}")
