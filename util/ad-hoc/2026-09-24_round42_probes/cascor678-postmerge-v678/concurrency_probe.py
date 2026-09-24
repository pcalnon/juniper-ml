"""Memo thread-safety probe: concurrent misses, a lock-holding reader, and a lock-free reader (read-only)."""
import sys
import threading
import time

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v678"
sys.path.insert(0, S + "/cascor/src")
from api.lifecycle.manager import _TruncatableGenerators  # noqa: E402

LISTING = [
    {"name": "equities", "schema": {"properties": {"allow_truncation": {}}}},
    {"name": "spiral", "schema": {"properties": {}}},
]
fetches = []


class _Client:
    def __init__(self, **kwargs):
        pass

    def list_generators(self):
        fetches.append(threading.get_ident())
        time.sleep(0.2)
        return LISTING


memo = _TruncatableGenerators()
results, errors = [], []


def _worker():
    try:
        results.append(memo.reader(_Client, source="http://jd:8100", api_key=None)())
    except BaseException as exc:  # noqa: BLE001
        errors.append(exc)


threads = [threading.Thread(target=_worker) for _ in range(16)]
t0 = time.monotonic()
for t in threads:
    t.start()
for t in threads:
    t.join(10)
print(f"16 concurrent first reads: fetches={len(fetches)} distinct_results={len(set(results))} errors={errors} elapsed={time.monotonic() - t0:.2f}s")
fetches.clear()
memo.reader(_Client, source="http://jd:8100", api_key=None)()
print("after warm memo, fetches on next read:", len(fetches))

# manager-lock holder (staged path) vs lock-free reader (auto-start) on a cold memo
memo2 = _TruncatableGenerators()
manager_lock = threading.Lock()
done = []


def _staged():
    with manager_lock:
        done.append(("staged", memo2.reader(_Client, source="http://jd2:8100", api_key=None)()))


def _autostart():
    done.append(("auto", memo2.reader(_Client, source="http://jd2:8100", api_key=None)()))


a, b = threading.Thread(target=_staged), threading.Thread(target=_autostart)
a.start()
b.start()
a.join(5)
b.join(5)
print("lock-holder + lock-free both finished:", sorted(k for k, _ in done), "alive:", a.is_alive(), b.is_alive())
