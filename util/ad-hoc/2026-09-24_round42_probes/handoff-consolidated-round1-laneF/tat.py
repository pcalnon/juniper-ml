"""print the full text of records at given timestamps (prefix match) in a JSONL transcript."""
import json, sys
path = sys.argv[1]; stamps = sys.argv[2].split(","); maxc = int(sys.argv[3]) if len(sys.argv) > 3 else 4000
with open(path, encoding="utf-8") as f:
    data = f.read()
for line in data.split("\n"):
    if not line.strip():
        continue
    r = json.loads(line)
    ts = r.get("timestamp") or ""
    if not any(ts.startswith(s) for s in stamps):
        continue
    msg = r.get("message") or {}
    c = msg.get("content") if isinstance(msg, dict) else None
    out = []
    if isinstance(c, str):
        out.append(c)
    elif isinstance(c, list):
        for b in c:
            if b.get("type") == "text":
                out.append("[text] " + b.get("text", ""))
            elif b.get("type") == "tool_use":
                out.append("[tool_use " + str(b.get("name")) + "] " + json.dumps(b.get("input"), ensure_ascii=False))
            elif b.get("type") == "tool_result":
                cc = b.get("content")
                if isinstance(cc, list):
                    cc = "\n".join(x.get("text", "") for x in cc if isinstance(x, dict))
                out.append("[tool_result] " + str(cc))
    print(f"=== {ts} {r.get('type')} isMeta={r.get('isMeta')}")
    print("\n".join(out)[:maxc])
