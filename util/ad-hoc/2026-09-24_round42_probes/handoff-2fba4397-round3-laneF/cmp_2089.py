"""Compare the worktree's untracked #2089 files with a2fa3ad8's blobs by blob hash, both ways. Read-only."""
import hashlib
from pathlib import Path

WT = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream")
tree = {}
for line in (Path(__file__).parent / "tree_2089.txt").read_text().splitlines():
    meta, path = line.split("\t", 1)
    tree[path] = meta.split()[2]


def blob(p: Path) -> str:
    data = p.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


same = diff = missing = 0
for path, sha in tree.items():
    p = WT / path
    if not p.exists():
        missing += 1
        print("MISSING locally:", path)
    elif blob(p) == sha:
        same += 1
    else:
        diff += 1
        print("DIFFERS:", path)
local = [p for p in (WT / "util/ad-hoc/2026-09-24_round42_probes").rglob("*") if p.is_file()]
extra = [str(p.relative_to(WT)) for p in local if str(p.relative_to(WT)) not in tree]
print(f"blobs at a2fa3ad8: {len(tree)}; identical {same}; differ {diff}; missing {missing}; local-only files under the probe dir: {extra}")
