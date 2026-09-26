"""list user records that are NOT tool results (i.e. prompts / SendMessage deliveries) in a transcript, and time gaps."""
import json, sys, datetime as dt
path = sys.argv[1]
rows = [json.loads(l) for l in open(path, encoding="utf-8").read().split("\n") if l.strip()]
def ts(r):
    t = r.get("timestamp")
    return dt.datetime.fromisoformat(t.replace("Z", "+00:00")) if t else None
for r in rows:
    if r.get("type") != "user":
        continue
    c = (r.get("message") or {}).get("content")
    if isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
        continue
    text = c if isinstance(c, str) else "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    print(f"USER {r.get('timestamp')} isMeta={r.get('isMeta')} len={len(text)} :: {text[:300]!r}")
stamps = [ts(r) for r in rows if ts(r)]
print("first", stamps[0], "last", stamps[-1], "records", len(rows))
gaps = sorted(((b - a).total_seconds(), a, b) for a, b in zip(stamps, stamps[1:]))[-8:]
for g, a, b in gaps:
    print(f"gap {g:.0f}s {a} -> {b}")
