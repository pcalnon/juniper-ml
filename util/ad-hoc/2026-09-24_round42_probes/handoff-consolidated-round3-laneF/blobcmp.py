#!/usr/bin/env python3
"""Read-only: compare fizzy's copies of PR #2089's files with the PR head tree's blob shas.

Blob sha = sha1(b"blob %d\0" % len(data) + data). No VCS binary is invoked.
Also compares each handoff-validation lane directory against its scratch source.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.abspath(os.path.join(HERE, "..", ".."))
FIZZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"


def blob(path):
    with open(path, "rb") as fh:
        data = fh.read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


tree = {}
with open(os.path.join(HERE, "tree_a64d.txt")) as fh:
    for line in fh:
        line = line.rstrip("\n")
        if " " not in line:
            continue
        sha, p = line.split(" ", 1)
        tree[p] = sha

files = [l.strip() for l in open(os.path.join(HERE, "pr2089_files.txt")) if l.strip()]
same = diff = missing = 0
for f in files:
    lp = os.path.join(FIZZY, f)
    if not os.path.exists(lp):
        missing += 1
        print("MISSING-LOCAL", f)
        continue
    if f not in tree:
        print("NOT-IN-TREE", f)
        continue
    if blob(lp) == tree[f]:
        same += 1
    else:
        diff += 1
        print("DIFF", f)
print(f"PR files {len(files)}: identical {same}, differ {diff}, missing locally {missing}")

# Extra files in fizzy's probe dir that are not in the PR
probe_root = os.path.join(FIZZY, "util/ad-hoc/2026-09-24_round42_probes")
extra = []
for dp, dn, fn in os.walk(probe_root):
    dn[:] = [d for d in dn if d != "__pycache__"]
    for n in fn:
        rel = os.path.relpath(os.path.join(dp, n), FIZZY)
        if rel not in files:
            extra.append(rel)
print("fizzy probe files not in PR:", len(extra))
for e in extra[:20]:
    print("  EXTRA", e)

# Lane directory -> scratch source
MAP = {
    "handoff-2fba4397-round1-laneF": "hv1/laneF",
    "handoff-2fba4397-round2-laneF": "hv2/laneF2",
    "handoff-2fba4397-round3-laneF": "hv3/laneD",
    "handoff-consolidated-round1-laneF": "hc1/laneF",
    "handoff-consolidated-round2-laneF": "hc2/laneF",
    "handoff-consolidated-round2-laneP": "hc2/laneP",
}
for lane, src in MAP.items():
    sdir = os.path.join(SCR, src)
    pr_names = sorted(os.path.basename(f) for f in files if f.startswith("util/ad-hoc/2026-09-24_round42_probes/" + lane + "/"))
    if not os.path.isdir(sdir):
        print(f"{lane}: source {src} ABSENT; PR has {len(pr_names)}")
        continue
    src_py = sorted(n for n in os.listdir(sdir) if n.endswith(".py"))
    eq = 0
    neq = []
    for n in pr_names:
        sp = os.path.join(sdir, n)
        tp = "util/ad-hoc/2026-09-24_round42_probes/" + lane + "/" + n
        if os.path.exists(sp) and blob(sp) == tree.get(tp):
            eq += 1
        else:
            neq.append(n)
    only_src = sorted(set(src_py) - set(pr_names))
    print(f"{lane}: PR {len(pr_names)}, source .py {len(src_py)}, equal-to-source {eq}, not-equal {neq}, source-only .py {only_src}")
