#!/usr/bin/env python3
"""Round 4 lane F probe: are fizzy's untracked copies of juniper-ml#2089's files byte-identical to
its head 669b2c75 (r4 L188)? Also lists fizzy files under #2089's paths that the PR does not carry,
and the copier's / pusher's lane-list variable names (r4 L195). Read-only (gh api GETs; open())."""
import hashlib
import json
import os
import re
import subprocess

FIZZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
HEAD = "669b2c7588b61889f5236c07f196df0510122409"
PREFIXES = (
    "util/ad-hoc/2026-09-24_round42_probes/",
    "util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py",
    "util/ad-hoc/2026-09-24_open_round42_session2fba4397_probes_pr.py",
    "util/ad-hoc/2026-09-24_push_round42_handoff_probes_to_2089.py",
)


def blob_sha(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


p = subprocess.run(["gh", "api", "--paginate", "repos/pcalnon/juniper-ml/pulls/2089/files?per_page=100", "--jq", ".[].filename"], capture_output=True, text=True)
files = p.stdout.split()
t = json.loads(subprocess.run(["gh", "api", f"repos/pcalnon/juniper-ml/git/trees/{HEAD}?recursive=1"], capture_output=True, text=True).stdout)
print("tree truncated:", t.get("truncated"))
tree = {e["path"]: e["sha"] for e in t["tree"] if e["type"] == "blob"}
same = differ = missing = 0
for f in files:
    full = os.path.join(FIZZY, f)
    if not os.path.isfile(full):
        missing += 1
        print("  MISSING in fizzy:", f)
        continue
    with open(full, "rb") as fh:
        b = blob_sha(fh.read())
    if tree.get(f) == b:
        same += 1
    else:
        differ += 1
        print("  DIFFERS:", f)
print(f"#2089 files: {len(files)}; identical {same}, differ {differ}, missing {missing}")
extra = []
for root, dirs, fnames in os.walk(os.path.join(FIZZY, "util/ad-hoc/2026-09-24_round42_probes")):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for fn in fnames:
        rel = os.path.relpath(os.path.join(root, fn), FIZZY)
        if rel not in files:
            extra.append(rel)
print("fizzy files under the probes dir that #2089 lacks:", extra)
for name in ("util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py", "util/ad-hoc/2026-09-24_push_round42_handoff_probes_to_2089.py"):
    with open(os.path.join(FIZZY, name), encoding="utf-8") as fh:
        src = fh.read()
    names = re.findall(r"^([A-Z][A-Z0-9_]+)\s*=", src, re.M)
    print(os.path.basename(name), "module constants:", names)
