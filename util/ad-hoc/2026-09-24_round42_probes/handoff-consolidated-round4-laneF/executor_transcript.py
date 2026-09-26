#!/usr/bin/env python3
"""Round 4 lane F probe: read executor a46e715a6801b98ca's transcript (read-only).

Reports: first/last record timestamps; every user record that is plain text
(timestamp + length + first 80 chars); every Bash tool_use whose command mentions
push_signed_commit / open_signed_pr / gh pr create / git push, with its timestamp
and the first 300 chars of its result; the last record's type and content kinds.
Never prints environment values.
"""
import glob
import json
import sys

PAT = "/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl"
paths = glob.glob(PAT)
print("glob matches:", len(paths))
path = paths[0]
recs = []
with open(path, "rb") as fh:
    for raw in fh.read().split(b"\n"):
        if not raw.strip():
            continue
        try:
            recs.append(json.loads(raw))
        except Exception as exc:  # noqa: BLE001
            print("bad line", exc)
print("records:", len(recs))
ts = [r.get("timestamp") for r in recs if r.get("timestamp")]
print("first ts:", ts[0], "last ts:", ts[-1])

# plain-text user records
print("\n== plain-text user records ==")
for r in recs:
    if r.get("type") != "user":
        continue
    msg = r.get("message", {})
    c = msg.get("content")
    if isinstance(c, str):
        print(r.get("timestamp"), len(c), repr(c[:80]))
    elif isinstance(c, list):
        kinds = [x.get("type") for x in c if isinstance(x, dict)]
        if kinds and all(k == "text" for k in kinds):
            t = "".join(x.get("text", "") for x in c)
            print(r.get("timestamp"), len(t), repr(t[:80]))

# tool uses of interest
keys = ("push_signed_commit", "open_signed_pr", "gh pr create", "git push", "createCommitOnBranch", "pr create")
uses = {}
for r in recs:
    if r.get("type") != "assistant":
        continue
    for x in r.get("message", {}).get("content", []) or []:
        if isinstance(x, dict) and x.get("type") == "tool_use":
            cmd = json.dumps(x.get("input", {}))
            if any(k in cmd for k in keys):
                uses[x.get("id")] = (r.get("timestamp"), cmd)
print("\n== tool uses mentioning push/PR ==")
results = {}
for r in recs:
    if r.get("type") != "user":
        continue
    c = r.get("message", {}).get("content")
    if isinstance(c, list):
        for x in c:
            if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("tool_use_id") in uses:
                cc = x.get("content")
                if isinstance(cc, list):
                    cc = "".join(y.get("text", "") for y in cc if isinstance(y, dict))
                results[x.get("tool_use_id")] = (r.get("timestamp"), str(cc))
for k, (t, cmd) in uses.items():
    print("---", t, cmd[:400])
    if k in results:
        rt, out = results[k]
        print("   result at", rt, ":", out[:600].replace("\n", " | "))

# last record
last = recs[-1]
print("\n== last record ==")
print(last.get("type"), last.get("timestamp"))
c = last.get("message", {}).get("content")
if isinstance(c, list):
    print("content kinds:", [x.get("type") for x in c if isinstance(x, dict)])
elif isinstance(c, str):
    print("content str len", len(c))
