#!/usr/bin/env python3
"""Round 4 lane F probe: can the 62f9b2bf draft of document 2 be rebuilt from session bc31e993's
transcript? Replays every Write/Edit to document 2's path in order (in memory only), and after each
step checks whether the sha256 prefix is 62f9b2bf or 4ebd0143. Writes nothing. Read-only."""
import glob
import hashlib
import json

DOC2 = "HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md"
path = glob.glob("/home/pcalnon/.claude/projects/*/bc31e993-97b0-4a01-ae04-cb39593eb647.jsonl")[0]
recs = []
with open(path, "rb") as fh:
    for raw in fh.read().split(b"\n"):
        if raw.strip():
            try:
                recs.append(json.loads(raw))
            except json.JSONDecodeError:
                pass
ops = []
results = {}
for r in recs:
    if r.get("type") == "user" and isinstance(r.get("message", {}).get("content"), list):
        for x in r["message"]["content"]:
            if isinstance(x, dict) and x.get("type") == "tool_result":
                results[x.get("tool_use_id")] = bool(x.get("is_error"))
for r in recs:
    if r.get("type") != "assistant":
        continue
    for x in r.get("message", {}).get("content", []) or []:
        if isinstance(x, dict) and x.get("type") == "tool_use" and x.get("name") in ("Write", "Edit"):
            inp = x.get("input", {})
            if str(inp.get("file_path", "")).endswith(DOC2):
                ops.append((r.get("timestamp"), x.get("name"), inp, x.get("id")))
print("ops on document 2:", len(ops))
content = None
for ts, name, inp, tid in ops:
    err = results.get(tid)
    if err:
        print(ts, name, "ERRORED, skipped")
        continue
    if name == "Write":
        content = inp["content"]
    elif content is not None:
        old, new = inp["old_string"], inp["new_string"]
        if inp.get("replace_all"):
            content = content.replace(old, new)
        else:
            if content.count(old) != 1:
                print(ts, "Edit old_string count", content.count(old), "-> replay diverged")
            content = content.replace(old, new, 1)
    if content is not None:
        s = hashlib.sha256(content.encode("utf-8")).hexdigest()
        print(ts, name, s[:16], len(content.encode("utf-8")), "bytes", "<-- 62f9b2bf" if s.startswith("62f9b2bf") else ("<-- 4ebd0143 (2e4917c2)" if s.startswith("4ebd0143") else ""))
