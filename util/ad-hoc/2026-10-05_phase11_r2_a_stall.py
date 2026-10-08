# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R2A.sffLXI/stall.py
# Written by Lane 11-R2A (measurement re-creation, on round 1's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
import json
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from myreader import requests  # noqa: E402

for p in sys.argv[1:]:
    with open(p) as fh:
        raw = json.load(fh)["raw"]
    req, _ = requests(raw)
    ids = sorted(req)
    a_times = sorted(req[i]["tEnd"] for i in ids if req[i]["end"] == "A")
    runs, cur = [], []
    for i in ids:
        if req[i]["end"] == "X":
            cur.append(i)
        elif cur:
            runs.append((cur, i))
            cur = []
    out = []
    for run, nxt in runs:
        prev = max([t for t in a_times if t < req[run[0]]["W"]] or [None], key=lambda x: -1 if x is None else x)
        out.append((len(run), (req[nxt]["tEnd"] - prev) if prev is not None else None))
    gaps = sorted(b - a for a, b in zip(a_times, a_times[1:]))
    print(p.split("/")[-2], "runs (len, ms without an applied answer):", out, "| longest A-to-A gap overall:", gaps[-1], "second:", gaps[-2])
