#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R4A.mG5yhk/guard_test.py
# Written by Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R4A CHECK 6: the ledger's alternation-guard text, tested on mutated copies (adcba49f readers, -B)."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
RD = S / "readers_adcba49f"
TRACE, REPLAY = RD / "2026-10-05_f058_census_v2_release_trace.py", RD / "2026-10-05_f058_watchdog_alias_replay.py"
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
T1 = W / "reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json"
T2 = W / "reports/e2e-canopy-2026-09-02/f058-census-v2/run2/2026-10-05_census_live.json"
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("rt", TRACE)
rt = importlib.util.module_from_spec(spec)
sys.modules["rt"] = rt
spec.loader.exec_module(rt)
my = importlib.util.spec_from_file_location("my", S / "myreader.py")
mym = importlib.util.module_from_spec(my)
my.loader.exec_module(mym)


def run(script, path, *extra):
    r = subprocess.run([sys.executable, "-B", str(script), str(path), *extra], capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout + r.stderr)


for T in (T1, T2):
    with open(T, encoding="utf-8") as fh:
        d = json.load(fh)
    lane = d["raw"]["lane"]
    sel = rt.lane_timeline(lane)
    mine, relog, breaks = mym.timeline(lane)
    mine_pairs = [(t, a) for t, a, _ty in mine]
    sel_pairs = [(x[0], x[1]) if isinstance(x, (list, tuple)) else x for x in sel]
    print(T.parent.name, "type-selection changes:", len(sel), "push-order changes:", len(mine), "identical:", sel_pairs == mine_pairs, "breaks(rt):", rt.alternation_breaks(lane))
    inner = [i for i, r in enumerate(lane) if r[3] in ("", "SET_LAYOUT")]
    # (1) drop ONE innermost record (an enable) mid-run -> a break
    m1 = copy.deepcopy(d)
    k = [i for i in inner if lane[i][2] is False][100]
    del m1["raw"]["lane"][k]
    p1 = S / f"mut_drop1_{T.parent.name}.json"
    p1.write_text(json.dumps(m1))
    print("  drop one innermost record: report exit", run(TRACE, p1)[0], "| replay exit", run(REPLAY, p1)[0], "| --self-test exit", run(TRACE, p1, "--self-test")[0], "PASS" in run(TRACE, p1, "--self-test")[1])
    # (2) re-type a disable and the enable after it (innermost) as non-thunk, AND remove their enclosing re-logs
    m2 = copy.deepcopy(d)
    L2 = m2["raw"]["lane"]
    # pick the 50th disable among innermost records and the next innermost enable
    dis = [i for i in inner if lane[i][2] is True][50]
    en = next(i for i in inner if i > dis and lane[i][2] is False)
    for i in (dis, en):
        L2[i] = [L2[i][0], L2[i][1], L2[i][2], "Callbacks.NonThunk"]
    p2 = S / f"mut_pair_{T.parent.name}.json"
    p2.write_text(json.dumps(m2))
    sel2 = rt.lane_timeline(L2)
    print(f"  re-type pair @{lane[dis][0]}/{lane[en][0]} non-thunk: rt breaks {rt.alternation_breaks(L2)}; timeline {len(sel)} -> {len(sel2)}; report exit {run(TRACE, p2)[0]}; replay exit {run(REPLAY, p2)[0]}")
