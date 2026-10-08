# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/rt_mut.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-A3: mutation tests of the frozen release trace (2026-10-05_f058_census_v2_release_trace.py)."""
import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh")
spec = importlib.util.spec_from_file_location("rt", S / "frozen/util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py")
rt = importlib.util.module_from_spec(spec)
sys.modules["rt"] = rt
spec.loader.exec_module(rt)
EV = S / "frozen/reports/e2e-canopy-2026-09-02/f058-census-v2"
RUNS = {"run1": EV / "2026-10-05_census_live.json", "run2": EV / "run2/2026-10-05_census_live.json"}


def summ(res):
    none = [e["id"] for e in res["evictions"] if e["late"] is None]
    flights = [x["flight_ms"] for x in res["late"]]
    gaps = sorted(g for _t, _r, g in res["own"])
    to_a = sorted(x["to_under_answer_ms"] for x in res["late"] if x["to_under_answer_ms"] is not None)
    false_f = sum(1 for f in res["fires"] if f["enabled_ms"] > 0)
    return (
        f"releases {res['releases']} own {len(res['own'])} (gap {gaps[0] if gaps else None}-{gaps[-1] if gaps else None}) late {len(res['late'])} unassigned {len(res['unassigned'])}; "
        f"evictions reading none {none}; late flight ms {min(flights) if flights else None}-{max(flights) if flights else None}; late->succ-answer {to_a}; false fires {false_f}/{len(res['fires'])}"
    )


def load(name):
    return json.loads(RUNS[name].read_text(encoding="utf-8"))


def own_gap_hist(name):
    res = rt.analyze(load(name))
    gaps = sorted(g for _t, _r, g in res["own"])
    print(name, "own gaps > 54 ms:", [g for g in gaps if g > 54], "; < 38 ms:", [g for g in gaps if g < 38])
    return res


def sweep(name):
    d = load(name)
    print(f"== {name}: --own-ms sweep (write-ms 2)")
    for own in (0, 13, 38, 54, 60, 88, 89, 90, 100, 200, 432, 433, 434, 500, 703, 704, 1000, 2100):
        print(f"  own-ms {own:5d}: {summ(rt.analyze(d, own_ms=own))}")
    print(f"== {name}: --write-ms sweep (own-ms 100)")
    for w in (0, 1, 2, 5, 50):
        res = rt.analyze(d, write_ms=w)
        print(f"  write-ms {w:3d}: {summ(res)}")
        if res["unassigned"]:
            print("     unassigned:", res["unassigned"])


def shift_mutation(name, evicted_successors_too=False, seed=0):
    """Move every late release to 1-50 ms before its successor's answer (or X, if asked and the successor was evicted)."""
    d = load(name)
    base = rt.analyze(d)
    rng = random.Random(seed)
    req = {}
    for t, kind, rid, _p in d["raw"]["req"]:
        r = req.setdefault(rid, {"end": None, "tEnd": None})
        if kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    m = copy.deepcopy(d)
    moved = 0
    for x in base["late"]:
        u = req[x["under"]]
        if u["end"] == "A" or evicted_successors_too:
            new_t = u["tEnd"] - rng.randint(1, 50)
            for rec in m["raw"]["lane"]:
                if rec[0] == x["release_ms"] and rec[1] is True and rec[2] is False and rec[3] == "":
                    rec[0] = new_t
                    moved += 1
                    break
    m["raw"]["lane"].sort(key=lambda r: r[0])
    res = rt.analyze(m)
    print(f"== {name}: shift {'every' if evicted_successors_too else 'answered-successor'} late release into the 50 ms before the successor's {'end' if evicted_successors_too else 'answer'} (moved {moved})")
    print("  ", summ(res))
    for x in res["late"]:
        if x["flight_ms"] > 6000:
            print(f"   mis-paired: evicted {x['evicted']} given release @{x['release_ms']} ({x['flight_ms']} ms after its W)")
    return res


def drop_one(name, which=0):
    """Remove a single late release (an evicted response that never released, e.g. it never landed)."""
    d = load(name)
    base = rt.analyze(d)
    x = base["late"][which]
    m = copy.deepcopy(d)
    m["raw"]["lane"] = [r for r in m["raw"]["lane"] if not (r[0] == x["release_ms"] and r[1] is True and r[2] is False and r[3] == "")]
    res = rt.analyze(m)
    print(f"== {name}: drop the late release of evicted req {x['evicted']} only")
    print("  ", summ(res))
    for y in res["late"]:
        if y["flight_ms"] > 6000:
            print(f"   mis-paired: evicted {y['evicted']} given release @{y['release_ms']} ({y['flight_ms']} ms after its W)")


if __name__ == "__main__":
    for n in ("run1", "run2"):
        own_gap_hist(n)
        sweep(n)
        shift_mutation(n)
        shift_mutation(n, evicted_successors_too=True)
        drop_one(n, 0)
