#!/usr/bin/env python3
"""Round 4 lane F probe: the sandbox refusals recorded in round 3's lane P transcript
(abc3fd42a271ebb61), for r4 L139's "a heredoc inside a compound command". Prints the refused
command's first 200 chars and the refusal's first 200 chars. Read-only."""
import glob
import json

path = glob.glob("/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-abc3fd42a271ebb61.jsonl")[0]
recs = [json.loads(x) for x in open(path, "rb").read().split(b"\n") if x.strip()]
cmds = {}
for r in recs:
    if r.get("type") == "assistant":
        for x in r.get("message", {}).get("content", []) or []:
            if isinstance(x, dict) and x.get("type") == "tool_use":
                cmds[x["id"]] = json.dumps(x.get("input", {}))[:200]
for r in recs:
    if r.get("type") != "user" or not isinstance(r.get("message", {}).get("content"), list):
        continue
    for x in r["message"]["content"]:
        if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("is_error"):
            cc = x.get("content")
            if isinstance(cc, list):
                cc = "".join(y.get("text", "") for y in cc if isinstance(y, dict))
            cc = str(cc)
            if any(k in cc.lower() for k in ("refus", "denied", "not allowed", "permission")):
                print("---", r.get("timestamp"))
                print("  CMD:", cmds.get(x.get("tool_use_id"), "?"))
                print("  ERR:", cc[:200].replace("\n", " | "))
