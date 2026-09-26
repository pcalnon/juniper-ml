#!/usr/bin/env python3
"""Count script files in the session's lane scratch trees and compare with #2089's copied set (read-only)."""
import hashlib
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad")
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/util/ad-hoc/2026-09-24_round42_probes")
EXT = {".py", ".sh", ".bash"}
copied = {}
for p in W.rglob("*"):
    if p.is_file() and p.suffix in EXT:
        copied.setdefault(hashlib.sha256(p.read_bytes()).hexdigest(), []).append(p.relative_to(W).as_posix())
print("copied scripts:", sum(len(v) for v in copied.values()))
for tree in ("r42b", "r42b2", "r42d"):
    files = [p for p in (S / tree).rglob("*") if p.is_file() and p.suffix in EXT]
    missing = [p for p in files if hashlib.sha256(p.read_bytes()).hexdigest() not in copied]
    subdirs = sorted({p.relative_to(S / tree).parts[0] + "/" + (p.relative_to(S / tree).parts[1] if len(p.relative_to(S / tree).parts) > 2 else "") for p in files})
    print(f"{tree}: {len(files)} scripts; not byte-present in #2089: {len(missing)}")
    by_dir = {}
    for p in missing:
        rel = p.relative_to(S / tree)
        key = "/".join(rel.parts[:-1])
        by_dir.setdefault(key, []).append(rel.name)
    for k, v in sorted(by_dir.items()):
        print(f"   {k}: {len(v)} e.g. {sorted(v)[:6]}")
