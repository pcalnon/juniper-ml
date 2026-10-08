# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11A1.4njt8I/fire_ranges.py
# Written by Lane 11-A1 (measurement re-creation, source-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("rt", sys.argv[1]); rt = importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)
allen, allep, inflight = [], [], 0
for p in sys.argv[2:]:
    with open(p) as fh:
        res = rt.analyze(json.load(fh))
    en = [f["enabled_ms"] for f in res["fires"]]; ep = [f["episode_ms"] for f in res["fires"]]
    inflight += sum(1 for f in res["fires"] if f["in_flight"])
    allen += en; allep += ep
    print(p.rsplit("/", 1)[-1], "fires", len(en), "enabled_ms", min(en), max(en), "episode_ms", min(ep), max(ep), "fire times", [f["t"] for f in res["fires"]])
print("overall enabled", min(allen), max(allen), "episode", min(allep), max(allep), "fires with a request in flight", inflight, "of", len(allen))
