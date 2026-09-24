"""Measure the bounded listing client's wall time on refused / blackholed endpoints (read-only)."""
import sys
import time

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v678"
sys.path.insert(0, S + "/cascor/src")
from juniper_data_client import JuniperDataClient  # noqa: E402

from api.lifecycle.manager import _GENERATOR_LIST_RETRIES, _GENERATOR_LIST_TIMEOUT_SECONDS, _TruncatableGenerators  # noqa: E402

memo = _TruncatableGenerators()
for url in ("http://127.0.0.1:9", "http://10.255.255.1:8100"):
    reader = memo.reader(JuniperDataClient, source=url, api_key=None)
    t0 = time.monotonic()
    result = reader()
    print(f"{url}: result={result!r} elapsed={time.monotonic() - t0:.2f}s (timeout={_GENERATOR_LIST_TIMEOUT_SECONDS}, retries={_GENERATOR_LIST_RETRIES})")
