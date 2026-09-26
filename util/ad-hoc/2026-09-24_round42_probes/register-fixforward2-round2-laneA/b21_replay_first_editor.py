#!/usr/bin/env python3
"""Lane A round 2: the FIRST editor's source changed in 990ef3f9 (F541 + escaped U+2028/U+2029). Does the changed
editor still turn df21367d's three files into e2f87aae's, byte for byte, and still refuse a second run?"""
import shutil
import subprocess
import sys
from pathlib import Path

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA")
FILES = ["notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md",
         "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md", "docs/REFERENCE.md"]
ED = "util/ad-hoc/2026-09-24_register_round42_second_fixforward.py"


def show(rev, rel):
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=WT, check=True, capture_output=True).stdout


root = S / "replay1"
if root.exists():
    shutil.rmtree(root)
for rel in FILES:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_bytes(show("df21367d", rel))
(root / ED).parent.mkdir(parents=True, exist_ok=True)
(root / ED).write_bytes(show("990ef3f9", ED))
p = subprocess.run([sys.executable, str(root / ED)], capture_output=True, text=True)
print("run 1 rc", p.returncode, "|", (p.stdout + p.stderr).strip().splitlines()[-1])
for rel in FILES:
    print(f"   {rel}: == e2f87aae: {(root / rel).read_bytes() == show('e2f87aae', rel)}")
p = subprocess.run([sys.executable, str(root / ED)], capture_output=True, text=True)
print("run 2 rc", p.returncode, "|", (p.stdout + p.stderr).strip().splitlines()[-1])
# old vs new editor source: same constants?
import importlib.util
vals = {}
for rev in ("e2f87aae", "990ef3f9"):
    f = S / "tmp" / f"ed_{rev}.py"
    f.write_bytes(show(rev, ED))
    spec = importlib.util.spec_from_file_location(f"ed_{rev}", f)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    vals[rev] = (m.REG_SUBS, m.PRIMER_LINES, m.LINE_BREAKERS, getattr(m, "REF_SUBS", None))
    f.unlink()
print("editor constants identical e2f87aae vs 990ef3f9:", vals["e2f87aae"] == vals["990ef3f9"])
shutil.rmtree(root)
