#!/usr/bin/env python3
"""Lane A: are the 14 reports this PR adds byte-identical to their agents' last assistant message?

Independent extraction: each subagent transcript is split on "\\n" (never splitlines()); every
record whose message.role is "assistant" is kept; the LAST such message that carries text is the
answer. Records sharing one message.id are merged (text blocks joined in order), since one API
message can be written as several JSONL records. The report body is everything after the first
line (the HTML provenance comment) and its newline."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA")
R = S / "head/reports/2026-09-24_defect-register-round-42"
SESS = {
    "bc31e993": Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-happy-skipping-hollerith/bc31e993-97b0-4a01-ae04-cb39593eb647/subagents"),
    "8f86dec2": Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-hazy-beaming-map/8f86dec2-21ea-43f2-911a-bb2314a822ec/subagents"),
}
ADDED = [
    "canopy660-round1-validation.md", "cascor678-premerge-validation.md", "data428-round1-laneA-reprobe.md",
    "data428-round1-laneB-attack.md", "data428-round3-laneA1-security.md", "data428-round3-laneA2-claims.md",
    "data428-round3-laneB-refute.md", "ml2032-2059-round4-laneA-reprobe.md", "ml2032-2059-round4-laneB-refute.md",
    "ml2032-round1-laneA-reprobe.md", "ml2032-round1-laneB-attack.md", "ml2032-round2-validation.md",
    "primer-correction-round1-laneA-reprobe.md", "primer-correction-round1-laneB-refute.md",
]


def last_assistant_text(path: Path) -> tuple[str, int, str]:
    raw = path.read_text(encoding="utf-8")
    msgs: list[tuple[str, list[str]]] = []  # (message id, text blocks) in order
    n_asst = 0
    for line in raw.split("\n"):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = rec.get("message")
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        n_asst += 1
        mid = msg.get("id") or f"rec{n_asst}"
        content = msg.get("content")
        blocks = [content] if isinstance(content, str) else [b.get("text", "") for b in (content or []) if isinstance(b, dict) and b.get("type") == "text"]
        if msgs and msgs[-1][0] == mid:
            msgs[-1][1].extend(blocks)
        else:
            msgs.append((mid, list(blocks)))
    with_text = [(mid, bl) for mid, bl in msgs if any(t.strip() for t in bl)]
    mid, blocks = with_text[-1]
    trailing_records_after = len(msgs) - 1 - msgs.index(with_text[-1])
    return "".join(blocks), trailing_records_after, mid


ok = 0
for name in ADDED:
    text = (R / name).read_text(encoding="utf-8")
    first, _, body = text.partition("\n")
    agent = first.split("subagent ", 1)[1].split(" ", 1)[0]
    sess = first.split("of session ", 1)[1].split(" ", 1)[0]
    tpath = SESS[sess] / f"agent-{agent}.jsonl"
    if not tpath.exists():
        print(f"{name}: transcript MISSING {tpath}")
        continue
    last, after, mid = last_assistant_text(tpath)
    exact = body == last
    nl = body == last + "\n"
    rs = body.rstrip("\n") == last.rstrip("\n")
    verdict = "IDENTICAL" if exact else ("IDENTICAL+trailing-newline" if nl else ("equal modulo trailing newlines" if rs else "DIFFERENT"))
    ok += exact or nl
    print(f"{name:45s} agent={agent} sess={sess} body={len(body.encode())}B last={len(last.encode())}B sha(body)={hashlib.sha256(body.encode()).hexdigest()[:12]} sha(last)={hashlib.sha256(last.encode()).hexdigest()[:12]} -> {verdict}; assistant msgs after it={after}")
print(f"{ok}/{len(ADDED)} identical (exact or +1 trailing newline)")
