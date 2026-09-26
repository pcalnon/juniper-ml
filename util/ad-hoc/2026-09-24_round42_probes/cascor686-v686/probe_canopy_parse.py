"""Run canopy main's _producer_detail_from_refusal (copied verbatim from 9cdfcad4) on each merged refusal branch (scratch)."""

import os
import sys

sys.path.insert(0, os.path.join(sys.argv[1], "src"))

from api.lifecycle.manager import _OPT_IN_SKIPPED_LIST_UNREADABLE, _OPT_IN_SKIPPED_NOT_TRUNCATABLE, TrainingLifecycleManager  # noqa: E402


def _producer_detail_from_refusal(detail: str) -> str:  # verbatim: juniper-canopy origin/main src/frontend/dashboard_manager.py:8332
    marker = "Producer detail: "
    if marker not in detail:
        return ""
    tail = detail.split(marker, 1)[1]
    for stop in (" To accept it,", " The resulting dataset"):
        if stop in tail:
            tail = tail.split(stop, 1)[0]
    return tail.strip()


PRODUCER = "Validation error (422): Shares outstanding could not be resolved for 3 symbols. Re-submit with allow_truncation=true"
exc = RuntimeError(PRODUCER)
cases = {
    "flag off, silent": dict(allow_truncated=False),
    "caller refused": dict(allow_truncated=False, caller_refused=True),
    "WITHHELD (flag on)": dict(allow_truncated=False, opt_in_skipped=_OPT_IN_SKIPPED_LIST_UNREADABLE, deployment_flag_on=True),
    "not declared (flag on)": dict(allow_truncated=False, opt_in_skipped=_OPT_IN_SKIPPED_NOT_TRUNCATABLE, deployment_flag_on=True),
    "null (flag on)": dict(allow_truncated=False, deployment_flag_on=True),
}
for name, kw in cases.items():
    msg = TrainingLifecycleManager._describe_dataset_fetch_failure(exc, **kw)
    extracted = _producer_detail_from_refusal(msg)
    print(f"[{name}] extracted == producer's own text: {extracted == PRODUCER}")
    if extracted != PRODUCER:
        print(f"    canopy would render: {extracted!r}")
