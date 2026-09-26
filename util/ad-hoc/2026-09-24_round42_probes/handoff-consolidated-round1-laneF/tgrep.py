"""grep a JSONL transcript: print timestamp, record type, role and a snippet around each match."""
import json, re, sys
path, pat = sys.argv[1], re.compile(sys.argv[2])
types = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] else None
ctx = int(sys.argv[4]) if len(sys.argv) > 4 else 150
maxhits = int(sys.argv[5]) if len(sys.argv) > 5 else 40
n = 0
with open(path, encoding="utf-8") as f:
    data = f.read()
for line in data.split("\n"):
    if not line.strip():
        continue
    try:
        r = json.loads(line)
    except Exception:
        continue
    t = r.get("type")
    if types and t not in types:
        continue
    msg = r.get("message") or {}
    content = msg.get("content") if isinstance(msg, dict) else None
    texts = []
    if isinstance(content, str):
        texts.append(("str", content))
    elif isinstance(content, list):
        for b in content:
            if not isinstance(b, dict):
                continue
            bt = b.get("type")
            if bt == "text":
                texts.append(("text", b.get("text", "")))
            elif bt == "tool_use":
                texts.append(("tool_use:" + str(b.get("name")), json.dumps(b.get("input"), ensure_ascii=False)))
            elif bt == "tool_result":
                c = b.get("content")
                if isinstance(c, list):
                    c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
                texts.append(("tool_result", str(c)))
    if r.get("toolUseResult") and not texts:
        texts.append(("tur", json.dumps(r.get("toolUseResult"), ensure_ascii=False)))
    for kind, tx in texts:
        for m in pat.finditer(tx):
            s = max(0, m.start() - ctx); e = min(len(tx), m.end() + ctx)
            snippet = tx[s:e].replace("\n", " | ")
            print(f"{r.get('timestamp')} {t} {kind} meta={r.get('isMeta')} :: {snippet}")
            n += 1
            break
        if n >= maxhits:
            sys.exit(0)
