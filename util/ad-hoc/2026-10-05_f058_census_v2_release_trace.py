#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-05
# Status      : ad-hoc — investigation; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Read F-CANOPY-058's MECHANISM, not only its signature, out of a ``2026-10-04_f058_census_v2_live.py`` transcript.

A run of consecutive evictions after one re-enable is F-CANOPY-058's signature. Its mechanism is narrower: an
EVICTED request's late completion releases the ``running=`` guard (``completeJob()`` dispatches ``runningOff``
whatever became of the request), so the lane is re-enabled UNDER ITS SUCCESSOR, ticks, and evicts that one too.
This reads that release directly, one request at a time, and it checks the watchdog's fires against the lane's
own timeline.

How the transcript is read (``…_shim.py`` wraps ``store.dispatch``):

* A dispatch that changes the lane's ``disabled`` is logged ``[t, before, after, types]``, ``t`` being the
  dispatch's ENTRY time. Observers run inside an outer dispatch, so a thunk (``types`` empty: ``running=``'s
  ``sideUpdate``, or a clientside write) is logged inside the outer ``Callbacks.*`` dispatch that ran it: first,
  at its own time, and then again by the outer dispatch at the outer's earlier entry time. The lane's STATE is
  read from the innermost records only (``lane_timeline``).
* A RELEASE is a thunk record ``True -> False`` that is not a watchdog fire or a gate write. Each of those writes
  is logged both as a thunk and as its ``AddExecuted``, sometimes a millisecond apart (three of the 13 fires in
  the 2026-10-05 run), so a thunk within ``--write-ms`` of a fire or of a gate write of ``false`` is that write.
* A request's OWN release precedes its ``A`` (``AddExecuted``) by tens of milliseconds, the same response being
  taken after ``completeJob()``: in the two 2026-10-05 runs, 273 own releases 38-54 ms before their ``A``, and
  276 at 13-89 ms. A release with no ``A`` of the in-flight request within ``--own-ms`` after it is assigned to
  the evicted request whose SUCCESSOR is the request in flight, if that request's eviction precedes the release:
  its response landing, discarded, and re-enabling the lane under its successor. Any other release is reported
  ``unassigned``. The successor's own ``runningOff`` then finds the lane already enabled and logs nothing, so a
  late release can sit hundreds of milliseconds before the successor's ``A`` (433 ms and 731 ms in the first
  run); a 1 s window misread both as the successor's own (the first version of this file). The report prints
  that margin for every late release whose successor was answered.
* Only the first completion to release a disabled lane is logged. An evicted request whose response lands
  AFTER its successor's own release finds the lane enabled and leaves no record; such a request reads
  ``late release: none`` here, which is a limit of the log, not evidence that its completion did not release.
