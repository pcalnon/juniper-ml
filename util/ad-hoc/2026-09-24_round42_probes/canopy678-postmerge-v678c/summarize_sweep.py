"""Summarize one or two sweep JSON files: counts per tier, and before/after status transitions."""

import json
import sys
from collections import Counter

STATE = {"POST", "PUT", "PATCH", "DELETE"}
MW401 = "Missing API key. Provide X-API-Key header."


def load(p):
    with open(p) as f:
        return json.load(f)


def summarize(doc, label):
    pairs = doc["pairs"]
    gated = [p for p in pairs if p["tier"] == "key_gated"]
    state = [p for p in gated if p["method"] in STATE]
    get_np = [p for p in gated if p["method"] == "GET" and not p["parameterized"]]
    get_p = [p for p in gated if p["method"] == "GET" and p["parameterized"]]
    kinds = Counter(r["kind"] for r in doc["routes"])
    print(f"== {label}: auth_enabled(main)={doc['auth_enabled_main']} singleton={doc['auth_enabled_singleton']} docs_enabled={doc['docs_enabled']} route kinds={dict(kinds)}")
    print(f"   pairs total={len(pairs)} tiers={dict(Counter(p['tier'] for p in pairs))}")
    print(f"   key_gated={len(gated)} state_changing={len(state)} GET_parameterless={len(get_np)} GET_parameterized={len(get_p)} other_methods={Counter(p['method'] for p in gated if p['method'] not in STATE | {'GET'})}")
    mw = [p for p in gated if p["status"] == 401 and p["detail"] == MW401]
    print(f"   key_gated refused by middleware (401 Missing API key): {len(mw)}/{len(gated)}")
    print(f"   key_gated status histogram: {dict(Counter(str(p['status']) for p in gated))}")
    print(f"   parameterless GET statuses: {dict(Counter(str(p['status']) for p in get_np))}")
    return {(p["method"], p["path"]): p for p in pairs}


docs = [(a, load(a)) for a in sys.argv[1:]]
maps = [summarize(d, a) for a, d in docs]
if len(maps) == 2:
    a, b = maps
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    print("pairs only in first:", only_a)
    print("pairs only in second:", only_b)
    gated_a = {k for k, v in a.items() if v["tier"] == "key_gated"}
    gated_b = {k for k, v in b.items() if v["tier"] == "key_gated"}
    print("key_gated only in first:", sorted(gated_a - gated_b))
    print("key_gated only in second:", sorted(gated_b - gated_a))
    trans = Counter()
    for k in sorted(gated_a & gated_b):
        trans[(str(a[k]["status"]), str(b[k]["status"]))] += 1
    print("status transitions first->second over common key_gated pairs:", dict(trans))
if "-v" in sys.argv or len(maps) == 1:
    pass
