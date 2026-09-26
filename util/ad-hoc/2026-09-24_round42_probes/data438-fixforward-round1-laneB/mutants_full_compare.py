"""Lane B (r42d): which mutants' full-suite failures go beyond the baseline's environment-only failures?"""

import json
from pathlib import Path

OUT = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneB/out")
rows = [json.loads(line) for line in (OUT / "my_mutants_full.log").read_text().splitlines() if line.startswith("{")]
base = set(next(r for r in rows if r["mutant"] == "BASELINE")["failed"])
print("baseline failures (environment):", sorted(base))
for r in rows:
    if r["mutant"] == "BASELINE":
        continue
    extra = sorted(set(r["failed"]) - base)
    print(f'{r["mutant"]:5} {"SURVIVES" if not extra else "CAUGHT  "} extra_failures={extra}')