* An evicted request whose response lands after its successor was itself evicted would have its release paired
  with the successor by the rule above, and itself read "none". Every late release is therefore checked for
  other evicted requests of the same eviction run still awaiting a release when it landed; any such release is
  flagged AMBIGUOUS, its pairing a guess (round 2 of Phase 11's review, Lane 11-R2B). There are none in the
  2026-10-05 runs. A lane change logged only by a non-thunk record would be missing from the innermost timeline;
  the report counts alternation breaks and exits 2 if there is any. A disable and the enable after it, both
  logged only so, leave no break and are not caught, and ``--self-test`` does not check for a break (round 3 of
  Phase 11's review, Lanes 11-R3A and 11-R3B). In the 2026-10-05 runs a walk of the records in push order
  finds the same changes as this selection (Lanes 11-R2A and 11-R3A).

What it prints:

  fires      for each watchdog fire: how long the lane had been disabled (the current episode), and how long
             it was ENABLED in the 30 s before (``--strand-ms``). Any enabled time means the lane was not
             continuously disabled for the threshold, so the fire was false by the watchdog's own contract
             (``dashboard_manager.py:2519-2522`` at canopy ``60ae1870``: it "must not re-enable DURING a
             legitimate fetch").
  evictions  for each evicted request: its eviction (``X``), its late release (the response landing) and the
             successor in flight at that release, and whether that successor was evicted in turn.
  counts     releases by kind. ``unassigned`` releases are reported, never hidden.

How it could have come out otherwise: if an evicted request's completion did NOT release the guard, no release
would occur while its successor was in flight except the successor's own, and every row of the ``evictions``
table would read ``late release: none``; a run of evictions would then need a new trigger for each eviction.
A fire on a lane that really was disabled for the whole threshold would read ``enabled in prior 30 s: 0 ms``.
``--self-test`` builds both cases from the transcript itself and checks that this reader reports them, and three
more: one late release dropped, and every late release with an answered successor shifted into that successor's
own window (in each, exactly the affected evictions must change, to "none", and no other pairing may move); and
one release moved into the flight after the next eviction, with that eviction's own release dropped, which must
be flagged AMBIGUOUS.

Usage:
    python3 <this file> <transcript.json> [--own-ms 100] [--strand-ms 30000] [--write-ms 2]
    python3 <this file> <transcript.json> --self-test   # five known-answer mutations; exit 0 only if all pass
"""

import argparse
import bisect
import copy
import json
import sys
from pathlib import Path


def lane_timeline(lane_log):
    """``[(t, disabled)]`` from the INNERMOST record of each nested chain: a thunk (types ``''``) or ``SET_LAYOUT``.

    The shim stamps a record with its dispatch's ENTRY time and pushes it after the dispatch returns. So a change
    made inside a nested thunk is logged first, at the thunk's own entry time, and then again by each enclosing
    dispatch, at that dispatch's EARLIER entry time. Reading the enclosing records backdates the change: by a
    median of about 22 ms and up to 327 ms in the 2026-10-05 runs (round 1 of Phase 11's review, Lane 11-A2; the
    first version of this file read them). The innermost records alternate cleanly, with no break, in both runs;
    ``alternation_breaks`` in the report counts any break.
    """
    inner = sorted(((t, i, after) for i, (t, _before, after, types) in enumerate(lane_log) if types in ("", "SET_LAYOUT")), key=lambda x: (x[0], x[1]))
    by_t = {}
    for t, _i, after in inner:
        by_t[t] = after
    return sorted(by_t.items())


def alternation_breaks(lane_log):
    """Innermost records whose ``before`` is not the previous innermost record's ``after``."""
    inner = sorted(((t, i, before, after) for i, (t, before, after, types) in enumerate(lane_log) if types in ("", "SET_LAYOUT")), key=lambda x: (x[0], x[1]))
    return sum(1 for a, b in zip(inner, inner[1:]) if b[2] != a[3])


def disabled_episodes(timeline):
    """Lengths, ms, of each complete disabled episode in a timeline."""
    out, start = [], None
    for t, s in timeline:
        if s is True and start is None:
            start = t
        elif s is False and start is not None:
            out.append(t - start)
            start = None
    return out


def enabled_ms(timeline, lo, hi):
    """Milliseconds in [lo, hi) during which the lane's ``disabled`` was False (enabled), and the last such moment."""
    times = [t for t, _ in timeline]
    i = bisect.bisect_right(times, lo) - 1
    state = timeline[i][1] if i >= 0 else False
    t_prev, total, last_enabled = lo, 0, None
    for t, s in timeline[i + 1 :]:
        if t >= hi:
            break
        if state is False:
            total += t - t_prev
            last_enabled = t
        t_prev, state = t, s
    if state is False:
        total += hi - t_prev
        last_enabled = hi
    return total, last_enabled


def analyze(d, own_ms=100, strand_ms=30000, write_ms=2):
    """Classify every release and every fire in transcript ``d``; returns plain rows (see the module docstring)."""
    raw = d["raw"]
    req = {}
    for t, kind, rid, _props in raw["req"]:
        r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
        if kind == "W" and r["tW"] is None:
            r["tW"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    reqs = sorted((r for r in req.values() if r["tW"] is not None), key=lambda r: r["tW"])
    writes = sorted({t for t, _b, _s in raw["fires"]} | {t for t, _b, v in raw["gate"] if v is False})
    timeline = lane_timeline(raw["lane"])

    def is_write(t):
        i = bisect.bisect_left(writes, t - write_ms)
        return i < len(writes) and writes[i] <= t + write_ms

    releases = sorted(t for t, b, a, ty in raw["lane"] if b is True and a is False and ty == "" and not is_write(t))

    def newest_in_flight(t):
        live = [r for r in reqs if r["tW"] <= t and (r["tEnd"] is None or r["tEnd"] > t)]
        return live[-1] if live else None

    # Each request's successor: the next request of the same callback to enter ``watched``. An evicted request's late
    # release can only fall after its eviction and while its successor is in flight, because the successor's own
    # entry is what evicted it. The first version of this file took the OLDEST pending evicted request instead, and
    # a dropped or shifted release then silently re-paired every later eviction (round 1 of Phase 11's review, Lane
    # 11-A3); pairing on the successor makes such a release read "unassigned" and its eviction "none", alone.
    succ = {a["id"]: b["id"] for a, b in zip(reqs, reqs[1:])}
    # Each evicted request's eviction run: a maximal sequence of consecutive evicted requests, in entry order. Only
    # requests of the same run compete for a release; a request left unreleased in one run is not a candidate in the
    # next, which would flag every later release.
    run_of, run_no, prev_x = {}, 0, False
    for r in reqs:
        if r["end"] == "X":
            if not prev_x:
                run_no += 1
            run_of[r["id"]] = run_no
        prev_x = r["end"] == "X"
    own, late, unassigned = [], [], []
    pending_x = [r for r in reqs if r["end"] == "X"]
    for t in releases:
        cur = newest_in_flight(t)
        if cur is not None and cur["end"] == "A" and 0 <= cur["tEnd"] - t <= own_ms:
            own.append((t, cur["id"], cur["tEnd"] - t))
            continue
        # Every evicted request already evicted and still awaiting its late release could own this release. In the
        # 2026-10-05 runs there is never more than one, so the pairing below is forced; where there are more, it is
        # a guess, and the release is flagged AMBIGUOUS (round 2 of Phase 11's review, Lane 11-R2B: an evicted
        # request whose response lands after its successor ends would otherwise read "none" while its release is
        # silently paired with the successor).
        pending_here = [r for r in pending_x if r["tEnd"] <= t]
        # The evicted request whose eviction precedes this release and whose successor is the request in flight.
        cand = [r for r in pending_here if cur is not None and succ.get(r["id"]) == cur["id"]]
        if cand:
            r = cand[0]
            pending_x.remove(r)
            late.append(
                {
                    "evicted": r["id"],
                    "x_ms": r["tEnd"],
                    "release_ms": t,
                    "flight_ms": t - r["tW"],
                    "under": cur["id"],
                    "under_end": cur["end"],
                    # How far this release sat from the successor's own answer, when there was one: the margin that
                    # keeps --own-ms from reading it as the successor's own release.
                    "to_under_answer_ms": cur["tEnd"] - t if cur["end"] == "A" else None,
                    "ambiguous_with": [p["id"] for p in pending_here if p["id"] != r["id"] and run_of.get(p["id"]) == run_of.get(r["id"])],
                }
            )
            continue
        nxt = [r for r in reqs if r["end"] == "A" and r["tEnd"] >= t]
        nxt = min(nxt, key=lambda r: r["tEnd"]) if nxt else None
        unassigned.append({"t": t, "in_flight": cur["id"] if cur else None, "next_a": nxt and (nxt["id"], nxt["tEnd"] - t)})

    fires = []
    for t, before, _since in raw["fires"]:
        en, last = enabled_ms(timeline, t - strand_ms, t)
        cur = newest_in_flight(t)
        ep_start = None
        for x, s in reversed([p for p in timeline if p[0] < t]):
            if s is False:
                break
            ep_start = x
        fires.append(
            {
                "t": t,
                "before": before,
                "episode_ms": t - ep_start if ep_start is not None else None,
                "enabled_ms": en,
                "last_enabled_ms": t - last if last is not None else None,
                "in_flight": cur and (cur["id"], cur["end"], cur["tEnd"] - t),
            }
        )
    by_ev = {x["evicted"]: x for x in late}
    evictions = [{"id": r["id"], "tW": r["tW"], "x_ms": r["tEnd"], "late": by_ev.get(r["id"])} for r in reqs if r["end"] == "X"]
    episodes = disabled_episodes(timeline)
    return {
        "served_sha": d.get("served_sha"),
        "alternation_breaks": alternation_breaks(raw["lane"]),
        "episodes": len(episodes),
        "episode_median_ms": sorted(episodes)[len(episodes) // 2] if episodes else None,
        "req_times": {r["id"]: (r["tW"], r["tEnd"], r["end"]) for r in reqs},
        "requests": len(reqs),
        "releases": len(releases),
        "own": own,
        "late": late,
        "unassigned": unassigned,
        "fires": fires,
        "evictions": evictions,
    }


def report(res, strand_ms):
    print(f"served {res['served_sha']}  requests {res['requests']}  evicted {len(res['evictions'])}  fires {len(res['fires'])}")
    print(f"lane, innermost records: {res['alternation_breaks']} alternation breaks; {res['episodes']} disabled episodes, median {res['episode_median_ms']} ms")
    if res["alternation_breaks"]:
        print("!! ALTERNATION BREAKS: a lane change was logged only by a non-thunk record, so the innermost timeline is "
              "incomplete and every lane timing below is unreliable (exit status 2)")
    ambiguous = [x for x in res["late"] if x["ambiguous_with"]]
    print(f"late releases with more than one pending evicted request (pairing a guess): {len(ambiguous)}")
    for x in ambiguous:
        print(f"  !! AMBIGUOUS: release @{x['release_ms']} paired with req {x['evicted']}, but reqs {x['ambiguous_with']} were also evicted and unreleased")
    print(f"\nfires (threshold {strand_ms} ms):")
    for f in res["fires"]:
        print(
            f"  @{f['t']}: lane before {f['before']}; current disabled episode {f['episode_ms']} ms; "
            f"enabled in prior {strand_ms // 1000} s: {f['enabled_ms']} ms (last enabled {f['last_enabled_ms']} ms before); "
            f"in flight: {f['in_flight']}"
        )
    false_fires = sum(1 for f in res["fires"] if f["enabled_ms"] > 0)
    print(f"  -> {false_fires} of {len(res['fires'])} fires had the lane enabled within the threshold before them")
    print("\nevictions (each evicted request's late release, i.e. its discarded response landing):")
    for e in res["evictions"]:
        x = e["late"]
        if x is None:
            print(f"  req {e['id']}: X @{e['x_ms']}; late release: none")
        else:
            print(
                f"  req {e['id']}: W @{e['tW']}, X @{e['x_ms']}, late release @{x['release_ms']} ({x['flight_ms']} ms after W), "
                f"under req {x['under']} (which then ended {x['under_end']})"
            )
    gaps = sorted(g for _t, _rid, g in res["own"])
    print(
        f"\nreleases: {res['releases']} total; own {len(res['own'])} (release-to-A gap ms: min {gaps[0] if gaps else None}, "
        f"median {gaps[len(gaps) // 2] if gaps else None}, max {gaps[-1] if gaps else None}); "
        f"late (evicted, under a successor) {len(res['late'])}; unassigned {len(res['unassigned'])}"
    )
    to_a = sorted(x["to_under_answer_ms"] for x in res["late"] if x["to_under_answer_ms"] is not None)
    print(f"  late releases whose successor was answered: {len(to_a)}; release-to-that-answer gap ms {to_a}")
    for u in res["unassigned"]:
        print(f"  unassigned @{u['t']}: newest in flight {u['in_flight']}; next A (id, ms later) {u['next_a']}")


def self_test(d, args) -> int:
    """Five mutated copies of the transcript, each with a known answer, so this reader is shown able to fail."""
    base = analyze(d, args.own_ms, args.strand_ms, args.write_ms)
    ok = True
    # (a) A renderer whose evicted completions did NOT release: drop every late release from the lane log.
    late_t = {x["release_ms"] for x in base["late"]}
    m = copy.deepcopy(d)
    m["raw"]["lane"] = [rec for rec in m["raw"]["lane"] if not (rec[0] in late_t and rec[1] is True and rec[2] is False and rec[3] == "")]
    ra = analyze(m, args.own_ms, args.strand_ms, args.write_ms)
    a_ok = len(base["late"]) > 0 and not ra["late"] and all(e["late"] is None for e in ra["evictions"])
    print(f"self-test (a) no late releases: late {len(base['late'])} -> {len(ra['late'])}; every eviction reads none: {a_ok}")
    ok &= a_ok
    # (b) A fire on a lane that really was disabled for the whole threshold: one placed 1 s past the threshold
    # into the longest disabled episode (in the 2026-10-05 run, the T-apply clamp's 62 s).
    tl = lane_timeline(d["raw"]["lane"])
    longest = max(((t0, t1) for (t0, s0), (t1, _s1) in zip(tl, tl[1:]) if s0 is True), key=lambda p: p[1] - p[0])
    fake = longest[0] + args.strand_ms + 1000
    if fake < longest[1]:
        m = copy.deepcopy(d)
        m["raw"]["fires"] = m["raw"]["fires"] + [[fake, True, None]]
        rb = analyze(m, args.own_ms, args.strand_ms, args.write_ms)
        f = next(x for x in rb["fires"] if x["t"] == fake)
        b_ok = f["enabled_ms"] == 0
        print(f"self-test (b) a fire {(args.strand_ms + 1000) // 1000} s into the {longest[1] - longest[0]} ms disabled episode from {longest[0]}: enabled {f['enabled_ms']} ms -> {b_ok}")
    else:
        b_ok = False
        print(f"self-test (b) no disabled episode longer than {args.strand_ms + 1000} ms in this transcript; cannot run")
    ok &= b_ok

    def pairing(res):
        return {e["id"]: (e["late"] or {}).get("release_ms") for e in res["evictions"]}

    base_pairs = pairing(base)
    # (c) One late release lost: its eviction, and only its eviction, must read "none" (round 1 of Phase 11's
    # review, Lane 11-A3, found the oldest-first rule re-pairing every later eviction instead).
    if base["late"]:
        drop = base["late"][0]
        m = copy.deepcopy(d)
        m["raw"]["lane"] = [rec for rec in m["raw"]["lane"] if not (rec[0] == drop["release_ms"] and rec[1] is True and rec[2] is False and rec[3] == "")]
        pairs = pairing(analyze(m, args.own_ms, args.strand_ms, args.write_ms))
        changed = sorted(k for k in base_pairs if base_pairs[k] != pairs[k])
        c_ok = changed == [drop["evicted"]] and pairs[drop["evicted"]] is None
        print(f"self-test (c) drop request {drop['evicted']}'s late release: evictions changed {changed} -> {c_ok}")
    else:
        c_ok = False
        print("self-test (c) no late release in this transcript; cannot run")
    ok &= c_ok
    # (d) Every late release whose successor was answered moved to 50 ms before that answer, where it reads as the
    # successor's own: exactly those evictions must read "none", and no other pairing may move.
    shift = [x for x in base["late"] if x["to_under_answer_ms"] is not None]
    if shift:
        moved = {x["release_ms"]: x["release_ms"] + x["to_under_answer_ms"] - 50 for x in shift}
        m = copy.deepcopy(d)
        for rec in m["raw"]["lane"]:
            if rec[0] in moved and rec[1] is True and rec[2] is False and rec[3] == "":
                rec[0] = moved[rec[0]]
        pairs = pairing(analyze(m, args.own_ms, args.strand_ms, args.write_ms))
        changed = sorted(k for k in base_pairs if base_pairs[k] != pairs[k])
        want = sorted(x["evicted"] for x in shift)
        d_ok = changed == want and all(pairs[k] is None for k in changed)
        print(f"self-test (d) shift {len(shift)} late releases into their successor's own window: evictions changed {changed}, expected {want} -> {d_ok}")
    else:
        d_ok = False
        print("self-test (d) no late release with an answered successor in this transcript; cannot run")
    ok &= d_ok
    # (e) An evicted request whose response lands after its successor was itself evicted (Lane 11-R2B's case): move the
    # first late release that has a later eviction in the same run to 100 ms into the flight of the request after
    # that next eviction, and drop the next request's own late release. The successor rule then pairs the moved
    # release with the wrong request, so the reader must flag it AMBIGUOUS.
    chain = [x for x in base["late"] if x["under_end"] == "X"]
    if chain:
        x = chain[0]
        nxt = next(y for y in base["late"] if y["evicted"] == x["under"])
        moved_to = base["req_times"][nxt["under"]][0] + 100
        m = copy.deepcopy(d)
        kept = []
        for rec in m["raw"]["lane"]:
            is_release = rec[1] is True and rec[2] is False and rec[3] == ""
            if is_release and rec[0] == nxt["release_ms"]:
                continue
            if is_release and rec[0] == x["release_ms"]:
                rec[0] = moved_to
            kept.append(rec)
        m["raw"]["lane"] = kept
        re_ = analyze(m, args.own_ms, args.strand_ms, args.write_ms)
        flagged = [y for y in re_["late"] if y["ambiguous_with"]]
        e_ok = any(y["release_ms"] == moved_to for y in flagged)
        print(f"self-test (e) req {x['evicted']}'s release moved past req {nxt['evicted']}'s eviction, req {nxt['evicted']}'s dropped: flagged ambiguous {[(y['release_ms'], y['evicted'], y['ambiguous_with']) for y in flagged]} -> {e_ok}")
    else:
        e_ok = False
        print("self-test (e) no late release whose successor was evicted in this transcript; cannot run")
    ok &= e_ok
    print("SELF-TEST PASS" if ok else "SELF-TEST FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("--own-ms", type=int, default=100, help="a release followed by the in-flight request's own A within this is its OWN release")
    ap.add_argument("--strand-ms", type=int, default=30000, help="the watchdog's threshold (METRICS_STORE_STRAND_TIMEOUT_MS)")
    ap.add_argument("--write-ms", type=int, default=2, help="a thunk True -> False this close to a fire or a gate write is that write")
    ap.add_argument("--self-test", action="store_true", help="run the five known-answer mutations instead of the report")
    args = ap.parse_args()
    d = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    if args.self_test:
        return self_test(d, args)
    res = analyze(d, args.own_ms, args.strand_ms, args.write_ms)
    report(res, args.strand_ms)
    return 2 if res["alternation_breaks"] else 0


if __name__ == "__main__":
    sys.exit(main())
