#!/usr/bin/env python3
"""Read-only check of the hazy-beaming-map worktree claims (Appendix F).

Reads hazy's files with open(); runs VCS plumbing only in fizzy (the shared object store), never in hazy.
"""
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
    for line in run("ls-tree", "-r", ref, *( [prefix] if prefix else [])).splitlines():
        meta, p = line.split("\t", 1)
        mode, typ, sha = meta.split()
        if typ == "blob":
            out[p] = sha
    return out


print("hazy exists:", os.path.isdir(HAZY))
gitfile = open(os.path.join(HAZY, ".git")).read().strip()
gd = gitfile.split(": ", 1)[1]
head = open(os.path.join(gd, "HEAD")).read().strip()
if head.startswith("ref: "):
    ref = head[5:]
    hsha = run("rev-parse", ref).strip()
    print("hazy HEAD ref", ref, hsha[:8])
else:
    hsha = head
    print("hazy HEAD detached", hsha[:8])

main = tree("origin/main")
pre2088 = tree("5af9d722^1")
at2088 = tree("5af9d722")
headtree = tree(hsha)

# untracked 2026-09-24 ad-hoc scripts
adhoc = sorted(n for n in os.listdir(os.path.join(HAZY, "util/ad-hoc")) if n.startswith("2026-09-24_"))
untracked = [n for n in adhoc if f"util/ad-hoc/{n}" not in headtree]
print("hazy util/ad-hoc/2026-09-24_* entries:", len(adhoc), "untracked:", len(untracked))
eq = [n for n in untracked if os.path.isfile(os.path.join(HAZY, "util/ad-hoc", n)) and main.get(f"util/ad-hoc/{n}") == blob_of(os.path.join(HAZY, "util/ad-hoc", n))]
dirs = [n for n in untracked if os.path.isdir(os.path.join(HAZY, "util/ad-hoc", n))]
print("  untracked files byte-identical on origin/main:", len(eq), "of", len(untracked) - len(dirs), "files;", "dirs:", dirs)
for n in untracked:
    p = os.path.join(HAZY, "util/ad-hoc", n)
    if os.path.isfile(p) and n not in eq:
        print("  NOT-EQUAL/ABSENT on main:", n, "on_main" if f"util/ad-hoc/{n}" in main else "absent")

# tracked modifications (working copy vs HEAD blob)
mods = []
for p, sha in headtree.items():
    lp = os.path.join(HAZY, p)
    if not os.path.exists(lp):
        mods.append((p, "DELETED"))
        continue
    if os.path.islink(lp) or not os.path.isfile(lp):
        continue
    if blob_of(lp) != sha:
        mods.append((p, "MOD"))
print("tracked entries differing from hazy HEAD:", len(mods))
for p, kind in mods[:20]:
    lp = os.path.join(HAZY, p)
    b = blob_of(lp) if kind == "MOD" else None
    print("  ", kind, p, "| = main-before-2088:", b == pre2088.get(p), "| = main-at-2088:", b == at2088.get(p), "| = origin/main:", b == main.get(p))
