"""Would appending the E.1 marker to the unmarked affected lines keep them within markdownlint's 512?
And does the register cite any of them (a marker changes that line's text, not its number)?"""

import re
from pathlib import Path

WT = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map/notes")
P = (WT / "JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md").read_text(encoding="utf-8").split("\n")
R = (WT / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md").read_text(encoding="utf-8")
M = " **[Corrected: E.1](#e1-artifact-validator)**"
for n in (3685, 5332, 9510):
    ln = P[n - 1]
    print(f"L{n}: len={len(ln)} with marker={len(ln.rstrip()) + len(M)} (<=512: {len(ln.rstrip()) + len(M) <= 512}); ends paragraph: {P[n].strip() == ''}")
for n in (3685, 5332, 9509, 9510):
    print(f"register cites {n}: {bool(re.search(rf'(?<![\\d.-]){n}(?![\\d])', R))}")
