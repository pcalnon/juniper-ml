"""Count what the copier saw in the six lane scratch dirs (top level + scripts/), by suffix. Read-only."""
import importlib.util
import sys
from pathlib import Path

WT = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream")
spec = importlib.util.spec_from_file_location("copier", WT / "util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py")
copier = importlib.util.module_from_spec(spec)
sys.modules["copier"] = copier
spec.loader.exec_module(copier)
print("EXTS:", copier.EXTS, "SRC:", copier.SRC)
tot: dict[str, int] = {}
for lane in copier.LANES:
    roots = [copier.SRC / lane]
    if (copier.SRC / lane / "scripts").is_dir():
        roots.append(copier.SRC / lane / "scripts")
    counts: dict[str, int] = {}
    for root in roots:
        for f in root.iterdir():
            if f.is_file():
                counts[f.suffix or "(none)"] = counts.get(f.suffix or "(none)", 0) + 1
    print(lane, dict(sorted(counts.items())))
    for k, v in counts.items():
        tot[k] = tot.get(k, 0) + v
print("TOTAL", dict(sorted(tot.items())), "all files:", sum(tot.values()))
