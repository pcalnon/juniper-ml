# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R2A.sffLXI/selftest_on_old.py
# Written by Lane 11-R2A (measurement re-creation, on round 1's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Adequacy: run b3c54692's four self-tests against the 1b7cf44b (oldest-first) analyze; (c) and (d) should FAIL."""
import argparse
import importlib.util
import inspect
import json
import sys
from pathlib import Path

S = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


new = load("rt_new", S / "tree_b3/util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py")
old = load("rt_old", S / "tree_b1/util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py")
print("old analyze signature:", inspect.signature(old.analyze))
args = argparse.Namespace(own_ms=100, strand_ms=30000, write_ms=2)
for p in sys.argv[1:]:
    d = json.loads(Path(p).read_text())
    print("==", p.split("/")[-2])
    new.analyze = old.analyze  # self_test resolves analyze from its module globals
    rc = new.self_test(d, args)
    print("exit with old pairing:", rc)
