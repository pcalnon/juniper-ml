# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6b.lTWETu/verbatim_check.py
# Written by Lane 11-R6B (adversarial, on round 5's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R6B: is each archived round-5 report the lane's last assistant text, verbatim? Prints flags and lengths only."""

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
T = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-dreamy-fluttering-kite/06e8868d-0c1f-4457-b7cb-b35e525032ef/subagents")
P = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite/reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md")
text = P.read_text(encoding="utf-8")
for part in re.split(r"\n## ", text)[1:]:
    title, rest = part.split("\n", 1)
    m = re.search(r"\*agent `([0-9a-f]+)` · .*? · (\d+) chars\*\n\n", rest)
    agent = m.group(1)
    body = rest[m.end():].split("\n---\n")[0].strip()
    last = None
    n_lines = 0
    with open(T / f"agent-{agent}.jsonl", encoding="utf-8") as fh:
        for line in fh:
            n_lines += 1
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue  # a partial line carries no message
            if o.get("type") != "assistant":
                continue
            content = (o.get("message") or {}).get("content") or []
            texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
            if texts and "".join(texts).strip():
                last = "".join(texts)
    print(f"{agent}: transcript lines {n_lines}; last text {len(last or '')} chars; archived {len(body)} chars; identical: {(last or '').strip() == body}")
