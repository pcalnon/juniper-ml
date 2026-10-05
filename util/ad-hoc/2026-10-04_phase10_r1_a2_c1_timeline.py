# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/c1_timeline.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, modified 2026-10-05 only to close the files it opens
# (CodeQL py/file-not-always-closed on juniper-ml#2157; and py/unused-import, so `import re` is gone); what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase10_r1_probes_close_files.py.
# ---------------------------------------------------------------------------
"""Claim 1: place the 80 network-stats 503 WARNINGs against the per-case windows (UTC) and backends."""
import glob
import json
import os
from datetime import datetime, timedelta, timezone

ROOT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/clever-juggling-spring/reports/2026-09-23_canopy-a-n2-generate-stage-train-render"


def parse_utc(s):
    return datetime.strptime(s.rstrip("Z"), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)


cases = []
for d in sorted(glob.glob(f"{ROOT}/[01][0-9]_*/")):
    if d.rstrip("/").endswith("00_stack"):
        continue
    name = os.path.basename(d.rstrip("/"))
    with open(f"{d}summary.json") as fh:
        s = json.load(fh)
    with open(f"{d}index.json") as fh:
        idx = json.load(fh)
    ts = [parse_utc(e["t_utc"]) for e in idx if e.get("t_utc")]
    tl = sorted(glob.glob(f"{d}dashboard*_timeline.json"))
    caps = []
    for t in tl:
        with open(t) as fh:
            j = json.load(fh)
        caps.append((os.path.basename(t), j if isinstance(j, dict) else {"_list_len": len(j)}))
    cases.append((name, s.get("model"), s.get("model_select", {}).get("backend"), min(ts), max(ts), caps))

for name, model, backend, t0, t1, caps in cases:
    print(f"{name:32} model={model:10} backend={backend!s:10} index {t0:%H:%M:%S}Z..{t1:%H:%M:%S}Z")
    for cname, c in caps:
        keys = list(c.keys())[:12]
        print(f"     {cname}: keys={keys}")

# The WARNING lines, local time -> UTC at -5h (CDT) -- the offset is checked separately.
with open(f"{ROOT}/00_stack/logs/juniper-canopy.log", errors="replace") as fh:
    lines = [l for l in fh if "Network stats API returned 503" in l]
print("\nwarnings:", len(lines))
stamps = [datetime.strptime(l[:23], "%Y-%m-%d %H:%M:%S,%f").replace(tzinfo=timezone.utc) + timedelta(hours=5) for l in lines]
print("first/last (UTC if offset is -5h):", stamps[0].strftime("%H:%M:%S"), stamps[-1].strftime("%H:%M:%S"))
# bucket each warning into the case whose window [index start, next case's index start) contains it
starts = [(c[0], c[3], c[2]) for c in cases]
buckets = {}
for st in stamps:
    owner = None
    for i, (n, t0, be) in enumerate(starts):
        nxt = starts[i + 1][1] if i + 1 < len(starts) else datetime.max.replace(tzinfo=timezone.utc)
        if t0 <= st < nxt:
            owner = (n, be)
    buckets.setdefault(owner, []).append(st)
for k, v in buckets.items():
    print(f"  {k}: {len(v)}  {v[0]:%H:%M:%S}..{v[-1]:%H:%M:%S}")
