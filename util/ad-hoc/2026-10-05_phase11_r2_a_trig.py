# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R2A.sffLXI/trig.py
# Written by Lane 11-R2A (measurement re-creation, on round 1's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
import json
import sys

for p in sys.argv[1:]:
    with open(p) as fh:
        d = json.load(fh)
    raw = d["raw"]
    req = {}
    for t, k, i, pr in raw["req"]:
        r = req.setdefault(i, {"W": None, "end": None, "tEnd": None})
        if k == "W" and r["W"] is None:
            r["W"] = t
        elif k in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = k, t
    print(p.split("/")[-2], d["served_sha"][:8])
    for tr in d["triggers"]:
        if "t_ms" not in tr:
            print("  ", tr["name"], tr.get("verdict"), "clamp", tr.get("clamp"))
            continue
        t = tr["t_ms"]
        k = tr["open_request"]
        into = t - tr["open_since_ms"]
        ans = req[k]["tEnd"] - t
        nxtW = min((r["W"] for r in req.values() if r["W"] is not None and r["W"] > t))
        ga = [g for g in raw["gate"] if t < g[0] <= t + 6000]
        gates_after = [(g[0] - t, g[1], g[2]) for g in ga]
        line = f"   {tr['name']}: t {t}; open req {k} {into} ms into flight; it ended {req[k]['end']} {ans} ms after; next W +{nxtW - t}; gate writes after (dt, before, v): {gates_after}"
        if "clicks_ms" in tr:
            c = tr["clicks_ms"]
            line += f"; clicks +{c[0]-t}, +{c[1]-t} (spacing {c[1]-c[0]}); gate-after-click: {[g[0] - c[i] for i, g in enumerate(ga)]}"
            g2 = ga[-1][0]
            live = [i for i, r in req.items() if r["W"] is not None and r["W"] <= g2 and (r["tEnd"] is None or r["tEnd"] > g2)]
            kk = max(live)
            line += f"; 2nd write {g2 - t} after trigger, {g2 - req[kk]['W']} ms into req {kk}, answered {req[kk]['tEnd'] - g2} later"
        print(line)
