#!/usr/bin/env python3
"""Lane B r2: what real juniper-data does with an explicit `seed: null`, at its main (read-only GitHub GETs).

Prints generate_dataset_id, and for every generator params model the declaration of its `seed` field, so the
5346 sentence ("the `seed: null` that E.1 describes the real service reading as a request for a fresh nonce")
can be checked against source.
"""
import base64
import json
import re
import subprocess

REPO = "pcalnon/juniper-data"


def gh(path):
    return json.loads(subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True).stdout)


def text(path, ref):
    blob = gh(f"repos/{REPO}/contents/{path}?ref={ref}")
    return base64.b64decode(blob["content"]).decode("utf-8")


main_sha = gh(f"repos/{REPO}/commits/main")["sha"][:8]
print("juniper-data main =", main_sha)
src = text("juniper_data/core/dataset_id.py", main_sha)
for i, line in enumerate(src.split("\n"), 1):
    if re.search(r"seed|nonce|def generate_dataset_id|uuid|token_hex|None", line):
        print(f"  dataset_id.py:{i}: {line.rstrip()[:130]}")

tree = gh(f"repos/{REPO}/git/trees/{main_sha}?recursive=1")["tree"]
params_files = [t["path"] for t in tree if t["path"].startswith("juniper_data/generators/") and t["path"].endswith("params.py")]
print(f"\n{len(params_files)} generator params files")
for pf in sorted(params_files):
    s = text(pf, main_sha)
    hits = [f"{i}: {l.strip()[:110]}" for i, l in enumerate(s.split("\n"), 1) if re.match(r"\s*seed\s*:", l)]
    print(f"  {pf.split('/')[2]:22} {hits if hits else 'NO seed field'}")
