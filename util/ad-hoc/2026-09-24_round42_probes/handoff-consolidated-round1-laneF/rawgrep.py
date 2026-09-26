"""raw substring search over JSONL lines: print timestamp, type and a snippet for each line containing the needle."""
import json, sys
path, needle = sys.argv[1], sys.argv[2]
ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 120
for line in open(path, encoding="utf-8").read().split("\n"):
    i = line.find(needle)
    if i < 0:
        continue
    try:
        r = json.loads(line)
    except Exception:
        r = {}
    print(r.get("timestamp"), r.get("type"), r.get("isMeta"), "::", line[max(0, i - ctx): i + len(needle) + ctx].replace("\\n", " | "))
