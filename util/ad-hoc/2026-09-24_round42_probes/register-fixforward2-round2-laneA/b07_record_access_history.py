#!/usr/bin/env python3
"""Lane A round 2: at each juniper-data commit that changed record_access in routes/datasets.py (and its parent),
which route handlers call record_access? Uses the local clone read-only (git show) and b06's AST mapper.
"""
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA")
REPO = "/home/pcalnon/Development/python/Juniper/juniper-data"
REL = "juniper_data/api/routes/datasets.py"
revs = ["cbae474^", "cbae474", "da2be27^", "da2be27", "af7831b^", "af7831b", "v0.11.0", "v0.14.0", "v0.15.0", "v0.16.0", "1afc3484"]
for rev in revs:
    p = subprocess.run(["git", "show", f"{rev}:{REL}"], cwd=REPO, capture_output=True, text=True)
    if p.returncode:
        print(f"== {rev}: {p.stderr.strip()}")
        continue
    f = S / "tmp" / f"datasets_{rev.replace('^', '_parent')}.py"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(p.stdout, encoding="utf-8")
    out = subprocess.run([sys.executable, str(S / "b06_record_access_routes.py"), str(f)], capture_output=True, text=True).stdout
    hits = [ln for ln in out.splitlines() if "record_access@[]" not in ln or "helpers" in ln]
    print(f"== {rev}")
    for ln in hits:
        print("   ", ln)
    f.unlink()
