# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/stamp_skew.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone; py/unused-local-variable: a binding nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-A3: the shim stamps each lane record with its dispatch's START time but logs it at completion. An outer
Callbacks.* dispatch whose observers ran the lane's thunk later is therefore stamped EARLIER than the change it
reports. How far, how often, and what does it do to the numbers read off the per-ms timeline?"""
import importlib.util
import json
import statistics
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh")


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, S / "frozen/util/ad-hoc" / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


rt = load("rt", "2026-10-05_f058_census_v2_release_trace.py")
wd = load("wd", "2026-10-05_f058_watchdog_alias_replay.py")
EV = S / "frozen/reports/e2e-canopy-2026-09-02/f058-census-v2"
for p in (EV / "2026-10-05_census_live.json", EV / "run2/2026-10-05_census_live.json"):
    d = json.loads(p.read_text(encoding="utf-8"))
    raw = d["raw"]
    lane = raw["lane"]
    # skew: an outer record stamped before the thunk record logged just ahead of it (log order)
    skews = []
    for i, (t, b, a, ty) in enumerate(lane):
        if ty == "" or ty == "SET_LAYOUT":
            continue
        j = i - 1
        while j >= 0 and lane[j][3] == "" and lane[j][0] >= t:
            if lane[j][2] == a:
                skews.append((lane[j][0] - t, ty, b, a, t))
                break
            j -= 1
    big = [s for s in skews if s[0] > 5]
    print(f"{p.parent.name}: outer records {sum(1 for r in lane if r[3] not in ('', 'SET_LAYOUT'))}; paired with an inner thunk {len(skews)}; stamped > 5 ms before their change: {len(big)}; max {max(s[0] for s in skews)} ms; sum {sum(s[0] for s in skews)} ms")
    print("   largest:", sorted(big, reverse=True)[:6])
    # timelines: as the instruments build it, and from thunk records only (each change at its own time)
    tl_inst = rt.lane_timeline(lane)
    tl_thunk = rt.lane_timeline([r for r in lane if r[3] in ("", "SET_LAYOUT")])
    # disabled episodes from each
    def episodes(tl):
        eps, start = [], None
        for t, s in tl:
            if s is True and start is None:
                start = t
            elif s is False and start is not None:
                eps.append(t - start)
                start = None
        return eps
    e1, e2 = episodes(tl_inst), episodes(tl_thunk)
    print(f"   disabled episodes: instrument timeline n={len(e1)} median {statistics.median(e1)}; thunk-only n={len(e2)} median {statistics.median(e2)}")
    # fires' enabled-in-30 s and episode age, both timelines
    rows = []
    for t, *_ in raw["fires"]:
        a1, _ = rt.enabled_ms(tl_inst, t - 30000, t)
        a2, _ = rt.enabled_ms(tl_thunk, t - 30000, t)
        rows.append((t, a1, a2))
    print(f"   fires' enabled ms in prior 30 s: instrument {min(r[1] for r in rows)}-{max(r[1] for r in rows)}; thunk-only {min(r[2] for r in rows)}-{max(r[2] for r in rows)}; max per-fire difference {max(r[2] - r[1] for r in rows)} ms")
    # alias replay at 5000 ms, both timelines
    cl = wd.clamp_windows(raw["gate"])
    t_hi = max(t for t, *_ in raw["req"])
    for label, tl in (("instrument", tl_inst), ("thunk-only", tl_thunk)):
        al = [len(wd.replay(tl, cl, wd.sample_times(0, t_hi, 5000, phi), 30000)) for phi in range(0, 5000, 10)]
        print(f"   replay P=5000 aligned on the {label} timeline: {wd.summary(al)}")
