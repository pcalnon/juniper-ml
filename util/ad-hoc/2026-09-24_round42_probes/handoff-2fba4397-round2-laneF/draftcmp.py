#!/usr/bin/env python3
"""Check that the durable PR draft equals '# ' + title + blank line + body (read-only)."""
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad")
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream")
title = (S / "data_fixforward_pr_title.txt").read_text(encoding="utf-8")
body = (S / "data_fixforward_pr_body.md").read_text(encoding="utf-8")
draft = (W / "reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md").read_text(encoding="utf-8")
cand1 = "# " + title.rstrip("\n") + "\n\n" + body
print("title bytes", len(title.encode()), "body bytes", len(body.encode()), "draft bytes", len(draft.encode()))
print("draft == '# '+title+'\\n\\n'+body:", draft == cand1)
if draft != cand1:
    cand2 = cand1.rstrip("\n") + "\n"
    print("draft == same with single trailing newline:", draft == cand2)
    # first differing position
    for i, (a, b) in enumerate(zip(draft, cand1)):
        if a != b:
            print("first diff at", i, repr(draft[i - 40:i + 40]), repr(cand1[i - 40:i + 40]))
            break
# the old title's claim
print("title claims 'a storage fault is a 500':", "a storage fault is a 500" in title)
