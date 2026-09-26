import re, sys
from pathlib import Path
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream")
R = (W / "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md").read_text(encoding="utf-8").split("\n")
def show(a, b, width=400):
    for i in range(a, b + 1):
        print(f"{i}: {R[i-1][:width]}")
pat = sys.argv[1] if len(sys.argv) > 1 else None
if pat:
    for i, l in enumerate(R, 1):
        if re.search(pat, l):
            print(f"{i}: {l[:int(sys.argv[2]) if len(sys.argv)>2 else 300]}")
else:
    print("lines:", len(R))
