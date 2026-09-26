#!/usr/bin/env python3
"""Lane B r2: which juniper-data routes call record_access, at the primer's era and now (read-only GitHub GETs).

For each ref: every route decorator in api/routes/datasets.py with its handler name and line, and whether
record_access is called inside that handler (by source span to the next decorator). Tests the scope
sentences the delta rewrote: "every single-dataset metadata read and every artifact download, though not by
the list, filter, /latest or versions reads".
"""
import base64
import json
import re
import subprocess

REPO = "pcalnon/juniper-data"
PATH = "juniper_data/api/routes/datasets.py"


def gh(path):
    return json.loads(subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True).stdout)


def text(ref):
    blob = gh(f"repos/{REPO}/contents/{PATH}?ref={ref}")
    if blob.get("content"):
        return base64.b64decode(blob["content"]).decode("utf-8")
    return base64.b64decode(gh(f"repos/{REPO}/git/blobs/{blob['sha']}")["content"]).decode("utf-8")


tags = gh(f"repos/{REPO}/tags?per_page=30")
print("tags:", ", ".join(t["name"] for t in tags[:12]))
for ref in ("v0.11.0", "1afc3484", "0f0f7e0e"):
    src = text(ref).split("\n")
    decos = [i for i, l in enumerate(src) if re.match(r"@router\.(get|post|put|patch|delete|head|api_route)\(", l.strip())]
    print(f"\n== {ref} ({len(src)} lines)")
    for k, i in enumerate(decos):
        end = decos[k + 1] if k + 1 < len(decos) else len(src)
        name = next((re.match(r"\s*(?:async\s+)?def\s+(\w+)", src[j]).group(1) for j in range(i, end) if re.match(r"\s*(?:async\s+)?def\s+(\w+)", src[j])), "?")
        calls = [j + 1 for j in range(i, end) if "record_access" in src[j] and not src[j].strip().startswith("#")]
        print(f"   :{i + 1:<5} {src[i].strip()[:62]:62} {name:32} record_access at {calls if calls else '-'}")
