#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 5 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R5A.LBVRcz/lane_transcripts.py
# Written by Lane 11-R5A (measurement re-creation, artifact-first, on round 4's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R5A: read the round-3 and round-4 lane transcripts for timestamps, the usage-limit
messages and the final assistant message. Prints ONLY timestamps, roles, counts and match flags,
never transcript text.
"""
import json
from datetime import datetime
from pathlib import Path

D = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-dreamy-fluttering-kite/06e8868d-0c1f-4457-b7cb-b35e525032ef/subagents")
REPORTS = {
    "r3": Path("reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md"),
    "r4": Path("reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md"),
}
AGENTS = {"ad8dc12fc07b898dc": "r3", "a013bab17436e8456": "r3", "a787c1b146b28dbbe": "r4", "abf8c493b595bcdb2": "r4"}


def texts(msg):
    """Every text string in a message's content."""
    c = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(c, str):
        yield c
    elif isinstance(c, list):
        for part in c:
            if isinstance(part, dict):
                if part.get("type") == "text" and isinstance(part.get("text"), str):
                    yield part["text"]
                elif part.get("type") == "tool_result":
                    cc = part.get("content")
                    if isinstance(cc, str):
                        yield cc
                    elif isinstance(cc, list):
                        for q in cc:
                            if isinstance(q, dict) and isinstance(q.get("text"), str):
                                yield q["text"]


def ts(e):
    t = e.get("timestamp")
    return t[:19] + "Z" if isinstance(t, str) else None


for aid, rnd in AGENTS.items():
    p = D / f"agent-{aid}.jsonl"
    rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    times = [ts(e) for e in rows if ts(e)]
    print(f"== {aid} ({rnd}): {len(rows)} entries, first {times[0]}, last {times[-1]}")
    # largest gap between consecutive entries
    dts = [datetime.fromisoformat(t[:-1]) for t in times]
    gaps = sorted(((b - a).total_seconds(), a, b) for a, b in zip(dts, dts[1:]))
    g, a, b = gaps[-1]
    print(f"   largest gap {g / 3600:.1f} h, {a.isoformat()}Z -> {b.isoformat()}Z")
    # usage-limit / weekly mentions, by entry type and role (non-tool-result text only, and tool results separately)
    for i, e in enumerate(rows):
        m = e.get("message") or {}
        role = m.get("role") if isinstance(m, dict) else None
        for tx in texts(m):
            low = tx.lower()
            hit_w = "weekly" in low
            hit_l = "usage limit" in low or "limit reached" in low or "rate limit" in low
            if (hit_w or hit_l) and len(tx) < 2000:
                # short message: likely a system/limit notice, not a lane's quoted file content
                print(f"   entry {i} {ts(e)} type={e.get('type')} role={role} isApiErrorMessage={e.get('isApiErrorMessage')} len={len(tx)} weekly={hit_w} limit={hit_l} starts_resume={tx.startswith('Resume Lane')}")
    # final assistant text
    last = None
    for e in rows:
        m = e.get("message") or {}
        if isinstance(m, dict) and m.get("role") == "assistant":
            tt = [t for t in texts(m)]
            if tt and any(t.strip() for t in tt):
                last = "\n".join(tt)
    rep = REPORTS[rnd].read_text(encoding="utf-8")
    print(f"   final assistant text {len(last)} chars; appears verbatim in the {rnd} report file: {last.strip() in rep}")
