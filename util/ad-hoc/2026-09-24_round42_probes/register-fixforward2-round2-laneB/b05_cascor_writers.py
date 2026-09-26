#!/usr/bin/env python3
"""Lane B r2: _dataset_shortfall writers in juniper-cascor's manager.py at several SHAs (read-only GitHub GETs).

For each ref: every line assigning self._dataset_shortfall, with its enclosing def, plus where ec8b5bdb sits
relative to #678's and #688's merge commits on main.
"""
import base64
import json
import re
import subprocess

PATH = "src/api/lifecycle/manager.py"
REPO = "pcalnon/juniper-cascor"


def gh(path: str):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def source(ref: str) -> "list[str]":
    blob = gh(f"repos/{REPO}/contents/{PATH}?ref={ref}")
    if blob.get("encoding") == "base64" and blob.get("content"):
        return base64.b64decode(blob["content"]).decode("utf-8").split("\n")
    # large file: fetch via git blob
    data = gh(f"repos/{REPO}/git/blobs/{blob['sha']}")
    return base64.b64decode(data["content"]).decode("utf-8").split("\n")


def writers(lines: "list[str]"):
    out = []
    for i, line in enumerate(lines, 1):
        if re.search(r"self\._dataset_shortfall\s*(:[^=]*)?=(?!=)", line):
            fn = "?"
            for j in range(i - 1, -1, -1):
                m = re.match(r"\s*(?:async\s+)?def\s+(\w+)", lines[j])
                if m:
                    fn = m.group(1)
                    break
            out.append((i, fn, line.strip()[:110]))
    return out


refs = {
    "678-parent": gh(f"repos/{REPO}/commits/0e016a7c")["parents"][0]["sha"][:8],
    "678-merge": "0e016a7c",
    "ec8b5bdb": "ec8b5bdb",
    "688-merge": "7f4a7213",
    "690-head": gh(f"repos/{REPO}/pulls/690")["head"]["sha"][:8],
}
for label, ref in refs.items():
    c = gh(f"repos/{REPO}/commits/{ref}")
    print(f"== {label} {ref} {c['commit']['committer']['date']} {c['commit']['message'].splitlines()[0][:90]}")
    for i, fn, text in writers(source(ref)):
        print(f"   :{i:<5} {fn:32} {text}")

for a, b in (("0e016a7c", "ec8b5bdb"), ("ec8b5bdb", "7f4a7213")):
    cmp = gh(f"repos/{REPO}/compare/{a}...{b}")
    print(f"compare {a}...{b}: status={cmp['status']} ahead={cmp['ahead_by']} behind={cmp['behind_by']}")
    for c in cmp.get("commits", []):
        print(f"    {c['sha'][:8]} {c['commit']['message'].splitlines()[0][:100]}")
