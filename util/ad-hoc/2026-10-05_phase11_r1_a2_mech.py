#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, a2/mech.py
# Written by Lane 11-A2 (measurement re-creation, raw-transcript-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-A2: mechanism claim (item 5), race numbers (item 6), gate/T-apply timing (item 7). Uses myreader.py."""
import importlib.util
import sys
from collections import Counter

spec = importlib.util.spec_from_file_location("myreader", "/tmp/tmp.AFzDbAMY9I/myreader.py")
mr = importlib.util.module_from_spec(spec)
sys.modules["myreader"] = mr
spec.loader.exec_module(mr)

import io, contextlib


def load(path):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        d, reqs, phys, ordered, fire_rows = mr.analyse(path, "x")
    return d, reqs, phys, ordered, fire_rows


def mech(path, label):
    d, reqs, phys, ordered, fire_rows = load(path)
    print("=" * 100)
    print(label)
    offs = [p for p in phys if p[3] == "off"]
    ons = [p for p in phys if p[3] == "on"]
    # --- every 'on' should precede a W by a few ms
    wt = sorted((r["tW"], r["id"]) for r in ordered)
    on_gap = []
    unmatched_on = []
    for p in ons:
        nxt = min((w for w in wt if w[0] >= p[0]), default=None)
        if nxt is None or nxt[0] - p[0] > 50:
            unmatched_on.append(p)
        else:
            on_gap.append(nxt[0] - p[0])
    print("running.on -> W gap:", mr.summ(on_gap), "unmatched on:", unmatched_on)
    # --- classify each 'off' release by the requests in flight at that instant
    rows = []
    for p in offs:
        t = p[0]
        fl = mr.in_flight(reqs, t)
        rows.append((t, fl))
    nfl = Counter(len(fl) for _, fl in rows)
    print("off releases:", len(offs), "in-flight count at release:", dict(nfl))
    # own release candidates: release during an ANSWERED request's flight; gap to its A
    own_gaps = []
    late_like = []
    no_flight = []
    for t, fl in rows:
        if not fl:
            no_flight.append(t)
            continue
        assert len(fl) == 1, (t, fl)
        q = fl[0]
        gap = q["tEnd"] - t if q["tEnd"] is not None else None
        if q["end"] == "A":
            own_gaps.append((gap, t, q["id"]))
        else:
            late_like.append((gap, t, q["id"], q["end"]))
    print("releases with no request in flight:", no_flight)
    g = sorted(x[0] for x in own_gaps)
    print("release during an ANSWERED request's flight -> gap to its A:", mr.summ(g))
    print("   gaps > 100 ms:", sorted([x for x in own_gaps if x[0] > 100]))
    print("release during an EVICTED (or open) request's flight -> gap to its end:", sorted(late_like))

    # --- per evicted request: releases after its X while a NEWER request is in flight
    ev = [r for r in ordered if r["end"] == "X"]
    print("\nPer evicted request e: releases after X(e) while a newer request is in flight, before that request's end")
    succ_evicted = 0
    late_list = []
    for e in ev:
        cands = []
        for t, fl in rows:
            if t <= e["tEnd"] or not fl:
                continue
            q = fl[0]
            if q["tW"] > e["tW"]:
                cands.append((t, q["id"], q["end"], q["tEnd"]))
        # the immediate successor (next request by entry)
        nxt = [r for r in ordered if r["tW"] > e["tW"]]
        s0 = nxt[0] if nxt else None
        # releases in the window (X(e), end of the immediate successor]
        win = [c for c in cands if s0 and c[0] <= (s0["tEnd"] if s0["tEnd"] is not None else 1e12) and c[1] == s0["id"]]
        # classify: a release during s0's flight whose gap to s0's A is <=100 ms is s0's own
        own = [c for c in win if c[2] == "A" and c[3] - c[0] <= 100]
        late = [c for c in win if c not in own]
        late_list.append((e, s0, late, own))
        print("  e=%d X@%d  succ=%s(%s W@%s end@%s)  late=%s own_in_window=%s" % (
            e["id"], e["tEnd"], s0 and s0["id"], s0 and s0["end"], s0 and s0["tW"], s0 and s0["tEnd"], [(c[0], round((c[3] - c[0]) if c[3] else -1)) for c in late], [(c[0], c[3] - c[0]) for c in own]))
        if s0 and s0["end"] == "X":
            succ_evicted += 1
    exactly_one = sum(1 for e, s0, late, own in late_list if len(late) == 1)
    print("evicted=%d with exactly one late release in successor's flight=%d; successors evicted=%d" % (len(ev), exactly_one, succ_evicted))
    # gap of late release to successor end, split by successor fate
    for kind in ("X", "A"):
        gs = [(s0["tEnd"] - late[0][0]) for e, s0, late, own in late_list if late and s0["end"] == kind]
        print("   late release -> successor's %s gap:" % kind, mr.summ(gs), sorted(gs))
    # late release relative to e's eviction
    gx = [(late[0][0] - e["tEnd"]) for e, s0, late, own in late_list if late]
    print("   e's X -> its late release:", mr.summ(gx))
    # e's W -> its late release (response time of evicted request)
    gw = [(late[0][0] - e["tW"]) for e, s0, late, own in late_list if late]
    print("   e's W -> its late release (implied server time):", mr.summ(gw))
    # releases unaccounted: off releases neither own (<=100ms before A of in-flight answered) nor assigned late
    assigned = {late[0][0] for e, s0, late, own in late_list if late}
    own_set = {t for gap, t, qid in own_gaps if gap <= 100}
    rest = [t for t, fl in rows if t not in assigned and t not in own_set]
    print("   off releases neither own (<=100ms) nor assigned late:", rest)
    # answered requests whose own release is NOT visible -> why?
    ans = [r for r in ordered if r["end"] == "A"]
    own_ids = {qid for gap, t, qid in own_gaps if gap <= 100}
    invisible = [r for r in ans if r["id"] not in own_ids]
    print("   answered requests with no visible own release: %d" % len(invisible))
    why = []
    fires = d["raw"]["fires"]
    gates = d["raw"]["gate"]
    for r in invisible:
        f_in = [f[0] for f in fires if r["tW"] <= f[0] < r["tEnd"]]
        g_in = [g for g in gates if r["tW"] <= g[0] < r["tEnd"]]
        l_in = [t for t in assigned if r["tW"] <= t < r["tEnd"]]
        why.append((r["id"], "fire" if f_in else "", "gate" if g_in else "", "late" if l_in else ""))
    print("   reasons:", Counter(w[1:] for w in why))
    print("   detail (no reason):", [w for w in why if not any(w[1:])])
    return d, reqs, phys, ordered, fire_rows, late_list


