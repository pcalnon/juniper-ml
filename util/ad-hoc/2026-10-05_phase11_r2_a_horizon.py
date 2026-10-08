# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R2A.sffLXI/horizon.py
# Written by Lane 11-R2A (measurement re-creation, on round 1's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Check the horizon rule on all 32 mid-request re-enables: evicted iff the in-flight response landed after the next request."""
import json
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from myreader import innermost_state_machine, requests  # noqa: E402

for p in sys.argv[1:]:
    with open(p) as fh:
        d = json.load(fh)
    raw = d["raw"]
    req, _ = requests(raw)
    ids = sorted(req)
    sm, _, _ = innermost_state_machine(raw["lane"])
    writes = [t for t, _, _ in raw["fires"]] + [t for t, b, v in raw["gate"] if v is False]
    rel = [c["t"] for c in sm if c["b"] is True and c["a"] is False and not any(abs(c["t"] - w) <= 2 for w in writes)]
    ev = [i for i in ids if req[i]["end"] == "X"]
    landed = {i: req[i]["tEnd"] for i in ids if req[i]["end"] == "A"}
    for k in ev:
        hi = req[k + 1]["tEnd"] if req.get(k + 1, {}).get("tEnd") is not None else 10**12
        c = [t for t in rel if req[k]["tEnd"] <= t < hi and not (req.get(k + 1, {}).get("end") == "A" and 0 <= req[k + 1]["tEnd"] - t <= 100)]
        landed[k] = c[0]
    # X vs successor W gap (eviction moment vs entry)
    xw = [req[k + 1]["W"] - req[k]["tEnd"] for k in ev]
    print(p.split("/")[-2], "X_k -> W_{k+1} ms:", sorted(xw))
    # answered k: A_k < W_{k+1} always?
    bad = [k for k in ids if req[k]["end"] == "A" and (k + 1) in req and req[k + 1]["W"] is not None and req[k]["tEnd"] > req[k + 1]["W"]]
    print("  answered requests whose answer came after the successor entered watched:", bad)
    re = [t for t, b, s in raw["fires"]] + [t for t, b, v in raw["gate"] if b is True and v is False]
    viol = []
    n = 0
    for t in sorted(re):
        live = [i for i in ids if req[i]["W"] is not None and req[i]["W"] <= t and (req[i]["tEnd"] is None or req[i]["tEnd"] > t)]
        if not live:
            continue
        n += 1
        k = live[-1]
        nxt = min((i for i in ids if req[i]["W"] is not None and req[i]["W"] > t), key=lambda i: req[i]["W"])
        evicted = req[k]["end"] == "X"
        after_next = landed[k] > req[nxt]["W"]
        if evicted != after_next:
            viol.append((t, k, evicted, landed[k] - t, req[nxt]["W"] - t))
        if evicted:
            print(f"  evicting re-enable @{t}: req {k} X at +{req[k]['tEnd'] - t}, next W at +{req[nxt]['W'] - t}, landing +{landed[k] - t}")
    print(f"  mid-request re-enables {n}; rule violations (evicted != landed-after-next-W): {viol}")
