"""Which transcript issued a Write/Edit on a given path? Usage: who_wrote.py <needle> <jsonl> [<jsonl> ...]. Read-only."""
import json
import sys

needle = sys.argv[1]
for path in sys.argv[2:]:
    raw = open(path, encoding="utf-8").read()
    for line in raw.split("\n"):
        if not line.strip():
            continue
        r = json.loads(line)
        msg = r.get("message")
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        for part in msg.get("content") or []:
            if isinstance(part, dict) and part.get("type") == "tool_use" and part.get("name") in ("Write", "Edit", "MultiEdit"):
                fp = (part.get("input") or {}).get("file_path", "")
                if needle in fp:
                    print(path.rsplit("/", 1)[-1], r.get("timestamp"), part.get("name"), fp)
