#!/usr/bin/env python3
"""Lane B r2: juniper-data's generate_dataset_id in full at main (read-only GET), to judge primer 5481's
"``{generator}-v{version}-{digest16}`` -- the real juniper-data scheme"."""
import base64
import json
import subprocess

blob = json.loads(subprocess.run(["gh", "api", "repos/pcalnon/juniper-data/contents/juniper_data/core/dataset_id.py?ref=0f0f7e0e"], capture_output=True, text=True, check=True).stdout)
src = base64.b64decode(blob["content"]).decode("utf-8").split("\n")
for i, line in enumerate(src[22:75], 23):
    print(f"{i:3}: {line}")
