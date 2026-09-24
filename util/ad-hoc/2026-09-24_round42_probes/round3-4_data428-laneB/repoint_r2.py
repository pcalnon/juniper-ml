"""Lane B: repoint the copied round-2 probes at this lane's extracted tree and scratch dirs.

Replacements run LONGEST first, so "<R2>/pr" cannot eat the prefix of "<R2>/probes".
"""

import re
from pathlib import Path

R2 = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2"
ME = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneB"
d = Path(ME) / "r2probes"
for f in sorted(d.glob("*.py")):
    s = f.read_text()
    n = s.count(R2)
    s = s.replace(R2 + "/probes/rfc_tmp", ME + "/r2probes/rfc_tmp")
    s = s.replace(R2 + "/probes", ME + "/r2probes")
    s = re.sub(re.escape(R2) + r"/pr\b", ME + "/src", s)
    s = s.replace(R2, ME + "/r2probes")
    f.write_text(s)
    print(f.name, "occurrences repointed:", n)
