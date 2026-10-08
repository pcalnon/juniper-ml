#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r4b.5mnsCd/breakmut.py
# Written by Lane 11-R4B (adversarial, on round 3's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Mutations for the alternation-guard text: one innermost change re-typed non-thunk; a disable/enable pair re-typed."""
import copy
import json
import subprocess
import sys
from pathlib import Path

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite/"
T1 = W + "reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json"
RT = W + "util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py"
AR = W + "util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py"
OUT = Path(__file__).resolve().parent / "mut"
OUT.mkdir(exist_ok=True)
with open(T1) as fh:
    d = json.load(fh)
lane = d["raw"]["lane"]
inner = [i for i, r in enumerate(lane) if r[3] in ("", "SET_LAYOUT") and r[0] > 100000]
# find an innermost disable (F->T) followed by its enable (T->F), each of which has NO enclosing re-log (so re-typing removes the change entirely)
def relogged(i):
    return i + 1 < len(lane) and (lane[i + 1][1], lane[i + 1][2]) == (lane[i][1], lane[i][2])
single = inner[5]
m1 = copy.deepcopy(d)
m1["raw"]["lane"][single][3] = "X.Fake"
pair = None
for a, b in zip(inner, inner[1:]):
    if lane[a][1] is False and lane[a][2] is True and lane[b][1] is True and lane[b][2] is False:
        pair = (a, b)
        break
m2 = copy.deepcopy(d)
for i in pair:
    m2["raw"]["lane"][i][3] = "X.Fake"
for name, m in (("one", m1), ("pair", m2)):
    p = OUT / f"{name}.json"
    p.write_text(json.dumps(m))
    rr = subprocess.run([sys.executable, RT, str(p)], capture_output=True, text=True)
    rs = subprocess.run([sys.executable, RT, str(p), "--self-test"], capture_output=True, text=True)
    ra = subprocess.run([sys.executable, AR, str(p), "--periods", "5000"], capture_output=True, text=True)
    brk = [l for l in rr.stdout.splitlines() if "alternation breaks" in l][:1]
    print(f"{name}: report rc {rr.returncode} {brk}; self-test rc {rs.returncode} last={rs.stdout.strip().splitlines()[-1]}; replay rc {ra.returncode} {ra.stderr.strip()[:90]}")
    # item 24's proposed check: push-order walk vs type selection
    L = m["raw"]["lane"]
    pw, prev = [], None
    for r in L:
        if prev is not None and (r[1], r[2]) == prev:
            continue
        pw.append((r[0], r[2]))
        prev = (r[1], r[2])
    ts = sorted((r[0], r[2]) for r in L if r[3] in ("", "SET_LAYOUT"))
    print(f"   push-order walk vs type selection differ: {sorted(pw) != ts} ({len(pw)} vs {len(ts)})")
print("pair re-typed at", [lane[i][0] for i in pair], "single at", lane[single][0])
