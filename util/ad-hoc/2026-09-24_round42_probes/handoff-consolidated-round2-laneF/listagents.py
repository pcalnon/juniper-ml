import json, pathlib, re, sys
P = pathlib.Path.home() / ".claude" / "projects"
hits = sorted(P.glob("*/2fba4397-7d9b-4929-8ca2-375b8168e1c8.jsonl"))
print("transcripts:", [str(h) for h in hits])
path = hits[0]
ids = {}
with open(path, encoding="utf-8") as fh:
    data = fh.read().split("\n")
for line in data:
    if not line.strip():
        continue
    try:
        rec = json.loads(line)
    except Exception:
        continue
    msg = rec.get("message") or {}
    content = msg.get("content")
    if not isinstance(content, list):
        continue
    for b in content:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "tool_use" and b.get("name") in ("ListAgents",):
            ids[b["id"]] = rec.get("timestamp")
            print("CALL", rec.get("timestamp"), b.get("name"), json.dumps(b.get("input"))[:100])
        elif b.get("type") == "tool_result" and b.get("tool_use_id") in ids:
            c = b.get("content")
            if isinstance(c, list):
                c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
            c = str(c)
            # print only names with [ref] and state words
            names = re.findall(r'[\w .-]*\[[0-9a-f]{6}\][^\n]{0,80}', c)
            print("RESULT", rec.get("timestamp"), "len", len(c))
            for n in names[:30]:
                print("   ", n.strip()[:140])
