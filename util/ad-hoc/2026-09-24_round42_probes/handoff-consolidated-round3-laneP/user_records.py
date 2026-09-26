"""List user records with plain-text content in an agent transcript (read-only; lane P r3)."""
import glob
import json
import sys

pat = "/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-" + sys.argv[1] + ".jsonl"
hits = glob.glob(pat)
print("transcripts:", len(hits))
for path in hits:
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(x) for x in fh.read().split("\n") if x.strip()]
    print("records:", len(rows))
    for r in rows:
        if r.get("type") != "user":
            continue
        c = r.get("message", {}).get("content")
        if isinstance(c, str):
            text = c
        elif isinstance(c, list):
            text = "".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
        else:
            text = ""
        if text.strip():
            print(r.get("timestamp"), len(text), repr(text[:90]))
    last = [r for r in rows if r.get("type") == "assistant"][-1]
    kinds = [b.get("type") for b in last["message"]["content"]]
    print("last assistant blocks:", kinds, "last record type:", rows[-1].get("type"))
