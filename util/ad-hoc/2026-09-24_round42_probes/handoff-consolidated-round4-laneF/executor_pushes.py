#!/usr/bin/env python3
"""Round 4 lane F probe: print the tail of each real (non-dry-run) signed push result in
executor a46e715a6801b98ca's transcript, to read the commit sha it created. Read-only."""
import glob
import json

path = glob.glob("/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl")[0]
recs = []
with open(path, "rb") as fh:
    for raw in fh.read().split(b"\n"):
        if raw.strip():
            recs.append(json.loads(raw))
uses = {}
for r in recs:
    if r.get("type") != "assistant":
        continue
    for x in r.get("message", {}).get("content", []) or []:
        if isinstance(x, dict) and x.get("type") == "tool_use":
            cmd = x.get("input", {}).get("command", "")
            if "push_signed_commit.py --repo" in cmd:
                uses[x["id"]] = (r.get("timestamp"), "--dry-run" in cmd)
for r in recs:
    if r.get("type") != "user":
        continue
    c = r.get("message", {}).get("content")
    if not isinstance(c, list):
        continue
    for x in c:
        if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("tool_use_id") in uses:
            cc = x.get("content")
            if isinstance(cc, list):
                cc = "".join(y.get("text", "") for y in cc if isinstance(y, dict))
            t, dry = uses[x["tool_use_id"]]
            lines = str(cc).splitlines()
            print("=====", t, "dry-run flag:", dry, "is_error:", x.get("is_error"), "result at", r.get("timestamp"))
            for ln in lines[:3]:
                print("  HEAD|", ln[:200])
            for ln in lines[-12:]:
                print("  TAIL|", ln[:200])
# any gh pr create / open_signed_pr execution (not reading)
print("\n== commands that could open a PR ==")
for r in recs:
    if r.get("type") != "assistant":
        continue
    for x in r.get("message", {}).get("content", []) or []:
        if isinstance(x, dict) and x.get("type") == "tool_use":
            cmd = x.get("input", {}).get("command", "")
            if ("gh pr create" in cmd) or ("open_signed_pr.py --" in cmd) or ("python3 util/open_signed_pr.py" in cmd):
                print(r.get("timestamp"), cmd[:300])
