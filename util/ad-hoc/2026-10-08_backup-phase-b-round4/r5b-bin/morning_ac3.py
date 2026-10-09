import importlib.util
import sys
from datetime import datetime, UTC
spec = importlib.util.spec_from_file_location("rt", sys.argv[1])
rt = importlib.util.module_from_spec(spec)
sys.modules["rt"] = rt
spec.loader.exec_module(rt)
pol = rt.parse_policy(rt.NEW_POLICY)
old = [rt.stamp(s) for s in rt.EXISTING]
for ac3 in ("10:00", "15:20"):
    h, m = map(int, ac3.split(":"))
    d0 = datetime(2026, 10, 12, h, m, tzinfo=UTC)
    sched = [datetime(2026, 10, 12 + k, 14, 0, tzinfo=UTC) for k in range(0, 4)]
    new = [d0] + [s for s in sched if s > d0]
    now = datetime(2026, 10, 15, 14, 30, tzinfo=UTC)
    gone = rt.to_delete(old + new, now, pol)
    print("AC-3 at", ac3, "post-recovery deleted:", sorted(rt.short(x) for x in new if x in gone))
