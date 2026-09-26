"""Every record (any type) whose serialized form mentions a cross-session message, in a window. Read-only."""
import json
import sys

P = "/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-fizzy-hugging-dream/2fba4397-7d9b-4929-8ca2-375b8168e1c8.jsonl"
lo, hi = sys.argv[1], sys.argv[2]
needle = sys.argv[3] if len(sys.argv) > 3 else "cross-session-message"
raw = open(P, encoding="utf-8").read()
for line in raw.split("\n"):
    if not line.strip() or needle not in line:
        continue
    r = json.loads(line)
    ts = r.get("timestamp", "")
    if not (lo <= ts <= hi):
        continue
    blob = json.dumps(r, ensure_ascii=False)
    i = blob.find(needle)
    print("===", ts, r.get("type"))
    print(blob[max(0, i - 50): i + 1100].replace("\\n", "\n"))
