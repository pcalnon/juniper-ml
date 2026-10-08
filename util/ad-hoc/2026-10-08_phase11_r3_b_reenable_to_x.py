# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r3b/reenable_to_x.py
# Written by Lane 11-R3B (adversarial, on round 2's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Independent of the repo readers: for each eviction X of request E, the last innermost lane change True->False
(any re-enable: fire, gate write or release) after E entered watched and before X; report X minus that time,
split by whether the re-enable coincides (within 2 ms) with a fire or gate write of false."""
import json
import sys

out_all = []
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    raw = d["raw"]
    req = {}
    for t, kind, rid, _p in raw["req"]:
        r = req.setdefault(rid, {"W": None, "end": None, "tEnd": None})
        if kind == "W" and r["W"] is None:
            r["W"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    writes = sorted({t for t, _b, _s in raw["fires"]} | {t for t, _b, v in raw["gate"] if v is False})
    reen = sorted(t for t, b, a, ty in raw["lane"] if ty in ("", "SET_LAYOUT") and b is True and a is False)
    trig, casc = [], []
    for rid, r in sorted(req.items(), key=lambda kv: kv[1]["W"] or 0):
        if r["end"] != "X":
            continue
        cands = [t for t in reen if r["W"] <= t < r["tEnd"]]
        if not cands:
            print("  no re-enable inside flight of", rid)
            continue
        t = cands[-1]
        is_w = any(abs(t - w) <= 2 for w in writes)
        (trig if is_w else casc).append(r["tEnd"] - t)
    print(path.split("/")[-2], "trigger-started:", sorted(trig), "cascade:", sorted(casc))
    out_all += trig + casc
print("all evictions:", len(out_all), "range", min(out_all), "-", max(out_all))
