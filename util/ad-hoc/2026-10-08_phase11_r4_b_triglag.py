#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r4b.5mnsCd/triglag.py
# Written by Lane 11-R4B (adversarial, on round 3's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Trigger lags from the transcripts: T-gate write, T-mode next W, T-tab clicks and their gate writes, T-apply."""
import json

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite/reports/e2e-canopy-2026-09-02/f058-census-v2/"
T = [W + "2026-10-05_census_live.json", W + "run2/2026-10-05_census_live.json"]
for ti, p in enumerate(T, 1):
    with open(p) as fh:
        d = json.load(fh)
    raw = d["raw"]
    req = {}
    for t, k, rid, props in raw["req"]:
        r = req.setdefault(rid, {"W": None, "end": None, "tEnd": None})
        if k == "W" and r["W"] is None:
            r["W"] = t
        elif k in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = k, t
    print(f"T{ti}: gate log {raw['gate']}")
    for rec in d["triggers"]:
        name = rec["name"]
        if rec.get("verdict") == "MISSED" or "t_ms" not in rec:
            print(f"  {name}: {rec.get('verdict')} keys={sorted(rec)}")
            continue
        t, rid = rec["t_ms"], rec["open_request"]
        tgt = req[rid]
        into = t - rec["open_since_ms"]
        line = f"  {name}: fired @{t} on req {rid}, {into} ms into its flight; target ended {tgt['end']} {tgt['tEnd'] - t} ms after; took={rec.get('took')}"
        gw = [(g[0] - t, g[1], g[2]) for g in raw["gate"] if g[0] > t and g[0] - t < 6000]
        nextW = sorted(r["W"] - t for r in req.values() if r["W"] is not None and r["W"] > t)[:2]
        line += f"; gate writes after (ms, before, val) {gw}; next W at {nextW}"
        if name == "T-tab":
            c = rec["clicks_ms"]
            line += f"; clicks at {[x - t for x in c]} (gap {c[1] - c[0]})"
            fw = [g[0] for g in raw["gate"] if g[0] > t and g[2] is False]
            line += f"; click->next gate-false write: {[min(w for w in fw if w > x) - x for x in c]}"
        print(line)
