# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/c3_captures.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Claim 3: was every CasCor capture taken after its run completed?  Print each capture's samples and the
case's poll timeline end, plus the metrics-history tail (kind/phase/epoch) for each CasCor case."""
import glob
import json
import os

ROOT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/clever-juggling-spring/reports/2026-09-23_canopy-a-n2-generate-stage-train-render"

for case in ("01_spirals_control", "02_gaussian", "03_checkerboard", "04_equities", "04_equities__restart-fresh"):
    d = f"{ROOT}/{case}"
    print(f"===== {case}")
    pt = f"{d}/poll_timeline.json"
    if os.path.exists(pt):
        p = json.load(open(pt))
        if isinstance(p, list) and p:
            print("  poll first:", {k: p[0].get(k) for k in list(p[0])[:8]})
            print("  poll last :", {k: p[-1].get(k) for k in list(p[-1])[:8]})
        else:
            print("  poll:", type(p), (list(p)[:5] if isinstance(p, dict) else p))
    for t in sorted(glob.glob(f"{d}/dashboard*_timeline.json")):
        j = json.load(open(t))
        samples = j["samples"] if isinstance(j, dict) else j
        print(f"  {os.path.basename(t)} modal={j.get('welcome_modal') if isinstance(j, dict) else None}")
        for s in samples:
            ni = s.get("network_info", "")
            step = ni.split("Training Step:")[1].split("|")[0].strip() if "Training Step:" in ni else None
            phase = ni.split("Training Phase:")[1].split("|")[0].strip() if "Training Phase:" in ni else None
            mon = ni.split("Monitoring:")[1].split("|")[0].strip() if "Monitoring:" in ni else None
            print(f"     t={s.get('t_s')} top={s.get('top_status')!r} step(ni)={step} phase(ni)={phase} monitoring={mon}")
    h = json.load(open(f"{d}/13_render_api_metrics_history_limit_0.json"))
    hist = h["response"]["history"]
    if isinstance(hist, dict):
        rows = hist.get("last_20") or []
        print(f"  history count={hist.get('count')} last rows (epoch,phase,acc):", [(r.get("epoch"), r.get("phase"), (r.get("metrics") or {}).get("accuracy")) for r in rows[-4:]])
    else:
        print(f"  history len={len(hist)} last rows (epoch,phase,acc):", [(r.get("epoch"), r.get("phase"), (r.get("metrics") or {}).get("accuracy")) for r in hist[-4:]])
