"""Lane A1: the most precondition work ONE request can buy, per route, with both fields at the cap.

GET  /{id} and /{id}/artifact: read_precondition_status(If-Match, If-None-Match, etag).
     If-Match is parsed first; only when it HOLDS is If-None-Match parsed too. So the worst
     GET names the current tag as the LAST of the maximum number of tags in If-Match, and
     sends a maximal well-formed If-None-Match that names nothing.
PATCH /{id}/tags: write_preconditions_hold(If-Match, If-None-Match, etag), evaluated INSIDE
     DatasetStore._version_lock. If-None-Match is parsed twice there (_well_formed, then
     _list_names), so the worst PATCH is three full parses and two tag scans under the lock.
"""

import sys
import time

SCRATCH = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA1"
sys.path.insert(0, f"{SCRATCH}/tree-3a76a4c")
from juniper_data.api import http_cache as hc  # noqa: E402

assert hc.__file__.startswith(SCRATCH)
CAP = hc.MAX_PRECONDITION_FIELD_LENGTH
ETAG = hc.body_etag(b"some metadata body")


def tmin(fn, reps=50):
    best = float("inf")
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        fn()
        best = min(best, time.perf_counter_ns() - t0)
    return best / 1e3


def max_tags_then(last: str, unit: str = '"",') -> str:
    k = (CAP - len(last)) // len(unit)
    f = unit * k + last
    assert len(f) <= CAP
    return f


im_hit = max_tags_then(ETAG)  # holds: names the current tag, last of ~2700
inm_miss = max_tags_then('""')  # well-formed, ~2730 tags, names nothing
inm_hit = max_tags_then(ETAG)
inm_garbage = (", " * (CAP // 2))[: CAP - 1] + "x"  # malformed: fails at the very end
assert hc._well_formed(im_hit) and hc._well_formed(inm_miss) and not hc._well_formed(inm_garbage)
assert len(im_hit) <= CAP and len(inm_miss) <= CAP and len(inm_garbage) == CAP

print(f"field lengths: If-Match={len(im_hit)} If-None-Match(miss)={len(inm_miss)} garbage={len(inm_garbage)}")
cases = {
    "GET  no headers": lambda: hc.read_precondition_status(None, None, ETAG),
    "GET  IM holds (last of max tags) + INM max tags miss -> 200": lambda: hc.read_precondition_status(im_hit, inm_miss, ETAG),
    "GET  IM holds + INM max tags hit last -> 304": lambda: hc.read_precondition_status(im_hit, inm_hit, ETAG),
    "GET  IM garbage at cap -> 412": lambda: hc.read_precondition_status(inm_garbage, None, ETAG),
    "GET  INM garbage at cap -> 200": lambda: hc.read_precondition_status(None, inm_garbage, ETAG),
    "PATCH no headers": lambda: hc.write_preconditions_hold(None, None, ETAG),
    "PATCH IM holds + INM max tags miss -> proceeds": lambda: hc.write_preconditions_hold(im_hit, inm_miss, ETAG),
    "PATCH IM holds + INM garbage -> 412": lambda: hc.write_preconditions_hold(im_hit, inm_garbage, ETAG),
    "PATCH INM max tags miss only -> proceeds": lambda: hc.write_preconditions_hold(None, inm_miss, ETAG),
}
assert hc.read_precondition_status(im_hit, inm_miss, ETAG) is None
assert hc.read_precondition_status(im_hit, inm_hit, ETAG) == 304
assert hc.write_preconditions_hold(im_hit, inm_miss, ETAG) is True
assert hc.write_preconditions_hold(im_hit, inm_garbage, ETAG) is False
for name, fn in cases.items():
    print(f"  {name:62s} {tmin(fn):9.1f} us")
