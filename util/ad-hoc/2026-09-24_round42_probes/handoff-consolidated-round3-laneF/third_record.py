#!/usr/bin/env python3
"""Read-only: characterise the executor's user text records (heads only, credential-shaped text masked)."""
import glob
import json
import re

SID = "2fba4397-7d9b-4929-8ca2-375b8168e1c8"
ex = glob.glob(f"/home/pcalnon/.claude/projects/*/{SID}/subagents/agent-a46e715a6801b98ca.jsonl")[0]
MASK = re.compile(r"(pypi-Ag|ghp_|gho_|github_pat_|hf_|AKIA|xox[abpr]-)[A-Za-z0-9_-]+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
with open(ex, encoding="utf-8") as fh:
    for raw in fh:
        rec = json.loads(raw)
        if rec.get("type") != "user":
            continue
        c = rec.get("message", {}).get("content")
        if isinstance(c, list):
            text = "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
        else:
            text = c or ""
        if not text.strip():
            continue
        ts = rec.get("timestamp")
        print("=====", ts, "chars", len(text), "isSidechain", rec.get("isSidechain"), "userType", rec.get("userType"))
        head = MASK.sub("<masked>", text[:700])
        print(head)
        heads = [l for l in text.split("\n") if l.startswith("#") or l.startswith("**")][:12]
        print("-- headings:", [MASK.sub("<masked>", h)[:90] for h in heads])
