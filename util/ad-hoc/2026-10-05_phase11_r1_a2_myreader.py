#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, a2/myreader.py
# Written by Lane 11-A2 (measurement re-creation, raw-transcript-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens; py/unused-local-variable: a binding nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-A2 independent reader for the F-058 census v2 transcripts (raw.req / raw.lane / raw.fires / raw.gate).

Written from the shim's JavaScript alone:
  * every record's time is the dispatch's ENTRY time (Date.now()-T0 taken before orig.apply);
  * records are PUSHED after orig.apply returns, so a nested dispatch is pushed BEFORE its parent (post-order);
  * a lane record is pushed by EVERY dispatch whose span saw a net change, so one physical change appears once
    per nesting level: the innermost (a thunk -> flat=[] -> types '') and then each enclosing dispatch;
  * a thunk logs types '' (flatten() skips non-objects), so the running= sideUpdate shows as ''.
Physical changes are therefore the '' records (plus SET_LAYOUT); every other lane record must be a duplicate.
"""
import json
import math
import statistics
import sys
from collections import Counter

FIRE_OUTER = "Callbacks.RemoveWatched+Callbacks.AddExecuted"


def pct_nearest(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    k = max(1, math.ceil(p * len(xs)))
    return xs[k - 1]


def pct_linear(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    pos = (len(xs) - 1) * p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def summ(xs):
    xs = sorted(xs)
    if not xs:
        return "n=0"
    return "n=%d min=%s median=%s (lo=%s hi=%s idx[n//2]=%s) p90_nearest=%s p90_linear=%.1f max=%s" % (
        len(xs), xs[0], statistics.median(xs), xs[(len(xs) - 1) // 2], xs[len(xs) // 2], xs[len(xs) // 2],
        pct_nearest(xs, 0.9), pct_linear(xs, 0.9), xs[-1])


def requests(raw):
    recs = {}
    for t, k, i, props in raw["req"]:
        r = recs.setdefault(i, {"id": i, "W": [], "A": [], "X": [], "R": []})
        r[k].append((t, props))
    bad = []
    out = {}
    for i, r in recs.items():
        if len(r["W"]) != 1 or len(r["A"]) + len(r["X"]) > 1:
            bad.append((i, {k: len(v) for k, v in r.items() if k != "id"}))
        tW = r["W"][0][0] if r["W"] else None
        if r["A"]:
            end, tEnd, props = "A", r["A"][0][0], r["A"][0][1]
        elif r["X"]:
            end, tEnd, props = "X", r["X"][0][0], 0
        else:
            end, tEnd, props = None, None, None
        out[i] = {"id": i, "tW": tW, "end": end, "tEnd": tEnd, "props": props}
    return out, bad


def physical(raw):
    """Return physical lane changes [(t, before, after, kind, idx)] and a duplicate-check report."""
    L = raw["lane"]
    fires = {f[0] for f in raw["fires"]}
    gate = {}
    for t, b, v in raw["gate"]:
        gate.setdefault(t, []).append((b, v))
    phys = []
    problems = []
    # duplicate check: each non-'' non-SET_LAYOUT record must sit directly above a chain ending in a '' record
    for j, (t, b, a, ty) in enumerate(L):
        if ty == "" or ty == "SET_LAYOUT":
            continue
        k = j - 1
        while k >= 0 and L[k][3] not in ("", "SET_LAYOUT"):
            if (L[k][1], L[k][2]) != (b, a) or L[k][0] < t:
                break
            k -= 1
        ok = k >= 0 and L[k][3] == "" and (L[k][1], L[k][2]) == (b, a) and L[k][0] >= t and L[k][0] - t <= 1000
        # all records between k and j must be same-direction duplicates
        ok = ok and all((L[m][1], L[m][2]) == (b, a) and L[m][0] >= t for m in range(k + 1, j))
        if not ok:
            problems.append((j, L[j], L[k] if k >= 0 else None))
    for j, (t, b, a, ty) in enumerate(L):
        if ty == "SET_LAYOUT":
            phys.append([t, b, a, "layout", j, t])
        elif ty == "":
            kind = None
            # what encloses this innermost change? the next record up the chain
            nxt = L[j + 1] if j + 1 < len(L) else None
            encl_t = None
            if nxt is not None and nxt[3] == FIRE_OUTER and (nxt[1], nxt[2]) == (b, a) and nxt[0] <= t:
                encl_t = nxt[0]
            if b is True and a is False:
                if encl_t is not None and encl_t in fires:
                    kind = "fire"
                elif encl_t is not None and encl_t in gate and any(v is False for _, v in gate[encl_t]):
                    kind = "gate_off"
                else:
                    kind = "off"
            elif b is False and a is True:
                if encl_t is not None and encl_t in gate and any(v is True for _, v in gate[encl_t]):
                    kind = "gate_on"
                else:
                    kind = "on"
            else:
                kind = "?"
            phys.append([t, b, a, kind, j, encl_t])
    phys.sort(key=lambda r: (r[0], r[4]))
    alt_breaks = [(p, q) for p, q in zip(phys, phys[1:]) if p[2] != q[1]]
    return phys, problems, alt_breaks


def lane_state_at(phys, t):
    """Lane disabled value just before time t (strictly: changes with time < t applied)."""
    s = None
    for r in phys:
        if r[0] < t:
            s = r[2]
        else:
            break
    return s


def enabled_ms(phys, lo, hi):
    """ms in [lo, hi) the lane was ENABLED (disabled is False)."""
    tot = 0
    s = lane_state_at(phys, lo)
    cur = lo
    for r in phys:
        if r[0] < lo:
            continue
        if r[0] >= hi:
            break
        if s is False:
            tot += r[0] - cur
        cur = r[0]
        s = r[2]
    if s is False:
        tot += hi - cur
    return tot


def in_flight(reqs, t):
    return [r for r in reqs.values() if r["tW"] is not None and r["tW"] <= t and (r["tEnd"] is None or t < r["tEnd"])]


def analyse(path, label):
    with open(path) as fh:
        d = json.load(fh)
    raw = d["raw"]
    print("=" * 100)
    print(label, path, "served_sha", d["served_sha"][:8], "dispatches", raw["dispatches"], "errors", len(raw["errors"]))
    reqs, bad = requests(raw)
    print("request-record anomalies (W!=1 or >1 end):", bad)
    phys, problems, alt = physical(raw)
    print("lane records", len(raw["lane"]), "physical", len(phys), "duplicate-check problems", len(problems), "alternation breaks", len(alt))
    for p in problems[:10]:
        print("   PROBLEM", p)
    for p in alt[:10]:
        print("   ALT", p)
    print("physical kinds", Counter(p[3] for p in phys))
    fires = raw["fires"]
    gates = raw["gate"]
    # fire/gate mapping completeness
    fire_mapped = Counter(p[5] for p in phys if p[3] == "fire")
    print("fires", len(fires), "mapped to physical", sum(1 for f in fires if fire_mapped.get(f[0])), "fire 'before' values", Counter(f[1] for f in fires), "sinceBefore", Counter(f[2] for f in fires))
    print("gate writes", gates)

    # ---- item 1
    ordered = sorted(reqs.values(), key=lambda r: r["tW"])
    ans = [r for r in ordered if r["end"] == "A"]
    ev = [r for r in ordered if r["end"] == "X"]
    op = [r for r in ordered if r["end"] is None]
    print("\n[1] requests total=%d answered=%d evicted=%d open=%d answered_with_props=%d" % (len(ordered), len(ans), len(ev), len(op), sum(1 for r in ans if r["props"])))
    print("    open:", [(r["id"], r["tW"]) for r in op])
    ift = [r["tEnd"] - r["tW"] for r in ordered if r["end"]]
    print("    in-flight all ended:", summ(ift))
    print("    in-flight answered :", summ([r["tEnd"] - r["tW"] for r in ans]))
    print("    in-flight evicted  :", summ([r["tEnd"] - r["tW"] for r in ev]))
    ids_by_entry = [r["id"] for r in ordered]
    print("    ids in entry order == numeric order:", ids_by_entry == sorted(ids_by_entry))

    # ---- item 2
    runs = []
    cur = []
    for idx, r in enumerate(ordered):
        if r["end"] == "X":
            cur.append(idx)
        else:
            if cur:
                runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    a_times = sorted(r["tEnd"] for r in ans)
    print("\n[2] eviction runs:", len(runs), "lengths", [len(x) for x in runs])
    run_gaps = []
    for x in runs:
        first, last = ordered[x[0]], ordered[x[-1]]
        prev_a = max((t for t in a_times if t < first["tEnd"]), default=None)
        next_a = min((t for t in a_times if t > last["tEnd"]), default=None)
        # entry-order neighbours
        pa = ordered[x[0] - 1] if x[0] > 0 else None
        na = ordered[x[-1] + 1] if x[-1] + 1 < len(ordered) else None
        gap = (next_a - prev_a) if (prev_a is not None and next_a is not None) else None
        run_gaps.append(gap)
        print("    run ids %s len=%d  X times %s  prevA=%s nextA=%s gap=%s | entry-neighbours prev id %s (%s@%s) next id %s (%s@%s)" % (
            [ordered[i]["id"] for i in x], len(x), [ordered[i]["tEnd"] for i in x], prev_a, next_a, gap,
            pa and pa["id"], pa and pa["end"], pa and pa["tEnd"], na and na["id"], na and na["end"], na and na["tEnd"]))
    agaps = [b - a for a, b in zip(a_times, a_times[1:])]
    print("    gaps between consecutive applied answers:", summ(agaps))

    # ---- item 3
    eps = []
    enab = []
    for p, q in zip(phys, phys[1:]):
        if p[2] is True and q[1] is True:
            eps.append((q[0] - p[0], p[3], q[3], p[0]))
        if p[2] is False and q[1] is False and p[3] != "layout":
            enab.append((q[0] - p[0], p[3], q[3], p[0]))
    print("\n[3] disabled episodes:", summ([e[0] for e in eps]))
    print("    disabled episodes excl. gate clamp:", summ([e[0] for e in eps if e[1] != "gate_on"]))
    print("    longest disabled episodes:", sorted(eps, reverse=True)[:4])
    print("    enabled intervals between episodes:", summ([e[0] for e in enab]))
    print("    enabled-interval end kinds:", Counter(e[2] for e in enab), "start kinds:", Counter(e[1] for e in enab))
    # what is the lane state between episodes: count of in-flight requests during enabled intervals
    busy_enabled = [e for e in enab if any(r["tW"] <= e[3] and (r["tEnd"] is None or r["tEnd"] > e[3]) for r in reqs.values())]
    print("    enabled intervals that START while a request is in flight:", len(busy_enabled))

    # ---- item 4
    print("\n[4] watchdog fires (t, episode_age_ms, in_flight ids, enabled_ms_in_prev_30s, lane_before_from_phys)")
    fire_rows = []
    for f in fires:
        t = f[0]
        last_on = max((p for p in phys if p[0] < t and p[2] is True and p[1] is False), key=lambda p: (p[0], p[4]), default=None)
        age = t - last_on[0] if last_on else None
        fl = in_flight(reqs, t)
        en = enabled_ms(phys, t - 30000, t)
        st = lane_state_at(phys, t)
        fire_rows.append((t, age, [r["id"] for r in fl], en, st))
        print("    ", t, age, [r["id"] for r in fl], en, st, "last_on_kind", last_on and last_on[3])
    ens = [r[3] for r in fire_rows]
    print("    enabled-ms range:", min(ens), max(ens), " ages:", summ([r[1] for r in fire_rows]))
    lane_last = max(x[0] for x in raw["lane"])
    req_last = max(x[0] for x in raw["req"])
    lo, hi = d["idle_window_ms"]
    idle_f = [f for f in fires if lo <= f[0] < hi]
    print("    fires=%d; last record t=%d (lane) %d (req); idle window [%s,%s) fires=%d -> %.1f/h idle" % (len(fires), lane_last, req_last, lo, hi, len(idle_f), len(idle_f) / ((hi - lo) / 3.6e6)))
    print("    rate over [0, last record]: %.2f/h; over [settle end=baseline start %s, last record]: %.2f/h" % (
        len(fires) / (max(lane_last, req_last) / 3.6e6), d["baseline_window_ms"][0],
        len([f for f in fires if f[0] >= d["baseline_window_ms"][0]]) / ((max(lane_last, req_last) - d["baseline_window_ms"][0]) / 3.6e6)))
    return d, reqs, phys, ordered, fire_rows


if __name__ == "__main__":
    for p, lab in zip(sys.argv[1::2], sys.argv[2::2]):
        analyse(p, lab)
