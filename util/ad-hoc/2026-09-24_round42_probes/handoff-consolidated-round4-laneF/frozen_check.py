#!/usr/bin/env python3
"""Round 4 lane F probe: check handoff-frozen/README.md against the files and the reports.

1. Each README row's sha256 prefix matches its file.
2. For each frozen file, which handoff-*.md reports quote its sha256 prefix (any 8+ hex prefix),
   compared with the README's "Cited by" column.
3. Every scratch path (hc<k>/..., handoff_session_r<k>_frozen.md, *_frozen.md, doc2_peer_final...)
   and every sha256-looking hex a report cites, and whether a copy of it is in the directory.
Read-only."""
import collections
import glob
import hashlib
import os
import re

D = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/reports/2026-09-24_defect-register-round-42"
FZ = os.path.join(D, "handoff-frozen")

with open(os.path.join(FZ, "README.md"), encoding="utf-8") as fh:
    readme = fh.read()
rows = re.findall(r"^\| `([^`]+)` \| `([^`]+)` \| `([0-9a-f]+)` \| (.*?) \|$", readme, re.M)
full = {}
for f in sorted(os.listdir(FZ)):
    with open(os.path.join(FZ, f), "rb") as fh:
        full[f] = hashlib.sha256(fh.read()).hexdigest()
print("== 1. README rows vs files ==")
for fname, scratch, prefix, cited in rows:
    print(f"  {fname:30s} {scratch:36s} {prefix} match={full.get(fname, '').startswith(prefix)}")
print("  files not in README:", sorted(set(full) - {r[0] for r in rows} - {"README.md"}))

reports = sorted(glob.glob(os.path.join(D, "handoff-*.md")))
texts = {}
for r in reports:
    with open(r, encoding="utf-8") as fh:
        texts[os.path.basename(r)] = fh.read()

print("\n== 2. which reports quote each frozen file's sha prefix (8+ hex) ==")
for fname, scratch, prefix, cited in rows:
    sha = full[fname]
    who = []
    for name, t in texts.items():
        # any run of 8+ hex chars that is a prefix of sha
        for m in re.finditer(r"(?<![0-9a-f])([0-9a-f]{8,64})(?![0-9a-f])", t):
            if sha.startswith(m.group(1)):
                who.append(name.replace(".md", ""))
                break
    also_path = [n.replace(".md", "") for n, t in texts.items() if scratch in t and n.replace(".md", "") not in who]
    print(f"  {fname}: README cites-by = {cited}")
    print(f"      sha quoted by: {who}")
    if also_path:
        print(f"      scratch path (no sha) cited by: {also_path}")

print("\n== 3. scratch paths and sha256s cited in the reports ==")
pat_path = re.compile(r"(hc\d/[A-Za-z0-9_./-]+\.md|handoff_session_r\d_frozen\.md|[A-Za-z0-9_-]+_frozen\.md|doc2_peer_final[A-Za-z0-9_]*\.md)")
paths = collections.defaultdict(set)
for name, t in texts.items():
    for m in pat_path.finditer(t):
        paths[m.group(1)].add(name.replace(".md", ""))
known_scratch = {r[1] for r in rows}
for p, who in sorted(paths.items()):
    base = p
    in_dir = base in known_scratch or any(base.endswith(k) or k.endswith(base) for k in known_scratch)
    print(f"  {p:45s} in README: {in_dir}  cited by {sorted(who)}")
# sha256 mentions: 'sha256' followed within 40 chars by hex
print("\n  sha256-labelled hex values:")
seen = collections.defaultdict(set)
for name, t in texts.items():
    for m in re.finditer(r"sha256[^0-9a-f]{0,40}?([0-9a-f]{8,64})", t):
        seen[m.group(1)].add(name.replace(".md", ""))
for h, who in sorted(seen.items()):
    match = [f for f, s in full.items() if s.startswith(h)]
    print(f"   {h[:20]:20s} -> {match or 'NOT IN DIRECTORY'}  cited by {sorted(who)}")
