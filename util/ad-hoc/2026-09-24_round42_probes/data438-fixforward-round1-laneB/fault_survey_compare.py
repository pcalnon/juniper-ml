"""Lane B (r42d): side-by-side main vs head for the fault survey."""

import json
from pathlib import Path

OUT = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneB/out")
h = json.loads((OUT / "fault_survey-head.json").read_text())
m = json.loads((OUT / "fault_survey-main.json").read_text())
mm = {(r["fault"], r["route"]): r for r in m}
lines = []
for r in h:
    b = mm[(r["fault"], r["route"])]
    flag = "" if (r["status"], r["detail"]) == (b["status"], b["detail"]) else "  <-- changed"
    lines.append(f'{r["fault"]:18} {r["route"]:32} main={b["status"]} head={r["status"]} head_loud={r["loud_records"]} head_loud_id={r["loud_records_naming_id"]} head_detail={r["detail"]!r}{flag}')
text = "\n".join(lines)
(OUT / "fault_survey-compare.txt").write_text(text + "\n")
print(text)
