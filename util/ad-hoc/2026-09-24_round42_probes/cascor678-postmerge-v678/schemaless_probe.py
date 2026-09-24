"""A schema-less listing is memoised as a SUCCESS (empty set) and yields the knob-already-on remedy (read-only)."""
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v678"
sys.path.insert(0, S + "/cascor/src")
from api.lifecycle.manager import TrainingLifecycleManager, _TruncatableGenerators  # noqa: E402

calls = []


class _Client:
    def __init__(self, **kwargs):
        pass

    def list_generators(self):
        calls.append(1)
        # names only -- e.g. a proxy/gateway or a future listing that drops the per-entry schema
        return [{"name": "equities", "version": "5.0.0"}, {"name": "spiral", "version": "3.0.0"}]


memo = _TruncatableGenerators()
reader = memo.reader(_Client, source="http://jd:8100", api_key=None)
print("first read:", reader(), "second read:", reader(), "fetches:", len(calls), "(memoised as a success)")
params, source, wire, refused, withheld = TrainingLifecycleManager._resolve_truncation_stance({}, generator="equities", allow_truncated=True, truncatable_generators=reader)
print("flag ON, caller silent ->", {"params": params, "wire": wire, "withheld": withheld})
msg = TrainingLifecycleManager._describe_dataset_fetch_failure(RuntimeError("HTTP 422: Re-submit with allow_truncation=true"), allow_truncated=wire, caller_refused=refused, opt_in_withheld=withheld)
print("remedy names the already-on knob:", "JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true" in msg)
