"""Lane B (r42d): per-fault status counts at head, from fault_survey-head.json."""

import collections
import json
from pathlib import Path

OUT = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneB/out")
rows = json.loads((OUT / "fault_survey-head.json").read_text())
by = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    by[r["fault"]][r["status"]].append(r["route"])
for fault, statuses in by.items():
    print(fault)
    for status, routes in sorted(statuses.items()):
        print(f"  {status}: {len(routes):2d}  {routes}")
