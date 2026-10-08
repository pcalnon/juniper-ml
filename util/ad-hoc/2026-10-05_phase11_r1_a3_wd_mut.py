# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/wd_mut.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-A3: can the frozen watchdog alias replay answer otherwise? Mutations and known-answer lanes."""
import bisect
import importlib.util
import json
import random
import statistics
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh")
spec = importlib.util.spec_from_file_location("wd", S / "frozen/util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py")
wd = importlib.util.module_from_spec(spec)
sys.modules["wd"] = wd
spec.loader.exec_module(wd)
EV = S / "frozen/reports/e2e-canopy-2026-09-02/f058-census-v2"
RUNS = {"run1": EV / "2026-10-05_census_live.json", "run2": EV / "run2/2026-10-05_census_live.json"}


def reqs_of(raw):
    req = {}
    for t, kind, rid, _p in raw["req"]:
        r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
        if kind == "W" and r["tW"] is None:
            r["tW"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    return req


def replay_progress(timeline, clamps, samples, strand_ms, progress_times):
    """The same predicate, but any progress event since the previous sample also resets the clock."""
    times = [t for t, _ in timeline]
    prog = sorted(progress_times)

    def disabled_at(t):
        i = bisect.bisect_right(times, t) - 1
        return timeline[i][1] if i >= 0 else False

    def clamped(t):
        return any(a <= t < b for a, b in clamps)

    since, fires, prev = None, [], None
    for t in samples:
        progressed = prev is not None and bisect.bisect_right(prog, t) - bisect.bisect_right(prog, prev) > 0
        prev = t
        if not disabled_at(t) or clamped(t) or progressed:
            since = None
        elif since is None:
            since = t
        elif t - since >= strand_ms:
            since = None
            fires.append(t)
    return fires


def counts(timeline, clamps, t_lo, t_hi, period, step=10, seeds=10, strand=30000, fn=None, extra=None):
    fn = fn or (lambda tl, cl, s, st: wd.replay(tl, cl, s, st))
    aligned = [len(fn(timeline, clamps, wd.sample_times(t_lo, t_hi, period, phi), strand)) for phi in range(0, period, step)]
    jit = []
    for phi in range(0, period, step * 10):
        for seed in range(seeds):
            rng = random.Random(seed * 100003 + phi)
            jit.append(len(fn(timeline, clamps, wd.sample_times(t_lo, t_hi, period, phi, period / 2, rng), strand)))
    return aligned, jit


def progress_test(name):
    d = json.loads(RUNS[name].read_text(encoding="utf-8"))
    raw = d["raw"]
    tl = wd.lane_timeline(raw["lane"])
    cl = wd.clamp_windows(raw["gate"])
    t_hi = max(t for t, *_ in raw["req"])
    req = reqs_of(raw)
    a_t = [r["tEnd"] for r in req.values() if r["end"] == "A"]
    wa_t = a_t + [r["tW"] for r in req.values() if r["tW"] is not None]
    for label, prog in (("progress = an A since the last sample", a_t), ("progress = a W or an A since the last sample", wa_t)):
        al, ji = counts(tl, cl, 0, t_hi, 5000, fn=lambda tl_, cl_, s, st: replay_progress(tl_, cl_, s, st, prog))
        print(f"  {name} {label}: aligned {wd.summary(al)} | jittered {wd.summary(ji)}")


def synthetic(cycle, disabled, span=1514034, period=5000, offset=0):
    """A lane disabled for `disabled` ms at the start of every `cycle` ms: raw lane/req/gate as the shim logs them."""
    lane, req, rid, t = [], [], 0, offset
    while t < span:
        rid += 1
        lane.append([t, False, True, ""])
        req.append([t, "W", rid, 0])
        lane.append([t + disabled, True, False, ""])
        req.append([t + disabled + 40, "A", rid, 0])
        t += cycle
    return {"raw": {"lane": lane, "req": req, "gate": [], "fires": []}}


def closed_form_4900(span, period=5000, cycle=4900, disabled=2800, strand=30000):
    """Brute-force the deterministic expectation independently of wd.replay: sample phases advance by period-cycle."""
    out = []
    for phi in range(0, period, 10):
        since, n, t = None, 0, phi
        while t < span:
            th = t % cycle
            dis = 0 < th < disabled or th == 0  # disabled on [0, disabled) as the synthetic lane's records give it
            if not dis:
                since = None
            elif since is None:
                since = t
            elif t - since >= strand:
                since = None
                n += 1
            t += period
        out.append(n)
    return out


def known_answer_lanes():
    for cycle, disabled in ((4900, 2800), (7500, 2800), (7500, 5400), (5000, 2800), (6000, 2800)):
        d = synthetic(cycle, disabled)
        raw = d["raw"]
        tl = wd.lane_timeline(raw["lane"])
        t_hi = max(t for t, *_ in raw["req"])
        al, ji = counts(tl, [], 0, t_hi, 5000)
        exp = closed_form_4900(t_hi, cycle=cycle, disabled=disabled)
        # chance model: independent samples, each disabled with p = disabled/cycle, same count of samples
        p = disabled / cycle
        rng = random.Random(7)
        n_samples = len(wd.sample_times(0, t_hi, 5000, 0))
        mc = []
        for _ in range(2000):
            since, n, t = None, 0, 0
            for k in range(n_samples):
                t = k * 5000
                if rng.random() >= p:
                    since = None
                elif since is None:
                    since = t
                elif t - since >= 30000:
                    since = None
                    n += 1
            mc.append(n)
        print(f"  synthetic lane cycle {cycle} ms, disabled {disabled} ms: replay aligned {wd.summary(al)}; independent brute force {wd.summary(exp)}; equal per phase: {al == exp} | jittered {wd.summary(ji)} | i.i.d. Bernoulli(p={p:.3f}) chance model median {statistics.median(mc)}, P(0) {sum(1 for x in mc if x == 0) / len(mc):.2f}")


def fitted_sampler(name):
    """Fit a strictly periodic sampler to the observed fire times, then check each fire's 30 s of predicted samples."""
    d = json.loads(RUNS[name].read_text(encoding="utf-8"))
    raw = d["raw"]
    fires = [t for t, *_ in raw["fires"]]
    tl = wd.lane_timeline(raw["lane"])
    cl = wd.clamp_windows(raw["gate"])
    times = [t for t, _ in tl]

    def disabled_at(t):
        i = bisect.bisect_right(times, t) - 1
        return tl[i][1] if i >= 0 else False

    best = None
    for p10 in range(49900, 50101):  # period in 0.1 ms
        P = p10 / 10
        res = [(f % P) for f in fires]
        # circular spread
        res.sort()
        gaps = [b - a for a, b in zip(res, res[1:])] + [res[0] + P - res[-1]]
        spread = P - max(gaps)
        if best is None or spread < best[0]:
            best = (spread, P)
    spread, P = best
    print(f"  {name}: fire residues mod P are tightest at P = {P} ms (spread {spread:.0f} ms over {len(fires)} fires)")
    # residues at 5000 exactly
    print(f"    residues mod 5000: {[f % 5000 for f in fires]}")
    # predicted samples before each fire: f - k*P, k=1..6 (the 6 samples before the firing one), checked 1 ms before the fire for the firing one
    bad = 0
    for f in fires:
        prev = [f - k * P for k in range(1, 7)]
        states = [disabled_at(x) for x in prev] + [disabled_at(f - 1)]
        if not all(states):
            bad += 1
            print(f"    fire @{f}: predicted samples' states (oldest last) {states}")
    print(f"    fires whose predicted preceding 30 s of samples all saw the lane disabled: {len(fires) - bad} of {len(fires)}")
    # does a replay at that period, phase-matched to the fires, reproduce them?
    phi = fires[0] % P - 1
    samples = wd.sample_times(0, max(t for t, *_ in raw["req"]), P, phi)
    rf = wd.replay(tl, cl, samples, 30000)
    match = sum(1 for f in fires if any(abs(f - x) <= 3 for x in rf))
    print(f"    replay at P={P}, phase {phi:.0f} (1 ms before the first fire's residue): {len(rf)} fires, {match} of {len(fires)} within 3 ms of an observed fire")


if __name__ == "__main__":
    print("== progress-based predicate on the measured lanes (expect 0)")
    for n in ("run1", "run2"):
        progress_test(n)
    print("== known-answer synthetic lanes (strictly periodic; expectation brute-forced independently of wd.replay)")
    known_answer_lanes()
    print("== a strictly periodic sampler fitted to the observed fires")
    for n in ("run1", "run2"):
        fitted_sampler(n)
