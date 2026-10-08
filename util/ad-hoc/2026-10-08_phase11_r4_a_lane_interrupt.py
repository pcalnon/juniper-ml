#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R4A.mG5yhk/lane_interrupt.py
# Written by Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/empty-except: an empty handler now says why it is empty),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R4A: from the two round-3 lane transcripts, print ONLY timestamps, counts and fixed short markers --
never message text (the transcripts may hold an e-mail address from earlier slips).

For each: first and last record timestamps; records mentioning a usage limit (count, first/last timestamp, and
whether 'weekly' occurs in the same record); the timestamp of a user record beginning 'Resume Lane 11-R3';
the largest gap between consecutive records; whether the final assistant text equals the archived report body.
"""
import json
import re
from pathlib import Path

D = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-dreamy-fluttering-kite/06e8868d-0c1f-4457-b7cb-b35e525032ef/subagents")
REPORTS = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite/reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md").read_text(encoding="utf-8")
LIMIT = re.compile(r"usage limit|rate limit|limit reached|hit your limit|weekly limit", re.I)


def text_of(rec):
    m = rec.get("message") or {}
    c = m.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    return ""


for aid in ("ad8dc12fc07b898dc", "a013bab17436e8456"):
    recs = []
    with open(D / f"agent-{aid}.jsonl", encoding="utf-8") as fh:
        for line in fh:
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # a line that is not JSON carries no timestamp; it is skipped
    ts = [r.get("timestamp") for r in recs if r.get("timestamp")]
    lim = [(r.get("timestamp"), r.get("type"), bool(re.search("weekly", text_of(r) or json.dumps(r.get("message", "")), re.I))) for r in recs if LIMIT.search(text_of(r) or "") or LIMIT.search(json.dumps(r.get("error", "")) if r.get("error") else "")]
    lim_any = [(r.get("timestamp"), r.get("type")) for r in recs if LIMIT.search(json.dumps(r))]
    resume = [r.get("timestamp") for r in recs if r.get("type") == "user" and (text_of(r) or "").lstrip().startswith("Resume Lane 11-R3")]
    # largest gap
    from datetime import datetime
    def p(t):
        return datetime.fromisoformat(t.replace("Z", "+00:00"))
    gaps = sorted(((p(b) - p(a)).total_seconds(), a, b) for a, b in zip(ts, ts[1:]))
    last_asst = [text_of(r) for r in recs if r.get("type") == "assistant" and text_of(r).strip()]
    final = last_asst[-1].strip() if last_asst else ""
    print(f"agent {aid}: records {len(recs)}; first {ts[0] if ts else None}; last {ts[-1] if ts else None}")
    print(f"  limit-mentioning records (text): {len(lim)}; first {lim[0][0] if lim else None}; any 'weekly' in them: {any(x[2] for x in lim)}")
    print(f"  limit-mentioning records (anywhere in JSON): {len(lim_any)}; timestamps {[x[0] for x in lim_any][:4]}; types {sorted(set(x[1] for x in lim_any))}")
    print(f"  'Resume Lane 11-R3' user records: {resume}")
    print(f"  largest gap: {gaps[-1][0] / 3600:.1f} h, from {gaps[-1][1]} to {gaps[-1][2]}")
    print(f"  final assistant text: {len(final)} chars; found verbatim in the archived reports: {final in REPORTS}")
