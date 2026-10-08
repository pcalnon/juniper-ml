# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r3b/horizon.py
# Written by Lane 11-R3B (adversarial, on round 2's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Independent horizon reader: every write of `false` (watchdog fire or gate write) made while a feeder request
is in flight; for each, the in-flight request's end (A answered / X evicted) and the next request's W, relative to
the write. Reads raw req / fires / gate only (no repo reader code)."""
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    d = json.load(fh)
raw = d["raw"]
req = {}
for t, kind, rid, _p in raw["req"]:
    r = req.setdefault(rid, {"id": rid, "W": None, "end": None, "tEnd": None, "kinds": []})
    r["kinds"].append((t, kind))
    if kind == "W" and r["W"] is None:
        r["W"] = t
    elif kind in ("A", "X") and r["end"] is None:
        r["end"], r["tEnd"] = kind, t
reqs = sorted((r for r in req.values() if r["W"] is not None), key=lambda r: r["W"])
kinds = sorted({k for r in req.values() for _t, k in r["kinds"]})
print("req kinds:", kinds, "requests:", len(reqs), "A:", sum(r["end"] == "A" for r in reqs), "X:", sum(r["end"] == "X" for r in reqs), "open:", sum(r["end"] is None for r in reqs))
writes = [(t, "fire", b) for t, b, _s in raw["fires"]] + [(t, "gate", b) for t, b, v in raw["gate"] if v is False]
writes.sort()
print("gate log:", raw["gate"])
trig = {x["name"]: x for x in d["triggers"]}
print("triggers:", {k: (v.get("t_ms"), v.get("clicks_ms")) for k, v in trig.items()})
rows = []
for t, kind, before in writes:
    inflight = [r for r in reqs if r["W"] <= t and (r["tEnd"] is None or r["tEnd"] > t)]
    if not inflight:
        print(f"  {kind}@{t} before={before}: nothing in flight")
        continue
    cur = inflight[-1]
    i = reqs.index(cur)
    nxt = reqs[i + 1] if i + 1 < len(reqs) else None
    row = {
        "t": t,
        "kind": kind,
        "before": before,
        "cur": cur["id"],
        "cur_age": t - cur["W"],
        "end": cur["end"],
        "end_after": (cur["tEnd"] - t) if cur["tEnd"] is not None else None,
        "next": nxt and nxt["id"],
        "nextW_after": (nxt["W"] - t) if nxt else None,
        "x_to_nextW": (nxt["W"] - cur["tEnd"]) if (nxt and cur["end"] == "X") else None,
        "ninflight": len(inflight),
    }
    rows.append(row)
for r in rows:
    print(r)
mid = [r for r in rows]
ev = [r for r in mid if r["end"] == "X"]
ok = [r for r in mid if r["end"] == "A"]
print(f"mid-request writes: {len(mid)} (fires {sum(r['kind']=='fire' for r in mid)}, gate {sum(r['kind']=='gate' for r in mid)}); evicting {len(ev)}; answered {len(ok)}; other {len(mid)-len(ev)-len(ok)}")
if ev:
    print("evicting: X after write ms", sorted(r["end_after"] for r in ev), "fires only", sorted(r["end_after"] for r in ev if r["kind"] == "fire"))
    print("evicting: X to next W ms", sorted(r["x_to_nextW"] for r in ev))
if ok:
    print("answered: A after write ms", sorted(r["end_after"] for r in ok), "fires only", sorted(r["end_after"] for r in ok if r["kind"] == "fire"))
print("next W after write ms (all)", sorted(r["nextW_after"] for r in mid if r["nextW_after"] is not None))
print("next W after write ms (fires)", sorted(r["nextW_after"] for r in mid if r["nextW_after"] is not None and r["kind"] == "fire"))
print("next W after write ms (non-evicting)", sorted(r["nextW_after"] for r in ok if r["nextW_after"] is not None))
print("next W after write ms (evicting)", sorted(r["nextW_after"] for r in ev if r["nextW_after"] is not None))
