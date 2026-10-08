# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, a2/replay_innermost.py
# Written by Lane 11-A2 (measurement re-creation, raw-transcript-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-global-variable: a binding nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Sensitivity check: run the repo's alias replay unchanged except that its lane timeline is built from the
INNERMOST records only (types '' or SET_LAYOUT), i.e. each change at the time the shim itself saw it happen."""
import importlib.util, sys
p = "/tmp/tmp.AFzDbAMY9I/adhoc/2026-10-05_f058_watchdog_alias_replay.py"
spec = importlib.util.spec_from_file_location("alias_replay", p)
m = importlib.util.module_from_spec(spec)
sys.modules["alias_replay"] = m
spec.loader.exec_module(m)


def innermost(lane_log):
    by_t = {}
    for t, _b, after, types in lane_log:
        if types in ("", "SET_LAYOUT"):
            by_t[t] = after
    return sorted(by_t.items())


m.lane_timeline = innermost
sys.argv = [p] + sys.argv[1:]
sys.exit(m.main())
