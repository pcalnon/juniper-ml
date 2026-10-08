# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R2A.sffLXI/myreader.py
# Written by Lane 11-R2A (measurement re-creation, on round 1's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens; py/unused-local-variable: a binding nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R2A's own reader of the census v2 shim's records (written from the shim's JS, not from the repo's readers).

Shim facts used:
  * every record carries its dispatch's ENTRY time (now = Date.now()-T0 taken before orig.apply) and is pushed AFTER
    orig.apply returns, so a nested (wrapped) dispatch's record is pushed BEFORE its encloser's, and the encloser
    re-logs the same lane change at its own earlier entry time.
  * lane records: [t, before, after, types]; pushed only if after !== before; types '' for a thunk.
  * req records: [t, kind, id, props]; W at AddWatched; A = RemoveWatched+AddExecuted in one action tree; X = removed
    without either; R = pruned and re-added (still in flight).
  * fires: [t, before, since]; gate: [t, before, value].
Innermost record of each chain: walk lane records in PUSH order, keeping the current state; a record whose `before`
equals the current state is a new change (the innermost that saw it); a record whose `before` differs is an encloser
re-logging a change already seen. Cross-checked against a type-based selection ('' or SET_LAYOUT).
"""
import json
import statistics
import sys


def load(p):
    with open(p) as fh:
        return json.load(fh)


def requests(raw):
    req, anomalies = {}, []
    for t, k, i, props in raw["req"]:
        r = req.setdefault(i, {"id": i, "W": None, "end": None, "tEnd": None, "props": None})
        if k == "W":
            if r["W"] is not None:
                anomalies.append(("dupW", i))
            r["W"] = t
        elif k == "R":
            continue
        else:
            if r["end"] is not None:
                anomalies.append(("dupEnd", i))
            r["end"], r["tEnd"], r["props"] = k, t, props
    return req, anomalies


def innermost_state_machine(lane):
    cur, changes, dups, anomalies = None, [], [], []
    for idx, (t, b, a, ty) in enumerate(lane):
        if not changes or b == cur:
            changes.append({"t": t, "b": b, "a": a, "ty": ty, "idx": idx, "enc": []})
            cur = a
        else:
            if a != cur:
                anomalies.append(("dup-after-mismatch", idx, t))
            # the encloser re-logs the most recent change(s); attach to the latest accepted change
            changes[-1]["enc"].append(t)
            if t > changes[-1]["t"]:
                anomalies.append(("encloser-later-than-inner", idx, t, changes[-1]["t"]))
            dups.append(idx)
    return changes, dups, anomalies


def innermost_by_type(lane):
    return [{"t": t, "b": b, "a": a, "ty": ty, "idx": i} for i, (t, b, a, ty) in enumerate(lane) if ty in ("", "SET_LAYOUT")]


def timeline_of(changes):
    return [(c["t"], c["a"]) for c in changes]


def state_at(tl, t):
    s = None
    for x, v in tl:
        if x <= t:
            s = v
        else:
            break
    return s


def enabled_ms(tl, lo, hi):
    # lane value is `disabled`; enabled == (value is False)
    s = state_at(tl, lo)
    total, prev = 0, lo
    for x, v in tl:
        if x <= lo:
            continue
        if x >= hi:
            break
        if s is False:
            total += x - prev
        prev, s = x, v
    if s is False:
        total += hi - prev
    return total


def episodes(tl):
    out, start = [], None
    for x, v in tl:
        if v is True and start is None:
            start = x
        elif v is False and start is not None:
            out.append((start, x, x - start))
            start = None
    return out


def main(paths):
    for p in paths:
        d = load(p)
        raw = d["raw"]
        print("=" * 100)
        print(p, "served", d["served_sha"][:8])
        req, ra = requests(raw)
        ids = sorted(req)
        ans = [i for i in ids if req[i]["end"] == "A"]
        ev = [i for i in ids if req[i]["end"] == "X"]
        op = [i for i in ids if req[i]["end"] is None]
        print(f"requests {len(ids)} answered {len(ans)} evicted {len(ev)} open {len(op)}; req anomalies {ra}")
        # entry order equals id order?
        byW = sorted((i for i in ids if req[i]["W"] is not None), key=lambda i: req[i]["W"])
        print("entry order == id order:", byW == sorted(byW))
        sm, dups, an = innermost_state_machine(raw["lane"])
        ty = innermost_by_type(raw["lane"])
        same = [(c["t"], c["b"], c["a"]) for c in sm] == [(c["t"], c["b"], c["a"]) for c in ty]
        alt_breaks = sum(1 for x, y in zip(ty, ty[1:]) if y["b"] != x["a"])
        print(f"lane records {len(raw['lane'])}; state-machine innermost {len(sm)}, dups {len(dups)}, anomalies {an[:5]} (n={len(an)}); type-based {len(ty)}; identical lists: {same}; type-based alternation breaks {alt_breaks}")
        # time order of innermost == push order?
        print("innermost push order is time-monotone:", all(x["t"] <= y["t"] for x, y in zip(sm, sm[1:])))
        # backdating: inner t minus earliest encloser t
        back = [c["t"] - min(c["enc"]) for c in sm if c["enc"]]
        print(f"changes with enclosers {len(back)}; backdate (inner - earliest encloser) median {statistics.median(back)} max {max(back)}; >5ms {sum(1 for b in back if b > 5)}; >100ms {sum(1 for b in back if b > 100)}")
        dis_back = [c["t"] - min(c["enc"]) for c in sm if c["enc"] and c["a"] is True]
        print(f"  nested DISABLES only: n={len(dis_back)} median {statistics.median(dis_back)} max {max(dis_back)}")
        tl = timeline_of(sm)
        # old timeline (enclosing records): last record's after at each ms, sorted by t
        by_t = {}
        for t, b, a, tyy in raw["lane"]:
            by_t[t] = a
        old_tl = sorted(by_t.items())
        eps = episodes(tl)
        lens = [e[2] for e in eps]
        old_lens = [e[2] for e in episodes(old_tl)]
        print(f"disabled episodes {len(lens)}: statistics.median {statistics.median(lens)}, upper median {sorted(lens)[len(lens)//2]}, lower {sorted(lens)[(len(lens)-1)//2]}; max {max(lens)}")
        print(f"  old (enclosing) timeline: episodes {len(old_lens)} statistics.median {statistics.median(old_lens)} upper {sorted(old_lens)[len(old_lens)//2]}")
        en_eps = []
        prev_end = None
        for (s0, s1, L) in eps:
            if prev_end is not None:
                en_eps.append(s0 - prev_end)
            prev_end = s1
        print(f"  enabled stretches between episodes: median {statistics.median(en_eps)}; min {min(en_eps)}")
        # fires
        def in_flight(t):
            live = [i for i in ids if req[i]["W"] is not None and req[i]["W"] <= t and (req[i]["tEnd"] is None or req[i]["tEnd"] > t)]
            return live
        fires = raw["fires"]
        f_en, f_age, f_en_old, f_age_old = [], [], [], []
        for t, before, since in fires:
            f_en.append(enabled_ms(tl, t - 30000, t))
            f_en_old.append(enabled_ms(old_tl, t - 30000, t))
            last_on = max(x for x, v in tl if x < t and v is True)
            # ensure state just before t is True
            assert state_at(tl, t - 1) is True, (t,)
            f_age.append(t - last_on)
            last_on_old = max(x for x, v in old_tl if x < t and v is True)
            f_age_old.append(t - last_on_old)
            assert len(in_flight(t)) >= 1
        print(f"fires {len(fires)}: enabled-in-prior-30s min {min(f_en)} max {max(f_en)} (old {min(f_en_old)}-{max(f_en_old)}); episode age min {min(f_age)} max {max(f_age)} (old {min(f_age_old)}-{max(f_age_old)}); in flight at all: {all(len(in_flight(t)) >= 1 for t,_,_ in fires)}; third field all null: {all(s is None for _,_,s in fires)}")
        # releases (innermost T->F not fire/gate writes)
        writes = [t for t, _, _ in fires] + [t for t, b, v in raw["gate"] if v is False]
        def is_write(t):
            return any(abs(t - w) <= 2 for w in writes)
        rel = [c["t"] for c in sm if c["b"] is True and c["a"] is False and not is_write(c["t"])]
        print(f"releases {len(rel)}")
        # own: release followed by in-flight request's A within 100 ms
        own, other = [], []
        for t in rel:
            live = in_flight(t)
            cur = live[-1] if live else None
            if cur is not None and req[cur]["end"] == "A" and 0 <= req[cur]["tEnd"] - t <= 100:
                own.append(req[cur]["tEnd"] - t)
            else:
                other.append((t, cur))
        print(f"  own {len(own)} gap {min(own)}-{max(own)}; non-own {len(other)}")
        # pair each evicted request k with the unique non-own release in (X_k, end of successor)
        late = {}
        for k in ev:
            succ = k + 1
            lo = req[k]["tEnd"]
            hi = req[succ]["tEnd"] if succ in req and req[succ]["tEnd"] is not None else 10**12
            cands = [t for t, cur in other if lo <= t < hi]
            late[k] = cands
        print(f"  evicted {len(ev)}; with exactly one non-own release in (X_k, end_k+1): {sum(1 for k in ev if len(late[k]) == 1)}; non-own outside all intervals: {len(other) - sum(len(v) for v in late.values())}")
        landed = {}
        for k in ans:
            landed[k] = req[k]["tEnd"]
        for k in ev:
            if len(late[k]) == 1:
                landed[k] = late[k][0]
        fl_ans = [req[k]["tEnd"] - req[k]["W"] for k in ans]
        fl_ev = [landed[k] - req[k]["W"] for k in ev if k in landed]
        print(f"  flight answered: median {statistics.median(fl_ans)} max {max(fl_ans)}; evicted W->late release: {min(fl_ev)}-{max(fl_ev)}; longest W->landing {max(fl_ans + fl_ev)}")
        succ_to_ans = [req[k + 1]["tEnd"] - late[k][0] for k in ev if req[k + 1]["end"] == "A"]
        print(f"  late release -> successor's answer (answered successors {len(succ_to_ans)}): {sorted(succ_to_ans)}; successors evicted {sum(1 for k in ev if req[k+1]['end']=='X')}")
        # eviction runs
        runs, cur_run = [], []
        for i in ids:
            if req[i]["end"] == "X":
                cur_run.append(i)
            else:
                if cur_run:
                    runs.append(cur_run)
                cur_run = []
        if cur_run:
            runs.append(cur_run)
        print(f"  eviction runs: {[len(r) for r in runs]} starting at reqs {[r[0] for r in runs]}")
        # re-enables mid-request: fires + gate T->F with a request in flight
        reen = [("fire", t) for t, b, s in fires] + [("gate", t) for t, b, v in raw["gate"] if b is True and v is False]
        rows = []
        for kind, t in sorted(reen, key=lambda x: x[1]):
            live = in_flight(t)
            if not live:
                rows.append((kind, t, None))
                continue
            k = live[-1]
            nxt = [i for i in ids if req[i]["W"] is not None and req[i]["W"] > t]
            n1 = min(nxt, key=lambda i: req[i]["W"]) if nxt else None
            rows.append((kind, t, {"k": k, "end": req[k]["end"], "land": landed.get(k), "land_dt": (landed.get(k) - t) if landed.get(k) is not None else None, "next": n1, "next_dt": req[n1]["W"] - t if n1 else None}))
        mid = [r for r in rows if r[2] is not None]
        notmid = [r for r in rows if r[2] is None]
        print(f"re-enables: {len(rows)} total; mid-request {len(mid)} (fires {sum(1 for r in mid if r[0]=='fire')}, gate {sum(1 for r in mid if r[0]=='gate')}); not mid-request {[(r[0], r[1]) for r in notmid]}")
        evicting = [r for r in mid if r[2]["end"] == "X"]
        print(f"  evicting {len(evicting)}: {[(r[0], r[1], r[2]['k']) for r in evicting]}")
        gt1 = [r for r in mid if r[2]["land_dt"] is not None and r[2]["land_dt"] > 1000]
        print(f"  landing > 1000 ms after re-enable: {len(gt1)}; of which evicting {sum(1 for r in gt1 if r[2]['end']=='X')}, non-evicting {sum(1 for r in gt1 if r[2]['end']=='A')}; non-evicting landing dts {sorted(r[2]['land_dt'] for r in gt1 if r[2]['end']=='A')}")
        nd = [r[2]["next_dt"] for r in mid]
        print(f"  next request after re-enable: min {min(nd)} max {max(nd)}; fires only {min(r[2]['next_dt'] for r in mid if r[0]=='fire')}-{max(r[2]['next_dt'] for r in mid if r[0]=='fire')}; gate only {[r[2]['next_dt'] for r in mid if r[0]=='gate']}")
        print(f"  evicting fire->X (next entry) {sorted(req[r[2]['k']]['tEnd'] - r[1] for r in evicting if r[0]=='fire')}; fire->landing {sorted(r[2]['land_dt'] for r in evicting if r[0]=='fire')}")
        print(f"  non-evicting fires -> answer {min(r[2]['land_dt'] for r in mid if r[0]=='fire' and r[2]['end']=='A')}-{max(r[2]['land_dt'] for r in mid if r[0]=='fire' and r[2]['end']=='A')}")
        for r in mid:
            if r[0] == "gate":
                print("   gate mid-request:", r[1], r[2])
        # fire gaps
        ft = [t for t, _, _ in fires]
        gaps = [b - a for a, b in zip(ft, ft[1:])]
        devs = [abs(g - 5000 * round(g / 5000)) for g in gaps]
        print(f"  fire gaps {len(gaps)}: min {min(gaps)}; devs from k*5000: {sorted(devs)}")
        globals().setdefault("ALLDEV", []).extend(devs)
        globals().setdefault("ALLBACK", []).extend(back)
        globals().setdefault("ALLDISBACK", []).extend(dis_back)
    devs = ALLDEV
    print("=" * 100)
    print(f"ALL fire gaps {len(devs)}: <=300 ms {sum(1 for x in devs if x <= 300)}; <=750 {sum(1 for x in devs if x <= 750)}; >750 {[x for x in devs if x > 750]}")
    print(f"ALL backdates n={len(ALLBACK)} median {statistics.median(ALLBACK)} max {max(ALLBACK)}; nested disables n={len(ALLDISBACK)} median {statistics.median(ALLDISBACK)}")


if __name__ == "__main__":
    main(sys.argv[1:])
