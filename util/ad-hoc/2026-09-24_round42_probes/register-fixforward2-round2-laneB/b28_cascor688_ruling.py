#!/usr/bin/env python3
"""Lane B r2: does juniper-cascor#688 apply the mixed-provenance ruling, including `current_dataset`? (read-only GETs)"""
import json
import re
import subprocess


def gh(path):
    return json.loads(subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True).stdout)


pr = gh("repos/pcalnon/juniper-cascor/pulls/688")
body = pr.get("body") or ""
print("body chars:", len(body))
for line in body.split("\n"):
    if re.search(r"current_dataset|ruling|mixed|provenance|any (fetched )?split|partition", line, re.I):
        print("  |", line.strip()[:220])
files = gh("repos/pcalnon/juniper-cascor/pulls/688/files?per_page=100")
print("files:", [f["filename"] for f in files])
for f in files:
    if f["filename"].endswith("manager.py"):
        added = [l[1:] for l in (f.get("patch") or "").split("\n") if l.startswith("+") and "current_dataset" in l]
        print(f"  manager.py: {len(added)} added lines mention current_dataset")
        for l in added[:8]:
            print("    +", l.strip()[:150])
