# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, a2/triggers.py
# Written by Lane 11-A2 (measurement re-creation, raw-transcript-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Item 7: per-trigger timeline (gate writes, requests, lane physical changes, fires) and wall-clock bounds."""
import importlib.util, sys, io, contextlib, json, datetime
spec = importlib.util.spec_from_file_location("myreader", "/tmp/tmp.AFzDbAMY9I/myreader.py")
mr = importlib.util.module_from_spec(spec); sys.modules["myreader"] = mr; spec.loader.exec_module(mr)

for p in sys.argv[1:]:
    with contextlib.redirect_stdout(io.StringIO()):
        d, reqs, phys, ordered, fire_rows = mr.analyse(p, "x")
    raw = d["raw"]
    print("=" * 90)
    print(p)
    for g in raw["gate"]:
        t = g[0]
        fl = mr.in_flight(reqs, t)
        prev = max((r for r in ordered if r["tEnd"] is not None and r["tEnd"] <= t), key=lambda r: r["tEnd"], default=None)
        nxt = min((r for r in ordered if r["tW"] > t), key=lambda r: r["tW"], default=None)
        pos = [(q["id"], t - q["tW"], (q["tEnd"] - t) if q["tEnd"] else None, q["end"]) for q in fl]
        print("  gate %7d before=%s wrote=%s | in flight (id, ms since W, ms to end, end)=%s | prev ended id %s (%s@%s, %+d ms) | next W id %s @%s (%+d ms)" % (
            t, g[1], g[2], pos, prev and prev["id"], prev and prev["end"], prev and prev["tEnd"], (t - prev["tEnd"]) if prev else 0,
            nxt and nxt["id"], nxt and nxt["tW"], (nxt["tW"] - t) if nxt else 0))
    for tr in d["triggers"]:
        print("  trigger", json.dumps({k: v for k, v in tr.items() if k != "stats"}))
        if "t_ms" not in tr:
            continue
        t = tr["t_ms"]
        rid = tr["open_request"]
        q = reqs[rid]
        print("     open request %d W@%d end=%s@%s (%+d ms after trigger); lane at trigger (phys)=%s" % (rid, q["tW"], q["end"], q["tEnd"], (q["tEnd"] - t) if q["tEnd"] else 0, mr.lane_state_at(phys, t)))
        ev = [p_ for p_ in phys if t - 3000 <= p_[0] <= t + 6000]
        print("     phys lane changes [t-3s, t+6s]:", [(x[0], x[3]) for x in ev])
        rq = [(r["id"], r["tW"], r["end"], r["tEnd"]) for r in ordered if (t - 4000 <= r["tW"] <= t + 6000)]
        print("     requests entering [t-4s, t+6s]:", rq)
        ff = [f[0] for f in raw["fires"] if t - 5000 <= f[0] <= t + 6000]
        print("     fires near:", ff)
    t0 = raw["t0"]
    tz = datetime.timezone(datetime.timedelta(hours=-5))
    print("  raw.t0 ->", datetime.datetime.fromtimestamp(t0 / 1000, tz).strftime("%H:%M:%S.%f")[:-3])
    for lab, ms in [("clamp gate write", [g for g in raw["gate"] if g[2] is True][0][0])] + [("gate after clamp", g[0]) for g in raw["gate"] if g[0] > [g for g in raw["gate"] if g[2] is True][0][0]] + [("idle start", d["idle_window_ms"][0])]:
        print("   %-18s page %8d -> wall %s" % (lab, ms, datetime.datetime.fromtimestamp((t0 + ms) / 1000, tz).strftime("%H:%M:%S.%f")[:-3]))
