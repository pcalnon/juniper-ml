# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r3b/r2b_case.py
# Written by Lane 11-R3B (adversarial, on round 2's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R2B's exact mutation (round-2 report, Finding 4) run through the 7af6a381 release trace's analyze():
move req 177's late release (902,896) to 905,500 and drop req 178's (905,789). Also two variants:
V2: keep req 178's release (both land under 179) -> is the first one flagged?
V3: drop req 176's late release only (a 'none' mid-run) -> how many later releases in that run are flagged?"""
import copy
import importlib.util
import json
import sys

spec = importlib.util.spec_from_file_location("rt", "/tmp/tmp.cIFAKjB6BD/7af/release_trace.py")
rt = importlib.util.module_from_spec(spec)
sys.modules["rt"] = rt
spec.loader.exec_module(rt)
with open(sys.argv[1], encoding="utf-8") as fh:
    d = json.load(fh)


def is_rel(rec):
    return rec[1] is True and rec[2] is False and rec[3] == ""


def mutate(move=None, drop=()):
    m = copy.deepcopy(d)
    kept = []
    for rec in m["raw"]["lane"]:
        if is_rel(rec) and rec[0] in drop:
            continue
        if move and is_rel(rec) and rec[0] == move[0]:
            rec[0] = move[1]
        kept.append(rec)
    m["raw"]["lane"] = kept
    return rt.analyze(m)


def show(tag, res):
    amb = [(x["release_ms"], x["evicted"], x["ambiguous_with"]) for x in res["late"] if x["ambiguous_with"]]
    none = [e["id"] for e in res["evictions"] if e["late"] is None]
    print(f"{tag}: ambiguous {amb}; none {none}; unassigned {[u['t'] for u in res['unassigned']]}; breaks {res['alternation_breaks']}")


show("base", rt.analyze(d))
show("R2B exact (177 -> 905500, drop 178's 905789)", mutate(move=(902896, 905500), drop=(905789,)))
show("V2 (177 -> 905500, keep 178's)", mutate(move=(902896, 905500)))
show("V3 (drop 176's 900313)", mutate(drop=(900313,)))
