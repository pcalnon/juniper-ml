from pathlib import Path
SRC = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad")
tb = ts = tp = 0
for lane in ("r42b/laneA", "r42b/laneB", "r42b2/laneA", "r42b2/laneB", "r42d/laneA", "r42d/laneB"):
    roots = [SRC / lane]
    if (SRC / lane / "scripts").is_dir():
        roots.append(SRC / lane / "scripts")
    b = s = p = 0
    for r in roots:
        if not r.is_dir():
            continue
        for f in r.iterdir():
            if f.is_file():
                b += f.suffix == ".bash"
                s += f.suffix == ".sh"
                p += f.suffix == ".py"
    print(lane, "exists" if (SRC / lane).is_dir() else "MISSING", "bash", b, "sh", s, "py", p)
    tb += b; ts += s; tp += p
print("total bash", tb, "sh", ts, "sum", tb + ts, "py", tp)
# recursive count too
rb = sum(1 for lane in ("r42b", "r42b2", "r42d") for f in (SRC / lane).rglob("*.bash")) if (SRC / "r42b").is_dir() else -1
rs = sum(1 for lane in ("r42b", "r42b2", "r42d") for f in (SRC / lane).rglob("*.sh")) if (SRC / "r42b").is_dir() else -1
print("recursive under r42b/r42b2/r42d: bash", rb, "sh", rs)
