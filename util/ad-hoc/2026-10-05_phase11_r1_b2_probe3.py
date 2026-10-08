# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B2.KZI9rh/probe3.py
# Written by Lane 11-B2 (adversarial, claims beyond evidence, escalate side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-B2 probe 3: does each reconstructed sample fall ~0.1 s LATER in the cycle (forward drift)?

For each observed fire, take the grid instants t_k = fire - 5000*k (k = 6..0) and read, on the measured lane, the
age of the disabled episode containing t_k (ms since that episode began) and its length. The fire's own instant
(k=0) is read 1 ms before the fire, since the fire's own write is logged at that millisecond.
Also: aligned replay percentile of the observed fire count, and the replayed fires' episode ages.
"""
import bisect
import importlib.util
import json
import statistics

spec = importlib.util.spec_from_file_location("rt", "util/2026-10-05_f058_census_v2_release_trace.py")
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
spec2 = importlib.util.spec_from_file_location("ar", "util/2026-10-05_f058_watchdog_alias_replay.py")
ar = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(ar)

for name, path in [("run1", "ev/2026-10-05_census_live.json"), ("run2", "ev/run2/2026-10-05_census_live.json")]:
    with open(path) as fh:
        d = json.load(fh)
    raw = d["raw"]
    tl = rt.lane_timeline(raw["lane"])
    times = [t for t, _ in tl]

    def episode(t):
        """(age_ms, length_ms) of the disabled episode containing t, or None if enabled at t."""
        i = bisect.bisect_right(times, t) - 1
        if i < 0 or tl[i][1] is not True:
            return None
        # walk back to the episode start (first True after a False)
        j = i
        while j > 0 and tl[j - 1][1] is True:
            j -= 1
        k = i + 1
        while k < len(tl) and tl[k][1] is True:
            k += 1
        end = tl[k][0] if k < len(tl) else None
        return (t - tl[j][0], (end - tl[j][0]) if end else None)

    print(f"=== {name}")
    slopes = []
    for f, _b, _s in raw["fires"]:
        row, ages = [], []
        for k in range(6, -1, -1):
            tk = f - 5000 * k - (1 if k == 0 else 0)
            e = episode(tk)
            row.append(f"{e[0]}/{e[1]}" if e else "en")
            ages.append(e[0] if e else None)
        pts = [(6 - i, a) for i, a in enumerate(ages) if a is not None]
        if len(pts) >= 4:
            xs, ys = zip(*pts)
            mx, my = statistics.mean(xs), statistics.mean(ys)
            sl = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x in xs)
            slopes.append(sl)
        else:
            sl = None
        print(f"  fire@{f}: age/len at k=6..0: {' '.join(row)}   slope ms/sample {sl and round(sl)}")
    print(f"  per-fire slopes of episode age vs sample (ms/sample): {[round(s) for s in slopes]}")
    print(f"  median slope {statistics.median(slopes):.0f}; positive {sum(1 for s in slopes if s > 0)} of {len(slopes)}")
    # aligned replay percentile of observed count at 5000 ms
    clamps = ar.clamp_windows(raw["gate"])
    t_hi = max(t for t, *_ in raw["req"])
    counts, rep_ages = [], []
    for phi in range(0, 5000, 10):
        fs = ar.replay(tl, clamps, ar.sample_times(0, t_hi, 5000, phi), 30000)
        counts.append(len(fs))
        for t in fs:
            e = episode(t)
            if e:
                rep_ages.append(e[0])
    obs = len(raw["fires"])
    print(f"  aligned 5000: share of phases with >= observed {obs}: {sum(1 for c in counts if c >= obs) / len(counts):.3f}; with > observed: {sum(1 for c in counts if c > obs) / len(counts):.3f}")
    q = sorted(rep_ages)
    print(f"  replayed fires' episode age (ms): n {len(q)} p10 {q[len(q)//10]} median {q[len(q)//2]} p90 {q[9*len(q)//10]}")
    obs_ages = []
    for f, _b, _s in raw["fires"]:
        e = episode(f - 1)
        obs_ages.append(e[0] if e else None)
    print(f"  observed fires' episode age (ms): {sorted(obs_ages)}")