def race(d, reqs, phys, ordered, fire_rows, late_list, label):
    print("\n[6]", label, "fires: in-flight request fate")
    late_by_e = {e["id"]: late for e, s0, late, own in late_list}
    ev_rows, ans_rows = [], []
    for t, age, fl, en, st in fire_rows:
        q = reqs[fl[0]]
        if q["end"] == "X":
            lr = late_by_e.get(q["id"])
            ev_rows.append((t, q["id"], q["tEnd"] - t, (lr[0][0] - t) if lr else None))
        else:
            ans_rows.append((t, q["id"], q["tEnd"] - t if q["tEnd"] else None))
    print("  evicting fires (t, id, fire->X ms, fire->response landed (late release) ms):", ev_rows)
    print("  other fires (t, id, fire->A ms):", ans_rows)
    return ev_rows, ans_rows


if __name__ == "__main__":
    allr = {}
    for p, lab in zip(sys.argv[1::2], sys.argv[2::2]):
        out = mech(p, lab)
        allr[lab] = (out, race(*out, lab))
    # combined
    ev_all = [r for lab in allr for r in allr[lab][1][0]]
    an_all = [r for lab in allr for r in allr[lab][1][1]]
    print("\nCOMBINED evicting fires:", len(ev_all), "fire->X:", mr.summ([r[2] for r in ev_all]), "fire->landed:", mr.summ([r[3] for r in ev_all if r[3] is not None]))
    print("COMBINED other fires:", len(an_all), "fire->A:", mr.summ([r[2] for r in an_all]))
