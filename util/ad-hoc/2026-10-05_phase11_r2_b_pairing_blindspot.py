# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/pairing_blindspot.py
# Written by Lane 11-R2B (adversarial, on round 1's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Mutation: request k's late response lands under k+2 (its successor k+1 itself evicted), and k+1's lands unlogged.

Run 1, cascade 174..184. Move req 177's late release (902896, under 178) to 905500 (inside 179's flight, after
178's eviction at 905165), and drop req 178's late release (905789), as if 178's response landed on an enabled lane.
Compare the old (oldest-first) and new (successor) pairing rules.
"""
import copy, json, sys, importlib.util


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


new = load("rt_new", sys.argv[1])
old = load("rt_old", sys.argv[2])
with open(sys.argv[3]) as fh:
    d = json.load(fh)
m = copy.deepcopy(d)
lane = m["raw"]["lane"]
moved = dropped = 0
for rec in lane:
    if rec[0] == 902896 and rec[1] is True and rec[2] is False and rec[3] == "":
        rec[0] = 905500
        moved += 1
before = len(lane)
m["raw"]["lane"] = [rec for rec in lane if not (rec[0] == 905789 and rec[1] is True and rec[2] is False and rec[3] == "")]
dropped = before - len(m["raw"]["lane"])
print("moved", moved, "dropped", dropped)
for label, mod in (("NEW (successor)", new), ("OLD (oldest-first)", old)):
    res = mod.analyze(m)
    print(label, "late", len(res["late"]), "unassigned", len(res["unassigned"]))
    for e in res["evictions"]:
        if 175 <= e["id"] <= 180:
            x = e["late"]
            print("   req", e["id"], "->", "none" if x is None else f"release @{x['release_ms']} under req {x['under']} (flight {x['flight_ms']} ms)")
