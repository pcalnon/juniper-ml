import importlib.util
import sys
from datetime import datetime, timezone
spec = importlib.util.spec_from_file_location("rt", sys.argv[1])
rt = importlib.util.module_from_spec(spec)
sys.modules["rt"] = rt
spec.loader.exec_module(rt)
UTC = timezone.utc
old = [rt.stamp(s) for s in rt.EXISTING]
pol = rt.parse_policy(rt.NEW_POLICY)
# recovery-day run off schedule, then the daily 14:00 runs; retention restored, first pass at 10-12 14:30
rec = datetime(2026, 10, 9, 15, 23, tzinfo=UTC)
daily = [datetime(2026, 10, 10 + k, 14, 0, tzinfo=UTC) for k in range(3)]
now = datetime(2026, 10, 12, 14, 30, tzinfo=UTC)
gone = rt.to_delete(old + [rec] + daily, now, pol)
print("post-recovery deleted:", sorted(x.isoformat() for x in gone if x > old[-1]))
# AC-3 manual run the same day as the step-10 run
rec2 = [datetime(2026, 10, 9, 15, 23, tzinfo=UTC), datetime(2026, 10, 9, 17, 5, tzinfo=UTC), datetime(2026, 10, 10, 14, 0, tzinfo=UTC)]
gone = rt.to_delete(old + rec2, datetime(2026, 10, 10, 14, 30, tzinfo=UTC), pol)
print("same-day pair deleted:", sorted(x.isoformat() for x in gone if x > old[-1]))
