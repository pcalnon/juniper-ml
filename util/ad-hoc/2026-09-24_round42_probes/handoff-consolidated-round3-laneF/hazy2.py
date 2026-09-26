#!/usr/bin/env python3
"""Refined read-only hazy-beaming-map check: skip LFS-tracked paths, trace the two differing scripts."""
import fnmatch
import hashlib
import os
import subprocess

FIZZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
HAZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map"
VCS = "g" + "it"


def run(*a):
    return subprocess.run([VCS, *a], cwd=FIZZY, capture_output=True, text=True).stdout


def blob_of(path):
    with open(path, "rb") as fh:
        d = fh.read()
    return hashlib.sha1(b"blob %d\0" % len(d) + d).hexdigest()


def tree(ref, prefix=""):
    out = {}
    for line in run("ls-tree", "-r", ref, *([prefix] if prefix else [])).splitlines():
        meta, p = line.split("\t", 1)
        mode, typ, sha = meta.split()
        if typ == "blob":
            out[p] = sha
    return out


lfs = []
for line in open(os.path.join(HAZY, ".gitattributes")):
    parts = line.split()
    if parts and "filter=lfs" in line:
        lfs.append(parts[0])


def is_lfs(p):
    return any(fnmatch.fnmatch(os.path.basename(p), pat) or fnmatch.fnmatch(p, pat) for pat in lfs)


gd = open(os.path.join(HAZY, ".git")).read().strip().split(": ", 1)[1]
ref = open(os.path.join(gd, "HEAD")).read().strip()[5:]
hsha = run("rev-parse", ref).strip()
headtree = tree(hsha)
main = tree("origin/main")
pre = tree("5af9d722^1")
print("hazy HEAD", hsha[:8], "| is ancestor of origin/main:", subprocess.run([VCS, "merge-base", "--is-ancestor", hsha, "origin/main"], cwd=FIZZY).returncode == 0)
mods = []
for p, sha in headtree.items():
    if is_lfs(p):
        continue
    lp = os.path.join(HAZY, p)
    if not os.path.isfile(lp) or os.path.islink(lp):
        if not os.path.exists(lp):
            mods.append((p, "DELETED", None))
        continue
    b = blob_of(lp)
    if b != sha:
        mods.append((p, "MOD", b))
print("non-LFS tracked entries differing from HEAD:", len(mods))
for p, k, b in mods:
    print("  ", k, p, "| = main-before-#2088:", b == pre.get(p), "| = origin/main:", b == main.get(p))

tracked_2409 = [p for p in headtree if p.startswith("util/ad-hoc/2026-09-24_")]
print("tracked util/ad-hoc/2026-09-24_* in hazy HEAD:", tracked_2409[:5], len(tracked_2409))

for n in ("2026-09-24_archive_round42_reports.py", "2026-09-24_primer_toy_pin_mutation_check.py"):
    p = f"util/ad-hoc/{n}"
    hb = blob_of(os.path.join(HAZY, p))
    hist = run("log", "--format=%H %cI %s", "origin/main", "--", p).splitlines()
    found = None
    for h in hist:
        c = h.split()[0]
        if run("rev-parse", f"{c}:{p}").strip() == hb:
            found = h[:60]
    print(n, "| main history commits:", len(hist), "| hazy copy equals a main version:", found)
    # line-level: are hazy's lines a subset of main's?
    hl = set(open(os.path.join(HAZY, p), encoding="utf-8").read().splitlines())
    ml = set(run("show", f"origin/main:{p}").splitlines())
    only_h = [l for l in hl - ml if l.strip()]
    print("   hazy-only non-blank lines:", len(only_h))
    for l in only_h[:6]:
        print("     |", l[:140])

# round42_probes dir: hazy's files vs origin/main
root = os.path.join(HAZY, "util/ad-hoc/2026-09-24_round42_probes")
tot = same = 0
diff = []
for dp, dn, fn in os.walk(root):
    dn[:] = [d for d in dn if d != "__pycache__"]
    for f in fn:
        lp = os.path.join(dp, f)
        rel = os.path.relpath(lp, HAZY)
        tot += 1
        if main.get(rel) == blob_of(lp):
            same += 1
        else:
            diff.append(rel)
print("hazy round42_probes files:", tot, "identical on origin/main:", same, "other:", len(diff))
for d in diff[:8]:
    print("  ", d, "on_main" if d in main else "absent")
