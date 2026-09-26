"""List memory files a transcript Edit/Write'd (or touched by Bash), with first/last timestamps, from a start time."""
import json, re, sys
path, since = sys.argv[1], sys.argv[2]
seen = {}
pat = re.compile(r"/\.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/([A-Za-z0-9_.\-]+\.md)")
for line in open(path, encoding="utf-8").read().split("\n"):
    if not line.strip():
        continue
    r = json.loads(line)
    if r.get("type") != "assistant" or (r.get("timestamp") or "") < since:
        continue
    for b in (r.get("message") or {}).get("content") or []:
        if not isinstance(b, dict) or b.get("type") != "tool_use":
            continue
        name = b.get("name")
        inp = b.get("input") or {}
        if name in ("Edit", "Write"):
            m = pat.search(inp.get("file_path", ""))
            if m:
                seen.setdefault(m.group(1), []).append((r["timestamp"], name))
        elif name == "Bash":
            cmd = inp.get("command", "")
            if re.search(r"(>|>>|sed -i|mv |cp |tee )[^|;&]*memory/", cmd):
                for m in pat.finditer(cmd):
                    seen.setdefault(m.group(1), []).append((r["timestamp"], "Bash-write?"))
for k, v in sorted(seen.items()):
    print(k, len(v), v[0][0], v[-1][0], sorted(set(x[1] for x in v)))
