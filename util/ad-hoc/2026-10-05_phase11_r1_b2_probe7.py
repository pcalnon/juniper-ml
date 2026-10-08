# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B2.KZI9rh/probe7.py
# Written by Lane 11-B2 (adversarial, claims beyond evidence, escalate side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-B2 probe 7: trigger timings (into flight, answered after), clicks, fire record fields, synth check."""
import json

for p in ["ev/2026-10-05_census_live.json", "ev/run2/2026-10-05_census_live.json"]:
    with open(p) as fh:
        d = json.load(fh)
    raw = d["raw"]
    req = {}
    for t, k, rid, _pr in raw["req"]:
        r = req.setdefault(rid, {"tW": None, "tEnd": None, "end": None})
        if k == "W" and r["tW"] is None:
            r["tW"] = t
        elif k in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = k, t
    for tr in d["triggers"]:
        if tr.get("verdict") == "MISSED":
            print(p[:8], tr["name"], "MISSED")
            continue
        r = req[tr["open_request"]]
        print(p[:8], tr["name"], f"into flight {(tr['t_ms'] - tr['open_since_ms']) / 1000:.2f} s", f"answered {(r['tEnd'] - tr['t_ms']) / 1000:.2f} s after", r["end"], "clicks", tr.get("clicks_ms"))
    print(" fires third field:", {f[2] for f in raw["fires"]}, "before:", {f[1] for f in raw["fires"]})
with open("ev/2026-10-05_synth_check.jsonl") as fh:
    for line in fh:
        o = json.loads(line)
        print(" synth:", {k: o[k] for k in list(o)[:4]})
