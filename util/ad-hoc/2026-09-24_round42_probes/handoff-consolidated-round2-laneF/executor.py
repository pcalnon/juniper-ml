import json, pathlib
P = pathlib.Path.home() / ".claude" / "projects"
hits = sorted(P.glob("*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl"))
print([str(h) for h in hits])
path = hits[0]
recs = []
with open(path, encoding="utf-8") as fh:
    for line in fh.read().split("\n"):
        if line.strip():
            try:
                recs.append(json.loads(line))
            except Exception:
                pass
print("records", len(recs))
last = recs[-1]
print("last ts", last.get("timestamp"), last.get("type"))
# last assistant text
for r in reversed(recs):
    m = r.get("message") or {}
    if r.get("type") == "assistant":
        c = m.get("content")
        kinds = [b.get("type") for b in c] if isinstance(c, list) else ["str"]
        print("last assistant", r.get("timestamp"), kinds)
        if "text" in kinds:
            t = "\n".join(b.get("text", "") for b in c if b.get("type") == "text")
            print("len", len(t))
            print(t[:600])
        break
# find push commands
for r in recs:
    m = r.get("message") or {}
    c = m.get("content")
    if isinstance(c, list):
        for b in c:
            if b.get("type") == "tool_use":
                cmd = json.dumps(b.get("input"))
                if "push_signed_commit" in cmd and "--dry-run" not in cmd:
                    print("PUSH CMD", r.get("timestamp"), cmd[:300])
