#!/usr/bin/env python3
"""Read-only transcript checks for lane F round 3. Prints only timestamps, booleans and short phrases."""
import glob
import json
import os
import re
import time

SID = "2fba4397-7d9b-4929-8ca2-375b8168e1c8"
dirs = glob.glob(f"/home/pcalnon/.claude/projects/*/{SID}/subagents")
print("subagents dirs matched by the glob:", len(dirs))
d = dirs[0]
files = sorted(glob.glob(os.path.join(d, "*.jsonl")))
print("transcripts:", len(files))

# 1. The executor's user records
ex = os.path.join(d, "agent-a46e715a6801b98ca.jsonl")
print("executor transcript exists:", os.path.exists(ex))
want = {"2026-09-25T19:37:50.383Z", "2026-09-24T19:37:50.383Z", "2026-09-24T23:48:49.313Z", "2026-09-25T23:48:49.313Z"}
users = []
with open(ex, encoding="utf-8") as fh:
    for raw in fh:
        try:
            rec = json.loads(raw)
        except ValueError:
            continue
        if rec.get("type") != "user":
            continue
        msg = rec.get("message", {})
        content = msg.get("content")
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            # skip tool results
            parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
            text = "\n".join(parts)
        if not text.strip():
            continue
        users.append((rec.get("timestamp"), text))
print("user text records:", len(users))
for ts, text in users:
    flags = {
        "unset": bool(re.search(r"\bunset\b", text, re.I)),
        "set-empty": bool(re.search(r'=""|to ""|to `""`|empty', text)),
        "expected-head": "--expected-head" in text,
        "scratch commit": bool(re.search(r"scratch commit", text, re.I)),
        "no PR": bool(re.search(r"(open|opens) no PR|never open|do not open|no PR", text, re.I)),
        "trailer": bool(re.search(r"trailer", text, re.I)),
        "spec files": [n for n in ("data_round3_original_brief.md", "data_round4_spec.md", "data_round4_redirect.md", "old_executor_summary.md") if n in text],
        "step 5": bool(re.search(r"step 5|5\.", text)),
    }
    print(ts, len(text), flags)
    # print the sentence(s) containing 'unset'
    for m in re.finditer(r"[^\n]{0,120}\bunset\b[^\n]{0,80}", text, re.I):
        print("   unset-context:", m.group(0)[:200])

# 2. tmpfs spec files
scr = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad"
for n in ("data_round3_original_brief.md", "data_round4_spec.md", "data_round4_redirect.md", "old_executor_summary.md"):
    hits = glob.glob(os.path.join(scr, "**", n), recursive=True)
    print("spec", n, [os.path.relpath(h, scr) for h in hits])

# 3. grep -l consolidated_r equivalent, and the ls -lt | head -4 view
hits = []
for f in files:
    with open(f, "rb") as fh:
        if b"consolidated_r" in fh.read():
            hits.append(os.path.basename(f))
print("transcripts containing 'consolidated_r':", len(hits))
for h in hits:
    st = os.stat(os.path.join(d, h))
    print("  ", h, time.strftime("%H:%M:%SZ", time.gmtime(st.st_mtime)))
entries = sorted(os.listdir(d), key=lambda n: -os.stat(os.path.join(d, n)).st_mtime)
print("newest 3 entries (ls -lt | head -4 shows 'total' + 3):")
for n in entries[:3]:
    st = os.stat(os.path.join(d, n))
    print("  ", n, time.strftime("%H:%M:%SZ", time.gmtime(st.st_mtime)))
print("non-jsonl entries in subagents dir:", [n for n in os.listdir(d) if not n.endswith(".jsonl")][:10])
