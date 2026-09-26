#!/usr/bin/env python3
"""Round 4 lane F probe: re-measure Appendix F's hazy-beaming-map counts.

Reads hazy's files with open() only, and hazy's index file (binary, read-only) to know
what is tracked. Git runs ONLY in fizzy (this lane's cwd) and only read-only plumbing on
existing objects (rev-parse, ls-tree, cat-file, merge-base --is-ancestor). Never git -C
into hazy.
"""
import hashlib
import os
import struct
import subprocess

FIZZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
HAZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map"
INDEX = "/home/pcalnon/Development/python/Juniper/juniper-ml/.git/worktrees/hazy-beaming-map/index"


def git(*args):
    p = subprocess.run(["git", "--no-optional-locks", *args], cwd=FIZZY, capture_output=True)
    return p.returncode, p.stdout


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def read(path):
    with open(path, "rb") as fh:
        return fh.read()


def parse_index(path):
    data = read(path)
    assert data[:4] == b"DIRC", data[:4]
    version, count = struct.unpack(">II", data[4:12])
    entries = {}
    off = 12
    for _ in range(count):
        start = off
        sha = data[off + 40: off + 60].hex()
        flags = struct.unpack(">H", data[off + 60: off + 62])[0]
        off += 62
        if version >= 3 and (flags & 0x4000):
            off += 2
        if version == 4:
            raise SystemExit("index v4 not handled")
        nul = data.index(b"\0", off)
        name = data[off:nul].decode("utf-8", "surrogateescape")
        off = nul + 1
        # pad to multiple of 8 from entry start
        entlen = off - start
        pad = (8 - (entlen % 8)) % 8
        off += pad
        entries[name] = sha
    return version, entries


rc, out = git("rev-parse", "worktree-hazy-beaming-map")
hazy_head = out.decode().strip()
print("hazy HEAD (worktree-hazy-beaming-map):", hazy_head[:8])
rc, out = git("rev-parse", "origin/main")
main = out.decode().strip()
print("origin/main:", main[:8])

version, idx = parse_index(INDEX)
print("hazy index version", version, "entries", len(idx))


def tree_blobs(rev, prefix):
    rc, out = git("ls-tree", "-r", rev, "--", prefix)
    m = {}
    for line in out.decode().splitlines():
        meta, path = line.split("\t", 1)
        m[path] = meta.split()[2]
    return m


adhoc = os.path.join(HAZY, "util/ad-hoc")
entries = sorted(e for e in os.listdir(adhoc) if e.startswith("2026-09-24_"))
print("\n16 entries?", len(entries))
main_adhoc = tree_blobs(main, "util/ad-hoc/")
tracked_s, untracked_s, untracked_d, tracked_d = [], [], [], []
for e in entries:
    rel = "util/ad-hoc/" + e
    full = os.path.join(HAZY, rel)
    if os.path.isdir(full):
        is_tracked = any(k.startswith(rel + "/") for k in idx)
        (tracked_d if is_tracked else untracked_d).append(e)
    else:
        (tracked_s if rel in idx else untracked_s).append(e)
print("tracked scripts:", tracked_s)
print("untracked scripts:", len(untracked_s))
print("untracked dirs:", untracked_d, "tracked dirs:", tracked_d)
same, diff = [], []
for e in untracked_s:
    rel = "util/ad-hoc/" + e
    b = blob_sha(read(os.path.join(HAZY, rel)))
    (same if main_adhoc.get(rel) == b else diff).append((e, b, main_adhoc.get(rel)))
print("untracked identical to origin/main:", len(same))
for e, b, m in diff:
    print("  DIFFERS:", e, "hazy", b[:8], "main", (m or "ABSENT")[:8])
    # find which main commit had this blob
    rc, out = git("log", "--format=%h", main, "--", "util/ad-hoc/" + e)
    for h in out.decode().split():
        rc2, out2 = git("rev-parse", f"{h}:util/ad-hoc/{e}")
        if out2.decode().strip() == b:
            print("     equals the file as at main commit", h)
            break
    else:
        print("     no main commit holds this blob")
for e in tracked_s:
    rel = "util/ad-hoc/" + e
    b = blob_sha(read(os.path.join(HAZY, rel)))
    print("tracked", e, "worktree==index:", idx[rel] == b, "==main:", main_adhoc.get(rel) == b)

# probes dir
pd = "util/ad-hoc/2026-09-24_round42_probes"
files = []
for root, _dirs, fnames in os.walk(os.path.join(HAZY, pd)):
    for f in fnames:
        files.append(os.path.relpath(os.path.join(root, f), HAZY))
main_probes = tree_blobs(main, pd + "/")
same_p, diff_p = 0, []
for rel in files:
    b = blob_sha(read(os.path.join(HAZY, rel)))
    if main_probes.get(rel) == b:
        same_p += 1
    else:
        diff_p.append((rel, b, main_probes.get(rel)))
print("\nprobes dir files:", len(files), "identical to main:", same_p)
for rel, b, m in diff_p:
    print("  DIFFERS:", rel, "hazy", b[:8], "main", (m or "ABSENT")[:8])

# tracked edits
print("\n== tracked files differing from hazy HEAD (worktree vs HEAD blob) ==")
head_all = tree_blobs(hazy_head, ".")
changed = []
for rel, isha in idx.items():
    full = os.path.join(HAZY, rel)
    if not os.path.isfile(full) or os.path.islink(full):
        continue
    b = blob_sha(read(full))
    if head_all.get(rel) != b:
        changed.append(rel)
print("changed tracked files:", changed)
rc, out = git("rev-parse", "5af9d722^1")
pre = out.decode().strip()
print("5af9d722^1 =", pre[:8])
pre_blobs = {}
for rel in changed:
    rc, out = git("rev-parse", f"{pre}:{rel}")
    b = blob_sha(read(os.path.join(HAZY, rel)))
    print(" ", rel, "== 5af9d722^1:", out.decode().strip() == b)
