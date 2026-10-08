# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/reenables.py
# Written by Lane 11-R2B (adversarial, on round 1's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Independent: every mid-request re-enable (fire or gate write of False on a disabled lane with a request in flight)."""
import json, sys, importlib.util
spec = importlib.util.spec_from_file_location("rt", sys.argv[1])
rt = importlib.util.module_from_spec(spec); sys.modules["rt"] = rt; spec.loader.exec_module(rt)
allrows = []
for path in sys.argv[2:]:
    with open(path) as fh:
        d = json.load(fh)
    raw = d["raw"]
    res = rt.analyze(d)
    late_by_ev = {x["evicted"]: x["release_ms"] for x in res["late"]}
    req = {}
    for t, kind, rid, _p in raw["req"]:
        r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
        if kind == "W" and r["tW"] is None:
            r["tW"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    reqs = sorted((r for r in req.values() if r["tW"] is not None), key=lambda r: r["tW"])
    tl = rt.lane_timeline(raw["lane"])
    def state_before(t):
        s = None
        for x, v in tl:
            if x < t: s = v
            else: break
        return s
    events = [("fire", t) for t, _b, _s in raw["fires"]] + [("gate", t) for t, b, v in raw["gate"] if b is True and v is False]
    for kind, t in sorted(events, key=lambda e: e[1]):
        live = [r for r in reqs if r["tW"] <= t and (r["tEnd"] is None or r["tEnd"] > t)]
        cur = live[-1] if live else None
        nxt = next((r for r in reqs if r["tW"] > t), None)
        if cur is None:
            allrows.append(("run2" if "run2" in path else "run1", kind, t, "no request in flight", "next W after", (nxt["tW"] - t) if nxt else None)); continue
        land = cur["tEnd"] if cur["end"] == "A" else late_by_ev.get(cur["id"])
        row = dict(run=1 if "run2" not in path else 2, kind=kind, t=t, cur=cur["id"], into=t - cur["tW"], outcome=cur["end"],
                   x_after=(cur["tEnd"] - t) if cur["end"] == "X" else None, land_after=(land - t) if land is not None else None,
                   next_id=nxt["id"] if nxt else None, next_w_after=(nxt["tW"] - t) if nxt else None, lane_before=state_before(t))
        allrows.append(row)
mid = [r for r in allrows if isinstance(r, dict)]
nomid = [r for r in allrows if not isinstance(r, dict)]
print("no request in flight:", nomid)
for r in mid:
    print(r)
print("mid-request re-enables:", len(mid), " evicting:", sum(1 for r in mid if r["outcome"] == "X"))
nw = [r["next_w_after"] for r in mid if r["next_w_after"] is not None]
print("next W after re-enable: min", min(nw), "max", max(nw))
for lab, sel in (("evicting", [r for r in mid if r["outcome"] == "X"]), ("non-evicting", [r for r in mid if r["outcome"] == "A"])):
    v = [r["next_w_after"] for r in sel]
    print(lab, "next W after: min", min(v), "max", max(v), sorted(v))
    v2 = [r["land_after"] for r in sel]
    print(lab, "in-flight response landed after: min", min(v2), "max", max(v2))
over = [r for r in mid if r["land_after"] is not None and r["land_after"] > 1000]
print("re-enables > 1 period before landing:", len(over), " of which evicted:", sum(1 for r in over if r["outcome"] == "X"))
under = [r for r in mid if r["land_after"] is not None and r["land_after"] <= 1000]
print("re-enables <= 1 period before landing:", len(under), " evicted:", sum(1 for r in under if r["outcome"] == "X"))
for r in mid:
    if r["outcome"] == "A" and r["next_w_after"] is not None and r["next_w_after"] < r["land_after"]:
        print("ANOMALY next W before answer", r)
